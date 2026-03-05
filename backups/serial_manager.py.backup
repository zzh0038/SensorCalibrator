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
        
        # 读取线程
        self._serial_thread: Optional[threading.Thread] = None
        
        # 统计数据
        self._packets_received = 0
        self._consecutive_errors = 0
        self._max_consecutive_errors = 5
    
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
            self._log_message(f"Connected to {port} at {baudrate} baud")
            
            # 通知连接状态变化
            if 'update_connection_state' in self.callbacks:
                self.callbacks['update_connection_state'](True)
            
            return True
            
        except Exception as e:
            self._log_message(f"Error connecting to {port}: {str(e)}")
            self._ser = None
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """断开串口连接"""
        # 先停止数据流
        if self._is_reading:
            self.stop_reading()
        
        # 关闭串口
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception as e:
                self._log_message(f"Error closing serial port: {str(e)}")
        
        self._ser = None
        self._is_connected = False
        self._log_message("Disconnected from serial port")
        
        # 通知连接状态变化
        if 'update_connection_state' in self.callbacks:
            self.callbacks['update_connection_state'](False)
    
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
            self._log_message(f"Error starting data reading: {str(e)}")
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
        串口数据读取线程
        在后台线程中运行，将解析后的数据放入队列
        """
        buffer = ""
        data_queue = self.callbacks.get('get_data_queue', lambda: None)()
        
        while self._is_reading and self.is_connected:
            try:
                if self._ser.in_waiting > 0:
                    # 读取可用数据
                    data = self._ser.read(self._ser.in_waiting).decode(
                        "ascii", errors="ignore"
                    )
                    buffer += data
                    
                    # 处理完整行
                    lines = buffer.split("\n")
                    buffer = lines[-1]  # 保留不完整的行
                    
                    for line in lines[:-1]:
                        line = line.strip()
                        if line and not line.startswith("SS:"):  # 过滤命令回显
                            # 放入队列
                            if data_queue and not data_queue.full():
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
                            
                            # 调用数据接收回调
                            if 'on_data_received' in self.callbacks:
                                self.callbacks['on_data_received'](line)
                
                # 自适应睡眠策略
                if self._ser.in_waiting > 0:
                    time.sleep(SerialConfig.READ_SLEEP_DATA)
                else:
                    time.sleep(SerialConfig.READ_SLEEP_IDLE)
                
                # 检查连接状态
                if not self.is_connected:
                    break
                    
            except serial.SerialException as e:
                self._consecutive_errors += 1
                if self._consecutive_errors >= self._max_consecutive_errors:
                    self._log_message(f"Multiple serial errors, stopping: {str(e)}")
                    break
                time.sleep(Config.THREAD_ERROR_DELAY)
                
            except Exception as e:
                self._consecutive_errors += 1
                if self._consecutive_errors >= self._max_consecutive_errors:
                    self._log_message(f"Unexpected error in serial reading: {str(e)}")
                    break
                time.sleep(Config.PARSE_RETRY_DELAY)
        
        # 如果因为错误退出，确保状态正确
        if self._is_reading:
            self._log_message("Serial reading thread exited unexpectedly")
            self._is_reading = False
    
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
                self._log_message(f"Serial error sending SS:{cmd_id}: {str(e)}")
            return False
            
        except Exception as e:
            if not silent:
                self._log_message(f"Unexpected error sending SS:{cmd_id}: {str(e)}")
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
            time.sleep(Config.CONFIG_COMMAND_DELAY)
            return True
            
        except Exception as e:
            self._log_message(f"Error sending {config_type} configuration: {str(e)}")
            return False
    
    # ==================== 辅助方法 ====================
    
    def _log_message(self, message: str) -> None:
        """记录日志（通过回调）"""
        if 'log_message' in self.callbacks:
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
        except Exception:
            pass
        return ports
