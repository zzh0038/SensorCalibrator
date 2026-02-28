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

# Import configuration
from sensor_calibrator import Config, UIConfig, CalibrationConfig, SerialConfig, ChartManager, UIManager, DataProcessor

matplotlib.use("TkAgg")

# 配置matplotlib
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


class StableSensorCalibrator:
    def __init__(self):
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
            'read_properties': self.read_sensor_properties,
            'activate_sensor': self.activate_sensor,
            'verify_activation': self.verify_activation,
            'set_wifi_config': self.set_wifi_config,
            'read_wifi_config': self.read_wifi_config,
            'set_mqtt_config': self.set_mqtt_config,
            'read_mqtt_config': self.read_mqtt_config,
            'set_OTA_config': self.set_OTA_config,
            'read_OTA_config': self.read_OTA_config,
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
        self.read_btn = self.ui_manager.get_widget('read_btn')
        
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

    def schedule_update_gui(self):
        """调度GUI更新 - 安全版本"""
        if not self.exiting:
            self.after_tasks.append(
                self.root.after(self.update_interval, self.update_gui)
            )

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
        """设置WiFi配置"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        ssid = self.ssid_var.get().strip()
        password = self.password_var.get().strip()

        if not ssid:
            self.log_message("Error: WiFi SSID cannot be empty!")
            return

        # 构建WiFi设置命令
        wifi_cmd = f"SET:WF,{ssid},{password}"

        self.log_message(f"Setting WiFi configuration: SSID={ssid}")

        # 在新线程中发送命令
        threading.Thread(
            target=self.send_config_command, args=(wifi_cmd, "WiFi"), daemon=True
        ).start()

    def set_OTA_config(self):
        """设置MQTT配置"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        URL1 = self.URL1_var.get().strip()
        URL2 = self.URL2_var.get().strip()
        URL3 = self.URL3_var.get().strip()
        URL4 = self.URL4_var.get().strip()

        # 构建MQTT设置命令
        OTA_cmd = f"SET:OTA,{URL1},{URL2},{URL3},{URL4}"

        self.log_message(f"Setting OTA configuration: OTA={URL1},{URL2},{URL3},{URL4}")

        # 在新线程中发送命令
        threading.Thread(
            target=self.send_config_command, args=(OTA_cmd, "OTA"), daemon=True
        ).start()

    def set_mqtt_config(self):
        """设置MQTT配置"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        broker = self.mqtt_broker_var.get().strip()
        username = self.mqtt_user_var.get().strip()
        password = self.mqtt_password_var.get().strip()
        port = self.mqtt_port_var.get().strip()

        if not broker:
            self.log_message("Error: MQTT broker address cannot be empty!")
            return

        if not port:
            port = "1883"

        # 构建MQTT设置命令
        mqtt_cmd = f"SET:MQ,{broker},{port},{username},{password}"

        self.log_message(f"Setting MQTT configuration: Broker={broker}, Port={port}")

        # 在新线程中发送命令
        threading.Thread(
            target=self.send_config_command, args=(mqtt_cmd, "MQTT"), daemon=True
        ).start()

    def send_config_command(self, command, config_type):
        """发送配置命令"""
        try:
            # 停止数据流（如果正在运行）
            original_reading_state = self.is_reading
            if self.is_reading:
                self.root.after(
                    0,
                    lambda: self.log_message(
                        f"Stopping data stream for {config_type} configuration..."
                    ),
                )
                self.root.after(0, self.stop_data_stream)
                time.sleep(1.0)

            # 清空输入缓冲区
            self.ser.reset_input_buffer()
            time.sleep(Config.BUFFER_CLEAR_DELAY)

            # 发送配置命令
            full_cmd = f"{command}"
            self.ser.write(full_cmd.encode())
            self.ser.flush()

            self.root.after(0, lambda: self.log_message(f"Sent: {command}"))

            # 等待响应
            time.sleep(2.0)

            # 读取响应
            response_bytes = b""
            start_time = time.time()
            timeout = 5.0

            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    response_bytes += self.ser.read(self.ser.in_waiting)

                response_str = response_bytes.decode("utf-8", errors="ignore")

                if "success" in response_str.lower() or "ok" in response_str.lower():
                    self.root.after(
                        0,
                        lambda: self.log_message(
                            f"{config_type} configuration successful!"
                        ),
                    )
                    break

                time.sleep(Config.THREAD_ERROR_DELAY)

            if not response_bytes:
                self.root.after(
                    0,
                    lambda: self.log_message(
                        f"{config_type} configuration sent (no response)"
                    ),
                )
            else:
                # 显示响应内容
                response_text = response_str.strip()
                if response_text:
                    self.root.after(
                        0, lambda: self.log_message(f"Response: {response_text}")
                    )

            # 恢复数据流状态
            if original_reading_state and not self.is_reading:
                self.root.after(
                    0, lambda: self.log_message("Restarting data stream...")
                )
                time.sleep(1.0)
                self.root.after(0, self.start_data_stream)

        except Exception as e:
            self.root.after(
                0,
                lambda: self.log_message(
                    f"Error setting {config_type} configuration: {str(e)}"
                ),
            )

    def read_wifi_config(self):
        """读取WiFi配置"""
        self.log_message("Reading WiFi configuration from device...")
        self.read_sensor_properties()

    def read_mqtt_config(self):
        """读取MQTT配置"""
        self.log_message("Reading MQTT configuration from device...")
        self.read_sensor_properties()

    def read_OTA_config(self):
        """读取MQTT配置"""
        self.log_message("Reading MQTT configuration from device...")
        self.read_sensor_properties()

    def set_coordinate_mode(self, mode: int, mode_name: str) -> None:
        """设置坐标模式

        Args:
            mode: 模式编号 (2=局部坐标, 3=整体坐标)
            mode_name: 模式名称（用于日志显示）
        """
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        try:
            command = f"SS:{mode}\n".encode()
            self.ser.write(command)
            self.ser.flush()
            self.log_message(f"Sent: SS:{mode} ({mode_name})")
        except serial.SerialException as e:
            self.log_message(f"Serial error sending coordinate command: {str(e)}")
        except Exception as e:
            self.log_message(f"Unexpected error: {str(e)}")

    def set_local_coordinate_mode(self) -> None:
        """设置局部坐标模式 - 发送 SS:2 指令"""
        self.set_coordinate_mode(2, "Local Coordinate Mode")

    def set_global_coordinate_mode(self) -> None:
        """设置整体坐标模式 - 发送 SS:3 指令"""
        self.set_coordinate_mode(3, "Global Coordinate Mode")

    def send_ss_command(self, cmd_id: int, description: str = "",
                        log_success: bool = True, silent: bool = False) -> bool:
        """发送 SS 指令的通用方法

        Args:
            cmd_id: 指令编号 (0-9)
            description: 指令描述（用于日志）
            log_success: 是否记录成功日志
            silent: 是否静默模式（不记录错误日志）

        Returns:
            bool: 发送是否成功
        """
        if not self.ser or not self.ser.is_open:
            if not silent:
                self.log_message("Error: Not connected to serial port!")
            return False

        try:
            command = f"SS:{cmd_id}\n".encode()
            self.ser.write(command)
            self.ser.flush()
            if log_success and not silent:
                self.log_message(f"Sent: SS:{cmd_id}" + (f" ({description})" if description else ""))
            return True
        except serial.SerialException as e:
            if not silent:
                self.log_message(f"Serial error sending SS:{cmd_id}: {str(e)}")
            return False
        except Exception as e:
            if not silent:
                self.log_message(f"Unexpected error sending SS:{cmd_id}: {str(e)}")
            return False

    def send_ss0_start_stream(self) -> bool:
        """发送 SS:0 指令 - 开始数据流"""
        return self.send_ss_command(0, "Start Data Stream")

    def send_ss1_start_calibration(self) -> bool:
        """发送 SS:1 指令 - 开始校准流"""
        return self.send_ss_command(1, "Start Calibration Stream")

    def send_ss4_stop_stream(self) -> bool:
        """发送 SS:4 指令 - 停止数据流/校准"""
        return self.send_ss_command(4, "Stop Stream")

    def send_ss8_get_properties(self) -> bool:
        """发送 SS:8 指令 - 获取传感器属性"""
        return self.send_ss_command(8, "Get Sensor Properties")

    def extract_network_config(self):
        """从传感器属性中提取网络配置"""
        if not self.sensor_properties:
            return
        # 提取WiFi配置
        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]

            # WiFi配置
            ssid = sys_info.get("SSID", "")
            password = sys_info.get("PA", "")

            if ssid:
                self.ssid_var.set(ssid)
                self.wifi_params["ssid"] = ssid
            if password:
                self.password_var.set(password)
                self.wifi_params["password"] = password

            # MQTT配置
            broker = sys_info.get("MBR", "")
            port = sys_info.get("MPT", "1883")
            username = sys_info.get("MUS", "")
            password = sys_info.get("MPW", "")

            URL1 = sys_info.get("URL1", "")
            URL2 = sys_info.get("URL2", "")
            URL3 = sys_info.get("URL3", "")
            URL4 = sys_info.get("URL4", "")

            if broker:
                self.mqtt_broker_var.set(broker)
                self.mqtt_params["broker"] = broker
            if username:
                self.mqtt_user_var.set(username)
                self.mqtt_params["username"] = username
            if password:
                self.mqtt_password_var.set(password)
                self.mqtt_params["password"] = password
            if port:
                self.mqtt_port_var.set(str(port))
                self.mqtt_params["port"] = str(port)

            if URL1:
                self.URL1_var.set(URL1)
                self.ota_params["URL1"] = URL1
            if URL2:
                self.URL2_var.set(URL2)
                self.ota_params["URL2"] = URL2
            if URL3:
                self.URL3_var.set(URL3)
                self.ota_params["URL3"] = URL3
            if URL4:
                self.URL4_var.set(URL4)
                self.ota_params["URL4"] = URL4
            # 启用设置按钮
            self.root.after(0, self.enable_config_buttons)

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
        if hasattr(self, "set_OTA_btn"):
            self.set_OTA_btn.config(state="normal")
        if hasattr(self, "read_OTA_btn"):
            self.read_OTA_btn.config(state="normal")
        if hasattr(self, "local_coord_btn"):
            self.local_coord_btn.config(state="normal")
        if hasattr(self, "global_coord_btn"):
            self.global_coord_btn.config(state="normal")

    def display_network_summary(self):
        """显示网络配置摘要"""
        if not self.sensor_properties:
            return

        self.log_message("\n" + "=" * 50)
        self.log_message("NETWORK CONFIGURATION SUMMARY")
        self.log_message("=" * 50)

        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]

            # WiFi信息
            ssid = sys_info.get("SSID", "Not set")
            self.log_message(f"WiFi SSID: {ssid}")
            self.log_message(
                f"WiFi Password: {'*' * 8 if sys_info.get('PA') else 'Not set'}"
            )

            # MQTT信息
            broker = sys_info.get("MBR", "Not set")
            username = sys_info.get("MUS", "Not set")
            port = sys_info.get("MPT", "Not set")

            self.log_message(f"MQTT Broker: {broker}")
            self.log_message(f"MQTT Username: {username}")
            self.log_message(f"MQTT Port: {port}")
            self.log_message(
                f"MQTT Password: {'*' * 8 if sys_info.get('MPW') else 'Not set'}"
            )

        self.log_message("=" * 50)

    def save_network_config(self):
        """保存网络配置到文件"""
        try:
            config_data = {
                "timestamp": datetime.now().isoformat(),
                "wifi_config": self.wifi_params,
                "mqtt_config": self.mqtt_params,
            }

            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"network_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )

            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)

                self.log_message(f"Network configuration saved to: {filename}")

        except Exception as e:
            self.log_message(f"Error saving network configuration: {str(e)}")

    def load_network_config(self):
        """从文件加载网络配置"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                with open(filename, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # 加载WiFi配置
                if "wifi_config" in config_data:
                    wifi_config = config_data["wifi_config"]
                    self.ssid_var.set(wifi_config.get("ssid", ""))
                    self.password_var.set(wifi_config.get("password", ""))

                # 加载MQTT配置
                if "mqtt_config" in config_data:
                    mqtt_config = config_data["mqtt_config"]
                    self.mqtt_broker_var.set(mqtt_config.get("broker", ""))
                    self.mqtt_user_var.set(mqtt_config.get("username", ""))
                    self.mqtt_password_var.set(mqtt_config.get("password", ""))
                    self.mqtt_port_var.set(mqtt_config.get("port", "1883"))

                self.log_message(f"Network configuration loaded from: {filename}")
                self.enable_config_buttons()

        except Exception as e:
            self.log_message(f"Error loading network configuration: {str(e)}")

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
        ports = []
        try:
            for port in serial.tools.list_ports.comports():
                ports.append(port.device)
        except:
            pass

        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)

    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        # 在主线程中更新UI
        self.root.after(0, lambda: self._add_log_entry(log_entry))

    def _add_log_entry(self, log_entry):
        """在主线程中添加日志条目"""
        self.log_text.insert(tk.END, log_entry + "\n")
        self.log_text.see(tk.END)

    def toggle_connection(self):
        """切换串口连接"""
        if self.ser is None or not self.ser.is_open:
            self.connect_serial()
        else:
            self.disconnect_serial()
        self.read_props_btn.config(state="normal")

    def connect_serial(self):
        """连接串口 - 添加更好的状态管理"""
        port = self.port_var.get()
        baudrate = int(self.baud_var.get())

        if not port:
            self.log_message("Error: No port selected!")
            return

        try:
            # 确保之前的状态被清理
            if hasattr(self, "ser") and self.ser and self.ser.is_open:
                self.disconnect_serial()
                time.sleep(SerialConfig.DISCONNECT_DELAY)  # 等待断开完成

            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=SerialConfig.TIMEOUT,
                write_timeout=SerialConfig.WRITE_TIMEOUT,
                rtscts=SerialConfig.RTSCTS,  # 禁用硬件流控制
                dsrdtr=SerialConfig.DSRDTR,  # 禁用硬件流控制
            )

            # 清空缓冲区
            time.sleep(SerialConfig.CONNECT_DELAY)  # 等待串口稳定
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            self.connect_btn.config(text="Disconnect")
            self.data_btn.config(state="normal")
            self.data_btn2.config(state="normal")
            self.log_message(f"Connected to {port} at {baudrate} baud")

            # 重置数据流状态
            self.is_reading = False
            if hasattr(self, "data_btn"):
                self.data_btn.config(text="Start Data Stream")

            self.is_reading = False
            if hasattr(self, "data_btn2"):
                self.data_btn2.config(text="Start CAS Stream")

        except Exception as e:
            self.log_message(f"Error connecting to {port}: {str(e)}")
            # 连接失败时确保状态正确
            self.ser = None
            if hasattr(self, "connect_btn"):
                self.connect_btn.config(text="Connect")
            if hasattr(self, "data_btn"):
                self.data_btn.config(state="disabled")
            if hasattr(self, "data_btn2"):
                self.data_btn2.config(state="disabled")

    def disconnect_serial(self):
        """断开串口连接"""
        if self.is_reading:
            self.stop_data_stream()

        if self.ser and self.ser.is_open:
            self.ser.close()

        # 新增：禁用按钮
        self.read_props_btn.config(state="disabled")
        self.resend_btn.config(state="disabled")
        if hasattr(self, "local_coord_btn"):
            self.local_coord_btn.config(state="disabled")
        if hasattr(self, "global_coord_btn"):
            self.global_coord_btn.config(state="disabled")

        self.ser = None
        self.connect_btn.config(text="Connect")
        self.data_btn.config(text="Start Data Stream")
        self.data_btn.config(state="disabled")
        # self.monitor_btn.config(state="disabled")
        self.calibrate_btn.config(state="disabled")
        self.send_btn.config(state="disabled")
        self.log_message("Disconnected from serial port")

    def toggle_data_stream(self):
        """切换数据流状态 - 修复版本"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        if not self.is_reading:
            self.start_data_stream()
        else:
            self.stop_data_stream()

    def toggle_data_stream2(self):
        """切换数据流状态 - 修复版本"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        if not self.is_reading:
            self.start_data_stream2()
        else:
            self.stop_data_stream2()

    def start_data_stream(self):
        """开始数据流 - 修复版本"""
        if self.ser and self.ser.is_open:
            try:
                if self.send_ss0_start_stream():
                    # 设置状态标志
                    self.is_reading = True
                    self.data_btn.config(text="Stop Data Stream")
                    self.calibrate_btn.config(state="normal")

                    # 重置数据和时间
                    self.clear_data()
                    self.data_start_time = time.time()
                    self.packet_count = 0
                    self.packets_received = 0  # 重置包计数

                    self.log_message("Data stream started with command: SS:0")

                    # 启动串口读取线程
                    self.serial_thread = threading.Thread(
                        target=self.read_serial_data, daemon=True
                    )
                    self.serial_thread.start()

                    # 确保GUI更新循环运行
                    self.schedule_update_gui()
            except Exception as e:
                self.log_message(f"Error starting data stream: {str(e)}")
                # 发生错误时重置状态
                self.is_reading = False
                self.data_btn.config(text="Start Data Stream")
                self.data_btn.config(state="normal")
        else:
            self.log_message("Error: Not connected to serial port or port not open!")

    def start_data_stream2(self):
        """开始数据流 - 修复版本"""
        if self.ser and self.ser.is_open:
            try:
                if self.send_ss1_start_calibration():
                    # 设置状态标志
                    self.is_reading = True
                    self.data_btn2.config(text="starting Calibration Stream")
                    self.calibrate_btn.config(state="disabled")

                    # 重置数据和时间
                    self.clear_data()
                    self.data_start_time = time.time()
                    self.packet_count = 0
                    self.packets_received = 0  # 重置包计数

                    self.log_message("calibration stream started with command: SS:1")

                    # 启动串口读取线程
                    self.serial_thread = threading.Thread(
                        target=self.read_serial_data, daemon=True
                    )
                    self.serial_thread.start()

                    # 确保GUI更新循环运行
                    self.schedule_update_gui()
            except Exception as e:
                self.log_message(f"Error starting data stream: {str(e)}")
                # 发生错误时重置状态
                self.is_reading = False
                self.data_btn2.config(text="Start calibration Stream")
                self.data_btn2.config(state="normal")
        else:
            self.log_message("Error: Not connected to serial port or port not open!")

    def stop_data_stream(self):
        """停止数据流 - 修复版本"""
        if not hasattr(self, "is_reading") or not self.is_reading:
            return

        self.is_reading = False

        if self.ser and self.ser.is_open:
            self.send_ss4_stop_stream()  # 发送 SS:4 停止命令

        # 更新UI状态
        if hasattr(self, "data_btn"):
            self.data_btn.config(text="Start Data Stream")
            self.data_btn.config(state="normal")

        if hasattr(self, "calibrate_btn"):
            self.calibrate_btn.config(state="disabled")

        if hasattr(self, "capture_btn"):
            self.capture_btn.config(state="disabled")

        self.log_message("Data stream stopped")

    def stop_data_stream2(self):
        """停止数据流 - 修复版本"""
        if not hasattr(self, "is_reading") or not self.is_reading:
            return

        self.is_reading = False

        if self.ser and self.ser.is_open:
            self.send_ss4_stop_stream()  # 发送 SS:4 停止命令

        # 更新UI状态
        if hasattr(self, "data_btn2"):
            self.data_btn2.config(text="Stop calibration Stream")
            self.data_btn2.config(state="normal")

        if hasattr(self, "calibrate_btn"):
            self.calibrate_btn.config(state="disabled")

        if hasattr(self, "capture_btn"):
            self.capture_btn.config(state="disabled")

        self.log_message("Data calibration stopped")

    def read_serial_data(self):
        """读取串口数据 - 修复版本，添加更好的错误处理"""
        buffer = ""
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.is_reading and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    # 读取可用数据
                    data = self.ser.read(self.ser.in_waiting).decode(
                        "ascii", errors="ignore"
                    )
                    buffer += data

                    # 处理完整行
                    lines = buffer.split("\n")
                    buffer = lines[-1]  # 保留不完整的行

                    for line in lines[:-1]:
                        line = line.strip()
                        if line and not line.startswith("SS:"):  # 过滤命令回显
                            # 非阻塞方式放入队列
                            try:
                                if not self.data_queue.full():
                                    self.data_queue.put_nowait(line)
                                    self.packets_received += 1
                                    consecutive_errors = 0  # 重置错误计数
                                else:
                                    # 队列满时丢弃最旧的数据
                                    try:
                                        self.data_queue.get_nowait()
                                        self.data_queue.put_nowait(line)
                                    except queue.Empty:
                                        pass
                            except queue.Full:
                                # 队列满，跳过此数据点
                                pass

                # 短暂休眠，避免过度占用CPU
                # 优化：使用自适应睡眠策略，有数据时快速轮询，无数据时降低频率
                if self.ser.in_waiting > 0:
                    time.sleep(SerialConfig.READ_SLEEP_DATA)  # 有数据时快速处理
                else:
                    time.sleep(SerialConfig.READ_SLEEP_IDLE)   # 无数据时降低轮询频率，减少CPU占用

                # 检查连接状态
                if not self.ser or not self.ser.is_open:
                    break

            except serial.SerialException as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    self.log_message(
                        f"Multiple serial errors, stopping data stream: {str(e)}"
                    )
                    break
                time.sleep(Config.THREAD_ERROR_DELAY)  # 错误时等待更长时间
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    self.log_message(f"Unexpected error in serial reading: {str(e)}")
                    break
                time.sleep(Config.PARSE_RETRY_DELAY)

        # 如果因为错误退出，确保状态正确
        if self.is_reading:
            self.log_message("Serial reading thread exited unexpectedly")
            self.is_reading = False
            if hasattr(self, "data_btn"):
                self.root.after(
                    0, lambda: self.data_btn.config(text="Start Data Stream")
                )

    def parse_sensor_data(self, data_string):
        """解析传感器数据 - 委托给 DataProcessor"""
        return self.data_processor.parse_sensor_data(data_string)

    def clear_data(self):
        """清空所有数据 - 委托给 DataProcessor"""
        self.data_processor.clear_all()

    def calculate_statistics(self, data_array, start_idx=None, end_idx=None):
        """计算统计信息 - 委托给 DataProcessor"""
        return self.data_processor.calculate_statistics(data_array, start_idx, end_idx)

    def generate_key_from_mac(self, mac_address):
        """
        基于MAC地址生成64字符的SHA-256密钥
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

        return hex_digest

    def verify_key(self, input_key, mac_address):
        """
        验证输入的密钥是否与基于MAC地址生成的密钥匹配
        """
        # 生成预期密钥
        expected_key = self.generate_key_from_mac(mac_address)
        expected_key2 = expected_key[5:12]
        # 使用恒定时间比较防止时序攻击
        if len(input_key) != 7 or len(expected_key) != 64:
            return False

        return secrets.compare_digest(input_key.lower(), expected_key2.lower())

    def extract_mac_from_properties(self):
        """从传感器属性中提取MAC地址"""
        if not self.sensor_properties:
            return None

        # 在sys字段中查找MAC地址
        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]

            # 尝试不同的MAC地址字段名
            mac_keys = ["MAC", "mac", "mac_address", "macAddress", "device_mac"]
            for key in mac_keys:
                if key in sys_info:
                    mac_value = sys_info[key]
                    if self.validate_mac_address(mac_value):
                        return mac_value

            # 在设备名称中查找MAC地址模式
            if "DN" in sys_info:
                dn_value = sys_info["DN"]
                mac_pattern = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
                match = re.search(mac_pattern, dn_value)
                if match:
                    return match.group()

        return None

    def validate_mac_address(self, mac_str):
        """验证MAC地址格式"""
        if not mac_str or not isinstance(mac_str, str):
            return False

        # MAC地址格式验证：XX:XX:XX:XX:XX:XX 或 XX-XX-XX-XX-XX-XX
        mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        return re.match(mac_pattern, mac_str) is not None

    def check_activation_status(self):
        """检查传感器激活状态"""
        if not self.sensor_properties or not self.mac_address:
            return False

        # 从属性中获取AKS字段
        aks_value = None
        if "sys" in self.sensor_properties:
            sys_info = self.sensor_properties["sys"]
            aks_value = (
                sys_info.get("AKY") or sys_info.get("aky") or sys_info.get("ak_key")
            )

        if not aks_value:
            return False

        # 验证密钥
        try:
            is_activated = self.verify_key(aks_value, self.mac_address)
            return is_activated
        except Exception as e:
            self.log_message(f"Error verifying activation key: {str(e)}")
            return False

    def activate_sensor(self):
        """激活传感器"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        if not self.mac_address or not self.generated_key:
            self.log_message("Error: MAC address or generated key not available!")
            return

        self.log_message("Starting sensor activation process...")

        # 在新线程中激活传感器
        threading.Thread(target=self.activate_sensor_thread, daemon=True).start()

    def activate_sensor_thread(self):
        """在新线程中激活传感器"""
        try:
            # 停止数据流（如果正在运行）
            original_reading_state = self.is_reading
            if self.is_reading:
                self.root.after(
                    0,
                    lambda: self.log_message("Stopping data stream for activation..."),
                )
                self.root.after(0, self.stop_data_stream)
                time.sleep(1.0)

            # 清空输入缓冲区
            self.ser.reset_input_buffer()
            time.sleep(Config.BUFFER_CLEAR_DELAY)

            # 发送激活命令
            activation_cmd = f"SET:AKY,{self.generated_key[5:12]}"
            self.ser.write(activation_cmd.encode())
            self.ser.flush()

            self.root.after(
                0,
                lambda: self.log_message(
                    f"Sent activation command: SET:AKY,{self.generated_key}"
                ),
            )

            # 等待响应
            time.sleep(2.0)

            # 读取响应
            response_bytes = b""
            start_time = time.time()
            timeout = 5.0

            self.root.after(0, lambda: self.log_message("Reading response..."))

            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    chunk = self.ser.read(self.ser.in_waiting)
                    response_bytes += chunk

                    response_str = response_bytes.decode("utf-8", errors="ignore")

                    if (
                        "success" in response_str.lower()
                        or "activated" in response_str.lower()
                    ):
                        self.root.after(
                            0, lambda: self.log_message("Sensor activation successful!")
                        )
                        self.sensor_activated = True
                        self.root.after(0, self.update_activation_status)
                        break

                time.sleep(Config.THREAD_ERROR_DELAY)

            if not self.sensor_activated:
                self.root.after(
                    0, lambda: self.log_message("Activation response timeout or failed")
                )

            # 恢复数据流状态
            if original_reading_state and not self.is_reading:
                self.root.after(
                    0, lambda: self.log_message("Restarting data stream...")
                )
                time.sleep(1.0)
                self.root.after(0, self.start_data_stream)

        except Exception as e:
            self.root.after(
                0, lambda: self.log_message(f"Error during activation: {str(e)}")
            )

    def verify_activation(self):
        """验证传感器激活状态"""
        self.log_message("Verifying sensor activation status...")

        # 重新读取传感器属性来获取最新的AKS值
        threading.Thread(target=self.verify_activation_thread, daemon=True).start()

    def verify_activation_thread(self):
        """在新线程中验证激活状态"""
        try:
            # 停止数据流
            original_reading_state = self.is_reading
            if self.is_reading:
                self.root.after(
                    0,
                    lambda: self.log_message(
                        "Stopping data stream for verification..."
                    ),
                )
                self.root.after(0, self.stop_data_stream)
                time.sleep(1.0)

            # 清空输入缓冲区
            self.ser.reset_input_buffer()
            time.sleep(Config.BUFFER_CLEAR_DELAY)

            # 发送SS:8命令获取最新属性
            self.send_ss8_get_properties()

            time.sleep(2.0)

            # 读取响应
            response_bytes = b""
            start_time = time.time()
            timeout = CalibrationConfig.TIMEOUT_PER_POSITION

            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    response_bytes += self.ser.read(self.ser.in_waiting)

                response_str = response_bytes.decode("utf-8", errors="ignore")
                json_start = response_str.find("{")
                json_end = response_str.rfind("}")

                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_str = response_str[json_start : json_end + 1]

                    try:
                        latest_properties = json.loads(json_str)
                        self.sensor_properties = latest_properties

                        # 检查激活状态
                        is_activated = self.check_activation_status()
                        self.sensor_activated = is_activated

                        self.root.after(0, self.update_activation_status)

                        if is_activated:
                            self.root.after(
                                0,
                                lambda: self.log_message(
                                    "✓ Sensor is properly activated!"
                                ),
                            )
                        else:
                            self.root.after(
                                0,
                                lambda: self.log_message(
                                    "✗ Sensor is not activated or activation key mismatch"
                                ),
                            )

                        break

                    except json.JSONDecodeError:
                        continue

                time.sleep(Config.THREAD_ERROR_DELAY)

            # 恢复数据流状态
            if original_reading_state and not self.is_reading:
                self.root.after(
                    0, lambda: self.log_message("Restarting data stream...")
                )
                time.sleep(1.0)
                self.root.after(0, self.start_data_stream)

        except Exception as e:
            self.root.after(
                0, lambda: self.log_message(f"Error during verification: {str(e)}")
            )

    def update_activation_status(self):
        """更新激活状态显示 - 同时更新 Activation 区域和 Status 区域"""
        if self.sensor_activated:
            # 更新下方 Status 区域
            self.status_var.set("Activated")
            # 更新 Activation 区域
            self.activation_status_var.set("Activated")
            if hasattr(self, "activation_status_label"):
                self.activation_status_label.config(foreground="green")
            if hasattr(self, "activate_btn"):
                self.activate_btn.config(state="disabled")
        else:
            # 更新下方 Status 区域
            self.status_var.set("Not activated")
            # 更新 Activation 区域
            self.activation_status_var.set("Not activated")
            if hasattr(self, "activation_status_label"):
                self.activation_status_label.config(foreground="red")
            if (
                hasattr(self, "activate_btn")
                and self.mac_address
                and self.generated_key
            ):
                self.activate_btn.config(state="normal")

    def extract_and_process_mac(self):
        """提取MAC地址并处理激活逻辑"""
        # 提取MAC地址
        self.mac_address = self.extract_mac_from_properties()

        if self.mac_address:
            # 确保mac_var存在
            if hasattr(self, "mac_var"):
                self.mac_var.set(self.mac_address)

            # 生成密钥
            try:
                self.generated_key = self.generate_key_from_mac(self.mac_address)
                self.log_message(
                    f"Generated activation key from MAC {self.mac_address}"
                )
                self.log_message(f"Key: {self.generated_key}")
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

            self.log_message(
                f"Sensor activation status: {'ACTIVATED' if self.sensor_activated else 'NOT ACTIVATED'}"
            )
        else:
            self.log_message("Warning: MAC address not found in sensor properties")
            if hasattr(self, "mac_var"):
                self.mac_var.set("Not found")

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
        
        # 性能优化：窗口移动期间跳过更新
        if Config.ENABLE_WINDOW_MOVE_PAUSE and self._window_moving:
            # 调度下一次更新
            if not self.exiting and hasattr(self, "root"):
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
        """开始校准"""
        if not self.is_reading:
            self.log_message("Error: Start data stream first!")
            return

        self.is_calibrating = True
        self.current_position = 0
        self.calibration_positions = []
        self.calibrate_btn.config(state="disabled")
        self.capture_btn.config(state="normal")
        self.data_btn.config(state="disabled")

        self.update_position_display()
        self.log_message("Starting 6-position calibration")
        self.log_message(f"Position 1: {self.position_names[0]}")
        self.log_message("Place sensor in position and click 'Capture Position'")

    def capture_position(self):
        """采集当前位置数据"""
        if not self.is_calibrating or self.current_position >= 6:
            return

        position = self.current_position

        # 禁用按钮防止重复点击
        self.capture_btn.config(state="disabled")
        self.log_message(f"Capturing data for position {position + 1}...")

        # 在新线程中采集数据
        threading.Thread(
            target=self.collect_calibration_data, args=(position,), daemon=True
        ).start()

    def collect_calibration_data(self, position):
        """采集校准数据"""
        try:
            mpu_accel_samples = []
            mpu_gyro_samples = []
            adxl_accel_samples = []

            start_time = time.time()
            samples_collected = 0

            # 采集数据
            while samples_collected < self.calibration_samples and self.is_reading:
                try:
                    # 从队列获取数据
                    data_string = self.data_queue.get(timeout=Config.QUICK_SLEEP)
                    mpu_accel, mpu_gyro, adxl_accel = self.parse_sensor_data(
                        data_string
                    )

                    if mpu_accel and mpu_gyro and adxl_accel:
                        mpu_accel_samples.append(mpu_accel)
                        mpu_gyro_samples.append(mpu_gyro)
                        adxl_accel_samples.append(adxl_accel)
                        samples_collected += 1

                    # 超时保护
                    if time.time() - start_time > 10:
                        self.root.after(
                            0,
                            lambda: self.log_message(
                                "Timeout: Stopping data collection"
                            ),
                        )
                        break

                except queue.Empty:
                    time.sleep(Config.QUICK_SLEEP)  # 短暂休眠
                    continue

            if samples_collected >= Config.CALIBRATION_SAMPLES // 10:  # 至少有10%的样本
                # 计算平均值
                mpu_accel_avg = np.mean(mpu_accel_samples, axis=0)
                mpu_gyro_avg = np.mean(mpu_gyro_samples, axis=0)
                adxl_accel_avg = np.mean(adxl_accel_samples, axis=0)

                # 计算标准差用于评估数据质量
                mpu_accel_std = np.std(mpu_accel_samples, axis=0)
                adxl_accel_std = np.std(adxl_accel_samples, axis=0)

                # 在主线程中更新
                self.root.after(
                    0,
                    lambda: self.process_calibration_data(
                        position,
                        samples_collected,
                        mpu_accel_avg,
                        mpu_gyro_avg,
                        adxl_accel_avg,
                        mpu_accel_std,
                        adxl_accel_std,
                    ),
                )
            else:
                self.root.after(
                    0,
                    lambda: self.log_message(
                        f"Error: Insufficient data collected for position {position + 1}"
                    ),
                )
                self.root.after(0, lambda: self.capture_btn.config(state="normal"))

        except Exception as e:
            self.root.after(
                0, lambda: self.log_message(f"Error in data collection: {str(e)}")
            )
            self.root.after(0, lambda: self.capture_btn.config(state="normal"))

    def process_calibration_data(
        self,
        position,
        samples_collected,
        mpu_accel_avg,
        mpu_gyro_avg,
        adxl_accel_avg,
        mpu_accel_std,
        adxl_accel_std,
    ):
        """处理校准数据"""
        # 存储校准数据
        self.calibration_positions.append(
            {
                "mpu_accel": mpu_accel_avg,
                "mpu_gyro": mpu_gyro_avg,
                "adxl_accel": adxl_accel_avg,
            }
        )

        # 记录数据质量信息
        self.log_message(
            f"Position {position + 1} captured: {samples_collected} samples"
        )
        self.log_message(
            f"  MPU6050: [{mpu_accel_avg[0]:.3f}, {mpu_accel_avg[1]:.3f}, {mpu_accel_avg[2]:.3f}]"
        )
        self.log_message(
            f"  ADXL355: [{adxl_accel_avg[0]:.3f}, {adxl_accel_avg[1]:.3f}, {adxl_accel_avg[2]:.3f}]"
        )
        self.log_message(
            f"  Data Quality - MPU6050 Noise: [{mpu_accel_std[0]:.4f}, {mpu_accel_std[1]:.4f}, {mpu_accel_std[2]:.4f}]"
        )

        self.current_position = position + 1

        if self.current_position < 6:
            self.update_position_display()
            self.log_message(
                f"Position {self.current_position + 1}: {self.position_names[self.current_position]}"
            )
            self.capture_btn.config(state="normal")
        else:
            self.finish_calibration()

    def update_position_display(self):
        """更新位置显示"""
        if self.current_position < 6:
            self.position_label.config(
                text=f"Position {self.current_position + 1}/6: {self.position_names[self.current_position]}"
            )
        else:
            self.position_label.config(text="Calibration complete!")

    def finish_calibration(self):
        """完成校准并计算参数"""
        self.log_message("Calculating calibration parameters...")

        if len(self.calibration_positions) != 6:
            self.log_message("Error: Need exactly 6 positions for calibration!")
            self.reset_calibration_state()
            return

        try:
            g = Config.GRAVITY_CONSTANT

            # 计算MPU6050加速度计参数
            mpu_scales = []
            mpu_offsets = []

            for axis in range(3):
                pos_idx = axis * 2
                neg_idx = axis * 2 + 1

                pos_val = self.calibration_positions[pos_idx]["mpu_accel"][axis]
                neg_val = self.calibration_positions[neg_idx]["mpu_accel"][axis]

                offset = (pos_val + neg_val) / 2.0
                delta = pos_val - neg_val

                if abs(delta) > 1e-6:
                    scale = delta / (2.0 * g)
                else:
                    scale = 1.0

                # 存储为1/scale用于校正
                scale_factor = 1.0 / scale if abs(scale) > 1e-6 else 1.0

                mpu_offsets.append(offset)
                mpu_scales.append(scale_factor)

            # 计算ADXL355加速度计参数
            adxl_scales = []
            adxl_offsets = []

            for axis in range(3):
                pos_idx = axis * 2
                neg_idx = axis * 2 + 1

                pos_val = self.calibration_positions[pos_idx]["adxl_accel"][axis]
                neg_val = self.calibration_positions[neg_idx]["adxl_accel"][axis]

                offset = (pos_val + neg_val) / 2.0
                delta = pos_val - neg_val

                if abs(delta) > 1e-6:
                    scale = delta / (2.0 * g)
                else:
                    scale = 1.0

                scale_factor = 1.0 / scale if abs(scale) > 1e-6 else 1.0

                adxl_offsets.append(offset)
                adxl_scales.append(scale_factor)

            # 计算陀螺仪偏移
            gyro_samples = []
            for pos in self.calibration_positions:
                gyro_samples.append(pos["mpu_gyro"])

            gyro_avg = np.mean(gyro_samples, axis=0)

            # 更新参数
            self.calibration_params = {
                "mpu_accel_scale": mpu_scales,
                "mpu_accel_offset": mpu_offsets,
                "adxl_accel_scale": adxl_scales,
                "adxl_accel_offset": adxl_offsets,
                "mpu_gyro_offset": gyro_avg.tolist(),
            }

            # 生成校准命令
            self.generate_calibration_commands()

            self.is_calibrating = False
            self.calibrate_btn.config(state="normal")
            self.capture_btn.config(state="disabled")
            self.data_btn.config(state="normal")
            self.send_btn.config(state="normal")

            self.log_message("Calibration completed successfully!")

        except Exception as e:
            self.log_message(f"Error calculating calibration: {str(e)}")
            self.reset_calibration_state()

    def generate_calibration_commands(self):
        """生成校准命令"""
        params = self.calibration_params

        commands = [
            f"SET:RACKS,{params['mpu_accel_scale'][0]:.6f},{params['mpu_accel_scale'][1]:.6f},{params['mpu_accel_scale'][2]:.6f}",
            f"SET:RACOF,{params['mpu_accel_offset'][0]:.6f},{params['mpu_accel_offset'][1]:.6f},{params['mpu_accel_offset'][2]:.6f}",
            f"SET:REACKS,{params['adxl_accel_scale'][0]:.6f},{params['adxl_accel_scale'][1]:.6f},{params['adxl_accel_scale'][2]:.6f}",
            f"SET:REACOF,{params['adxl_accel_offset'][0]:.6f},{params['adxl_accel_offset'][1]:.6f},{params['adxl_accel_offset'][2]:.6f}",
            f"SET:VROOF,{params['mpu_gyro_offset'][0]:.6f},{params['mpu_gyro_offset'][1]:.6f},{params['mpu_gyro_offset'][2]:.6f}",
        ]

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
