"""
SensorCalibrator CPU Monitor Module

CPU 监控功能。
提供 SS:5 命令和相关功能。
"""

from typing import Dict, Any, Optional
import json


def build_ss5_cpu_monitor() -> str:
    """
    构建 SS:5 命令 - CPU监控模式
    
    进入CPU监控模式后，传感器将返回CPU使用率等信息。
    
    Returns:
        命令字符串
        
    Example:
        >>> build_ss5_cpu_monitor()
        'SS:5'
    """
    return "SS:5"


def parse_cpu_monitor_response(response: str) -> Optional[Dict[str, Any]]:
    """
    解析 CPU 监控响应
    
    Args:
        response: 响应字符串
        
    Returns:
        解析后的CPU信息字典，或 None 如果解析失败
        
    Example:
        >>> parse_cpu_monitor_response('{"cpu":45,"memory":60,"uptime":3600}')
        {'cpu': 45, 'memory': 60, 'uptime': 3600}
    """
    try:
        # 尝试解析为JSON
        data = json.loads(response)
        return data
    except json.JSONDecodeError:
        # 如果不是JSON，尝试简单解析
        if "cpu" in response.lower():
            return {'raw': response}
        return None


# ============================================================================
# CPU 信息格式化
# ============================================================================

def format_cpu_info(cpu_data: Dict[str, Any]) -> str:
    """
    格式化 CPU 信息为显示文本
    
    Args:
        cpu_data: CPU信息字典
        
    Returns:
        格式化后的文本
    """
    lines = []
    lines.append("=== CPU Monitor ===")
    
    if 'cpu' in cpu_data:
        lines.append(f"CPU Usage: {cpu_data['cpu']}%")
    if 'memory' in cpu_data:
        lines.append(f"Memory: {cpu_data['memory']}%")
    if 'uptime' in cpu_data:
        uptime = cpu_data['uptime']
        if uptime > 3600:
            lines.append(f"Uptime: {uptime/3600:.1f} hours")
        elif uptime > 60:
            lines.append(f"Uptime: {uptime/60:.1f} minutes")
        else:
            lines.append(f"Uptime: {uptime} seconds")
    if 'temperature' in cpu_data:
        lines.append(f"Temperature: {cpu_data['temperature']}°C")
    
    return "\n".join(lines)
