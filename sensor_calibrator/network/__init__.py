"""
SensorCalibrator Network Module

网络模块，提供WiFi、MQTT、OTA、报警配置、阿里云MQTT和位置配置。
"""

from .alarm import (
    build_set_alarm_command,
    build_read_alarm_command,
    parse_alarm_response,
)

from .cloud_mqtt import (
    build_kns_command,
    build_cmq_command,
    build_aliyun_mqtt_command,
    build_local_mqtt_command,
    MqttMode,
    validate_product_key,
    validate_device_name,
    validate_device_secret,
    validate_mqtt_mode,
    get_mqtt_mode_description,
)

from .position_config import (
    build_po_command,
    validate_region_path,
    validate_building_type,
    validate_user_attribute,
    validate_device_name,
    parse_region_path,
    get_region_level_name,
    format_region_display,
    BUILDING_TYPE_OPTIONS,
    REGION_EXAMPLES,
)

__all__ = [
    # Alarm
    'build_set_alarm_command',
    'build_read_alarm_command',
    'parse_alarm_response',
    # Cloud MQTT (Aliyun)
    'build_kns_command',
    'build_cmq_command',
    'build_aliyun_mqtt_command',
    'build_local_mqtt_command',
    'MqttMode',
    'validate_product_key',
    'validate_device_name',
    'validate_device_secret',
    'validate_mqtt_mode',
    'get_mqtt_mode_description',
    # Position Config
    'build_po_command',
    'validate_region_path',
    'validate_building_type',
    'validate_user_attribute',
    'parse_region_path',
    'get_region_level_name',
    'format_region_display',
    'BUILDING_TYPE_OPTIONS',
    'REGION_EXAMPLES',
]
