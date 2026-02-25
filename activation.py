import hashlib
import re
import secrets
from typing import Dict, Optional


def generate_key_from_mac(mac_address: str) -> str:
    """
    基于 MAC 地址生成 64 字符的 SHA-256 十六进制密钥。
    """
    cleaned_mac = mac_address.replace(":", "").replace("-", "").lower()
    if len(cleaned_mac) != 12:
        raise ValueError(
            f"无效的MAC地址格式: {mac_address}. 清理后应为12个十六进制字符，实际得到{len(cleaned_mac)}个字符: {cleaned_mac}"
        )
    try:
        mac_bytes = bytes.fromhex(cleaned_mac)
    except ValueError as e:
        raise ValueError(f"MAC地址包含无效的十六进制字符: {cleaned_mac}") from e

    hash_object = hashlib.sha256(mac_bytes)
    return hash_object.hexdigest()


def verify_key(input_key: str, mac_address: str) -> bool:
    """
    验证输入的 7 字符密钥是否与基于 MAC 地址生成的密钥片段匹配。
    """
    expected_key = generate_key_from_mac(mac_address)
    expected_short = expected_key[5:12]
    if len(input_key) != 7 or len(expected_key) != 64:
        return False
    return secrets.compare_digest(input_key.lower(), expected_short.lower())


def validate_mac_address(mac_str: str) -> bool:
    """验证 MAC 地址格式。"""
    if not mac_str or not isinstance(mac_str, str):
        return False
    mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    return re.match(mac_pattern, mac_str) is not None


def extract_mac_from_properties(sensor_properties: Dict) -> Optional[str]:
    """从传感器属性中提取 MAC 地址。"""
    if not sensor_properties or "sys" not in sensor_properties:
        return None

    sys_info = sensor_properties["sys"] or {}

    # 常见字段名
    mac_keys = ["MAC", "mac", "mac_address", "macAddress", "device_mac"]
    for key in mac_keys:
        if key in sys_info:
            mac_value = sys_info[key]
            if validate_mac_address(mac_value):
                return mac_value

    # 尝试从设备名称中解析
    dn_value = sys_info.get("DN")
    if isinstance(dn_value, str):
        mac_pattern = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
        match = re.search(mac_pattern, dn_value)
        if match:
            return match.group()

    return None


def check_activation_status(sensor_properties: Dict, mac_address: Optional[str]) -> bool:
    """根据属性中的 AKY 字段和 MAC 地址判断是否已经激活。"""
    if not sensor_properties or not mac_address or "sys" not in sensor_properties:
        return False

    sys_info = sensor_properties["sys"] or {}
    aks_value = sys_info.get("AKY") or sys_info.get("aky") or sys_info.get("ak_key")
    if not aks_value:
        return False

    try:
        return verify_key(aks_value, mac_address)
    except Exception:
        return False

