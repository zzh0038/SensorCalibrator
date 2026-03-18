"""
SensorCalibrator System Configuration Manager

系统配置管理模块。
提供 SS:11, SS:12, SS:27 等系统级命令。
"""

from typing import Tuple, Callable, Optional
from enum import Enum


class ConfigAction(Enum):
    """配置操作类型"""
    RESTORE_DEFAULT = "restore_default"      # 恢复默认配置
    SAVE_SENSOR_CONFIG = "save_sensor"       # 保存传感器配置
    READ_SENSOR_CONFIG = "read_sensor"       # 读取传感器配置
    DEACTIVATE = "deactivate"                # 反激活传感器


# 危险操作确认配置
DANGEROUS_ACTIONS = {
    ConfigAction.RESTORE_DEFAULT: {
        "title": "恢复默认配置",
        "message": "确定要恢复默认配置吗？\n\n这将清除所有自定义设置，包括：\n- 网络配置 (WiFi/MQTT)\n- 校准参数\n- 报警阈值\n\n此操作不可撤销！",
        "confirm_text": "恢复默认",
        "icon": "warning"
    },
    ConfigAction.DEACTIVATE: {
        "title": "传感器反激活",
        "message": "确定要反激活传感器吗？\n\n反激活后：\n- 传感器将停止工作\n- 需要重新激活才能使用\n- 网络连接将被断开\n\n此操作不可撤销！",
        "confirm_text": "反激活",
        "icon": "warning"
    },
}


def build_ss11_restore_default() -> str:
    """
    构建 SS:11 命令 - 恢复默认配置
    
    ⚠️ 警告：此命令会清除所有用户配置！
    
    Returns:
        命令字符串
        
    Example:
        >>> build_ss11_restore_default()
        'SS:11'
    """
    return "SS:11"


def build_ss12_save_sensor_config() -> str:
    """
    构建 SS:12 命令 - 保存传感器配置
    
    将当前的传感器配置（校准参数、报警阈值等）
    保存到传感器的永久存储中。
    
    Returns:
        命令字符串
        
    Example:
        >>> build_ss12_save_sensor_config()
        'SS:12'
    """
    return "SS:12"


def build_ss13_read_sensor_config() -> str:
    """
    构建 SS:13 命令 - 读取传感器配置
    
    从传感器读取当前的配置参数。
    
    Returns:
        命令字符串
        
    Example:
        >>> build_ss13_read_sensor_config()
        'SS:13'
    """
    return "SS:13"


def build_ss27_deactivate() -> str:
    """
    构建 SS:27 命令 - 传感器反激活
    
    ⚠️ 警告：此命令会使传感器停止工作！
    
    反激活后传感器将：
    - 停止数据传输
    - 断开网络连接
    - 需要重新激活才能使用
    
    Returns:
        命令字符串
        
    Example:
        >>> build_ss27_deactivate()
        'SS:27'
    """
    return "SS:27"


# ============================================================================
# 配置管理器类
# ============================================================================

class SystemConfigManager:
    """
    系统配置管理器
    
    管理传感器的系统级配置操作，包括：
    - 恢复默认配置
    - 保存/读取传感器配置
    - 传感器反激活
    
    Attributes:
        serial_manager: 串口管理器实例
        log_callback: 日志回调函数
    """
    
    def __init__(
        self,
        serial_manager,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        初始化系统配置管理器
        
        Args:
            serial_manager: SerialManager 实例
            log_callback: 日志回调函数，接收日志消息字符串
        """
        self.serial_manager = serial_manager
        self.log_callback = log_callback or (lambda msg: None)
    
    def _send_command(self, command: str, description: str = "") -> bool:
        """
        发送命令到传感器
        
        Args:
            command: 命令字符串
            description: 命令描述（用于日志）
            
        Returns:
            是否发送成功
        """
        if not self.serial_manager or not self.serial_manager.is_connected:
            self.log_callback(f"Error: Not connected to sensor")
            return False
        
        try:
            self.serial_manager.serial_port.write(f"{command}\n".encode())
            self.serial_manager.serial_port.flush()
            
            if description:
                self.log_callback(f"Sent: {command} ({description})")
            else:
                self.log_callback(f"Sent: {command}")
            
            return True
        except Exception as e:
            self.log_callback(f"Error sending command: {e}")
            return False
    
    def restore_default_config(self, confirmed: bool = False) -> Tuple[bool, str]:
        """
        恢复传感器默认配置 (SS:11)
        
        Args:
            confirmed: 是否已确认执行（危险操作）
            
        Returns:
            (success, message) 元组
        """
        if not confirmed:
            return False, "Confirmation required for restore default"
        
        cmd = build_ss11_restore_default()
        success = self._send_command(cmd, "Restore Default Config")
        
        if success:
            return True, "Restore default command sent successfully"
        else:
            return False, "Failed to send restore default command"
    
    def save_sensor_config(self) -> Tuple[bool, str]:
        """
        保存传感器配置 (SS:12)
        
        Returns:
            (success, message) 元组
        """
        cmd = build_ss12_save_sensor_config()
        success = self._send_command(cmd, "Save Sensor Config")
        
        if success:
            return True, "Save sensor config command sent successfully"
        else:
            return False, "Failed to send save sensor config command"
    
    def read_sensor_config(self) -> Tuple[bool, str]:
        """
        读取传感器配置 (SS:13)
        
        Returns:
            (success, message) 元组
        """
        cmd = build_ss13_read_sensor_config()
        success = self._send_command(cmd, "Read Sensor Config")
        
        if success:
            return True, "Read sensor config command sent successfully"
        else:
            return False, "Failed to send read sensor config command"
    
    def deactivate_sensor(self, confirmed: bool = False) -> Tuple[bool, str]:
        """
        反激活传感器 (SS:27)
        
        Args:
            confirmed: 是否已确认执行（危险操作）
            
        Returns:
            (success, message) 元组
        """
        if not confirmed:
            return False, "Confirmation required for deactivation"
        
        cmd = build_ss27_deactivate()
        success = self._send_command(cmd, "Deactivate Sensor")
        
        if success:
            return True, "Deactivate command sent successfully"
        else:
            return False, "Failed to send deactivate command"


# ============================================================================
# 辅助函数
# ============================================================================

def get_dangerous_action_info(action: ConfigAction) -> dict:
    """
    获取危险操作的确认对话框信息
    
    Args:
        action: 配置操作类型
        
    Returns:
        包含对话框信息的字典，如果不是危险操作则返回空字典
    """
    return DANGEROUS_ACTIONS.get(action, {})


def is_dangerous_action(action: ConfigAction) -> bool:
    """
    检查操作是否为危险操作（需要确认）
    
    Args:
        action: 配置操作类型
        
    Returns:
        是否为危险操作
    """
    return action in DANGEROUS_ACTIONS


def format_config_response(response: str) -> str:
    """
    格式化配置命令的响应
    
    Args:
        response: 原始响应字符串
        
    Returns:
        格式化后的响应信息
    """
    if not response:
        return "No response from sensor"
    
    response = response.strip()
    
    if response.upper() == "OK":
        return "Configuration applied successfully"
    elif response.upper().startswith("ERROR"):
        error_msg = response[5:].strip() if len(response) > 5 else "Unknown error"
        return f"Configuration failed: {error_msg}"
    else:
        return f"Sensor response: {response}"


# ============================================================================
# 命令序列辅助
# ============================================================================

def build_full_save_sequence() -> list:
    """
    构建完整的保存配置命令序列
    
    这个序列会：
    1. 保存传感器配置 (SS:12)
    2. 保存用户配置 (SS:7)
    
    Returns:
        命令列表
    """
    return [
        build_ss12_save_sensor_config(),  # 保存传感器配置
        "SS:7",                            # 保存用户配置
    ]


def build_factory_reset_sequence() -> list:
    """
    构建恢复出厂设置的完整序列
    
    这个序列会：
    1. 恢复默认配置 (SS:11)
    2. 重启传感器 (SS:9) - 需要外部添加
    
    Returns:
        命令列表
    """
    return [
        build_ss11_restore_default(),  # 恢复默认配置
        # SS:9 需要外部添加，因为通常需要延迟
    ]
