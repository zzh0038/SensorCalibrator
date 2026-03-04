"""
Ring Buffer Module - 高性能环形缓冲区

为高频数据采集场景优化的队列实现：
- 满时自动覆盖最旧数据（单操作）
- 减少锁竞争
- 支持批量操作
"""

import threading
from typing import Optional, List, TypeVar, Generic

T = TypeVar('T')


class RingBuffer(Generic[T]):
    """
    线程安全的环形缓冲区
    
    特点：
    - 固定容量，满时自动覆盖最旧数据
    - 相比 queue.Queue，满队列处理只需单次操作
    - 支持批量放入/取出，减少锁竞争
    """
    
    def __init__(self, capacity: int = 1024) -> None:
        """
        初始化环形缓冲区
        
        Args:
            capacity: 缓冲区容量，默认1024
        """
        self._capacity = capacity
        self._buffer: List[Optional[T]] = [None] * capacity
        self._head = 0  # 写入位置
        self._tail = 0  # 读取位置
        self._size = 0  # 当前元素数量
        self._lock = threading.Lock()
    
    def put(self, item: T) -> None:
        """
        放入一个元素
        
        如果缓冲区已满，自动覆盖最旧的数据
        
        Args:
            item: 要放入的元素
        """
        with self._lock:
            self._buffer[self._head] = item
            self._head = (self._head + 1) % self._capacity
            
            if self._size < self._capacity:
                self._size += 1
            else:
                # 满时覆盖，读取位置也前移
                self._tail = self._head
    
    def get(self) -> Optional[T]:
        """
        取出一个元素
        
        Returns:
            最旧的元素，如果为空返回 None
        """
        with self._lock:
            if self._size == 0:
                return None
            
            item = self._buffer[self._tail]
            self._buffer[self._tail] = None  # 帮助GC
            self._tail = (self._tail + 1) % self._capacity
            self._size -= 1
            return item
    
    def get_all(self) -> List[T]:
        """
        取出所有元素（批量操作）
        
        减少多次获取时的锁竞争
        
        Returns:
            所有元素的列表
        """
        with self._lock:
            if self._size == 0:
                return []
            
            items = []
            for _ in range(self._size):
                items.append(self._buffer[self._tail])
                self._buffer[self._tail] = None
                self._tail = (self._tail + 1) % self._capacity
            
            self._size = 0
            return items
    
    def put_batch(self, items: List[T]) -> None:
        """
        批量放入元素
        
        Args:
            items: 要放入的元素列表
        """
        with self._lock:
            for item in items:
                self._buffer[self._head] = item
                self._head = (self._head + 1) % self._capacity
                
                if self._size < self._capacity:
                    self._size += 1
                else:
                    self._tail = self._head
    
    def full(self) -> bool:
        """检查缓冲区是否已满"""
        with self._lock:
            return self._size >= self._capacity
    
    def empty(self) -> bool:
        """检查缓冲区是否为空"""
        with self._lock:
            return self._size == 0
    
    def qsize(self) -> int:
        """获取当前元素数量"""
        with self._lock:
            return self._size
    
    def clear(self) -> None:
        """清空缓冲区"""
        with self._lock:
            self._buffer = [None] * self._capacity
            self._head = 0
            self._tail = 0
            self._size = 0
    
    def __len__(self) -> int:
        """返回元素数量"""
        return self.qsize()


# 为了保持与 queue.Queue 接口兼容的适配器
class QueueAdapter:
    """
    RingBuffer 的 Queue 接口适配器
    
    使 RingBuffer 可以无缝替换 queue.Queue
    """
    
    def __init__(self, capacity: int = 1024):
        self._buffer = RingBuffer(capacity)
        self.maxsize = capacity
    
    def put(self, item, block=True, timeout=None):
        """兼容 Queue.put 接口"""
        self._buffer.put(item)
    
    def put_nowait(self, item):
        """兼容 Queue.put_nowait 接口"""
        self._buffer.put(item)
    
    def put_batch(self, items):
        """批量放入元素（高效率接口）"""
        self._buffer.put_batch(items)
    
    def get(self, block=True, timeout=None):
        """兼容 Queue.get 接口"""
        item = self._buffer.get()
        if item is None:
            raise Exception("Queue is empty")  # 模拟 Queue 行为
        return item
    
    def get_nowait(self):
        """兼容 Queue.get_nowait 接口"""
        return self.get(block=False)
    
    def full(self):
        """兼容 Queue.full 接口"""
        return self._buffer.full()
    
    def empty(self):
        """兼容 Queue.empty 接口"""
        return self._buffer.empty()
    
    def qsize(self):
        """兼容 Queue.qsize 接口"""
        return self._buffer.qsize()
