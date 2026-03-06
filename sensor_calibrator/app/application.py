"""
SensorCalibrator Application Core

主应用类，整合所有组件并管理应用生命周期。
"""

import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, StringVar, messagebox
from typing import Optional, Dict

from ..config import Config, UIConfig, CalibrationConfig
from ..data_processor import DataProcessor
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
        self.scrollable_frame = ttk.Frame(canvas, width=UIConfig.LEFT_PANEL_WIDTH)

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
        
        # 创建回调函数字典
        callbacks = {
            # 串口相关
            'refresh_ports': self.ui_callbacks.refresh_ports,
            'toggle_connection': self.ui_callbacks.toggle_connection,
            
            # 数据流相关
            'toggle_data_stream': self.ui_callbacks.toggle_data_stream,
            'toggle_data_stream2': self.ui_callbacks.toggle_data_stream2,
            
            # 校准相关
            'start_calibration': self.ui_callbacks.start_calibration,
            'capture_position': self.ui_callbacks.capture_position,
            'send_all_commands': self.ui_callbacks.send_all_commands,
            'save_calibration_parameters': self.ui_callbacks.save_calibration_parameters,
            'read_properties': self.ui_callbacks.read_sensor_properties,
            'resend_all_commands': self.ui_callbacks.resend_all_commands,
            
            # 坐标模式
            'set_local_coordinate_mode': self.ui_callbacks.set_local_coordinate_mode,
            'set_global_coordinate_mode': self.ui_callbacks.set_global_coordinate_mode,
            
            # 激活相关
            'activate_sensor': self.ui_callbacks.activate_sensor,
            'verify_activation': self.ui_callbacks.verify_activation,
            'copy_activation_key': self.ui_callbacks.copy_activation_key,
            
            # 网络配置
            'set_wifi_config': self.ui_callbacks.set_wifi_config,
            'read_wifi_config': self.ui_callbacks.read_wifi_config,
            'set_mqtt_config': self.ui_callbacks.set_mqtt_config,
            'read_mqtt_config': self.ui_callbacks.read_mqtt_config,
            'set_ota_config': self.ui_callbacks.set_ota_config,
            'read_ota_config': self.ui_callbacks.read_ota_config,
            
            # 报警和设备控制
            'set_alarm_threshold': self.ui_callbacks.set_alarm_threshold,
            'restart_sensor': self.ui_callbacks.restart_sensor,
            'save_config': self.ui_callbacks.save_config,
        }
        
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
        
        # 校准位置变量
        self.position_var = self.ui_manager.vars.get('position')
        
        # 激活相关变量
        self.mac_var = self.ui_manager.vars.get('activation_mac')
        
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

    def _on_connection_state_changed(self, connected: bool):
        """串口连接状态变化回调"""
        if connected:
            self.ser = self.serial_manager.serial_port
        else:
            self.ser = None

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
        self.log_message("Calibration finished successfully!")

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
                self.send_ss0_start_stream()

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
                    except Exception:
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
                processed_count = 0
                while not self.data_queue.empty() and processed_count < 100:
                    try:
                        data_string = self.data_queue.get_nowait()
                        mpu_accel, mpu_gyro, adxl_accel = self.parse_sensor_data(
                            data_string
                        )

                        if mpu_accel and mpu_gyro and adxl_accel:
                            if self.data_processor.data_start_time is None:
                                self.data_processor.data_start_time = time.time()

                            current_relative_time = (
                                self.data_processor.packet_count / 
                                self.data_processor.expected_frequency
                            )
                            self.data_processor.packet_count += 1

                            self.data_processor.time_data.append(current_relative_time)

                            for i in range(3):
                                self.data_processor.mpu_accel_data[i].append(mpu_accel[i])
                                self.data_processor.mpu_gyro_data[i].append(mpu_gyro[i])
                                self.data_processor.adxl_accel_data[i].append(adxl_accel[i])

                            gravity_mag = (
                                mpu_accel[0] ** 2 +
                                mpu_accel[1] ** 2 +
                                mpu_accel[2] ** 2
                            ) ** 0.5
                            self.data_processor.gravity_mag_data.append(gravity_mag)
                        
                        processed_count += 1

                    except Exception:
                        break

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

    def parse_sensor_data(self, data_string):
        """解析传感器数据"""
        return self.data_processor.parse_sensor_data(data_string)

    def clear_data(self):
        """清空所有数据"""
        self.data_processor.clear_all()

    def send_ss0_start_stream(self):
        """发送 SS:0 指令 - 开始数据流"""
        return self.serial_manager.send_ss0_start_stream()

    def send_ss8_get_properties(self):
        """发送 SS:8 指令 - 获取传感器属性"""
        return self.serial_manager.send_ss8_get_properties()

    def read_sensor_properties(self):
        """读取传感器属性"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        self.log_message("Starting sensor properties reading process...")
        threading.Thread(target=self._read_properties_thread, daemon=True).start()

    def _read_properties_thread(self):
        """在新线程中读取传感器属性"""
        if not self.ser:
            return
        
        original_reading_state = self.is_reading

        try:
            if self.is_reading:
                self.root.after(0, lambda: self.log_message("Stopping data stream..."))
                self.root.after(0, self.stop_data_stream)
                time.sleep(1.0)

            self.ser.reset_input_buffer()
            time.sleep(0.5)

            self.root.after(0, lambda: self.log_message("Sending SS:8 command..."))
            self.send_ss8_get_properties()

            time.sleep(2.0)

            response_bytes = b""
            start_time = time.time()
            timeout = 10.0

            self.root.after(0, lambda: self.log_message("Reading response..."))

            while time.time() - start_time < timeout:
                if not self.ser:
                    break
                if self.ser.in_waiting > 0:
                    chunk = self.ser.read(self.ser.in_waiting)
                    response_bytes += chunk

                    response_str = response_bytes.decode("utf-8", errors="ignore")

                    json_start = response_str.find("{")
                    json_end = response_str.rfind("}")

                    if json_start != -1 and json_end != -1 and json_end > json_start:
                        json_str = response_str[json_start : json_end + 1]

                        try:
                            self.sensor_properties = __import__('json').loads(json_str)
                            self.root.after(0, self.extract_and_process_mac)
                            self.root.after(0, self.display_sensor_properties)
                            self.root.after(0, self.extract_network_config)
                            self.root.after(0, self.extract_and_display_alarm_threshold)
                            self.root.after(0, self.display_network_summary)
                            self.root.after(0, self.display_activation_info)
                            self.root.after(0, self.auto_save_properties)
                            return

                        except Exception:
                            continue

                time.sleep(0.1)

            self.root.after(
                0,
                lambda: self.log_message("Timeout: Failed to receive complete sensor properties")
            )

        except Exception as e:
            self.root.after(
                0, lambda: self.log_message(f"Error reading sensor properties: {str(e)}")
            )

        finally:
            if original_reading_state and not self.is_reading:
                self.root.after(0, lambda: self.log_message("Restarting data stream..."))
                time.sleep(1.0)
                self.root.after(0, self.start_data_stream)

    def extract_and_process_mac(self):
        """提取MAC地址并处理激活逻辑"""
        self.mac_address = self.activation_workflow.extract_mac_from_properties(
            self.sensor_properties
        )

        if self.mac_address:
            self.generated_key = self.activation_workflow.generate_key_from_mac(
                self.mac_address
            )
            self.log_message(f"Generated activation key from MAC {self.mac_address}")
            
            self.sensor_activated = self.check_activation_status()
            self.update_activation_status()

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

    def update_activation_status(self):
        """更新激活状态显示"""
        if self.sensor_activated:
            self.log_message("Sensor activation status: ACTIVATED")
        else:
            self.log_message("Sensor activation status: NOT ACTIVATED")

    def display_sensor_properties(self):
        """显示传感器属性"""
        if not self.sensor_properties:
            self.log_message("No sensor properties to display")
            return

        self.log_message("\n" + "=" * 60)
        self.log_message("SENSOR PROPERTIES")
        self.log_message("=" * 60)

        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]
            self.log_message(f"Device Name: {sys_info.get('DN', 'N/A')}")
            self.log_message(f"Device Serial: {sys_info.get('DS', 'N/A')}")

        self.log_message("=" * 60)

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
        self.log_message("Data stream stopped")

    def enable_config_buttons(self):
        """启用配置按钮"""
        self.log_message("Config buttons enabled")

    def reset_calibration_state(self):
        """重置校准状态"""
        self.is_calibrating = False
        self.log_message("Calibration state reset")

    def update_position_display(self):
        """更新位置显示"""
        if hasattr(self, 'calibration_workflow') and self.position_var:
            self.position_var.set(self.calibration_workflow.position_progress)
