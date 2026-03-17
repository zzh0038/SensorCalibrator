"""
Sensor Data Buffer Module

Manages storage, slicing, and statistics for sensor data streams.
Thread-safe operations for use with concurrent data acquisition.
"""

import threading
from typing import List, Optional, Tuple, Dict, Any, Deque
from collections import deque
import itertools
import numpy as np

import time
from .config import Config


class SensorDataBuffer:
    """
    Thread-safe buffer for sensor time-series data.
    
    Manages multiple data channels (time, accelerometer, gyroscope, etc.)
    with automatic size limiting and efficient slicing.
    
    优化：
    - 使用 __slots__ 减少内存占用
    - 提供视图模式避免不必要的数据复制
    """
    
    # 优化：__slots__ 减少内存占用
    __slots__ = [
        '_max_points', '_lock',
        '_time_data', '_mpu_accel_data', '_mpu_gyro_data', 
        '_adxl_accel_data', '_gravity_mag_data',
        '_stats_cache', '_stats_valid', '_data_version', '_stats_version',
        '_data_start_time', '_packet_count', '_expected_frequency'
    ]
    
    def __init__(self, max_points: Optional[int] = None) -> None:
        """
        Initialize data buffer.
        
        Args:
            max_points: Maximum data points to retain. Defaults to Config.MAX_DATA_POINTS.
        """
        self._max_points = max_points or Config.MAX_DATA_POINTS
        self._lock = threading.Lock()
        
        # Data storage - 使用 deque 自动管理长度
        self._time_data: Deque[float] = deque(maxlen=self._max_points)
        self._mpu_accel_data: List[Deque[float]] = [deque(maxlen=self._max_points) for _ in range(3)]
        self._mpu_gyro_data: List[Deque[float]] = [deque(maxlen=self._max_points) for _ in range(3)]
        self._adxl_accel_data: List[Deque[float]] = [deque(maxlen=self._max_points) for _ in range(3)]
        self._gravity_mag_data: Deque[float] = deque(maxlen=self._max_points)
        
        # Statistics cache - 优化：添加版本号机制避免重复计算
        self._stats_cache: Dict[str, Any] = {}
        self._stats_valid = False
        self._data_version = 0  # 数据版本号，数据变化时递增
        self._stats_version = -1  # 统计信息对应的版本号
        
        # 时间跟踪（兼容 DataProcessor 接口）
        self._data_start_time: Optional[float] = None
        self._packet_count = 0
        self._expected_frequency = Config.EXPECTED_FREQUENCY
    
    # -------------------------------------------------------------------------
    # Data Addition
    # -------------------------------------------------------------------------
    
    def add_sample(
        self,
        timestamp: float,
        mpu_accel: Tuple[float, float, float],
        mpu_gyro: Tuple[float, float, float],
        adxl_accel: Tuple[float, float, float],
        gravity_mag: float
    ) -> None:
        """
        Add a complete sensor sample to the buffer.
        
        Args:
            timestamp: Time value
            mpu_accel: MPU6050 accelerometer (x, y, z)
            mpu_gyro: MPU6050 gyroscope (x, y, z)
            adxl_accel: ADXL355 accelerometer (x, y, z)
            gravity_mag: Gravity magnitude
        """
        with self._lock:
            self._time_data.append(timestamp)
            for i in range(3):
                self._mpu_accel_data[i].append(mpu_accel[i])
                self._mpu_gyro_data[i].append(mpu_gyro[i])
                self._adxl_accel_data[i].append(adxl_accel[i])
            self._gravity_mag_data.append(gravity_mag)
            
            # deque 自动处理长度限制
            # 优化：数据变化时递增版本号，使缓存失效
            self._data_version += 1
            self._stats_valid = False
    
    # -------------------------------------------------------------------------
    # Data Access
    # -------------------------------------------------------------------------
    
    # -------------------------------------------------------------------------
    # Data Access - 优化：提供视图模式避免不必要的数据复制
    # -------------------------------------------------------------------------
    
    def get_time_data_view(self):
        """
        获取时间数据的只读视图（不复制数据）
        
        注意：返回的是视图对象，不是数据副本。数据可能随时被其他线程修改。
        适用于只读访问且对数据新鲜度要求不高的场景。
        
        Returns:
            DataView: 时间数据视图
        """
        return DataView(self._time_data, self._lock)
    
    def get_mpu_accel_view(self, channel: int = 0):
        """
        获取 MPU 加速度数据的只读视图
        
        Args:
            channel: 通道索引 (0=X, 1=Y, 2=Z)
            
        Returns:
            DataView: 指定通道的数据视图
        """
        if 0 <= channel < 3:
            return DataView(self._mpu_accel_data[channel], self._lock)
        raise ValueError(f"Channel must be 0, 1, or 2, got {channel}")
    
    @property
    def time_data(self) -> List[float]:
        """Get copy of time data."""
        with self._lock:
            return list(self._time_data)
    
    @property
    def mpu_accel_data(self) -> List[List[float]]:
        """Get copy of MPU6050 accelerometer data (3 channels)."""
        with self._lock:
            return [list(ch) for ch in self._mpu_accel_data]
    
    @property
    def mpu_gyro_data(self) -> List[List[float]]:
        """Get copy of MPU6050 gyroscope data (3 channels)."""
        with self._lock:
            return [list(ch) for ch in self._mpu_gyro_data]
    
    @property
    def adxl_accel_data(self) -> List[List[float]]:
        """Get copy of ADXL355 accelerometer data (3 channels)."""
        with self._lock:
            return [list(ch) for ch in self._adxl_accel_data]
    
    @property
    def gravity_mag_data(self) -> List[float]:
        """Get copy of gravity magnitude data."""
        with self._lock:
            return list(self._gravity_mag_data)
    
    def get_latest(self, n: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get the latest n samples.
        
        Args:
            n: Number of samples to retrieve
            
        Returns:
            Dictionary with data arrays, or None if insufficient data
        """
        with self._lock:
            if len(self._time_data) < n:
                return None
            
            # 使用 itertools.islice 高效获取最后 n 个元素
            # 避免将完整 deque 转换为 list
            return {
                'time': list(itertools.islice(self._time_data, max(0, len(self._time_data) - n), None)),
                'mpu_accel': [list(itertools.islice(ch, max(0, len(ch) - n), None)) for ch in self._mpu_accel_data],
                'mpu_gyro': [list(itertools.islice(ch, max(0, len(ch) - n), None)) for ch in self._mpu_gyro_data],
                'adxl_accel': [list(itertools.islice(ch, max(0, len(ch) - n), None)) for ch in self._adxl_accel_data],
                'gravity': list(itertools.islice(self._gravity_mag_data, max(0, len(self._gravity_mag_data) - n), None)),
            }
    
    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------
    
    def calculate_statistics(
        self,
        window_size: Optional[int] = None
    ) -> Dict[str, Dict[str, List[float]]]:
        """
        Calculate statistics for recent data - 优化版本
        
        优化点：
        - 最小化临界区，只在锁内复制数据
        - 计算在锁外进行，减少锁竞争
        
        Args:
            window_size: Number of samples to include. Defaults to Config.STATS_WINDOW_SIZE.
            
        Returns:
            Dictionary with mean and std for each channel
        """
        window = window_size or Config.STATS_WINDOW_SIZE
        
        # 第一阶段：在锁内快速复制数据
        with self._lock:
            if len(self._time_data) < 10:
                return self._empty_stats()
            
            # Adjust window to available data
            window = min(window, len(self._time_data))
            start_idx = len(self._time_data) - window
            
            # 只复制数据，不进行计算
            mpu_accel_data = []
            mpu_gyro_data = []
            adxl_accel_data = []
            gravity_data = []
            
            for i in range(3):
                if len(self._mpu_accel_data[i]) >= window:
                    mpu_accel_data.append(
                        list(itertools.islice(self._mpu_accel_data[i], start_idx, None))
                    )
                else:
                    mpu_accel_data.append(None)
                    
                if len(self._mpu_gyro_data[i]) >= window:
                    mpu_gyro_data.append(
                        list(itertools.islice(self._mpu_gyro_data[i], start_idx, None))
                    )
                else:
                    mpu_gyro_data.append(None)
                    
                if len(self._adxl_accel_data[i]) >= window:
                    adxl_accel_data.append(
                        list(itertools.islice(self._adxl_accel_data[i], start_idx, None))
                    )
                else:
                    adxl_accel_data.append(None)
            
            if len(self._gravity_mag_data) >= window:
                gravity_data = list(itertools.islice(self._gravity_mag_data, start_idx, None))
        
        # 第二阶段：在锁外进行计算（减少锁竞争）
        stats = {
            'mpu_accel': {'mean': [0.0, 0.0, 0.0], 'std': [0.0, 0.0, 0.0]},
            'mpu_gyro': {'mean': [0.0, 0.0, 0.0], 'std': [0.0, 0.0, 0.0]},
            'adxl_accel': {'mean': [0.0, 0.0, 0.0], 'std': [0.0, 0.0, 0.0]},
            'gravity': {'mean': 0.0, 'std': 0.0},
        }
        
        for i in range(3):
            if mpu_accel_data[i] is not None:
                stats['mpu_accel']['mean'][i] = float(np.mean(mpu_accel_data[i]))
                stats['mpu_accel']['std'][i] = float(np.std(mpu_accel_data[i]))
            
            if mpu_gyro_data[i] is not None:
                stats['mpu_gyro']['mean'][i] = float(np.mean(mpu_gyro_data[i]))
                stats['mpu_gyro']['std'][i] = float(np.std(mpu_gyro_data[i]))
            
            if adxl_accel_data[i] is not None:
                stats['adxl_accel']['mean'][i] = float(np.mean(adxl_accel_data[i]))
                stats['adxl_accel']['std'][i] = float(np.std(adxl_accel_data[i]))
        
        if gravity_data:
            stats['gravity']['mean'] = float(np.mean(gravity_data))
            stats['gravity']['std'] = float(np.std(gravity_data))
        
        return stats
    
    def _empty_stats(self) -> Dict[str, Dict[str, List[float]]]:
        """Return empty statistics structure."""
        return {
            'mpu_accel': {'mean': [0.0, 0.0, 0.0], 'std': [0.0, 0.0, 0.0]},
            'mpu_gyro': {'mean': [0.0, 0.0, 0.0], 'std': [0.0, 0.0, 0.0]},
            'adxl_accel': {'mean': [0.0, 0.0, 0.0], 'std': [0.0, 0.0, 0.0]},
            'gravity': {'mean': 0.0, 'std': 0.0},
        }
    
    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    
    def clear(self) -> None:
        """Clear all data from buffer."""
        with self._lock:
            self._time_data.clear()
            # 重新初始化 deque，保持 maxlen
            self._mpu_accel_data = [deque(maxlen=self._max_points) for _ in range(3)]
            self._mpu_gyro_data = [deque(maxlen=self._max_points) for _ in range(3)]
            self._adxl_accel_data = [deque(maxlen=self._max_points) for _ in range(3)]
            self._gravity_mag_data.clear()
            self._stats_cache.clear()
            self._stats_valid = False
            # 优化：重置版本号
            self._data_version = 0
            self._stats_version = -1
    
    def __len__(self) -> int:
        """Return number of samples in buffer."""
        with self._lock:
            return len(self._time_data)
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        with self._lock:
            return len(self._time_data) == 0
    
    @property
    def max_points(self) -> int:
        """Get maximum buffer size."""
        return self._max_points
    
    @max_points.setter
    def max_points(self, value: int) -> None:
        """Set maximum buffer size."""
        with self._lock:
            self._max_points = value
            # 重新创建 deque 以应用新的 maxlen
            # 注意：这会保留数据，但超出新限制的旧数据会被丢弃
            self._time_data = deque(self._time_data, maxlen=value)
            self._mpu_accel_data = [deque(ch, maxlen=value) for ch in self._mpu_accel_data]
            self._mpu_gyro_data = [deque(ch, maxlen=value) for ch in self._mpu_gyro_data]
            self._adxl_accel_data = [deque(ch, maxlen=value) for ch in self._adxl_accel_data]
            self._gravity_mag_data = deque(self._gravity_mag_data, maxlen=value)

    # -------------------------------------------------------------------------
    # DataProcessor Compatibility Layer
    # -------------------------------------------------------------------------
    
    @property
    def data_start_time(self) -> Optional[float]:
        """获取数据开始时间（兼容 DataProcessor）"""
        with self._lock:
            return self._data_start_time
    
    @data_start_time.setter
    def data_start_time(self, value: Optional[float]) -> None:
        """设置数据开始时间（兼容 DataProcessor）"""
        with self._lock:
            self._data_start_time = value
    
    @property
    def packet_count(self) -> int:
        """获取包计数（兼容 DataProcessor）"""
        with self._lock:
            return self._packet_count
    
    @packet_count.setter
    def packet_count(self, value: int) -> None:
        """设置包计数（兼容 DataProcessor）"""
        with self._lock:
            self._packet_count = value
    
    @property
    def expected_frequency(self) -> int:
        """获取期望频率（兼容 DataProcessor）"""
        return self._expected_frequency
    
    # 注意：time_data, mpu_accel_data 等属性定义在前面（第 93-165 行）
    # 提供线程安全的副本访问
    
    def has_data(self) -> bool:
        """检查是否有数据（兼容 DataProcessor）"""
        with self._lock:
            return len(self._time_data) > 0
    
    def get_display_data(self, max_points: Optional[int] = None) -> Dict[str, Any]:
        """
        获取用于显示的数据（兼容 DataProcessor）
        
        Args:
            max_points: 最大数据点数，None 表示使用配置值
            
        Returns:
            包含时间序列数据的字典
        """
        if max_points is None:
            max_points = Config.DISPLAY_DATA_POINTS
        
        with self._lock:
            return {
                'time': list(self._time_data),
                'mpu_accel': [list(d) for d in self._mpu_accel_data],
                'adxl_accel': [list(d) for d in self._adxl_accel_data],
                'mpu_gyro': [list(d) for d in self._mpu_gyro_data],
                'gravity': list(self._gravity_mag_data),
            }
    
    def update_statistics(self) -> Dict[str, Any]:
        """
        更新并返回统计信息（兼容 DataProcessor）- 优化版本
        
        优化点：
        - 检查缓存版本，数据未变化时直接返回缓存
        - 最小化临界区，分离数据复制和计算
        
        Returns:
            包含所有统计信息的字典
        """
        # 优化：检查缓存是否有效（数据未变化）
        with self._lock:
            if self._stats_valid and self._stats_version == self._data_version:
                return self._stats_cache.copy()
            
            if len(self._time_data) < 10:
                return self._get_empty_stats()
            
            window_size = min(Config.STATS_WINDOW_SIZE, len(self._time_data))
            start_idx = len(self._time_data) - window_size
            
            # 在锁内只复制数据
            mpu_accel_data = []
            adxl_accel_data = []
            mpu_gyro_data = []
            gravity_data = []
            
            for i in range(3):
                if len(self._mpu_accel_data[i]) >= window_size:
                    mpu_accel_data.append(
                        list(itertools.islice(self._mpu_accel_data[i], start_idx, None))
                    )
                else:
                    mpu_accel_data.append(None)
                    
                if len(self._adxl_accel_data[i]) >= window_size:
                    adxl_accel_data.append(
                        list(itertools.islice(self._adxl_accel_data[i], start_idx, None))
                    )
                else:
                    adxl_accel_data.append(None)
                    
                if len(self._mpu_gyro_data[i]) >= window_size:
                    mpu_gyro_data.append(
                        list(itertools.islice(self._mpu_gyro_data[i], start_idx, None))
                    )
                else:
                    mpu_gyro_data.append(None)
            
            if len(self._gravity_mag_data) >= window_size:
                gravity_data = list(itertools.islice(self._gravity_mag_data, start_idx, None))
        
        # 在锁外进行计算
        stats = self._get_empty_stats()
        
        for i in range(3):
            if mpu_accel_data[i] is not None:
                stats["mpu_accel_mean"][i] = float(np.mean(mpu_accel_data[i]))
                stats["mpu_accel_std"][i] = float(np.std(mpu_accel_data[i]))
            
            if adxl_accel_data[i] is not None:
                stats["adxl_accel_mean"][i] = float(np.mean(adxl_accel_data[i]))
                stats["adxl_accel_std"][i] = float(np.std(adxl_accel_data[i]))
            
            if mpu_gyro_data[i] is not None:
                stats["mpu_gyro_mean"][i] = float(np.mean(mpu_gyro_data[i]))
                stats["mpu_gyro_std"][i] = float(np.std(mpu_gyro_data[i]))
        
        if gravity_data:
            stats["gravity_mean"] = float(np.mean(gravity_data))
            stats["gravity_std"] = float(np.std(gravity_data))
        
        # 更新缓存
        with self._lock:
            self._stats_cache = stats
            self._stats_valid = True
            self._stats_version = self._data_version
        
        return stats.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取当前统计信息（兼容 DataProcessor）
        
        Returns:
            统计信息字典的副本
        """
        with self._lock:
            if not self._stats_valid:
                return self._get_empty_stats()
            return self._stats_cache.copy()
    
    def _get_empty_stats(self) -> Dict[str, Any]:
        """返回空的统计信息结构"""
        return {
            "mpu_accel_mean": [0.0, 0.0, 0.0],
            "mpu_accel_std": [0.0, 0.0, 0.0],
            "adxl_accel_mean": [0.0, 0.0, 0.0],
            "adxl_accel_std": [0.0, 0.0, 0.0],
            "mpu_gyro_mean": [0.0, 0.0, 0.0],
            "mpu_gyro_std": [0.0, 0.0, 0.0],
            "gravity_mean": 0.0,
            "gravity_std": 0.0,
        }
    
    def clear_all(self) -> None:
        """
        清空所有数据（兼容 DataProcessor 接口）
        
        与 clear() 方法功能相同，提供接口兼容性。
        """
        with self._lock:
            self._time_data.clear()
            # 重新初始化 deque，保持 maxlen
            self._mpu_accel_data = [deque(maxlen=self._max_points) for _ in range(3)]
            self._mpu_gyro_data = [deque(maxlen=self._max_points) for _ in range(3)]
            self._adxl_accel_data = [deque(maxlen=self._max_points) for _ in range(3)]
            self._gravity_mag_data.clear()
            self._stats_cache.clear()
            self._stats_valid = False
            self._data_start_time = None
            self._packet_count = 0
            # 优化：重置版本号
            self._data_version = 0
            self._stats_version = -1
    
    @staticmethod
    def _parse_float_safe(s: str) -> float:
        """
        安全地将字符串转换为 float
        
        Args:
            s: 输入字符串
            
        Returns:
            转换后的 float，如果失败返回 0.0
        """
        try:
            return float(s.strip())
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_sensor_data(data_string: str) -> Tuple[Optional[List[float]], Optional[List[float]], Optional[List[float]]]:
        """
        解析传感器数据字符串 - 优化版本
        
        优化点：
        - 使用列表推导式替代 for 循环，减少解释器开销
        - 提取安全转换函数便于复用
        
        Args:
            data_string: 从串口接收的数据字符串，格式为逗号分隔的数字
        
        Returns:
            (mpu_accel, mpu_gyro, adxl_accel) 或 (None, None, None) 如果解析失败
        """
        try:
            parts = data_string.split(",")
            if len(parts) >= 9:
                # 优化：使用列表推导式，比 for 循环更快
                values = [
                    SensorDataBuffer._parse_float_safe(part)
                    for part in parts[:9]
                ]
                
                mpu_accel = values[0:3]
                mpu_gyro = values[3:6]
                adxl_accel = values[6:9]
                
                return mpu_accel, mpu_gyro, adxl_accel
        except Exception:
            # 数据解析失败（格式错误/无效数据），静默返回 None
            pass
        
        return None, None, None



# =============================================================================
# DataView - 只读数据视图（优化内存访问）
# =============================================================================

class DataView:
    """
    数据视图 - 只读访问内部数据，避免复制
    
    使用场景：
    - 需要频繁读取数据但不需要修改
    - 对数据一致性要求不是极高（数据可能随时被写入）
    - 内存敏感的场景
    
    注意：
    - 视图中的数据可能被其他线程修改
    - 如果需要稳定的数据快照，请使用 copy() 方法
    """
    
    __slots__ = ['_data', '_lock']
    
    def __init__(self, data, lock):
        """
        初始化数据视图
        
        Args:
            data: 底层数据（deque）
            lock: 数据锁
        """
        self._data = data
        self._lock = lock
    
    def __len__(self) -> int:
        """获取数据长度"""
        with self._lock:
            return len(self._data)
    
    def __getitem__(self, idx):
        """获取指定索引的数据"""
        with self._lock:
            return self._data[idx]
    
    def get_latest(self, n: int = 1) -> list:
        """
        获取最新的 n 个数据点
        
        Args:
            n: 数据点数量
            
        Returns:
            最新的 n 个数据
        """
        with self._lock:
            if n >= len(self._data):
                return list(self._data)
            return list(itertools.islice(self._data, len(self._data) - n, None))
    
    def get_range(self, start: int, end: Optional[int] = None) -> list:
        """
        获取指定范围的数据
        
        Args:
            start: 起始索引
            end: 结束索引（None 表示到末尾）
            
        Returns:
            指定范围的数据
        """
        with self._lock:
            return list(itertools.islice(self._data, start, end))
    
    def copy(self) -> list:
        """获取数据的完整副本"""
        with self._lock:
            return list(self._data)
    
    def __iter__(self):
        """迭代数据（获取快照后迭代）"""
        return iter(self.copy())


# 为向后兼容添加别名
SensorDataView = DataView
