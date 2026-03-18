"""
SensorCalibrator Serial Module

串口模块，提供串口管理和SS命令协议。
"""

from .protocol import (
    # SS 命令常量 (0-9)
    SS_START_STREAM,
    SS_START_CALIBRATION,
    SS_LOCAL_MODE,
    SS_GLOBAL_MODE,
    SS_STOP_STREAM,
    SS_CPU_MONITOR,
    SS_SENSOR_CALIBRATION,
    SS_SAVE_CONFIG,
    SS_GET_PROPERTIES,
    SS_RESTART_SENSOR,
    # SS 命令常量 (10-19)
    SS_RESTORE_DEFAULT,
    SS_SAVE_SENSOR_CONFIG,
    SS_READ_SENSOR_CONFIG,
    SS_BUZZER_LONG,
    SS_CHECK_UPGRADE,
    SS_AP_CONFIG_MODE,
    SS_TOGGLE_FILTER,
    SS_SWITCH_MQTT_MODE,
    SS_CAMERA_MODE,
    # SS 命令常量 (20-27)
    SS_GET_SENSOR_ATTRS,
    SS_MONITORING_MODE,
    SS_TIMELAPSE_MODE,
    SS_REBOOT_CAMERA_SLAVE,
    SS_START_CAMERA_STREAM,
    SS_TAKE_PHOTO,
    SS_FORCE_CAMERA_OTA,
    SS_DEACTIVATE_SENSOR,
    # CA 命令常量
    CA_START_PUSH_STREAM,
    CA_TAKE_PHOTO,
    CA_REBOOT_CAMERA_MODULE,
    CA_FORCE_OTA_UPGRADE,
    # 基础构建函数
    build_ss_command,
    # 基础 SS 命令 (0-9)
    build_ss0_start_stream,
    build_ss1_start_calibration,
    build_ss2_local_mode,
    build_ss3_global_mode,
    build_ss4_stop_stream,
    build_ss5_cpu_monitor,
    build_ss6_sensor_calibration,
    build_ss7_save_config,
    build_ss8_get_properties,
    build_ss9_restart_sensor,
    # 存储和配置命令 (11-19)
    build_ss11_restore_default,
    build_ss12_save_sensor_config,
    build_ss13_read_sensor_config,
    build_ss14_buzzer_long,
    build_ss15_check_upgrade,
    build_ss16_ap_config_mode,
    build_ss17_toggle_filter,
    build_ss18_switch_mqtt_mode,
    build_ss19_camera_mode,
    # 监测和相机命令 (20-27)
    build_ss20_get_sensor_attrs,
    build_ss21_monitoring_mode,
    build_ss22_timelapse_mode,
    build_ss23_reboot_camera_slave,
    build_ss24_start_camera_stream,
    build_ss25_take_photo,
    build_ss26_force_camera_ota,
    build_ss27_deactivate_sensor,
    # CA 命令构建函数
    build_ca_command,
    build_ca1_start_push_stream,
    build_ca2_take_photo,
    build_ca9_reboot_camera_module,
    build_ca10_force_ota_upgrade,
    # 响应解析
    parse_ss_response,
    # 命令描述
    COMMAND_DESCRIPTIONS,
    CA_COMMAND_DESCRIPTIONS,
)

__all__ = [
    # SS 命令常量 (0-9)
    'SS_START_STREAM',
    'SS_START_CALIBRATION',
    'SS_LOCAL_MODE',
    'SS_GLOBAL_MODE',
    'SS_STOP_STREAM',
    'SS_CPU_MONITOR',
    'SS_SENSOR_CALIBRATION',
    'SS_SAVE_CONFIG',
    'SS_GET_PROPERTIES',
    'SS_RESTART_SENSOR',
    # SS 命令常量 (10-19)
    'SS_RESTORE_DEFAULT',
    'SS_SAVE_SENSOR_CONFIG',
    'SS_READ_SENSOR_CONFIG',
    'SS_BUZZER_LONG',
    'SS_CHECK_UPGRADE',
    'SS_AP_CONFIG_MODE',
    'SS_TOGGLE_FILTER',
    'SS_SWITCH_MQTT_MODE',
    'SS_CAMERA_MODE',
    # SS 命令常量 (20-27)
    'SS_GET_SENSOR_ATTRS',
    'SS_MONITORING_MODE',
    'SS_TIMELAPSE_MODE',
    'SS_REBOOT_CAMERA_SLAVE',
    'SS_START_CAMERA_STREAM',
    'SS_TAKE_PHOTO',
    'SS_FORCE_CAMERA_OTA',
    'SS_DEACTIVATE_SENSOR',
    # CA 命令常量
    'CA_START_PUSH_STREAM',
    'CA_TAKE_PHOTO',
    'CA_REBOOT_CAMERA_MODULE',
    'CA_FORCE_OTA_UPGRADE',
    # 基础构建函数
    'build_ss_command',
    # 基础 SS 命令 (0-9)
    'build_ss0_start_stream',
    'build_ss1_start_calibration',
    'build_ss2_local_mode',
    'build_ss3_global_mode',
    'build_ss4_stop_stream',
    'build_ss5_cpu_monitor',
    'build_ss6_sensor_calibration',
    'build_ss7_save_config',
    'build_ss8_get_properties',
    'build_ss9_restart_sensor',
    # 存储和配置命令 (11-19)
    'build_ss11_restore_default',
    'build_ss12_save_sensor_config',
    'build_ss13_read_sensor_config',
    'build_ss14_buzzer_long',
    'build_ss15_check_upgrade',
    'build_ss16_ap_config_mode',
    'build_ss17_toggle_filter',
    'build_ss18_switch_mqtt_mode',
    'build_ss19_camera_mode',
    # 监测和相机命令 (20-27)
    'build_ss20_get_sensor_attrs',
    'build_ss21_monitoring_mode',
    'build_ss22_timelapse_mode',
    'build_ss23_reboot_camera_slave',
    'build_ss24_start_camera_stream',
    'build_ss25_take_photo',
    'build_ss26_force_camera_ota',
    'build_ss27_deactivate_sensor',
    # CA 命令构建函数
    'build_ca_command',
    'build_ca1_start_push_stream',
    'build_ca2_take_photo',
    'build_ca9_reboot_camera_module',
    'build_ca10_force_ota_upgrade',
    # 响应解析
    'parse_ss_response',
    # 命令描述
    'COMMAND_DESCRIPTIONS',
    'CA_COMMAND_DESCRIPTIONS',
]
