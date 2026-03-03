"""
Network Manager Module

Manages WiFi, MQTT, and OTA configuration.
"""

import json
import threading
import time
from datetime import datetime
from tkinter import filedialog
from typing import Callable, Optional

from .config import Config


class NetworkManager:
    """
    管理WiFi、MQTT和OTA配置
    
    负责:
    - WiFi配置设置/读取
    - MQTT配置设置/读取
    - OTA配置设置/读取
    - 网络配置保存/加载到文件
    - 从传感器属性提取网络配置
    """
    
    def __init__(self, serial_manager, callbacks: dict):
        """
        初始化 NetworkManager
        
        Args:
            serial_manager: SerialManager 实例
            callbacks: 回调函数字典，包含:
                - 'log_message': 日志记录函数 (message: str) -> None
                - 'get_wifi_params': 获取WiFi参数 () -> dict
                - 'set_wifi_params': 设置WiFi参数 (params: dict) -> None
                - 'get_mqtt_params': 获取MQTT参数 () -> dict
                - 'set_mqtt_params': 设置MQTT参数 (params: dict) -> None
                - 'get_ota_params': 获取OTA参数 () -> dict
                - 'set_ota_params': 设置OTA参数 (params: dict) -> None
                - 'enable_config_buttons': 启用配置按钮 () -> None
        """
        self.serial_manager = serial_manager
        self.callbacks = callbacks
        
        # 配置存储
        self._wifi_params: dict = {"ssid": "", "password": ""}
        self._mqtt_params: dict = {
            "broker": "",
            "username": "",
            "password": "",
            "port": "1883",
        }
        self._ota_params: dict = {
            "URL1": "",
            "URL2": "",
            "URL3": "",
            "URL4": "1883",
        }
    
    # ==================== 属性 ====================
    
    @property
    def wifi_params(self) -> dict:
        """获取WiFi参数"""
        return self._wifi_params.copy()
    
    @wifi_params.setter
    def wifi_params(self, value: dict):
        """设置WiFi参数"""
        self._wifi_params = value.copy()
    
    @property
    def mqtt_params(self) -> dict:
        """获取MQTT参数"""
        return self._mqtt_params.copy()
    
    @mqtt_params.setter
    def mqtt_params(self, value: dict):
        """设置MQTT参数"""
        self._mqtt_params = value.copy()
    
    @property
    def ota_params(self) -> dict:
        """获取OTA参数"""
        return self._ota_params.copy()
    
    @ota_params.setter
    def ota_params(self, value: dict):
        """设置OTA参数"""
        self._ota_params = value.copy()
    
    # ==================== WiFi 配置 ====================
    
    def set_wifi_config(self, ssid: str, password: str) -> bool:
        """
        设置WiFi配置
        
        Args:
            ssid: WiFi SSID
            password: WiFi密码
            
        Returns:
            bool: 是否成功启动配置流程
        """
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        if not ssid:
            self._log_message("Error: WiFi SSID cannot be empty!")
            return False
        
        # 更新本地参数
        self._wifi_params = {"ssid": ssid, "password": password}
        
        # 构建WiFi设置命令
        wifi_cmd = f"SET:WF,{ssid},{password}"
        self._log_message(f"Setting WiFi configuration: SSID={ssid}")
        
        # 在新线程中发送命令
        threading.Thread(
            target=self._send_config_command_thread,
            args=(wifi_cmd, "WiFi"),
            daemon=True
        ).start()
        
        return True
    
    def read_wifi_config(self) -> None:
        """读取WiFi配置（触发读取传感器属性）"""
        self._log_message("Reading WiFi configuration from device...")
        # 实际读取通过读取传感器属性完成
        if 'read_sensor_properties' in self.callbacks:
            self.callbacks['read_sensor_properties']()
    
    # ==================== MQTT 配置 ====================
    
    def set_mqtt_config(self, broker: str, username: str, password: str, port: str) -> bool:
        """
        设置MQTT配置
        
        Args:
            broker: MQTT服务器地址
            username: 用户名
            password: 密码
            port: 端口号
            
        Returns:
            bool: 是否成功启动配置流程
        """
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        if not broker:
            self._log_message("Error: MQTT broker address cannot be empty!")
            return False
        
        if not port:
            port = "1883"
        
        # 更新本地参数
        self._mqtt_params = {
            "broker": broker,
            "username": username,
            "password": password,
            "port": port,
        }
        
        # 构建MQTT设置命令
        mqtt_cmd = f"SET:MQ,{broker},{port},{username},{password}"
        self._log_message(f"Setting MQTT configuration: Broker={broker}, Port={port}")
        
        # 在新线程中发送命令
        threading.Thread(
            target=self._send_config_command_thread,
            args=(mqtt_cmd, "MQTT"),
            daemon=True
        ).start()
        
        return True
    
    def read_mqtt_config(self) -> None:
        """读取MQTT配置（触发读取传感器属性）"""
        self._log_message("Reading MQTT configuration from device...")
        if 'read_sensor_properties' in self.callbacks:
            self.callbacks['read_sensor_properties']()
    
    # ==================== OTA 配置 ====================
    
    def set_ota_config(self, url1: str, url2: str, url3: str, url4: str) -> bool:
        """
        设置OTA配置
        
        Args:
            url1: URL1
            url2: URL2
            url3: URL3
            url4: URL4
            
        Returns:
            bool: 是否成功启动配置流程
        """
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        # 更新本地参数
        self._ota_params = {
            "URL1": url1,
            "URL2": url2,
            "URL3": url3,
            "URL4": url4,
        }
        
        # 构建OTA设置命令
        ota_cmd = f"SET:OTA,{url1},{url2},{url3},{url4}"
        self._log_message(f"Setting OTA configuration: OTA={url1},{url2},{url3},{url4}")
        
        # 在新线程中发送命令
        threading.Thread(
            target=self._send_config_command_thread,
            args=(ota_cmd, "OTA"),
            daemon=True
        ).start()
        
        return True
    
    def read_ota_config(self) -> None:
        """读取OTA配置（触发读取传感器属性）"""
        self._log_message("Reading OTA configuration from device...")
        if 'read_sensor_properties' in self.callbacks:
            self.callbacks['read_sensor_properties']()
    
    # ==================== 报警阈值配置 ====================
    
    def set_alarm_threshold(self, accel_threshold: float, gyro_threshold: float) -> bool:
        """
        设置报警阈值
        
        发送 SET:AGT 命令设置传感器的加速度报警阈值和倾角报警阈值。
        
        Args:
            accel_threshold: 加速度报警阈值 (m/s²)，范围 0.1-10.0
            gyro_threshold: 倾角报警阈值 (°)，范围 0.1-45.0
            
        Returns:
            bool: 是否成功启动配置流程
            
        Raises:
            ValueError: 如果阈值超出有效范围
        """
        # 验证连接
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        # 验证阈值范围
        if not (0.1 <= accel_threshold <= 10.0):
            self._log_message(f"Error: Accel threshold {accel_threshold} out of range (0.1-10.0 m/s²)")
            return False
        
        if not (0.1 <= gyro_threshold <= 45.0):
            self._log_message(f"Error: Gyro threshold {gyro_threshold} out of range (0.1-45.0°)")
            return False
        
        # 构建报警阈值设置命令
        # 格式: SET:AGT,<accel_threshold>,<gyro_threshold>
        agt_cmd = f"SET:AGT,{accel_threshold},{gyro_threshold}"
        self._log_message(f"Setting alarm threshold: Accel={accel_threshold} m/s², Gyro={gyro_threshold}°")
        
        # 在新线程中发送命令
        threading.Thread(
            target=self._send_config_command_thread,
            args=(agt_cmd, "Alarm Threshold"),
            daemon=True
        ).start()
        
        return True
    
    def extract_alarm_threshold(self, sensor_properties: dict) -> dict:
        """
        从传感器属性中提取报警阈值
        
        Args:
            sensor_properties: 传感器属性字典
            
        Returns:
            dict: 包含 accel_threshold 和 gyro_threshold 的字典，
                  如果未找到则返回空字典
        """
        if not sensor_properties:
            return {}
        
        threshold_info = {}
        
        # 在 sys 字段中查找报警阈值
        # 注意：实际的字段名需要根据传感器实际返回的属性确定
        if "sys" in sensor_properties:
            sys_info = sensor_properties["sys"]
            
            # 加速度报警阈值 (AT)
            accel_threshold = sys_info.get("AT")
            if accel_threshold is not None:
                try:
                    threshold_info["accel_threshold"] = float(accel_threshold)
                except (ValueError, TypeError):
                    pass
            
            # 倾角报警阈值 (GT)
            gyro_threshold = sys_info.get("GT")
            if gyro_threshold is not None:
                try:
                    threshold_info["gyro_threshold"] = float(gyro_threshold)
                except (ValueError, TypeError):
                    pass
        
        return threshold_info
    
    # ==================== 配置命令发送 ====================
    
    def _send_config_command_thread(self, command: str, config_type: str) -> None:
        """
        在线程中发送配置命令
        
        Args:
            command: 命令字符串
            config_type: 配置类型 (WiFi/MQTT/OTA)
        """
        try:
            # 停止数据流（如果正在运行）
            if 'stop_data_stream' in self.callbacks:
                self.callbacks['stop_data_stream']()
                time.sleep(1.0)
            
            # 清空输入缓冲区
            if self.serial_manager.serial_port:
                self.serial_manager.serial_port.reset_input_buffer()
                time.sleep(Config.BUFFER_CLEAR_DELAY)
            
            # 发送配置命令
            self.serial_manager.serial_port.write(command.encode())
            self.serial_manager.serial_port.flush()
            
            self._log_message(f"Sent: {command}")
            
            # 等待响应
            time.sleep(2.0)
            
            # 读取响应
            response_bytes = b""
            start_time = time.time()
            timeout = 5.0
            
            while time.time() - start_time < timeout:
                if self.serial_manager.serial_port.in_waiting > 0:
                    response_bytes += self.serial_manager.serial_port.read(
                        self.serial_manager.serial_port.in_waiting
                    )
                
                response_str = response_bytes.decode("utf-8", errors="ignore")
                
                if "success" in response_str.lower() or "ok" in response_str.lower():
                    self._log_message(f"{config_type} configuration successful!")
                    break
                
                time.sleep(Config.THREAD_ERROR_DELAY)
            
            if not response_bytes:
                self._log_message(f"{config_type} configuration sent (no response)")
            else:
                # 显示响应内容
                response_text = response_str.strip()
                if response_text:
                    self._log_message(f"Response: {response_text}")
            
            # 恢复数据流
            if 'start_data_stream' in self.callbacks:
                time.sleep(1.0)
                self.callbacks['start_data_stream']()
                
        except Exception as e:
            self._log_message(f"Error setting {config_type} configuration: {str(e)}")
    
    # ==================== 从属性提取配置 ====================
    
    def extract_network_config(self, sensor_properties: dict) -> dict:
        """
        从传感器属性中提取网络配置
        
        Args:
            sensor_properties: 传感器属性字典
            
        Returns:
            dict: 提取的配置
        """
        if not sensor_properties:
            return {}
        
        config = {}
        
        if "sys" in sensor_properties:
            sys_info = sensor_properties["sys"]
            
            # WiFi配置
            ssid = sys_info.get("SSID", "")
            password = sys_info.get("PA", "")
            
            if ssid:
                self._wifi_params["ssid"] = ssid
                config['wifi'] = {'ssid': ssid, 'password': password}
            
            # MQTT配置
            broker = sys_info.get("MBR", "")
            port = sys_info.get("MPT", "1883")
            username = sys_info.get("MUS", "")
            password = sys_info.get("MPW", "")
            
            if broker:
                self._mqtt_params = {
                    "broker": broker,
                    "username": username,
                    "password": password,
                    "port": str(port),
                }
                config['mqtt'] = self._mqtt_params.copy()
            
            # OTA配置
            url1 = sys_info.get("URL1", "")
            url2 = sys_info.get("URL2", "")
            url3 = sys_info.get("URL3", "")
            url4 = sys_info.get("URL4", "")
            
            if url1 or url2 or url3 or url4:
                self._ota_params = {
                    "URL1": url1,
                    "URL2": url2,
                    "URL3": url3,
                    "URL4": url4,
                }
                config['ota'] = self._ota_params.copy()
            
            # 启用设置按钮
            if 'enable_config_buttons' in self.callbacks:
                self.callbacks['enable_config_buttons']()
        
        return config
    
    def display_network_summary(self, sensor_properties: dict) -> None:
        """
        显示网络配置摘要
        
        Args:
            sensor_properties: 传感器属性字典
        """
        if not sensor_properties:
            return
        
        self._log_message("\n" + "=" * 50)
        self._log_message("NETWORK CONFIGURATION SUMMARY")
        self._log_message("=" * 50)
        
        if "sys" in sensor_properties:
            sys_info = sensor_properties["sys"]
            
            # WiFi信息
            ssid = sys_info.get("SSID", "Not set")
            self._log_message(f"WiFi SSID: {ssid}")
            self._log_message(
                f"WiFi Password: {'*' * 8 if sys_info.get('PA') else 'Not set'}"
            )
            
            # MQTT信息
            broker = sys_info.get("MBR", "Not set")
            username = sys_info.get("MUS", "Not set")
            port = sys_info.get("MPT", "Not set")
            
            self._log_message(f"MQTT Broker: {broker}")
            self._log_message(f"MQTT Username: {username}")
            self._log_message(f"MQTT Port: {port}")
            self._log_message(
                f"MQTT Password: {'*' * 8 if sys_info.get('MPW') else 'Not set'}"
            )
        
        self._log_message("=" * 50)
    
    # ==================== 文件操作 ====================
    
    def save_network_config(self) -> bool:
        """
        保存网络配置到文件
        
        Returns:
            bool: 是否成功保存
        """
        try:
            config_data = {
                "timestamp": datetime.now().isoformat(),
                "wifi_config": self._wifi_params,
                "mqtt_config": self._mqtt_params,
            }
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"network_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )
            
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                self._log_message(f"Network configuration saved to: {filename}")
                return True
                
        except Exception as e:
            self._log_message(f"Error saving network configuration: {str(e)}")
        
        return False
    
    def load_network_config(self) -> bool:
        """
        从文件加载网络配置
        
        Returns:
            bool: 是否成功加载
        """
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                
                # 加载WiFi配置
                if "wifi_config" in config_data:
                    self._wifi_params = config_data["wifi_config"]
                    if 'on_wifi_loaded' in self.callbacks:
                        self.callbacks['on_wifi_loaded'](self._wifi_params)
                
                # 加载MQTT配置
                if "mqtt_config" in config_data:
                    self._mqtt_params = config_data["mqtt_config"]
                    if 'on_mqtt_loaded' in self.callbacks:
                        self.callbacks['on_mqtt_loaded'](self._mqtt_params)
                
                self._log_message(f"Network configuration loaded from: {filename}")
                
                # 启用设置按钮
                if 'enable_config_buttons' in self.callbacks:
                    self.callbacks['enable_config_buttons']()
                
                return True
                
        except Exception as e:
            self._log_message(f"Error loading network configuration: {str(e)}")
        
        return False
    
    # ==================== 辅助方法 ====================
    
    def _log_message(self, message: str) -> None:
        """记录日志（通过回调）"""
        if 'log_message' in self.callbacks:
            self.callbacks['log_message'](message)
    
    def get_config_summary(self) -> str:
        """获取配置摘要字符串"""
        lines = []
        lines.append("=" * 50)
        lines.append("NETWORK CONFIGURATION SUMMARY")
        lines.append("=" * 50)
        lines.append(f"WiFi SSID: {self._wifi_params.get('ssid', 'Not set')}")
        lines.append(f"MQTT Broker: {self._mqtt_params.get('broker', 'Not set')}")
        lines.append(f"MQTT Port: {self._mqtt_params.get('port', '1883')}")
        lines.append("=" * 50)
        return "\n".join(lines)
