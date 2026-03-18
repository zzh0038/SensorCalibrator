"""
SensorCalibrator Sensor Calibration Control Module

传感器校准控制功能。
提供 SS:6 命令和相关功能。
"""

from typing import Dict, Any, Optional


def build_ss6_sensor_calibration() -> str:
    """
    构建 SS:6 命令 - 传感器校准模式
    
    进入传感器校准模式，传感器将执行内置的校准程序。
    这与 SS:1 校准流不同，SS:6 是传感器自带的校准功能。
    
    Returns:
        命令字符串
        
    Example:
        >>> build_ss6_sensor_calibration()
        'SS:6'
    """
    return "SS:6"


def parse_sensor_cal_response(response: str) -> Dict[str, Any]:
    """
    解析传感器校准响应
    
    Args:
        response: 响应字符串
        
    Returns:
        解析结果字典
    """
    response_lower = response.lower().strip()
    
    if "ok" in response_lower or "success" in response_lower:
        return {
            'success': True,
            'message': 'Calibration started',
            'raw': response
        }
    elif "error" in response_lower:
        return {
            'success': False,
            'message': response,
            'raw': response
        }
    else:
        return {
            'success': None,  # 未知状态
            'message': response,
            'raw': response
        }


# ============================================================================
# 校准状态跟踪
# ============================================================================

class SensorCalState:
    """传感器校准状态"""
    IDLE = "idle"
    CALIBRATING = "calibrating"
    COMPLETED = "completed"
    ERROR = "error"


class SensorCalibrationTracker:
    """
    传感器校准跟踪器
    
    用于跟踪 SS:6 命令的校准进度
    """
    
    def __init__(self):
        self.state = SensorCalState.IDLE
        self.progress = 0  # 0-100
        self.message = ""
        self.start_time = None
        self.duration = None
    
    def start(self):
        """开始校准"""
        import time
        self.state = SensorCalState.CALIBRATING
        self.progress = 0
        self.message = "Calibration started..."
        self.start_time = time.time()
        self.duration = None
    
    def update_progress(self, progress: int, message: str = ""):
        """更新进度"""
        self.progress = max(0, min(100, progress))
        if message:
            self.message = message
    
    def complete(self, success: bool = True):
        """完成校准"""
        import time
        self.state = SensorCalState.COMPLETED if success else SensorCalState.ERROR
        self.progress = 100 if success else 0
        self.duration = time.time() - self.start_time if self.start_time else None
        self.message = "Calibration completed" if success else "Calibration failed"
    
    def reset(self):
        """重置状态"""
        self.state = SensorCalState.IDLE
        self.progress = 0
        self.message = ""
        self.start_time = None
        self.duration = None
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'state': self.state,
            'progress': self.progress,
            'message': self.message,
            'duration': self.duration,
        }
