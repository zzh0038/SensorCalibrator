"""
UI 模块 - 传感器校准系统界面组件

重构后的模块化结构:
- base: 基础 Section 类
- theme: 主题管理
- sections/: 各个功能区块
  - serial: 串口设置
  - data_stream: 数据流控制
  - calibration: 校准控制
  - statistics: 统计显示
  - commands: 命令区域
  - coordinate: 坐标模式
  - activation: 激活状态
  - network: 网络配置 (含 WiFi/MQTT/OTA/Cloud/Position)
  - system: 系统控制
  - dashboard: 仪表盘

向后兼容: UIManager 仍可从 sensor_calibrator.ui_manager 导入
"""

# 主题
from .theme import LightTheme, theme_manager

# 基础类
from .base import BaseSection

# 为了向后兼容，UIManager 仍在原位置
# from ..ui_manager import UIManager

__all__ = [
    'LightTheme',
    'theme_manager',
    'BaseSection',
]
