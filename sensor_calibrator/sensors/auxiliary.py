"""
SensorCalibrator Auxiliary Sensors Module

辅助传感器配置管理。
提供 SET:VKS, SET:TME, SET:MAGOF 命令构建功能。
"""

from typing import Tuple


# ============================================================================
# 电压传感器配置 (SET:VKS)
# ============================================================================

# 电压比例范围
VKS_MIN = 0.1
VKS_MAX = 10.0
VKS_DEFAULT = 1.0


def validate_voltage_scale(scale: float) -> Tuple[bool, str]:
    """
    验证电压比例参数
    
    Args:
        scale: 电压比例系数
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not isinstance(scale, (int, float)):
        return False, f"Voltage scale must be a number, got {type(scale).__name__}"
    
    if scale < VKS_MIN or scale > VKS_MAX:
        return False, f"Voltage scale must be between {VKS_MIN} and {VKS_MAX}, got {scale}"
    
    return True, ""


def build_vks_command(voltage1_scale: float, voltage2_scale: float) -> Tuple[bool, str, str]:
    """
    构建 SET:VKS 命令 - 设定电压传感器比例
    
    格式: SET:VKS,<voltage1_scale>,<voltage2_scale>
    
    Args:
        voltage1_scale: 电压1比例系数，范围 0.1-10.0
        voltage2_scale: 电压2比例系数，范围 0.1-10.0
        
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_vks_command(1.0, 1.0)
        (True, "", "SET:VKS,1.0,1.0")
    """
    # 验证电压1比例
    valid, error = validate_voltage_scale(voltage1_scale)
    if not valid:
        return False, f"Invalid voltage1 scale: {error}", ""
    
    # 验证电压2比例
    valid, error = validate_voltage_scale(voltage2_scale)
    if not valid:
        return False, f"Invalid voltage2 scale: {error}", ""
    
    # 构建命令
    cmd = f"SET:VKS,{voltage1_scale:.2f},{voltage2_scale:.2f}"
    return True, "", cmd


# ============================================================================
# 温度传感器配置 (SET:TME)
# ============================================================================

# 温度偏移范围 (摄氏度)
TME_MIN = -50.0
TME_MAX = 50.0
TME_DEFAULT = 0.0


def validate_temperature_offset(offset: float) -> Tuple[bool, str]:
    """
    验证温度偏移参数
    
    Args:
        offset: 温度偏移值 (°C)
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not isinstance(offset, (int, float)):
        return False, f"Temperature offset must be a number, got {type(offset).__name__}"
    
    if offset < TME_MIN or offset > TME_MAX:
        return False, f"Temperature offset must be between {TME_MIN} and {TME_MAX}°C, got {offset}"
    
    return True, ""


def build_tme_command(temp_offset: float) -> Tuple[bool, str, str]:
    """
    构建 SET:TME 命令 - 设定温度传感器偏移
    
    格式: SET:TME,<temp_offset>
    
    Args:
        temp_offset: 温度偏移值 (°C)，范围 -50.0 到 50.0
        
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_tme_command(-15.0)
        (True, "", "SET:TME,-15.0")
        
        >>> build_tme_command(0.0)
        (True, "", "SET:TME,0.0")
    """
    # 验证温度偏移
    valid, error = validate_temperature_offset(temp_offset)
    if not valid:
        return False, error, ""
    
    # 构建命令
    cmd = f"SET:TME,{temp_offset:.2f}"
    return True, "", cmd


# ============================================================================
# 磁力传感器配置 (SET:MAGOF)
# ============================================================================

# 磁力零偏范围
MAGOF_MIN = -1000.0
MAGOF_MAX = 1000.0
MAGOF_DEFAULT = 0.0


def validate_magnetic_offset(offset: float) -> Tuple[bool, str]:
    """
    验证磁力零偏参数
    
    Args:
        offset: 磁力零偏值
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not isinstance(offset, (int, float)):
        return False, f"Magnetic offset must be a number, got {type(offset).__name__}"
    
    if offset < MAGOF_MIN or offset > MAGOF_MAX:
        return False, f"Magnetic offset must be between {MAGOF_MIN} and {MAGOF_MAX}, got {offset}"
    
    return True, ""


def build_magof_command(x_offset: float, y_offset: float, z_offset: float) -> Tuple[bool, str, str]:
    """
    构建 SET:MAGOF 命令 - 设定磁力传感器零偏
    
    格式: SET:MAGOF,<x_offset>,<y_offset>,<z_offset>
    
    Args:
        x_offset: X轴磁感零偏
        y_offset: Y轴磁感零偏
        z_offset: Z轴磁感零偏
        
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_magof_command(1.0, 1.0, 1.0)
        (True, "", "SET:MAGOF,1.0,1.0,1.0")
    """
    # 验证各轴零偏
    for axis, offset in [('X', x_offset), ('Y', y_offset), ('Z', z_offset)]:
        valid, error = validate_magnetic_offset(offset)
        if not valid:
            return False, f"Invalid {axis} axis offset: {error}", ""
    
    # 构建命令
    cmd = f"SET:MAGOF,{x_offset:.2f},{y_offset:.2f},{z_offset:.2f}"
    return True, "", cmd


# ============================================================================
# 便捷函数
# ============================================================================

def build_default_vks_command() -> Tuple[bool, str, str]:
    """构建默认电压传感器配置命令"""
    return build_vks_command(1.0, 1.0)


def build_default_tme_command() -> Tuple[bool, str, str]:
    """构建默认温度传感器配置命令 (无偏移)"""
    return build_tme_command(0.0)


def build_default_magof_command() -> Tuple[bool, str, str]:
    """构建默认磁力传感器配置命令 (无零偏)"""
    return build_magof_command(0.0, 0.0, 0.0)


# ============================================================================
# 辅助传感器信息
# ============================================================================

AUXILIARY_SENSOR_INFO = {
    'vks': {
        'name': 'Voltage Sensor',
        'description': '电压传感器，用于监测电池电压',
        'units': 'V',
        'range': f'{VKS_MIN}-{VKS_MAX}',
        'default': VKS_DEFAULT,
    },
    'tme': {
        'name': 'Temperature Sensor',
        'description': '温度传感器，用于监测设备温度',
        'units': '°C',
        'range': f'{TME_MIN} to {TME_MAX}',
        'default': TME_DEFAULT,
    },
    'magof': {
        'name': 'Magnetometer',
        'description': '磁力传感器，用于方向检测',
        'units': 'μT',
        'range': f'{MAGOF_MIN} to {MAGOF_MAX}',
        'default': MAGOF_DEFAULT,
    },
}


def get_auxiliary_sensor_info(sensor_type: str) -> dict:
    """
    获取辅助传感器信息
    
    Args:
        sensor_type: 传感器类型 ('vks', 'tme', 'magof')
        
    Returns:
        传感器信息字典
    """
    return AUXILIARY_SENSOR_INFO.get(sensor_type, {})
