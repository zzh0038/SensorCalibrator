from typing import Dict, Tuple

from sensor_calibrator import validate_password, validate_port, validate_ssid, validate_url


def build_wifi_command(ssid: str, password: str) -> Tuple[bool, str, str]:
    """
    校验 WiFi 参数并生成指令。
    返回 (ok, error_message, command)。
    """
    ssid = ssid.strip()
    password = password.strip()

    valid, error = validate_ssid(ssid)
    if not valid:
        return False, error, ""

    valid, error = validate_password(password)
    if not valid:
        return False, error, ""

    cmd = f"SET:WF,{ssid},{password}"
    return True, "", cmd


def build_mqtt_command(
    broker: str, port: str, username: str, password: str
) -> Tuple[bool, str, str]:
    """
    校验 MQTT 参数并生成指令。
    返回 (ok, error_message, command)。
    """
    broker = broker.strip()
    username = username.strip()
    password = password.strip()
    port = port.strip() or "1883"

    if not broker:
        return False, "MQTT broker address cannot be empty!", ""

    valid, error = validate_port(port)
    if not valid:
        return False, error, ""

    valid, error = validate_password(password)
    if not valid:
        return False, error, ""

    cmd = f"SET:MQ,{broker},{port},{username},{password}"
    return True, "", cmd


def build_ota_command(url1: str, url2: str, url3: str, url4: str) -> Tuple[bool, str, str]:
    """
    校验 OTA 参数并生成指令。
    返回 (ok, error_message, command)。
    """
    urls = [url1.strip(), url2.strip(), url3.strip(), url4.strip()]

    for i, u in enumerate(urls, 1):
        if u:
            valid, error = validate_url(u)
            if not valid:
                return False, f"URL{i} {error}", ""

    cmd = f"SET:OTA,{urls[0]},{urls[1]},{urls[2]},{urls[3]}"
    return True, "", cmd


def extract_network_from_properties(sensor_properties: Dict) -> Dict[str, Dict[str, str]]:
    """
    从设备属性字典中提取 WiFi / MQTT / OTA 配置信息。
    返回形如:
    {
        \"wifi\": {\"ssid\": ..., \"password\": ...},
        \"mqtt\": {\"broker\": ..., \"port\": ..., \"username\": ..., \"password\": ...},
        \"ota\":  {\"URL1\": ..., \"URL2\": ..., \"URL3\": ..., \"URL4\": ...},
    }
    若某些字段不存在，则使用空字符串。
    """
    result = {
        "wifi": {"ssid": "", "password": ""},
        "mqtt": {"broker": "", "port": "1883", "username": "", "password": ""},
        "ota": {"URL1": "", "URL2": "", "URL3": "", "URL4": ""},
    }

    if not sensor_properties or "sys" not in sensor_properties:
        return result

    sys_info = sensor_properties["sys"] or {}

    # WiFi
    result["wifi"]["ssid"] = sys_info.get("SSID", "") or ""
    result["wifi"]["password"] = sys_info.get("PA", "") or ""

    # MQTT
    result["mqtt"]["broker"] = sys_info.get("MBR", "") or ""
    result["mqtt"]["port"] = str(sys_info.get("MPT", "1883") or "1883")
    result["mqtt"]["username"] = sys_info.get("MUS", "") or ""
    result["mqtt"]["password"] = sys_info.get("MPW", "") or ""

    # OTA
    result["ota"]["URL1"] = sys_info.get("URL1", "") or ""
    result["ota"]["URL2"] = sys_info.get("URL2", "") or ""
    result["ota"]["URL3"] = sys_info.get("URL3", "") or ""
    result["ota"]["URL4"] = sys_info.get("URL4", "") or ""

    return result

