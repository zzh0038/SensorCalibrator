"""
SensorCalibrator Package

A sensor calibration application for MPU6050 and ADXL355 sensors.
"""

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

__all__ = [
    'Config',
    'SerialConfig',
    'UIConfig',
    'CalibrationConfig',
    'SensorDataBuffer',
    'MAX_DATA_POINTS',
    'DISPLAY_DATA_POINTS',
    'STATS_WINDOW_SIZE',
    'UPDATE_INTERVAL_MS',
    'GRAVITY_CONSTANT',
]


def validate_ssid(ssid: str) -> tuple:
    """Validate WiFi SSID."""
    if not ssid:
        return False, "SSID cannot be empty"
    if len(ssid) > 32:
        return False, "SSID too long (max 32 characters)"
    return True, ""


def validate_password(password: str) -> tuple:
    """Validate WiFi/Network password."""
    if len(password) > 64:
        return False, "Password too long (max 64 characters)"
    return True, ""


def validate_port(port: str) -> tuple:
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


def validate_url(url: str) -> tuple:
    """Validate URL format."""
    if not url:
        return True, ""
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "URL must start with http:// or https://"
    return True, ""
