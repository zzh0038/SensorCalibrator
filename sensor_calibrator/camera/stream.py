"""
SensorCalibrator Camera Stream Module

视频流控制功能。
提供 SS:24 和 CA:1 命令。
"""

from typing import Dict, Any, Optional
from enum import Enum


# ============================================================================
# 流类型枚举
# ============================================================================

class StreamType(Enum):
    """视频流类型"""
    NONE = "none"
    CAMERA_STREAM = "camera_stream"  # SS:24 - 摄像机串流
    PUSH_STREAM = "push_stream"      # CA:1 - 推流


# ============================================================================
# 流控制命令
# ============================================================================

def build_ss24_start_camera_stream() -> str:
    """
    构建 SS:24 命令 - 开启摄像机串流
    
    开启摄像机的视频串流功能。
    
    Returns:
        命令字符串
    """
    return "SS:24"


def build_ca1_start_push_stream() -> str:
    """
    构建 CA:1 命令 - 开启相机推流
    
    开启相机的推流功能（通常是RTMP或RTSP）。
    
    Returns:
        命令字符串
    """
    return "CA:1"


# ============================================================================
# 流状态管理
# ============================================================================

class StreamState(Enum):
    """流状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    STREAMING = "streaming"
    ERROR = "error"


class StreamManager:
    """
    视频流管理器
    
    管理视频流的启动、停止和状态跟踪
    """
    
    def __init__(self, serial_manager, log_callback=None):
        """
        初始化流管理器
        
        Args:
            serial_manager: SerialManager 实例
            log_callback: 日志回调函数
        """
        self.serial_manager = serial_manager
        self.log_callback = log_callback or (lambda msg: None)
        
        self.camera_stream_state = StreamState.STOPPED
        self.push_stream_state = StreamState.STOPPED
        
        # 流统计
        self.stream_start_time = None
        self.frame_count = 0
        self.last_frame_time = None
    
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
    
    def start_camera_stream(self) -> bool:
        """
        开启摄像机串流
        
        Returns:
            是否成功启动
        """
        if self.camera_stream_state == StreamState.STREAMING:
            self.log_callback("Camera stream is already running")
            return True
        
        self.camera_stream_state = StreamState.STARTING
        
        if self._send_command(build_ss24_start_camera_stream(), "Start Camera Stream"):
            self.camera_stream_state = StreamState.STREAMING
            import time
            self.stream_start_time = time.time()
            self.frame_count = 0
            return True
        else:
            self.camera_stream_state = StreamState.ERROR
            return False
    
    def stop_camera_stream(self) -> bool:
        """
        停止摄像机串流
        
        注意：SS:24 是开关命令，再次发送会停止串流
        
        Returns:
            是否成功停止
        """
        if self.camera_stream_state == StreamState.STOPPED:
            self.log_callback("Camera stream is not running")
            return True
        
        if self._send_command(build_ss24_start_camera_stream(), "Stop Camera Stream"):
            self.camera_stream_state = StreamState.STOPPED
            self.stream_start_time = None
            return True
        return False
    
    def toggle_camera_stream(self) -> bool:
        """
        切换摄像机串流状态
        
        Returns:
            操作是否成功
        """
        if self.camera_stream_state == StreamState.STREAMING:
            return self.stop_camera_stream()
        else:
            return self.start_camera_stream()
    
    def start_push_stream(self) -> bool:
        """
        开启相机推流
        
        Returns:
            是否成功启动
        """
        if self.push_stream_state == StreamState.STREAMING:
            self.log_callback("Push stream is already running")
            return True
        
        self.push_stream_state = StreamState.STARTING
        
        if self._send_command(build_ca1_start_push_stream(), "Start Push Stream"):
            self.push_stream_state = StreamState.STREAMING
            return True
        else:
            self.push_stream_state = StreamState.ERROR
            return False
    
    def stop_push_stream(self) -> bool:
        """
        停止相机推流
        
        注意：CA:1 是开关命令，再次发送会停止推流
        
        Returns:
            是否成功停止
        """
        if self.push_stream_state == StreamState.STOPPED:
            self.log_callback("Push stream is not running")
            return True
        
        if self._send_command(build_ca1_start_push_stream(), "Stop Push Stream"):
            self.push_stream_state = StreamState.STOPPED
            return True
        return False
    
    def toggle_push_stream(self) -> bool:
        """
        切换推流状态
        
        Returns:
            操作是否成功
        """
        if self.push_stream_state == StreamState.STREAMING:
            return self.stop_push_stream()
        else:
            return self.start_push_stream()
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取流状态
        
        Returns:
            状态字典
        """
        status = {
            'camera_stream': self.camera_stream_state.value,
            'push_stream': self.push_stream_state.value,
        }
        
        if self.stream_start_time and self.camera_stream_state == StreamState.STREAMING:
            import time
            duration = time.time() - self.stream_start_time
            status['stream_duration'] = duration
        
        return status
    
    def reset(self):
        """重置所有状态"""
        self.camera_stream_state = StreamState.STOPPED
        self.push_stream_state = StreamState.STOPPED
        self.stream_start_time = None
        self.frame_count = 0
        self.last_frame_time = None


# ============================================================================
# 便捷函数
# ============================================================================

def is_stream_command(command: str) -> bool:
    """
    检查命令是否是流控制命令
    
    Args:
        command: 命令字符串
        
    Returns:
        是否是流控制命令
    """
    return command in ("SS:24", "CA:1")


def get_stream_type(command: str) -> Optional[StreamType]:
    """
    获取命令对应的流类型
    
    Args:
        command: 命令字符串
        
    Returns:
        流类型，如果不是流命令则返回 None
    """
    if command == "SS:24":
        return StreamType.CAMERA_STREAM
    elif command == "CA:1":
        return StreamType.PUSH_STREAM
    return None
