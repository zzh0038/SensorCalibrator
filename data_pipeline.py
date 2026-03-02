import queue
import threading
from typing import Any, Dict, Optional


class DataHub:
    """
    简单的数据分发中心，用于在多个消费者之间广播解析后的传感器样本。

    - 每个订阅者拥有自己的 Queue，不会互相抢占数据
    - 发布样本时尝试放入每个订阅者队列，满时丢弃最旧数据
    """

    def __init__(self, max_queue_size: int = 1000, logger=None) -> None:
        self._subscribers: Dict[str, "queue.Queue[Any]"] = {}
        self._sub_lock = threading.Lock()
        self._max_queue_size = max_queue_size
        self._logger = logger

    def register_subscriber(
        self, name: str, maxsize: Optional[int] = None
    ) -> "queue.Queue[Any]":
        q: "queue.Queue[Any]" = queue.Queue(maxsize=maxsize or self._max_queue_size)
        with self._sub_lock:
            self._subscribers[name] = q
        return q

    def unregister_subscriber(self, name: str) -> None:
        with self._sub_lock:
            self._subscribers.pop(name, None)

    def publish_sample(self, sample: Any) -> None:
        with self._sub_lock:
            items = list(self._subscribers.items())

        for name, q in items:
            try:
                if q.full():
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        pass
                q.put_nowait(sample)
            except queue.Full:
                # 队列满时丢弃数据，不中断其他订阅者
                if self._logger:
                    try:
                        self._logger(f"DataHub: queue full for subscriber '{name}'")
                    except (AttributeError, TypeError):
                        pass
            except Exception:
                # 其他意外错误，记录后继续处理其他订阅者
                if self._logger:
                    try:
                        self._logger(f"DataHub: failed to publish to subscriber '{name}'")
                    except (AttributeError, TypeError):
                        pass

