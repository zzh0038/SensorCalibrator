import queue
import threading
import time
from typing import Callable, List, Optional, Tuple

import serial


LineListener = Callable[[str], None]


class SerialManager:
    """
    统一管理串口的打开/关闭、写入以及读取线程，并通过监听回调分发每一行数据。

    - 只维护一个底层 serial.Serial 实例和一个读取线程
    - 写操作通过内部锁进行串行化
    - 读取线程按行解析数据，并调用已注册的监听回调
    """

    def __init__(self, logger: Optional[Callable[[str], None]] = None) -> None:
        self._ser: Optional[serial.Serial] = None
        self._read_thread: Optional[threading.Thread] = None
        self._read_thread_running: bool = False

        self._listeners: List[LineListener] = []
        self._listeners_lock = threading.Lock()
        self._write_lock = threading.Lock()

        # 可选的日志回调，由上层 UI 提供
        self._logger = logger

    # 公共 API -------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self._ser is not None and self._ser.is_open

    def set_logger(self, logger: Optional[Callable[[str], None]]) -> None:
        self._logger = logger

    def open(
        self,
        port: str,
        baudrate: int,
        timeout: float = 0.1,
        write_timeout: float = 1.0,
    ) -> None:
        """打开串口并启动读取线程。"""
        if self.is_open:
            # 如果已经打开，先关闭旧连接
            self.close()
            time.sleep(0.1)

        try:
            self._ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=write_timeout,
                rtscts=False,
                dsrdtr=False,
            )

            # 清空缓冲区
            time.sleep(0.5)
            self._ser.reset_input_buffer()
            self._ser.reset_output_buffer()

            # 启动读取线程
            self._start_read_thread()
            self._log(f"SerialManager: Connected to {port} at {baudrate} baud")
        except Exception as e:  # serial.SerialException 或其他
            self._ser = None
            self._log(f"SerialManager: Error connecting to {port}: {e}")
            raise

    def close(self) -> None:
        """关闭串口并停止读取线程。"""
        self._read_thread_running = False
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1.0)
        self._read_thread = None

        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None

    def reset_input_buffer(self) -> None:
        if self.is_open:
            try:
                self._ser.reset_input_buffer()
            except Exception:
                pass

    def send_line(self, line: str) -> None:
        """发送一行文本（自动追加换行）。"""
        if not self.is_open:
            raise RuntimeError("SerialManager: Port is not open")

        data = (line + "\n").encode("utf-8")
        with self._write_lock:
            self._ser.write(data)
            self._ser.flush()

    def add_listener(self, listener: LineListener) -> LineListener:
        """注册一个行监听回调，返回同一个对象用于之后移除。"""
        if not callable(listener):
            raise ValueError("listener must be callable")
        with self._listeners_lock:
            self._listeners.append(listener)
        return listener

    def remove_listener(self, listener: LineListener) -> None:
        with self._listeners_lock:
            try:
                self._listeners.remove(listener)
            except ValueError:
                pass

    def request_response(
        self,
        command: str,
        timeout: float,
        match_func: Callable[[str, List[str]], Optional[object]],
    ) -> Tuple[Optional[object], List[str]]:
        """
        发送一条指令并等待响应。

        - command: 不带换行的指令字符串
        - timeout: 超时时间（秒）
        - match_func: 每收到一行就调用一次，入参为 (line, all_lines)，
                      返回 None 表示继续等待，返回非 None 表示匹配成功并返回结果

        返回 (result, all_lines)，其中 result 可能为 None（超时未匹配）。
        """
        if not self.is_open:
            raise RuntimeError("SerialManager: Port is not open")

        all_lines: List[str] = []
        line_queue: "queue.Queue[str]" = queue.Queue()

        def _listener(line: str) -> None:
            line_queue.put(line)

        # 清空输入缓冲区，避免旧数据干扰
        self.reset_input_buffer()

        self.add_listener(_listener)
        try:
            # 发送指令
            self.send_line(command)

            deadline = time.time() + timeout
            result: Optional[object] = None

            while time.time() < deadline:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                try:
                    line = line_queue.get(timeout=remaining)
                except queue.Empty:
                    continue

                all_lines.append(line)
                try:
                    result = match_func(line, all_lines)
                except Exception as e:
                    self._log(f"SerialManager: match_func error: {e}")
                    # 不中断等待，继续尝试后续行
                    continue

                if result is not None:
                    break

            return result, all_lines
        finally:
            self.remove_listener(_listener)

    # 内部实现 -------------------------------------------------------------

    def _start_read_thread(self) -> None:
        if self._read_thread_running:
            return

        self._read_thread_running = True
        self._read_thread = threading.Thread(
            target=self._read_loop, name="SerialManagerReadThread", daemon=True
        )
        self._read_thread.start()

    def _read_loop(self) -> None:
        buffer = ""
        while self._read_thread_running and self._ser and self._ser.is_open:
            try:
                if self._ser.in_waiting > 0:
                    chunk = self._ser.read(self._ser.in_waiting)
                    if not chunk:
                        time.sleep(0.001)
                        continue

                    text = chunk.decode("utf-8", errors="ignore")
                    buffer += text
                    lines = buffer.split("\n")
                    buffer = lines[-1]

                    for raw_line in lines[:-1]:
                        line = raw_line.strip()
                        if not line:
                            continue
                        self._dispatch_line(line)
                else:
                    time.sleep(0.001)
            except serial.SerialException as e:
                self._log(f"SerialManager: serial error: {e}")
                break
            except Exception as e:
                # 记录错误但不中断线程
                self._log(f"SerialManager: unexpected error in read loop: {e}")
                time.sleep(0.05)

        self._read_thread_running = False

    def _dispatch_line(self, line: str) -> None:
        with self._listeners_lock:
            listeners_snapshot = list(self._listeners)
        for listener in listeners_snapshot:
            try:
                listener(line)
            except Exception as e:
                self._log(f"SerialManager: listener error: {e}")

    def _log(self, message: str) -> None:
        if self._logger:
            try:
                self._logger(message)
            except Exception:
                pass

