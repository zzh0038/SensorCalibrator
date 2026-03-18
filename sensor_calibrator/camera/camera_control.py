"""
SensorCalibrator Camera Control Module

相机控制功能。
提供 SS:19, SS:21, SS:22, SS:23, SS:25, SS:26, CA:2, CA:9, CA:10 命令。
"""

from typing import Tuple, Dict, Any, Optional
from enum import Enum


# ============================================================================
# 相机模式命令
# ============================================================================

def build_ss19_camera_mode(enable: bool = True) -> str:
    """
    构建 SS:19 命令 - 打开/关闭拍照模式
    
    Args:
        enable: True=开启, False=关闭
        
    Returns:
        命令字符串
        
    Example:
        >>> build_ss19_camera_mode(True)
        'SS:19,1'
    """
    state = 1 if enable else 0
    return f"SS:19,{state}"


# ============================================================================
# 监测模式命令
# ============================================================================

def build_ss21_monitoring_mode(enable: bool = True) -> str:
    """
    构建 SS:21 命令 - 开启/关闭监测模式
    
    Args:
        enable: True=开启, False=关闭
        
    Returns:
        命令字符串
        
    Example:
        >>> build_ss21_monitoring_mode(True)
        'SS:21,1'
    """
    state = 1 if enable else 0
    return f"SS:21,{state}"


# ============================================================================
# 时程传输模式命令
# ============================================================================

def build_ss22_timelapse_mode(enable: bool = True) -> str:
    """
    构建 SS:22 命令 - 开启/关闭时程传输模式
    
    时程传输模式用于定时拍照并传输图像。
    
    Args:
        enable: True=开启, False=关闭
        
    Returns:
        命令字符串
        
    Example:
        >>> build_ss22_timelapse_mode(True)
        'SS:22,1'
    """
    state = 1 if enable else 0
    return f"SS:22,{state}"


# ============================================================================
# 摄像机控制命令
# ============================================================================

def build_ss23_reboot_camera_slave() -> str:
    """
    构建 SS:23 命令 - 重启摄像机下位机
    
    Returns:
        命令字符串
    """
    return "SS:23"


def build_ss25_take_photo() -> str:
    """
    构建 SS:25 命令 - 控制拍照
    
    Returns:
        命令字符串
    """
    return "SS:25"


def build_ss26_force_camera_ota() -> str:
    """
    构建 SS:26 命令 - 强制摄像机OTA升级
    
    ⚠️ 警告：此命令会强制相机进行OTA升级
    
    Returns:
        命令字符串
    """
    return "SS:26"


# ============================================================================
# CA 命令 (相机专用)
# ============================================================================

def build_ca2_take_photo() -> str:
    """
    构建 CA:2 命令 - 控制拍照
    
    Returns:
        命令字符串
    """
    return "CA:2"


def build_ca9_reboot_camera_module() -> str:
    """
    构建 CA:9 命令 - 重启摄像机模组
    
    Returns:
        命令字符串
    """
    return "CA:9"


def build_ca10_force_ota_upgrade() -> str:
    """
    构建 CA:10 命令 - ESP32 S3强制OTA升级
    
    ⚠️ 警告：此命令会强制ESP32 S3进行OTA升级
    
    Returns:
        命令字符串
    """
    return "CA:10"


# ============================================================================
# 相机状态管理
# ============================================================================

class CameraMode(Enum):
    """相机模式状态"""
    IDLE = "idle"
    PHOTO_MODE = "photo_mode"
    MONITORING = "monitoring"
    TIMELAPSE = "timelapse"
    STREAMING = "streaming"


class CameraStateManager:
    """
    相机状态管理器
    
    跟踪相机的各种模式状态
    """
    
    def __init__(self):
        self.photo_mode = False
        self.monitoring_mode = False
        self.timelapse_mode = False
        self.streaming = False
        self.push_streaming = False
    
    def set_photo_mode(self, enabled: bool):
        """设置拍照模式状态"""
        self.photo_mode = enabled
    
    def set_monitoring_mode(self, enabled: bool):
        """设置监测模式状态"""
        self.monitoring_mode = enabled
    
    def set_timelapse_mode(self, enabled: bool):
        """设置时程传输模式状态"""
        self.timelapse_mode = enabled
    
    def set_streaming(self, enabled: bool):
        """设置串流状态"""
        self.streaming = enabled
    
    def set_push_streaming(self, enabled: bool):
        """设置推流状态"""
        self.push_streaming = enabled
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'photo_mode': self.photo_mode,
            'monitoring_mode': self.monitoring_mode,
            'timelapse_mode': self.timelapse_mode,
            'streaming': self.streaming,
            'push_streaming': self.push_streaming,
        }
    
    def reset(self):
        """重置所有状态"""
        self.photo_mode = False
        self.monitoring_mode = False
        self.timelapse_mode = False
        self.streaming = False
        self.push_streaming = False


# ============================================================================
# 相机控制器
# ============================================================================

class CameraController:
    """
    相机控制器
    
    管理所有相机相关命令的发送
    """
    
    def __init__(self, serial_manager, log_callback=None):
        """
        初始化相机控制器
        
        Args:
            serial_manager: SerialManager 实例
            log_callback: 日志回调函数
        """
        self.serial_manager = serial_manager
        self.log_callback = log_callback or (lambda msg: None)
        self.state = CameraStateManager()
    
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
    
    def set_photo_mode(self, enable: bool) -> bool:
        """设置拍照模式"""
        cmd = build_ss19_camera_mode(enable)
        if self._send_command(cmd, f"Photo Mode {'ON' if enable else 'OFF'}"):
            self.state.set_photo_mode(enable)
            return True
        return False
    
    def set_monitoring_mode(self, enable: bool) -> bool:
        """设置监测模式"""
        cmd = build_ss21_monitoring_mode(enable)
        if self._send_command(cmd, f"Monitoring Mode {'ON' if enable else 'OFF'}"):
            self.state.set_monitoring_mode(enable)
            return True
        return False
    
    def set_timelapse_mode(self, enable: bool) -> bool:
        """设置时程传输模式"""
        cmd = build_ss22_timelapse_mode(enable)
        if self._send_command(cmd, f"Timelapse Mode {'ON' if enable else 'OFF'}"):
            self.state.set_timelapse_mode(enable)
            return True
        return False
    
    def reboot_camera_slave(self) -> bool:
        """重启摄像机下位机"""
        return self._send_command(build_ss23_reboot_camera_slave(), "Reboot Camera Slave")
    
    def take_photo_ss(self) -> bool:
        """使用 SS:25 拍照"""
        return self._send_command(build_ss25_take_photo(), "Take Photo (SS:25)")
    
    def take_photo_ca(self) -> bool:
        """使用 CA:2 拍照"""
        return self._send_command(build_ca2_take_photo(), "Take Photo (CA:2)")
    
    def force_camera_ota(self) -> bool:
        """强制摄像机OTA升级"""
        return self._send_command(build_ss26_force_camera_ota(), "Force Camera OTA")
    
    def reboot_camera_module(self) -> bool:
        """重启摄像机模组"""
        return self._send_command(build_ca9_reboot_camera_module(), "Reboot Camera Module")
    
    def force_esp32_ota(self) -> bool:
        """强制ESP32 S3 OTA升级"""
        return self._send_command(build_ca10_force_ota_upgrade(), "Force ESP32 S3 OTA")
