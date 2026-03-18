"""
SensorCalibrator System Control Module

系统控制功能。
提供 SS:14, SS:15, SS:16, SS:18 等命令。
"""

from typing import Tuple


# ============================================================================
# 喇叭控制 (SS:14)
# ============================================================================

def build_ss14_buzzer_long() -> str:
    """
    构建 SS:14 命令 - 喇叭长响
    
    用于测试喇叭或发出警报。
    
    Returns:
        命令字符串
    """
    return "SS:14"


# ============================================================================
# 升级检查 (SS:15)
# ============================================================================

def build_ss15_check_upgrade() -> str:
    """
    构建 SS:15 命令 - 监查升级
    
    检查是否有可用的固件升级。
    
    Returns:
        命令字符串
    """
    return "SS:15"


# ============================================================================
# AP 配置模式 (SS:16)
# ============================================================================

def build_ss16_ap_config_mode() -> str:
    """
    构建 SS:16 命令 - 进入AP配置模式
    
    传感器进入AP模式，可以通过WiFi直接连接配置。
    
    Returns:
        命令字符串
    """
    return "SS:16"


# ============================================================================
# MQTT 模式切换 (SS:18)
# ============================================================================

def build_ss18_switch_mqtt_mode(mode: int = 1) -> str:
    """
    构建 SS:18 命令 - 切换MQTT模式
    
    Args:
        mode: MQTT模式 (1=局域网, 10=阿里云)
        
    Returns:
        命令字符串
        
    Example:
        >>> build_ss18_switch_mqtt_mode(1)
        'SS:18,1'
        
        >>> build_ss18_switch_mqtt_mode(10)
        'SS:18,10'
    """
    return f"SS:18,{mode}"


# ============================================================================
# 便捷函数
# ============================================================================

def build_ss18_local_mode() -> str:
    """构建切换到局域网MQTT模式的命令"""
    return build_ss18_switch_mqtt_mode(1)


def build_ss18_aliyun_mode() -> str:
    """构建切换到阿里云MQTT模式的命令"""
    return build_ss18_switch_mqtt_mode(10)


# ============================================================================
# 系统控制管理器
# ============================================================================

class SystemController:
    """
    系统控制器
    
    管理 SS:14-18 等系统控制命令
    """
    
    def __init__(self, serial_manager, log_callback=None):
        """
        初始化系统控制器
        
        Args:
            serial_manager: SerialManager 实例
            log_callback: 日志回调函数
        """
        self.serial_manager = serial_manager
        self.log_callback = log_callback or (lambda msg: None)
    
    def _send_command(self, command: str, description: str = "") -> bool:
        """
        发送命令
        
        Args:
            command: 命令字符串
            description: 命令描述
            
        Returns:
            是否发送成功
        """
        if not self.serial_manager or not self.serial_manager.is_connected:
            self.log_callback("Error: Not connected to sensor")
            return False
        
        try:
            success, error = self.serial_manager.send_line(command)
            if success:
                if description:
                    self.log_callback(f"Sent: {command} ({description})")
                else:
                    self.log_callback(f"Sent: {command}")
                return True
            else:
                self.log_callback(f"Error: {error}")
                return False
        except Exception as e:
            self.log_callback(f"Error sending command: {e}")
            return False
    
    def buzzer_long(self) -> bool:
        """喇叭长响"""
        return self._send_command(build_ss14_buzzer_long(), "Buzzer Long Beep")
    
    def check_upgrade(self) -> bool:
        """检查升级"""
        return self._send_command(build_ss15_check_upgrade(), "Check Upgrade")
    
    def enter_ap_mode(self) -> bool:
        """进入AP配置模式"""
        return self._send_command(build_ss16_ap_config_mode(), "Enter AP Mode")
    
    def switch_mqtt_mode(self, mode: int) -> bool:
        """
        切换MQTT模式
        
        Args:
            mode: 1=局域网, 10=阿里云
        """
        mode_name = "Local" if mode == 1 else "Aliyun" if mode == 10 else f"Mode {mode}"
        return self._send_command(
            build_ss18_switch_mqtt_mode(mode),
            f"Switch MQTT to {mode_name}"
        )
