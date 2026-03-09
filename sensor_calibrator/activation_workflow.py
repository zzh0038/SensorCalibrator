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
    
    # 密钥片段长度配置（16字符 = 64位密钥空间）
    KEY_FRAGMENT_LENGTH: int = 16
    
    @property
    def key_fragment(self) -> Optional[str]:
        """获取密钥片段（用于显示）- 16字符（64位密钥空间）"""
        if self._generated_key and len(self._generated_key) >= self.KEY_FRAGMENT_LENGTH:
            return self._generated_key[:self.KEY_FRAGMENT_LENGTH]
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

        使用恒定时间比较防止时序攻击。

        Args:
            input_key: 输入的密钥
            mac_address: MAC地址（可选，使用已存储的）

        Returns:
            bool: 是否匹配
        """
        mac = mac_address or self._mac_address
        if not mac:
            return False

        # 生成预期密钥
        expected_key = self.generate_key_from_mac(mac)
        expected_fragment = expected_key[:self.KEY_FRAGMENT_LENGTH]

        # 修复：使用 try/except 包裹 compare_digest
        # 如果长度不匹配会抛出 TypeError，但在时间上是恒定的
        # 避免在比较前进行长度检查导致的时序泄漏
        try:
            return secrets.compare_digest(input_key.lower(), expected_fragment.lower())
        except TypeError:
            # 长度不匹配，比较失败
            return False
    
    def check_activation_status(
        self,
        sensor_properties: Dict[str, Any],
        mac_address: Optional[str] = None
    ) -> bool:
        """
        检查传感器激活状态

        Args:
            sensor_properties: 传感器属性字典
            mac_address: MAC地址（可选，优先于内部状态）

        Returns:
            bool: 是否已激活
        """
        # 优先使用传入的参数，保持向后兼容
        mac = mac_address or self._mac_address

        if not sensor_properties or not mac:
            return False

        # 从属性中获取AKY字段
        aks_value = None
        if "sys" in sensor_properties:
            sys_info = sensor_properties["sys"]
            aks_value = (
                sys_info.get("AKY") or sys_info.get("aky") or sys_info.get("ak_key")
            )

        if not aks_value:
            self._is_activated = False
            return False

        # 验证密钥（传入 MAC 地址）
        try:
            self._is_activated = self.verify_key(aks_value, mac_address=mac)
            return self._is_activated
        except Exception as e:
            self._log_message(f"Error verifying activation key: {str(e)}")
            return False
    
    # ==================== 激活操作 ====================
    
    def activate_sensor(
        self,
        mac_address: Optional[str] = None,
        generated_key: Optional[str] = None
    ) -> bool:
        """
        激活传感器

        Args:
            mac_address: MAC地址（可选，优先于内部状态）
            generated_key: 生成的密钥（可选，优先于内部状态）

        Returns:
            bool: 是否成功启动激活流程
        """
        if 'is_connected' in self.callbacks and not self.callbacks['is_connected']():
            self._log_message("Error: Not connected to serial port!")
            return False

        # 优先使用传入的参数
        mac = mac_address or self._mac_address
        key = generated_key or self._generated_key

        if not mac or not key:
            self._log_message("Error: MAC address or generated key not available!")
            return False

        # 保存到内部状态（供线程使用）
        self._mac_address = mac
        self._generated_key = key

        self._log_message("Starting sensor activation process...")

        # 在新线程中激活传感器，传递参数
        threading.Thread(
            target=self._activate_sensor_thread,
            args=(mac, key),
            daemon=True
        ).start()

        return True
    
    def _activate_sensor_thread(
        self,
        mac_address: str,
        generated_key: str
    ) -> None:
        """在新线程中激活传感器

        Args:
            mac_address: MAC地址
            generated_key: 生成的密钥
        """
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

            # 发送激活命令（使用线程安全的 send_line 回调）
            key_fragment = generated_key[:self.KEY_FRAGMENT_LENGTH]
            activation_cmd = f"SET:AKY,{key_fragment}"
            if 'send_line' in self.callbacks:
                success, error = self.callbacks['send_line'](activation_cmd)
                if not success:
                    self._log_message(f"Error sending activation command: {error}")
                    return
            else:
                # 回退：直接写入（不推荐，但为了兼容性保留）
                ser.write(activation_cmd.encode())
                ser.flush()

            self._log_message(f"Sent activation command: SET:AKY,{key_fragment}")
            
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
