"""
SensorCalibrator Serial Protocol

SS 命令协议定义和命令构建。
"""

from typing import Tuple


# SS 命令常量
SS_START_STREAM = 0          # SS:0 - 开始数据流
SS_START_CALIBRATION = 1     # SS:1 - 开始校准流
SS_LOCAL_MODE = 2            # SS:2 - 局部坐标模式
SS_GLOBAL_MODE = 3           # SS:3 - 整体坐标模式
SS_STOP_STREAM = 4           # SS:4 - 停止数据流/校准
SS_SET_WIFI = 5              # SS:5 - 设置WiFi配置
SS_SET_MQTT = 6              # SS:6 - 设置MQTT配置
SS_SAVE_CONFIG = 7           # SS:7 - 保存配置
SS_GET_PROPERTIES = 8        # SS:8 - 获取传感器属性
SS_RESTART_SENSOR = 9        # SS:9 - 重启传感器


def build_ss_command(cmd_id: int, description: str = "") -> str:
    """
    构建 SS 命令字符串
    
    Args:
        cmd_id: 命令ID (0-9)
        description: 命令描述（可选）
        
    Returns:
        命令字符串
    """
    return f"SS:{cmd_id}"


def build_ss0_start_stream() -> str:
    """构建 SS:0 命令 - 开始数据流"""
    return build_ss_command(SS_START_STREAM, "Start Data Stream")


def build_ss1_start_calibration() -> str:
    """构建 SS:1 命令 - 开始校准流"""
    return build_ss_command(SS_START_CALIBRATION, "Start Calibration Stream")


def build_ss2_local_mode(mode_name: str = "Local Coordinate Mode") -> str:
    """构建 SS:2 命令 - 局部坐标模式"""
    return build_ss_command(SS_LOCAL_MODE, mode_name)


def build_ss3_global_mode(mode_name: str = "Global Coordinate Mode") -> str:
    """构建 SS:3 命令 - 整体坐标模式"""
    return build_ss_command(SS_GLOBAL_MODE, mode_name)


def build_ss4_stop_stream() -> str:
    """构建 SS:4 命令 - 停止数据流/校准"""
    return build_ss_command(SS_STOP_STREAM, "Stop Data Stream")


def build_ss7_save_config() -> str:
    """构建 SS:7 命令 - 保存配置"""
    return build_ss_command(SS_SAVE_CONFIG, "Save Config")


def build_ss8_get_properties() -> str:
    """构建 SS:8 命令 - 获取传感器属性"""
    return build_ss_command(SS_GET_PROPERTIES, "Get Properties")


def build_ss9_restart_sensor() -> str:
    """构建 SS:9 命令 - 重启传感器"""
    return build_ss_command(SS_RESTART_SENSOR, "Restart Sensor")


def parse_ss_response(response: str) -> Tuple[bool, str]:
    """
    解析 SS 命令响应
    
    Args:
        response: 响应字符串
        
    Returns:
        (success, message) 元组
    """
    if not response:
        return False, "Empty response"
    
    response = response.strip().lower()
    
    if response.startswith("ok"):
        return True, "Command executed successfully"
    elif response.startswith("error"):
        return False, response[5:].strip()
    else:
        return True, response


# SS 命令描述
COMMAND_DESCRIPTIONS = {
    SS_START_STREAM: "Start Data Stream",
    SS_START_CALIBRATION: "Start Calibration Stream",
    SS_LOCAL_MODE: "Set Local Coordinate Mode",
    SS_GLOBAL_MODE: "Set Global Coordinate Mode",
    SS_STOP_STREAM: "Stop Data Stream",
    SS_SET_WIFI: "Set WiFi Configuration",
    SS_SET_MQTT: "Set MQTT Configuration",
    SS_SAVE_CONFIG: "Save Configuration",
    SS_GET_PROPERTIES: "Get Sensor Properties",
    SS_RESTART_SENSOR: "Restart Sensor",
}
