"""
基础 Section 类 - 所有 UI 区块的基类

提供统一的接口和通用功能，简化 UIManager 的实现。
"""

import tkinter as tk
from tkinter import ttk, StringVar
from typing import Dict, Callable, Any, Optional, List
from abc import ABC, abstractmethod

from .theme import LightTheme


class BaseSection(ABC):
    """
    UI 区块基类
    
    所有功能区块应继承此类，实现统一的接口。
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        callbacks: Dict[str, Callable],
        widgets: Dict[str, Any],
        vars: Dict[str, StringVar]
    ):
        """
        初始化区块
        
        Args:
            parent: 父容器
            callbacks: 回调函数字典
            widgets: 控件引用字典（共享）
            vars: 变量字典（共享）
        """
        self.parent = parent
        self.callbacks = callbacks
        self.widgets = widgets
        self.vars = vars
        self.t = LightTheme
        
    @abstractmethod
    def setup(self) -> None:
        """设置区块 UI - 子类必须实现"""
        pass
    
    def create_frame(
        self,
        parent: Optional[tk.Widget] = None,
        text: Optional[str] = None,
        **kwargs
    ) -> tk.Widget:
        """
        创建框架
        
        Args:
            parent: 父容器，默认 self.parent
            text: LabelFrame 标题，None 则创建普通 Frame
            **kwargs: 额外的配置参数
            
        Returns:
            创建的框架
        """
        parent = parent or self.parent
        bg = kwargs.pop('bg', self.t.BG_MAIN)
        
        if text:
            # 使用 LabelFrame，但用 tk.Frame 包装以控制背景
            outer = tk.Frame(parent, bg=bg)
            outer.pack(fill="x", pady=(0, 5))
            
            frame = tk.LabelFrame(
                outer,
                text=text,
                bg=self.t.BG_CARD,
                fg=self.t.TEXT_PRIMARY,
                font=("Segoe UI", 9, "bold"),
                padx=5,
                pady=5
            )
            frame.pack(fill="x", padx=5, pady=5)
        else:
            frame = tk.Frame(parent, bg=bg, **kwargs)
            
        return frame
    
    def create_button(
        self,
        parent: tk.Widget,
        text: str,
        callback_key: str,
        **kwargs
    ) -> ttk.Button:
        """
        创建按钮
        
        Args:
            parent: 父容器
            text: 按钮文本
            callback_key: 回调函数在 callbacks 中的键
            **kwargs: 额外配置
            
        Returns:
            创建的按钮
        """
        callback = self.callbacks.get(callback_key, lambda: None)
        btn = ttk.Button(parent, text=text, command=callback, **kwargs)
        return btn
    
    def create_entry(
        self,
        parent: tk.Widget,
        var_key: str,
        width: int = 20,
        **kwargs
    ) -> ttk.Entry:
        """
        创建输入框
        
        Args:
            parent: 父容器
            var_key: 变量键名，会自动创建 StringVar
            width: 宽度
            **kwargs: 额外配置
            
        Returns:
            创建的输入框
        """
        var = StringVar()
        self.vars[var_key] = var
        
        entry = ttk.Entry(parent, textvariable=var, width=width, **kwargs)
        return entry
    
    def create_combobox(
        self,
        parent: tk.Widget,
        var_key: str,
        values: List[str],
        width: int = 20,
        readonly: bool = True,
        **kwargs
    ) -> ttk.Combobox:
        """
        创建下拉框
        
        Args:
            parent: 父容器
            var_key: 变量键名
            values: 选项列表
            width: 宽度
            readonly: 是否只读
            **kwargs: 额外配置
            
        Returns:
            创建的下拉框
        """
        var = StringVar()
        self.vars[var_key] = var
        
        state = "readonly" if readonly else "normal"
        combo = ttk.Combobox(
            parent,
            textvariable=var,
            values=values,
            width=width,
            state=state,
            **kwargs
        )
        return combo
    
    def create_label(
        self,
        parent: tk.Widget,
        text: str,
        is_title: bool = False,
        **kwargs
    ) -> tk.Label:
        """
        创建标签
        
        Args:
            parent: 父容器
            text: 标签文本
            is_title: 是否标题样式
            **kwargs: 额外配置
            
        Returns:
            创建的标签
        """
        font = ("Segoe UI", 10, "bold") if is_title else ("Segoe UI", 9)
        fg = kwargs.pop('fg', self.t.TEXT_PRIMARY)
        bg = kwargs.pop('bg', self.t.BG_CARD)
        
        label = tk.Label(
            parent,
            text=text,
            font=font,
            fg=fg,
            bg=bg,
            **kwargs
        )
        return label
    
    def enable_widget(self, key: str, enabled: bool = True) -> None:
        """启用/禁用控件"""
        if key in self.widgets:
            widget = self.widgets[key]
            state = "normal" if enabled else "disabled"
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass  # 某些控件可能不支持 state
    
    def get_var(self, key: str) -> Optional[StringVar]:
        """获取变量"""
        return self.vars.get(key)
    
    def get_widget(self, key: str) -> Optional[Any]:
        """获取控件"""
        return self.widgets.get(key)
