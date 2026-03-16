"""
SensorCalibrator Application Callbacks

回调函数集合，处理UI事件和业务逻辑。
"""

import threading
import time
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
from typing import Dict, Any

from ..config import Config


class AppCallbacks:
    """应用回调函数集合"""
    
    def __init__(self, app):
        """
        初始化回调函数集合
        
        Args:
            app: SensorCalibratorApp 实例
        """
        self.app = app
    
    # ==================== 串口相关回调 ====================
    
    def refresh_ports(self):
        """刷新可用串口列表"""
        self.app.refresh_ports()
    
    def toggle_connection(self):
        """切换串口连接"""
        if not self.app.port_var or not self.app.baud_var:
            self.app.log_message("Error: Port variables not initialized!")
            return
        
        port = self.app.port_var.get()
        baudrate = int(self.app.baud_var.get())
        
        if self.app.serial_manager.is_connected:
            self.disconnect_serial()
        else:
            self.connect_serial(port, baudrate)
    
    def connect_serial(self, port: str, baudrate: int):
        """连接串口"""
        if self.app.serial_manager.connect(port, baudrate):
            if self.app.connect_btn:
                self.app.connect_btn.config(text="Disconnect")
            if self.app.data_btn:
                self.app.data_btn.config(state="normal")
            if self.app.data_btn2:
                self.app.data_btn2.config(state="normal")
            self.app.ser = self.app.serial_manager.serial_port
            
            if self.app.read_props_btn:
                self.app.read_props_btn.config(state="normal")
            if self.app.read_device_btn:
                self.app.read_device_btn.config(state="normal")
    
    def disconnect_serial(self):
        """断开串口连接（带确认弹窗）"""
        # 如果正在读取数据，先停止
        if self.app.is_reading:
            self.stop_data_stream()
        
        # 显示确认弹窗
        if not self.app.reset_ui_with_confirmation():
            # 用户取消，不断开连接
            return
        
        # 用户确认，执行断开
        self.app.serial_manager.disconnect()
        self.app.ser = None
        
        if self.app.connect_btn:
            self.app.connect_btn.config(text="Connect")
        if self.app.data_btn:
            self.app.data_btn.config(text="Start Data Stream")
            self.app.data_btn.config(state="disabled")
        if self.app.data_btn2:
            self.app.data_btn2.config(text="Start CAS Stream")
            self.app.data_btn2.config(state="disabled")
        if self.app.read_props_btn:
            self.app.read_props_btn.config(state="disabled")
        if self.app.read_device_btn:
            self.app.read_device_btn.config(state="disabled")
        if self.app.resend_btn:
            self.app.resend_btn.config(state="disabled")
        if self.app.local_coord_btn:
            self.app.local_coord_btn.config(state="disabled")
        if self.app.global_coord_btn:
            self.app.global_coord_btn.config(state="disabled")
        if self.app.calibrate_btn:
            self.app.calibrate_btn.config(state="disabled")
        if self.app.send_btn:
            self.app.send_btn.config(state="disabled")
        
        # 重置激活相关状态
        self.app._aky_from_ss13 = None
        self.app.log_message("串口已断开连接")
    
    # ==================== 数据流相关回调 ====================
    
    def toggle_data_stream(self):
        """切换数据流状态"""
        if not self.app.serial_manager.is_connected:
            self.app.log_message("Error: Not connected to serial port!")
            return

        if not self.app.serial_manager.is_reading:
            self.start_data_stream()
        else:
            self.stop_data_stream()
    
    def toggle_data_stream2(self):
        """切换校准流状态"""
        if not self.app.serial_manager.is_connected:
            self.app.log_message("Error: Not connected to serial port!")
            return

        if not self.app.serial_manager.is_reading:
            self.start_data_stream2()
        else:
            self.stop_data_stream2()
    
    def start_data_stream(self):
        """开始数据流"""
        if not self.app.serial_manager.is_connected:
            self.app.log_message("Error: Not connected to serial port!")
            return
        
        if self.app.serial_manager.send_ss0_start_stream():
            if self.app.serial_manager.start_reading():
                self.app.is_reading = True
                if self.app.data_btn:
                    self.app.data_btn.config(text="Stop Data Stream")
                if self.app.calibrate_btn:
                    self.app.calibrate_btn.config(state="normal")
                
                self.app.clear_data()
                self.app.data_processor.data_start_time = time.time()
                self.app.data_processor.packet_count = 0
                self.app.packets_received = 0
                
                self.app.schedule_update_gui()
    
    def start_data_stream2(self):
        """开始校准流"""
        if not self.app.serial_manager.is_connected:
            self.app.log_message("Error: Not connected to serial port!")
            return
        
        if self.app.serial_manager.send_ss1_start_calibration():
            if self.app.serial_manager.start_reading():
                self.app.is_reading = True
                if self.app.data_btn2:
                    self.app.data_btn2.config(text="Stop Calibration Stream")
                if self.app.calibrate_btn:
                    self.app.calibrate_btn.config(state="disabled")
                
                self.app.clear_data()
                self.app.data_processor.data_start_time = time.time()
                self.app.data_processor.packet_count = 0
                self.app.packets_received = 0
                
                self.app.schedule_update_gui()
    
    def stop_data_stream(self):
        """停止数据流"""
        if not self.app.is_reading:
            return

        self.app.is_reading = False
        self.app.serial_manager.stop_reading()
        self.app.serial_manager.send_ss4_stop_stream()

        if self.app.data_btn:
            self.app.data_btn.config(text="Start Data Stream")
            self.app.data_btn.config(state="normal")
        if self.app.calibrate_btn:
            self.app.calibrate_btn.config(state="disabled")
        if self.app.capture_btn:
            self.app.capture_btn.config(state="disabled")
    
    def stop_data_stream2(self):
        """停止校准流"""
        if not self.app.is_reading:
            return

        self.app.is_reading = False
        self.app.serial_manager.stop_reading()
        self.app.serial_manager.send_ss4_stop_stream()

        if self.app.data_btn2:
            self.app.data_btn2.config(text="Start CAS Stream")
            self.app.data_btn2.config(state="normal")
        if self.app.calibrate_btn:
            self.app.calibrate_btn.config(state="disabled")
        if self.app.capture_btn:
            self.app.capture_btn.config(state="disabled")
    
    # ==================== 校准相关回调 ====================
    
    def start_calibration(self):
        """开始校准"""
        if not self.app.is_reading:
            self.app.log_message("Error: Start data stream first!")
            return
        
        self.app.is_calibrating = True
        self.app.calibration_workflow.start_calibration()
        if self.app.calibrate_btn:
            self.app.calibrate_btn.config(state="disabled")
        if self.app.capture_btn:
            self.app.capture_btn.config(state="normal")
        if self.app.data_btn:
            self.app.data_btn.config(state="disabled")
    
    def capture_position(self):
        """采集当前位置数据"""
        if self.app.capture_btn:
            self.app.capture_btn.config(state="disabled")
        self.app.calibration_workflow.capture_position()
    
    def finish_calibration(self):
        """完成校准"""
        self.app.calibration_workflow.finish_calibration()
    
    def generate_calibration_commands(self):
        """生成校准命令"""
        if self.app.calibration_workflow.calibration_params:
            self.app.calibration_params = self.app.calibration_workflow.calibration_params
        
        commands = self.app.calibration_workflow.generate_calibration_commands()
        
        if self.app.cmd_text:
            self.app.cmd_text.delete(1.0, "end")
            for cmd in commands:
                self.app.cmd_text.insert("end", cmd + "\n")
        
        self.app.log_message(
            "Calibration commands generated. Click 'Send All Commands' to send to ESP32."
        )
    
    def send_all_commands(self):
        """发送所有校准命令到串口"""
        if not self.app.ser or not self.app.ser.is_open:
            self.app.log_message("Error: Not connected to serial port!")
            return

        if not self.app.cmd_text:
            self.app.log_message("Error: Command text widget not available!")
            return
        
        commands = self.app.cmd_text.get(1.0, "end").strip().split("\n")

        if not commands or commands[0] == "":
            self.app.log_message("Error: No calibration commands to send!")
            return

        self.app.log_message("Sending calibration commands to ESP32...")

        threading.Thread(
            target=self.send_commands_thread, args=(commands,), daemon=True
        ).start()
    
    def send_commands_thread(self, commands):
        """在新线程中发送命令"""
        if self.app.ser is None:
            return
        
        try:
            for i, cmd in enumerate(commands):
                if cmd.strip():
                    self.app.ser.write(f"{cmd}\n".encode())
                    self.app.ser.flush()

                    self.app.root.after(0, lambda c=cmd: self.app.log_message(f"Sent: {c}"))

                    time.sleep(2)

                    try:
                        if self.app.ser is None:
                            continue
                        response = self.app.ser.readline().decode().strip()
                        if response:
                            self.app.root.after(
                                0, lambda r=response: self.app.log_message(f"Response: {r}")
                            )
                    except Exception as e:
                        self.app.log_message(f"Error reading command response: {e}", "DEBUG")

            self.app.root.after(
                0,
                lambda: self.app.log_message("All calibration commands sent successfully!")
            )

            self.app.root.after(0, lambda: self.app.resend_btn.config(state="normal") if self.app.resend_btn else None)
            self.app.root.after(0, self.ask_read_properties)

        except Exception as e:
            self.app.root.after(
                0, lambda: self.app.log_message(f"Error sending commands: {str(e)}")
            )
    
    def resend_all_commands(self):
        """重新发送所有命令"""
        response = messagebox.askyesno(
            "Resend Commands",
            "Are you sure you want to resend all calibration commands?",
        )
        if response:
            self.send_all_commands()
    
    def save_calibration_parameters(self):
        """保存校准参数到文件"""
        if not self.app.cmd_text:
            self.app.log_message("Error: Command text widget not available!")
            return
        
        try:
            save_data = {
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "calibration_parameters": self.app.calibration_params,
                "calibration_commands": self.app.cmd_text.get(1.0, "end")
                .strip()
                .split("\n"),
                "sensor_properties": self.app.sensor_properties,
            }

            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"calibration_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )

            if filename:
                import json
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)

                self.app.log_message(f"Calibration parameters saved to: {filename}")

                with open(self.app.calibration_file, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)

                self.app.log_message(
                    f"Parameters also saved to default file: {self.app.calibration_file}"
                )

        except Exception as e:
            self.app.log_message(f"Error saving calibration parameters: {str(e)}")
    
    def load_calibration_parameters(self):
        """从文件加载校准参数"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                import json
                with open(filename, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)

                if "calibration_parameters" in loaded_data:
                    self.app.calibration_params.update(
                        loaded_data["calibration_parameters"]
                    )

                if "calibration_commands" in loaded_data and self.app.cmd_text:
                    self.app.cmd_text.delete(1.0, "end")
                    for cmd in loaded_data["calibration_commands"]:
                        self.app.cmd_text.insert("end", cmd + "\n")

                if "sensor_properties" in loaded_data:
                    self.app.sensor_properties = loaded_data["sensor_properties"]

                self.app.log_message(f"Calibration parameters loaded from: {filename}")
                if self.app.send_btn:
                    self.app.send_btn.config(state="normal")
                if self.app.save_btn:
                    self.app.save_btn.config(state="normal")
                if self.app.read_props_btn:
                    self.app.read_props_btn.config(state="normal")
                if self.app.read_device_btn:
                    self.app.read_device_btn.config(state="normal")

        except Exception as e:
            self.app.log_message(f"Error loading calibration parameters: {str(e)}")
    
    def ask_read_properties(self):
        """询问是否读取校准参数"""
        response = messagebox.askyesno(
            "Read Calibration Parameters",
            "All calibration commands have been sent successfully.\n\n"
            "Do you want to read calibration parameters from device?",
        )
        if response:
            self.read_device_info()
    
    def read_sensor_properties(self):
        """读取传感器属性"""
        self.app.read_sensor_properties()
    
    def read_device_info(self):
        """读取设备信息（如MAC、序列号、固件版本等）"""
        self.app.read_device_info()
    
    # ==================== 坐标模式相关回调 ====================
    
    def set_local_coordinate_mode(self):
        """设置局部坐标模式"""
        self.app.serial_manager.send_ss2_local_mode("Local Coordinate Mode")
    
    def set_global_coordinate_mode(self):
        """设置整体坐标模式"""
        self.app.serial_manager.send_ss3_global_mode("Global Coordinate Mode")
    
    # ==================== 激活相关回调 ====================
    
    def activate_sensor(self):
        """激活传感器"""
        if not self.app.mac_address or not self.app.generated_key:
            self.app.log_message("Error: MAC address or key not available")
            return

        self.app.activation_workflow.activate_sensor(
            mac_address=self.app.mac_address,
            generated_key=self.app.generated_key
        )
    
    def verify_activation(self):
        """验证传感器激活状态"""
        self.app.activation_workflow.verify_activation(self.app.sensor_properties)
    
    def read_calibration_params(self):
        """读取校准参数（独立命令）"""
        self.app.read_calibration_params()
    
    def verify_activation_status(self):
        """验证激活状态（独立命令）"""
        self.app.verify_activation_status()
    
    def copy_activation_key(self):
        """复制激活密钥片段到剪贴板"""
        try:
            if self.app.generated_key and len(self.app.generated_key) >= 12:
                key_fragment = self.app.generated_key[5:12]
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append(key_fragment)
                self.app.log_message(f"Activation key fragment copied to clipboard: {key_fragment}")
            else:
                self.app.log_message("Error: No activation key available to copy")
        except Exception as e:
            self.app.log_message(f"Error copying activation key: {str(e)}")
    
    # ==================== 网络配置相关回调 ====================
    
    def set_wifi_config(self):
        """设置WiFi配置"""
        if not self.app.ssid_var or not self.app.password_var:
            self.app.log_message("Error: WiFi variables not initialized!")
            return
        
        ssid = self.app.ssid_var.get().strip()
        password = self.app.password_var.get().strip()
        
        if self.app.network_manager.set_wifi_config(ssid, password):
            self.app.wifi_params = {"ssid": ssid, "password": password}
    
    def read_wifi_config(self):
        """读取WiFi配置"""
        self.app.network_manager.read_wifi_config()
    
    def set_mqtt_config(self):
        """设置MQTT配置"""
        if not self.app.mqtt_broker_var or not self.app.mqtt_user_var or not self.app.mqtt_password_var or not self.app.mqtt_port_var:
            self.app.log_message("Error: MQTT variables not initialized!")
            return
        
        broker = self.app.mqtt_broker_var.get().strip()
        username = self.app.mqtt_user_var.get().strip()
        password = self.app.mqtt_password_var.get().strip()
        port = self.app.mqtt_port_var.get().strip()
        
        if self.app.network_manager.set_mqtt_config(broker, username, password, port):
            self.app.mqtt_params = {
                "broker": broker,
                "username": username,
                "password": password,
                "port": port or "1883",
            }
    
    def read_mqtt_config(self):
        """读取MQTT配置"""
        self.app.network_manager.read_mqtt_config()
    
    def set_ota_config(self):
        """设置OTA配置"""
        if not self.app.URL1_var or not self.app.URL2_var or not self.app.URL3_var or not self.app.URL4_var:
            self.app.log_message("Error: OTA variables not initialized!")
            return
        
        url1 = self.app.URL1_var.get().strip()
        url2 = self.app.URL2_var.get().strip()
        url3 = self.app.URL3_var.get().strip()
        url4 = self.app.URL4_var.get().strip()
        
        if self.app.network_manager.set_ota_config(url1, url2, url3, url4):
            self.app.ota_params = {"URL1": url1, "URL2": url2, "URL3": url3, "URL4": url4}
    
    def read_ota_config(self):
        """读取OTA配置"""
        self.app.network_manager.read_ota_config()
    
    # ==================== Alarm & Device 回调 ====================
    
    def set_alarm_threshold(self):
        """设置报警阈值"""
        try:
            accel_str = self.app.ui_manager.get_entry_value('alarm_accel_threshold')
            gyro_str = self.app.ui_manager.get_entry_value('alarm_gyro_threshold')
            
            try:
                accel_threshold = float(accel_str)
                gyro_threshold = float(gyro_str)
            except ValueError:
                self.app.log_message("Error: Invalid threshold values")
                return
            
            if hasattr(self.app, 'network_manager'):
                success = self.app.network_manager.set_alarm_threshold(
                    accel_threshold, gyro_threshold
                )
                if success:
                    self.app.log_message(f"Setting alarm threshold: Accel={accel_threshold} m/s², Gyro={gyro_threshold}°")
            else:
                self.app.log_message("Error: NetworkManager not available")
                
        except Exception as e:
            self.app.log_message(f"Error setting alarm threshold: {str(e)}")
    
    def restart_sensor(self):
        """重启传感器"""
        try:
            if hasattr(self.app, 'serial_manager'):
                success = self.app.serial_manager.send_ss9_restart_sensor()
                if success:
                    self.app.log_message("Sent restart command to sensor (SS:9)")
            else:
                self.app.log_message("Error: SerialManager not available")
        except Exception as e:
            self.app.log_message(f"Error restarting sensor: {str(e)}")
    
    def save_config(self):
        """保存配置到传感器"""
        try:
            if hasattr(self.app, 'serial_manager'):
                success = self.app.serial_manager.send_ss7_save_config()
                if success:
                    self.app.log_message("Sent save config command to sensor (SS:7)")
            else:
                self.app.log_message("Error: SerialManager not available")
        except Exception as e:
            self.app.log_message(f"Error saving config: {str(e)}")

    def reset_ui_with_confirmation(self):
        """带确认的刷新页面"""
        # 如果正在读取数据，先停止
        if self.app.is_reading:
            self.stop_data_stream()
        
        # 显示确认弹窗并重置
        self.app.reset_ui_with_confirmation()
