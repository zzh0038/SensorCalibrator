"""
SensorCalibrator Camera Module

相机模块，提供相机控制、视频流和拍照功能。
"""

from .camera_control import (
    # 命令构建函数
    build_ss19_camera_mode,
    build_ss21_monitoring_mode,
    build_ss22_timelapse_mode,
    build_ss23_reboot_camera_slave,
    build_ss25_take_photo,
    build_ss26_force_camera_ota,
    build_ca2_take_photo,
    build_ca9_reboot_camera_module,
    build_ca10_force_ota_upgrade,
    # 状态管理
    CameraMode,
    CameraStateManager,
    CameraController,
)

from .stream import (
    # 命令构建函数
    build_ss24_start_camera_stream,
    build_ca1_start_push_stream,
    # 流管理
    StreamType,
    StreamState,
    StreamManager,
    # 便捷函数
    is_stream_command,
    get_stream_type,
)

__all__ = [
    # Camera Control Commands
    'build_ss19_camera_mode',
    'build_ss21_monitoring_mode',
    'build_ss22_timelapse_mode',
    'build_ss23_reboot_camera_slave',
    'build_ss25_take_photo',
    'build_ss26_force_camera_ota',
    'build_ca2_take_photo',
    'build_ca9_reboot_camera_module',
    'build_ca10_force_ota_upgrade',
    # Stream Commands
    'build_ss24_start_camera_stream',
    'build_ca1_start_push_stream',
    # Enums
    'CameraMode',
    'StreamType',
    'StreamState',
    # Managers
    'CameraStateManager',
    'CameraController',
    'StreamManager',
    # Helpers
    'is_stream_command',
    'get_stream_type',
]
