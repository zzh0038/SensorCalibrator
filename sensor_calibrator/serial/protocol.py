"""
SensorCalibrator Serial Protocol

SS 命令协议定义和命令构建。
"""

from typing import Tuple


# ============================================================================
# SS 命令常量 (0-9 - 基础命令)
# ============================================================================
SS_START_STREAM = 0          # SS:0 - 开始数据流
SS_START_CALIBRATION = 1     # SS:1 - 开始校准流
SS_LOCAL_MODE = 2            # SS:2 - 局部坐标模式
SS_GLOBAL_MODE = 3           # SS:3 - 整体坐标模式
SS_STOP_STREAM = 4           # SS:4 - 停止数据流/校准
SS_CPU_MONITOR = 5           # SS:5 - CPU监控模式
SS_SENSOR_CALIBRATION = 6    # SS:6 - 传感器校准模式
SS_SAVE_CONFIG = 7           # SS:7 - 保存配置
SS_GET_PROPERTIES = 8        # SS:8 - 获取传感器属性
SS_RESTART_SENSOR = 9        # SS:9 - 重启传感器

# ============================================================================
# SS 命令常量 (10-19 - 存储和配置)
# ============================================================================
# SS:10 - SD存储保存 (根据用户要求，不实现)
SS_RESTORE_DEFAULT = 11      # SS:11 - 恢复默认配置
SS_SAVE_SENSOR_CONFIG = 12   # SS:12 - 保存传感器配置
SS_READ_SENSOR_CONFIG = 13   # SS:13 - 读取传感器配置
SS_BUZZER_LONG = 14          # SS:14 - 喇叭长响
SS_CHECK_UPGRADE = 15        # SS:15 - 监查升级
SS_AP_CONFIG_MODE = 16       # SS:16 - 进入AP配置模式
SS_TOGGLE_FILTER = 17        # SS:17 - 开启/关闭滤波
SS_SWITCH_MQTT_MODE = 18     # SS:18 - 切换MQTT模式
SS_CAMERA_MODE = 19          # SS:19 - 打开/关闭拍照模式

# ============================================================================
# SS 命令常量 (20-27 - 监测和相机)
# ============================================================================
SS_GET_SENSOR_ATTRS = 20     # SS:20 - 获取传感器属性
SS_MONITORING_MODE = 21      # SS:21 - 开启/关闭监测模式
SS_TIMELAPSE_MODE = 22       # SS:22 - 开启/关闭时程传输模式
SS_REBOOT_CAMERA_SLAVE = 23  # SS:23 - 重启摄像机下位机
SS_START_CAMERA_STREAM = 24  # SS:24 - 开启摄像机串流
SS_TAKE_PHOTO = 25           # SS:25 - 控制拍照
SS_FORCE_CAMERA_OTA = 26     # SS:26 - 强制摄像机OTA升级
SS_DEACTIVATE_SENSOR = 27    # SS:27 - 传感器反激活

# ============================================================================
# CA 命令常量 (相机专用)
# ============================================================================
CA_START_PUSH_STREAM = 1     # CA:1 - 开启相机推流
CA_TAKE_PHOTO = 2            # CA:2 - 控制拍照
CA_REBOOT_CAMERA_MODULE = 9  # CA:9 - 重启摄像机模组
CA_FORCE_OTA_UPGRADE = 10    # CA:10 - ESP32 S3强制OTA升级


# ============================================================================
# SS 命令构建函数
# ============================================================================

def build_ss_command(cmd_id: int, description: str = "") -> str:
    """
    构建 SS 命令字符串
    
    Args:
        cmd_id: 命令ID (0-27)
        description: 命令描述（可选）
        
    Returns:
        命令字符串
    """
    return f"SS:{cmd_id}"


# ============================================================================
# 基础 SS 命令 (0-9)
# ============================================================================

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


def build_ss5_cpu_monitor() -> str:
    """构建 SS:5 命令 - CPU监控模式"""
    return build_ss_command(SS_CPU_MONITOR, "CPU Monitor Mode")


def build_ss6_sensor_calibration() -> str:
    """构建 SS:6 命令 - 传感器校准模式"""
    return build_ss_command(SS_SENSOR_CALIBRATION, "Sensor Calibration Mode")


def build_ss7_save_config() -> str:
    """构建 SS:7 命令 - 保存配置"""
    return build_ss_command(SS_SAVE_CONFIG, "Save Config")


def build_ss8_get_properties() -> str:
    """构建 SS:8 命令 - 获取传感器属性"""
    return build_ss_command(SS_GET_PROPERTIES, "Get Properties")


def build_ss9_restart_sensor() -> str:
    """构建 SS:9 命令 - 重启传感器"""
    return build_ss_command(SS_RESTART_SENSOR, "Restart Sensor")


# ============================================================================
# 存储和配置命令 (11-19)
# ============================================================================

def build_ss11_restore_default() -> str:
    """构建 SS:11 命令 - 恢复默认配置"""
    return build_ss_command(SS_RESTORE_DEFAULT, "Restore Default Config")


def build_ss12_save_sensor_config() -> str:
    """构建 SS:12 命令 - 保存传感器配置"""
    return build_ss_command(SS_SAVE_SENSOR_CONFIG, "Save Sensor Config")


def build_ss13_read_sensor_config() -> str:
    """构建 SS:13 命令 - 读取传感器配置"""
    return build_ss_command(SS_READ_SENSOR_CONFIG, "Read Sensor Config")


def build_ss14_buzzer_long() -> str:
    """构建 SS:14 命令 - 喇叭长响"""
    return build_ss_command(SS_BUZZER_LONG, "Buzzer Long Beep")


def build_ss15_check_upgrade() -> str:
    """构建 SS:15 命令 - 监查升级"""
    return build_ss_command(SS_CHECK_UPGRADE, "Check Upgrade")


def build_ss16_ap_config_mode() -> str:
    """构建 SS:16 命令 - 进入AP配置模式"""
    return build_ss_command(SS_AP_CONFIG_MODE, "AP Config Mode")


def build_ss17_toggle_filter(enable: bool = True) -> str:
    """
    构建 SS:17 命令 - 开启/关闭滤波
    
    Args:
        enable: True=开启滤波, False=关闭滤波
        
    Returns:
        命令字符串
    """
    # SS:17 通常带参数，格式为 SS:17,0 或 SS:17,1
    state = 1 if enable else 0
    return f"SS:{SS_TOGGLE_FILTER},{state}"


def build_ss18_switch_mqtt_mode(mode: int = 1) -> str:
    """
    构建 SS:18 命令 - 切换MQTT模式
    
    Args:
        mode: 1=局域网模式, 10=阿里云模式
        
    Returns:
        命令字符串
    """
    return f"SS:{SS_SWITCH_MQTT_MODE},{mode}"


def build_ss19_camera_mode(enable: bool = True) -> str:
    """
    构建 SS:19 命令 - 打开/关闭拍照模式
    
    Args:
        enable: True=开启, False=关闭
        
    Returns:
        命令字符串
    """
    state = 1 if enable else 0
    return f"SS:{SS_CAMERA_MODE},{state}"


# ============================================================================
# 监测和相机命令 (20-27)
# ============================================================================

def build_ss20_get_sensor_attrs() -> str:
    """构建 SS:20 命令 - 获取传感器属性"""
    return build_ss_command(SS_GET_SENSOR_ATTRS, "Get Sensor Attributes")


def build_ss21_monitoring_mode(enable: bool = True) -> str:
    """
    构建 SS:21 命令 - 开启/关闭监测模式
    
    Args:
        enable: True=开启, False=关闭
        
    Returns:
        命令字符串
    """
    state = 1 if enable else 0
    return f"SS:{SS_MONITORING_MODE},{state}"


def build_ss22_timelapse_mode(enable: bool = True) -> str:
    """
    构建 SS:22 命令 - 开启/关闭时程传输模式
    
    Args:
        enable: True=开启, False=关闭
        
    Returns:
        命令字符串
    """
    state = 1 if enable else 0
    return f"SS:{SS_TIMELAPSE_MODE},{state}"


def build_ss23_reboot_camera_slave() -> str:
    """构建 SS:23 命令 - 重启摄像机下位机"""
    return build_ss_command(SS_REBOOT_CAMERA_SLAVE, "Reboot Camera Slave")


def build_ss24_start_camera_stream() -> str:
    """构建 SS:24 命令 - 开启摄像机串流"""
    return build_ss_command(SS_START_CAMERA_STREAM, "Start Camera Stream")


def build_ss25_take_photo() -> str:
    """构建 SS:25 命令 - 控制拍照"""
    return build_ss_command(SS_TAKE_PHOTO, "Take Photo")


def build_ss26_force_camera_ota() -> str:
    """构建 SS:26 命令 - 强制摄像机OTA升级"""
    return build_ss_command(SS_FORCE_CAMERA_OTA, "Force Camera OTA")


def build_ss27_deactivate_sensor() -> str:
    """构建 SS:27 命令 - 传感器反激活"""
    return build_ss_command(SS_DEACTIVATE_SENSOR, "Deactivate Sensor")


# ============================================================================
# CA 命令构建函数 (相机专用)
# ============================================================================

def build_ca_command(cmd_id: int, description: str = "") -> str:
    """
    构建 CA 命令字符串
    
    Args:
        cmd_id: 命令ID
        description: 命令描述（可选）
        
    Returns:
        命令字符串
    """
    return f"CA:{cmd_id}"


def build_ca1_start_push_stream() -> str:
    """构建 CA:1 命令 - 开启相机推流"""
    return build_ca_command(CA_START_PUSH_STREAM, "Start Push Stream")


def build_ca2_take_photo() -> str:
    """构建 CA:2 命令 - 控制拍照"""
    return build_ca_command(CA_TAKE_PHOTO, "Take Photo")


def build_ca9_reboot_camera_module() -> str:
    """构建 CA:9 命令 - 重启摄像机模组"""
    return build_ca_command(CA_REBOOT_CAMERA_MODULE, "Reboot Camera Module")


def build_ca10_force_ota_upgrade() -> str:
    """构建 CA:10 命令 - ESP32 S3强制OTA升级"""
    return build_ca_command(CA_FORCE_OTA_UPGRADE, "Force OTA Upgrade")


# ============================================================================
# 响应解析函数
# ============================================================================

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


# ============================================================================
# SS 命令描述字典
# ============================================================================

COMMAND_DESCRIPTIONS = {
    # 基础命令 (0-9)
    SS_START_STREAM: "Start Data Stream",
    SS_START_CALIBRATION: "Start Calibration Stream",
    SS_LOCAL_MODE: "Set Local Coordinate Mode",
    SS_GLOBAL_MODE: "Set Global Coordinate Mode",
    SS_STOP_STREAM: "Stop Data Stream",
    SS_CPU_MONITOR: "CPU Monitor Mode",
    SS_SENSOR_CALIBRATION: "Sensor Calibration Mode",
    SS_SAVE_CONFIG: "Save Configuration",
    SS_GET_PROPERTIES: "Get Sensor Properties",
    SS_RESTART_SENSOR: "Restart Sensor",
    # 存储和配置命令 (11-19)
    SS_RESTORE_DEFAULT: "Restore Default Configuration",
    SS_SAVE_SENSOR_CONFIG: "Save Sensor Configuration",
    SS_READ_SENSOR_CONFIG: "Read Sensor Configuration",
    SS_BUZZER_LONG: "Buzzer Long Beep",
    SS_CHECK_UPGRADE: "Check Firmware Upgrade",
    SS_AP_CONFIG_MODE: "Enter AP Configuration Mode",
    SS_TOGGLE_FILTER: "Toggle Filter On/Off",
    SS_SWITCH_MQTT_MODE: "Switch MQTT Mode",
    SS_CAMERA_MODE: "Toggle Camera Photo Mode",
    # 监测和相机命令 (20-27)
    SS_GET_SENSOR_ATTRS: "Get Sensor Attributes",
    SS_MONITORING_MODE: "Toggle Monitoring Mode",
    SS_TIMELAPSE_MODE: "Toggle Timelapse Transmission Mode",
    SS_REBOOT_CAMERA_SLAVE: "Reboot Camera Slave Device",
    SS_START_CAMERA_STREAM: "Start Camera Video Stream",
    SS_TAKE_PHOTO: "Take a Photo",
    SS_FORCE_CAMERA_OTA: "Force Camera OTA Upgrade",
    SS_DEACTIVATE_SENSOR: "Deactivate Sensor",
}

# CA 命令描述
CA_COMMAND_DESCRIPTIONS = {
    CA_START_PUSH_STREAM: "Start Camera Push Stream",
    CA_TAKE_PHOTO: "Take Photo",
    CA_REBOOT_CAMERA_MODULE: "Reboot Camera Module",
    CA_FORCE_OTA_UPGRADE: "Force ESP32 S3 OTA Upgrade",
}
