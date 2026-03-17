"""
Serial Manager Module

Manages serial port connection, communication, and data streaming.
"""

import serial
import serial.tools.list_ports
import threading
import queue
import time
from typing import Callable, Optional

from .config import Config, SerialConfig
from .ring_buffer import RingBuffer, QueueAdapter


class SerialManager:
    """
    管理串口连接和通信
    
    负责:
    - 串口连接/断开
    - 数据流控制 (SS0/SS1/SS4)
    - SS 命令发送
    - 串口数据读取线程
    """
    
    def __init__(self, callbacks: dict):
        """
        初始化 SerialManager
        
        Args:
            callbacks: 回调函数字典，包含:
                - 'log_message': 日志记录函数 (message: str) -> None
                - 'on_data_received': 数据接收回调 (data: str) -> None
                - 'update_connection_state': 连接状态更新 (connected: bool) -> None
                - 'get_data_queue': 获取数据队列 () -> queue.Queue
        """
        self.callbacks = callbacks
        
        # 串口对象
        self._ser: Optional[serial.Serial] = None
        
        # 状态标志
        self._is_connected = False
        self._is_reading = False
        self._user_disconnect = False  # 标记是否为用户主动断开
        
        # 线程
        self._serial_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None  # 连接监控线程
        
        # 统计数据
        self._packets_received = 0
        self._consecutive_errors = 0
        self._max_consecutive_errors = 5
        
        # 写入锁（保证多线程写入串口的线程安全）
        self._write_lock = threading.Lock()
    
    # ==================== 属性 ====================
    
    @property
    def is_connected(self) -> bool:
        """检查串口是否连接"""
        return self._ser is not None and self._ser.is_open
    
    @property
    def is_reading(self) -> bool:
        """检查是否正在读取数据"""
        return self._is_reading
    
    @property
    def serial_port(self) -> Optional[serial.Serial]:
        """获取串口对象（谨慎使用）"""
        return self._ser
    
    @property
    def packets_received(self) -> int:
        """获取接收到的数据包数量"""
        return self._packets_received
    
    # ==================== 连接管理 ====================
    
    def connect(self, port: str, baudrate: int) -> bool:
        """
        连接串口
        
        Args:
            port: 串口名称 (如 "COM3")
            baudrate: 波特率
            
        Returns:
            bool: 连接是否成功
        """
        if not port:
            self._log_message("Error: No port selected!")
            return False
        
        try:
            # 确保之前的状态被清理
            if self.is_connected:
                self.disconnect()
                time.sleep(SerialConfig.DISCONNECT_DELAY)
            
            self._ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=SerialConfig.TIMEOUT,
                write_timeout=SerialConfig.WRITE_TIMEOUT,
                rtscts=SerialConfig.RTSCTS,
                dsrdtr=SerialConfig.DSRDTR,
            )
            
            # 清空缓冲区
            time.sleep(SerialConfig.CONNECT_DELAY)
            self._ser.reset_input_buffer()
            self._ser.reset_output_buffer()
            
            self._is_connected = True
            self._user_disconnect = False  # 重置用户断开标志
            self._log_message(f"Connected to {port} at {baudrate} baud")
            
            # 启动连接监控线程
            self._start_connection_monitor()
            
            # 通知连接状态变化
            if self.callbacks.get('update_connection_state') is not None:
                self.callbacks['update_connection_state'](True)
            
            return True
            
        except Exception as e:
            self._log_message(f"Error connecting to {port}: {str(e)}", "ERROR")
            self._ser = None
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """断开串口连接"""
        # 标记为用户主动断开
        self._user_disconnect = True
        
        # 先停止监控线程
        self._stop_connection_monitor()
        
        # 停止数据流
        if self._is_reading:
            self.stop_reading()
        
        # 关闭串口
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception as e:
                self._log_message(f"Error closing serial port: {str(e)}", "ERROR")
        
        self._ser = None
        self._is_connected = False
        self._log_message("Disconnected from serial port")
        
        # 通知连接状态变化（用户主动断开）
        if self.callbacks.get('update_connection_state') is not None:
            self.callbacks['update_connection_state'](False, user_initiated=True)
    
    def toggle_connection(self, port: str, baudrate: int) -> bool:
        """
        切换串口连接状态
        
        Args:
            port: 串口名称
            baudrate: 波特率
            
        Returns:
            bool: 连接是否已建立
        """
        if self.is_connected:
            self.disconnect()
            return False
        else:
            return self.connect(port, baudrate)
    
    # ==================== 数据流控制 ====================
    
    def start_reading(self) -> bool:
        """
        开始串口数据读取线程
        
        Returns:
            bool: 是否成功启动
        """
        if not self.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        if self._is_reading:
            return True  # 已经在读取
        
        try:
            self._is_reading = True
            self._packets_received = 0
            self._consecutive_errors = 0
            
            # 启动读取线程
            self._serial_thread = threading.Thread(
                target=self._read_serial_data, daemon=True
            )
            self._serial_thread.start()
            
            self._log_message("Serial data reading started")
            return True
            
        except Exception as e:
            self._log_message(f"Error starting data reading: {str(e)}", "ERROR")
            self._is_reading = False
            return False
    
    def stop_reading(self) -> None:
        """停止串口数据读取"""
        if not self._is_reading:
            return
        
        self._is_reading = False
        
        # 等待线程结束
        if self._serial_thread and self._serial_thread.is_alive():
            self._serial_thread.join(timeout=1.0)
        
        self._log_message("Serial data reading stopped")
    
    def toggle_reading(self) -> bool:
        """
        切换数据读取状态
        
        Returns:
            bool: 读取是否正在运行
        """
        if not self.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        if self._is_reading:
            self.stop_reading()
            return False
        else:
            return self.start_reading()
    
    def _read_serial_data(self) -> None:
        """
        串口数据读取线程 - 优化版本（使用RingBuffer）
        
        优化点：
        - 使用RingBuffer替代Queue，满时单操作覆盖
        - 减少锁竞争
        - 批量处理行数据
        - 主动连接健康检查（检测USB断开等异常情况）
        """
        import time
        buffer = ""
        data_queue = self.callbacks.get('get_data_queue', lambda: None)()
        
        # 使用RingBuffer或QueueAdapter更高效（它们支持put_batch）
        use_ring_buffer = isinstance(data_queue, (RingBuffer, QueueAdapter))
        
        # 记录时间戳用于健康检查
        last_data_time = time.time()
        last_health_check = time.time()
        
        while self._is_reading and self.is_connected:
            try:
                if self._ser.in_waiting > 0:
                    # 读取可用数据
                    bytes_to_read = self._ser.in_waiting
                    data = self._ser.read(bytes_to_read).decode(
                        "ascii", errors="ignore"
                    )
                    buffer += data

                    
                    # 处理完整行
                    lines = buffer.split("\n")
                    buffer = lines[-1]  # 保留不完整的行
                    
                    # 批量处理有效行
                    valid_lines = []
                    for line in lines[:-1]:
                        line = line.strip()
                        if line and not line.startswith("SS:"):  # 过滤命令回显
                            valid_lines.append(line)
                            
                            # 调用数据接收回调（每行都调用）
                            if self.callbacks.get('on_data_received') is not None:
                                self.callbacks['on_data_received'](line)
                    
                    # 批量放入队列
                    if data_queue and valid_lines:
                        # 更新上次收到数据的时间
                        last_data_time = time.time()
                        if use_ring_buffer:
                            # RingBuffer：批量放入更高效
                            data_queue.put_batch(valid_lines)
                            self._packets_received += len(valid_lines)
                            self._consecutive_errors = 0
                        else:
                            # 标准Queue：逐行放入，保持兼容性
                            for line in valid_lines:
                                if not data_queue.full():
                                    try:
                                        data_queue.put_nowait(line)
                                        self._packets_received += 1
                                        self._consecutive_errors = 0
                                    except queue.Full:
                                        # 队列满时丢弃最旧的数据
                                        try:
                                            data_queue.get_nowait()
                                            data_queue.put_nowait(line)
                                        except queue.Empty:
                                            pass
                                else:
                                    # 满了也要尝试放入（丢弃最旧的）
                                    try:
                                        data_queue.get_nowait()
                                        data_queue.put_nowait(line)
                                        self._packets_received += 1
                                    except queue.Empty:
                                        pass
                
                # 自适应睡眠策略
                if self._ser.in_waiting > 0:
                    time.sleep(SerialConfig.READ_SLEEP_DATA)
                else:
                    time.sleep(SerialConfig.READ_SLEEP_IDLE)
                
                # 检查连接状态
                if not self.is_connected:
                    break
                
                # 主动连接健康检查（用于检测USB断开等异常情况）
                current_time = time.time()
                time_since_last_data = current_time - last_data_time
                
                # 如果超过健康检查间隔没有收到数据，执行健康检查
                if time_since_last_data > SerialConfig.HEALTH_CHECK_INTERVAL:
                    if current_time - last_health_check > SerialConfig.HEALTH_CHECK_INTERVAL:
                        last_health_check = current_time
                        if not self._check_connection_health():
                            self._log_message("Connection health check failed, device may be disconnected", "ERROR")
                            break
                
                # 如果超过无数据超时时间，认为连接已断开
                if time_since_last_data > SerialConfig.NO_DATA_TIMEOUT:
                    self._log_message(f"No data received for {SerialConfig.NO_DATA_TIMEOUT}s, assuming disconnected", "ERROR")
                    break
                    
            except serial.SerialException as e:
                self._consecutive_errors += 1
                if self._consecutive_errors >= self._max_consecutive_errors:
                    self._log_message(f"Multiple serial errors, stopping: {str(e)}", "ERROR")
                    break
                time.sleep(Config.THREAD_ERROR_DELAY)
                
            except Exception as e:
                self._consecutive_errors += 1
                if self._consecutive_errors >= self._max_consecutive_errors:
                    self._log_message(f"Unexpected error in serial reading: {str(e)}", "ERROR")
                    break
                time.sleep(Config.PARSE_RETRY_DELAY)
        
        # 检查是否因为错误/异常退出（不是用户正常停止）
        # 当用户正常 stop_reading() 时，_is_reading 会在 join 前被设为 False
        # 如果到这里 _is_reading 仍为 True，说明是异常退出
        if self._is_reading:
            self._log_message("Serial reading thread exited unexpectedly", "WARNING")
            self._is_reading = False
            
            # 如果是异常退出且不是用户主动断开，通知 UI 层
            if not self._user_disconnect and (self._ser is not None or self._is_connected):
                self._log_message("Serial connection lost unexpectedly", "ERROR")
                self._is_connected = False
                self._ser = None
                if self.callbacks.get('update_connection_state') is not None:
                    self.callbacks['update_connection_state'](False, user_initiated=False)
    
    def _check_connection_health(self) -> bool:
        """
        检查串口连接健康状态
        
        通过尝试访问串口属性来检测连接是否实际可用。
        当 USB 设备被拔出时，这个检查会失败。
        
        Returns:
            bool: 连接健康返回 True，否则返回 False
        """
        if self._ser is None:
            return False
        
        try:
            # 尝试读取输入缓冲区的字节数
            # 如果设备已断开，这会抛出 SerialException 或 OSError
            _ = self._ser.in_waiting
            return True
        except (serial.SerialException, OSError) as e:
            self._log_message(f"Connection health check failed: {e}", "DEBUG")
            return False
        except Exception as e:
            self._log_message(f"Unexpected error in health check: {e}", "DEBUG")
            return False
    
    # ==================== 连接监控线程 ====================
    
    def _start_connection_monitor(self) -> None:
        """
        启动连接监控线程
        
        该线程独立运行，用于检测 USB 设备意外断开。
        无论是否开启数据流，只要连接了就启动监控。
        """
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return  # 已经在运行
        
        self._monitor_running = True
        self._monitor_thread = threading.Thread(
            target=self._connection_monitor_loop,
            daemon=True,
            name="ConnectionMonitor"
        )
        self._monitor_thread.start()
        self._log_message("Connection monitor started")
    
    def _stop_connection_monitor(self) -> None:
        """停止连接监控线程"""
        self._monitor_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        self._monitor_thread = None
    
    def _connection_monitor_loop(self) -> None:
        """
        连接监控循环
        
        定期检查串口连接状态，检测到断开时触发回调。
        这个线程只要连接了就运行，与数据流无关。
        """
        while self._monitor_running and self.is_connected:
            try:
                # 执行健康检查
                if not self._check_connection_health():
                    self._log_message("Connection monitor detected disconnection", "ERROR")
                    # 触发断开处理
                    if not self._user_disconnect:
                        self._handle_unexpected_disconnect()
                    break
                
                # 休眠一段时间再检查
                time.sleep(SerialConfig.HEALTH_CHECK_INTERVAL)
                
            except Exception as e:
                self._log_message(f"Error in connection monitor: {e}", "DEBUG")
                time.sleep(1.0)
        
        self._log_message("Connection monitor stopped")
    
    def _handle_unexpected_disconnect(self) -> None:
        """处理意外断开连接"""
        self._log_message("Handling unexpected disconnection", "ERROR")
        
        # 停止读取线程（如果正在运行）
        if self._is_reading:
            self._is_reading = False
        
        # 清理状态
        self._is_connected = False
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        except:
            pass
        self._ser = None
        
        # 通知 UI 层
        if self.callbacks.get('update_connection_state') is not None:
            self.callbacks['update_connection_state'](False, user_initiated=False)
    
    # ==================== SS 命令 ====================
    
    def send_ss_command(self, cmd_id: int, description: str = "",
                       log_success: bool = True, silent: bool = False) -> bool:
        """
        发送 SS 指令的通用方法
        
        Args:
            cmd_id: 指令编号 (0-9)
            description: 指令描述（用于日志）
            log_success: 是否记录成功日志
            silent: 是否静默模式（不记录错误日志）
            
        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected:
            if not silent:
                self._log_message("Error: Not connected to serial port!")
            return False
        
        try:
            command = f"SS:{cmd_id}\n".encode()
            self._ser.write(command)
            self._ser.flush()
            
            if log_success and not silent:
                desc = f" ({description})" if description else ""
                self._log_message(f"Sent: SS:{cmd_id}{desc}")
            return True
            
        except serial.SerialException as e:
            if not silent:
                self._log_message(f"Serial error sending SS:{cmd_id}: {str(e)}", "ERROR")
            return False
            
        except Exception as e:
            if not silent:
                self._log_message(f"Unexpected error sending SS:{cmd_id}: {str(e)}", "ERROR")
            return False
    
    def send_ss0_start_stream(self, description: str = "Start Data Stream") -> bool:
        """发送 SS:0 指令 - 开始数据流"""
        return self.send_ss_command(0, description)
    
    def send_ss1_start_calibration(self, description: str = "Start Calibration Stream") -> bool:
        """发送 SS:1 指令 - 开始校准流"""
        return self.send_ss_command(1, description)
    
    def send_ss2_local_mode(self, description: str = "Local Coordinate Mode") -> bool:
        """发送 SS:2 指令 - 局部坐标模式"""
        return self.send_ss_command(2, description)
    
    def send_ss3_global_mode(self, description: str = "Global Coordinate Mode") -> bool:
        """发送 SS:3 指令 - 整体坐标模式"""
        return self.send_ss_command(3, description)
    
    def send_ss4_stop_stream(self, description: str = "Stop Stream") -> bool:
        """发送 SS:4 指令 - 停止数据流/校准"""
        return self.send_ss_command(4, description)
    
    def send_ss7_save_config(self, description: str = "Save Configuration to Sensor") -> bool:
        """发送 SS:7 指令 - 保存配置到传感器"""
        return self.send_ss_command(7, description)
    
    def send_ss8_get_properties(self, description: str = "Get Sensor Properties") -> bool:
        """发送 SS:8 指令 - 获取传感器属性"""
        return self.send_ss_command(8, description)
    
    def send_ss9_restart_sensor(self, description: str = "Restart Sensor") -> bool:
        """发送 SS:9 指令 - 重启传感器"""
        return self.send_ss_command(9, description)
    
    def send_line(self, command: str) -> tuple[bool, str]:
        """
        线程安全地发送命令行（自动添加换行符）
        
        此方法使用写锁保证多线程环境下串口写入的线程安全。
        
        Args:
            command: 命令字符串（不含换行符）
            
        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        if not self.is_connected:
            return False, "Not connected to serial port"
        
        with self._write_lock:
            try:
                self._ser.write(f"{command}\n".encode())
                self._ser.flush()
                return True, ""
            except serial.SerialException as e:
                return False, f"Serial error: {str(e)}"
            except Exception as e:
                return False, f"Unexpected error: {str(e)}"
    
    # ==================== 原始命令发送 ====================
    
    def send_command(self, command: bytes) -> tuple[bool, str]:
        """
        发送原始命令到串口
        
        Args:
            command: 要发送的字节数据
            
        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        if not self.is_connected:
            return False, "Not connected to serial port"
        
        try:
            self._ser.write(command)
            self._ser.flush()
            return True, ""
            
        except serial.SerialException as e:
            return False, f"Serial error: {str(e)}"
            
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def send_config_command(self, command: bytes, config_type: str = "") -> bool:
        """
        发送配置命令（带超时重试）
        
        Args:
            command: 命令字节
            config_type: 配置类型名称（用于日志）
            
        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected:
            self._log_message(f"Error: Not connected to serial port!")
            return False
        
        try:
            self._ser.write(command)
            self._ser.flush()
            
            if config_type:
                self._log_message(f"Sent {config_type} configuration command")
            
            # 等待设备处理
            time.sleep(Config.COMMAND_DELAY)
            return True
            
        except Exception as e:
            self._log_message(f"Error sending {config_type} configuration: {str(e)}")
            return False
    
    # ==================== 辅助方法 ====================
    
    def _log_message(self, message: str, level: str = "INFO") -> None:
        """
        记录日志（通过回调）
        
        Args:
            message: 日志消息
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR)，默认 INFO
        """
        if self.callbacks.get('log_message') is not None:
            # 检查回调是否支持 level 参数
            import inspect
            sig = inspect.signature(self.callbacks['log_message'])
            param_count = len([p for p in sig.parameters.values() if p.default is inspect.Parameter.empty or p.default != inspect.Parameter.empty])
            
            if level != "INFO" and param_count >= 2:
                # 非 INFO 级别且支持 level 参数
                self.callbacks['log_message'](message, level)
            else:
                # 保持向后兼容：INFO 级别或旧回调只传 message
                self.callbacks['log_message'](message)
    
    def reset_packet_count(self) -> None:
        """重置数据包计数"""
        self._packets_received = 0
    
    # ==================== 静态工具方法 ====================
    
    @staticmethod
    def list_available_ports() -> list[str]:
        """
        获取可用串口列表
        
        Returns:
            list[str]: 可用串口名称列表
        """
        ports = []
        try:
            for port in serial.tools.list_ports.comports():
                ports.append(port.device)
        except Exception as e:
            # 串口枚举失败时返回空列表（合理回退）
            # 静默处理，因为这是预期的回退行为
            # 如需诊断问题，可临时启用调试日志
            # import logging
            # logging.debug(f"Serial port enumeration failed: {e}")
            pass
            # 串口枚举失败时返回空列表（合理回退）
            pass
        return ports
