"""
SensorCalibrator Install Mode Module

传感器安装模式配置管理。
提供 SET:ISG 命令构建功能。
"""

from typing import Tuple, Dict
from enum import IntEnum


class InstallMode(IntEnum):
    """
    传感器安装模式枚举
    
    根据文档，模式 0-12 分别对应不同的安装位置和方向
    """
    DEFAULT = 0           # 默认模式
    GROUND_1 = 1          # 地面安装 - 模式1
    GROUND_2 = 2          # 地面安装 - 模式2
    SIDE_1 = 3            # 侧面安装 - 模式1
    SIDE_2 = 4            # 侧面安装 - 模式2
    SIDE_3 = 5            # 侧面安装 - 模式3
    SIDE_4 = 6            # 侧面安装 - 模式4
    TOP_1 = 7             # 顶部安装 - 模式1
    TOP_2 = 8             # 顶部安装 - 模式2
    TOP_3 = 9             # 顶部安装 - 模式3
    TOP_4 = 10            # 顶部安装 - 模式4
    TOP_5 = 11            # 顶部安装 - 模式5
    TOP_6 = 12            # 顶部安装 - 模式6


# 安装模式描述（中文和英文）
INSTALL_MODE_DESCRIPTIONS: Dict[int, str] = {
    InstallMode.DEFAULT: "默认模式 (Default)",
    InstallMode.GROUND_1: "地面安装-模式1 (Ground Mode 1)",
    InstallMode.GROUND_2: "地面安装-模式2 (Ground Mode 2)",
    InstallMode.SIDE_1: "侧面安装-模式1 (Side Mode 1)",
    InstallMode.SIDE_2: "侧面安装-模式2 (Side Mode 2)",
    InstallMode.SIDE_3: "侧面安装-模式3 (Side Mode 3)",
    InstallMode.SIDE_4: "侧面安装-模式4 (Side Mode 4)",
    InstallMode.TOP_1: "顶部安装-模式1 (Top Mode 1)",
    InstallMode.TOP_2: "顶部安装-模式2 (Top Mode 2)",
    InstallMode.TOP_3: "顶部安装-模式3 (Top Mode 3)",
    InstallMode.TOP_4: "顶部安装-模式4 (Top Mode 4)",
    InstallMode.TOP_5: "顶部安装-模式5 (Top Mode 5)",
    InstallMode.TOP_6: "顶部安装-模式6 (Top Mode 6)",
}

# 安装位置分类
INSTALL_MODE_CATEGORIES: Dict[int, str] = {
    InstallMode.DEFAULT: "default",
    InstallMode.GROUND_1: "ground",
    InstallMode.GROUND_2: "ground",
    InstallMode.SIDE_1: "side",
    InstallMode.SIDE_2: "side",
    InstallMode.SIDE_3: "side",
    InstallMode.SIDE_4: "side",
    InstallMode.TOP_1: "top",
    InstallMode.TOP_2: "top",
    InstallMode.TOP_3: "top",
    InstallMode.TOP_4: "top",
    InstallMode.TOP_5: "top",
    InstallMode.TOP_6: "top",
}

# 分类名称
CATEGORY_NAMES: Dict[str, str] = {
    "default": "默认",
    "ground": "地面 (地)",
    "side": "侧面 (侧)",
    "top": "顶部 (顶)",
}

# 有效的模式值范围
MIN_MODE = 0
MAX_MODE = 12


def validate_install_mode(mode: int) -> Tuple[bool, str]:
    """
    验证安装模式值是否有效
    
    Args:
        mode: 安装模式值 (0-12)
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not isinstance(mode, int):
        return False, f"Install mode must be an integer, got {type(mode).__name__}"
    
    if mode < MIN_MODE or mode > MAX_MODE:
        return False, f"Install mode must be between {MIN_MODE} and {MAX_MODE}, got {mode}"
    
    return True, ""


def build_isg_command(mode: int) -> Tuple[bool, str, str]:
    """
    构建 SET:ISG 命令 - 设置传感器安装模式
    
    格式: SET:ISG,<mode>
    
    Args:
        mode: 安装模式 (0-12)
              0 = 默认模式
              1-2 = 地面安装模式
              3-6 = 侧面安装模式
              7-12 = 顶部安装模式
              
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_isg_command(0)
        (True, "", "SET:ISG,0")
        
        >>> build_isg_command(3)
        (True, "", "SET:ISG,3")
    """
    # 验证模式值
    valid, error = validate_install_mode(mode)
    if not valid:
        return False, error, ""
    
    # 构建命令
    cmd = f"SET:ISG,{mode}"
    return True, "", cmd


def get_mode_description(mode: int) -> str:
    """
    获取安装模式的描述文本
    
    Args:
        mode: 安装模式值
        
    Returns:
        模式描述字符串，如果无效则返回 "Unknown"
    """
    return INSTALL_MODE_DESCRIPTIONS.get(mode, f"Unknown Mode ({mode})")


def get_mode_category(mode: int) -> str:
    """
    获取安装模式的分类（地面/侧面/顶部）
    
    Args:
        mode: 安装模式值
        
    Returns:
        分类代码 (default/ground/side/top)
    """
    return INSTALL_MODE_CATEGORIES.get(mode, "unknown")


def get_category_display_name(category: str) -> str:
    """
    获取分类的显示名称
    
    Args:
        category: 分类代码
        
    Returns:
        分类的显示名称
    """
    return CATEGORY_NAMES.get(category, category)


def get_modes_by_category(category: str) -> list:
    """
    获取指定分类下的所有安装模式
    
    Args:
        category: 分类代码 (default/ground/side/top)
        
    Returns:
        该分类下的所有模式值列表
    """
    return [mode for mode, cat in INSTALL_MODE_CATEGORIES.items() if cat == category]


# ============================================================================
# UI 辅助函数
# ============================================================================

def get_all_modes_for_ui() -> list:
    """
    获取用于UI下拉框的所有模式选项
    
    Returns:
        列表，每项为 (mode_value, display_text) 元组
    """
    return [
        (mode, f"{mode} - {description}")
        for mode, description in sorted(INSTALL_MODE_DESCRIPTIONS.items())
    ]


def get_modes_grouped_by_category() -> Dict[str, list]:
    """
    按分类分组获取所有安装模式
    
    Returns:
        字典，键为分类代码，值为该分类下的模式列表
        每项为 (mode_value, display_text) 元组
    """
    result = {}
    for category in ["default", "ground", "side", "top"]:
        modes = get_modes_by_category(category)
        result[category] = [
            (mode, f"{mode} - {INSTALL_MODE_DESCRIPTIONS[mode]}")
            for mode in sorted(modes)
        ]
    return result


def suggest_mode_by_installation(
    location: str,
    orientation: str = ""
) -> int:
    """
    根据安装位置和方向建议合适的安装模式
    
    Args:
        location: 安装位置 ("ground"/"side"/"top")
        orientation: 具体方向或编号
        
    Returns:
        建议的安装模式值
    """
    location = location.lower().strip()
    
    if location in ["ground", "地", "地面", "地板"]:
        return InstallMode.GROUND_1
    elif location in ["side", "侧", "侧面", "墙壁", "墙"]:
        return InstallMode.SIDE_1
    elif location in ["top", "顶", "顶部", "天花板", "吊顶"]:
        return InstallMode.TOP_1
    else:
        return InstallMode.DEFAULT


# ============================================================================
# 便捷函数
# ============================================================================

def build_default_mode_command() -> Tuple[bool, str, str]:
    """构建设置为默认模式的命令"""
    return build_isg_command(InstallMode.DEFAULT)


def build_ground_mode_command(variant: int = 1) -> Tuple[bool, str, str]:
    """
    构建设置为地面安装模式的命令
    
    Args:
        variant: 地面模式变体 (1 或 2)
    """
    if variant == 1:
        return build_isg_command(InstallMode.GROUND_1)
    elif variant == 2:
        return build_isg_command(InstallMode.GROUND_2)
    else:
        return False, "Ground mode variant must be 1 or 2", ""


def build_side_mode_command(variant: int = 1) -> Tuple[bool, str, str]:
    """
    构建设置为侧面安装模式的命令
    
    Args:
        variant: 侧面模式变体 (1-4)
    """
    mode_map = {1: InstallMode.SIDE_1, 2: InstallMode.SIDE_2, 
                3: InstallMode.SIDE_3, 4: InstallMode.SIDE_4}
    if variant in mode_map:
        return build_isg_command(mode_map[variant])
    else:
        return False, "Side mode variant must be 1-4", ""


def build_top_mode_command(variant: int = 1) -> Tuple[bool, str, str]:
    """
    构建设置为顶部安装模式的命令
    
    Args:
        variant: 顶部模式变体 (1-6)
    """
    mode_map = {1: InstallMode.TOP_1, 2: InstallMode.TOP_2, 3: InstallMode.TOP_3,
                4: InstallMode.TOP_4, 5: InstallMode.TOP_5, 6: InstallMode.TOP_6}
    if variant in mode_map:
        return build_isg_command(mode_map[variant])
    else:
        return False, "Top mode variant must be 1-6", ""
