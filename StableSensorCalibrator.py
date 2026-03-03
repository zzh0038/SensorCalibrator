import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import queue
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, scrolledtext, StringVar, messagebox, filedialog
import json
import os
from datetime import datetime
import hashlib
import secrets
import re
import matplotlib
import atexit
from collections import deque
from typing import Optional

# Import configuration
from sensor_calibrator import Config, UIConfig, CalibrationConfig, SerialConfig, ChartManager, UIManager, DataProcessor, SerialManager, NetworkManager, CalibrationWorkflow, ActivationWorkflow

matplotlib.use("TkAgg")

# 配置matplotlib
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


class StableSensorCalibrator:
    """
    MPU6050 & ADXL355 传感器校准应用程序主类。
    
    提供串口通信、数据采集可视化、六位置校准、
    激活验证和网络配置等功能。
    
    Attributes:
        data_processor: 数据处理器，管理传感器数据解析和统计
        calibration_params: 校准参数字典
        sensor_properties: 传感器属性字典
        is_connected: 串口连接状态
        is_calibrating: 校准状态标志
    """
    
    def __init__(self):
        """初始化应用程序状态和所有组件。"""
        # 初始化所有变量...
        self.ser = None
        self.is_reading = False
        self.data_queue = queue.Queue(maxsize=Config.MAX_QUEUE_SIZE)
        self.update_interval = Config.UPDATE_INTERVAL_MS

        # 数据处理器（替代原有的数据存储）
        self.data_processor = DataProcessor()
        
        # 保持向后兼容的引用
        self._setup_data_references()

        # 统计数据
        self.serial_freq = 0
        self.last_freq_update = time.time()
        self.packets_received = 0
        
        # 统计信息存储（从data_processor同步）
        self.stats_window_size = Config.STATS_WINDOW_SIZE
        self.real_time_stats = self.data_processor.get_statistics()

        # 传感器属性存储
        self.sensor_properties = {}
        self.mac_address = None
        self.generated_key = None
        self.sensor_activated = False

        # 监控状态
        self.is_monitoring = False
        self.monitoring_position = 0
        self.monitoring_data = []
        self.monitoring_duration = Config.MONITORING_DURATION
        self.monitoring_samples_needed = Config.MONITORING_SAMPLES_NEEDED

        # 校准状态
        self.is_calibrating = False
        self.current_position = 0
        self.calibration_positions = []
        self.calibration_samples = Config.CALIBRATION_SAMPLES

        # 校准参数
        self.calibration_params = {
            "mpu_accel_scale": [1.0, 1.0, 1.0],
            "mpu_accel_offset": [0.0, 0.0, 0.0],
            "adxl_accel_scale": [1.0, 1.0, 1.0],
            "adxl_accel_offset": [0.0, 0.0, 0.0],
            "mpu_gyro_offset": [0.0, 0.0, 0.0],
        }

        # 位置定义
        self.position_names = CalibrationConfig.POSITION_NAMES

        # 新增：WiFi和MQTT参数存储
        self.wifi_params = {"ssid": "", "password": ""}
        self.mqtt_params = {
            "broker": "",
            "username": "",
            "password": "",
            "port": "1883",
        }
        self.ota_params = {
            "URL1": "",
            "URL2": "",
            "URL3": "",
            "URL4": "1883",
        }

        # 文件路径
        self.calibration_file = Config.DEFAULT_CALIBRATION_FILE
        self.properties_file = Config.DEFAULT_PROPERTIES_FILE

        # 新增：退出标志
        self.exiting = False

        # 新增：after任务ID存储
        self.after_tasks = []

        # 新增：性能优化相关变量
        self.last_stats_update = 0
        self.stats_update_interval = Config.STATS_UPDATE_INTERVAL   # 统计信息更新间隔（秒）
        
        # 窗口移动检测相关变量
        self._window_moving = False
        self._window_move_timer = None
        self._last_window_pos = None
        self._window_configure_count = 0
        
        # 图表管理器（在setup_gui中初始化）
        self.chart_manager = None

        # 设置GUI
        self.setup_gui()

    def setup_gui(self):
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        self.root = tk.Tk()
        self.root.tk.call("tk", "scaling", UIConfig.SCALING_FACTOR)
        self.root.title(UIConfig.TITLE)
        self.root.geometry(f"{UIConfig.WINDOW_WIDTH}x{UIConfig.WINDOW_HEIGHT}")  # 初始窗口尺寸

        # 设置窗口关闭协议
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        atexit.register(self.cleanup)
        
        # 绑定窗口移动/调整大小事件（性能优化）
        if Config.ENABLE_WINDOW_MOVE_PAUSE:
            self.root.bind("<Configure>", self._on_window_configure)
            self._last_window_pos = (self.root.winfo_x(), self.root.winfo_y())

        # 设置窗口图标
        try:
            self.root.iconbitmap(default="icon.ico")
        except:
            pass

        # 配置网格权重 - 关键修改：调整列权重比例
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=0)  # 左侧面板固定宽度
        self.root.grid_columnconfigure(1, weight=1)  # 右侧图表区域可扩展

        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 配置主框架网格 - 修正权重分配
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)  # 左侧面板不扩展
        main_frame.grid_columnconfigure(1, weight=2)  # 右侧图表区域占据更多空间

        # ========== 左侧控制面板 ==========
        # 设置固定宽度并允许垂直扩展
        left_panel = ttk.Frame(main_frame, width=UIConfig.LEFT_PANEL_WIDTH)  # 设置宽度
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        # left_panel.grid_propagate(False)  # 禁止自动调整大小

        # 配置左侧面板网格
        left_panel.grid_rowconfigure(0, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # 创建可滚动的左侧面板
        canvas = tk.Canvas(left_panel, highlightthickness=0, width=UIConfig.LEFT_PANEL_WIDTH)  # 设置画布宽度
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, width=UIConfig.LEFT_PANEL_WIDTH)  # 设置滚动框架宽度

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=430)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # 使用grid布局而不是pack，确保正确填充
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 配置画布网格权重
        # left_panel.grid_rowconfigure(0, weight=1)
        # left_panel.grid_columnconfigure(0, weight=1)
        # left_panel.grid_columnconfigure(1, weight=0)

        # 左侧面板内容 - 使用 UIManager
        self.ui_callbacks = {
            'refresh_ports': self.refresh_ports,
            'toggle_connection': self.toggle_connection,
            'toggle_data_stream': self.toggle_data_stream,
            'toggle_data_stream2': self.toggle_data_stream2,
            'start_calibration': self.start_calibration,
            'capture_position': self.capture_position,
            'send_all_commands': self.send_all_commands,
            'save_calibration_parameters': self.save_calibration_parameters,
            'read_properties': self.read_sensor_properties,
            'resend_all_commands': self.resend_all_commands,
            'set_local_coordinate_mode': self.set_local_coordinate_mode,
            'set_global_coordinate_mode': self.set_global_coordinate_mode,
            'activate_sensor': self.activate_sensor,
            'verify_activation': self.verify_activation,
            'set_wifi_config': self.set_wifi_config,
            'read_wifi_config': self.read_wifi_config,
            'set_mqtt_config': self.set_mqtt_config,
            'read_mqtt_config': self.read_mqtt_config,
            'set_ota_config': self.set_ota_config,
            'read_ota_config': self.read_ota_config,
            # Alarm & Device 回调
            'set_alarm_threshold': self.set_alarm_threshold,
            'restart_sensor': self.restart_sensor,
            'save_config': self.save_config,
            # Activation 回调
            'copy_activation_key': self.copy_activation_key,
        }
        self.ui_manager = UIManager(scrollable_frame, self.ui_callbacks)
        
        # 保持对旧变量的引用（兼容性）
        self._setup_ui_references()

        # ========== 右侧图表区域 ==========
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # 创建图表管理器
        self.chart_manager = ChartManager(right_panel)
        self.chart_manager.setup_plots()
        self.canvas = self.chart_manager.get_canvas()
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # ========== 底部输出区域 ==========
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(5, 0))
        bottom_frame.grid_rowconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        # 日志输出
        log_frame = ttk.LabelFrame(bottom_frame, text="Log Output", padding="5")
        log_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=8, font=("Courier", 9)  # 增加高度
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # 校准命令
        cmd_frame = ttk.LabelFrame(
            bottom_frame, text="Calibration Commands", padding="5"
        )
        cmd_frame.grid(row=0, column=1, sticky="nsew")
        cmd_frame.grid_rowconfigure(0, weight=1)
        cmd_frame.grid_columnconfigure(0, weight=1)

        self.cmd_text = scrolledtext.ScrolledText(
            cmd_frame, height=8, font=("Courier", 9)  # 增加高度
        )
        self.cmd_text.grid(row=0, column=0, sticky="nsew")

        # 刷新端口列表
        self.refresh_ports()

        # 启动GUI更新循环
        self.schedule_update_gui()

    def _setup_data_references(self):
        """设置数据引用，保持与旧代码的兼容性"""
        # 直接引用DataProcessor的数据缓冲区
        self.time_data = self.data_processor.time_data
        self.mpu_accel_data = self.data_processor.mpu_accel_data
        self.mpu_gyro_data = self.data_processor.mpu_gyro_data
        self.adxl_accel_data = self.data_processor.adxl_accel_data
        self.gravity_mag_data = self.data_processor.gravity_mag_data
        
        # 时间跟踪
        self.data_start_time = self.data_processor.data_start_time
        self.packet_count = self.data_processor.packet_count
        self.expected_frequency = self.data_processor.expected_frequency

    def _setup_ui_references(self):
        """设置UI引用，保持与旧代码的兼容性"""
        # 串口相关
        self.port_var = self.ui_manager.get_var('port')
        self.port_combo = self.ui_manager.get_widget('port_combo')
        self.refresh_btn = self.ui_manager.get_widget('refresh_btn')
        self.baud_var = self.ui_manager.get_var('baud')
        self.connect_btn = self.ui_manager.get_widget('connect_btn')
        
        # 数据流相关
        self.data_btn = self.ui_manager.get_widget('data_btn')
        self.data_btn2 = self.ui_manager.get_widget('data_btn2')
        self.freq_var = self.ui_manager.get_var('freq')
        
        # 校准相关
        self.calibrate_btn = self.ui_manager.get_widget('calibrate_btn')
        self.capture_btn = self.ui_manager.get_widget('capture_btn')
        self.position_label = self.ui_manager.get_widget('position_label')
        
        # 状态相关
        self.status_var = self.ui_manager.get_var('status')
        self.status_label = self.ui_manager.get_widget('status_label')
        
        # 命令相关
        self.send_btn = self.ui_manager.get_widget('send_btn')
        self.save_btn = self.ui_manager.get_widget('save_btn')
        self.read_props_btn = self.ui_manager.get_widget('read_props_btn')
        self.resend_btn = self.ui_manager.get_widget('resend_btn')
        
        # 坐标模式相关
        self.local_coord_btn = self.ui_manager.get_widget('local_coord_btn')
        self.global_coord_btn = self.ui_manager.get_widget('global_coord_btn')
        
        # 激活相关
        self.activate_btn = self.ui_manager.get_widget('activate_btn')
        self.verify_btn = self.ui_manager.get_widget('verify_btn')
        
        # WiFi相关
        self.ssid_var = self.ui_manager.get_var('ssid')
        self.password_var = self.ui_manager.get_var('password')
        self.set_wifi_btn = self.ui_manager.get_widget('set_wifi_btn')
        self.read_wifi_btn = self.ui_manager.get_widget('read_wifi_btn')
        
        # MQTT相关
        self.mqtt_broker_var = self.ui_manager.get_var('mqtt_broker')
        self.mqtt_user_var = self.ui_manager.get_var('mqtt_user')
        self.mqtt_password_var = self.ui_manager.get_var('mqtt_password')
        self.mqtt_port_var = self.ui_manager.get_var('mqtt_port')
        self.set_mqtt_btn = self.ui_manager.get_widget('set_mqtt_btn')
        self.read_mqtt_btn = self.ui_manager.get_widget('read_mqtt_btn')
        
        # OTA相关
        self.URL1_var = self.ui_manager.get_var('url1')
        self.URL2_var = self.ui_manager.get_var('url2')
        self.URL3_var = self.ui_manager.get_var('url3')
        self.URL4_var = self.ui_manager.get_var('url4')
        self.set_ota_btn = self.ui_manager.get_widget('set_ota_btn')
        self.read_ota_btn = self.ui_manager.get_widget('read_ota_btn')
        
        # 统计标签
        self.stats_labels = {
            'mpu_accel_x_mean': self.ui_manager.get_var('mpu_accel_x_mean'),
            'mpu_accel_x_std': self.ui_manager.get_var('mpu_accel_x_std'),
            'mpu_accel_y_mean': self.ui_manager.get_var('mpu_accel_y_mean'),
            'mpu_accel_y_std': self.ui_manager.get_var('mpu_accel_y_std'),
            'mpu_accel_z_mean': self.ui_manager.get_var('mpu_accel_z_mean'),
            'mpu_accel_z_std': self.ui_manager.get_var('mpu_accel_z_std'),
            'adxl_accel_x_mean': self.ui_manager.get_var('adxl_accel_x_mean'),
            'adxl_accel_x_std': self.ui_manager.get_var('adxl_accel_x_std'),
            'adxl_accel_y_mean': self.ui_manager.get_var('adxl_accel_y_mean'),
            'adxl_accel_y_std': self.ui_manager.get_var('adxl_accel_y_std'),
            'adxl_accel_z_mean': self.ui_manager.get_var('adxl_accel_z_mean'),
            'adxl_accel_z_std': self.ui_manager.get_var('adxl_accel_z_std'),
            'mpu_gyro_x_mean': self.ui_manager.get_var('mpu_gyro_x_mean'),
            'mpu_gyro_x_std': self.ui_manager.get_var('mpu_gyro_x_std'),
            'mpu_gyro_y_mean': self.ui_manager.get_var('mpu_gyro_y_mean'),
            'mpu_gyro_y_std': self.ui_manager.get_var('mpu_gyro_y_std'),
            'mpu_gyro_z_mean': self.ui_manager.get_var('mpu_gyro_z_mean'),
            'mpu_gyro_z_std': self.ui_manager.get_var('mpu_gyro_z_std'),
            'gravity_mean': self.ui_manager.get_var('gravity_mean'),
            'gravity_std': self.ui_manager.get_var('gravity_std'),
        }

        # 初始化串口管理器
        self._init_serial_manager()
        
        # 初始化网络管理器
        self._init_network_manager()
        
        # 初始化校准工作流
        self._init_calibration_workflow()
        
        # 初始化激活工作流
        self._init_activation_workflow()

    def _init_calibration_workflow(self):
        """初始化校准工作流"""
        callbacks = {
            'log_message': self.log_message,
            'parse_sensor_data': self.parse_sensor_data,
            'on_position_captured': self._on_position_captured,
            'on_calibration_finished': self._on_calibration_finished,
            'on_calibration_error': self._on_calibration_error,
            'on_capture_error': self._on_capture_error,
        }
        self.calibration_workflow = CalibrationWorkflow(self.data_queue, callbacks)
    
    def _on_position_captured(self, next_position: int):
        """位置采集完成回调"""
        self.current_position = next_position
        self.capture_btn.config(state="normal")
        self.update_position_display()
    
    def _on_calibration_finished(self, params: dict):
        """校准完成回调"""
        self.calibration_params = params
        self.calibrate_btn.config(state="normal")
        self.capture_btn.config(state="disabled")
        self.data_btn.config(state="normal")
        self.position_label.config(text="Calibration complete!")
        self.log_message("Calibration finished successfully!")
    
    def _on_calibration_error(self):
        """校准错误回调"""
        self.reset_calibration_state()
    
    def _on_capture_error(self):
        """采集错误回调"""
        self.capture_btn.config(state="normal")
    
    def _init_activation_workflow(self):
        """初始化激活工作流"""
        callbacks = {
            'log_message': self.log_message,
            'get_serial_port': lambda: self.serial_manager.serial_port,
            'is_connected': lambda: self.serial_manager.is_connected,
            'is_reading': lambda: self.is_reading,
            'stop_data_stream': self.stop_data_stream,
            'start_data_stream': self.start_data_stream,
            'send_ss8_command': self.send_ss8_get_properties,
            'update_activation_status': self.update_activation_status,
        }
        self.activation_workflow = ActivationWorkflow(callbacks)

    def _init_network_manager(self):
        """初始化网络管理器"""
        callbacks = {
            'log_message': self.log_message,
            'read_sensor_properties': self.read_sensor_properties,
            'start_data_stream': self.start_data_stream,
            'stop_data_stream': self.stop_data_stream,
            'enable_config_buttons': self.enable_config_buttons,
            'on_wifi_loaded': self._on_wifi_config_loaded,
            'on_mqtt_loaded': self._on_mqtt_config_loaded,
        }
        self.network_manager = NetworkManager(self.serial_manager, callbacks)
        
        # 同步初始配置
        self.network_manager.wifi_params = self.wifi_params
        self.network_manager.mqtt_params = self.mqtt_params
        self.network_manager.ota_params = self.ota_params
    
    def _on_wifi_config_loaded(self, params: dict):
        """WiFi配置加载回调"""
        self.ssid_var.set(params.get('ssid', ''))
        self.password_var.set(params.get('password', ''))
        self.wifi_params = params
    
    def _on_mqtt_config_loaded(self, params: dict):
        """MQTT配置加载回调"""
        self.mqtt_broker_var.set(params.get('broker', ''))
        self.mqtt_user_var.set(params.get('username', ''))
        self.mqtt_password_var.set(params.get('password', ''))
        self.mqtt_port_var.set(params.get('port', '1883'))
        self.mqtt_params = params

    def _init_serial_manager(self):
        """初始化串口管理器"""
        callbacks = {
            'log_message': self.log_message,
            'get_data_queue': lambda: self.data_queue,
            'on_data_received': None,  # 可选：如果需要实时处理
            'update_connection_state': self._on_connection_state_changed,
        }
        self.serial_manager = SerialManager(callbacks)
        
        # 保持向后兼容的引用
        self.ser = None  # 将通过 serial_manager.serial_port 访问
    
    def _on_connection_state_changed(self, connected: bool):
        """串口连接状态变化回调"""
        # 更新按钮状态等
        if connected:
            self.ser = self.serial_manager.serial_port
        else:
            self.ser = None

    def schedule_update_gui(self):
        """调度GUI更新 - 安全版本"""
        if not self.exiting and hasattr(self, 'root') and self.root:
            try:
                if self.root.winfo_exists():
                    task_id = self.root.after(self.update_interval, self.update_gui)
                    self.after_tasks.append(task_id)
            except Exception:
                pass  # 窗口已关闭，忽略

    def on_closing(self):
        """窗口关闭事件处理"""
        response = messagebox.askyesno(
            "退出程序", "确定要退出程序吗？\n\n所有未保存的数据将丢失。"
        )

        if response:
            self.exiting = True
            self.cleanup()
            self.root.destroy()

    def cleanup(self):
        """清理资源，确保安全退出"""
        if hasattr(self, "_cleaned"):
            return

        self._cleaned = True
        self.log_message("正在清理资源，准备退出...")

        # 1. 取消所有after任务
        self.cancel_all_after_tasks()

        # 2. 停止数据流
        if hasattr(self, "is_reading") and self.is_reading:
            self.stop_data_stream_safe()

        # 3. 关闭串口
        if hasattr(self, "ser") and self.ser and self.ser.is_open:
            try:
                self.ser.close()
                self.log_message("串口已关闭")
            except Exception as e:
                self.log_message(f"关闭串口时出错: {str(e)}")

        # 4. 停止所有子线程
        self.stop_all_threads()

        # 5. 清理matplotlib资源
        if hasattr(self, "fig"):
            try:
                plt.close(self.fig)
            except:
                pass

        self.log_message("清理完成，程序即将退出")
        time.sleep(Config.SERIAL_CLEANUP_DELAY)  # 短暂延迟确保清理完成

    def cancel_all_after_tasks(self):
        """取消所有after任务"""
        for task_id in self.after_tasks:
            try:
                self.root.after_cancel(task_id)
            except:
                pass
        self.after_tasks.clear()
        
        # 取消窗口移动定时器
        if self._window_move_timer:
            try:
                self.root.after_cancel(self._window_move_timer)
            except:
                pass
            self._window_move_timer = None

    def _on_window_configure(self, event):
        """窗口移动/调整大小事件处理 - 性能优化"""
        if not hasattr(self, 'root') or not self.root:
            return
        
        # 检查窗口位置是否改变
        try:
            current_pos = (self.root.winfo_x(), self.root.winfo_y())
            if current_pos != self._last_window_pos:
                self._last_window_pos = current_pos
                self._window_moving = True
                self._window_configure_count += 1
                
                # 取消之前的定时器
                if self._window_move_timer:
                    try:
                        self.root.after_cancel(self._window_move_timer)
                    except:
                        pass
                
                # 设置新的定时器，延迟后恢复更新
                self._window_move_timer = self.root.after(
                    Config.WINDOW_MOVE_PAUSE_DELAY, 
                    self._on_window_move_end
                )
        except:
            pass
    
    def _on_window_move_end(self):
        """窗口移动结束后的处理"""
        self._window_moving = False
        self._window_move_timer = None
        self._window_configure_count = 0

    def stop_data_stream_safe(self):
        """安全停止数据流"""
        try:
            self.is_reading = False
            if hasattr(self, "ser") and self.ser and self.ser.is_open:
                self.send_ss0_start_stream()  # 静默停止

            if hasattr(self, "data_btn"):
                self.data_btn.config(text="Start Data Stream")
            if hasattr(self, "calibrate_btn"):
                self.calibrate_btn.config(state="disabled")
            if hasattr(self, "capture_btn"):
                self.capture_btn.config(state="disabled")

            self.log_message("数据流已停止")
        except Exception as e:
            self.log_message(f"停止数据流时出错: {str(e)}")

    def stop_all_threads(self):
        """停止所有活动的线程"""
        # 设置退出标志
        self.exiting = True

        # 等待串口读取线程结束
        if hasattr(self, "serial_thread") and self.serial_thread.is_alive():
            # 设置超时等待线程结束
            start_time = time.time()
            while (
                time.time() - start_time < 2.0
                and hasattr(self, "serial_thread")
                and self.serial_thread.is_alive()
            ):
                time.sleep(Config.THREAD_ERROR_DELAY)

        # 清除数据队列
        if hasattr(self, "data_queue"):
            try:
                while not self.data_queue.empty():
                    self.data_queue.get_nowait()
            except:
                pass

        # 清空数据缓冲区（支持deque）
        if hasattr(self, "time_data"):
            self.time_data.clear()
        if hasattr(self, "mpu_accel_data"):
            for d in self.mpu_accel_data:
                d.clear()
        if hasattr(self, "mpu_gyro_data"):
            for d in self.mpu_gyro_data:
                d.clear()
        if hasattr(self, "adxl_accel_data"):
            for d in self.adxl_accel_data:
                d.clear()
        if hasattr(self, "gravity_mag_data"):
            self.gravity_mag_data.clear()

    def set_wifi_config(self):
        """设置WiFi配置 - 委托给 NetworkManager"""
        ssid = self.ssid_var.get().strip()
        password = self.password_var.get().strip()
        
        if self.network_manager.set_wifi_config(ssid, password):
            self.wifi_params = {"ssid": ssid, "password": password}

    def set_ota_config(self):
        """设置OTA配置 - 委托给 NetworkManager"""
        url1 = self.URL1_var.get().strip()
        url2 = self.URL2_var.get().strip()
        url3 = self.URL3_var.get().strip()
        url4 = self.URL4_var.get().strip()
        
        if self.network_manager.set_ota_config(url1, url2, url3, url4):
            self.ota_params = {"URL1": url1, "URL2": url2, "URL3": url3, "URL4": url4}

    def set_mqtt_config(self):
        """设置MQTT配置 - 委托给 NetworkManager"""
        broker = self.mqtt_broker_var.get().strip()
        username = self.mqtt_user_var.get().strip()
        password = self.mqtt_password_var.get().strip()
        port = self.mqtt_port_var.get().strip()
        
        if self.network_manager.set_mqtt_config(broker, username, password, port):
            self.mqtt_params = {
                "broker": broker,
                "username": username,
                "password": password,
                "port": port or "1883",
            }

    def read_wifi_config(self):
        """读取WiFi配置 - 委托给 NetworkManager"""
        self.network_manager.read_wifi_config()

    def read_mqtt_config(self):
        """读取MQTT配置 - 委托给 NetworkManager"""
        self.network_manager.read_mqtt_config()

    def read_ota_config(self):
        """读取OTA配置 - 委托给 NetworkManager"""
        self.network_manager.read_ota_config()

    def set_coordinate_mode(self, mode: int, mode_name: str) -> None:
        """设置坐标模式

        Args:
            mode: 模式编号 (2=局部坐标, 3=整体坐标)
            mode_name: 模式名称（用于日志显示）
        """
        if mode == 2:
            self.serial_manager.send_ss2_local_mode(mode_name)
        elif mode == 3:
            self.serial_manager.send_ss3_global_mode(mode_name)
        else:
            self.serial_manager.send_ss_command(mode, mode_name)

    def set_local_coordinate_mode(self) -> None:
        """设置局部坐标模式 - 发送 SS:2 指令"""
        self.set_coordinate_mode(2, "Local Coordinate Mode")

    def set_global_coordinate_mode(self) -> None:
        """设置整体坐标模式 - 发送 SS:3 指令"""
        self.set_coordinate_mode(3, "Global Coordinate Mode")

    def send_ss_command(self, cmd_id: int, description: str = "",
                        log_success: bool = True, silent: bool = False) -> bool:
        """发送 SS 指令的通用方法 - 委托给 SerialManager"""
        return self.serial_manager.send_ss_command(cmd_id, description, log_success, silent)

    def send_ss0_start_stream(self) -> bool:
        """发送 SS:0 指令 - 开始数据流"""
        return self.serial_manager.send_ss0_start_stream()

    def send_ss1_start_calibration(self) -> bool:
        """发送 SS:1 指令 - 开始校准流"""
        return self.serial_manager.send_ss1_start_calibration()

    def send_ss4_stop_stream(self) -> bool:
        """发送 SS:4 指令 - 停止数据流/校准"""
        return self.serial_manager.send_ss4_stop_stream()

    def send_ss8_get_properties(self) -> bool:
        """发送 SS:8 指令 - 获取传感器属性"""
        return self.serial_manager.send_ss8_get_properties()

    def extract_network_config(self):
        """从传感器属性中提取网络配置 - 委托给 NetworkManager"""
        config = self.network_manager.extract_network_config(self.sensor_properties)
        
        # 同步回主类
        self.wifi_params = self.network_manager.wifi_params
        self.mqtt_params = self.network_manager.mqtt_params
        self.ota_params = self.network_manager.ota_params
        
        # 更新UI变量
        if self.wifi_params.get('ssid'):
            self.ssid_var.set(self.wifi_params['ssid'])
            self.password_var.set(self.wifi_params.get('password', ''))
        if self.mqtt_params.get('broker'):
            self.mqtt_broker_var.set(self.mqtt_params['broker'])
            self.mqtt_user_var.set(self.mqtt_params.get('username', ''))
            self.mqtt_password_var.set(self.mqtt_params.get('password', ''))
            self.mqtt_port_var.set(self.mqtt_params.get('port', '1883'))
        if self.ota_params.get('URL1') or self.ota_params.get('URL2'):
            self.URL1_var.set(self.ota_params.get('URL1', ''))
            self.URL2_var.set(self.ota_params.get('URL2', ''))
            self.URL3_var.set(self.ota_params.get('URL3', ''))
            self.URL4_var.set(self.ota_params.get('URL4', ''))
    
    def extract_and_display_alarm_threshold(self):
        """
        从传感器属性中提取报警阈值并显示在 UI 上
        """
        try:
            # 使用 NetworkManager 提取阈值
            threshold_info = self.network_manager.extract_alarm_threshold(self.sensor_properties)
            
            if threshold_info:
                accel_threshold = threshold_info.get('accel_threshold')
                gyro_threshold = threshold_info.get('gyro_threshold')
                
                # 更新 UI 显示
                if accel_threshold is not None:
                    self.ui_manager.set_entry_value('alarm_accel_threshold', str(accel_threshold))
                    self.ui_manager.update_statistics_label('current_accel_threshold', 
                                                            f"Accel: {accel_threshold} m/s²")
                
                if gyro_threshold is not None:
                    self.ui_manager.set_entry_value('alarm_gyro_threshold', str(gyro_threshold))
                    self.ui_manager.update_statistics_label('current_gyro_threshold', 
                                                            f"Gyro: {gyro_threshold}°")
                
                self.log_message(f"Current alarm threshold - Accel: {accel_threshold} m/s², Gyro: {gyro_threshold}°")
            else:
                self.log_message("No alarm threshold found in sensor properties")
                
        except Exception as e:
            self.log_message(f"Error extracting alarm threshold: {str(e)}")

    def enable_config_buttons(self):
        """启用配置按钮"""
        if hasattr(self, "set_wifi_btn"):
            self.set_wifi_btn.config(state="normal")
        if hasattr(self, "read_wifi_btn"):
            self.read_wifi_btn.config(state="normal")
        if hasattr(self, "set_mqtt_btn"):
            self.set_mqtt_btn.config(state="normal")
        if hasattr(self, "read_mqtt_btn"):
            self.read_mqtt_btn.config(state="normal")
        if hasattr(self, "set_ota_btn"):
            self.set_ota_btn.config(state="normal")
        if hasattr(self, "read_ota_btn"):
            self.read_ota_btn.config(state="normal")
        if hasattr(self, "local_coord_btn"):
            self.local_coord_btn.config(state="normal")
        if hasattr(self, "global_coord_btn"):
            self.global_coord_btn.config(state="normal")
        # 启用 Alarm & Device 标签页按钮
        if hasattr(self, "set_alarm_threshold_btn"):
            self.set_alarm_threshold_btn.config(state="normal")
        if hasattr(self, "save_config_btn"):
            self.save_config_btn.config(state="normal")
        if hasattr(self, "restart_sensor_btn"):
            self.restart_sensor_btn.config(state="normal")

    def display_network_summary(self):
        """显示网络配置摘要 - 委托给 NetworkManager"""
        self.network_manager.display_network_summary(self.sensor_properties)

    def save_network_config(self):
        """保存网络配置到文件 - 委托给 NetworkManager"""
        # 先同步参数到 network_manager
        self.network_manager.wifi_params = self.wifi_params
        self.network_manager.mqtt_params = self.mqtt_params
        self.network_manager.save_network_config()

    def load_network_config(self):
        """从文件加载网络配置 - 委托给 NetworkManager"""
        if self.network_manager.load_network_config():
            # 同步回主类
            self.wifi_params = self.network_manager.wifi_params
            self.mqtt_params = self.network_manager.mqtt_params

    def setup_stats_grid(self, parent, sensor_name):
        """设置统计信息网格 - 修复键名生成"""
        # 存储标签的字典
        if not hasattr(self, "stats_labels"):
            self.stats_labels = {}

        # 传感器标题
        ttk.Label(parent, text=f"{sensor_name}:", font=("Arial", 9, "bold")).pack(
            anchor="w", padx=5, pady=2
        )

        # 三轴统计
        axes = ["X", "Y", "Z"]
        for i, axis in enumerate(axes):
            axis_frame = ttk.Frame(parent)
            axis_frame.pack(fill="x", padx=10, pady=1)

            ttk.Label(axis_frame, text=f"{axis}:", width=3, font=("Arial", 9)).pack(
                side="left"
            )

            # 均值标签
            mean_var = StringVar(value="Mean: 0.000")
            mean_label = ttk.Label(
                axis_frame, textvariable=mean_var, font=("Courier", 8)
            )
            mean_label.pack(side="left", padx=5)

            # 标准差标签
            std_var = StringVar(value="Std: 0.000")
            std_label = ttk.Label(axis_frame, textvariable=std_var, font=("Courier", 8))
            std_label.pack(side="left", padx=5)

            # 存储标签引用 - 使用统一的键名生成规则
            # 简化传感器名称：移除数字和空格，转换为小写
            sensor_key = (
                sensor_name.lower()
                .replace(" ", "_")
                .replace("6050", "")
                .replace("355", "")
            )

            # 确保键名一致性
            mean_key = f"{sensor_key}_{axis.lower()}_mean"
            std_key = f"{sensor_key}_{axis.lower()}_std"

            self.stats_labels[mean_key] = mean_var
            self.stats_labels[std_key] = std_var

    def refresh_ports(self):
        """刷新可用串口列表"""
        ports = SerialManager.list_available_ports()
        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)

    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        # 在主线程中更新UI（检查窗口是否还存在）
        if hasattr(self, 'root') and self.root and self.root.winfo_exists():
            try:
                self.root.after(0, lambda: self._add_log_entry(log_entry))
            except Exception:
                pass  # 窗口已关闭，忽略

    def _add_log_entry(self, log_entry):
        """在主线程中添加日志条目"""
        try:
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                self.log_text.insert(tk.END, log_entry + "\n")
                self.log_text.see(tk.END)
        except Exception:
            pass  # 控件已销毁，忽略

    def toggle_connection(self):
        """切换串口连接"""
        port = self.port_var.get()
        baudrate = int(self.baud_var.get())
        
        if self.serial_manager.is_connected:
            self.disconnect_serial()
            self.connect_btn.config(text="Connect")
            self.data_btn.config(state="disabled")
            self.data_btn2.config(state="disabled")
            self.read_props_btn.config(state="disabled")
        else:
            if self.serial_manager.connect(port, baudrate):
                self.connect_btn.config(text="Disconnect")
                self.data_btn.config(state="normal")
                self.data_btn2.config(state="normal")
                self.ser = self.serial_manager.serial_port
        
        self.read_props_btn.config(state="normal")

    def connect_serial(self):
        """连接串口 - 委托给 SerialManager"""
        port = self.port_var.get()
        baudrate = int(self.baud_var.get())
        
        if self.serial_manager.connect(port, baudrate):
            self.connect_btn.config(text="Disconnect")
            self.data_btn.config(state="normal")
            self.data_btn2.config(state="normal")
            self.ser = self.serial_manager.serial_port

    def disconnect_serial(self):
        """断开串口连接 - 委托给 SerialManager"""
        self.serial_manager.disconnect()
        self.ser = None
        
        # 禁用按钮
        self.connect_btn.config(text="Connect")
        self.data_btn.config(text="Start Data Stream")
        self.data_btn.config(state="disabled")
        self.data_btn2.config(text="Start CAS Stream")
        self.data_btn2.config(state="disabled")
        self.read_props_btn.config(state="disabled")
        self.resend_btn.config(state="disabled")
        if hasattr(self, "local_coord_btn"):
            self.local_coord_btn.config(state="disabled")
        if hasattr(self, "global_coord_btn"):
            self.global_coord_btn.config(state="disabled")
        self.calibrate_btn.config(state="disabled")
        self.send_btn.config(state="disabled")

    def toggle_data_stream(self):
        """切换数据流状态"""
        if not self.serial_manager.is_connected:
            self.log_message("Error: Not connected to serial port!")
            return

        if not self.serial_manager.is_reading:
            self.start_data_stream()
        else:
            self.stop_data_stream()

    def toggle_data_stream2(self):
        """切换校准流状态"""
        if not self.serial_manager.is_connected:
            self.log_message("Error: Not connected to serial port!")
            return

        if not self.serial_manager.is_reading:
            self.start_data_stream2()
        else:
            self.stop_data_stream2()

    def start_data_stream(self):
        """开始数据流"""
        if not self.serial_manager.is_connected:
            self.log_message("Error: Not connected to serial port!")
            return
            
        if self.serial_manager.send_ss0_start_stream():
            if self.serial_manager.start_reading():
                self.is_reading = True
                self.data_btn.config(text="Stop Data Stream")
                self.calibrate_btn.config(state="normal")
                
                # 重置数据
                self.clear_data()
                self.data_start_time = time.time()
                self.packet_count = 0
                self.packets_received = 0
                
                # 启动GUI更新
                self.schedule_update_gui()

    def start_data_stream2(self):
        """开始校准流"""
        if not self.serial_manager.is_connected:
            self.log_message("Error: Not connected to serial port!")
            return
            
        if self.serial_manager.send_ss1_start_calibration():
            if self.serial_manager.start_reading():
                self.is_reading = True
                self.data_btn2.config(text="Stop Calibration Stream")
                self.calibrate_btn.config(state="disabled")
                
                # 重置数据
                self.clear_data()
                self.data_start_time = time.time()
                self.packet_count = 0
                self.packets_received = 0
                
                # 启动GUI更新
                self.schedule_update_gui()

    def stop_data_stream(self):
        """停止数据流"""
        if not self.is_reading:
            return

        self.is_reading = False
        self.serial_manager.stop_reading()
        self.serial_manager.send_ss4_stop_stream()

        # 更新UI状态
        self.data_btn.config(text="Start Data Stream")
        self.data_btn.config(state="normal")
        self.calibrate_btn.config(state="disabled")
        if hasattr(self, "capture_btn"):
            self.capture_btn.config(state="disabled")

    def stop_data_stream2(self):
        """停止校准流"""
        if not self.is_reading:
            return

        self.is_reading = False
        self.serial_manager.stop_reading()
        self.serial_manager.send_ss4_stop_stream()

        # 更新UI状态
        self.data_btn2.config(text="Start CAS Stream")
        self.data_btn2.config(state="normal")
        self.calibrate_btn.config(state="disabled")
        if hasattr(self, "capture_btn"):
            self.capture_btn.config(state="disabled")

    def parse_sensor_data(self, data_string):
        """解析传感器数据 - 委托给 DataProcessor"""
        return self.data_processor.parse_sensor_data(data_string)

    def clear_data(self):
        """清空所有数据 - 委托给 DataProcessor"""
        self.data_processor.clear_all()

    def calculate_statistics(self, data_array, start_idx=None, end_idx=None):
        """计算统计信息 - 委托给 DataProcessor"""
        return self.data_processor.calculate_statistics(data_array, start_idx, end_idx)

    def generate_key_from_mac(self, mac_address: str) -> str:
        """基于MAC地址生成密钥 - 委托给 ActivationWorkflow"""
        return self.activation_workflow.generate_key_from_mac(mac_address)

    def verify_key(self, input_key: str, mac_address: str) -> bool:
        """验证密钥 - 委托给 ActivationWorkflow"""
        return self.activation_workflow.verify_key(input_key, mac_address)

    def extract_mac_from_properties(self) -> Optional[str]:
        """从传感器属性中提取MAC地址 - 委托给 ActivationWorkflow"""
        mac = self.activation_workflow.extract_mac_from_properties(self.sensor_properties)
        if mac:
            self.mac_address = mac
        return mac

    def validate_mac_address(self, mac_str: str) -> bool:
        """验证MAC地址格式 - 委托给 ActivationWorkflow"""
        return ActivationWorkflow.validate_mac_address(mac_str)

    def check_activation_status(self) -> bool:
        """检查传感器激活状态 - 委托给 ActivationWorkflow"""
        is_activated = self.activation_workflow.check_activation_status(self.sensor_properties)
        self.sensor_activated = is_activated
        return is_activated

    def activate_sensor(self):
        """激活传感器 - 委托给 ActivationWorkflow"""
        # 同步参数
        self.activation_workflow._mac_address = self.mac_address
        self.activation_workflow._generated_key = self.generated_key
        self.activation_workflow.activate_sensor()

    def activate_sensor_thread(self):
        """在新线程中激活传感器 - 已委托给 ActivationWorkflow"""
        pass

    def verify_activation(self):
        """验证传感器激活状态 - 委托给 ActivationWorkflow"""
        self.activation_workflow.verify_activation(self.sensor_properties)

    def verify_activation_thread(self):
        """在新线程中验证激活状态 - 已委托给 ActivationWorkflow"""
        pass

    def update_activation_status(self):
        """更新激活状态显示 - 同时更新 Activation 区域和 Status 区域"""
        if self.sensor_activated:
            # 更新下方 Status 区域
            self.status_var.set("Activated")
            # 更新 Activation 区域（兼容性）
            self.activation_status_var.set("Activated")
            if hasattr(self, "activation_status_label"):
                self.activation_status_label.config(foreground="green")
            if hasattr(self, "activate_btn"):
                self.activate_btn.config(state="disabled")
            # 更新新的 UI 变量
            if hasattr(self, "ui_manager"):
                self.ui_manager.update_statistics_label('activation_status', "Activated")
                status_label = self.ui_manager.get_widget('activation_status_label')
                if status_label:
                    status_label.config(foreground="green")
        else:
            # 更新下方 Status 区域
            self.status_var.set("Not activated")
            # 更新 Activation 区域（兼容性）
            self.activation_status_var.set("Not activated")
            if hasattr(self, "activation_status_label"):
                self.activation_status_label.config(foreground="red")
            if (
                hasattr(self, "activate_btn")
                and self.mac_address
                and self.generated_key
            ):
                self.activate_btn.config(state="normal")
            # 更新新的 UI 变量
            if hasattr(self, "ui_manager"):
                self.ui_manager.update_statistics_label('activation_status', "Not Activated")
                status_label = self.ui_manager.get_widget('activation_status_label')
                if status_label:
                    status_label.config(foreground="red")

    def extract_and_process_mac(self):
        """提取MAC地址并处理激活逻辑"""
        # 提取MAC地址
        self.mac_address = self.extract_mac_from_properties()

        if self.mac_address:
            # 确保mac_var存在（兼容性）
            if hasattr(self, "mac_var"):
                self.mac_var.set(self.mac_address)
            
            # 更新新的UI变量（Activation区域显示）
            if hasattr(self, "ui_manager"):
                self.ui_manager.set_entry_value('activation_mac', self.mac_address)

            # 生成密钥
            try:
                self.generated_key = self.generate_key_from_mac(self.mac_address)
                self.log_message(
                    f"Generated activation key from MAC {self.mac_address}"
                )
                self.log_message(f"Key: {self.generated_key}")
                
                # 更新UI显示密钥片段（7字符）
                if hasattr(self, "ui_manager") and len(self.generated_key) >= 12:
                    key_fragment = self.generated_key[5:12]
                    self.ui_manager.set_entry_value('activation_key', key_fragment)
                    
            except Exception as e:
                self.log_message(f"Error generating key from MAC: {str(e)}")
                return

            # 检查激活状态
            self.sensor_activated = self.check_activation_status()
            self.update_activation_status()

            # 启用激活按钮
            if not self.sensor_activated and hasattr(self, "activate_btn"):
                self.activate_btn.config(state="normal")
                if hasattr(self, "verify_btn"):
                    self.verify_btn.config(state="normal")
            
            # 启用复制密钥按钮
            if hasattr(self, "ui_manager"):
                self.ui_manager.set_widget_state('copy_key_btn', 'normal')

            self.log_message(
                f"Sensor activation status: {'ACTIVATED' if self.sensor_activated else 'NOT ACTIVATED'}"
            )
        else:
            self.log_message("Warning: MAC address not found in sensor properties")
            if hasattr(self, "mac_var"):
                self.mac_var.set("Not found")
            if hasattr(self, "ui_manager"):
                self.ui_manager.set_entry_value('activation_mac', "Not found")

    def display_activation_info(self):
        """显示激活相关信息"""
        if not self.sensor_properties:
            return

        self.log_message("\n" + "=" * 60)
        self.log_message("ACTIVATION INFORMATION")
        self.log_message("=" * 60)

        if self.mac_address:
            self.log_message(f"MAC Address: {self.mac_address}")

            if self.generated_key:
                self.log_message(f"Generated Key: {self.generated_key}")

                # 检查AKS字段
                aks_value = None
                if "sys" in self.sensor_properties:
                    sys_info = self.sensor_properties["sys"]
                    aks_keys = ["AKY", "aky", "ak_key"]
                    for key in aks_keys:
                        if key in sys_info:
                            aks_value = sys_info[key]
                            break

                if aks_value:
                    self.log_message(f"Stored AKY: {aks_value}")

                    try:
                        is_match = self.verify_key(aks_value, self.mac_address)
                        self.log_message(f"Key Match: {is_match}")
                        self.log_message(
                            f"Activation Status: {'ACTIVATED' if is_match else 'NOT ACTIVATED'}"
                        )

                        if not is_match:
                            self.log_message(
                                "ACTION REQUIRED: Activate sensor using 'Activate Sensor' button"
                            )
                    except Exception as e:
                        self.log_message(f"Key verification error: {str(e)}")
                else:
                    self.log_message("AKY field: Not found in properties")
                    self.log_message(
                        "ACTION REQUIRED: Activate sensor using 'Activate Sensor' button"
                    )
            else:
                self.log_message("Generated Key: Not available")
        else:
            self.log_message("MAC Address: Not found in properties")

        self.log_message("=" * 60)

    def update_gui(self):
        """更新GUI - 主更新循环（性能优化版本）"""
        if self.exiting or not hasattr(self, "root") or not self.root:
            return
        
        # 检查窗口是否仍然存在
        try:
            if not self.root.winfo_exists():
                return
        except Exception:
            return
        
        # 性能优化：窗口移动期间跳过更新
        if Config.ENABLE_WINDOW_MOVE_PAUSE and self._window_moving:
            # 调度下一次更新
            if not self.exiting and hasattr(self, "root") and self.root.winfo_exists():
                self.schedule_update_gui()
            return
        
        # 更新频率显示
        try:
            # 检查窗口是否仍然存在
            if not hasattr(self, "root") or not self.root.winfo_exists():
                return
            current_time = time.time()
            if current_time - self.last_freq_update >= 1.0:
                self.serial_freq = self.packets_received
                self.packets_received = 0
                self.last_freq_update = current_time
                self.freq_var.set(f"{self.serial_freq} Hz")

            # 处理数据队列
            processed_count = 0
            if hasattr(self, "data_queue"):
                while (
                    not self.data_queue.empty() and processed_count < 100
                ):  # 增加处理数量
                    try:
                        data_string = self.data_queue.get_nowait()

                        mpu_accel, mpu_gyro, adxl_accel = self.parse_sensor_data(
                            data_string
                        )

                        if mpu_accel and mpu_gyro and adxl_accel:
                            # 使用包计数计算时间，确保时间连续
                            if self.data_start_time is None:
                                self.data_start_time = time.time()

                            # 使用包计数计算时间
                            current_relative_time = (
                                self.packet_count / self.expected_frequency
                            )
                            self.packet_count += 1

                            # 更新时间数据
                            self.time_data.append(current_relative_time)

                            # 更新传感器数据
                            for i in range(3):
                                self.mpu_accel_data[i].append(mpu_accel[i])
                                self.mpu_gyro_data[i].append(mpu_gyro[i])
                                self.adxl_accel_data[i].append(adxl_accel[i])

                            # 计算重力矢量模长
                            gravity_mag = np.sqrt(
                                mpu_accel[0] ** 2
                                + mpu_accel[1] ** 2
                                + mpu_accel[2] ** 2
                            )
                            self.gravity_mag_data.append(gravity_mag)
                            
                            # 注意：deque 会自动处理长度限制，无需手动切片
                        processed_count += 1

                    except queue.Empty:
                        break
                    except Exception as e:
                        continue
                # 更新统计信息（带频率控制）
                if current_time - self.last_stats_update >= self.stats_update_interval:
                    self.safe_update_statistics()
                    self.last_stats_update = current_time

                if not self.exiting:
                    self.update_charts()

                # 调度下一次更新
                if not self.exiting and hasattr(self, "root"):
                    self.schedule_update_gui()
        except Exception as e:
            # 如果发生异常，记录日志但不要中断
            if not self.exiting:
                self.log_message(f"GUI update error: {str(e)}")

    def update_statistics(self):
        """更新统计信息 - 委托给 DataProcessor"""
        if not self.data_processor.has_data():
            return
        
        # 更新统计数据
        self.data_processor.update_statistics()
        
        # 同步到本地引用
        self.real_time_stats = self.data_processor.get_statistics()
        
        # 更新UI显示
        axis_names = ["x", "y", "z"]
        
        # 更新MPU6050加速度计统计
        for i in range(3):
            mean_val = self.real_time_stats["mpu_accel_mean"][i]
            std_val = self.real_time_stats["mpu_accel_std"][i]
            mean_key = f"mpu_accel_{axis_names[i]}_mean"
            std_key = f"mpu_accel_{axis_names[i]}_std"
            
            if mean_key in self.stats_labels:
                self.stats_labels[mean_key].set(f"Mean: {mean_val:6.3f}")
            if std_key in self.stats_labels:
                self.stats_labels[std_key].set(f"Std: {std_val:6.3f}")
        
        # 更新ADXL355加速度计统计
        for i in range(3):
            mean_val = self.real_time_stats["adxl_accel_mean"][i]
            std_val = self.real_time_stats["adxl_accel_std"][i]
            mean_key = f"adxl_accel_{axis_names[i]}_mean"
            std_key = f"adxl_accel_{axis_names[i]}_std"
            
            if mean_key in self.stats_labels:
                self.stats_labels[mean_key].set(f"Mean: {mean_val:6.3f}")
            if std_key in self.stats_labels:
                self.stats_labels[std_key].set(f"Std: {std_val:6.3f}")
        
        # 更新MPU6050陀螺仪统计
        for i in range(3):
            mean_val = self.real_time_stats["mpu_gyro_mean"][i]
            std_val = self.real_time_stats["mpu_gyro_std"][i]
            mean_key = f"mpu_gyro_{axis_names[i]}_mean"
            std_key = f"mpu_gyro_{axis_names[i]}_std"
            
            if mean_key in self.stats_labels:
                self.stats_labels[mean_key].set(f"Mean: {mean_val:6.3f}")
            if std_key in self.stats_labels:
                self.stats_labels[std_key].set(f"Std: {std_val:6.3f}")
        
        # 更新重力矢量统计
        mean_val = self.real_time_stats["gravity_mean"]
        std_val = self.real_time_stats["gravity_std"]
        
        if "gravity_mean" in self.stats_labels:
            self.stats_labels["gravity_mean"].set(f"Mean: {mean_val:6.3f}")
        if "gravity_std" in self.stats_labels:
            self.stats_labels["gravity_std"].set(f"Std: {std_val:6.3f}")

    def safe_update_statistics(self):
        """安全的统计信息更新 - 带错误处理"""
        try:
            self.update_statistics()
        except KeyError as e:
            # 记录错误但不中断程序
            missing_key = str(e).strip("'")
            self.log_message(f"Warning: Statistics key not found: {missing_key}")

            # 调试信息：显示所有可用的键
            available_keys = list(self.stats_labels.keys())
            self.log_message(f"Available keys: {available_keys}")

        except Exception as e:
            self.log_message(f"Error updating statistics: {str(e)}")

    def debug_stats_labels(self):
        """调试统计标签 - 显示所有可用的键"""
        if not hasattr(self, "stats_labels") or not self.stats_labels:
            self.log_message("No statistics labels available")
            return

        self.log_message("Available statistics labels:")
        for key in sorted(self.stats_labels.keys()):
            self.log_message(f"  {key}")

    def update_charts(self):
        """更新图表 - 使用ChartManager和DataProcessor"""
        if (
            self.exiting
            or not self.chart_manager
            or not self.data_processor.has_data()
        ):
            return
        
        # 从DataProcessor获取显示数据
        data_dict = self.data_processor.get_display_data()
        
        # 使用ChartManager更新图表
        updated = self.chart_manager.update_charts(data_dict)
        
        # 如果图表更新成功，更新统计信息
        if updated:
            self._update_chart_statistics_to_manager()
    
    def _update_chart_statistics_to_manager(self):
        """将统计信息传递给ChartManager更新"""
        if not self.chart_manager:
            return
        
        stats = self.data_processor.get_statistics()
        stats_dict = {
            'window_size': self.stats_window_size,
            'mpu_accel_mean': stats['mpu_accel_mean'],
            'mpu_accel_std': stats['mpu_accel_std'],
            'adxl_accel_mean': stats['adxl_accel_mean'],
            'adxl_accel_std': stats['adxl_accel_std'],
            'mpu_gyro_mean': stats['mpu_gyro_mean'],
            'mpu_gyro_std': stats['mpu_gyro_std'],
            'gravity_mean': stats['gravity_mean'],
            'gravity_std': stats['gravity_std'],
        }
        self.chart_manager.update_statistics_text(stats_dict)

    def adjust_y_limits(self):
        """调整Y轴范围 - 优化版（使用numpy向量化计算）"""
        # MPU6050加速度计
        if self.mpu_accel_data[0] and len(self.mpu_accel_data[0]) > 0:
            recent_points = min(Config.DISPLAY_DATA_POINTS, len(self.mpu_accel_data[0]))
            
            # 使用list转换后计算（deque不支持直接slice）
            recent_data = []
            for i in range(3):
                data_list = list(self.mpu_accel_data[i])
                if len(data_list) >= recent_points:
                    recent_data.extend(data_list[-recent_points:])

            if recent_data:
                # 使用numpy向量化计算
                y_min = float(np.min(recent_data)) - Config.CHART_Y_PADDING
                y_max = float(np.max(recent_data)) + Config.CHART_Y_PADDING

                # 确保范围合理
                if abs(y_max - y_min) < Config.CHART_MIN_Y_RANGE:
                    y_min = -10
                    y_max = 10

                self.ax1.set_ylim(y_min, y_max)

        # ADXL355加速度计
        if self.adxl_accel_data[0] and len(self.adxl_accel_data[0]) > 0:
            recent_points = min(Config.DISPLAY_DATA_POINTS, len(self.adxl_accel_data[0]))

            recent_data = []
            for i in range(3):
                data_list = list(self.adxl_accel_data[i])
                if len(data_list) >= recent_points:
                    recent_data.extend(data_list[-recent_points:])

            if recent_data:
                y_min = float(np.min(recent_data)) - 2
                y_max = float(np.max(recent_data)) + 2

                if abs(y_max - y_min) < 1:
                    y_min = -10
                    y_max = 10

                self.ax2.set_ylim(y_min, y_max)

        # MPU6050陀螺仪
        if self.mpu_gyro_data[0] and len(self.mpu_gyro_data[0]) > 0:
            recent_points = min(Config.DISPLAY_DATA_POINTS, len(self.mpu_gyro_data[0]))

            recent_data = []
            for i in range(3):
                data_list = list(self.mpu_gyro_data[i])
                if len(data_list) >= recent_points:
                    recent_data.extend(data_list[-recent_points:])

            if recent_data:
                y_min = float(np.min(recent_data)) - 1
                y_max = float(np.max(recent_data)) + 1

                if abs(y_max - y_min) < Config.CHART_MIN_Y_RANGE / 2:
                    y_min = -5
                    y_max = 5

                self.ax3.set_ylim(y_min, y_max)

        # 重力矢量模长
        if self.gravity_mag_data and len(self.gravity_mag_data) > 0:
            recent_points = min(Config.DISPLAY_DATA_POINTS, len(self.gravity_mag_data))
            recent_data = list(self.gravity_mag_data)[-recent_points:]

            if recent_data:
                y_min = max(0, float(np.min(recent_data)) - Config.CHART_Y_PADDING)
                y_max = float(np.max(recent_data)) + Config.CHART_Y_PADDING

                if abs(y_max - y_min) < 1:
                    y_min = 0
                    y_max = 20

                self.ax4.set_ylim(y_min, y_max)

    def start_calibration(self):
        """开始校准 - 委托给 CalibrationWorkflow"""
        if not self.is_reading:
            self.log_message("Error: Start data stream first!")
            return
        
        self.is_calibrating = True
        self.calibration_workflow.start_calibration()
        self.calibrate_btn.config(state="disabled")
        self.capture_btn.config(state="normal")
        self.data_btn.config(state="disabled")

    def capture_position(self):
        """采集当前位置数据 - 委托给 CalibrationWorkflow"""
        self.capture_btn.config(state="disabled")
        self.calibration_workflow.capture_position()

    def update_position_display(self):
        """更新位置显示"""
        if hasattr(self, 'calibration_workflow'):
            self.position_label.config(text=self.calibration_workflow.position_progress)

    def finish_calibration(self):
        """完成校准 - 委托给 CalibrationWorkflow"""
        self.calibration_workflow.finish_calibration()

    def generate_calibration_commands(self):
        """生成校准命令 - 使用 CalibrationWorkflow"""
        # 从 workflow 获取参数
        if self.calibration_workflow.calibration_params:
            self.calibration_params = self.calibration_workflow.calibration_params
        
        commands = self.calibration_workflow.generate_calibration_commands()
        
        # 显示命令
        self.cmd_text.delete(1.0, tk.END)
        for cmd in commands:
            self.cmd_text.insert(tk.END, cmd + "\n")
        
        self.log_message(
            "Calibration commands generated. Click 'Send All Commands' to send to ESP32."
        )

    def send_all_commands(self):
        """发送所有校准命令到串口"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        # 获取命令
        commands = self.cmd_text.get(1.0, tk.END).strip().split("\n")

        if not commands or commands[0] == "":
            self.log_message("Error: No calibration commands to send!")
            return

        self.log_message("Sending calibration commands to ESP32...")

        # 在新线程中发送命令
        threading.Thread(
            target=self.send_commands_thread, args=(commands,), daemon=True
        ).start()

    def send_commands_thread(self, commands):
        """在新线程中发送命令"""
        try:
            for i, cmd in enumerate(commands):
                if cmd.strip():  # 跳过空行
                    # 发送命令
                    self.ser.write(f"{cmd}\n".encode())
                    self.ser.flush()

                    # 在主线程中更新日志
                    self.root.after(0, lambda c=cmd: self.log_message(f"Sent: {c}"))

                    # 等待响应
                    time.sleep(2)

                    # 尝试读取响应（可选）
                    try:
                        response = self.ser.readline().decode().strip()
                        if response:
                            self.root.after(
                                0, lambda r=response: self.log_message(f"Response: {r}")
                            )
                    except:
                        pass

            self.root.after(
                0,
                lambda: self.log_message("All calibration commands sent successfully!"),
            )

            # 启用重新发送按钮
            self.root.after(0, lambda: self.resend_btn.config(state="normal"))

            # 询问是否读取传感器属性
            self.root.after(0, self.ask_read_properties)

        except Exception as e:
            self.root.after(
                0, lambda: self.log_message(f"Error sending commands: {str(e)}")
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
        try:
            # 创建保存的数据结构
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "calibration_parameters": self.calibration_params,
                "calibration_commands": self.cmd_text.get(1.0, tk.END)
                .strip()
                .split("\n"),
                "sensor_properties": self.sensor_properties,
            }

            # 弹出文件保存对话框
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )

            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)

                self.log_message(f"Calibration parameters saved to: {filename}")

                # 同时保存到默认文件
                with open(self.calibration_file, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)

                self.log_message(
                    f"Parameters also saved to default file: {self.calibration_file}"
                )

        except Exception as e:
            self.log_message(f"Error saving calibration parameters: {str(e)}")

    def load_calibration_parameters(self):
        """从文件加载校准参数"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                with open(filename, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)

                # 更新校准参数
                if "calibration_parameters" in loaded_data:
                    self.calibration_params.update(
                        loaded_data["calibration_parameters"]
                    )

                # 更新命令文本
                if "calibration_commands" in loaded_data:
                    self.cmd_text.delete(1.0, tk.END)
                    for cmd in loaded_data["calibration_commands"]:
                        self.cmd_text.insert(tk.END, cmd + "\n")

                # 更新传感器属性
                if "sensor_properties" in loaded_data:
                    self.sensor_properties = loaded_data["sensor_properties"]

                self.log_message(f"Calibration parameters loaded from: {filename}")
                self.send_btn.config(state="normal")
                self.save_btn.config(state="normal")
                self.read_props_btn.config(state="normal")

        except Exception as e:
            self.log_message(f"Error loading calibration parameters: {str(e)}")

    def ask_read_properties(self):
        """询问是否读取传感器属性"""
        response = messagebox.askyesno(
            "Read Sensor Properties",
            "All calibration commands have been sent successfully.\n\n"
            "Do you want to read sensor properties now?",
        )
        if response:
            self.read_sensor_properties()

    def read_sensor_properties(self):
        """读取传感器属性"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        self.log_message("Starting sensor properties reading process...")

        # 在新线程中读取属性
        threading.Thread(target=self.read_properties_thread, daemon=True).start()

    def read_properties_thread(self):
        """在新线程中读取传感器属性"""
        original_reading_state = self.is_reading

        try:
            # 第一步：停止数据流（如果正在运行）
            if self.is_reading:
                self.root.after(0, lambda: self.log_message("Stopping data stream..."))
                self.root.after(0, self.stop_data_stream)
                time.sleep(1.0)  # 等待数据流停止

            # 第二步：清空输入缓冲区
            self.ser.reset_input_buffer()
            time.sleep(Config.BUFFER_CLEAR_DELAY)

            # 第三步：发送SS:8命令获取属性
            self.root.after(0, lambda: self.log_message("Sending SS:8 command..."))
            self.send_ss8_get_properties()

            # 第四步：等待并读取响应
            time.sleep(2.0)  # 等待设备响应

            response_bytes = b""
            start_time = time.time()
            timeout = Config.RESPONSE_TIMEOUT * 2  # 10秒超时

            self.root.after(0, lambda: self.log_message("Reading response..."))

            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    chunk = self.ser.read(self.ser.in_waiting)
                    response_bytes += chunk

                    # 检查是否收到完整的JSON响应
                    response_str = response_bytes.decode("utf-8", errors="ignore")

                    # 查找JSON开始和结束标记
                    json_start = response_str.find("{")
                    json_end = response_str.rfind("}")

                    if json_start != -1 and json_end != -1 and json_end > json_start:
                        json_str = response_str[json_start : json_end + 1]

                        try:
                            # 解析JSON
                            self.sensor_properties = json.loads(json_str)
                            # 新增：处理MAC地址和激活状态
                            self.root.after(0, self.extract_and_process_mac)
                            # 在主线程中显示属性
                            self.root.after(0, self.display_sensor_properties)

                            # 提取网络配置
                            self.root.after(0, self.extract_network_config)
                            
                            # 提取并显示报警阈值
                            self.root.after(0, self.extract_and_display_alarm_threshold)

                            # 显示网络配置摘要
                            self.root.after(0, self.display_network_summary)

                            self.root.after(
                                0,
                                lambda: self.log_message(
                                    "Sensor properties received successfully!"
                                ),
                            )

                            # 新增：显示激活信息
                            self.root.after(0, self.display_activation_info)
                            # 保存属性到文件
                            self.root.after(0, self.auto_save_properties)

                            return

                        except json.JSONDecodeError as e:
                            # JSON解析失败，继续等待更多数据
                            continue

                time.sleep(Config.THREAD_ERROR_DELAY)  # 短暂休眠

            # 超时处理
            self.root.after(
                0,
                lambda: self.log_message(
                    "Timeout: Failed to receive complete sensor properties"
                ),
            )

            # 显示接收到的部分数据（用于调试）
            if response_bytes:
                partial_response = response_bytes.decode("utf-8", errors="ignore")
                self.root.after(
                    0,
                    lambda: self.log_message(
                        f"Partial response: {partial_response[:500]}..."
                    ),
                )

        except Exception as e:
            self.root.after(
                0,
                lambda: self.log_message(f"Error reading sensor properties: {str(e)}"),
            )

        finally:
            # 恢复之前的数据流状态
            if original_reading_state and not self.is_reading:
                self.root.after(
                    0, lambda: self.log_message("Restarting data stream...")
                )
                time.sleep(1.0)
                self.root.after(0, self.start_data_stream)
                

        
    
    def auto_save_properties(self):
        """自动保存传感器属性"""
        try:
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "sensor_properties": self.sensor_properties,
                "calibration_parameters": self.calibration_params,
            }

            with open(self.properties_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            self.log_message(
                f"Sensor properties automatically saved to: {self.properties_file}"
            )

        except Exception as e:
            self.log_message(f"Error auto-saving properties: {str(e)}")

    def display_sensor_properties(self):
        """显示传感器属性"""
        if not self.sensor_properties:
            self.log_message("No sensor properties to display")
            return

        # 创建新窗口显示属性
        prop_window = tk.Toplevel(self.root)
        prop_window.title("Sensor Properties")
        prop_window.geometry("1200x1500")

        # 创建框架
        main_frame = ttk.Frame(prop_window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # 创建树形视图显示属性
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))

        # 创建滚动条
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        # 创建树形视图
        self.props_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll.set,
            columns=("value",),
            show="tree",
            height=20,
        )
        self.props_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=self.props_tree.yview)

        # 配置列
        self.props_tree.column("#0", width=300, minwidth=200)
        self.props_tree.column("value", width=400, minwidth=200)

        # 添加数据
        self.populate_properties_tree(self.sensor_properties, "")

        # 添加按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        # 保存按钮
        save_btn = ttk.Button(
            button_frame,
            text="Save Properties to File",
            command=self.save_properties_to_file,
            width=20,
        )
        save_btn.pack(side="left", padx=5)

        # 关闭按钮
        close_btn = ttk.Button(
            button_frame, text="Close", command=prop_window.destroy, width=20
        )
        close_btn.pack(side="right", padx=5)

        # 在日志中显示关键信息摘要
        self.display_properties_summary()

    def populate_properties_tree(self, data, parent, prefix=""):
        """递归填充属性树"""
        if isinstance(data, dict):
            for key, value in data.items():
                node_id = self.props_tree.insert(
                    parent, "end", text=str(key), values=("",)
                )
                if isinstance(value, (dict, list)):
                    self.populate_properties_tree(
                        value, node_id, f"{prefix}.{key}" if prefix else key
                    )
                else:
                    self.props_tree.set(node_id, "value", str(value))
        elif isinstance(data, list):
            for i, value in enumerate(data):
                node_id = self.props_tree.insert(
                    parent, "end", text=f"[{i}]", values=("",)
                )
                if isinstance(value, (dict, list)):
                    self.populate_properties_tree(value, node_id, f"{prefix}[{i}]")
                else:
                    self.props_tree.set(node_id, "value", str(value))

    def display_properties_summary(self):
        """在日志中显示属性摘要"""
        if not self.sensor_properties or "sys" not in self.sensor_properties:
            return

        sys_info = self.sensor_properties["sys"]

        self.log_message("\n" + "=" * 60)
        self.log_message("SENSOR PROPERTIES SUMMARY")
        self.log_message("=" * 60)

        # 设备信息
        self.log_message(f"Device Name: {sys_info.get('DN', 'N/A')}")
        self.log_message(f"Device Serial: {sys_info.get('DS', 'N/A')}")

        # 网络信息
        self.log_message(f"SSID: {sys_info.get('SSID', 'N/A')}")
        self.log_message(f"WiFi Password: {sys_info.get('PA', 'N/A')}")

        # 位置信息
        self.log_message(
            f"Location: {sys_info.get('PR', 'N/A')}, {sys_info.get('PO', 'N/A')}, {sys_info.get('CI', 'N/A')}"
        )
        self.log_message(
            f"Coordinates: {sys_info.get('LAT', 'N/A')}, {sys_info.get('LON', 'N/A')}"
        )

        # 校准参数
        if "RACKS" in sys_info:
            self.log_message(f"MPU6050 Accel Scale: {sys_info['RACKS']}")
        if "RACOF" in sys_info:
            self.log_message(f"MPU6050 Accel Offset: {sys_info['RACOF']}")
        if "REACKS" in sys_info:
            self.log_message(f"ADXL355 Accel Scale: {sys_info['REACKS']}")
        if "REACOF" in sys_info:
            self.log_message(f"ADXL355 Accel Offset: {sys_info['REACOF']}")
        if "VROOF" in sys_info:  # 修正：使用VROOF
            self.log_message(f"MPU6050 Gyro Offset (VROOF): {sys_info['VROOF']}")
        if "GROOF" in sys_info:
            self.log_message(f"Gyro Offset (GROOF): {sys_info['GROOF']}")

        # 服务器信息
        self.log_message(
            f"MQTT Broker: {sys_info.get('MBR', 'N/A')}:{sys_info.get('MPT', 'N/A')}"
        )
        self.log_message(f"MQTT Username: {sys_info.get('MUS', 'N/A')}")

        self.log_message("=" * 60)

    def save_properties_to_file(self):
        """保存属性到文件"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"sensor_properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )

            if filename:
                save_data = {
                    "timestamp": datetime.now().isoformat(),
                    "sensor_properties": self.sensor_properties,
                }

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)

                self.log_message(f"Sensor properties saved to: {filename}")

        except Exception as e:
            self.log_message(f"Error saving properties to file: {str(e)}")

    def reset_calibration_state(self):
        """重置校准状态"""
        self.is_calibrating = False
        self.calibrate_btn.config(state="normal")
        self.capture_btn.config(state="disabled")
        self.data_btn.config(state="normal")
        self.status_var.set("Status: Ready")

    # ==================== Alarm & Device 回调方法 ====================
    
    def set_alarm_threshold(self):
        """
        设置报警阈值
        
        从 UI 获取加速度阈值和倾角阈值，
        调用 NetworkManager 发送 SET:AGT 命令。
        """
        try:
            # 从 UI 获取阈值
            accel_str = self.ui_manager.get_entry_value('alarm_accel_threshold')
            gyro_str = self.ui_manager.get_entry_value('alarm_gyro_threshold')
            
            # 转换为浮点数
            try:
                accel_threshold = float(accel_str)
                gyro_threshold = float(gyro_str)
            except ValueError:
                self.log_message("Error: Invalid threshold values")
                return
            
            # 调用 NetworkManager 设置阈值
            if hasattr(self, 'network_manager'):
                success = self.network_manager.set_alarm_threshold(
                    accel_threshold, gyro_threshold
                )
                if success:
                    self.log_message(f"Setting alarm threshold: Accel={accel_threshold} m/s², Gyro={gyro_threshold}°")
            else:
                self.log_message("Error: NetworkManager not available")
                
        except Exception as e:
            self.log_message(f"Error setting alarm threshold: {str(e)}")
    
    def restart_sensor(self):
        """
        重启传感器
        
        发送 SS:9 命令重启传感器设备。
        """
        try:
            if hasattr(self, 'serial_manager'):
                success = self.serial_manager.send_ss9_restart_sensor()
                if success:
                    self.log_message("Sent restart command to sensor (SS:9)")
            else:
                self.log_message("Error: SerialManager not available")
        except Exception as e:
            self.log_message(f"Error restarting sensor: {str(e)}")
    
    def save_config(self):
        """
        保存配置到传感器
        
        发送 SS:7 命令让传感器保存当前配置。
        """
        try:
            if hasattr(self, 'serial_manager'):
                success = self.serial_manager.send_ss7_save_config()
                if success:
                    self.log_message("Sent save config command to sensor (SS:7)")
            else:
                self.log_message("Error: SerialManager not available")
        except Exception as e:
            self.log_message(f"Error saving config: {str(e)}")
    
    def copy_activation_key(self):
        """
        复制激活密钥片段到剪贴板
        
        复制7字符密钥片段（generated_key[5:12]）到系统剪贴板。
        """
        try:
            if self.generated_key and len(self.generated_key) >= 12:
                # 提取7字符片段（与 SET:AKY 命令使用的片段一致）
                key_fragment = self.generated_key[5:12]
                # 复制到剪贴板
                self.root.clipboard_clear()
                self.root.clipboard_append(key_fragment)
                self.log_message(f"Activation key fragment copied to clipboard: {key_fragment}")
            else:
                self.log_message("Error: No activation key available to copy")
        except Exception as e:
            self.log_message(f"Error copying activation key: {str(e)}")

    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log_message("程序被用户中断")
        except Exception as e:
            self.log_message(f"程序发生错误: {str(e)}")
        finally:
            if not self.exiting:
                self.cleanup()

    def __del__(self):
        """析构函数，确保资源被清理"""
        if not self.exiting:
            self.cleanup()


# 运行程序
if __name__ == "__main__":
    app = StableSensorCalibrator()
    try:
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
