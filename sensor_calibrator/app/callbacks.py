"""
SensorCalibrator Application Callbacks

重构后的回调函数集合，使用 CallbackRegistry 按功能域组织。

向后兼容: 原有的回调字典访问方式和直接属性访问仍然支持。
"""

from typing import TYPE_CHECKING, Dict, Callable

if TYPE_CHECKING:
    from .application import SensorCalibratorApp

from .callback_groups import CallbackRegistry


class AppCallbacks:
    """
    应用回调函数集合 - 兼容层
    
    实际回调实现已迁移到 callback_groups 模块，
    此类保持向后兼容，继续提供回调字典访问方式。
    
    属性:
        registry: CallbackRegistry 实例，可直接访问分组回调
        callbacks: Dict[str, Callable] - 所有回调的字典（用于 UI 绑定）
    """
    
    def __init__(self, app: "SensorCalibratorApp"):
        """
        初始化回调函数集合
        
        Args:
            app: SensorCalibratorApp 实例
        """
        self.app = app
        self.registry = CallbackRegistry(app)
        
        # 将所有回调方法暴露为实例属性（向后兼容）
        self._expose_callbacks()
    
    def _expose_callbacks(self):
        """将所有回调暴露为 AppCallbacks 的实例属性"""
        all_callbacks = self.registry.get_all_callbacks()
        for name, callback in all_callbacks.items():
            setattr(self, name, callback)
    
    @property
    def callbacks(self) -> Dict[str, Callable]:
        """获取所有回调函数的字典（供 UI 使用）"""
        return self.registry.get_all_callbacks()
    
    # ==================== 快捷访问属性 ====================
    # 允许通过 app.callbacks.serial.refresh_ports() 方式访问
    
    @property
    def serial(self):
        """串口相关回调"""
        return self.registry.serial
    
    @property
    def data_stream(self):
        """数据流相关回调"""
        return self.registry.data_stream
    
    @property
    def calibration(self):
        """校准相关回调"""
        return self.registry.calibration
    
    @property
    def activation(self):
        """激活相关回调"""
        return self.registry.activation
    
    @property
    def network(self):
        """网络相关回调"""
        return self.registry.network
    
    @property
    def system(self):
        """系统相关回调"""
        return self.registry.system
    
    @property
    def camera(self):
        """相机相关回调"""
        return self.registry.camera
    
    # ==================== 向后兼容字典访问 ====================
    
    def __getitem__(self, key: str) -> Callable:
        """支持 callbacks['key'] 语法"""
        return self.registry[key]
    
    def __contains__(self, key: str) -> bool:
        """支持 'key' in callbacks 语法"""
        return key in self.registry
    
    def get(self, key: str, default=None) -> Callable:
        """支持 callbacks.get('key') 语法"""
        return self.registry.get(key, default)
    
    def keys(self):
        """返回所有回调键名"""
        return self.registry.get_all_callbacks().keys()
    
    def values(self):
        """返回所有回调函数"""
        return self.registry.get_all_callbacks().values()
    
    def items(self):
        """返回所有回调项"""
        return self.registry.get_all_callbacks().items()
