"""
SensorCalibrator System Module

系统模块，提供系统级配置管理，包括恢复默认、保存配置、反激活等。
"""

from .config_manager import (
    ConfigAction,
    DANGEROUS_ACTIONS,
    SystemConfigManager,
    build_ss11_restore_default,
    build_ss12_save_sensor_config,
    build_ss13_read_sensor_config,
    build_ss27_deactivate,
    get_dangerous_action_info,
    is_dangerous_action,
    format_config_response,
    build_full_save_sequence,
    build_factory_reset_sequence,
)

from .cpu_monitor import (
    build_ss5_cpu_monitor,
    parse_cpu_monitor_response,
    format_cpu_info,
)

from .sensor_cal import (
    build_ss6_sensor_calibration,
    parse_sensor_cal_response,
    SensorCalState,
    SensorCalibrationTracker,
)

from .system_control import (
    build_ss14_buzzer_long,
    build_ss15_check_upgrade,
    build_ss16_ap_config_mode,
    build_ss18_switch_mqtt_mode,
    build_ss18_local_mode,
    build_ss18_aliyun_mode,
    SystemController,
)

__all__ = [
    # Config Manager
    'ConfigAction',
    'DANGEROUS_ACTIONS',
    'SystemConfigManager',
    'build_ss11_restore_default',
    'build_ss12_save_sensor_config',
    'build_ss13_read_sensor_config',
    'build_ss27_deactivate',
    'get_dangerous_action_info',
    'is_dangerous_action',
    'format_config_response',
    'build_full_save_sequence',
    'build_factory_reset_sequence',
    # CPU Monitor (Sprint 2)
    'build_ss5_cpu_monitor',
    'parse_cpu_monitor_response',
    'format_cpu_info',
    # Sensor Calibration (Sprint 2)
    'build_ss6_sensor_calibration',
    'parse_sensor_cal_response',
    'SensorCalState',
    'SensorCalibrationTracker',
    # System Control (Sprint 2)
    'build_ss14_buzzer_long',
    'build_ss15_check_upgrade',
    'build_ss16_ap_config_mode',
    'build_ss18_switch_mqtt_mode',
    'build_ss18_local_mode',
    'build_ss18_aliyun_mode',
    'SystemController',
]
