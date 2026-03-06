"""
SensorCalibrator Serial Module

串口模块，提供串口管理和SS命令协议。
"""

from .protocol import (
    SS_START_STREAM,
    SS_START_CALIBRATION,
    SS_LOCAL_MODE,
    SS_GLOBAL_MODE,
    SS_STOP_STREAM,
    SS_SAVE_CONFIG,
    SS_GET_PROPERTIES,
    SS_RESTART_SENSOR,
    build_ss0_start_stream,
    build_ss1_start_calibration,
    build_ss2_local_mode,
    build_ss3_global_mode,
    build_ss4_stop_stream,
    build_ss7_save_config,
    build_ss8_get_properties,
    build_ss9_restart_sensor,
    parse_ss_response,
    COMMAND_DESCRIPTIONS,
)

__all__ = [
    'SS_START_STREAM',
    'SS_START_CALIBRATION',
    'SS_LOCAL_MODE',
    'SS_GLOBAL_MODE',
    'SS_STOP_STREAM',
    'SS_SAVE_CONFIG',
    'SS_GET_PROPERTIES',
    'SS_RESTART_SENSOR',
    'build_ss0_start_stream',
    'build_ss1_start_calibration',
    'build_ss2_local_mode',
    'build_ss3_global_mode',
    'build_ss4_stop_stream',
    'build_ss7_save_config',
    'build_ss8_get_properties',
    'build_ss9_restart_sensor',
    'parse_ss_response',
    'COMMAND_DESCRIPTIONS',
]
