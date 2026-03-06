"""
SensorCalibrator Configuration Module

Centralized configuration constants for the Sensor Calibrator application.
All timing values are in seconds unless otherwise specified.
"""

from typing import Final


class Config:
    """Main configuration container."""

    # =========================================================================
    # Performance Optimization Switches
    # =========================================================================
    ENABLE_BLIT_OPTIMIZATION: Final[bool] = True  # Enable blit for faster rendering
    ENABLE_WINDOW_MOVE_PAUSE: Final[bool] = True  # Pause updates during window move
    ENABLE_DATA_DECIMATION: Final[bool] = True  # Enable data sampling for display

    # =========================================================================
    # Data Management
    # =========================================================================
    MAX_DATA_POINTS: Final[int] = 2000  # Maximum data points to retain
    DISPLAY_DATA_POINTS: Final[int] = 200  # Points to display on charts
    STATS_WINDOW_SIZE: Final[int] = 100  # Samples for statistics calculation
    MAX_QUEUE_SIZE: Final[int] = 2000  # Maximum data queue size
    MAX_GUI_UPDATE_BATCH: Final[int] = 100  # Max packets processed per GUI update cycle

    # =========================================================================
    # Timing (seconds)
    # =========================================================================
    UPDATE_INTERVAL_MS: Final[int] = 100  # GUI update interval in milliseconds (10 FPS)
    CHART_UPDATE_INTERVAL: Final[float] = 0.1  # Chart refresh rate (10 FPS)
    STATS_UPDATE_INTERVAL: Final[float] = 1.0  # Statistics update interval (1 FPS)
    Y_LIMIT_UPDATE_INTERVAL: Final[float] = 0.5  # Y-axis limit update interval
    WINDOW_MOVE_PAUSE_DELAY: Final[int] = (
        200  # ms to wait after window move before resuming
    )

    # Serial timing
    SERIAL_TIMEOUT: Final[float] = 0.1  # Serial read timeout
    SERIAL_WRITE_TIMEOUT: Final[float] = 1.0  # Serial write timeout
    SERIAL_CLEANUP_DELAY: Final[float] = 0.5  # Delay for serial cleanup
    SERIAL_STABILITY_DELAY: Final[float] = 0.5  # Delay for serial port stability

    # Command/response timing
    COMMAND_DELAY: Final[float] = 2.0  # Delay after sending commands
    RESPONSE_TIMEOUT: Final[float] = 5.0  # Timeout for device responses
    BUFFER_CLEAR_DELAY: Final[float] = 0.5  # Delay for buffer clearing

    # Threading
    THREAD_JOIN_TIMEOUT: Final[float] = 2.0  # Timeout for thread join
    THREAD_ERROR_DELAY: Final[float] = 0.1  # Delay after thread errors
    DATA_STREAM_STOP_DELAY: Final[float] = 1.0  # Delay when stopping data stream

    # Polling intervals
    QUICK_SLEEP: Final[float] = 0.01  # Short sleep for polling
    PARSE_RETRY_DELAY: Final[float] = 0.05  # Delay between parse retries

    # =========================================================================
    # Calibration
    # =========================================================================
    CALIBRATION_SAMPLES: Final[int] = 100  # Samples per calibration position
    MIN_CALIBRATION_SAMPLE_RATIO: Final[float] = 0.1  # Min ratio of required samples (10%)
    MONITORING_SAMPLES_NEEDED: Final[int] = 300  # Samples for monitoring
    MONITORING_DURATION: Final[int] = 3  # Monitoring duration in seconds
    EXPECTED_FREQUENCY: Final[int] = 100  # Expected data frequency (Hz)
    GRAVITY_CONSTANT: Final[float] = 9.8015  # Standard gravity (m/s²)

    # =========================================================================
    # Serial Communication
    # =========================================================================
    MAX_CONSECUTIVE_ERRORS: Final[int] = 5  # Max errors before stopping
    BAUDRATE_DEFAULT: Final[int] = 115200  # Default baud rate

    # =========================================================================
    # UI Configuration
    # =========================================================================
    WINDOW_WIDTH: Final[int] = 1920
    WINDOW_HEIGHT: Final[int] = 1080
    LEFT_PANEL_WIDTH: Final[int] = 430
    LOG_HEIGHT: Final[int] = 8  # Lines in log text

    # Font sizes
    FONT_TITLE: Final[int] = 12
    FONT_NORMAL: Final[int] = 9
    FONT_SMALL: Final[int] = 8
    FONT_STATS: Final[int] = 8

    # Chart configuration
    CHART_TIME_WINDOW: Final[float] = 10.0  # Seconds to display on time charts
    CHART_Y_PADDING: Final[float] = 2.0  # Y-axis padding
    CHART_MIN_Y_RANGE: Final[float] = 1.0  # Minimum Y-axis range
    CHART_DECIMATION_FACTOR: Final[int] = 2  # Data decimation factor for display

    # =========================================================================
    # File Paths
    # =========================================================================
    DEFAULT_PROPERTIES_FILE: Final[str] = "sensor_properties.json"
    DEFAULT_CALIBRATION_FILE: Final[str] = "calibration_params.json"

    # =========================================================================
    # Coordinate Modes
    # =========================================================================
    COORD_MODE_LOCAL: Final[int] = 2  # SS:2 - Local coordinate mode
    COORD_MODE_GLOBAL: Final[int] = 3  # SS:3 - Global coordinate mode

    # =========================================================================
    # SS Command IDs
    # =========================================================================
    CMD_START_STREAM: Final[int] = 0  # SS:0 - Start data stream
    CMD_START_CALIBRATION: Final[int] = 1  # SS:1 - Start calibration stream
    CMD_COORD_LOCAL: Final[int] = 2  # SS:2 - Local coordinates
    CMD_COORD_GLOBAL: Final[int] = 3  # SS:3 - Global coordinates
    CMD_STOP_STREAM: Final[int] = 4  # SS:4 - Stop stream
    CMD_SAVE_CONFIG: Final[int] = 7  # SS:7 - Save configuration to sensor
    CMD_GET_PROPERTIES: Final[int] = 8  # SS:8 - Get sensor properties
    CMD_RESTART_SENSOR: Final[int] = 9  # SS:9 - Restart sensor

    # =========================================================================
    # Network Configuration Defaults
    # =========================================================================
    MQTT_DEFAULT_PORT: Final[str] = "1883"  # Default MQTT broker port
    MQTT_DEFAULT_QOS: Final[int] = 0  # Default MQTT QoS level
    WIFI_MAX_SSID_LENGTH: Final[int] = 32  # Maximum SSID length
    WIFI_MAX_PASSWORD_LENGTH: Final[int] = 64  # Maximum WiFi password length
    NETWORK_COMMAND_TIMEOUT: Final[float] = 5.0  # Network command timeout (seconds)
    NETWORK_RETRY_COUNT: Final[int] = 3  # Number of retries for network operations

    # =========================================================================
    # Alarm Threshold Configuration
    # =========================================================================
    ALARM_THRESHOLD_ACCEL_MIN: Final[float] = 0.1  # Minimum accel threshold (m/s²)
    ALARM_THRESHOLD_ACCEL_MAX: Final[float] = 10.0  # Maximum accel threshold (m/s²)
    ALARM_THRESHOLD_ACCEL_DEFAULT: Final[float] = 0.2  # Default accel threshold (m/s²)
    ALARM_THRESHOLD_GYRO_MIN: Final[float] = 0.1  # Minimum gyro threshold (°)
    ALARM_THRESHOLD_GYRO_MAX: Final[float] = 45.0  # Maximum gyro threshold (°)
    ALARM_THRESHOLD_GYRO_DEFAULT: Final[float] = 0.2  # Default gyro threshold (°)


class SerialConfig:
    """Serial communication specific configuration."""

    TIMEOUT: Final[float] = 0.1
    WRITE_TIMEOUT: Final[float] = 1.0
    BAUD_RATES: Final[list] = [9600, 19200, 38400, 57600, 115200]
    DEFAULT_BAUD: Final[int] = 115200

    # Flow control
    RTSCTS: Final[bool] = False
    DSRDTR: Final[bool] = False

    # Timing
    CONNECT_DELAY: Final[float] = 0.5
    DISCONNECT_DELAY: Final[float] = 0.1
    RESET_DELAY: Final[float] = 0.5

    # Read loop
    READ_SLEEP_DATA: Final[float] = 0.001  # When data available
    READ_SLEEP_IDLE: Final[float] = 0.01  # When no data
    READ_ERROR_SLEEP: Final[float] = 0.05  # After read error


class UIConfig:
    """UI-specific configuration."""

    # Window
    TITLE: Final[str] = "MPU6050 & ADXL355 Sensor Calibration System"
    SCALING_FACTOR: Final[float] = 1.2
    WINDOW_WIDTH: Final[int] = 1920
    WINDOW_HEIGHT: Final[int] = 1080

    # Layout
    LEFT_PANEL_WIDTH: Final[int] = 430
    PAD_X: Final[int] = 5
    PAD_Y: Final[int] = 5

    # Colors
    COLOR_OK: Final[str] = "green"
    COLOR_ERROR: Final[str] = "red"
    COLOR_INFO: Final[str] = "blue"
    COLOR_WARNING: Final[str] = "orange"

    # Chart colors (RGB hex)
    CHART_COLOR_X: Final[str] = "#ff4444"  # Red
    CHART_COLOR_Y: Final[str] = "#44ff44"  # Green
    CHART_COLOR_Z: Final[str] = "#4444ff"  # Blue
    CHART_COLOR_GRAVITY: Final[str] = "#ff9900"  # Orange


class CalibrationConfig:
    """Calibration-specific configuration."""

    NUM_POSITIONS: Final[int] = 6
    SAMPLES_PER_POSITION: Final[int] = 100
    TIMEOUT_PER_POSITION: Final[float] = 10.0

    # Position names
    POSITION_NAMES: Final[list] = [
        "+X axis down (X = +9.81 m/s²)",
        "-X axis down (X = -9.81 m/s²)",
        "+Y axis down (Y = +9.81 m/s²)",
        "-Y axis down (Y = -9.81 m/s²)",
        "+Z axis down (Z = +9.81 m/s²)",
        "-Z axis down (Z = -9.81 m/s²)",
    ]

    # Scale calculation
    MIN_DELTA: Final[float] = 1e-6  # Minimum delta for scale calc
    DEFAULT_SCALE: Final[float] = 1.0  # Default scale factor


# Backward compatibility aliases
MAX_DATA_POINTS = Config.MAX_DATA_POINTS
DISPLAY_DATA_POINTS = Config.DISPLAY_DATA_POINTS
STATS_WINDOW_SIZE = Config.STATS_WINDOW_SIZE
UPDATE_INTERVAL_MS = Config.UPDATE_INTERVAL_MS
GRAVITY_CONSTANT = Config.GRAVITY_CONSTANT
