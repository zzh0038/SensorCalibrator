"""
SensorCalibrator Position Configuration Module

设备位置和属性配置管理。
提供 SET:PO 命令构建功能。
"""

import re
from typing import Tuple, List


# 行政区划路径验证
# 格式: /省/市/县/街道 或 /省/市/区/街道
REGION_PATH_PATTERN = re.compile(r'^(/[a-zA-Z\u4e00-\u9fa5]+){3,6}$')

# 建筑类型有效值
VALID_BUILDING_TYPES = {
    'zhuzhai', '住宅', 'residential',
    'shangye', '商业', 'commercial',
    'gongye', '工业', 'industrial',
    'bangong', '办公', 'office',
    'qita', '其他', 'other',
}

# 字段长度限制
MAX_REGION_LENGTH = 128
MAX_BUILDING_TYPE_LENGTH = 32
MAX_USER_ATTR_LENGTH = 64
MAX_DEVICE_NAME_LENGTH = 32


def validate_region_path(region: str) -> Tuple[bool, str]:
    """
    验证行政区划路径格式
    
    格式要求:
    - 以 / 开头
    - 各级之间用 / 分隔
    - 至少3级 (省/市/县)
    - 最多6级 (省/市/县/街道/社区/楼宇)
    - 支持中文和英文
    
    Args:
        region: 行政区划路径，如 "/Shandong/RiZhao/Juxian/Guanbao"
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not region:
        return False, "Region path cannot be empty"
    
    region = region.strip()
    
    if len(region) > MAX_REGION_LENGTH:
        return False, f"Region path too long (max {MAX_REGION_LENGTH} chars)"
    
    # 检查基本格式
    if not region.startswith('/'):
        return False, "Region path must start with '/'"
    
    # 分割各级
    parts = [p for p in region.split('/') if p]
    
    if len(parts) < 3:
        return False, f"Region path must have at least 3 levels (province/city/district), got {len(parts)}"
    
    if len(parts) > 6:
        return False, f"Region path too many levels (max 6), got {len(parts)}"
    
    # 检查每级内容
    for i, part in enumerate(parts):
        if not part:
            return False, f"Level {i+1} is empty"
        
        # 检查非法字符
        if not re.match(r'^[a-zA-Z0-9\u4e00-\u9fa5_-]+$', part):
            return False, f"Level {i+1} '{part}' contains invalid characters"
        
        # 每级长度限制
        if len(part) > 32:
            return False, f"Level {i+1} too long (max 32 chars)"
    
    return True, ""


def validate_building_type(building_type: str) -> Tuple[bool, str]:
    """
    验证建筑类型
    
    Args:
        building_type: 建筑类型，如 "Zhuzhai", "住宅"
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not building_type:
        return False, "Building type cannot be empty"
    
    building_type = building_type.strip()
    
    if len(building_type) > MAX_BUILDING_TYPE_LENGTH:
        return False, f"Building type too long (max {MAX_BUILDING_TYPE_LENGTH} chars)"
    
    # 检查是否是预定义类型（不区分大小写）
    if building_type.lower() not in VALID_BUILDING_TYPES:
        # 如果不是预定义类型，只允许字母、数字、下划线
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', building_type):
            return False, f"Building type contains invalid characters"
    
    return True, ""


def validate_user_attribute(user_attr: str) -> Tuple[bool, str]:
    """
    验证用户属性
    
    Args:
        user_attr: 用户属性，如 "Gonglisuo-201202"
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not user_attr:
        return False, "User attribute cannot be empty"
    
    user_attr = user_attr.strip()
    
    if len(user_attr) > MAX_USER_ATTR_LENGTH:
        return False, f"User attribute too long (max {MAX_USER_ATTR_LENGTH} chars)"
    
    # 用户属性通常包含字母、数字、连字符、下划线
    if not re.match(r'^[a-zA-Z0-9_\-\u4e00-\u9fa5]+$', user_attr):
        return False, "User attribute contains invalid characters"
    
    return True, ""


def validate_device_name(device_name: str) -> Tuple[bool, str]:
    """
    验证监测仪名称
    
    Args:
        device_name: 监测仪名称，如 "HLSYZG-01010001"
        
    Returns:
        (is_valid, error_message) 元组
    """
    if not device_name:
        return False, "Device name cannot be empty"
    
    device_name = device_name.strip()
    
    if len(device_name) > MAX_DEVICE_NAME_LENGTH:
        return False, f"Device name too long (max {MAX_DEVICE_NAME_LENGTH} chars)"
    
    # 监测仪名称通常包含字母、数字、连字符
    if not re.match(r'^[a-zA-Z0-9_\-]+$', device_name):
        return False, "Device name must contain only alphanumeric, underscore, or hyphen"
    
    return True, ""


def build_po_command(
    region: str,
    building_type: str,
    user_attr: str,
    device_name: str
) -> Tuple[bool, str, str]:
    """
    构建 SET:PO 命令 - 配置设备行政区划和属性
    
    格式: SET:PO,<region>,<building_type>,<user_attr>,<device_name>
    
    Args:
        region: 行政区划路径，如 "/Shandong/RiZhao/Juxian/Guanbao"
        building_type: 建筑属性，如 "Zhuzhai" (住宅)
        user_attr: 用户属性，如 "Gonglisuo-201202"
        device_name: 监测仪名称，如 "HLSYZG-01010001"
        
    Returns:
        (success, error_message, command) 元组
        
    Example:
        >>> build_po_command(
        ...     "/Shandong/RiZhao/Juxian/Guanbao",
        ...     "Zhuzhai",
        ...     "Gonglisuo-201202",
        ...     "HLSYZG-01010001"
        ... )
        (True, "", "SET:PO,/Shandong/RiZhao/Juxian/Guanbao,Zhuzhai,Gonglisuo-201202,HLSYZG-01010001")
    """
    # 验证行政区划路径
    valid, error = validate_region_path(region)
    if not valid:
        return False, f"Invalid region path: {error}", ""
    
    # 验证建筑类型
    valid, error = validate_building_type(building_type)
    if not valid:
        return False, f"Invalid building type: {error}", ""
    
    # 验证用户属性
    valid, error = validate_user_attribute(user_attr)
    if not valid:
        return False, f"Invalid user attribute: {error}", ""
    
    # 验证监测仪名称
    valid, error = validate_device_name(device_name)
    if not valid:
        return False, f"Invalid device name: {error}", ""
    
    # 构建命令
    cmd = f"SET:PO,{region.strip()},{building_type.strip()},{user_attr.strip()},{device_name.strip()}"
    return True, "", cmd


# ============================================================================
# 辅助函数
# ============================================================================

def parse_region_path(region: str) -> List[str]:
    """
    解析行政区划路径为各级列表
    
    Args:
        region: 行政区划路径，如 "/Shandong/RiZhao/Juxian/Guanbao"
        
    Returns:
        各级名称列表
        
    Example:
        >>> parse_region_path("/Shandong/RiZhao/Juxian/Guanbao")
        ['Shandong', 'RiZhao', 'Juxian', 'Guanbao']
    """
    if not region:
        return []
    
    return [p for p in region.strip().split('/') if p]


def get_region_level_name(level: int) -> str:
    """
    获取行政区划级别的中文名称
    
    Args:
        level: 级别索引 (0-based)
        
    Returns:
        级别名称
    """
    level_names = ['省/直辖市', '市', '区/县', '街道/镇', '社区/村', '楼宇']
    if 0 <= level < len(level_names):
        return level_names[level]
    return f"级别{level+1}"


def format_region_display(region: str) -> str:
    """
    格式化行政区划路径为显示文本
    
    Args:
        region: 原始路径
        
    Returns:
        格式化后的显示文本
        
    Example:
        >>> format_region_display("/Shandong/RiZhao/Juxian/Guanbao")
        '山东省 > 日照市 > 莒县 > 管鲍街道'
    """
    parts = parse_region_path(region)
    if not parts:
        return ""
    
    # 简单添加常见的后缀（不完美，但用于显示）
    suffixes = ['省', '市', '县', '街道', '', '']
    formatted = []
    for i, part in enumerate(parts):
        suffix = suffixes[i] if i < len(suffixes) else ''
        # 如果已经以这些字结尾，不再添加
        if any(part.endswith(s) for s in ['省', '市', '县', '区', '街道', '镇']):
            formatted.append(part)
        else:
            formatted.append(part + suffix)
    
    return ' > '.join(formatted)


# ============================================================================
# 预设值
# ============================================================================

# 常见建筑类型选项（用于UI下拉框）
BUILDING_TYPE_OPTIONS = [
    ('zhuzhai', '住宅 (Residential)'),
    ('shangye', '商业 (Commercial)'),
    ('gongye', '工业 (Industrial)'),
    ('bangong', '办公 (Office)'),
    ('qita', '其他 (Other)'),
]

# 示例行政区划（用于UI提示）
REGION_EXAMPLES = [
    '/Shandong/RiZhao/Juxian/Guanbao',
    '/Beijing/Haidian/Zhongguancun',
    '/Shanghai/Pudong/Lujiazui',
]
