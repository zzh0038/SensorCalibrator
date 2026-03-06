"""
SensorCalibrator Network Alarm

网络报警配置。
"""

from typing import Tuple


def build_set_alarm_command(accel_threshold: float, gyro_threshold: float) -> str:
    """
    构建设置报警阈值命令
    
    Args:
        accel_threshold: 加速度计报警阈值 (m/s²)
        gyro_threshold: 陀螺仪报警阈值 (°/s)
        
    Returns:
        报警命令字符串
    """
    return f"SET:ALARM,{accel_threshold:.2f},{gyro_threshold:.2f}"


def build_read_alarm_command() -> str:
    """构建读取报警配置命令"""
    return "GET:ALARM"


def parse_alarm_response(response: str) -> Tuple[float, float]:
    """
    解析报警响应
    
    Args:
        response: 响应字符串
        
    Returns:
        (accel_threshold, gyro_threshold) 元组
    """
    response = response.strip()
    
    if response.startswith("ALARM:"):
        values = response[6:].split(",")
        if len(values) == 2:
            try:
                accel = float(values[0])
                gyro = float(values[1])
                return accel, gyro
            except ValueError:
                pass
    
    return 0.0, 0.0
