"""
SensorCalibrator Cloud MQTT Module

阿里云MQTT配置管理。
提供 SET:KNS 和 SET:CMQ 命令构建功能。
"""

import re
from typing import Tuple


# MQTT 模式常量
class MqttMode:
    """MQTT模式常量"""
    LOCAL = 1           # 局域网模式
    ALIYUN = 10         # 阿里云模式


# 阿里云三元组验证规则
PRODUCT_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9]{11,20}$')
DEVICE_NAME_MAX_LENGTH = 64
DEVICE_SECRET_LENGTH = 32


def validate_product_key(product_key: str) -> Tuple[bool, str]:
    """
    验证阿里云 ProductKey
    
    Args:
        product_key: 产品密钥
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not product_key:
        return False, "ProductKey cannot be empty"
    
    product_key = product_key.strip()
    
    if len(product_key) < 11 or len(product_key) > 20:
        return False, f"ProductKey length must be 11-20 characters, got {len(product_key)}"
    
    if not PRODUCT_KEY_PATTERN.match(product_key):
        return False, "ProductKey must contain only alphanumeric characters"
    
    return True, ""


def validate_device_name(device_name: str) -> Tuple[bool, str]:
    """
    验证阿里云 DeviceName
    
    Args:
        device_name: 设备名称
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not device_name:
        return False, "DeviceName cannot be empty"
    
    device_name = device_name.strip()
    
    if len(device_name) > DEVICE_NAME_MAX_LENGTH:
        return False, f"DeviceName too long (max {DEVICE_NAME_MAX_LENGTH} chars)"
    
    # 设备名通常允许字母、数字、下划线、连字符
    if not re.match(r'^[a-zA-Z0-9_-]+$', device_name):
        return False, "DeviceName must contain only alphanumeric, underscore, or hyphen"
    
    return True, ""


def validate_device_secret(device_secret: str) -> Tuple[bool, str]:
    """
    验证阿里云 DeviceSecret
    
    Args:
        device_secret: 设备密钥
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not device_secret:
        return False, "DeviceSecret cannot be empty"
    
    device_secret = device_secret.strip()
    
    # DeviceSecret 通常是 32 字符的十六进制字符串
    if len(device_secret) != DEVICE_SECRET_LENGTH:
        return False, f"DeviceSecret must be exactly {DEVICE_SECRET_LENGTH} characters"
    
    if not re.match(r'^[a-fA-F0-9]+$', device_secret):
        return False, "DeviceSecret must be hexadecimal characters only"
    
    return True, ""


def build_kns_command(
    product_key: str,
    device_name: str,
    device_secret: str
) -> Tuple[bool, str, str]:
    """
    构建 SET:KNS 命令 - 配置阿里云互联网MQTT
    
    格式: SET:KNS,<product_key>,<device_name>,<device_secret>
    
    Args:
        product_key: 产品密钥 (ProductKey)
        device_name: 设备名称 (DeviceName)
        device_secret: 设备密钥 (DeviceSecret)
        
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_kns_command(
        ...     "ha9yyoY8xfJ",
        ...     "ESP23_BHM_000003",
        ...     "cfde2faeaf725ce185f16781ae58f6fc"
        ... )
        (True, "", "SET:KNS,ha9yyoY8xfJ,ESP23_BHM_000003,cfde2faeaf725ce185f16781ae58f6fc")
    """
    # 验证 ProductKey
    valid, error = validate_product_key(product_key)
    if not valid:
        return False, f"Invalid ProductKey: {error}", ""
    
    # 验证 DeviceName
    valid, error = validate_device_name(device_name)
    if not valid:
        return False, f"Invalid DeviceName: {error}", ""
    
    # 验证 DeviceSecret
    valid, error = validate_device_secret(device_secret)
    if not valid:
        return False, f"Invalid DeviceSecret: {error}", ""
    
    # 构建命令
    cmd = f"SET:KNS,{product_key.strip()},{device_name.strip()},{device_secret.strip().lower()}"
    return True, "", cmd


def validate_mqtt_mode(mode: int) -> Tuple[bool, str]:
    """
    验证 MQTT 模式值
    
    Args:
        mode: MQTT模式 (1=局域网, 10=阿里云)
        
    Returns:
        (is_valid, error_message) 元组
    """
    if mode not in (MqttMode.LOCAL, MqttMode.ALIYUN):
        return False, f"Invalid MQTT mode: {mode}. Must be {MqttMode.LOCAL} (local) or {MqttMode.ALIYUN} (Aliyun)"
    
    return True, ""


def build_cmq_command(mode: int) -> Tuple[bool, str, str]:
    """
    构建 SET:CMQ 命令 - 配置MQTT模式
    
    格式: SET:CMQ,<mode>
    
    Args:
        mode: MQTT模式
              - 1 = 局域网模式
              - 10 = 阿里云模式
              
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_cmq_command(10)
        (True, "", "SET:CMQ,10")
        
        >>> build_cmq_command(1)
        (True, "", "SET:CMQ,1")
    """
    # 验证模式
    valid, error = validate_mqtt_mode(mode)
    if not valid:
        return False, error, ""
    
    # 构建命令
    cmd = f"SET:CMQ,{mode}"
    return True, "", cmd


def get_mqtt_mode_description(mode: int) -> str:
    """
    获取 MQTT 模式的描述文本
    
    Args:
        mode: MQTT模式值
        
    Returns:
        模式描述字符串
    """
    descriptions = {
        MqttMode.LOCAL: "Local Network Mode (局域网模式)",
        MqttMode.ALIYUN: "Aliyun IoT Platform (阿里云物联网平台)",
    }
    return descriptions.get(mode, f"Unknown Mode ({mode})")


# ============================================================================
# 便捷函数
# ============================================================================

def build_aliyun_mqtt_command(
    product_key: str,
    device_name: str,
    device_secret: str
) -> Tuple[bool, str, str]:
    """
    构建完整的阿里云MQTT配置命令（包含 KNS + CMQ）
    
    这个函数返回两个命令，应该按顺序发送：
    1. SET:KNS - 配置阿里云三元组
    2. SET:CMQ,10 - 切换到阿里云模式
    
    Args:
        product_key: 产品密钥
        device_name: 设备名称
        device_secret: 设备密钥
        
    Returns:
        (success, error_message, commands) 元组
        commands 是命令列表
    """
    # 构建 KNS 命令
    valid, error, kns_cmd = build_kns_command(product_key, device_name, device_secret)
    if not valid:
        return False, error, []
    
    # 构建 CMQ 命令（阿里云模式）
    valid, error, cmq_cmd = build_cmq_command(MqttMode.ALIYUN)
    if not valid:
        return False, error, []
    
    return True, "", [kns_cmd, cmq_cmd]


def build_local_mqtt_command() -> Tuple[bool, str, str]:
    """
    构建切换到局域网MQTT模式的命令
    
    Returns:
        (success, error_message, command) 元组
    """
    return build_cmq_command(MqttMode.LOCAL)
