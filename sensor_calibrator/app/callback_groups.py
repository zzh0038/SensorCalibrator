"""
回调分组 - 按功能域组织回调方法

将 AppCallbacks 的 75+ 个方法按功能分组，提高可维护性。
每个组负责一个功能域，通过 CallbackRegistry 统一注册。
"""

import threading
import time
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
from typing import TYPE_CHECKING, Dict, Any, Optional
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .application import SensorCalibratorApp


class CallbackGroup(ABC):
    """回调分组基类"""
    
    def __init__(self, app: "SensorCalibratorApp"):
        self.app = app
    
    @abstractmethod
    def register_all(self) -> Dict[str, callable]:
        """返回该组所有回调方法的字典"""
        pass


class SerialCallbacks(CallbackGroup):
    """串口连接相关回调"""
    
    CALLBACK_NAMES = [
        'refresh_ports', 'toggle_connection', 'connect_serial', 'disconnect_serial'
    ]
    
    def register_all(self) -> Dict[str, callable]:
        return {
            'refresh_ports': self.refresh_ports,
            'toggle_connection': self.toggle_connection,
            'connect_serial': self.connect_serial,
            'disconnect_serial': self.disconnect_serial,
        }
    
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
            self.app.ser = self.app.serial_manager.serial_port
            
            self.app.enable_config_buttons()
    
    def disconnect_serial(self):
        """断开串口连接（带确认弹窗）"""
        if self.app.is_reading:
            self.app.callbacks.data_stream.stop_data_stream()
        
        if not self.app.show_reset_confirmation():
            return
        
        self.app.ser = None
        self.app.serial_manager.disconnect()
        self.app.reset_ui_state()
        self.app._aky_from_ss13 = None
        self.app.log_message("串口已断开连接")


class DataStreamCallbacks(CallbackGroup):
    """数据流控制相关回调"""
    
    CALLBACK_NAMES = [
        'toggle_data_stream', 'toggle_data_stream2', 'start_data_stream', 'stop_data_stream'
    ]
    
    def register_all(self) -> Dict[str, callable]:
        return {
            'toggle_data_stream': self.toggle_data_stream,
            'toggle_data_stream2': self.toggle_data_stream,  # 别名，用于第二个按钮
            'start_data_stream': self.start_data_stream,
            'stop_data_stream': self.stop_data_stream,
        }
    
    def toggle_data_stream(self):
        """切换数据流状态"""
        if not self.app.serial_manager.is_connected:
            self.app.log_message("Error: Not connected to serial port!")
            return

        if not self.app.serial_manager.is_reading:
            self.start_data_stream()
        else:
            self.stop_data_stream()
    
    def start_data_stream(self):
        """开始数据流"""
        self.app.start_data_stream()
    
    def stop_data_stream(self):
        """停止数据流"""
        self.app.stop_data_stream()


class CalibrationCallbacks(CallbackGroup):
    """六位置校准相关回调"""
    
    CALLBACK_NAMES = [
        'start_calibration', 'capture_position', 'finish_calibration',
        'pause_calibration', 'reset_calibration',
        'generate_calibration_commands', 'send_all_commands', 'resend_all_commands',
        'save_calibration_parameters', 'load_calibration_parameters',
        'read_calibration_params', 'check_calibration_status',
    ]
    
    def register_all(self) -> Dict[str, callable]:
        return {
            'start_calibration': self.start_calibration,
            'capture_position': self.capture_position,
            'finish_calibration': self.finish_calibration,
            'pause_calibration': self.pause_calibration,
            'reset_calibration': self.reset_calibration,
            'generate_calibration_commands': self.generate_calibration_commands,
            'send_all_commands': self.send_all_commands,
            'resend_all_commands': self.resend_all_commands,
            'save_calibration_parameters': self.save_calibration_parameters,
            'load_calibration_parameters': self.load_calibration_parameters,
            'read_calibration_params': self.read_calibration_params,
            'check_calibration_status': self.check_calibration_status,
        }
    
    def start_calibration(self):
        """开始六位置校准"""
        # 读取自动引导设置
        auto_guide = self.app.ui_manager.vars.get('cal_auto_guide')
        if auto_guide:
            enabled = auto_guide.get() == "1"
            self.app.calibration_workflow.set_auto_advance(enabled)
        
        self.app.calibration_workflow.start_calibration()
        
        # 更新UI显示
        if self.app.ui_manager:
            self.app.ui_manager.reset_calibration_display()
            self.app.ui_manager.set_widget_state('cal_capture_position_btn', 'normal')
            self.app.ui_manager.set_widget_state('cal_pause_calibration_btn', 'normal')
            self.app.ui_manager.set_widget_state('cal_reset_calibration_btn', 'normal')
    
    def capture_position(self):
        """捕获当前位置"""
        self.app.calibration_workflow.capture_position()
    
    def pause_calibration(self):
        """暂停/继续校准"""
        workflow = self.app.calibration_workflow
        btn = self.app.ui_manager.widgets.get('cal_pause_calibration_btn')
        
        if workflow.is_paused:
            workflow.resume()
            if btn:
                btn.config(text="Pause")
        else:
            workflow.pause()
            if btn:
                btn.config(text="Resume")
    
    def reset_calibration(self):
        """重置校准"""
        self.app.calibration_workflow.reset()
        if self.app.ui_manager:
            self.app.ui_manager.reset_calibration_display()
    
    def finish_calibration(self):
        """完成校准"""
        self.app.calibration_workflow.finish_calibration()
    
    def generate_calibration_commands(self):
        """生成校准命令并显示在命令文本框中"""
        commands = self.app.calibration_workflow.generate_calibration_commands()
        if not commands:
            self.app.log_message("Error: No calibration parameters available. Please complete calibration first.")
            return
        
        # 显示在命令文本框中
        if hasattr(self.app, 'cmd_text') and self.app.cmd_text:
            self.app.cmd_text.delete(1.0, "end")
            for cmd in commands:
                self.app.cmd_text.insert("end", cmd + "\n")
        
        self.app.log_message(f"Generated {len(commands)} calibration commands")
    
    def send_all_commands(self):
        """发送所有命令到设备"""
        commands = self.app.calibration_workflow.generate_calibration_commands()
        if not commands:
            self.app.log_message("Error: No commands to send. Please complete calibration first.")
            return
        
        if not self.app.serial_manager or not self.app.serial_manager.is_connected:
            self.app.log_message("Error: Not connected to device")
            return
        
        thread = threading.Thread(
            target=self.send_commands_thread,
            args=(commands,),
            daemon=True
        )
        thread.start()
    
    def send_commands_thread(self, commands):
        """在后台线程发送命令"""
        for cmd in commands:
            try:
                # 使用 serial_manager 的 send_line 方法（线程安全）
                success, error = self.app.serial_manager.send_line(cmd)
                if not success:
                    self.app.log_message(f"Error sending command '{cmd}': {error}")
                    return
                time.sleep(0.2)  # 增加延迟确保设备处理完成
            except Exception as e:
                self.app.log_message(f"Error sending command: {e}")
                return
        self.app.log_message(f"Sent {len(commands)} calibration commands to device")
    
    def resend_all_commands(self):
        """重新发送所有命令"""
        self.send_all_commands()
    
    def save_calibration_parameters(self):
        """保存校准参数到文件"""
        params = self.app.calibration_workflow.calibration_params
        if not params:
            self.app.log_message("Error: No calibration parameters to save. Please complete calibration first.")
            return
        
        from tkinter import filedialog
        from datetime import datetime
        import json
        
        # 构建默认文件名
        default_name = f"calibration_params_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 弹出保存对话框
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save Calibration Parameters",
        )
        
        if not filename:
            self.app.log_message("Save cancelled")
            return
        
        # 构建保存数据
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "calibration_params": params,
        }
        
        # 保存到文件
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            self.app.log_message(f"Calibration parameters saved to: {filename}")
        except Exception as e:
            self.app.log_message(f"Error saving calibration parameters: {e}")
    
    def load_calibration_parameters(self):
        """加载校准参数从文件"""
        from tkinter import filedialog
        import json
        
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Calibration Parameters",
        )
        
        if not filename:
            self.app.log_message("Load cancelled")
            return
        
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            params = data.get("calibration_params")
            if not params:
                self.app.log_message("Error: Invalid calibration file format")
                return
            
            # 设置到校准工作流
            self.app.calibration_workflow._calibration_params = params
            
            # 显示在命令文本框中
            self.generate_calibration_commands()
            
            self.app.log_message(f"Calibration parameters loaded from: {filename}")
        except Exception as e:
            self.app.log_message(f"Error loading calibration parameters: {e}")
    
    def read_calibration_params(self):
        """读取校准参数"""
        self.app.read_device_info()
    
    def check_calibration_status(self):
        """检查校准状态"""
        self.app.update_calibration_status_display()


class ActivationCallbacks(CallbackGroup):
    """传感器激活相关回调"""
    
    CALLBACK_NAMES = [
        'ask_read_properties', 'read_sensor_properties', 'read_device_info',
        'activate_sensor', 'verify_activation', 'verify_activation_status',
        'copy_activation_key',
    ]
    
    def register_all(self) -> Dict[str, callable]:
        return {
            'ask_read_properties': self.ask_read_properties,
            'read_sensor_properties': self.read_sensor_properties,
            'read_device_info': self.read_device_info,
            'activate_sensor': self.activate_sensor,
            'verify_activation': self.verify_activation,
            'verify_activation_status': self.verify_activation_status,
            'copy_activation_key': self.copy_activation_key,
        }
    
    def ask_read_properties(self):
        """询问并读取传感器属性"""
        self.app.read_sensor_properties()
    
    def read_sensor_properties(self):
        """读取传感器属性"""
        self.app.read_sensor_properties()
    
    def read_device_info(self):
        """读取设备信息"""
        self.app.read_device_info()
    
    def activate_sensor(self):
        """激活传感器"""
        self.app.activation_workflow.activate_sensor()
    
    def verify_activation(self):
        """验证激活"""
        self.app.activation_workflow.verify_activation()
    
    def verify_activation_status(self):
        """验证激活状态"""
        self.app.verify_activation_status()
    
    def copy_activation_key(self):
        """复制激活密钥"""
        self.app.copy_activation_key()


class NetworkCallbacks(CallbackGroup):
    """网络配置相关回调"""
    
    CALLBACK_NAMES = [
        'set_wifi_config', 'read_wifi_config', 'set_mqtt_config', 'read_mqtt_config',
        'set_ota_config', 'read_ota_config', 'set_alarm_threshold',
        'set_aliyun_mqtt_config', 'set_mqtt_local_mode', 'set_mqtt_aliyun_mode',
        'set_position_config', 'set_install_mode',
    ]
    
    def register_all(self) -> Dict[str, callable]:
        return {
            'set_wifi_config': self.set_wifi_config,
            'read_wifi_config': self.read_wifi_config,
            'set_mqtt_config': self.set_mqtt_config,
            'read_mqtt_config': self.read_mqtt_config,
            'set_ota_config': self.set_ota_config,
            'read_ota_config': self.read_ota_config,
            'set_alarm_threshold': self.set_alarm_threshold,
            'set_aliyun_mqtt_config': self.set_aliyun_mqtt_config,
            'set_mqtt_local_mode': self.set_mqtt_local_mode,
            'set_mqtt_aliyun_mode': self.set_mqtt_aliyun_mode,
            'set_position_config': self.set_position_config,
            'set_install_mode': self.set_install_mode,
        }
    
    def set_wifi_config(self):
        """设置 WiFi 配置 - 从 UI 获取参数"""
        ssid = self.app.ui_manager.get_entry_value('ssid')
        password = self.app.ui_manager.get_entry_value('password')
        
        if not ssid:
            self.app.log_message("Error: WiFi SSID cannot be empty!")
            return
        
        self.app.network_manager.set_wifi_config(ssid, password)
    
    def read_wifi_config(self):
        """读取 WiFi 配置"""
        self.app.network_manager.read_wifi_config()
    
    def set_mqtt_config(self):
        """设置 MQTT 配置 - 从 UI 获取参数"""
        broker = self.app.ui_manager.get_entry_value('mqtt_broker')
        username = self.app.ui_manager.get_entry_value('mqtt_user')
        password = self.app.ui_manager.get_entry_value('mqtt_password')
        port = self.app.ui_manager.get_entry_value('mqtt_port')
        
        if not broker:
            self.app.log_message("Error: MQTT broker cannot be empty!")
            return
        
        self.app.network_manager.set_mqtt_config(broker, username, password, port)
    
    def read_mqtt_config(self):
        """读取 MQTT 配置"""
        self.app.network_manager.read_mqtt_config()
    
    def set_ota_config(self):
        """设置 OTA 配置 - 从 UI 获取参数"""
        url1 = self.app.ui_manager.get_entry_value('url1')
        url2 = self.app.ui_manager.get_entry_value('url2')
        url3 = self.app.ui_manager.get_entry_value('url3')
        url4 = self.app.ui_manager.get_entry_value('url4')
        
        self.app.network_manager.set_ota_config(url1, url2, url3, url4)
    
    def read_ota_config(self):
        """读取 OTA 配置"""
        self.app.network_manager.read_ota_config()
    
    def set_alarm_threshold(self):
        """设置报警阈值 - 从 UI 获取参数"""
        # TODO: 添加报警阈值输入框到 UI
        self.app.log_message("Alarm threshold configuration not yet implemented in UI")
    
    def set_aliyun_mqtt_config(self):
        """设置阿里云 MQTT - 从 UI 获取参数"""
        product_key = self.app.ui_manager.get_entry_value('aliyun_product_key')
        device_name = self.app.ui_manager.get_entry_value('aliyun_device_name')
        device_secret = self.app.ui_manager.get_entry_value('aliyun_device_secret')
        
        if not all([product_key, device_name, device_secret]):
            self.app.log_message("Error: Aliyun MQTT requires ProductKey, DeviceName, and DeviceSecret!")
            return
        
        self.app.network_manager.set_aliyun_mqtt_config(product_key, device_name, device_secret)
    
    def set_mqtt_local_mode(self):
        """设置 MQTT 本地模式"""
        self.app.network_manager.set_mqtt_mode(1)
    
    def set_mqtt_aliyun_mode(self):
        """设置 MQTT 阿里云模式"""
        self.app.network_manager.set_mqtt_mode(10)
    
    def set_position_config(self):
        """设置位置配置 - 从 UI 获取参数"""
        region = self.app.ui_manager.get_entry_value('position_region')
        building = self.app.ui_manager.get_entry_value('position_building')
        user_attr = self.app.ui_manager.get_entry_value('position_user_attr')
        device_name = self.app.ui_manager.get_entry_value('position_device_name')
        
        self.app.network_manager.set_position_config(region, building, user_attr, device_name)
    
    def set_install_mode(self):
        """设置安装模式 - 从 UI 获取参数"""
        mode_str = self.app.ui_manager.get_entry_value('install_mode')
        
        # 从字符串中提取数字（如 "0 - Default" -> 0）
        try:
            mode = int(mode_str.split('-')[0].strip())
            self.app.network_manager.set_install_mode(mode)
        except (ValueError, AttributeError):
            self.app.log_message(f"Error: Invalid install mode value: {mode_str}")


class SystemCallbacks(CallbackGroup):
    """系统控制相关回调"""
    
    CALLBACK_NAMES = [
        'restart_sensor', 'save_config', 'reset_ui_with_confirmation',
        'save_sensor_config', 'restore_default_config',
        'deactivate_sensor', 'set_kalman_filter', 'set_filter_on', 'set_filter_off',
        'set_gyro_levels', 'set_accel_levels', 'set_voltage_scales',
        'set_temp_offset', 'set_mag_offsets', 'start_cpu_monitor',
        'start_sensor_calibration', 'trigger_buzzer', 'check_upgrade',
        'enter_ap_mode', 'set_local_coordinate_mode', 'set_global_coordinate_mode',
    ]
    
    def register_all(self) -> Dict[str, callable]:
        return {
            'restart_sensor': self.restart_sensor,
            'save_config': self.save_config,
            'reset_ui_with_confirmation': self.reset_ui_with_confirmation,
            'save_sensor_config': self.save_sensor_config,
            'restore_default_config': self.restore_default_config,
            'deactivate_sensor': self.deactivate_sensor,
            'set_kalman_filter': self.set_kalman_filter,
            'set_filter_on': self.set_filter_on,
            'set_filter_off': self.set_filter_off,
            'set_gyro_levels': self.set_gyro_levels,
            'set_accel_levels': self.set_accel_levels,
            'set_voltage_scales': self.set_voltage_scales,
            'set_temp_offset': self.set_temp_offset,
            'set_mag_offsets': self.set_mag_offsets,
            'start_cpu_monitor': self.start_cpu_monitor,
            'start_sensor_calibration': self.start_sensor_calibration,
            'trigger_buzzer': self.trigger_buzzer,
            'check_upgrade': self.check_upgrade,
            'enter_ap_mode': self.enter_ap_mode,
            'set_local_coordinate_mode': self.set_local_coordinate_mode,
            'set_global_coordinate_mode': self.set_global_coordinate_mode,
        }
    
    def restart_sensor(self):
        """重启传感器"""
        self.app.network_manager.restart_sensor()
    
    def save_config(self):
        """保存配置"""
        self.app.network_manager.save_config()
    
    def reset_ui_with_confirmation(self):
        """带确认的重置 UI"""
        self.app.reset_ui_with_confirmation()
    
    def save_sensor_config(self):
        """保存传感器配置"""
        self.app.network_manager.save_sensor_config()
    
    def restore_default_config(self):
        """恢复默认配置"""
        self.app.network_manager.restore_default_config()
    
    def deactivate_sensor(self):
        """停用传感器"""
        self.app.network_manager.deactivate_sensor()
    
    def set_kalman_filter(self):
        """设置卡尔曼滤波 - 从 UI 获取 Q/R 值"""
        try:
            q_var = self.app.ui_manager.vars.get('kf_q')
            r_var = self.app.ui_manager.vars.get('kf_r')
            
            q = float(q_var.get() if q_var else '0.005')
            r = float(r_var.get() if r_var else '15')
            
            self.app.network_manager.set_kalman_filter(q, r)
        except ValueError as e:
            self.app.log_message(f"Error: Invalid Kalman filter parameters: {e}")
    
    def set_filter_on(self):
        """开启滤波"""
        self.app.network_manager.set_filter_on()
    
    def set_filter_off(self):
        """关闭滤波"""
        self.app.network_manager.set_filter_off()
    
    def set_gyro_levels(self):
        """设置陀螺仪报警等级 - 从 UI 获取5个等级值"""
        try:
            levels = []
            for i in range(1, 6):
                var = self.app.ui_manager.vars.get(f'gyro_level{i}')
                if var:
                    val = float(var.get())
                    levels.append(val)
            
            if len(levels) == 5:
                self.app.network_manager.set_gyro_levels(*levels)
            else:
                self.app.log_message("Error: Could not read all gyro level values")
        except ValueError as e:
            self.app.log_message(f"Error: Invalid gyro level parameters: {e}")
    
    def set_accel_levels(self):
        """设置加速度报警等级 - 从 UI 获取5个等级值"""
        try:
            levels = []
            for i in range(1, 6):
                var = self.app.ui_manager.vars.get(f'accel_level{i}')
                if var:
                    val = float(var.get())
                    levels.append(val)
            
            if len(levels) == 5:
                self.app.network_manager.set_accel_levels(*levels)
            else:
                self.app.log_message("Error: Could not read all accel level values")
        except ValueError as e:
            self.app.log_message(f"Error: Invalid accel level parameters: {e}")
    
    def set_voltage_scales(self):
        """设置电压量程 - 从 UI 获取两个电压比例"""
        try:
            v1_var = self.app.ui_manager.vars.get('vks_v1')
            v2_var = self.app.ui_manager.vars.get('vks_v2')
            
            scale1 = float(v1_var.get() if v1_var else '1.0')
            scale2 = float(v2_var.get() if v2_var else '1.0')
            
            self.app.network_manager.set_voltage_scales(scale1, scale2)
        except ValueError as e:
            self.app.log_message(f"Error: Invalid voltage scale parameters: {e}")
    
    def set_temp_offset(self):
        """设置温度偏移 - 从 UI 获取偏移值"""
        try:
            tme_var = self.app.ui_manager.vars.get('tme_offset')
            offset = float(tme_var.get() if tme_var else '0.0')
            
            self.app.network_manager.set_temp_offset(offset)
        except ValueError as e:
            self.app.log_message(f"Error: Invalid temperature offset: {e}")
    
    def set_mag_offsets(self):
        """设置磁力计偏移 - 从 UI 获取 XYZ 值"""
        try:
            x_var = self.app.ui_manager.vars.get('magof_x')
            y_var = self.app.ui_manager.vars.get('magof_y')
            z_var = self.app.ui_manager.vars.get('magof_z')
            
            x = float(x_var.get() if x_var else '0.0')
            y = float(y_var.get() if y_var else '0.0')
            z = float(z_var.get() if z_var else '0.0')
            
            self.app.network_manager.set_mag_offsets(x, y, z)
        except ValueError as e:
            self.app.log_message(f"Error: Invalid magnetometer offset parameters: {e}")
    
    def start_cpu_monitor(self):
        """启动 CPU 监控"""
        self.app.network_manager.start_cpu_monitor()
    
    def start_sensor_calibration(self):
        """启动传感器校准"""
        self.app.network_manager.start_sensor_calibration()
    
    def trigger_buzzer(self):
        """触发蜂鸣器"""
        self.app.network_manager.trigger_buzzer()
    
    def check_upgrade(self):
        """检查升级"""
        self.app.network_manager.check_upgrade()
    
    def enter_ap_mode(self):
        """进入 AP 模式"""
        self.app.network_manager.enter_ap_mode()
    
    def set_local_coordinate_mode(self):
        """设置局部坐标模式"""
        self.app.network_manager.set_local_coordinate_mode()
    
    def set_global_coordinate_mode(self):
        """设置全局坐标模式"""
        self.app.network_manager.set_global_coordinate_mode()


class CameraCallbacks(CallbackGroup):
    """相机控制相关回调"""
    
    CALLBACK_NAMES = [
        'set_camera_photo_mode_on', 'set_camera_photo_mode_off',
        'set_monitoring_mode_on', 'set_monitoring_mode_off',
        'set_timelapse_mode_on', 'set_timelapse_mode_off',
        'take_photo', 'reboot_camera_slave', 'reboot_camera_module',
        'toggle_camera_stream', 'toggle_push_stream',
        'force_camera_ota', 'force_esp32_ota',
    ]
    
    def register_all(self) -> Dict[str, callable]:
        return {
            'set_camera_photo_mode_on': self.set_camera_photo_mode_on,
            'set_camera_photo_mode_off': self.set_camera_photo_mode_off,
            'set_monitoring_mode_on': self.set_monitoring_mode_on,
            'set_monitoring_mode_off': self.set_monitoring_mode_off,
            'set_timelapse_mode_on': self.set_timelapse_mode_on,
            'set_timelapse_mode_off': self.set_timelapse_mode_off,
            'take_photo': self.take_photo,
            'reboot_camera_slave': self.reboot_camera_slave,
            'reboot_camera_module': self.reboot_camera_module,
            'toggle_camera_stream': self.toggle_camera_stream,
            'toggle_push_stream': self.toggle_push_stream,
            'force_camera_ota': self.force_camera_ota,
            'force_esp32_ota': self.force_esp32_ota,
        }
    
    def set_camera_photo_mode_on(self):
        """开启相机拍照模式"""
        self.app.camera_manager.set_photo_mode_on()
    
    def set_camera_photo_mode_off(self):
        """关闭相机拍照模式"""
        self.app.camera_manager.set_photo_mode_off()
    
    def set_monitoring_mode_on(self):
        """开启监控模式"""
        self.app.camera_manager.set_monitoring_mode_on()
    
    def set_monitoring_mode_off(self):
        """关闭监控模式"""
        self.app.camera_manager.set_monitoring_mode_off()
    
    def set_timelapse_mode_on(self):
        """开启延时模式"""
        self.app.camera_manager.set_timelapse_mode_on()
    
    def set_timelapse_mode_off(self):
        """关闭延时模式"""
        self.app.camera_manager.set_timelapse_mode_off()
    
    def take_photo(self):
        """拍照"""
        self.app.camera_manager.take_photo()
    
    def reboot_camera_slave(self):
        """重启相机从机"""
        self.app.camera_manager.reboot_camera_slave()
    
    def reboot_camera_module(self):
        """重启相机模块"""
        self.app.camera_manager.reboot_camera_module()
    
    def toggle_camera_stream(self):
        """切换相机流"""
        self.app.camera_manager.toggle_camera_stream()
    
    def toggle_push_stream(self):
        """切换推流"""
        self.app.camera_manager.toggle_push_stream()
    
    def force_camera_ota(self):
        """强制相机 OTA"""
        self.app.camera_manager.force_camera_ota()
    
    def force_esp32_ota(self):
        """强制 ESP32 OTA"""
        self.app.camera_manager.force_esp32_ota()


class CallbackRegistry:
    """
    回调注册表 - 统一管理和访问所有回调
    
    用法:
        registry = CallbackRegistry(app)
        callbacks = registry.get_all_callbacks()
    """
    
    GROUPS = [
        SerialCallbacks,
        DataStreamCallbacks,
        CalibrationCallbacks,
        ActivationCallbacks,
        NetworkCallbacks,
        SystemCallbacks,
        CameraCallbacks,
    ]
    
    def __init__(self, app: "SensorCalibratorApp"):
        self.app = app
        self._groups: Dict[str, CallbackGroup] = {}
        self._callbacks: Dict[str, callable] = {}
        self._register_all()
    
    def _register_all(self):
        """注册所有回调组"""
        for group_class in self.GROUPS:
            group_name = group_class.__name__.replace('Callbacks', '').lower()
            group = group_class(self.app)
            self._groups[group_name] = group
            
            # 将组作为属性访问
            setattr(self, group_name, group)
            
            # 合并到总回调字典
            group_callbacks = group.register_all()
            self._callbacks.update(group_callbacks)
    
    def get_all_callbacks(self) -> Dict[str, callable]:
        """获取所有回调函数的字典"""
        return self._callbacks.copy()
    
    def get(self, name: str, default=None):
        """获取单个回调"""
        return self._callbacks.get(name, default)
    
    def __getitem__(self, name: str):
        """支持 registry['callback_name'] 语法"""
        return self._callbacks[name]
    
    def __contains__(self, name: str) -> bool:
        """支持 'callback_name' in registry 语法"""
        return name in self._callbacks
