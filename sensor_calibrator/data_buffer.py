"""
Sensor Data Buffer Module

Manages storage, slicing, and statistics for sensor data streams.
Thread-safe operations for use with concurrent data acquisition.
"""

import threading
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

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
        
        # Data storage
        self._time_data: List[float] = []
        self._mpu_accel_data: List[List[float]] = [[], [], []]
        self._mpu_gyro_data: List[List[float]] = [[], [], []]
        self._adxl_accel_data: List[List[float]] = [[], [], []]
        self._gravity_mag_data: List[float] = []
        
        # Statistics cache
        self._stats_cache: Dict[str, Any] = {}
        self._stats_valid = False
    
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
            
            # Limit size if needed
            self._enforce_size_limit()
            self._stats_valid = False
    
    def _enforce_size_limit(self) -> None:
        """Remove oldest data if buffer exceeds max size."""
        current_len = len(self._time_data)
        if current_len > self._max_points:
            # Calculate start index for retention
            start_idx = current_len - self._max_points
            
            # Slice all data arrays
            self._time_data = self._time_data[start_idx:]
            self._gravity_mag_data = self._gravity_mag_data[start_idx:]
            
            for i in range(3):
                if len(self._mpu_accel_data[i]) > self._max_points:
                    self._mpu_accel_data[i] = self._mpu_accel_data[i][start_idx:]
                if len(self._mpu_gyro_data[i]) > self._max_points:
                    self._mpu_gyro_data[i] = self._mpu_gyro_data[i][start_idx:]
                if len(self._adxl_accel_data[i]) > self._max_points:
                    self._adxl_accel_data[i] = self._adxl_accel_data[i][start_idx:]
    
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
            
            start = -n if n > 0 else 0
            return {
                'time': self._time_data[start:],
                'mpu_accel': [ch[start:] for ch in self._mpu_accel_data],
                'mpu_gyro': [ch[start:] for ch in self._mpu_gyro_data],
                'adxl_accel': [ch[start:] for ch in self._adxl_accel_data],
                'gravity': self._gravity_mag_data[start:],
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
            
            # Calculate for each channel
            for i in range(3):
                if len(self._mpu_accel_data[i]) >= window:
                    data = self._mpu_accel_data[i][start_idx:]
                    stats['mpu_accel']['mean'][i] = float(np.mean(data))
                    stats['mpu_accel']['std'][i] = float(np.std(data))
                
                if len(self._mpu_gyro_data[i]) >= window:
                    data = self._mpu_gyro_data[i][start_idx:]
                    stats['mpu_gyro']['mean'][i] = float(np.mean(data))
                    stats['mpu_gyro']['std'][i] = float(np.std(data))
                
                if len(self._adxl_accel_data[i]) >= window:
                    data = self._adxl_accel_data[i][start_idx:]
                    stats['adxl_accel']['mean'][i] = float(np.mean(data))
                    stats['adxl_accel']['std'][i] = float(np.std(data))
            
            if len(self._gravity_mag_data) >= window:
                data = self._gravity_mag_data[start_idx:]
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
            self._mpu_accel_data = [[], [], []]
            self._mpu_gyro_data = [[], [], []]
            self._adxl_accel_data = [[], [], []]
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
            self._enforce_size_limit()
