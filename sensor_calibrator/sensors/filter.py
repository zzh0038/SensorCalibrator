"""
SensorCalibrator Filter Module

卡尔曼滤波配置管理。
提供 SET:KFQR 和 SS:17 命令构建功能。
"""

from typing import Tuple


# 卡尔曼滤波参数范围
MIN_PROCESS_NOISE = 0.001
MAX_PROCESS_NOISE = 1.0
DEFAULT_PROCESS_NOISE = 0.005

MIN_MEASUREMENT_NOISE = 1.0
MAX_MEASUREMENT_NOISE = 100.0
DEFAULT_MEASUREMENT_NOISE = 15.0


def validate_process_noise(noise: float) -> Tuple[bool, str]:
    """
    验证过程噪声参数
    
    Args:
        noise: 过程噪声值 (Q)
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not isinstance(noise, (int, float)):
        return False, f"Process noise must be a number, got {type(noise).__name__}"
    
    if noise < MIN_PROCESS_NOISE or noise > MAX_PROCESS_NOISE:
        return False, (
            f"Process noise must be between {MIN_PROCESS_NOISE} and {MAX_PROCESS_NOISE}, "
            f"got {noise}"
        )
    
    return True, ""


def validate_measurement_noise(noise: float) -> Tuple[bool, str]:
    """
    验证测量噪声参数
    
    Args:
        noise: 测量噪声值 (R)
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not isinstance(noise, (int, float)):
        return False, f"Measurement noise must be a number, got {type(noise).__name__}"
    
    if noise < MIN_MEASUREMENT_NOISE or noise > MAX_MEASUREMENT_NOISE:
        return False, (
            f"Measurement noise must be between {MIN_MEASUREMENT_NOISE} and {MAX_MEASUREMENT_NOISE}, "
            f"got {noise}"
        )
    
    return True, ""


def build_kfqr_command(process_noise: float, measurement_noise: float) -> Tuple[bool, str, str]:
    """
    构建 SET:KFQR 命令 - 设置卡尔曼滤波系数
    
    格式: SET:KFQR,<process_noise>,<measurement_noise>
    
    Args:
        process_noise: 过程噪声 (Q)，范围 0.001-1.0，默认 0.005
        measurement_noise: 测量噪声 (R)，范围 1.0-100.0，默认 15
        
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_kfqr_command(0.005, 15)
        (True, "", "SET:KFQR,0.005,15")
        
        >>> build_kfqr_command(0.01, 20)
        (True, "", "SET:KFQR,0.01,20")
    """
    # 验证过程噪声
    valid, error = validate_process_noise(process_noise)
    if not valid:
        return False, f"Invalid process noise: {error}", ""
    
    # 验证测量噪声
    valid, error = validate_measurement_noise(measurement_noise)
    if not valid:
        return False, f"Invalid measurement noise: {error}", ""
    
    # 构建命令
    cmd = f"SET:KFQR,{process_noise:.6f},{measurement_noise:.2f}"
    return True, "", cmd


def build_ss17_toggle_filter(enable: bool = True) -> str:
    """
    构建 SS:17 命令 - 开启/关闭滤波
    
    Args:
        enable: True=开启滤波, False=关闭滤波
        
    Returns:
        命令字符串
        
    Example:
        >>> build_ss17_toggle_filter(True)
        'SS:17,1'
        
        >>> build_ss17_toggle_filter(False)
        'SS:17,0'
    """
    state = 1 if enable else 0
    return f"SS:17,{state}"


# ============================================================================
# 便捷函数
# ============================================================================

def build_default_filter_command() -> str:
    """构建默认卡尔曼滤波系数命令"""
    return "SET:KFQR,0.005,15"


def build_filter_on_command() -> str:
    """构建开启滤波命令"""
    return build_ss17_toggle_filter(True)


def build_filter_off_command() -> str:
    """构建关闭滤波命令"""
    return build_ss17_toggle_filter(False)


# ============================================================================
# 预设值
# ============================================================================

# 常用滤波配置预设
FILTER_PRESETS = {
    'default': {'q': 0.005, 'r': 15, 'desc': '默认配置'},
    'smooth': {'q': 0.001, 'r': 30, 'desc': '平滑优先 (低Q, 高R)'},
    'responsive': {'q': 0.1, 'r': 5, 'desc': '响应优先 (高Q, 低R)'},
    'balanced': {'q': 0.01, 'r': 10, 'desc': '平衡配置'},
}


def get_filter_preset(name: str) -> dict:
    """
    获取滤波预设配置
    
    Args:
        name: 预设名称
        
    Returns:
        预设配置字典，包含 q, r, desc
    """
    return FILTER_PRESETS.get(name, FILTER_PRESETS['default'])


def get_all_filter_presets() -> list:
    """
    获取所有可用的滤波预设
    
    Returns:
        预设列表，每项为 (name, description) 元组
    """
    return [(name, f"{info['desc']} (Q={info['q']}, R={info['r']})") 
            for name, info in FILTER_PRESETS.items()]
