"""
SensorCalibrator Package

A sensor calibration application for MPU6050 and ADXL355 sensors.
"""

from typing import TYPE_CHECKING, Tuple

# 使用 TYPE_CHECKING 避免循环导入
# 在静态类型检查时导入，运行时不导入
if TYPE_CHECKING:
    from .config import Config, SerialConfig, UIConfig, CalibrationConfig
    from .data_buffer import SensorDataBuffer
    from .ring_buffer import RingBuffer, QueueAdapter
    from .log_throttler import LogThrottler, CountingLogThrottler
    from .chart_manager import ChartManager
    from .ui_manager import UIManager
    from .data_processor import DataProcessor
    from .serial_manager import SerialManager
    from .network_manager import NetworkManager
    from .calibration_workflow import CalibrationWorkflow
    from .activation_workflow import ActivationWorkflow


def __getattr__(name: str):
    """懒加载模块成员，避免循环导入"""
    import sys

    # 映射名称到模块
    _module_map = {
        "Config": (".config", "Config"),
        "SerialConfig": (".config", "SerialConfig"),
        "UIConfig": (".config", "UIConfig"),
        "CalibrationConfig": (".config", "CalibrationConfig"),
        "MAX_DATA_POINTS": (".config", "MAX_DATA_POINTS"),
        "DISPLAY_DATA_POINTS": (".config", "DISPLAY_DATA_POINTS"),
        "STATS_WINDOW_SIZE": (".config", "STATS_WINDOW_SIZE"),
        "UPDATE_INTERVAL_MS": (".config", "UPDATE_INTERVAL_MS"),
        "GRAVITY_CONSTANT": (".config", "GRAVITY_CONSTANT"),
        "SensorDataBuffer": (".data_buffer", "SensorDataBuffer"),
        "DataProcessor": (".data_processor", "DataProcessor"),
        "RingBuffer": (".ring_buffer", "RingBuffer"),
        "QueueAdapter": (".ring_buffer", "QueueAdapter"),
        "LogThrottler": (".log_throttler", "LogThrottler"),
        "CountingLogThrottler": (".log_throttler", "CountingLogThrottler"),
        "ChartManager": (".chart_manager", "ChartManager"),
        "UIManager": (".ui_manager", "UIManager"),
        "SerialManager": (".serial_manager", "SerialManager"),
        "NetworkManager": (".network_manager", "NetworkManager"),
        "CalibrationWorkflow": (".calibration_workflow", "CalibrationWorkflow"),
        "ActivationWorkflow": (".activation_workflow", "ActivationWorkflow"),
    }

    if name in _module_map:
        import importlib

        module_name, attr_name = _module_map[name]
        module = importlib.import_module(module_name, package="sensor_calibrator")
        return getattr(module, attr_name)

    raise AttributeError(f"module 'sensor_calibrator' has no attribute {name!r}")


__all__ = [
    "Config",
    "SerialConfig",
    "UIConfig",
    "CalibrationConfig",
    "SensorDataBuffer",
    "RingBuffer",
    "QueueAdapter",
    "LogThrottler",
    "CountingLogThrottler",
    "ChartManager",
    "UIManager",
    "DataProcessor",
    "SerialManager",
    "NetworkManager",
    "CalibrationWorkflow",
    "ActivationWorkflow",
    "MAX_DATA_POINTS",
    "DISPLAY_DATA_POINTS",
    "STATS_WINDOW_SIZE",
    "UPDATE_INTERVAL_MS",
    "GRAVITY_CONSTANT",
    "validate_ssid",
    "validate_password",
    "validate_port",
    "validate_url",
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
