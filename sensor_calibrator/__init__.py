"""
SensorCalibrator Package

A sensor calibration application for MPU6050 and ADXL355 sensors.
"""

from typing import Tuple

from .config import (
    Config,
    SerialConfig,
    UIConfig,
    CalibrationConfig,
    # Backward compatibility
    MAX_DATA_POINTS,
    DISPLAY_DATA_POINTS,
    STATS_WINDOW_SIZE,
    UPDATE_INTERVAL_MS,
    GRAVITY_CONSTANT,
)
from .data_buffer import SensorDataBuffer

# 默认导出 SensorDataBuffer 作为 DataProcessor 的替代品
# DataProcessor 已弃用，将在未来版本中移除
DataProcessor = SensorDataBuffer
from .ring_buffer import RingBuffer, QueueAdapter
from .log_throttler import LogThrottler, CountingLogThrottler
from .chart_manager import ChartManager
from .ui_manager import UIManager
from .data_processor import DataProcessor
from .serial_manager import SerialManager
from .network_manager import NetworkManager
from .calibration_workflow import CalibrationWorkflow
from .activation_workflow import ActivationWorkflow

__all__ = [
    'Config',
    'SerialConfig',
    'UIConfig',
    'CalibrationConfig',
    'SensorDataBuffer',
    'RingBuffer',
    'LogThrottler',
    'CountingLogThrottler',
    'ChartManager',
    'UIManager',
    'DataProcessor',
    'SerialManager',
    'NetworkManager',
    'CalibrationWorkflow',
    'ActivationWorkflow',
    'MAX_DATA_POINTS',
    'DISPLAY_DATA_POINTS',
    'STATS_WINDOW_SIZE',
    'UPDATE_INTERVAL_MS',
    'GRAVITY_CONSTANT',
]


def validate_ssid(ssid: str) -> Tuple[bool, str]:
    """Validate WiFi SSID."""
    if not ssid:
        return False, "SSID cannot be empty"
    if len(ssid) > 32:
        return False, "SSID too long (max 32 characters)"
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate WiFi/Network password."""
    if len(password) > 64:
        return False, "Password too long (max 64 characters)"
    return True, ""


def validate_port(port: str) -> Tuple[bool, str]:
    """Validate network port number."""
    if not port:
        return False, "Port cannot be empty"
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            return False, "Port must be between 1 and 65535"
    except ValueError:
        return False, "Port must be a number"
    return True, ""


def validate_url(url: str) -> Tuple[bool, str]:
    """Validate URL format."""
    if not url:
        return True, ""
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "URL must start with http:// or https://"
    return True, ""
