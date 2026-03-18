"""
SensorCalibrator Application Core

主应用类，整合所有组件并管理应用生命周期。
"""

import math
import threading
import json
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, StringVar, messagebox, filedialog
from datetime import datetime
from typing import Optional, Dict

from ..config import Config, UIConfig, CalibrationConfig
from ..data_buffer import SensorDataBuffer as DataProcessor
from ..serial_manager import SerialManager
from ..network_manager import NetworkManager
from ..calibration_workflow import CalibrationWorkflow
from ..activation_workflow import ActivationWorkflow
from ..chart_manager import ChartManager
from ..ui_manager import UIManager
from ..ring_buffer import QueueAdapter, RingBuffer
from ..log_throttler import LogThrottler
from .callbacks import AppCallbacks


class SensorCalibratorApp:
    """
    MPU6050 & ADXL355 传感器校准应用程序主类。
    
    提供串口通信、数据采集可视化、六位置校准、
    激活验证和网络配置等功能。
    """
    
    def __init__(self):
        """初始化应用程序状态和所有组件。"""
        # 初始化所有变量
        self.ser = None
        self.is_reading = False
        
        # 数据队列
        self.data_queue = QueueAdapter(capacity=Config.MAX_QUEUE_SIZE)
        self.update_interval = Config.UPDATE_INTERVAL_MS

        # 数据处理器
        self.data_processor = DataProcessor()
        
        # 统计数据
        self.serial_freq = 0
        self.last_freq_update = time.time()
        self.packets_received = 0
        self.stats_window_size = Config.STATS_WINDOW_SIZE
        self.real_time_stats = self.data_processor.get_statistics()

        # 传感器属性
        self.sensor_properties = {}
        self.mac_address = None
        self.generated_key = None
        self.sensor_activated = False
        self._aky_from_ss13 = None  # SS:13 读取的激活密钥

        # 校准状态
        self.is_calibrating = False
        self.current_position = 0
        self.calibration_params = {
            "mpu_accel_scale": [1.0, 1.0, 1.0],
            "mpu_accel_offset": [0.0, 0.0, 0.0],
            "adxl_accel_scale": [1.0, 1.0, 1.0],
            "adxl_accel_offset": [0.0, 0.0, 0.0],
            "mpu_gyro_offset": [0.0, 0.0, 0.0],
        }
        self.position_names = CalibrationConfig.POSITION_NAMES

        # 网络配置
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
            "URL4": "",
        }

        # 文件路径
        self.calibration_file = Config.DEFAULT_CALIBRATION_FILE
        self.properties_file = Config.DEFAULT_PROPERTIES_FILE

        # 退出标志
        self.exiting = False
        self.after_tasks = []

        # 性能优化
        self.last_stats_update = 0
        self.stats_update_interval = Config.STATS_UPDATE_INTERVAL
        self.log_throttler: Optional[LogThrottler] = None
        
        # 窗口移动检测
        self._window_moving = False
        self._window_move_timer = None
        self._last_window_pos = None
        self._window_configure_count = 0
        
        # 图表管理器
        self.chart_manager: Optional[ChartManager] = None
        self.canvas = None
        
        # tkinter 变量和组件
        self.root: Optional[tk.Tk] = None
        self.port_var: Optional[StringVar] = None
        self.baud_var: Optional[StringVar] = None
        self.freq_var: Optional[StringVar] = None
        self.mac_var: Optional[StringVar] = None
        self.position_var: Optional[StringVar] = None
        self.log_text: Optional[scrolledtext.ScrolledText] = None
        self.cmd_text: Optional[scrolledtext.ScrolledText] = None
        
        # UI 组件引用
        self.port_combo = None
        self.connect_btn = None
        self.refresh_btn = None
        self.data_btn = None
        self.data_btn2 = None
        self.calibrate_btn = None
        self.capture_btn = None
        self.send_btn = None
        self.save_btn = None
        self.read_props_btn = None
        self.read_device_btn = None
        self.resend_btn = None
        self.stats_labels: Dict[str, Optional[StringVar]] = {}
        
        # 线程
        self.serial_thread = None
        
        # 子组件
        self.ui_manager = None
        self.serial_manager = None
        self.network_manager = None
        self.calibration_workflow = None
        self.activation_workflow = None
        
        # 回调函数字典
        self.ui_callbacks = None
        
        # 布局引用
        self.scrollable_frame = None
        self.right_panel = None
        
        # 图表轴
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.ax4 = None
        self.fig = None

    def setup(self):
        """设置GUI和初始化所有组件"""
        self._setup_dpi()
        self._create_root_window()
        self._setup_layout()
        self._init_components()
        self.refresh_ports()

    def _setup_dpi(self):
        """设置DPI感知"""
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except (ImportError, AttributeError, OSError):
            pass

    def _create_root_window(self):
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.tk.call("tk", "scaling", UIConfig.SCALING_FACTOR)
        self.root.title(UIConfig.TITLE)
        self.root.geometry(f"{UIConfig.WINDOW_WIDTH}x{UIConfig.WINDOW_HEIGHT}")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_layout(self):
        """设置布局"""
        # 绑定窗口移动事件
        if Config.ENABLE_WINDOW_MOVE_PAUSE:
            self.root.bind("<Configure>", self._on_window_configure)
            if self.root:
                self._last_window_pos = (self.root.winfo_x(), self.root.winfo_y())

        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 左侧面板
        left_panel = ttk.Frame(main_frame, width=UIConfig.LEFT_PANEL_WIDTH)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # 配置左侧面板网格
        left_panel.grid_rowconfigure(0, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # 创建可滚动的左侧面板
        canvas = tk.Canvas(left_panel, highlightthickness=0, width=UIConfig.LEFT_PANEL_WIDTH)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, width=UIConfig.LEFT_PANEL_WIDTH, bg='#f8f9fa')

        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=430)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 右侧图表区域
        self.right_panel = ttk.Frame(main_frame)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # 底部输出区域
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
            log_frame, height=8, font=("Courier", 9)
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
            cmd_frame, height=8, font=("Courier", 9)
        )
        self.cmd_text.grid(row=0, column=0, sticky="nsew")

    def _init_components(self):
        """初始化所有子组件"""
        # 初始化日志限流器
        self.log_throttler = LogThrottler(interval_ms=100, max_buffer_size=50)
        self.log_throttler.set_log_function(self._do_log_message)

        # 初始化UI管理器
        self._setup_ui_manager()

        # 初始化图表管理器
        self._setup_chart_manager()

        # 初始化串口管理器
        self._init_serial_manager()

        # 初始化网络管理器
        self._init_network_manager()

        # 初始化校准工作流
        self._init_calibration_workflow()

        # 初始化激活工作流
        self._init_activation_workflow()

    def _setup_ui_manager(self):
        """设置UI管理器"""
        # 创建 AppCallbacks 实例
        self.ui_callbacks = AppCallbacks(self)
        
        # 使用 CallbackRegistry 获取所有回调
        callbacks = self.ui_callbacks.callbacks
        
        # 初始化 UIManager
        self.ui_manager = UIManager(self.scrollable_frame, callbacks)
        
        # 绑定 UI 变量引用
        self._bind_ui_variables()
        
        # 绑定 UI 控件引用
        self._bind_ui_widgets()
    
    def _bind_ui_variables(self):
        """绑定 UI 变量引用"""
        # 串口设置变量
        self.port_var = self.ui_manager.vars.get('port')
        self.baud_var = self.ui_manager.vars.get('baud')
        self.freq_var = self.ui_manager.vars.get('freq')
        
        # Dashboard 状态变量
        self.connection_status_var = self.ui_manager.vars.get('connection_status')
        self.stream_status_var = self.ui_manager.vars.get('stream_status')
        self.dashboard_calibration_status_var = self.ui_manager.vars.get('calibration_status')
        
        # 校准位置变量
        self.position_var = self.ui_manager.vars.get('position')
        
        # 激活相关变量
        self.mac_var = self.ui_manager.vars.get('activation_mac')
        self.key_var = self.ui_manager.vars.get('activation_key')
        
        # 校准状态变量
        self.calibration_status_var = self.ui_manager.vars.get('calibration_status')
        
        # WiFi 配置变量
        self.ssid_var = self.ui_manager.vars.get('ssid')
        self.password_var = self.ui_manager.vars.get('password')
        
        # MQTT 配置变量
        self.mqtt_broker_var = self.ui_manager.vars.get('mqtt_broker')
        self.mqtt_user_var = self.ui_manager.vars.get('mqtt_user')
        self.mqtt_password_var = self.ui_manager.vars.get('mqtt_password')
        self.mqtt_port_var = self.ui_manager.vars.get('mqtt_port')
        
        # OTA 配置变量
        self.URL1_var = self.ui_manager.vars.get('url1')
        self.URL2_var = self.ui_manager.vars.get('url2')
        
        # 记录变量绑定情况（调试用）
        self.log_message("DEBUG: UI Variables bound:")
        self.log_message(f"  mac_var: {'OK' if self.mac_var else 'None'}")
        self.log_message(f"  key_var: {'OK' if self.key_var else 'None'}")
        self.log_message(f"  ssid_var: {'OK' if self.ssid_var else 'None'}")
        self.log_message(f"  mqtt_broker_var: {'OK' if self.mqtt_broker_var else 'None'}")
        self.URL3_var = self.ui_manager.vars.get('url3')
        self.URL4_var = self.ui_manager.vars.get('url4')
    
    def _bind_ui_widgets(self):
        """绑定 UI 控件引用"""
        # 串口相关控件
        self.port_combo = self.ui_manager.widgets.get('port_combo')
        self.connect_btn = self.ui_manager.widgets.get('connect_btn')
        self.refresh_btn = self.ui_manager.widgets.get('refresh_btn')
        
        # 数据流控件
        self.data_btn = self.ui_manager.widgets.get('data_btn')
        self.data_btn2 = self.ui_manager.widgets.get('data_btn2')
        self.widgets_freq_label = self.ui_manager.widgets.get('freq_label')
        
        # 校准控件
        self.calibrate_btn = self.ui_manager.widgets.get('calibrate_btn')
        self.capture_btn = self.ui_manager.widgets.get('capture_btn')
        
        # 命令控件
        self.send_btn = self.ui_manager.widgets.get('send_btn')
        self.save_btn = self.ui_manager.widgets.get('save_btn')
        self.read_props_btn = self.ui_manager.widgets.get('read_props_btn')
        self.read_device_btn = self.ui_manager.widgets.get('read_device_btn')
        self.resend_btn = self.ui_manager.widgets.get('resend_btn')
        
        # 坐标模式控件
        self.local_coord_btn = self.ui_manager.widgets.get('local_coord_btn')
        self.global_coord_btn = self.ui_manager.widgets.get('global_coord_btn')
        
        # 网络配置控件
        self.set_wifi_btn = self.ui_manager.widgets.get('set_wifi_btn')
        self.read_wifi_btn = self.ui_manager.widgets.get('read_wifi_btn')
        self.set_mqtt_btn = self.ui_manager.widgets.get('set_mqtt_btn')
        self.read_mqtt_btn = self.ui_manager.widgets.get('read_mqtt_btn')
        self.set_ota_btn = self.ui_manager.widgets.get('set_ota_btn')
        self.read_ota_btn = self.ui_manager.widgets.get('read_ota_btn')
        
        # 报警阈值控件
        self.set_alarm_threshold_btn = self.ui_manager.widgets.get('set_alarm_threshold_btn')
        self.save_config_btn = self.ui_manager.widgets.get('save_config_btn')
        self.restart_sensor_btn = self.ui_manager.widgets.get('restart_sensor_btn')
        
        # 激活状态控件
        self.activation_status_var = self.ui_manager.vars.get('activation_status')
        self.activation_status_label = self.ui_manager.widgets.get('activation_status_label')
        self.activate_btn = self.ui_manager.widgets.get('activate_btn')
        
        # 校准状态控件
        self.calibration_status_label = self.ui_manager.widgets.get('calibration_status_label')
        
        # 统计标签变量
        self.stats_labels = {
            'mpu_accel_x_mean': self.ui_manager.vars.get('mpu_accel_x_mean'),
            'mpu_accel_x_std': self.ui_manager.vars.get('mpu_accel_x_std'),
            'mpu_accel_y_mean': self.ui_manager.vars.get('mpu_accel_y_mean'),
            'mpu_accel_y_std': self.ui_manager.vars.get('mpu_accel_y_std'),
            'mpu_accel_z_mean': self.ui_manager.vars.get('mpu_accel_z_mean'),
            'mpu_accel_z_std': self.ui_manager.vars.get('mpu_accel_z_std'),
            'adxl_accel_x_mean': self.ui_manager.vars.get('adxl_accel_x_mean'),
            'adxl_accel_x_std': self.ui_manager.vars.get('adxl_accel_x_std'),
            'adxl_accel_y_mean': self.ui_manager.vars.get('adxl_accel_y_mean'),
            'adxl_accel_y_std': self.ui_manager.vars.get('adxl_accel_y_std'),
            'adxl_accel_z_mean': self.ui_manager.vars.get('adxl_accel_z_mean'),
            'adxl_accel_z_std': self.ui_manager.vars.get('adxl_accel_z_std'),
            'mpu_gyro_x_mean': self.ui_manager.vars.get('mpu_gyro_x_mean'),
            'mpu_gyro_x_std': self.ui_manager.vars.get('mpu_gyro_x_std'),
            'mpu_gyro_y_mean': self.ui_manager.vars.get('mpu_gyro_y_mean'),
            'mpu_gyro_y_std': self.ui_manager.vars.get('mpu_gyro_y_std'),
            'mpu_gyro_z_mean': self.ui_manager.vars.get('mpu_gyro_z_mean'),
            'mpu_gyro_z_std': self.ui_manager.vars.get('mpu_gyro_z_std'),
            'gravity_mean': self.ui_manager.vars.get('gravity_mean'),
            'gravity_std': self.ui_manager.vars.get('gravity_std'),
        }

    def _setup_chart_manager(self):
        """设置图表管理器"""
        # 初始化 ChartManager
        self.chart_manager = ChartManager(self.right_panel, figsize=(14, 9))
        
        # 设置图表
        self.chart_manager.setup_plots()
        self.canvas = self.chart_manager.canvas
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # 保存图表引用
        self.fig = self.chart_manager.fig
        self.ax1 = self.chart_manager.ax1
        self.ax2 = self.chart_manager.ax2
        self.ax3 = self.chart_manager.ax3
        self.ax4 = self.chart_manager.ax4

    def _init_serial_manager(self):
        """初始化串口管理器"""
        callbacks = {
            'log_message': self.log_message,
            'get_data_queue': lambda: self.data_queue,
            'update_connection_state': self._on_connection_state_changed,
        }
        self.serial_manager = SerialManager(callbacks)
        self.ser = None

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
        self.network_manager.wifi_params = self.wifi_params
        self.network_manager.mqtt_params = self.mqtt_params
        self.network_manager.ota_params = self.ota_params

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
            'send_line': lambda cmd: self.serial_manager.send_line(cmd),
        }
        self.activation_workflow = ActivationWorkflow(callbacks)

    def refresh_ports(self):
        """刷新可用串口列表"""
        ports = SerialManager.list_available_ports()
        port_combo = self.ui_manager.widgets.get('port_combo') if self.ui_manager else None
        if port_combo:
            port_combo["values"] = ports
            if ports:
                port_combo.current(0)

    def _do_log_message(self, log_entry):
        """实际执行日志输出的内部方法"""
        if self.root and self.root.winfo_exists():
            try:
                self.root.after(0, lambda: self._add_log_entry(log_entry))
            except Exception:
                pass

    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        if self.log_throttler:
            self.log_throttler.log(log_entry, level)

    def _add_log_entry(self, log_entry):
        """在主线程中添加日志条目"""
        try:
            if self.log_text and self.log_text.winfo_exists():
                self.log_text.insert(tk.END, log_entry + "\n")
                self.log_text.see(tk.END)
        except Exception:
            pass

    def _on_connection_state_changed(self, connected: bool, user_initiated: bool = False):
        """
        串口连接状态变化回调
        
        Args:
            connected: 是否已连接
            user_initiated: 是否为用户主动断开（点击 Disconnect 按钮）
        """
        # 如果程序正在退出，不处理连接状态变化
        if self.exiting:
            return
            
        if connected:
            self.ser = self.serial_manager.serial_port
            # 更新 Dashboard 连接状态
            if hasattr(self, 'connection_status_var') and self.connection_status_var:
                self.connection_status_var.set("Connected")
        else:
            self.ser = None
            # 更新 Dashboard 连接状态
            if hasattr(self, 'connection_status_var') and self.connection_status_var:
                self.connection_status_var.set("Disconnected")
            # 更新 Dashboard 数据流状态
            if hasattr(self, 'stream_status_var') and self.stream_status_var:
                self.stream_status_var.set("Stopped")
            # 如果不是用户主动断开（异常断连）且程序未在退出，显示弹窗
            if not user_initiated and not self.exiting:
                # 使用 after 确保在主线程显示弹窗
                if self.root:
                    self.root.after(0, self._show_device_disconnected_dialog)

    def _on_position_captured(self, next_position: int):
        """位置采集完成回调"""
        self.current_position = next_position
        if self.capture_btn:
            self.capture_btn.config(state="normal")
        self.update_position_display()

    def _on_calibration_finished(self, params: dict):
        """校准完成回调"""
        self.calibration_params = params
        if self.calibrate_btn:
            self.calibrate_btn.config(state="normal")
        if self.capture_btn:
            self.capture_btn.config(state="disabled")
        if self.data_btn:
            self.data_btn.config(state="normal")
        if self.position_var:
            self.position_var.set("Calibration complete!")
        
        # 生成校准命令并显示在命令文本框中
        commands = self.calibration_workflow.generate_calibration_commands()
        if self.cmd_text:
            self.cmd_text.delete(1.0, "end")
            for cmd in commands:
                self.cmd_text.insert("end", cmd + "\n")
        
        # 启用发送和保存按钮
        if self.send_btn:
            self.send_btn.config(state="normal")
        if self.save_btn:
            self.save_btn.config(state="normal")
        
        self.log_message("Calibration finished successfully!")
        self.log_message("Calibration commands generated. Click 'Send Commands' to upload to device.")

    def _on_calibration_error(self):
        """校准错误回调"""
        self.reset_calibration_state()

    def _on_capture_error(self):
        """采集错误回调"""
        if self.capture_btn:
            self.capture_btn.config(state="normal")

    def _on_wifi_config_loaded(self, params: dict):
        """WiFi配置加载回调"""
        self.wifi_params = params
        # 更新UI变量
        if self.ssid_var and params.get('ssid'):
            self.ssid_var.set(params.get('ssid', ''))
            self.password_var.set(params.get('password', ''))

    def _on_mqtt_config_loaded(self, params: dict):
        """MQTT配置加载回调"""
        self.mqtt_params = params
        # 更新UI变量
        if self.mqtt_broker_var and params.get('broker'):
            self.mqtt_broker_var.set(params.get('broker', ''))
            self.mqtt_user_var.set(params.get('username', ''))
            self.mqtt_password_var.set(params.get('password', ''))
            self.mqtt_port_var.set(params.get('port', '1883'))

    def run(self):
        """运行应用程序"""
        try:
            if self.root:
                self.root.mainloop()
        except KeyboardInterrupt:
            self.log_message("程序被用户中断")
        except Exception as e:
            self.log_message(f"程序发生错误: {str(e)}")
        finally:
            if not self.exiting:
                self.cleanup()

    def cleanup(self):
        """清理资源，确保安全退出"""
        if hasattr(self, "_cleaned"):
            return

        self._cleaned = True
        self.log_message("正在清理资源，准备退出...")

        # 取消所有after任务
        self.cancel_all_after_tasks()

        # 停止数据流
        if self.is_reading:
            self.stop_data_stream_safe()

        # 关闭串口
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                self.log_message("串口已关闭")
            except Exception as e:
                self.log_message(f"关闭串口时出错: {str(e)}")

        # 停止所有子线程
        self.stop_all_threads()

        # 清理matplotlib资源
        if self.fig:
            try:
                import matplotlib.pyplot as plt
                plt.close(self.fig)
            except (ValueError, AttributeError):
                pass
            finally:
                self.fig = None

        self.log_message("清理完成，程序即将退出")

    def cancel_all_after_tasks(self):
        """取消所有after任务"""
        if not self.root:
            return
            
        for task_id in list(self.after_tasks):
            try:
                self.root.after_cancel(task_id)
            except tk.TclError:
                pass
        self.after_tasks.clear()
        
        if self._window_move_timer:
            try:
                self.root.after_cancel(self._window_move_timer)
            except tk.TclError:
                pass
            finally:
                self._window_move_timer = None

    def _on_window_configure(self, event):
        """窗口移动/调整大小事件处理"""
        try:
            if not self.root or not self.root.winfo_exists():
                return
            
            current_pos = (self.root.winfo_x(), self.root.winfo_y())
            
            if not hasattr(self, '_last_window_pos'):
                self._last_window_pos = current_pos
                return
            
            if current_pos == self._last_window_pos:
                return
            
            self._last_window_pos = current_pos
            self._window_moving = True
            self._window_configure_count += 1
            
            if self._window_move_timer and self.root:
                try:
                    self.root.after_cancel(self._window_move_timer)
                except tk.TclError:
                    pass
            
            if self.root:
                try:
                    self._window_move_timer = self.root.after(
                        Config.WINDOW_MOVE_PAUSE_DELAY,
                        self._on_window_move_end
                    )
                except tk.TclError:
                    pass
        except Exception:
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
            if self.ser and self.ser.is_open:
                self.send_ss4_stop_stream()

            if self.data_btn:
                self.data_btn.config(text="Start Data Stream")
            if self.calibrate_btn:
                self.calibrate_btn.config(state="disabled")
            if self.capture_btn:
                self.capture_btn.config(state="disabled")

            self.log_message("数据流已停止")
        except Exception as e:
            self.log_message(f"停止数据流时出错: {str(e)}")

    def stop_all_threads(self):
        """停止所有活动的线程"""
        self.exiting = True

        if self.serial_thread and self.serial_thread.is_alive():
            start_time = time.time()
            while (
                time.time() - start_time < 2.0
                and self.serial_thread.is_alive()
            ):
                time.sleep(0.1)

        if self.data_queue:
            try:
                while not self.data_queue.empty():
                    try:
                        self.data_queue.get_nowait()
                    except Exception as e:
                        self.log_message(f"Error processing data packet: {e}", "ERROR")
                        break
            except Exception:
                pass

        if hasattr(self, "data_processor"):
            self.data_processor.clear_all()

    def on_closing(self):
        """窗口关闭事件处理"""
        if self.root:
            response = messagebox.askyesno(
                "退出程序", "确定要退出程序吗？\n\n所有未保存的数据将丢失。"
            )
            if response:
                self.exiting = True
                self.cleanup()
                if self.root:
                    delay_ms = int(Config.SERIAL_CLEANUP_DELAY * 1000)
                    self.root.after(delay_ms, self._do_destroy)

    def _do_destroy(self):
        """执行实际的窗口销毁"""
        if self.root:
            self.root.destroy()

    def schedule_update_gui(self):
        """调度GUI更新"""
        if not self.exiting and self.root and self.root.winfo_exists():
            try:
                task_id = self.root.after(self.update_interval, self.update_gui)
                self.after_tasks.append(task_id)
            except Exception:
                pass

    def _collect_data_batch(self) -> list:
        """
        批量收集数据队列中的数据
        
        Returns:
            数据字符串列表
        """
        batch = []
        try:
            while (not self.data_queue.empty() and 
                   len(batch) < Config.MAX_GUI_UPDATE_BATCH):
                try:
                    data_string = self.data_queue.get_nowait()
                    batch.append(data_string)
                except Exception:
                    break
        except Exception:
            pass
        return batch

    def _process_data_batch(self, batch: list) -> None:
        """
        批量处理数据 - 优化版本
        
        优化点：
        - 批量解析数据
        - 批量追加到缓冲区（减少锁获取次数）
        
        Args:
            batch: 数据字符串列表
        """
        if not batch:
            return
        
        # 批量解析
        parsed_data = []
        for data_string in batch:
            mpu_accel, mpu_gyro, adxl_accel = self.parse_sensor_data(data_string)
            if mpu_accel and mpu_gyro and adxl_accel:
                parsed_data.append((mpu_accel, mpu_gyro, adxl_accel))
        
        if not parsed_data:
            return
        
        # 初始化时间基准
        if self.data_processor.data_start_time is None:
            self.data_processor.data_start_time = time.time()
        
        # 批量准备数据
        batch_size = len(parsed_data)
        start_packet = self.data_processor.packet_count
        
        # 准备所有时间戳和数据
        time_values = []
        mpu_accel_values = [[] for _ in range(3)]
        mpu_gyro_values = [[] for _ in range(3)]
        adxl_accel_values = [[] for _ in range(3)]
        gravity_values = []
        
        for i, (mpu_accel, mpu_gyro, adxl_accel) in enumerate(parsed_data):
            current_relative_time = (start_packet + i) / self.data_processor.expected_frequency
            time_values.append(current_relative_time)
            
            for j in range(3):
                mpu_accel_values[j].append(mpu_accel[j])
                mpu_gyro_values[j].append(mpu_gyro[j])
                adxl_accel_values[j].append(adxl_accel[j])
            
            gravity_mag = math.sqrt(
                mpu_accel[0] ** 2 +
                mpu_accel[1] ** 2 +
                mpu_accel[2] ** 2
            )
            gravity_values.append(gravity_mag)
        
        # 批量追加到缓冲区（使用内部属性直接访问）
        # 注意：使用 _time_data 而不是 time_data property，避免返回副本
        self.data_processor._time_data.extend(time_values)
        for i in range(3):
            self.data_processor._mpu_accel_data[i].extend(mpu_accel_values[i])
            self.data_processor._mpu_gyro_data[i].extend(mpu_gyro_values[i])
            self.data_processor._adxl_accel_data[i].extend(adxl_accel_values[i])
        self.data_processor._gravity_mag_data.extend(gravity_values)
        
        # 更新数据版本号，使统计缓存失效（关键修复！）
        self.data_processor._data_version += 1
        self.data_processor._stats_valid = False
        
        # 更新包计数（同时更新 UI 频率计数和处理器计数）
        self.data_processor.packet_count += batch_size
        self.packets_received += batch_size

    def update_gui(self):
        """更新GUI - 主更新循环"""
        if self.exiting or not self.root or not self.root.winfo_exists():
            return
        
        if Config.ENABLE_WINDOW_MOVE_PAUSE and self._window_moving:
            self.schedule_update_gui()
            return
        
        try:
            current_time = time.time()
            if current_time - self.last_freq_update >= 1.0:
                self.serial_freq = self.packets_received
                self.packets_received = 0
                self.last_freq_update = current_time
                if self.freq_var:
                    self.freq_var.set(f"{self.serial_freq} Hz")

            if hasattr(self, "data_queue"):
                # 优化：批量处理数据（减少锁获取次数和函数调用开销）
                batch = self._collect_data_batch()
                if batch:
                    self._process_data_batch(batch)

                if current_time - self.last_stats_update >= self.stats_update_interval:
                    self.safe_update_statistics()
                    self.last_stats_update = current_time

                if not self.exiting:
                    self.update_charts()

                self.schedule_update_gui()

        except Exception as e:
            if not self.exiting:
                self.log_message(f"GUI update error: {str(e)}")

    def safe_update_statistics(self):
        """安全的统计信息更新"""
        try:
            self.update_statistics()
        except Exception as e:
            self.log_message(f"Error updating statistics: {str(e)}")

    def update_statistics(self):
        """更新统计信息"""
        if not self.data_processor.has_data():
            return
        
        self.data_processor.update_statistics()
        self.real_time_stats = self.data_processor.get_statistics()
        
        # 更新UI显示
        if not self.stats_labels:
            return
        
        axis_names = ["x", "y", "z"]
        
        # 更新MPU6050加速度计统计
        for i in range(3):
            mean_val = self.real_time_stats["mpu_accel_mean"][i]
            std_val = self.real_time_stats["mpu_accel_std"][i]
            mean_key = f"mpu_accel_{axis_names[i]}_mean"
            std_key = f"mpu_accel_{axis_names[i]}_std"
            
            if mean_key in self.stats_labels and self.stats_labels[mean_key]:
                self.stats_labels[mean_key].set(f"μ: {mean_val:6.3f}")
            if std_key in self.stats_labels and self.stats_labels[std_key]:
                self.stats_labels[std_key].set(f"σ: {std_val:6.3f}")
        
        # 更新ADXL355加速度计统计
        for i in range(3):
            mean_val = self.real_time_stats["adxl_accel_mean"][i]
            std_val = self.real_time_stats["adxl_accel_std"][i]
            mean_key = f"adxl_accel_{axis_names[i]}_mean"
            std_key = f"adxl_accel_{axis_names[i]}_std"
            
            if mean_key in self.stats_labels and self.stats_labels[mean_key]:
                self.stats_labels[mean_key].set(f"μ: {mean_val:6.3f}")
            if std_key in self.stats_labels and self.stats_labels[std_key]:
                self.stats_labels[std_key].set(f"σ: {std_val:6.3f}")
        
        # 更新MPU6050陀螺仪统计
        for i in range(3):
            mean_val = self.real_time_stats["mpu_gyro_mean"][i]
            std_val = self.real_time_stats["mpu_gyro_std"][i]
            mean_key = f"mpu_gyro_{axis_names[i]}_mean"
            std_key = f"mpu_gyro_{axis_names[i]}_std"
            
            if mean_key in self.stats_labels and self.stats_labels[mean_key]:
                self.stats_labels[mean_key].set(f"μ: {mean_val:6.3f}")
            if std_key in self.stats_labels and self.stats_labels[std_key]:
                self.stats_labels[std_key].set(f"σ: {std_val:6.3f}")
        
        # 更新重力矢量统计
        mean_val = self.real_time_stats["gravity_mean"]
        std_val = self.real_time_stats["gravity_std"]
        
        if "gravity_mean" in self.stats_labels and self.stats_labels["gravity_mean"]:
            self.stats_labels["gravity_mean"].set(f"Mean: {mean_val:6.3f}")
        if "gravity_std" in self.stats_labels and self.stats_labels["gravity_std"]:
            self.stats_labels["gravity_std"].set(f"Std: {std_val:6.3f}")

    def update_charts(self):
        """更新图表"""
        if self.exiting or not self.chart_manager or not self.data_processor.has_data():
            return
        
        data_dict = self.data_processor.get_display_data()
        updated = self.chart_manager.update_charts(data_dict)
        
        if updated:
            # 计算图表显示数据的统计信息（与图表显示窗口一致）
            stats_dict = self._calculate_chart_stats(data_dict)
            self.chart_manager.update_statistics_text(stats_dict)

    def parse_sensor_data(self, data_string):
        """解析传感器数据"""
        return DataProcessor.parse_sensor_data(data_string)

    def clear_data(self):
        """清空所有数据"""
        self.data_processor.clear_all()

    def _calculate_chart_stats(self, data_dict: dict) -> dict:
        """
        计算图表显示数据的统计信息
        
        与图表显示使用相同的数据窗口，确保统计信息与图表显示一致
        
        Args:
            data_dict: 包含显示数据的字典
            
        Returns:
            包含统计信息的字典
        """
        import numpy as np
        
        # 获取数据
        mpu_accel = data_dict.get('mpu_accel', [[], [], []])
        adxl_accel = data_dict.get('adxl_accel', [[], [], []])
        mpu_gyro = data_dict.get('mpu_gyro', [[], [], []])
        gravity = data_dict.get('gravity', [])
        
        # 如果启用了降采样，图表实际显示的数据可能更少
        # 我们需要计算图表实际显示的数据的统计信息
        time_data = data_dict.get('time', [])
        if not time_data:
            return self._get_empty_chart_stats()
        
        # 确定实际显示的数据点数（与 chart_manager 逻辑一致）
        display_points = len(time_data)
        if Config.ENABLE_DATA_DECIMATION and len(time_data) > Config.DISPLAY_DATA_POINTS * 2:
            # 降采样后的数据点数
            decimation = Config.CHART_DECIMATION_FACTOR
            display_points = len(time_data[::decimation])
        
        # 计算最近显示数据的统计信息（使用最后 min(STATS_WINDOW_SIZE, display_points) 个）
        window_size = min(Config.STATS_WINDOW_SIZE, display_points)
        
        stats_dict = {
            'window_size': window_size,
            'mpu_accel_mean': [0.0, 0.0, 0.0],
            'mpu_accel_std': [0.0, 0.0, 0.0],
            'adxl_accel_mean': [0.0, 0.0, 0.0],
            'adxl_accel_std': [0.0, 0.0, 0.0],
            'mpu_gyro_mean': [0.0, 0.0, 0.0],
            'mpu_gyro_std': [0.0, 0.0, 0.0],
            'gravity_mean': 0.0,
            'gravity_std': 0.0,
        }
        
        # 计算各通道统计
        for i in range(3):
            if len(mpu_accel[i]) >= window_size:
                data = mpu_accel[i][-window_size:]
                stats_dict['mpu_accel_mean'][i] = float(np.mean(data))
                stats_dict['mpu_accel_std'][i] = float(np.std(data))
            
            if len(adxl_accel[i]) >= window_size:
                data = adxl_accel[i][-window_size:]
                stats_dict['adxl_accel_mean'][i] = float(np.mean(data))
                stats_dict['adxl_accel_std'][i] = float(np.std(data))
            
            if len(mpu_gyro[i]) >= window_size:
                data = mpu_gyro[i][-window_size:]
                stats_dict['mpu_gyro_mean'][i] = float(np.mean(data))
                stats_dict['mpu_gyro_std'][i] = float(np.std(data))
        
        if len(gravity) >= window_size:
            data = gravity[-window_size:]
            stats_dict['gravity_mean'] = float(np.mean(data))
            stats_dict['gravity_std'] = float(np.std(data))
        
        return stats_dict
    
    def _get_empty_chart_stats(self) -> dict:
        """返回空的图表统计信息"""
        return {
            'window_size': 0,
            'mpu_accel_mean': [0.0, 0.0, 0.0],
            'mpu_accel_std': [0.0, 0.0, 0.0],
            'adxl_accel_mean': [0.0, 0.0, 0.0],
            'adxl_accel_std': [0.0, 0.0, 0.0],
            'mpu_gyro_mean': [0.0, 0.0, 0.0],
            'mpu_gyro_std': [0.0, 0.0, 0.0],
            'gravity_mean': 0.0,
            'gravity_std': 0.0,
        }

    def send_ss0_start_stream(self):
        """发送 SS:0 指令 - 开始数据流"""
        return self.serial_manager.send_ss0_start_stream()

    def send_ss8_get_properties(self):
        """发送 SS:8 指令 - 获取传感器属性"""
        return self.serial_manager.send_ss8_get_properties()

    def check_activation_status(self) -> bool:
        """检查传感器激活状态"""
        if not self.sensor_properties:
            return False

        is_activated = self.activation_workflow.check_activation_status(
            self.sensor_properties,
            mac_address=self.mac_address
        )
        self.sensor_activated = is_activated
        return is_activated

    def update_activation_status(self, activated=None):
        """更新激活状态显示
        
        Args:
            activated: 可选参数，如果传入则使用该值，否则使用 self.sensor_activated
        """
        # 如果传入了参数，更新状态
        if activated is not None:
            self.sensor_activated = activated
        
        if self.sensor_activated:
            self.log_message("Sensor activation status: ACTIVATED")
            if self.activation_status_var:
                self.activation_status_var.set("Activated")
            if self.activation_status_label:
                self.activation_status_label.config(foreground="green")
            if self.activate_btn:
                self.activate_btn.config(state="disabled")
        else:
            self.log_message("Sensor activation status: NOT ACTIVATED")
            if self.activation_status_var:
                self.activation_status_var.set("Not Activated")
            if self.activation_status_label:
                self.activation_status_label.config(foreground="red")
            if self.activate_btn and self.mac_address and self.generated_key:
                self.activate_btn.config(state="normal")

    def display_sensor_properties(self):
        """显示传感器属性"""
        if not self.sensor_properties:
            self.log_message("No sensor properties to display")
            return

        # 创建新窗口显示属性
        prop_window = tk.Toplevel(self.root)
        prop_window.title("Sensor Properties")
        prop_window.geometry("800x600")

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
        if "VROOF" in sys_info:
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

    def extract_network_config(self):
        """从传感器属性中提取网络配置"""
        config = self.network_manager.extract_network_config(self.sensor_properties)
        
        if config:
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
        """从传感器属性中提取报警阈值并显示"""
        try:
            threshold_info = self.network_manager.extract_alarm_threshold(
                self.sensor_properties
            )
            
            if threshold_info:
                accel = threshold_info.get('accel_threshold')
                gyro = threshold_info.get('gyro_threshold')
                self.log_message(f"Current alarm threshold - Accel: {accel} m/s², Gyro: {gyro}°")
            else:
                self.log_message("No alarm threshold found in sensor properties")
                
        except Exception as e:
            self.log_message(f"Error extracting alarm threshold: {str(e)}")

    def display_network_summary(self):
        """显示网络配置摘要"""
        self.network_manager.display_network_summary(self.sensor_properties)

    def auto_save_properties(self):
        """自动保存传感器属性"""
        try:
            import json
            save_data = {
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "sensor_properties": self.sensor_properties,
                "calibration_params": self.calibration_params,
            }

            with open(self.properties_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            self.log_message(
                f"Sensor properties automatically saved to: {self.properties_file}"
            )

        except Exception as e:
            self.log_message(f"Error auto-saving properties: {str(e)}")

    def display_activation_info(self):
        """显示激活相关信息"""
        if not self.sensor_properties or not self.mac_address:
            return

        self.log_message("\n" + "=" * 60)
        self.log_message("ACTIVATION INFORMATION")
        self.log_message("=" * 60)
        self.log_message(f"MAC Address: {self.mac_address}")

        if self.generated_key:
            self.log_message(f"Generated Key: {self.generated_key}")

        self.log_message("=" * 60)

    def start_data_stream(self):
        """开始数据流"""
        if not self.serial_manager.is_connected:
            self.log_message("Error: Not connected to serial port!")
            return
            
        if self.serial_manager.send_ss0_start_stream():
            if self.serial_manager.start_reading():
                self.is_reading = True
                # 更新按钮文本
                if self.data_btn:
                    self.data_btn.config(text="Stop Data")
                # 更新 Dashboard 数据流状态
                if hasattr(self, 'stream_status_var') and self.stream_status_var:
                    self.stream_status_var.set("Running")
                self.log_message("Data stream started")
                
                self.clear_data()
                self.data_processor.data_start_time = time.time()
                self.data_processor.packet_count = 0
                self.packets_received = 0
                
                self.schedule_update_gui()

    def stop_data_stream(self):
        """停止数据流"""
        if not self.is_reading:
            return

        self.is_reading = False
        self.serial_manager.stop_reading()
        self.serial_manager.send_ss4_stop_stream()
        # 更新按钮文本
        if self.data_btn:
            self.data_btn.config(text="Start Data")
        # 更新 Dashboard 数据流状态
        if hasattr(self, 'stream_status_var') and self.stream_status_var:
            self.stream_status_var.set("Stopped")
        self.log_message("Data stream stopped")

    def read_sensor_properties(self):
        """读取传感器属性"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        self.log_message("Starting sensor properties reading process...")
        self.log_message(f"Serial port: {self.ser.port}, is_open: {self.ser.is_open}")
        threading.Thread(target=self._read_sensor_properties_thread, daemon=True).start()

    def _parse_keyvalue_response(self, response_str: str):
        """解析key: value格式的响应"""
        import re
        
        try:
            props = {"sys": {}}
            lines = response_str.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                
                # 分割key和value
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # 尝试转换value为适当类型
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value)
                    
                    props["sys"][key] = value
            
            if props["sys"]:
                self.log_message(f"Parsed {len(props['sys'])} properties from key-value format")
                return props
            
            return None
        
        except Exception as e:
            self.log_message(f"Error parsing key-value response: {e}", "WARNING")
            return None

    def read_device_info(self):
        """
        读取校准参数（RACKS, RACOF, GROOF 等）
        通过 SS:13 命令获取
        """
        if not self.serial_manager.is_connected:
            self.log_message("Error: Not connected to serial port!")
            return

        self.log_message("Starting device info reading process...")
        threading.Thread(target=self._read_device_info_thread, daemon=True).start()

    def _read_device_info_thread(self):
        """在线程中读取校准参数"""
        original_reading_state = self.is_reading

        try:
            if self.is_reading:
                self.root.after(0, lambda: self.log_message("Stopping data stream..."))
                self.root.after(0, self.stop_data_stream)
                time.sleep(1.0)

            if self.serial_manager.serial_port:
                self.serial_manager.serial_port.reset_input_buffer()
            time.sleep(0.5)

            self.root.after(0, lambda: self.log_message("Sending SS:13 command for calibration params..."))
            self.serial_manager.serial_port.write(b"SS:13\n")
            self.serial_manager.serial_port.flush()

            time.sleep(1.0)
            response_bytes = b""
            start_time = time.time()
            timeout = 15.0
            json_found = False

            first_data_logged = False
            while time.time() - start_time < timeout:
                if self.serial_manager.serial_port.in_waiting > 0:
                    chunk = self.serial_manager.serial_port.read(self.serial_manager.serial_port.in_waiting)
                    response_bytes += chunk

                    response_str = response_bytes.decode("utf-8", errors="ignore")
                    json_start = response_str.find("{")
                    json_end = response_str.rfind("}")

                    if not first_data_logged:
                        first_data_logged = True
                        self.root.after(0, lambda l=len(response_bytes), s=response_str[:300]: 
                            self.log_message(f"First chunk: {l} bytes, preview: {s}..."))
                        # 调试：显示 json_start 位置
                        self.root.after(0, lambda js=json_start: self.log_message(f"JSON '{{' found at position: {js}"))

                    if json_start != -1 and not json_found:
                        json_found = True
                        self.root.after(0, lambda js=json_start, je=json_end: self.log_message(f"JSON data started at {js}, current end at {je}"))

                    if json_start != -1 and json_end != -1 and json_end > json_start:
                        json_str = response_str[json_start:json_end + 1]

                        try:
                            device_info = json.loads(json_str)
                            self.root.after(0, lambda l=len(json_str): self.log_message(f"Complete JSON received: {l} bytes"))
                            # 保存 AKY（如果有）
                            if "sys" in device_info and "AKY" in device_info["sys"]:
                                aky_value = device_info["sys"]["AKY"]
                                self.root.after(0, lambda a=aky_value: self._save_aky_from_ss13(a))
                            # 使用默认参数正确捕获 device_info 的值
                            self.root.after(0, lambda d=device_info: self._display_device_info(d))
                            return
                        except json.JSONDecodeError as e:
                            self.root.after(0, lambda js=json_start, je=json_end, l=len(response_bytes), err=str(e): 
                                self.log_message(f"JSON parse error: {err}, start={js}, end={je}, total={l} bytes, waiting..."))
                            continue

                time.sleep(0.1)

            # 超时后显示实际接收到的内容，帮助调试
            final_str = response_bytes.decode("utf-8", errors="ignore")
            self.root.after(0, lambda l=len(response_bytes): self.log_message(f"TIMEOUT: Received {l} bytes total"))
            self.root.after(0, lambda s=final_str[:500]: self.log_message(f"Final content preview: {s}..."))
            self.root.after(0, lambda: self.log_message("Hint: SS:13 may not return JSON format. Check actual response above."))

        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Error reading calibration params: {str(e)}"))

        finally:
            if original_reading_state and not self.is_reading:
                self.root.after(0, lambda: self.log_message("Restarting data stream..."))
                time.sleep(1.0)
                self.root.after(0, self.start_data_stream)
            # 注意：校准状态检测现在移到 _display_device_info 中，
            # 确保在 sensor_properties 更新后再检测

    def _display_device_info(self, device_info):
        """显示校准参数（SS:13 返回的是校准参数）"""
        import json
        self.log_message(f"_display_device_info called with data: {type(device_info)}")
        
        if not device_info:
            self.log_message("No device info to display (device_info is None or empty)")
            return
        
        # 打印完整的 device_info 用于调试
        self.log_message(f"DEBUG: Full device_info keys: {list(device_info.keys())}")
        self.log_message(f"DEBUG: Full device_info content:\n{json.dumps(device_info, indent=2)}")
        
        # 保存到 self.sensor_properties，以便后续检测使用
        self.sensor_properties = device_info
        self.log_message(f"DEBUG: Saved device_info to sensor_properties")
        
        # SS:13 返回的数据优先从 "sys" 字段中获取（校准参数在这里）
        # 如果 "sys" 不存在，则尝试 "params" 字段
        if "sys" in device_info:
            sys_info = device_info["sys"]
            self.log_message(f"Using 'sys' field with {len(sys_info)} fields")
        elif "params" in device_info:
            sys_info = device_info["params"]
            self.log_message(f"Using 'params' field with {len(sys_info)} fields")
        else:
            # 直接使用根级别的数据
            sys_info = device_info
            self.log_message(f"No 'sys' or 'params' field found, using root level. Keys: {list(device_info.keys())}")

        # 校准参数字段（SS:13 实际返回的字段）
        calibration_fields = {
            "RACKS": "MPU6050 Accel Scale",
            "RACOF": "MPU6050 Accel Offset",
            "GROOF": "Gyro Offset",
            "VROOF": "MPU6050 Gyro Offset",
            "REACKS": "ADXL355 Accel Scale",
            "REACOF": "ADXL355 Accel Offset",
            "EROOF": "E-Compass Offset",
            "VKS": "VKS Parameter",
            "MAGOF": "Magnetometer Offset",
            "TEM": "Temperature",
            "AKY": "Activation Key",
        }

        self.log_message("\n" + "=" * 50)
        self.log_message("CALIBRATION PARAMETERS")
        self.log_message("=" * 50)

        found_count = 0
        for key, label in calibration_fields.items():
            if key in sys_info:
                value = sys_info[key]
                # 数组类型的值格式化显示
                if isinstance(value, list):
                    value_str = f"[{', '.join(str(v) for v in value)}]"
                else:
                    value_str = str(value)
                self.log_message(f"{label}: {value_str}")
                found_count += 1

        if found_count == 0:
            self.log_message("No calibration parameters found in response")
            self.log_message(f"Available fields: {list(sys_info.keys())}")

        self.log_message("=" * 50)

        # 创建弹窗显示校准参数
        try:
            self._show_device_info_dialog(sys_info, calibration_fields)
        except Exception as e:
            self.log_message(f"Error showing device info dialog: {e}")
            import traceback
            self.log_message(traceback.format_exc())
        
        # 检查并显示校准状态 - 直接传入 device_info
        try:
            self.log_message("DEBUG: About to check calibration status from _display_device_info", "DEBUG")
            # 永久更新 sensor_properties，确保 Check 按钮使用最新数据
            self.sensor_properties = {"sys": sys_info}
            self.check_and_display_calibration_status(self.sensor_properties)
        except Exception as e:
            self.log_message(f"Error checking calibration status: {e}")
            import traceback
            self.log_message(traceback.format_exc())

    def _show_device_info_dialog(self, sys_info, calibration_fields):
        """创建弹窗显示校准参数"""
        import tkinter as tk
        from tkinter import ttk

        info_window = tk.Toplevel(self.root)
        info_window.title("Calibration Parameters")
        info_window.geometry("550x500")
        info_window.transient(self.root)
        # 移除 grab_set() 避免与 matplotlib 渲染冲突导致卡住
        # info_window.grab_set()  # 暂时禁用模态，防止死锁

        main_frame = ttk.Frame(info_window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="Calibration Parameters", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

        # 创建树形视图
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        info_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll.set,
            columns=("value",),
            show="tree headings",
            height=18,
        )
        info_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=info_tree.yview)

        info_tree.heading("#0", text="Parameter")
        info_tree.heading("value", text="Value")
        info_tree.column("#0", width=220, minwidth=180)
        info_tree.column("value", width=280, minwidth=200)

        # 填充数据
        inserted_count = 0
        for key, label in calibration_fields.items():
            if key in sys_info:
                value = sys_info[key]
                # 数组类型的值格式化显示
                if isinstance(value, list):
                    value_str = f"[{', '.join(str(v) for v in value)}]"
                else:
                    value_str = str(value)
                info_tree.insert("", "end", text=label, values=(value_str,))
                inserted_count += 1
                # 移除逐行日志，避免 UI 阻塞，改为只记录总数
        
        # 批量日志记录，减少 UI 更新
        if inserted_count > 0:
            self.log_message(f"  Added {inserted_count} parameters to dialog")
        
        if inserted_count == 0:
            self.log_message("Warning: No calibration fields matched the received data")
            # 显示所有可用的字段
            info_tree.insert("", "end", text="[Error]", values=("No matching fields found",))
            for key, value in sys_info.items():
                info_tree.insert("", "end", text=key, values=(str(value)[:50],))
            self.log_message(f"Available fields in sys_info: {list(sys_info.keys())}")

        # 关闭按钮
        close_btn = ttk.Button(main_frame, text="Close", command=info_window.destroy, width=15)
        close_btn.pack(pady=10)

        # 居中窗口
        info_window.update_idletasks()
        width = info_window.winfo_width()
        height = info_window.winfo_height()
        x = (info_window.winfo_screenwidth() // 2) - (width // 2)
        y = (info_window.winfo_screenheight() // 2) - (height // 2)
        info_window.geometry(f"{width}x{height}+{x}+{y}")

    def _read_sensor_properties_thread(self):
        """在新线程中读取传感器属性"""
        original_reading_state = self.is_reading

        try:
            if self.is_reading:
                self.root.after(0, lambda: self.log_message("Stopping data stream..."))
                self.root.after(0, self.stop_data_stream)
                time.sleep(1.0)

            self.ser.reset_input_buffer()
            time.sleep(0.5)

            self.root.after(0, lambda: self.log_message("Sending SS:8 command..."))
            self.ser.write(b"SS:8\n")
            self.ser.flush()

            time.sleep(1.0)
            response_bytes = b""
            start_time = time.time()
            timeout = 15.0
            json_found = False

            first_data_logged = False
            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    chunk = self.ser.read(self.ser.in_waiting)
                    response_bytes += chunk

                    response_str = response_bytes.decode("utf-8", errors="ignore")
                    json_start = response_str.find("{")
                    json_end = response_str.rfind("}")

                    # 调试：首次收到数据时打印长度和内容预览
                    if not first_data_logged:
                        first_data_logged = True
                        self.root.after(0, lambda l=len(response_bytes), s=response_str[:300]: 
                            self.log_message(f"First chunk: {l} bytes, preview: {s}..."))

                    # 找到 JSON 开始标记后，打印接收进度
                    if json_start != -1 and not json_found:
                        json_found = True
                        self.root.after(0, lambda: self.log_message(f"JSON data started, receiving..."))

                    if json_start != -1 and json_end != -1 and json_end > json_start:
                        json_str = response_str[json_start:json_end + 1]

                        try:
                            self.sensor_properties = json.loads(json_str)
                            self.root.after(0, lambda l=len(json_str): self.log_message(f"Complete JSON received: {l} bytes"))
                            self.root.after(0, self._extract_mac_only)
                            self.root.after(0, self._try_update_activation_status)  # 尝试更新激活状态
                            self.root.after(0, self._display_sensor_properties)
                            self.root.after(0, self._extract_network_config)
                            self.root.after(0, self.extract_and_display_alarm_threshold)
                            self.root.after(0, self._display_network_summary)
                            self.root.after(0, lambda: self.log_message("Sensor properties received successfully!"))
                            self.root.after(0, self._auto_save_properties)
                            return
                        except json.JSONDecodeError as e:
                            # JSON 不完整，继续等待更多数据
                            self.root.after(0, lambda l=len(response_bytes): self.log_message(f"JSON incomplete, received {l} bytes so far, waiting..."))
                            continue

                # 如果没有数据到达，短暂休眠后继续检查
                time.sleep(0.1)
                
                # 每 3 秒报告一次接收进度
                elapsed = time.time() - start_time
                if int(elapsed) % 3 == 0 and response_bytes and json_found:
                    total_len = len(response_bytes)
                    self.root.after(0, lambda l=total_len, t=int(elapsed): self.log_message(f"Receiving... {l} bytes in {t}s", "DEBUG"))

            self.root.after(0, lambda: self.log_message("Timeout: Failed to receive complete sensor properties"))
            
            # 超时后尝试 key-value 解析作为最后的备选方案
            if response_bytes:
                partial_response = response_bytes.decode("utf-8", errors="ignore")
                # 尝试 key-value 解析
                parsed_props = self._parse_keyvalue_response(partial_response)
                if parsed_props:
                    self.root.after(0, lambda: self.log_message(f"Parsed {len(parsed_props.get('sys', {}))} properties via fallback"))
                    self.sensor_properties = parsed_props
                    self.root.after(0, self._extract_mac_only)
                    self.root.after(0, self._try_update_activation_status)  # 尝试更新激活状态
                    self.root.after(0, self._display_sensor_properties)
                    self.root.after(0, self._extract_network_config)
                    self.root.after(0, self.extract_and_display_alarm_threshold)
                    self.root.after(0, self._display_network_summary)
                    self.root.after(0, lambda: self.log_message("Sensor properties received (fallback mode)!"))
                    self.root.after(0, self._auto_save_properties)
                    return

        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Error reading sensor properties: {str(e)}"))

        finally:
            # 恢复之前的数据流状态
            if original_reading_state and not self.is_reading:
                self.root.after(0, lambda: self.log_message("Restarting data stream..."))
                time.sleep(1.0)
                self.root.after(0, self.start_data_stream)

    def _extract_mac_only(self):
        """仅从传感器属性中提取MAC地址并生成密钥（不处理激活状态）"""
        self.log_message("DEBUG: _extract_mac_only called")
        
        if not self.sensor_properties:
            self.log_message("DEBUG: sensor_properties is empty")
            return

        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]
            mac_keys = ["MAC", "mac", "mac_address", "macAddress", "device_mac"]
            for key in mac_keys:
                if key in sys_info:
                    self.mac_address = sys_info[key]
                    self.log_message(f"DEBUG: Found MAC address: {self.mac_address} (key: {key})")
                    break

        if self.mac_address:
            import hashlib
            cleaned_mac = self.mac_address.replace(":", "").replace("-", "").lower()
            if len(cleaned_mac) == 12:
                mac_bytes = bytes.fromhex(cleaned_mac)
                hash_object = hashlib.sha256(mac_bytes)
                self.generated_key = hash_object.hexdigest()
                self.log_message(f"Generated activation key from MAC {self.mac_address}")
                
                # 更新 UI 显示
                if self.mac_var:
                    self.mac_var.set(self.mac_address)
                    self.log_message(f"DEBUG: Updated mac_var with {self.mac_address}")
                else:
                    self.log_message("DEBUG: mac_var is None, cannot update UI")
                    
                if self.key_var and self.generated_key:
                    # 显示密钥片段（7位：generated_key[5:12]）
                    key_display = self.generated_key[5:12] if len(self.generated_key) >= 12 else self.generated_key[:7]
                    self.key_var.set(key_display)
                    self.log_message(f"DEBUG: Updated key_var with {key_display}")
                else:
                    self.log_message(f"DEBUG: key_var is None or generated_key is empty")
            else:
                self.log_message(f"DEBUG: MAC address format invalid: {cleaned_mac}")
        else:
            self.log_message("DEBUG: MAC address not found in sensor properties")

    def _extract_and_process_mac(self):
        """提取MAC地址并处理激活逻辑（用于独立的激活验证流程）"""
        if not self.sensor_properties:
            return

        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]
            mac_keys = ["MAC", "mac", "mac_address", "macAddress", "device_mac"]
            for key in mac_keys:
                if key in sys_info:
                    self.mac_address = sys_info[key]
                    break

        if self.mac_address:
            import hashlib
            cleaned_mac = self.mac_address.replace(":", "").replace("-", "").lower()
            if len(cleaned_mac) == 12:
                mac_bytes = bytes.fromhex(cleaned_mac)
                hash_object = hashlib.sha256(mac_bytes)
                self.generated_key = hash_object.hexdigest()
                self.log_message(f"Generated activation key from MAC {self.mac_address}")

            self._check_activation_status()
            self.update_activation_status()

    def _save_aky_from_ss13(self, aky_value):
        """保存从 SS:13 读取的 AKY"""
        self._aky_from_ss13 = aky_value
        self.log_message(f"AKY saved from SS:13: '{aky_value}'")
        self._try_update_activation_status()

    def _try_update_activation_status(self):
        """
        尝试更新激活状态
        需要: MAC (来自 SS:8) + AKY (来自 SS:13)
        """
        # 检查 MAC
        if not self.mac_address:
            self.log_message("MAC address not available - read User Info first")
            return

        # 检查 AKY
        if not hasattr(self, '_aky_from_ss13') or self._aky_from_ss13 is None:
            self.log_message("MAC available but AKY not found - read Calibration Params to check activation")
            return

        aky = self._aky_from_ss13

        # 两个条件都满足
        self.log_message("Both MAC and AKY available - checking activation status")

        # 生成期望的密钥片段
        if not self.generated_key or len(self.generated_key) < 12:
            self.log_message("Error: Generated key not available")
            return

        expected_key = self.generated_key[5:12]

        # 比较（不区分大小写）
        if aky:
            # 调试：显示完整的比较信息
            self.log_message(f"DEBUG: AKY length={len(aky)}, value='{aky}'")
            self.log_message(f"DEBUG: Expected length={len(expected_key)}, value='{expected_key}'")
            self.log_message(f"DEBUG: Full generated_key length={len(self.generated_key)}")
            
            # 如果 AKY 是16位（固件返回），截取[5:12]位进行比较
            if len(aky) == 16:
                aky_to_compare = aky[5:12]
                self.log_message(f"DEBUG: AKY is 16 chars, extracting [5:12]: '{aky_to_compare}'")
            elif len(aky) > len(expected_key):
                aky_to_compare = aky[:7]
                self.log_message(f"DEBUG: AKY longer than expected, comparing first 7 chars: '{aky_to_compare}'")
            else:
                aky_to_compare = aky
                
            self.sensor_activated = (aky_to_compare.lower() == expected_key.lower())
            self.log_message(f"Activation check: AKY='{aky_to_compare}', Expected='{expected_key}', Match={self.sensor_activated}")
        else:
            self.sensor_activated = False
            self.log_message("AKY is empty - sensor not activated")

        # 更新 UI
        self.update_activation_status()

    def _check_activation_status(self):
        """检查传感器激活状态"""
        if not self.sensor_properties or not self.mac_address:
            return

        aks_value = None
        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]
            aks_value = sys_info.get("AKY") or sys_info.get("aky") or sys_info.get("ak_key")

        if not aks_value:
            return

        if self.generated_key and len(self.generated_key) >= 12:
            expected_key = self.generated_key[5:12]
            # 适配：固件可能返回16位AKY，截取[5:12]位进行比较
            aks_to_compare = aks_value.lower()
            if len(aks_value) == 16:
                aks_to_compare = aks_value[5:12].lower()
            self.sensor_activated = (aks_to_compare == expected_key.lower())
            self.log_message(f"Sensor activation status: {'ACTIVATED' if self.sensor_activated else 'NOT ACTIVATED'}")

    def _display_sensor_properties(self):
        """显示传感器属性 - 在日志和弹窗中显示"""
        if not self.sensor_properties:
            return

        # 1. 在日志中显示属性
        self.log_message("\n" + "=" * 50)
        self.log_message("SENSOR PROPERTIES")
        self.log_message("=" * 50)

        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]
            for key, value in sys_info.items():
                self.log_message(f"{key}: {value}")

        self.log_message("=" * 50)

        # 2. 创建弹窗显示属性树
        self._show_properties_dialog()

    def _show_properties_dialog(self):
        """创建弹窗显示传感器属性树"""
        import tkinter as tk
        from tkinter import ttk

        prop_window = tk.Toplevel(self.root)
        prop_window.title("Sensor Properties")
        prop_window.geometry("800x600")
        prop_window.transient(self.root)  # 设置为模态窗口的父窗口
        prop_window.grab_set()  # 模态窗口

        # 创建主框架
        main_frame = ttk.Frame(prop_window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # 创建树形视图显示属性
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))

        # 创建滚动条
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        # 创建树形视图
        props_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            columns=("value",),
            show="tree headings",
            height=20,
        )
        props_tree.pack(side="left", fill="both", expand=True)
        tree_scroll_y.config(command=props_tree.yview)
        tree_scroll_x.config(command=props_tree.xview)

        # 配置列
        props_tree.heading("#0", text="Property")
        props_tree.heading("value", text="Value")
        props_tree.column("#0", width=250, minwidth=150)
        props_tree.column("value", width=450, minwidth=200)

        # 填充数据
        self._populate_properties_tree(props_tree, self.sensor_properties, "")

        # 添加按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        # 保存按钮
        save_btn = ttk.Button(
            button_frame,
            text="Save to File",
            command=lambda: [self.save_properties_to_file(), prop_window.destroy()],
            width=15,
        )
        save_btn.pack(side="left", padx=5)

        # 关闭按钮
        close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=prop_window.destroy,
            width=15,
        )
        close_btn.pack(side="right", padx=5)

        # 居中窗口
        prop_window.update_idletasks()
        width = prop_window.winfo_width()
        height = prop_window.winfo_height()
        x = (prop_window.winfo_screenwidth() // 2) - (width // 2)
        y = (prop_window.winfo_screenheight() // 2) - (height // 2)
        prop_window.geometry(f"{width}x{height}+{x}+{y}")

    def _populate_properties_tree(self, tree, data, parent):
        """递归填充属性树"""
        if isinstance(data, dict):
            for key, value in data.items():
                node_id = tree.insert(parent, "end", text=str(key), values=("",))
                if isinstance(value, (dict, list)):
                    self._populate_properties_tree(tree, value, node_id)
                else:
                    tree.set(node_id, "value", str(value))
        elif isinstance(data, list):
            for i, value in enumerate(data):
                node_id = tree.insert(parent, "end", text=f"[{i}]", values=("",))
                if isinstance(value, (dict, list)):
                    self._populate_properties_tree(tree, value, node_id)
                else:
                    tree.set(node_id, "value", str(value))

    def _extract_network_config(self):
        """从传感器属性中提取网络配置"""
        self.log_message("DEBUG: _extract_network_config called")
        
        if not self.sensor_properties:
            self.log_message("DEBUG: sensor_properties is empty")
            return

        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]
            self.log_message(f"DEBUG: Extracting network config from {len(sys_info)} fields")

            ssid = sys_info.get("SSID", "")
            password = sys_info.get("PA", "")
            if ssid:
                self.wifi_params = {"ssid": ssid, "password": password}
                self.log_message(f"DEBUG: Found WiFi SSID: {ssid}")
                if hasattr(self, 'ssid_var') and self.ssid_var:
                    self.ssid_var.set(ssid)
                    self.log_message("DEBUG: Updated ssid_var")
                else:
                    self.log_message("DEBUG: ssid_var is None")
                if hasattr(self, 'password_var') and self.password_var:
                    self.password_var.set(password)
            else:
                self.log_message("DEBUG: WiFi SSID not found in properties")

            broker = sys_info.get("MBR", "")
            username = sys_info.get("MUS", "")
            mqtt_password = sys_info.get("MPW", "")
            port = sys_info.get("MPT", "1883")

            if broker:
                self.mqtt_params = {"broker": broker, "username": username, "password": mqtt_password, "port": str(port)}
                self.log_message(f"DEBUG: Found MQTT broker: {broker}")
                if hasattr(self, 'mqtt_broker_var') and self.mqtt_broker_var:
                    self.mqtt_broker_var.set(broker)
                    self.log_message("DEBUG: Updated mqtt_broker_var")
                else:
                    self.log_message("DEBUG: mqtt_broker_var is None")
            else:
                self.log_message("DEBUG: MQTT broker not found in properties")

            # OTA URL 配置
            url1 = sys_info.get("URL1", "")
            url2 = sys_info.get("URL2", "")
            url3 = sys_info.get("URL3", "")
            url4 = sys_info.get("URL4", "")
            
            self.ota_params = {"URL1": url1, "URL2": url2, "URL3": url3, "URL4": url4}
            if url1:
                self.log_message(f"DEBUG: Found OTA URL1: {url1[:30]}...")
        else:
            self.log_message("DEBUG: No 'sys' field in sensor_properties")

        self.root.after(0, self.enable_config_buttons)

    def _display_network_summary(self):
        """显示网络配置摘要"""
        if not self.sensor_properties:
            return

        self.log_message("\n" + "=" * 50)
        self.log_message("NETWORK CONFIGURATION SUMMARY")
        self.log_message("=" * 50)

        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]
            ssid = sys_info.get("SSID", "Not set")
            self.log_message(f"WiFi SSID: {ssid}")
            self.log_message(f"WiFi Password: {'*' * 8 if sys_info.get('PA') else 'Not set'}")

            broker = sys_info.get("MBR", "Not set")
            username = sys_info.get("MUS", "Not set")
            port = sys_info.get("MPT", "Not set")
            self.log_message(f"MQTT Broker: {broker}")
            self.log_message(f"MQTT Username: {username}")
            self.log_message(f"MQTT Port: {port}")
            self.log_message(f"MQTT Password: {'*' * 8 if sys_info.get('MPW') else 'Not set'}")

        self.log_message("=" * 50)

    def _display_activation_info(self):
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
                    self.log_message(f"Activation Status: {'ACTIVATED' if self.sensor_activated else 'NOT ACTIVATED'}")
                    if not self.sensor_activated:
                        self.log_message("ACTION REQUIRED: Activate sensor using 'Activate Sensor' button")
                else:
                    self.log_message("AKY field: Not found in properties")
                    self.log_message("ACTION REQUIRED: Activate sensor using 'Activate Sensor' button")
        else:
            self.log_message("MAC Address: Not found in properties")

        self.log_message("=" * 60)

    def is_sensor_calibrated(self, device_info: dict = None) -> bool:
        """
        检查传感器是否已经校准
        
        通过检查校准参数是否为默认值来判断：
        - Scale 参数：默认 [1.0, 1.0, 1.0]，已校准则偏离 1.0
        - Offset 参数：默认 [0.0, 0.0, 0.0] 或接近 0，已校准则明显非 0
        
        Args:
            device_info: 可选，直接传入设备信息字典进行检测
        
        Returns:
            bool: True 表示已校准，False 表示未校准
        """
        # 确定数据源
        if device_info is not None:
            # 优先使用传入的参数
            if "sys" in device_info:
                sys_info = device_info["sys"]
            elif "params" in device_info:
                sys_info = device_info["params"]
            else:
                sys_info = device_info
        elif self.sensor_properties and "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]
        else:
            self.log_message("DEBUG: is_sensor_calibrated - no data available", "DEBUG")
            return False
        
        self.log_message(f"DEBUG: Checking calibration with {len(sys_info)} fields", "DEBUG")
        
        # 检查关键校准参数
        calibration_params = {
            "RACKS": sys_info.get("RACKS"),  # MPU6050 Scale
            "RACOF": sys_info.get("RACOF"),  # MPU6050 Offset
            "REACKS": sys_info.get("REACKS"),  # ADXL355 Scale
            "REACOF": sys_info.get("REACOF"),  # ADXL355 Offset
            "VROOF": sys_info.get("VROOF"),   # Gyro Offset
            "GROOF": sys_info.get("GROOF"),   # Gyro Offset (alternative)
        }
        
        self.log_message(f"DEBUG: Calibration params found: {[k for k, v in calibration_params.items() if v is not None]}", "DEBUG")
        
        # 如果没有任何校准参数，认为未校准
        if all(v is None for v in calibration_params.values()):
            self.log_message("DEBUG: No calibration params found", "DEBUG")
            return False
        
        # 检查 Scale 参数是否偏离默认值 [1.0, 1.0, 1.0]
        for scale_key in ["RACKS", "REACKS"]:
            scale = calibration_params[scale_key]
            if isinstance(scale, list) and len(scale) == 3:
                max_deviation = max(abs(float(s) - 1.0) for s in scale)
                self.log_message(f"DEBUG: {scale_key} = {scale}, max_deviation = {max_deviation:.6f}", "DEBUG")
                if max_deviation > 0.01:
                    self.log_message(f"DEBUG: {scale_key} deviation {max_deviation:.4f} > 0.01, CALIBRATED", "DEBUG")
                    return True
            else:
                self.log_message(f"DEBUG: {scale_key} is not a valid list: {type(scale)}", "DEBUG")
        
        # 检查 Offset 参数是否偏离默认值 [0.0, 0.0, 0.0]
        for offset_key in ["RACOF", "REACOF", "VROOF", "GROOF"]:
            offset = calibration_params[offset_key]
            if isinstance(offset, list) and len(offset) == 3:
                max_offset = max(abs(float(o)) for o in offset)
                self.log_message(f"DEBUG: {offset_key} = {offset}, max_offset = {max_offset:.6f}", "DEBUG")
                if max_offset > 0.01:
                    self.log_message(f"DEBUG: {offset_key} offset {max_offset:.4f} > 0.01, CALIBRATED", "DEBUG")
                    return True
            else:
                self.log_message(f"DEBUG: {offset_key} is not a valid list: {type(offset)}", "DEBUG")
        
        # 如果都没有偏离默认值，认为未校准
        self.log_message("DEBUG: No significant deviation found, NOT CALIBRATED", "DEBUG")
        return False

    def get_calibration_quality(self) -> dict:
        """
        获取校准质量评估
        
        Returns:
            dict: 包含校准状态和各参数偏离程度的详细信息
        """
        if not self.sensor_properties or "sys" not in self.sensor_properties:
            return {
                "status": "unknown",
                "message": "No sensor properties available",
                "details": {}
            }
        
        sys_info = self.sensor_properties["sys"]
        details = {}
        
        # MPU6050 加速度计
        racks = sys_info.get("RACKS", [1.0, 1.0, 1.0])
        racof = sys_info.get("RACOF", [0.0, 0.0, 0.0])
        
        if isinstance(racks, list) and len(racks) == 3:
            details["mpu_accel_scale"] = racks
            details["mpu_accel_scale_deviation"] = max(abs(s - 1.0) for s in racks)
            details["mpu_accel_scale_calibrated"] = details["mpu_accel_scale_deviation"] > 0.01
        
        if isinstance(racof, list) and len(racof) == 3:
            details["mpu_accel_offset"] = racof
            details["mpu_accel_offset_max"] = max(abs(o) for o in racof)
            details["mpu_accel_offset_calibrated"] = details["mpu_accel_offset_max"] > 0.01
        
        # ADXL355 加速度计
        reacks = sys_info.get("REACKS", [1.0, 1.0, 1.0])
        reacof = sys_info.get("REACOF", [0.0, 0.0, 0.0])
        
        if isinstance(reacks, list) and len(reacks) == 3:
            details["adxl_accel_scale"] = reacks
            details["adxl_accel_scale_deviation"] = max(abs(s - 1.0) for s in reacks)
            details["adxl_accel_scale_calibrated"] = details["adxl_accel_scale_deviation"] > 0.01
        
        if isinstance(reacof, list) and len(reacof) == 3:
            details["adxl_accel_offset"] = reacof
            details["adxl_accel_offset_max"] = max(abs(o) for o in reacof)
            details["adxl_accel_offset_calibrated"] = details["adxl_accel_offset_max"] > 0.01
        
        # 陀螺仪
        vroof = sys_info.get("VROOF", [0.0, 0.0, 0.0])
        groof = sys_info.get("GROOF", [0.0, 0.0, 0.0])
        
        if isinstance(vroof, list) and len(vroof) == 3:
            details["gyro_offset"] = vroof
            details["gyro_offset_max"] = max(abs(o) for o in vroof)
            details["gyro_calibrated"] = details["gyro_offset_max"] > 0.01
        
        # 综合判断
        is_calibrated = any([
            details.get("mpu_accel_scale_calibrated", False),
            details.get("mpu_accel_offset_calibrated", False),
            details.get("adxl_accel_scale_calibrated", False),
            details.get("adxl_accel_offset_calibrated", False),
            details.get("gyro_calibrated", False),
        ])
        
        if is_calibrated:
            status = "calibrated"
            message = "Sensor has been calibrated"
        else:
            status = "uncalibrated"
            message = "Sensor not calibrated - Calibration recommended"
        
        return {
            "status": status,
            "message": message,
            "is_calibrated": is_calibrated,
            "details": details
        }

    def check_and_display_calibration_status(self, device_info: dict = None):
        """
        检查并显示校准状态
        
        Args:
            device_info: 可选，直接传入设备信息字典
        """
        self.log_message("\n" + "=" * 60)
        self.log_message("CALIBRATION STATUS CHECK")
        self.log_message("=" * 60)
        
        # 使用传入的参数或 self.sensor_properties
        if device_info is not None:
            self.log_message("DEBUG: Using provided device_info", "DEBUG")
            # 永久更新 sensor_properties，确保后续 Check 按钮使用最新数据
            self.sensor_properties = device_info
            is_calibrated = self.is_sensor_calibrated()
            quality = self.get_calibration_quality()
        else:
            self.log_message("DEBUG: Using self.sensor_properties", "DEBUG")
            is_calibrated = self.is_sensor_calibrated()
            quality = self.get_calibration_quality()
        
        self.log_message(f"DEBUG: is_calibrated = {is_calibrated}", "DEBUG")
        
        if is_calibrated:
            self.log_message("Status: ✓ CALIBRATED")
            
            # 显示详细的校准信息
            details = quality.get("details", {})
            
            if details.get("mpu_accel_scale_calibrated"):
                self.log_message(f"MPU6050 Accel Scale: {details.get('mpu_accel_scale')}")
                self.log_message(f"  Deviation: {details.get('mpu_accel_scale_deviation', 0):.4f}")
            
            if details.get("mpu_accel_offset_calibrated"):
                self.log_message(f"MPU6050 Accel Offset: {details.get('mpu_accel_offset')}")
                self.log_message(f"  Max Offset: {details.get('mpu_accel_offset_max', 0):.4f}")
            
            if details.get("adxl_accel_scale_calibrated"):
                self.log_message(f"ADXL355 Accel Scale: {details.get('adxl_accel_scale')}")
                self.log_message(f"  Deviation: {details.get('adxl_accel_scale_deviation', 0):.4f}")
            
            if details.get("adxl_accel_offset_calibrated"):
                self.log_message(f"ADXL355 Accel Offset: {details.get('adxl_accel_offset')}")
                self.log_message(f"  Max Offset: {details.get('adxl_accel_offset_max', 0):.4f}")
            
            if details.get("gyro_calibrated"):
                self.log_message(f"Gyro Offset: {details.get('gyro_offset')}")
                self.log_message(f"  Max Offset: {details.get('gyro_offset_max', 0):.4f}")
                
        else:
            self.log_message("Status: ✗ NOT CALIBRATED")
            self.log_message("")
            self.log_message("⚠️  WARNING: Sensor calibration required!")
            self.log_message("")
            self.log_message("To calibrate the sensor:")
            self.log_message("1. Click 'Start Data Stream' to begin data acquisition")
            self.log_message("2. Click 'Start Calib' to enter calibration mode")
            self.log_message("3. Follow the 6-position calibration procedure:")
            self.log_message("   Position 1: +X facing down (X-axis up)")
            self.log_message("   Position 2: -X facing down (X-axis down)")
            self.log_message("   Position 3: +Y facing down (Y-axis up)")
            self.log_message("   Position 4: -Y facing down (Y-axis down)")
            self.log_message("   Position 5: +Z facing down (Z-axis up)")
            self.log_message("   Position 6: -Z facing down (Z-axis down)")
            self.log_message("4. Click 'Capture Pos' at each position")
            self.log_message("5. After all positions captured, send calibration commands")
        
        self.log_message("=" * 60)
        
        # 更新UI显示
        self.update_calibration_status_display(is_calibrated)
        
        return is_calibrated

    def update_calibration_status_display(self, is_calibrated: bool = None):
        """
        更新校准状态UI显示
        
        Args:
            is_calibrated: 校准状态，None 表示自动检测
        """
        if is_calibrated is None:
            is_calibrated = self.is_sensor_calibrated()
        
        if hasattr(self, 'calibration_status_var') and self.calibration_status_var:
            if is_calibrated:
                self.calibration_status_var.set("Calibrated")
            else:
                self.calibration_status_var.set("Not Calibrated")
        
        if hasattr(self, 'calibration_status_label') and self.calibration_status_label:
            if is_calibrated:
                self.calibration_status_label.config(foreground="green")
            else:
                self.calibration_status_label.config(foreground="orange")

    def read_calibration_params(self):
        """
        通过独立命令读取校准参数（从 SS:8 中剥离的功能）
        注意：此方法需要通过特定命令获取校准参数，而非 SS:8
        """
        if not self.serial_manager.is_connected:
            self.log_message("Error: Not connected to serial port!")
            return

        self.log_message("Starting calibration parameters reading process...")
        # TODO: 在这里实现通过特定命令读取校准参数的逻辑
        # 例如：发送 SS:? 命令获取 RACKS, RACOF, REACKS, REACOF, VROOF, GROOF 等参数
        threading.Thread(target=self._read_calibration_params_thread, daemon=True).start()

    def _read_calibration_params_thread(self):
        """在线程中读取校准参数"""
        try:
            # 停止数据流
            if self.is_reading:
                self.root.after(0, lambda: self.log_message("Stopping data stream..."))
                self.root.after(0, self.stop_data_stream)
                time.sleep(1.0)

            # 清空缓冲区
            if self.serial_manager.serial_port:
                self.serial_manager.serial_port.reset_input_buffer()
                time.sleep(0.5)

            # TODO: 发送获取校准参数的命令
            # 例如：self.serial_manager.send_ssX_get_calibration()
            self.root.after(0, lambda: self.log_message("Sending calibration params request command..."))
            
            # 等待响应并解析
            time.sleep(2.0)
            
            # TODO: 解析校准参数响应
            # 临时显示提示信息
            self.root.after(0, lambda: self.log_message("Calibration params reading not yet implemented - needs specific command"))
            self.root.after(0, lambda: self.log_message("Expected params: RACKS, RACOF, REACKS, REACOF, VROOF, GROOF"))

        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Error reading calibration params: {str(e)}"))

        finally:
            # 恢复数据流
            if self.is_reading:
                self.root.after(0, lambda: self.log_message("Restarting data stream..."))
                time.sleep(1.0)
                self.root.after(0, self.start_data_stream)

    def verify_activation_status(self):
        """
        通过独立命令验证激活状态（从 SS:8 中剥离的功能）
        注意：此方法需要通过特定命令获取 AKY/PK 字段，而非 SS:8
        """
        if not self.serial_manager.is_connected:
            self.log_message("Error: Not connected to serial port!")
            return

        if not self.mac_address:
            self.log_message("Error: MAC address not available. Please read sensor properties first.")
            return

        self.log_message("Starting activation status verification...")
        threading.Thread(target=self._verify_activation_thread, daemon=True).start()

    def _verify_activation_thread(self):
        """在线程中验证激活状态"""
        try:
            # 停止数据流
            if self.is_reading:
                self.root.after(0, lambda: self.log_message("Stopping data stream..."))
                self.root.after(0, self.stop_data_stream)
                time.sleep(1.0)

            # 清空缓冲区
            if self.serial_manager.serial_port:
                self.serial_manager.serial_port.reset_input_buffer()
                time.sleep(0.5)

            # TODO: 发送获取激活状态的命令
            # 例如：self.serial_manager.send_ssX_get_activation()
            self.root.after(0, lambda: self.log_message("Sending activation status request command..."))
            
            # 等待响应并解析
            time.sleep(2.0)
            
            # TODO: 解析激活状态响应，获取 AKY/PK 字段
            # 临时显示提示信息
            self.root.after(0, lambda: self.log_message("Activation status verification not yet implemented - needs specific command"))
            self.root.after(0, lambda: self.log_message("Expected fields: AKY/PK for activation key verification"))
            
            # 显示当前已知的激活信息（基于已有数据）
            self.root.after(0, self._display_activation_info)

        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Error verifying activation status: {str(e)}"))

        finally:
            # 恢复数据流
            if self.is_reading:
                self.root.after(0, lambda: self.log_message("Restarting data stream..."))
                time.sleep(1.0)
                self.root.after(0, self.start_data_stream)

    def copy_activation_key(self):
        """复制激活密钥到剪贴板"""
        if not self.generated_key:
            self.log_message("Error: No activation key generated. Please read sensor properties first.")
            return
        
        try:
            # 复制密钥片段到剪贴板
            key_fragment = self.generated_key[5:12] if len(self.generated_key) >= 12 else self.generated_key[:7]
            
            # 使用 tkinter 的剪贴板功能
            if self.root:
                self.root.clipboard_clear()
                self.root.clipboard_append(key_fragment)
                self.log_message(f"Activation key copied to clipboard: {key_fragment}")
        except Exception as e:
            self.log_message(f"Error copying activation key: {str(e)}")

    def _auto_save_properties(self):
        """自动保存属性到文件"""
        try:
            from datetime import datetime

            config_data = {
                "timestamp": datetime.now().isoformat(),
                "sensor_properties": self.sensor_properties,
                "mac_address": self.mac_address,
                "sensor_activated": self.sensor_activated,
            }

            with open(self.properties_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.log_message(f"Sensor properties saved to: {self.properties_file}")

        except Exception as e:
            self.log_message(f"Error saving sensor properties: {str(e)}")

    def enable_config_buttons(self):
        """启用配置按钮"""
        # WiFi 配置按钮
        if hasattr(self, 'set_wifi_btn') and self.set_wifi_btn:
            self.set_wifi_btn.config(state="normal")
        if hasattr(self, 'read_wifi_btn') and self.read_wifi_btn:
            self.read_wifi_btn.config(state="normal")
        
        # MQTT 配置按钮
        if hasattr(self, 'set_mqtt_btn') and self.set_mqtt_btn:
            self.set_mqtt_btn.config(state="normal")
        if hasattr(self, 'read_mqtt_btn') and self.read_mqtt_btn:
            self.read_mqtt_btn.config(state="normal")
        
        # OTA 配置按钮
        if hasattr(self, 'set_ota_btn') and self.set_ota_btn:
            self.set_ota_btn.config(state="normal")
        if hasattr(self, 'read_ota_btn') and self.read_ota_btn:
            self.read_ota_btn.config(state="normal")
        
        # 报警阈值和设备控制按钮
        if hasattr(self, 'set_alarm_threshold_btn') and self.set_alarm_threshold_btn:
            self.set_alarm_threshold_btn.config(state="normal")
        if hasattr(self, 'save_config_btn') and self.save_config_btn:
            self.save_config_btn.config(state="normal")
        if hasattr(self, 'restart_sensor_btn') and self.restart_sensor_btn:
            self.restart_sensor_btn.config(state="normal")
        
        # Sprint 1: 启用新增按钮
        # Cloud MQTT 按钮
        if self.ui_manager.widgets.get('set_aliyun_mqtt_btn'):
            self.ui_manager.widgets['set_aliyun_mqtt_btn'].config(state="normal")
        if self.ui_manager.widgets.get('mqtt_local_mode_btn'):
            self.ui_manager.widgets['mqtt_local_mode_btn'].config(state="normal")
        if self.ui_manager.widgets.get('mqtt_aliyun_mode_btn'):
            self.ui_manager.widgets['mqtt_aliyun_mode_btn'].config(state="normal")
        # Position 按钮
        if self.ui_manager.widgets.get('set_position_btn'):
            self.ui_manager.widgets['set_position_btn'].config(state="normal")
        if self.ui_manager.widgets.get('set_install_mode_btn'):
            self.ui_manager.widgets['set_install_mode_btn'].config(state="normal")
        # System 按钮
        if self.ui_manager.widgets.get('save_sensor_config_btn'):
            self.ui_manager.widgets['save_sensor_config_btn'].config(state="normal")
        if self.ui_manager.widgets.get('restore_default_btn'):
            self.ui_manager.widgets['restore_default_btn'].config(state="normal")
        if self.ui_manager.widgets.get('restart_sensor_system_btn'):
            self.ui_manager.widgets['restart_sensor_system_btn'].config(state="normal")
        if self.ui_manager.widgets.get('deactivate_sensor_btn'):
            self.ui_manager.widgets['deactivate_sensor_btn'].config(state="normal")
        
        # Sprint 2: Advanced 标签页按钮
        if self.ui_manager.widgets.get('set_kalman_filter_btn'):
            self.ui_manager.widgets['set_kalman_filter_btn'].config(state="normal")
        if self.ui_manager.widgets.get('filter_on_btn'):
            self.ui_manager.widgets['filter_on_btn'].config(state="normal")
        if self.ui_manager.widgets.get('filter_off_btn'):
            self.ui_manager.widgets['filter_off_btn'].config(state="normal")
        
        # Sprint 2: Alarm Levels 标签页按钮
        if self.ui_manager.widgets.get('set_gyro_levels_btn'):
            self.ui_manager.widgets['set_gyro_levels_btn'].config(state="normal")
        if self.ui_manager.widgets.get('set_accel_levels_btn'):
            self.ui_manager.widgets['set_accel_levels_btn'].config(state="normal")
        
        # Sprint 2: Auxiliary 标签页按钮
        if self.ui_manager.widgets.get('set_vks_btn'):
            self.ui_manager.widgets['set_vks_btn'].config(state="normal")
        if self.ui_manager.widgets.get('set_tme_btn'):
            self.ui_manager.widgets['set_tme_btn'].config(state="normal")
        if self.ui_manager.widgets.get('set_magof_btn'):
            self.ui_manager.widgets['set_magof_btn'].config(state="normal")
        
        # Sprint 2: Debug 标签页按钮
        if self.ui_manager.widgets.get('cpu_monitor_btn'):
            self.ui_manager.widgets['cpu_monitor_btn'].config(state="normal")
        if self.ui_manager.widgets.get('sensor_cal_btn'):
            self.ui_manager.widgets['sensor_cal_btn'].config(state="normal")
        if self.ui_manager.widgets.get('buzzer_btn'):
            self.ui_manager.widgets['buzzer_btn'].config(state="normal")
        if self.ui_manager.widgets.get('check_upgrade_btn'):
            self.ui_manager.widgets['check_upgrade_btn'].config(state="normal")
        if self.ui_manager.widgets.get('ap_mode_btn'):
            self.ui_manager.widgets['ap_mode_btn'].config(state="normal")
        
        # Sprint 3: Camera 标签页按钮
        if self.ui_manager.widgets.get('camera_photo_on_btn'):
            self.ui_manager.widgets['camera_photo_on_btn'].config(state="normal")
        if self.ui_manager.widgets.get('camera_photo_off_btn'):
            self.ui_manager.widgets['camera_photo_off_btn'].config(state="normal")
        if self.ui_manager.widgets.get('monitoring_on_btn'):
            self.ui_manager.widgets['monitoring_on_btn'].config(state="normal")
        if self.ui_manager.widgets.get('monitoring_off_btn'):
            self.ui_manager.widgets['monitoring_off_btn'].config(state="normal")
        if self.ui_manager.widgets.get('timelapse_on_btn'):
            self.ui_manager.widgets['timelapse_on_btn'].config(state="normal")
        if self.ui_manager.widgets.get('timelapse_off_btn'):
            self.ui_manager.widgets['timelapse_off_btn'].config(state="normal")
        if self.ui_manager.widgets.get('take_photo_btn'):
            self.ui_manager.widgets['take_photo_btn'].config(state="normal")
        if self.ui_manager.widgets.get('reboot_camera_slave_btn'):
            self.ui_manager.widgets['reboot_camera_slave_btn'].config(state="normal")
        if self.ui_manager.widgets.get('reboot_camera_module_btn'):
            self.ui_manager.widgets['reboot_camera_module_btn'].config(state="normal")
        if self.ui_manager.widgets.get('toggle_camera_stream_btn'):
            self.ui_manager.widgets['toggle_camera_stream_btn'].config(state="normal")
        if self.ui_manager.widgets.get('toggle_push_stream_btn'):
            self.ui_manager.widgets['toggle_push_stream_btn'].config(state="normal")
        if self.ui_manager.widgets.get('force_camera_ota_btn'):
            self.ui_manager.widgets['force_camera_ota_btn'].config(state="normal")
        if self.ui_manager.widgets.get('force_esp32_ota_btn'):
            self.ui_manager.widgets['force_esp32_ota_btn'].config(state="normal")
        
        # Dashboard 标签页按钮
        dashboard_buttons = [
            'dashboard_read_sensor_properties_btn',
            'dashboard_read_calibration_params_btn', 
            'dashboard_save_sensor_config_btn',
            'dashboard_restart_sensor_btn'
        ]
        for btn_name in dashboard_buttons:
            if self.ui_manager.widgets.get(btn_name):
                self.ui_manager.widgets[btn_name].config(state="normal")
        
        # Calibration 标签页按钮
        cal_buttons = [
            'cal_start_calibration_btn',
            'cal_capture_position_btn',
            'cal_finish_calibration_btn',
            'cal_generate_calibration_commands_btn',
            'cal_send_all_commands_btn',
            'cal_save_calibration_parameters_btn'
        ]
        for btn_name in cal_buttons:
            if self.ui_manager.widgets.get(btn_name):
                self.ui_manager.widgets[btn_name].config(state="normal")
        
        self.log_message("All config buttons enabled")

    def reset_calibration_state(self):
        """重置校准状态"""
        self.is_calibrating = False
        self.log_message("Calibration state reset")

    def update_position_display(self):
        """更新位置显示"""
        if hasattr(self, 'calibration_workflow') and self.position_var:
            self.position_var.set(self.calibration_workflow.position_progress)

    # =========================================================================
    # UI 重置功能 (UI Reset Functionality)
    # =========================================================================

    def reset_ui_state(self):
        """
        重置UI到初始状态
        
        清空所有数据、图表、统计信息，重置UI变量到初始值
        重置所有按钮状态
        """
        # 1. 清空数据缓冲区
        if hasattr(self, 'data_processor'):
            self.data_processor.clear_all()
        
        # 2. 清空图表
        if self.chart_manager:
            self.chart_manager.clear_data()
        
        # 3. 重置统计标签显示
        self._reset_statistics_display()
        
        # 4. 重置UI变量
        if self.freq_var:
            self.freq_var.set("0 Hz")
        if self.position_var:
            self.position_var.set("Position: Not calibrating")
        
        # 5. 清空命令区
        if self.cmd_text:
            self.cmd_text.delete(1.0, "end")
        
        # 6. 重置激活状态
        self._reset_activation_display()
        
        # 7. 重置内部状态
        self.packets_received = 0
        self.serial_freq = 0
        self._aky_from_ss13 = None
        
        # 8. 重置按钮状态
        self._reset_button_states()
        
        self.log_message("UI 已重置")
    
    def _reset_button_states(self):
        """
        重置所有按钮状态
        
        - Connect 按钮：根据实际连接状态设置
        - 其他按钮：重置为初始状态（禁用）
        """
        # Connect 按钮：根据实际连接状态
        if self.connect_btn:
            if hasattr(self, 'serial_manager') and self.serial_manager.is_connected:
                self.connect_btn.config(text="Disconnect")
            else:
                self.connect_btn.config(text="Connect")
        
        # Data Stream 按钮
        if self.data_btn:
            self.data_btn.config(text="Start Data", state="disabled")
        
        # Dashboard 标签页按钮
        dashboard_buttons = [
            'dashboard_read_sensor_properties_btn',
            'dashboard_read_calibration_params_btn',
            'dashboard_save_sensor_config_btn',
            'dashboard_restart_sensor_btn'
        ]
        for btn_name in dashboard_buttons:
            if self.ui_manager.widgets.get(btn_name):
                self.ui_manager.widgets[btn_name].config(state="disabled")
        
        # Calibration 标签页按钮
        cal_buttons = [
            'cal_start_calibration_btn',
            'cal_capture_position_btn',
            'cal_finish_calibration_btn',
            'cal_generate_calibration_commands_btn',
            'cal_send_all_commands_btn',
            'cal_save_calibration_parameters_btn'
        ]
        for btn_name in cal_buttons:
            if self.ui_manager.widgets.get(btn_name):
                self.ui_manager.widgets[btn_name].config(state="disabled")
        
        # 激活按钮
        if hasattr(self, 'activate_btn') and self.activate_btn:
            self.activate_btn.config(state="disabled")
        if hasattr(self, 'verify_btn') and self.verify_btn:
            self.verify_btn.config(state="disabled")
        
        # 网络配置按钮
        if hasattr(self, 'set_wifi_btn') and self.set_wifi_btn:
            self.set_wifi_btn.config(state="disabled")
        if hasattr(self, 'read_wifi_btn') and self.read_wifi_btn:
            self.read_wifi_btn.config(state="disabled")
        if hasattr(self, 'set_mqtt_btn') and self.set_mqtt_btn:
            self.set_mqtt_btn.config(state="disabled")
        if hasattr(self, 'read_mqtt_btn') and self.read_mqtt_btn:
            self.read_mqtt_btn.config(state="disabled")
        if hasattr(self, 'set_ota_btn') and self.set_ota_btn:
            self.set_ota_btn.config(state="disabled")
        if hasattr(self, 'read_ota_btn') and self.read_ota_btn:
            self.read_ota_btn.config(state="disabled")
        
        # 报警和设备控制按钮
        if hasattr(self, 'set_alarm_threshold_btn') and self.set_alarm_threshold_btn:
            self.set_alarm_threshold_btn.config(state="disabled")
        if hasattr(self, 'save_config_btn') and self.save_config_btn:
            self.save_config_btn.config(state="disabled")
        if hasattr(self, 'restart_sensor_btn') and self.restart_sensor_btn:
            self.restart_sensor_btn.config(state="disabled")

    def _reset_statistics_display(self):
        """重置统计标签显示为初始值"""
        if not self.stats_labels:
            return
        
        # 重置所有轴的统计
        for sensor_key in ['mpu_accel', 'adxl_accel', 'mpu_gyro']:
            for axis in ['x', 'y', 'z']:
                mean_key = f"{sensor_key}_{axis}_mean"
                std_key = f"{sensor_key}_{axis}_std"
                if mean_key in self.stats_labels and self.stats_labels[mean_key]:
                    self.stats_labels[mean_key].set("μ: 0.000")
                if std_key in self.stats_labels and self.stats_labels[std_key]:
                    self.stats_labels[std_key].set("σ: 0.000")
        
        # 重置重力统计
        if 'gravity_mean' in self.stats_labels and self.stats_labels['gravity_mean']:
            self.stats_labels['gravity_mean'].set("Mean: 0.000")
        if 'gravity_std' in self.stats_labels and self.stats_labels['gravity_std']:
            self.stats_labels['gravity_std'].set("Std: 0.000")

    def _reset_activation_display(self):
        """重置激活状态显示"""
        # 重置内部变量
        self.sensor_properties = {}
        self.mac_address = None
        self.generated_key = None
        self.sensor_activated = False
        
        # 重置UI显示
        if self.mac_var:
            self.mac_var.set("--")
        if self.key_var:
            self.key_var.set("")
        if self.activation_status_var:
            self.activation_status_var.set("Not Activated")
        if self.activation_status_label:
            self.activation_status_label.config(foreground="red")
        
        # 重置校准状态显示
        if self.calibration_status_var:
            self.calibration_status_var.set("Unknown")
        if self.calibration_status_label:
            self.calibration_status_label.config(foreground="gray")

    def show_reset_confirmation(self, callback=None):
        """
        显示重置确认弹窗
        
        Args:
            callback: 用户点击确定后的回调函数
        
        Returns:
            bool: 用户是否点击了确定
        """
        result = messagebox.askokcancel(
            "确认重置 UI",
            "刷新页面将清空以下数据：\n"
            "• 所有图表数据\n"
            "• 实时统计信息\n"
            "• 校准命令记录\n"
            "• 传感器激活状态\n\n"
            "此操作不可撤销。确定要继续吗？",
            icon='warning'
        )
        
        if result and callback:
            callback()
        
        return result

    def reset_ui_with_confirmation(self, silent=False):
        """
        带确认弹窗的UI重置
        
        Args:
            silent: 如果为True，不显示确认弹窗直接重置（用于程序内部调用）
        
        Returns:
            bool: 是否执行了重置
        """
        if silent:
            self.reset_ui_state()
            return True
        
        def do_reset():
            self.reset_ui_state()
        
        return self.show_reset_confirmation(do_reset)

    def _show_device_disconnected_dialog(self):
        """显示设备断开连接提示框"""
        # 先停止数据流
        if self.is_reading:
            self.is_reading = False
            if self.serial_manager:
                self.serial_manager.stop_reading()
        
        # 清空串口缓冲区（COM口数据）
        if self.serial_manager and self.serial_manager.serial_port:
            try:
                self.serial_manager.serial_port.reset_input_buffer()
                self.serial_manager.serial_port.reset_output_buffer()
                self.log_message("COM port buffers cleared")
            except Exception as e:
                self.log_message(f"Failed to clear COM port buffers: {e}", "DEBUG")
        
        # 显示信息提示框
        try:
            messagebox.showinfo(
                "设备已断开连接",
                "检测到设备已断开连接（USB可能被拔出）。\n\n"
                "点击确定后将重置UI界面。",
                icon='warning',
                parent=self.root if self.root else None
            )
        except Exception:
            # 在测试环境中可能没有 root 窗口，忽略错误
            pass
        
        # 用户点击确定后执行重置
        self.reset_ui_state()
        self.log_message("设备断开连接，UI 已重置")
