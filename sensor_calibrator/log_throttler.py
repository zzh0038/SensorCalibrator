"""
Log Throttler Module - 日志限流器

防止高频日志输出导致 UI 卡顿
"""

import time
from typing import Callable, Optional, List
from collections import deque


class LogThrottler:
    """
    日志限流器
    
    功能：
    - 限制日志输出频率
    - 批量输出非紧急日志
    - 紧急日志（ERROR）立即输出
    
    优化：
    - 使用 __slots__ 减少内存占用
    """
    
    # 优化：__slots__ 减少内存占用
    __slots__ = ['interval', 'max_buffer_size', 'immediate_levels', 
                 '_buffer', '_last_flush', '_log_func']
    
    def __init__(self, 
                 interval_ms: float = 100.0,
                 max_buffer_size: int = 100,
                 immediate_levels: Optional[set] = None):
        """
        初始化日志限流器
        
        Args:
            interval_ms: 日志输出间隔（毫秒）
            max_buffer_size: 最大缓冲数量
            immediate_levels: 立即输出的日志级别集合，默认 {"ERROR"}
        """
        self.interval = interval_ms / 1000.0  # 转换为秒
        self.max_buffer_size = max_buffer_size
        self.immediate_levels = immediate_levels or {"ERROR"}
        
        self._buffer: deque = deque(maxlen=max_buffer_size)
        self._last_flush = time.perf_counter()  # 初始化为当前时间，避免立即刷新
        self._log_func: Optional[Callable[[str], None]] = None
    
    def set_log_function(self, log_func: Callable[[str], None]) -> None:
        """
        设置实际的日志输出函数
        
        Args:
            log_func: 日志输出函数，接收字符串参数
        """
        self._log_func = log_func
    
    def log(self, message: str, level: str = "INFO") -> None:
        """
        记录日志
        
        Args:
            message: 日志消息
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        """
        if self._log_func is None:
            return
        
        # 错误级别立即输出
        if level in self.immediate_levels:
            self._flush()
            self._log_func(f"[{level}] {message}")
            self._last_flush = time.perf_counter()
            return
        
        # 添加到缓冲区
        self._buffer.append((level, message))
        
        # 检查是否需要刷新
        current = time.perf_counter()
        if current - self._last_flush >= self.interval:
            self._flush()
            self._last_flush = current
    
    def _flush(self) -> None:
        """刷新缓冲区，输出所有待处理的日志"""
        if not self._buffer or self._log_func is None:
            return
        
        # 合并相同级别的连续日志
        if len(self._buffer) > 1:
            # 批量输出提示
            count = len(self._buffer)
            self._log_func(f"[BATCH] {count} messages:")
            
            # 输出前10条，如果有更多则显示省略
            for i, (level, msg) in enumerate(self._buffer):
                if i >= 10:
                    remaining = count - 10
                    self._log_func(f"  ... and {remaining} more")
                    break
                self._log_func(f"  [{level}] {msg}")
        else:
            # 单条直接输出
            level, msg = self._buffer[0]
            self._log_func(f"[{level}] {msg}")
        
        self._buffer.clear()
    
    def force_flush(self) -> None:
        """强制刷新缓冲区"""
        self._flush()
        self._last_flush = time.perf_counter()


class CountingLogThrottler(LogThrottler):
    """
    计数型日志限流器 - 适用于高频重复消息的压缩
    
    将重复的消息压缩为 "消息内容 (x重复次数)"
    
    优化：
    - 使用 __slots__ 减少内存占用
    - 注意：继承父类的 __slots__，无需重复定义
    """
    
    # 注意：子类自动继承父类的 __slots__，只需要添加新增的属性
    __slots__ = ['_message_counts']
    
    def __init__(self, 
                 interval_ms: float = 500.0,
                 max_buffer_size: int = 100):
        super().__init__(interval_ms, max_buffer_size)
        self._message_counts: dict = {}
    
    def log(self, message: str, level: str = "INFO") -> None:
        """
        记录日志（自动计数重复消息）
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        if self._log_func is None:
            return
        
        # 错误级别立即输出
        if level in self.immediate_levels:
            self._flush()
            self._log_func(f"[{level}] {message}")
            self._last_flush = time.perf_counter()
            return
        
        # 计数
        key = (level, message)
        if key in self._message_counts:
            self._message_counts[key] += 1
        else:
            self._message_counts[key] = 1
            self._buffer.append(key)
        
        # 检查是否需要刷新
        current = time.perf_counter()
        if current - self._last_flush >= self.interval:
            self._flush()
            self._last_flush = current
    
    def _flush(self) -> None:
        """刷新缓冲区，输出带计数的日志"""
        if not self._buffer or self._log_func is None:
            return
        
        for key in self._buffer:
            level, message = key
            count = self._message_counts[key]
            if count > 1:
                self._log_func(f"[{level}] {message} (x{count})")
            else:
                self._log_func(f"[{level}] {message}")
        
        self._buffer.clear()
        self._message_counts.clear()
