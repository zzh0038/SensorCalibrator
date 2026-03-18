"""
SensorCalibrator UI Theme Module

主题管理系统，提供浅色现代主题支持。
"""

from typing import Dict, Callable, List
import tkinter as tk
from tkinter import ttk


class LightTheme:
    """浅色现代主题配色方案"""
    
    # 主色调
    PRIMARY = "#0078d4"           # 微软蓝
    PRIMARY_HOVER = "#106ebe"     # 悬停蓝
    PRIMARY_LIGHT = "#e5f1fb"     # 浅蓝背景
    PRIMARY_DARK = "#005a9e"      # 深蓝（激活）
    
    # 背景色
    BG_MAIN = "#f8f9fa"           # 主背景（淡灰白）
    BG_CARD = "#ffffff"           # 卡片背景（纯白）
    BG_SIDEBAR = "#f3f4f6"        # 侧边栏背景
    BG_INPUT = "#ffffff"          # 输入框背景
    BG_HOVER = "#f3f4f6"          # 悬停背景
    
    # 文字色
    TEXT_PRIMARY = "#202124"      # 主要文字（深灰黑）
    TEXT_SECONDARY = "#5f6368"    # 次要文字（中灰）
    TEXT_DISABLED = "#9aa0a6"     # 禁用文字（浅灰）
    TEXT_ON_PRIMARY = "#ffffff"   # 主色上的文字（白）
    
    # 边框色
    BORDER = "#dadce0"            # 默认边框
    BORDER_HOVER = "#bdc1c6"      # 悬停边框
    BORDER_FOCUS = "#0078d4"      # 聚焦边框（蓝）
    
    # 状态色
    SUCCESS = "#137333"           # 成功绿
    SUCCESS_BG = "#e6f4ea"        # 成功背景
    SUCCESS_LIGHT = "#34a853"     # 亮绿
    
    WARNING = "#f9ab00"           # 警告黄
    WARNING_BG = "#fef3e8"        # 警告背景
    
    ERROR = "#d93025"             # 错误红
    ERROR_BG = "#fce8e6"          # 错误背景
    ERROR_LIGHT = "#ea4335"       # 亮红
    
    INFO = "#0078d4"              # 信息蓝
    INFO_BG = "#e8f0fe"           # 信息背景
    
    # 图表色
    CHART_X = "#ea4335"           # 红
    CHART_Y = "#34a853"           # 绿
    CHART_Z = "#4285f4"           # 蓝
    CHART_GRAVITY = "#fbbc04"     # 黄


class ThemeManager:
    """主题管理器"""
    
    def __init__(self):
        self.theme = LightTheme
        self.callbacks: List[Callable] = []
    
    def configure_styles(self, style: ttk.Style):
        """配置ttk样式"""
        t = self.theme
        
        # 配置主框架样式
        style.configure(
            'Main.TFrame',
            background=t.BG_MAIN
        )
        
        # 配置卡片框架
        style.configure(
            'Card.TLabelframe',
            background=t.BG_CARD,
            borderwidth=0
        )
        style.configure(
            'Card.TLabelframe.Label',
            background=t.BG_CARD,
            foreground=t.TEXT_PRIMARY,
            font=('Segoe UI', 11, 'bold')
        )
        
        # 配置标题标签
        style.configure(
            'Title.TLabel',
            background=t.BG_MAIN,
            foreground=t.TEXT_PRIMARY,
            font=('Segoe UI', 16, 'bold')
        )
        
        style.configure(
            'Subtitle.TLabel',
            background=t.BG_MAIN,
            foreground=t.TEXT_SECONDARY,
            font=('Segoe UI', 10)
        )
        
        style.configure(
            'Heading.TLabel',
            background=t.BG_CARD,
            foreground=t.TEXT_PRIMARY,
            font=('Segoe UI', 12, 'bold')
        )
        
        # 配置Notebook样式 - 注意：Tab不支持background/foreground
        style.configure(
            'Custom.TNotebook',
            background=t.BG_MAIN,
            tabmargins=(2, 5, 2, 0)
        )
        style.configure(
            'Custom.TNotebook.Tab',
            font=('Segoe UI', 10),
            padding=(16, 8)
        )
        
        # 配置二级Notebook
        style.configure(
            'Secondary.TNotebook',
            background=t.BG_CARD,
            tabmargins=(2, 2, 2, 0)
        )
        style.configure(
            'Secondary.TNotebook.Tab',
            font=('Segoe UI', 9),
            padding=(12, 6)
        )


# 全局主题实例
theme_manager = ThemeManager()
