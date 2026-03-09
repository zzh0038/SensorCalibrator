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
    """
    
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
        
        # Statistics cache
        self._stats_cache: Dict[str, Any] = {}
        self._stats_valid = False
        
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
            
            # deque 自动处理长度限制，无需手动调用 _enforce_size_limit
            self._stats_valid = False
    
    # -------------------------------------------------------------------------
    # Data Access
    # -------------------------------------------------------------------------
    
    @property
    def time_data(self) -> List[float]:
        """Get copy of time data."""
        with self._lock:
            return self._time_data.copy()
    
    @property
    def mpu_accel_data(self) -> List[List[float]]:
        """Get copy of MPU6050 accelerometer data (3 channels)."""
        with self._lock:
            return [ch.copy() for ch in self._mpu_accel_data]
    
    @property
    def mpu_gyro_data(self) -> List[List[float]]:
        """Get copy of MPU6050 gyroscope data (3 channels)."""
        with self._lock:
            return [ch.copy() for ch in self._mpu_gyro_data]
    
    @property
    def adxl_accel_data(self) -> List[List[float]]:
        """Get copy of ADXL355 accelerometer data (3 channels)."""
        with self._lock:
            return [ch.copy() for ch in self._adxl_accel_data]
    
    @property
    def gravity_mag_data(self) -> List[float]:
        """Get copy of gravity magnitude data."""
        with self._lock:
            return self._gravity_mag_data.copy()
    
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
        Calculate statistics for recent data.
        
        Args:
            window_size: Number of samples to include. Defaults to Config.STATS_WINDOW_SIZE.
            
        Returns:
            Dictionary with mean and std for each channel
        """
        window = window_size or Config.STATS_WINDOW_SIZE
        
        with self._lock:
            if len(self._time_data) < 10:
                return self._empty_stats()
            
            # Adjust window to available data
            window = min(window, len(self._time_data))
            start_idx = len(self._time_data) - window
            
            stats = {
                'mpu_accel': {'mean': [0.0, 0.0, 0.0], 'std': [0.0, 0.0, 0.0]},
                'mpu_gyro': {'mean': [0.0, 0.0, 0.0], 'std': [0.0, 0.0, 0.0]},
                'adxl_accel': {'mean': [0.0, 0.0, 0.0], 'std': [0.0, 0.0, 0.0]},
                'gravity': {'mean': 0.0, 'std': 0.0},
            }
            
            # Calculate for each channel - 使用 itertools.islice 处理 deque
            for i in range(3):
                if len(self._mpu_accel_data[i]) >= window:
                    data = list(itertools.islice(self._mpu_accel_data[i], start_idx, None))
                    stats['mpu_accel']['mean'][i] = float(np.mean(data))
                    stats['mpu_accel']['std'][i] = float(np.std(data))
                
                if len(self._mpu_gyro_data[i]) >= window:
                    data = list(itertools.islice(self._mpu_gyro_data[i], start_idx, None))
                    stats['mpu_gyro']['mean'][i] = float(np.mean(data))
                    stats['mpu_gyro']['std'][i] = float(np.std(data))
                
                if len(self._adxl_accel_data[i]) >= window:
                    data = list(itertools.islice(self._adxl_accel_data[i], start_idx, None))
                    stats['adxl_accel']['mean'][i] = float(np.mean(data))
                    stats['adxl_accel']['std'][i] = float(np.std(data))
            
            if len(self._gravity_mag_data) >= window:
                data = list(itertools.islice(self._gravity_mag_data, start_idx, None))
                stats['gravity']['mean'] = float(np.mean(data))
                stats['gravity']['std'] = float(np.std(data))
            
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
    
    @property
    def time_data(self) -> Deque[float]:
        """直接访问时间数据（兼容 DataProcessor，注意：非线程安全直接访问）"""
        return self._time_data
    
    @property
    def mpu_accel_data(self) -> List[Deque[float]]:
        """直接访问 MPU 加速度数据（兼容 DataProcessor）"""
        return self._mpu_accel_data
    
    @property
    def mpu_gyro_data(self) -> List[Deque[float]]:
        """直接访问 MPU 陀螺仪数据（兼容 DataProcessor）"""
        return self._mpu_gyro_data
    
    @property
    def adxl_accel_data(self) -> List[Deque[float]]:
        """直接访问 ADXL 加速度数据（兼容 DataProcessor）"""
        return self._adxl_accel_data
    
    @property
    def gravity_mag_data(self) -> Deque[float]:
        """直接访问重力数据（兼容 DataProcessor）"""
        return self._gravity_mag_data
    
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
        更新并返回统计信息（兼容 DataProcessor）
        
        Returns:
            包含所有统计信息的字典
        """
        with self._lock:
            if len(self._time_data) < 10:
                return self._get_empty_stats()
            
            window_size = min(Config.STATS_WINDOW_SIZE, len(self._time_data))
            start_idx = len(self._time_data) - window_size
            
            stats = self._get_empty_stats()
            
            # 计算各通道统计
            for i in range(3):
                if len(self._mpu_accel_data[i]) >= window_size:
                    data = list(itertools.islice(self._mpu_accel_data[i], start_idx, None))
                    stats["mpu_accel_mean"][i] = float(np.mean(data))
                    stats["mpu_accel_std"][i] = float(np.std(data))
                
                if len(self._adxl_accel_data[i]) >= window_size:
                    data = list(itertools.islice(self._adxl_accel_data[i], start_idx, None))
                    stats["adxl_accel_mean"][i] = float(np.mean(data))
                    stats["adxl_accel_std"][i] = float(np.std(data))
                
                if len(self._mpu_gyro_data[i]) >= window_size:
                    data = list(itertools.islice(self._mpu_gyro_data[i], start_idx, None))
                    stats["mpu_gyro_mean"][i] = float(np.mean(data))
                    stats["mpu_gyro_std"][i] = float(np.std(data))
            
            if len(self._gravity_mag_data) >= window_size:
                data = list(itertools.islice(self._gravity_mag_data, start_idx, None))
                stats["gravity_mean"] = float(np.mean(data))
                stats["gravity_std"] = float(np.std(data))
            
            self._stats_cache = stats
            self._stats_valid = True
            return stats
    
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
    
    @staticmethod
    def parse_sensor_data(data_string: str) -> Tuple[Optional[List[float]], Optional[List[float]], Optional[List[float]]]:
        """
        解析传感器数据字符串（从 DataProcessor 迁移）
        
        Args:
            data_string: 从串口接收的数据字符串，格式为逗号分隔的数字
        
        Returns:
            (mpu_accel, mpu_gyro, adxl_accel) 或 (None, None, None) 如果解析失败
        """
        try:
            parts = data_string.split(",")
            if len(parts) >= 9:
                values = []
                for part in parts[:9]:
                    try:
                        values.append(float(part.strip()))
                    except (ValueError, TypeError):
                        values.append(0.0)
                
                mpu_accel = values[0:3]
                mpu_gyro = values[3:6]
                adxl_accel = values[6:9]
                
                return mpu_accel, mpu_gyro, adxl_accel
        except Exception:
            # 数据解析失败（格式错误/无效数据），静默返回 None
            pass
        
        return None, None, None
