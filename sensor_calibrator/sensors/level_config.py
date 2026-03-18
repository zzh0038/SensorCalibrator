"""
SensorCalibrator Level Configuration Module

多级报警阈值配置管理。
提供 SET:GROLEVEL 和 SET:ACCLEVEL 命令构建功能。
"""

from typing import Tuple, List


# 报警等级数量
NUM_ALARM_LEVELS = 5

# 角度报警阈值范围 (度)
GROLEVEL_MIN = 0.0
GROLEVEL_MAX = 90.0

# 加速度报警阈值范围 (m/s²)
ACCLEVEL_MIN = 0.0
ACCLEVEL_MAX = 20.0


def validate_level_thresholds(
    thresholds: List[float],
    min_val: float,
    max_val: float,
    name: str
) -> Tuple[bool, str]:
    """
    验证多级报警阈值
    
    Args:
        thresholds: 阈值列表，必须包含5个递增的值
        min_val: 最小允许值
        max_val: 最大允许值
        name: 阈值类型名称（用于错误信息）
        
    Returns:
        (is_valid, error_message) 元组
    """
    # 检查数量
    if len(thresholds) != NUM_ALARM_LEVELS:
        return False, f"{name} must have exactly {NUM_ALARM_LEVELS} levels, got {len(thresholds)}"
    
    # 检查所有值都是数字
    for i, val in enumerate(thresholds):
        if not isinstance(val, (int, float)):
            return False, f"{name} level {i+1} must be a number, got {type(val).__name__}"
    
    # 检查范围
    for i, val in enumerate(thresholds):
        if val < min_val or val > max_val:
            return False, f"{name} level {i+1} ({val}) out of range [{min_val}, {max_val}]"
    
    # 检查递增顺序
    for i in range(1, len(thresholds)):
        if thresholds[i] <= thresholds[i-1]:
            return False, (
                f"{name} thresholds must be strictly increasing, "
                f"but level {i+1} ({thresholds[i]}) <= level {i} ({thresholds[i-1]})"
            )
    
    return True, ""


def build_grolevel_command(
    level1: float,
    level2: float,
    level3: float,
    level4: float,
    level5: float
) -> Tuple[bool, str, str]:
    """
    构建 SET:GROLEVEL 命令 - 设置传感器角度报警等级
    
    格式: SET:GROLEVEL,<level1>,<level2>,<level3>,<level4>,<level5>
    
    Args:
        level1: 等级1阈值 (°)
        level2: 等级2阈值 (°)
        level3: 等级3阈值 (°)
        level4: 等级4阈值 (°)
        level5: 等级5阈值 (°)
        
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_grolevel_command(0.40107, 0.573, 1.146, 2.292, 4.584)
        (True, "", "SET:GROLEVEL,0.40107,0.573,1.146,2.292,4.584")
    """
    thresholds = [level1, level2, level3, level4, level5]
    
    # 验证阈值
    valid, error = validate_level_thresholds(
        thresholds, GROLEVEL_MIN, GROLEVEL_MAX, "Gyro level"
    )
    if not valid:
        return False, error, ""
    
    # 构建命令
    cmd = f"SET:GROLEVEL,{level1:.5f},{level2:.5f},{level3:.5f},{level4:.5f},{level5:.5f}"
    return True, "", cmd


def build_acclevel_command(
    level1: float,
    level2: float,
    level3: float,
    level4: float,
    level5: float
) -> Tuple[bool, str, str]:
    """
    构建 SET:ACCLEVEL 命令 - 设置传感器加速度报警等级
    
    格式: SET:ACCLEVEL,<level1>,<level2>,<level3>,<level4>,<level5>
    
    Args:
        level1: 等级1阈值 (m/s²)
        level2: 等级2阈值 (m/s²)
        level3: 等级3阈值 (m/s²)
        level4: 等级4阈值 (m/s²)
        level5: 等级5阈值 (m/s²)
        
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_acclevel_command(0.2, 0.5, 1.0, 2.0, 4.0)
        (True, "", "SET:ACCLEVEL,0.2,0.5,1.0,2.0,4.0")
    """
    thresholds = [level1, level2, level3, level4, level5]
    
    # 验证阈值
    valid, error = validate_level_thresholds(
        thresholds, ACCLEVEL_MIN, ACCLEVEL_MAX, "Accel level"
    )
    if not valid:
        return False, error, ""
    
    # 构建命令
    cmd = f"SET:ACCLEVEL,{level1:.2f},{level2:.2f},{level3:.2f},{level4:.2f},{level5:.2f}"
    return True, "", cmd


# ============================================================================
# 便捷函数
# ============================================================================

def build_default_grolevel_command() -> Tuple[bool, str, str]:
    """构建默认角度报警等级命令"""
    return build_grolevel_command(0.40107, 0.573, 1.146, 2.292, 4.584)


def build_default_acclevel_command() -> Tuple[bool, str, str]:
    """构建默认加速度报警等级命令"""
    return build_acclevel_command(0.2, 0.5, 1.0, 2.0, 4.0)


# ============================================================================
# 预设配置
# ============================================================================

# 角度报警等级预设 (单位: 度)
GROLEVEL_PRESETS = {
    'default': [0.40107, 0.573, 1.146, 2.292, 4.584],
    'strict': [0.1, 0.3, 0.5, 1.0, 2.0],
    'relaxed': [1.0, 2.0, 4.0, 8.0, 15.0],
}

# 加速度报警等级预设 (单位: m/s²)
ACCLEVEL_PRESETS = {
    'default': [0.2, 0.5, 1.0, 2.0, 4.0],
    'strict': [0.05, 0.1, 0.2, 0.5, 1.0],
    'relaxed': [0.5, 1.0, 2.0, 5.0, 10.0],
}


def get_grolevel_preset(name: str) -> List[float]:
    """获取角度报警等级预设"""
    return GROLEVEL_PRESETS.get(name, GROLEVEL_PRESETS['default'])


def get_acclevel_preset(name: str) -> List[float]:
    """获取加速度报警等级预设"""
    return ACCLEVEL_PRESETS.get(name, ACCLEVEL_PRESETS['default'])


def get_all_grolevel_presets() -> List[Tuple[str, List[float]]]:
    """获取所有角度报警等级预设"""
    return [(name, values) for name, values in GROLEVEL_PRESETS.items()]


def get_all_acclevel_presets() -> List[Tuple[str, List[float]]]:
    """获取所有加速度报警等级预设"""
    return [(name, values) for name, values in ACCLEVEL_PRESETS.items()]


# ============================================================================
# 等级描述
# ============================================================================

LEVEL_DESCRIPTIONS = {
    1: "等级1 - 轻微异常 (黄色预警)",
    2: "等级2 - 一般异常 (橙色预警)",
    3: "等级3 - 严重异常 (红色预警)",
    4: "等级4 - 危险状态 (紧急处理)",
    5: "等级5 - 极度危险 (立即撤离)",
}


def get_level_description(level: int) -> str:
    """获取报警等级描述"""
    return LEVEL_DESCRIPTIONS.get(level, f"等级{level}")
