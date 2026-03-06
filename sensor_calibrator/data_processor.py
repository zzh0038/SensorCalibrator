"""
DataProcessor - 管理传感器数据的解析、存储和统计计算

职责：
- 管理数据缓冲区（时间、加速度、陀螺仪、重力）
- 解析传感器数据字符串
- 计算统计信息（均值、标准差）
- 提供数据访问接口
"""

import time
from typing import List, Tuple, Optional, Dict, Any
from collections import deque
import itertools
import numpy as np

from . import Config


class DataProcessor:
    """
    管理传感器数据的解析、存储和统计计算
    
    使用 deque 实现自动长度限制，避免内存泄漏
    """
    
    def __init__(self):
        """初始化数据处理器"""
        max_points = Config.MAX_DATA_POINTS
        
        # 数据缓冲区
        self.time_data: deque = deque(maxlen=max_points)
        self.mpu_accel_data: List[deque] = [deque(maxlen=max_points) for _ in range(3)]
        self.mpu_gyro_data: List[deque] = [deque(maxlen=max_points) for _ in range(3)]
        self.adxl_accel_data: List[deque] = [deque(maxlen=max_points) for _ in range(3)]
        self.gravity_mag_data: deque = deque(maxlen=max_points)
        
        # 统计信息
        self.stats_window_size = Config.STATS_WINDOW_SIZE
        self.real_time_stats = {
            "mpu_accel_mean": [0.0, 0.0, 0.0],
            "mpu_accel_std": [0.0, 0.0, 0.0],
            "adxl_accel_mean": [0.0, 0.0, 0.0],
            "adxl_accel_std": [0.0, 0.0, 0.0],
            "mpu_gyro_mean": [0.0, 0.0, 0.0],
            "mpu_gyro_std": [0.0, 0.0, 0.0],
            "gravity_mean": 0.0,
            "gravity_std": 0.0,
        }
        
        # 时间跟踪
        self.data_start_time: Optional[float] = None
        self.packet_count = 0
        self.expected_frequency = Config.EXPECTED_FREQUENCY
    
    def parse_sensor_data(self, data_string: str) -> Tuple[Optional[List[float]], Optional[List[float]], Optional[List[float]]]:
        """
        解析传感器数据字符串
        
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
            # 这是预期情况，串口数据可能包含噪声或不完整帧
            pass
        
        return None, None, None
    
    def process_packet(self, data_string: str) -> Optional[Dict[str, Any]]:
        """
        处理单个数据包
        
        Args:
            data_string: 原始数据字符串
        
        Returns:
            包含解析后数据的字典，或 None 如果解析失败
        """
        mpu_accel, mpu_gyro, adxl_accel = self.parse_sensor_data(data_string)
        
        if mpu_accel is None or mpu_gyro is None or adxl_accel is None:
            return None
        
        # 初始化时间基准
        if self.data_start_time is None:
            self.data_start_time = time.time()
        
        # 使用包计数计算时间
        current_relative_time = self.packet_count / self.expected_frequency
        self.packet_count += 1
        
        # 计算重力矢量模长
        gravity_mag = np.sqrt(
            mpu_accel[0] ** 2 + mpu_accel[1] ** 2 + mpu_accel[2] ** 2
        )
        
        # 存储数据
        self.time_data.append(current_relative_time)
        for i in range(3):
            self.mpu_accel_data[i].append(mpu_accel[i])
            self.mpu_gyro_data[i].append(mpu_gyro[i])
            self.adxl_accel_data[i].append(adxl_accel[i])
        self.gravity_mag_data.append(gravity_mag)
        
        return {
            'time': current_relative_time,
            'mpu_accel': mpu_accel,
            'mpu_gyro': mpu_gyro,
            'adxl_accel': adxl_accel,
            'gravity': gravity_mag,
        }
    
    def calculate_statistics(self, data_array, start_idx: Optional[int] = None, end_idx: Optional[int] = None) -> Tuple[float, float]:
        """
        计算统计信息（支持deque和list）- 优化版本
        
        优化点：
        - 避免将deque转换为list
        - 使用itertools.islice直接获取切片
        - 使用numpy.fromiter直接从迭代器创建数组
        
        Args:
            data_array: 数据数组（list 或 deque）
            start_idx: 起始索引
            end_idx: 结束索引
        
        Returns:
            (mean, std) 均值和标准差
        """
        # 处理空数据
        if not data_array or len(data_array) == 0:
            return 0.0, 0.0
        
        # 设置默认索引
        if start_idx is None:
            start_idx = 0
        if end_idx is None:
            end_idx = len(data_array)
        
        # 获取数据片段 - 根据类型选择最优方式
        if isinstance(data_array, deque):
            # 对于deque，使用islice避免完整转换
            # 计算实际结束位置
            actual_end = min(end_idx, len(data_array))
            count = actual_end - start_idx
            
            if count <= 0:
                return 0.0, 0.0
            
            # 使用islice获取数据，然后直接从迭代器创建numpy数组
            segment_iter = itertools.islice(data_array, start_idx, actual_end)
            segment = np.fromiter(segment_iter, dtype=float, count=count)
        else:
            # 对于list，使用切片（已经是高效的）
            if len(data_array) >= end_idx:
                segment = data_array[start_idx:end_idx]
            else:
                segment = data_array[start_idx:]
            
            if len(segment) == 0:
                return 0.0, 0.0
        
        # 使用numpy向量化计算
        mean_val = float(np.mean(segment))
        std_val = float(np.std(segment))
        
        return mean_val, std_val
    
    def update_statistics(self) -> Dict[str, Any]:
        """
        更新所有统计信息
        
        Returns:
            包含所有统计信息的字典
        """
        if len(self.time_data) < 10:  # 至少需要10个数据点
            return self.real_time_stats
        
        # 计算窗口大小
        window_size = min(self.stats_window_size, len(self.time_data))
        start_idx = len(self.time_data) - window_size
        
        # 更新MPU6050加速度计统计
        for i in range(3):
            if len(self.mpu_accel_data[i]) >= window_size:
                mean_val, std_val = self.calculate_statistics(
                    self.mpu_accel_data[i], start_idx
                )
                self.real_time_stats["mpu_accel_mean"][i] = mean_val
                self.real_time_stats["mpu_accel_std"][i] = std_val
        
        # 更新ADXL355加速度计统计
        for i in range(3):
            if len(self.adxl_accel_data[i]) >= window_size:
                mean_val, std_val = self.calculate_statistics(
                    self.adxl_accel_data[i], start_idx
                )
                self.real_time_stats["adxl_accel_mean"][i] = mean_val
                self.real_time_stats["adxl_accel_std"][i] = std_val
        
        # 更新MPU6050陀螺仪统计
        for i in range(3):
            if len(self.mpu_gyro_data[i]) >= window_size:
                mean_val, std_val = self.calculate_statistics(
                    self.mpu_gyro_data[i], start_idx
                )
                self.real_time_stats["mpu_gyro_mean"][i] = mean_val
                self.real_time_stats["mpu_gyro_std"][i] = std_val
        
        # 更新重力矢量统计
        if len(self.gravity_mag_data) >= window_size:
            mean_val, std_val = self.calculate_statistics(
                self.gravity_mag_data, start_idx
            )
            self.real_time_stats["gravity_mean"] = mean_val
            self.real_time_stats["gravity_std"] = std_val
        
        return self.real_time_stats
    
    def get_display_data(self, max_points: Optional[int] = None) -> Dict[str, Any]:
        """
        获取用于显示的数据
        
        Args:
            max_points: 最大数据点数，None 表示使用配置值
        
        Returns:
            包含时间序列数据的字典
        """
        if max_points is None:
            max_points = Config.DISPLAY_DATA_POINTS
        
        return {
            'time': list(self.time_data),
            'mpu_accel': [list(d) for d in self.mpu_accel_data],
            'adxl_accel': [list(d) for d in self.adxl_accel_data],
            'mpu_gyro': [list(d) for d in self.mpu_gyro_data],
            'gravity': list(self.gravity_mag_data),
        }
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """
        获取最新数据点
        
        Returns:
            最新数据点，或 None 如果没有数据
        """
        if not self.time_data:
            return None
        
        return {
            'time': self.time_data[-1],
            'mpu_accel': [d[-1] if d else 0.0 for d in self.mpu_accel_data],
            'mpu_gyro': [d[-1] if d else 0.0 for d in self.mpu_gyro_data],
            'adxl_accel': [d[-1] if d else 0.0 for d in self.adxl_accel_data],
            'gravity': self.gravity_mag_data[-1] if self.gravity_mag_data else 0.0,
        }
    
    def clear_all(self):
        """清空所有数据"""
        self.time_data.clear()
        for d in self.mpu_accel_data:
            d.clear()
        for d in self.mpu_gyro_data:
            d.clear()
        for d in self.adxl_accel_data:
            d.clear()
        self.gravity_mag_data.clear()
        
        # 重置统计
        self.real_time_stats = {
            "mpu_accel_mean": [0.0, 0.0, 0.0],
            "mpu_accel_std": [0.0, 0.0, 0.0],
            "adxl_accel_mean": [0.0, 0.0, 0.0],
            "adxl_accel_std": [0.0, 0.0, 0.0],
            "mpu_gyro_mean": [0.0, 0.0, 0.0],
            "mpu_gyro_std": [0.0, 0.0, 0.0],
            "gravity_mean": 0.0,
            "gravity_std": 0.0,
        }
        
        # 重置时间
        self.data_start_time = None
        self.packet_count = 0
    
    def get_data_count(self) -> int:
        """获取当前数据点数量"""
        return len(self.time_data)
    
    def has_data(self) -> bool:
        """检查是否有数据"""
        return len(self.time_data) > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        return self.real_time_stats.copy()
