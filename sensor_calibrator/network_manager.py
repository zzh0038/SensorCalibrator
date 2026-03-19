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
            "URL4": "",
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
    
    # ==================== 验证辅助方法 ====================
    
    def _validate_port(self, port: str) -> tuple[bool, str]:
        """
        验证端口号有效性
        
        Args:
            port: 端口号字符串
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        if not port:
            return True, ""  # 空字符串将使用默认值
        try:
            port_num = int(port)
            if not (1 <= port_num <= 65535):
                return False, f"Port must be between 1 and 65535, got {port_num}"
            return True, ""
        except ValueError:
            return False, f"Port must be a number, got '{port}'"
    
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
        
        # 验证端口
        is_valid, error_msg = self._validate_port(port)
        if not is_valid:
            self._log_message(f"Error: {error_msg}")
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
            
            # 发送配置命令（使用线程安全的 send_line）
            success, error = self.serial_manager.send_line(command)
            if not success:
                self._log_message(f"Error sending {config_type} command: {error}")
                return
            
            self._log_message(f"Sent: {command}")
            
            # 等待响应
            time.sleep(2.0)
            
            # 读取响应
            response_bytes = b""
            response_str = ""
            start_time = time.time()
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
    
    # ==================== 阿里云 MQTT 配置 (Sprint 1 新增) ====================
    
    def set_aliyun_mqtt_config(
        self,
        product_key: str,
        device_name: str,
        device_secret: str
    ) -> bool:
        """
        设置阿里云 MQTT 配置 (SET:KNS)
        
        Args:
            product_key: 阿里云产品密钥 (ProductKey)
            device_name: 设备名称 (DeviceName)
            device_secret: 设备密钥 (DeviceSecret)
            
        Returns:
            bool: 是否成功启动配置流程
        """
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        # 导入命令构建函数
        from .network.cloud_mqtt import build_kns_command
        
        # 构建命令
        valid, error, kns_cmd = build_kns_command(product_key, device_name, device_secret)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        self._log_message(f"Setting Aliyun MQTT: Product={product_key}, Device={device_name}")
        
        # 在新线程中发送命令
        threading.Thread(
            target=self._send_config_command_thread,
            args=(kns_cmd, "Aliyun MQTT"),
            daemon=True
        ).start()
        
        return True
    
    def set_mqtt_mode(self, mode: int) -> bool:
        """
        设置 MQTT 工作模式 (SET:CMQ)
        
        Args:
            mode: MQTT模式 (1=局域网, 10=阿里云)
            
        Returns:
            bool: 是否成功启动配置流程
        """
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        # 导入命令构建函数
        from .network.cloud_mqtt import build_cmq_command, get_mqtt_mode_description
        
        # 构建命令
        valid, error, cmq_cmd = build_cmq_command(mode)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        mode_desc = get_mqtt_mode_description(mode)
        self._log_message(f"Setting MQTT mode: {mode_desc}")
        
        # 在新线程中发送命令
        threading.Thread(
            target=self._send_config_command_thread,
            args=(cmq_cmd, "MQTT Mode"),
            daemon=True
        ).start()
        
        return True
    
    def configure_full_aliyun_mqtt(
        self,
        product_key: str,
        device_name: str,
        device_secret: str
    ) -> bool:
        """
        配置完整的阿里云 MQTT（KNS + CMQ）
        
        这个配置会发送两个命令：
        1. SET:KNS - 配置阿里云三元组
        2. SET:CMQ,10 - 切换到阿里云模式
        
        Args:
            product_key: 阿里云产品密钥
            device_name: 设备名称
            device_secret: 设备密钥
            
        Returns:
            bool: 是否成功启动配置流程
        """
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        # 导入命令构建函数
        from .network.cloud_mqtt import build_aliyun_mqtt_command
        
        # 构建命令序列
        valid, error, commands = build_aliyun_mqtt_command(
            product_key, device_name, device_secret
        )
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        self._log_message(f"Configuring Aliyun MQTT (2 commands)...")
        
        # 在新线程中发送命令序列
        threading.Thread(
            target=self._send_command_sequence_thread,
            args=(commands, "Aliyun MQTT Full Config"),
            daemon=True
        ).start()
        
        return True
    
    # ==================== 位置和安装配置 (Sprint 1 新增) ====================
    
    def set_position_config(
        self,
        region: str,
        building_type: str,
        user_attr: str,
        device_name: str
    ) -> bool:
        """
        设置设备位置和属性配置 (SET:PO)
        
        Args:
            region: 行政区划路径，如 "/Shandong/RiZhao/Juxian/Guanbao"
            building_type: 建筑属性，如 "Zhuzhai"
            user_attr: 用户属性，如 "Gonglisuo-201202"
            device_name: 监测仪名称，如 "HLSYZG-01010001"
            
        Returns:
            bool: 是否成功启动配置流程
        """
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        # 导入命令构建函数
        from .network.position_config import build_po_command
        
        # 构建命令
        valid, error, po_cmd = build_po_command(region, building_type, user_attr, device_name)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        self._log_message(f"Setting position config: Region={region}, Device={device_name}")
        
        # 在新线程中发送命令
        threading.Thread(
            target=self._send_config_command_thread,
            args=(po_cmd, "Position Config"),
            daemon=True
        ).start()
        
        return True
    
    def set_install_mode(self, mode: int) -> bool:
        """
        设置传感器安装模式 (SET:ISG)
        
        Args:
            mode: 安装模式 (0-12)
                  0 = 默认模式
                  1-2 = 地面安装
                  3-6 = 侧面安装
                  7-12 = 顶部安装
                  
        Returns:
            bool: 是否成功启动配置流程
        """
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        # 导入命令构建函数
        from .sensors.install_mode import build_isg_command, get_mode_description
        
        # 构建命令
        valid, error, isg_cmd = build_isg_command(mode)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        mode_desc = get_mode_description(mode)
        self._log_message(f"Setting install mode: {mode} - {mode_desc}")
        
        # 在新线程中发送命令
        threading.Thread(
            target=self._send_config_command_thread,
            args=(isg_cmd, "Install Mode"),
            daemon=True
        ).start()
        
        return True
    
    # ==================== 命令序列发送 (辅助方法) ====================
    
    def _send_command_sequence_thread(
        self,
        commands: list,
        config_type: str
    ) -> None:
        """
        在线程中发送命令序列
        
        Args:
            commands: 命令字符串列表
            config_type: 配置类型描述
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
            
            # 逐个发送命令
            for i, command in enumerate(commands):
                self._log_message(f"Sending command {i+1}/{len(commands)}: {command}")
                
                success, error = self.serial_manager.send_line(command)
                if not success:
                    self._log_message(f"Error sending command {i+1}: {error}")
                    return
                
                # 等待响应
                time.sleep(2.0)
                
                # 读取响应
                if self.serial_manager.serial_port.in_waiting > 0:
                    response = self.serial_manager.serial_port.read(
                        self.serial_manager.serial_port.in_waiting
                    )
                    response_str = response.decode("utf-8", errors="ignore").strip()
                    if response_str:
                        self._log_message(f"Response {i+1}: {response_str}")
                
                # 命令间隔
                if i < len(commands) - 1:
                    time.sleep(1.0)
            
            self._log_message(f"{config_type} sequence completed!")
            
            # 恢复数据流
            if 'start_data_stream' in self.callbacks:
                time.sleep(1.0)
                self.callbacks['start_data_stream']()
                
        except Exception as e:
            self._log_message(f"Error in command sequence: {str(e)}")

    # ==================== System 控制命令 (SS:11-SS:27) ====================

    def _send_simple_command(self, command: str, description: str) -> bool:
        """
        发送简单命令（无参数）
        
        Args:
            command: 命令字符串
            description: 命令描述
            
        Returns:
            bool: 是否发送成功
        """
        if not self.serial_manager.is_connected:
            self._log_message("Error: Not connected to serial port!")
            return False
        
        try:
            success, error = self.serial_manager.send_line(command)
            if success:
                self._log_message(f"Sent: {command} ({description})")
                return True
            else:
                self._log_message(f"Error sending {command}: {error}")
                return False
        except Exception as e:
            self._log_message(f"Error sending command: {e}")
            return False

    def save_sensor_config(self) -> bool:
        """保存传感器配置 (SS:12)"""
        return self._send_simple_command("SS:12", "Save Sensor Config")

    def restore_default_config(self) -> bool:
        """恢复默认配置 (SS:11)"""
        return self._send_simple_command("SS:11", "Restore Default")

    def deactivate_sensor(self) -> bool:
        """停用传感器 (SS:27)"""
        return self._send_simple_command("SS:27", "Deactivate Sensor")

    def set_local_coordinate_mode(self) -> bool:
        """设置局部坐标模式 (SS:2)"""
        return self._send_simple_command("SS:2", "Local Coordinate Mode")

    def set_global_coordinate_mode(self) -> bool:
        """设置全局坐标模式 (SS:3)"""
        return self._send_simple_command("SS:3", "Global Coordinate Mode")

    def start_cpu_monitor(self) -> bool:
        """启动 CPU 监控 (SS:5)"""
        return self._send_simple_command("SS:5", "CPU Monitor")

    def start_sensor_calibration(self) -> bool:
        """启动传感器校准 (SS:6)"""
        return self._send_simple_command("SS:6", "Sensor Calibration")

    def trigger_buzzer(self) -> bool:
        """触发蜂鸣器 (SS:14)"""
        return self._send_simple_command("SS:14", "Buzzer")

    def check_upgrade(self) -> bool:
        """检查升级 (SS:15)"""
        return self._send_simple_command("SS:15", "Check Upgrade")

    def enter_ap_mode(self) -> bool:
        """进入 AP 模式 (SS:16)"""
        return self._send_simple_command("SS:16", "AP Mode")

    # ==================== Sensors 配置命令 ====================

    def set_kalman_filter(self, q: float, r: float) -> bool:
        """
        设置卡尔曼滤波系数 (SET:KFQR)
        
        Args:
            q: 过程噪声 (Q)，范围 0.001-1.0
            r: 测量噪声 (R)，范围 1.0-100.0
            
        Returns:
            bool: 是否发送成功
        """
        from sensor_calibrator.sensors.filter import build_kfqr_command
        
        valid, error, cmd = build_kfqr_command(q, r)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        return self._send_simple_command(cmd, "Kalman Filter")

    def set_filter_on(self) -> bool:
        """开启滤波 (SS:17,1)"""
        from sensor_calibrator.sensors.filter import build_ss17_toggle_filter
        cmd = build_ss17_toggle_filter(True)
        return self._send_simple_command(cmd, "Filter ON")

    def set_filter_off(self) -> bool:
        """关闭滤波 (SS:17,0)"""
        from sensor_calibrator.sensors.filter import build_ss17_toggle_filter
        cmd = build_ss17_toggle_filter(False)
        return self._send_simple_command(cmd, "Filter OFF")

    def set_gyro_levels(self, level1: float, level2: float, level3: float,
                        level4: float, level5: float) -> bool:
        """
        设置角度报警等级 (SET:GROLEVEL)
        
        Args:
            level1-level5: 5个等级阈值（递增）
            
        Returns:
            bool: 是否发送成功
        """
        from sensor_calibrator.sensors.level_config import build_grolevel_command
        
        valid, error, cmd = build_grolevel_command(level1, level2, level3, level4, level5)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        return self._send_simple_command(cmd, "Gyro Levels")

    def set_accel_levels(self, level1: float, level2: float, level3: float,
                         level4: float, level5: float) -> bool:
        """
        设置加速度报警等级 (SET:ACCLEVEL)
        
        Args:
            level1-level5: 5个等级阈值（递增）
            
        Returns:
            bool: 是否发送成功
        """
        from sensor_calibrator.sensors.level_config import build_acclevel_command
        
        valid, error, cmd = build_acclevel_command(level1, level2, level3, level4, level5)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        return self._send_simple_command(cmd, "Accel Levels")

    def set_voltage_scales(self, scale1: float, scale2: float) -> bool:
        """
        设置电压传感器比例 (SET:VKS)
        
        Args:
            scale1: 电压1比例系数
            scale2: 电压2比例系数
            
        Returns:
            bool: 是否发送成功
        """
        from sensor_calibrator.sensors.auxiliary import build_vks_command
        
        valid, error, cmd = build_vks_command(scale1, scale2)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        return self._send_simple_command(cmd, "Voltage Scales")

    def set_temp_offset(self, offset: float) -> bool:
        """
        设置温度传感器偏移 (SET:TME)
        
        Args:
            offset: 温度偏移值 (°C)
            
        Returns:
            bool: 是否发送成功
        """
        from sensor_calibrator.sensors.auxiliary import build_tme_command
        
        valid, error, cmd = build_tme_command(offset)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        return self._send_simple_command(cmd, "Temperature Offset")

    def set_mag_offsets(self, x: float, y: float, z: float) -> bool:
        """
        设置磁力传感器零偏 (SET:MAGOF)
        
        Args:
            x: X轴零偏
            y: Y轴零偏
            z: Z轴零偏
            
        Returns:
            bool: 是否发送成功
        """
        from sensor_calibrator.sensors.auxiliary import build_magof_command
        
        valid, error, cmd = build_magof_command(x, y, z)
        if not valid:
            self._log_message(f"Error: {error}")
            return False
        
        return self._send_simple_command(cmd, "Mag Offsets")
