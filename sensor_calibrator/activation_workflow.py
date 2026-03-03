"""
Activation Workflow Module

Manages sensor activation workflow.
"""

import hashlib
import json
import re
import secrets
import threading
import time
from typing import Callable, Optional, Dict, Any

from .config import Config


class ActivationWorkflow:
    """
    管理传感器激活流程
    
    负责:
    - MAC地址提取和验证
    - 激活密钥生成
    - 密钥验证
    - 传感器激活
    """
    
    def __init__(self, callbacks: dict):
        """
        初始化 ActivationWorkflow
        
        Args:
            callbacks: 回调函数字典，包含:
                - 'log_message': 日志记录函数
                - 'get_serial_port': 获取串口对象
                - 'is_connected': 检查连接状态
                - 'stop_data_stream': 停止数据流
                - 'start_data_stream': 开始数据流
                - 'send_ss8_command': 发送SS8命令
                - 'update_activation_status': 更新激活状态显示
        """
        self.callbacks = callbacks
        
        # 激活状态
        self._mac_address: Optional[str] = None
        self._generated_key: Optional[str] = None
        self._is_activated: bool = False
    
    # ==================== 属性 ====================
    
    @property
    def mac_address(self) -> Optional[str]:
        """获取MAC地址"""
        return self._mac_address
    
    @property
    def generated_key(self) -> Optional[str]:
        """获取生成的密钥"""
        return self._generated_key
    
    @property
    def is_activated(self) -> bool:
        """获取激活状态"""
        return self._is_activated
    
    @property
    def key_fragment(self) -> Optional[str]:
        """获取密钥片段（用于显示）"""
        if self._generated_key and len(self._generated_key) >= 12:
            return self._generated_key[5:12]
        return None
    
    # ==================== MAC地址处理 ====================
    
    def extract_mac_from_properties(self, sensor_properties: Dict[str, Any]) -> Optional[str]:
        """
        从传感器属性中提取MAC地址
        
        Args:
            sensor_properties: 传感器属性字典
            
        Returns:
            Optional[str]: MAC地址或None
        """
        if not sensor_properties:
            return None
        
        # 在sys字段中查找MAC地址
        if "sys" in sensor_properties:
            sys_info = sensor_properties["sys"]
            
            # 尝试不同的MAC地址字段名
            mac_keys = ["MAC", "mac", "mac_address", "macAddress", "device_mac"]
            for key in mac_keys:
                if key in sys_info:
                    mac_value = sys_info[key]
                    if self.validate_mac_address(mac_value):
                        self._mac_address = mac_value
                        return mac_value
            
            # 在设备名称中查找MAC地址模式
            if "DN" in sys_info:
                dn_value = sys_info["DN"]
                mac_pattern = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
                match = re.search(mac_pattern, dn_value)
                if match:
                    self._mac_address = match.group()
                    return self._mac_address
        
        return None
    
    @staticmethod
    def validate_mac_address(mac_str: str) -> bool:
        """
        验证MAC地址格式
        
        Args:
            mac_str: MAC地址字符串
            
        Returns:
            bool: 是否有效
        """
        if not mac_str or not isinstance(mac_str, str):
            return False
        
        # MAC地址格式验证：XX:XX:XX:XX:XX:XX 或 XX-XX-XX-XX-XX-XX
        mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        return re.match(mac_pattern, mac_str) is not None
    
    # ==================== 密钥生成和验证 ====================
    
    def generate_key_from_mac(self, mac_address: str) -> str:
        """
        基于MAC地址生成64字符的SHA-256密钥
        
        Args:
            mac_address: MAC地址
            
        Returns:
            str: 64字符十六进制密钥
        """
        # 清理MAC地址格式（移除冒号、连字符等分隔符）
        cleaned_mac = mac_address.replace(":", "").replace("-", "").lower()
        
        # 验证MAC地址长度（应为12个十六进制字符，对应6字节）
        if len(cleaned_mac) != 12:
            raise ValueError(
                f"无效的MAC地址格式: {mac_address}. 清理后应为12个十六进制字符，实际得到{len(cleaned_mac)}个字符: {cleaned_mac}"
            )
        
        # 将十六进制字符串转换为字节
        try:
            mac_bytes = bytes.fromhex(cleaned_mac)
        except ValueError as e:
            raise ValueError(f"MAC地址包含无效的十六进制字符: {cleaned_mac}") from e
        
        # 计算SHA-256哈希值
        hash_object = hashlib.sha256(mac_bytes)
        hex_digest = hash_object.hexdigest()  # 直接获取64字符的十六进制字符串
        
        self._generated_key = hex_digest
        return hex_digest
    
    def verify_key(self, input_key: str, mac_address: Optional[str] = None) -> bool:
        """
        验证输入的密钥是否与基于MAC地址生成的密钥匹配
        
        Args:
            input_key: 输入的密钥
            mac_address: MAC地址（可选，使用已存储的）
            
        Returns:
            bool: 是否匹配
        """
        self._log_message(f"[DEBUG] verify_key called with input: {input_key}, len={len(input_key) if input_key else 0}")
        
        mac = mac_address or self._mac_address
        if not mac:
            self._log_message("[DEBUG] No MAC address available")
            return False
        
        # 生成预期密钥
        expected_key = self.generate_key_from_mac(mac)
        expected_fragment = expected_key[5:12]
        
        self._log_message(f"[DEBUG] Expected fragment: {expected_fragment}")
        self._log_message(f"[DEBUG] Input key: {input_key}")
        
        # 使用恒定时间比较防止时序攻击
        if len(input_key) != 7 or len(expected_key) != 64:
            self._log_message(f"[DEBUG] Length check failed: input_len={len(input_key)}, expected_len={len(expected_key)}")
            return False
        
        result = secrets.compare_digest(input_key.lower(), expected_fragment.lower())
        self._log_message(f"[DEBUG] Compare result: {result}")
        return result
    
    def check_activation_status(self, sensor_properties: Dict[str, Any]) -> bool:
        """
        检查传感器激活状态
        
        Args:
            sensor_properties: 传感器属性字典
            
        Returns:
            bool: 是否已激活
        """
        self._log_message(f"[DEBUG] check_activation_status called")
        self._log_message(f"[DEBUG] MAC in workflow: {self._mac_address}")
        
        if not sensor_properties or not self._mac_address:
            self._log_message(f"[DEBUG] Missing data: properties={bool(sensor_properties)}, mac={bool(self._mac_address)}")
            return False
        
        # 从属性中获取AKY字段
        aks_value = None
        if "sys" in sensor_properties:
            sys_info = sensor_properties["sys"]
            aks_value = (
                sys_info.get("AKY") or sys_info.get("aky") or sys_info.get("ak_key")
            )
        
        self._log_message(f"[DEBUG] AKY value: {aks_value}")
        
        if not aks_value:
            self._is_activated = False
            self._log_message("[DEBUG] No AKY value found")
            return False
        
        # 验证密钥
        try:
            self._is_activated = self.verify_key(aks_value)
            self._log_message(f"[DEBUG] verify_key result: {self._is_activated}")
            return self._is_activated
        except Exception as e:
            self._log_message(f"Error verifying activation key: {str(e)}")
            return False
    
    # ==================== 激活操作 ====================
    
    def activate_sensor(self) -> bool:
        """
        激活传感器
        
        Returns:
            bool: 是否成功启动激活流程
        """
        if 'is_connected' in self.callbacks and not self.callbacks['is_connected']():
            self._log_message("Error: Not connected to serial port!")
            return False
        
        if not self._mac_address or not self._generated_key:
            self._log_message("Error: MAC address or generated key not available!")
            return False
        
        self._log_message("Starting sensor activation process...")
        
        # 在新线程中激活传感器
        threading.Thread(target=self._activate_sensor_thread, daemon=True).start()
        
        return True
    
    def _activate_sensor_thread(self) -> None:
        """在新线程中激活传感器"""
        try:
            # 停止数据流（如果正在运行）
            original_reading_state = False
            if 'is_reading' in self.callbacks:
                original_reading_state = self.callbacks['is_reading']()
            
            if original_reading_state and 'stop_data_stream' in self.callbacks:
                self._log_message("Stopping data stream for activation...")
                self.callbacks['stop_data_stream']()
                time.sleep(1.0)
            
            # 获取串口
            ser = None
            if 'get_serial_port' in self.callbacks:
                ser = self.callbacks['get_serial_port']()
            
            if not ser:
                self._log_message("Error: Serial port not available")
                return
            
            # 清空输入缓冲区
            ser.reset_input_buffer()
            time.sleep(Config.BUFFER_CLEAR_DELAY)
            
            # 发送激活命令
            activation_cmd = f"SET:AKY,{self._generated_key[5:12]}"
            ser.write(activation_cmd.encode())
            ser.flush()
            
            self._log_message(f"Sent activation command: SET:AKY,{self._generated_key[5:12]}")
            
            # 等待响应
            time.sleep(2.0)
            
            # 读取响应
            response_bytes = b""
            start_time = time.time()
            timeout = 5.0
            
            self._log_message("Reading response...")
            
            activated = False
            while time.time() - start_time < timeout:
                if ser.in_waiting > 0:
                    chunk = ser.read(ser.in_waiting)
                    response_bytes += chunk
                    
                    response_str = response_bytes.decode("utf-8", errors="ignore")
                    
                    if "success" in response_str.lower() or "activated" in response_str.lower():
                        self._log_message("Sensor activation successful!")
                        self._is_activated = True
                        activated = True
                        if 'update_activation_status' in self.callbacks:
                            self.callbacks['update_activation_status'](True)
                        break
                
                time.sleep(Config.THREAD_ERROR_DELAY)
            
            if not activated:
                self._log_message("Activation response timeout or failed")
            
            # 恢复数据流状态
            if original_reading_state and 'start_data_stream' in self.callbacks:
                self._log_message("Restarting data stream...")
                time.sleep(1.0)
                self.callbacks['start_data_stream']()
                
        except Exception as e:
            self._log_message(f"Error during activation: {str(e)}")
    
    def verify_activation(self, sensor_properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        验证传感器激活状态
        
        Args:
            sensor_properties: 传感器属性字典（可选）
            
        Returns:
            bool: 是否成功启动验证流程
        """
        self._log_message("Verifying sensor activation status...")
        
        # 重新读取传感器属性来获取最新的AKY值
        threading.Thread(
            target=self._verify_activation_thread,
            args=(sensor_properties,),
            daemon=True
        ).start()
        
        return True
    
    def _verify_activation_thread(self, sensor_properties: Optional[Dict[str, Any]] = None) -> None:
        """在新线程中验证激活状态"""
        try:
            # 停止数据流
            original_reading_state = False
            if 'is_reading' in self.callbacks:
                original_reading_state = self.callbacks['is_reading']()
            
            if original_reading_state and 'stop_data_stream' in self.callbacks:
                self._log_message("Stopping data stream for verification...")
                self.callbacks['stop_data_stream']()
                time.sleep(1.0)
            
            # 获取串口
            ser = None
            if 'get_serial_port' in self.callbacks:
                ser = self.callbacks['get_serial_port']()
            
            if not ser:
                self._log_message("Error: Serial port not available")
                return
            
            # 清空输入缓冲区
            ser.reset_input_buffer()
            time.sleep(Config.BUFFER_CLEAR_DELAY)
            
            # 发送SS:8命令获取最新属性
            if 'send_ss8_command' in self.callbacks:
                self.callbacks['send_ss8_command']()
            
            time.sleep(2.0)
            
            # 读取响应
            response_bytes = b""
            start_time = time.time()
            timeout = 5.0
            
            while time.time() - start_time < timeout:
                if ser.in_waiting > 0:
                    response_bytes += ser.read(ser.in_waiting)
                
                response_str = response_bytes.decode("utf-8", errors="ignore")
                json_start = response_str.find("{")
                json_end = response_str.rfind("}")
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_str = response_str[json_start:json_end + 1]
                    
                    try:
                        latest_properties = json.loads(json_str)
                        
                        # 检查激活状态
                        is_activated = self.check_activation_status(latest_properties)
                        self._is_activated = is_activated
                        
                        if 'update_activation_status' in self.callbacks:
                            self.callbacks['update_activation_status'](is_activated)
                        
                        if is_activated:
                            self._log_message("✓ Sensor is properly activated!")
                        else:
                            self._log_message("✗ Sensor is not activated or activation key mismatch")
                        
                        break
                        
                    except json.JSONDecodeError:
                        continue
                
                time.sleep(Config.THREAD_ERROR_DELAY)
            
            # 恢复数据流状态
            if original_reading_state and 'start_data_stream' in self.callbacks:
                self._log_message("Restarting data stream...")
                time.sleep(1.0)
                self.callbacks['start_data_stream']()
                
        except Exception as e:
            self._log_message(f"Error during verification: {str(e)}")
    
    # ==================== 辅助方法 ====================
    
    def _log_message(self, message: str) -> None:
        """记录日志（通过回调）"""
        if 'log_message' in self.callbacks:
            self.callbacks['log_message'](message)
    
    def reset(self) -> None:
        """重置激活状态"""
        self._mac_address = None
        self._generated_key = None
        self._is_activated = False
