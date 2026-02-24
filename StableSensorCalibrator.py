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
from datetime import datetime
import hashlib
import secrets
import re
import matplotlib
import atexit
import functools
from collections import deque

from sensor_calibrator import Config, validate_ssid, validate_password, validate_port, validate_url

matplotlib.use("TkAgg")

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


class StableSensorCalibrator:
    def __init__(self):
        # 初始化所有变量...
        self.ser = None
        self.is_reading = False
        self.data_queue = queue.Queue(maxsize=Config.MAX_QUEUE_SIZE)
        self.update_interval = Config.UPDATE_INTERVAL_MS

        # 数据存储 (using deque for efficient memory management)
        self.time_data = deque(maxlen=Config.MAX_DATA_POINTS)
        self.mpu_accel_data = [deque(maxlen=Config.MAX_DATA_POINTS) for _ in range(3)]
        self.mpu_gyro_data = [deque(maxlen=Config.MAX_DATA_POINTS) for _ in range(3)]
        self.adxl_accel_data = [deque(maxlen=Config.MAX_DATA_POINTS) for _ in range(3)]
        self.gravity_mag_data = deque(maxlen=Config.MAX_DATA_POINTS)

        # 时间跟踪
        self.data_start_time = None
        self.packet_count = 0
        self.expected_frequency = Config.EXPECTED_FREQUENCY

        # 统计数据
        self.serial_freq = 0
        self.last_freq_update = time.time()

        # 坐标模式状态
        self.current_coordinate_mode = None
        self.packets_received = 0

        # 统计信息存储
        self.stats_window_size = Config.STATS_WINDOW_SIZE
        self.real_time_stats = {
            "mpu_accel_mean": [0, 0, 0],
            "mpu_accel_std": [0, 0, 0],
            "adxl_accel_mean": [0, 0, 0],
            "adxl_accel_std": [0, 0, 0],
            "mpu_gyro_mean": [0, 0, 0],
            "mpu_gyro_std": [0, 0, 0],
            "gravity_mean": 0,
            "gravity_std": 0,
        }

        # 传感器属性存储
        self.sensor_properties = {}
        self.mac_address = None
        self.generated_key = None
        self.sensor_activated = False

        # 监控状态
        self.is_monitoring = False
        self.monitoring_position = 0
        self.monitoring_data = []
        self.monitoring_duration = 3
        self.monitoring_samples_needed = 300

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
        self.calibration_file = "calibration_params.json"

        # 位置定义
        self.position_names = [
            "+X axis down (X = +9.81 m/s²)",
            "-X axis down (X = -9.81 m/s²)",
            "+Y axis down (Y = +9.81 m/s²)",
            "-Y axis down (Y = -9.81 m/s²)",
            "+Z axis down (Z = +9.81 m/s²)",
            "-Z axis down (Z = -9.81 m/s²)",
        ]

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

        # 新增：退出标志
        self.exiting = False

        # 新增：after任务ID存储
        self.after_tasks = []

        # 设置GUI
        self.setup_gui()

    def setup_gui(self):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.root = tk.Tk()
        self.root.tk.call("tk", "scaling", 1.2)
        self.root.title("MPU6050 & ADXL355 Sensor Calibration System")
        self.root.geometry("1920x1080")  # 减小初始窗口尺寸

        # 设置窗口关闭协议
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        atexit.register(self.cleanup)

        # 设置窗口图标
        try:
            self.root.iconbitmap(default="icon.ico")
        except Exception:
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
        left_panel = ttk.Frame(main_frame, width=430)  # 增加宽度
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        # left_panel.grid_propagate(False)  # 禁止自动调整大小

        # 配置左侧面板网格
        left_panel.grid_rowconfigure(0, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # 创建可滚动的左侧面板
        canvas = tk.Canvas(left_panel, highlightthickness=0, width=430)  # 设置画布宽度
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, width=430)  # 设置滚动框架宽度

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

        # 左侧面板内容
        self.setup_left_panel(scrollable_frame)

        # ========== 右侧图表区域 ==========
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # 创建图表
        self.setup_plots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
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
            except Exception:
                pass

        self.log_message("清理完成，程序即将退出")
        time.sleep(0.5)  # 短暂延迟确保清理完成

    def cancel_all_after_tasks(self):
        """取消所有after任务"""
        for task_id in self.after_tasks:
            try:
                self.root.after_cancel(task_id)
            except Exception:
                pass
        self.after_tasks.clear()

    def stop_data_stream_safe(self):
        """安全停止数据流"""
        try:
            self.is_reading = False
            if hasattr(self, "ser") and self.ser and self.ser.is_open:
                try:
                    self.ser.write(b"SS:0\n")
                    self.ser.flush()
                except Exception:
                    pass

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
                time.sleep(0.1)

        # 清除数据队列
        if hasattr(self, "data_queue"):
            try:
                while not self.data_queue.empty():
                    self.data_queue.get_nowait()
            except Exception:
                pass

        # 清空数据缓冲区
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

    def setup_left_panel(self, parent):
        """设置左侧控制面板内容 - 优化布局，减少空隙"""
        style = ttk.Style()
        style.configure("Compact.TLabelframe", padding=12)  # 减少内边距
        # style.configure("Compact.TLabelframe.Label", font=("Arial", 9, "bold"))

        # 标题
        title_label = ttk.Label(
            parent, text="Calibration Panel", font=("Arial", 12, "bold")  # 减小字体
        )
        title_label.pack(pady=(0, 6))  # 减少下边距

        # ===== 串口设置 =====
        serial_frame = ttk.LabelFrame(
            parent, text="Serial Settings", style="Compact.TLabelframe"
        )
        serial_frame.pack(fill="x", pady=(0, 5))  # 减少下边距

        # 使用网格布局，更加紧凑
        serial_grid = ttk.Frame(serial_frame)
        serial_grid.pack(fill="x", padx=3, pady=2)  # 减少内边距

        # 第一行：端口和刷新按钮
        port_row = ttk.Frame(serial_grid)
        port_row.pack(fill="x", pady=1)

        ttk.Label(port_row, text="Port:", font=("Arial", 9)).pack(side="left", padx=2)
        self.port_var = StringVar()
        self.port_combo = ttk.Combobox(
            port_row,
            textvariable=self.port_var,
            width=15,  # 增加宽度
            state="readonly",
            font=("Arial", 9),
        )
        self.port_combo.pack(side="left", padx=2, fill="x", expand=True)

        self.refresh_btn = ttk.Button(
            port_row, text="Refresh", command=self.refresh_ports, width=8
        )
        self.refresh_btn.pack(side="left", padx=2)

        # 第二行：波特率和连接按钮
        baud_row = ttk.Frame(serial_grid)
        baud_row.pack(fill="x", pady=1)

        ttk.Label(baud_row, text="Baud:", font=("Arial", 9)).pack(side="left", padx=2)
        self.baud_var = StringVar(value="115200")
        baud_combo = ttk.Combobox(
            baud_row,
            textvariable=self.baud_var,
            values=["9600", "19200", "38400", "57600", "115200"],
            width=8,
            state="readonly",
            font=("Arial", 9),
        )
        baud_combo.pack(side="left", padx=2)

        self.connect_btn = ttk.Button(
            baud_row, text="Connect", command=self.toggle_connection, width=8
        )
        self.connect_btn.pack(side="left", padx=2)

        # ===== 数据流控制 =====
        stream_frame = ttk.LabelFrame(
            parent, text="Data Stream", style="Compact.TLabelframe"  # 缩短标题
        )
        stream_frame.pack(fill="x", pady=(0, 5))

        stream_content = ttk.Frame(stream_frame)
        stream_content.pack(fill="x", padx=3, pady=2)

        # 单行布局：按钮和频率显示
        stream_row = ttk.Frame(stream_content)
        stream_row.pack(fill="x", pady=2)

        self.data_btn = ttk.Button(
            stream_row,
            text="Start RawData",
            command=self.toggle_data_stream,
            state="disabled",
            width=12,  # 减小按钮宽度
        )
        self.data_btn.pack(side="left", padx=1)

        self.data_btn2 = ttk.Button(
            stream_row,
            text="Start NormalData",
            command=self.toggle_data_stream2,
            state="disabled",
            width=12,  # 减小按钮宽度
        )
        self.data_btn2.pack(side="left", padx=2)

        # 频率显示
        freq_frame = ttk.Frame(stream_row)
        freq_frame.pack(side="left", padx=5)

        ttk.Label(freq_frame, text="Rate:", font=("Arial", 9)).pack(side="left", padx=1)
        self.freq_var = StringVar(value="0 Hz")
        freq_label = ttk.Label(
            freq_frame,
            textvariable=self.freq_var,
            foreground="green",
            font=("Arial", 9, "bold"),
        )
        freq_label.pack(side="left", padx=3)

        # ===== 坐标模式按钮 =====
        coord_row = ttk.Frame(stream_content)
        coord_row.pack(fill="x", pady=2)

        self.local_coord_btn = ttk.Button(
            coord_row,
            text="局部坐标模式",
            command=self.set_local_coordinate_mode,
            state="disabled",
            width=12,
        )
        self.local_coord_btn.pack(side="left", padx=1)

        self.global_coord_btn = ttk.Button(
            coord_row,
            text="整体坐标模式",
            command=self.set_global_coordinate_mode,
            state="disabled",
            width=12,
        )
        self.global_coord_btn.pack(side="left", padx=2)

        # ===== 校准控制 =====
        calib_frame = ttk.LabelFrame(
            parent, text="Calibration", style="Compact.TLabelframe"  # 缩短标题
        )
        calib_frame.pack(fill="x", pady=(0, 5))

        calib_content = ttk.Frame(calib_frame)
        calib_content.pack(fill="x", padx=3, pady=2)

        # 校准按钮
        btn_row = ttk.Frame(calib_content)
        btn_row.pack(fill="x", pady=1)

        self.calibrate_btn = ttk.Button(
            btn_row,
            text="Start Calib",
            command=self.start_calibration,
            state="disabled",
            width=12,
        )
        self.calibrate_btn.pack(side="left", padx=2)

        self.capture_btn = ttk.Button(
            btn_row,
            text="Capture Pos",
            command=self.capture_position,
            state="disabled",
            width=12,
        )
        self.capture_btn.pack(side="left", padx=2)

        # 位置显示
        self.position_label = ttk.Label(
            calib_content,
            text="Position: Not calibrating",
            font=("Arial", 9),
            # wraplength=350,  # 允许换行
        )
        self.position_label.pack(fill="x", padx=2, pady=1)

        # ===== 实时统计信息 =====
        stats_frame = ttk.LabelFrame(
            parent, text="Statistics", style="Compact.TLabelframe"  # 缩短标题
        )
        stats_frame.pack(fill="x", pady=(0, 5))

        # 紧凑统计显示，不使用Notebook节省空间
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill="x", padx=3, pady=2)

        # 存储统计标签
        self.stats_labels = {}

        # MPU6050加速度计统计
        mpu_accel_frame = ttk.LabelFrame(stats_grid, text="MPU Accel", padding=2)
        mpu_accel_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.setup_compact_stats(mpu_accel_frame, "MPU6050 Accel", "mpu_accel")

        # ADXL355加速度计统计
        adxl_accel_frame = ttk.LabelFrame(stats_grid, text="ADXL Accel", padding=2)
        adxl_accel_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        self.setup_compact_stats(adxl_accel_frame, "ADXL355 Accel", "adxl_accel")

        # MPU6050陀螺仪统计
        mpu_gyro_frame = ttk.LabelFrame(stats_grid, text="MPU Gyro", padding=2)
        mpu_gyro_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.setup_compact_stats(mpu_gyro_frame, "MPU6050 Gyro", "mpu_gyro")

        # 重力矢量统计
        gravity_frame = ttk.LabelFrame(stats_grid, text="Gravity", padding=2)
        gravity_frame.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)

        ttk.Label(
            gravity_frame, text="Gravity Magnitude:", font=("Arial", 8, "bold")
        ).pack(anchor="w", padx=2, pady=1)

        gravity_stats_frame = ttk.Frame(gravity_frame)
        gravity_stats_frame.pack(fill="x", padx=5, pady=1)

        gravity_mean_var = StringVar(value="Mean: 0.000")
        ttk.Label(
            gravity_stats_frame, textvariable=gravity_mean_var, font=("Courier", 8)
        ).pack(anchor="w")

        gravity_std_var = StringVar(value="Std: 0.000")
        ttk.Label(
            gravity_stats_frame, textvariable=gravity_std_var, font=("Courier", 8)
        ).pack(anchor="w")

        self.stats_labels["gravity_mean"] = gravity_mean_var
        self.stats_labels["gravity_std"] = gravity_std_var

        # 配置网格权重
        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)
        stats_grid.rowconfigure(0, weight=1)
        stats_grid.rowconfigure(1, weight=1)

        # ===== 命令控制 =====
        cmd_frame = ttk.LabelFrame(parent, text="Commands", style="Compact.TLabelframe")
        cmd_frame.pack(fill="x", pady=(0, 5))

        cmd_content = ttk.Frame(cmd_frame)
        cmd_content.pack(fill="x", padx=3, pady=2)

        # 两行按钮布局
        row1 = ttk.Frame(cmd_content)
        row1.pack(fill="x", pady=1)

        self.send_btn = ttk.Button(
            row1,
            text="Send Commands",
            command=self.send_all_commands,
            state="disabled",
            width=15,
        )
        self.send_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.save_btn = ttk.Button(
            row1,
            text="Save Params",
            command=self.save_calibration_parameters,
            state="disabled",
            width=15,
        )
        self.save_btn.pack(side="left", padx=2, expand=True, fill="x")

        row2 = ttk.Frame(cmd_content)
        row2.pack(fill="x", pady=1)

        self.read_props_btn = ttk.Button(
            row2,
            text="Read Props",
            command=self.read_sensor_properties,
            state="disabled",
            width=15,
        )
        self.read_props_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.resend_btn = ttk.Button(
            row2,
            text="Resend",
            command=self.resend_all_commands,
            state="disabled",
            width=15,
        )
        self.resend_btn.pack(side="left", padx=2, expand=True, fill="x")

        # ===== 传感器激活 =====
        activation_frame = ttk.LabelFrame(
            parent, text="Activation", style="Compact.TLabelframe"  # 缩短标题
        )
        activation_frame.pack(fill="x", pady=(0, 5))

        activation_content = ttk.Frame(activation_frame)
        activation_content.pack(fill="x", padx=3, pady=2)

        # 两行布局
        act_row1 = ttk.Frame(activation_content)
        act_row1.pack(fill="x", pady=1)

        ttk.Label(act_row1, text="MAC:", font=("Arial", 9)).pack(side="left", padx=2)
        self.mac_var = StringVar(value="Not detected")
        mac_label = ttk.Label(
            act_row1, textvariable=self.mac_var, foreground="blue", font=("Arial", 9)
        )
        mac_label.pack(side="left", padx=2, fill="x", expand=True)

        act_row2 = ttk.Frame(activation_content)
        act_row2.pack(fill="x", pady=1)

        ttk.Label(act_row2, text="Status:", font=("Arial", 9)).pack(side="left", padx=2)
        self.activation_status_var = StringVar(value="Not activated")
        self.status_label = ttk.Label(
            act_row2,
            textvariable=self.activation_status_var,
            foreground="red",
            font=("Arial", 9),
        )
        self.status_label.pack(side="left", padx=2, fill="x", expand=True)

        # 按钮行
        act_btn_row = ttk.Frame(activation_content)
        act_btn_row.pack(fill="x", pady=2)

        self.activate_btn = ttk.Button(
            act_btn_row,
            text="Activate",
            command=self.activate_sensor,
            state="disabled",
            width=10,
        )
        self.activate_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.verify_btn = ttk.Button(
            act_btn_row,
            text="Verify",
            command=self.verify_activation,
            state="disabled",
            width=10,
        )
        self.verify_btn.pack(side="left", padx=2, expand=True, fill="x")

        # ===== 状态显示 =====
        status_frame = ttk.LabelFrame(
            parent, text="Status", style="Compact.TLabelframe"  # 缩短标题
        )
        status_frame.pack(fill="x", pady=(0, 5))

        status_content = ttk.Frame(status_frame)
        status_content.pack(fill="x", padx=3, pady=2)

        self.status_var = StringVar(value="Ready")
        status_label = ttk.Label(
            status_content,
            textvariable=self.status_var,
            font=("Arial", 9),
            foreground="blue",
        )
        status_label.pack(pady=1)

        # ===== WiFi设置 =====
        wifi_frame = ttk.LabelFrame(
            parent, text="WiFi Settings", style="Compact.TLabelframe"
        )
        wifi_frame.pack(fill="x", pady=(0, 5))

        wifi_content = ttk.Frame(wifi_frame)
        wifi_content.pack(fill="x", padx=5, pady=2)

        # SSID设置
        ssid_frame = ttk.Frame(wifi_content)
        ssid_frame.pack(fill="x", pady=1)

        ttk.Label(ssid_frame, text="SSID:", font=("Arial", 9)).pack(side="left", padx=2)
        self.ssid_var = StringVar()
        ssid_entry = ttk.Entry(
            ssid_frame, textvariable=self.ssid_var, font=("Arial", 9), width=20
        )
        ssid_entry.pack(side="left", padx=2, fill="x", expand=True)

        # 密码设置
        password_frame = ttk.Frame(wifi_content)
        password_frame.pack(fill="x", pady=1)

        ttk.Label(password_frame, text="Password:", font=("Arial", 9)).pack(
            side="left", padx=2
        )
        self.password_var = StringVar()
        password_entry = ttk.Entry(
            password_frame,
            textvariable=self.password_var,
            show="*",
            font=("Arial", 9),
            width=20,
        )
        password_entry.pack(side="left", padx=2, fill="x", expand=True)

        # WiFi设置按钮
        wifi_btn_frame = ttk.Frame(wifi_content)
        wifi_btn_frame.pack(fill="x", pady=2)

        self.set_wifi_btn = ttk.Button(
            wifi_btn_frame,
            text="Set WiFi",
            command=self.set_wifi_config,
            state="disabled",
            width=10,
        )
        self.set_wifi_btn.pack(side="left", padx=2)

        self.read_wifi_btn = ttk.Button(
            wifi_btn_frame,
            text="Read WiFi",
            command=self.read_wifi_config,
            state="disabled",
            width=10,
        )
        self.read_wifi_btn.pack(side="left", padx=2)

        # ===== MQTT设置 =====
        mqtt_frame = ttk.LabelFrame(
            parent, text="MQTT Settings", style="Compact.TLabelframe"
        )
        mqtt_frame.pack(fill="x", pady=(0, 5))

        mqtt_content = ttk.Frame(mqtt_frame)
        mqtt_content.pack(fill="x", padx=5, pady=2)

        # MQTT代理设置
        broker_frame = ttk.Frame(mqtt_content)
        broker_frame.pack(fill="x", pady=1)

        ttk.Label(broker_frame, text="Broker:", font=("Arial", 9)).pack(
            side="left", padx=2
        )
        self.mqtt_broker_var = StringVar()
        broker_entry = ttk.Entry(
            broker_frame, textvariable=self.mqtt_broker_var, font=("Arial", 9), width=20
        )
        broker_entry.pack(side="left", padx=2, fill="x", expand=True)

        # 用户名设置
        user_frame = ttk.Frame(mqtt_content)
        user_frame.pack(fill="x", pady=1)

        ttk.Label(user_frame, text="Username:", font=("Arial", 9)).pack(
            side="left", padx=2
        )
        self.mqtt_user_var = StringVar()
        user_entry = ttk.Entry(
            user_frame, textvariable=self.mqtt_user_var, font=("Arial", 9), width=20
        )
        user_entry.pack(side="left", padx=2, fill="x", expand=True)

        # 密码设置
        mqtt_pwd_frame = ttk.Frame(mqtt_content)
        mqtt_pwd_frame.pack(fill="x", pady=1)

        ttk.Label(mqtt_pwd_frame, text="Password:", font=("Arial", 9)).pack(
            side="left", padx=2
        )
        self.mqtt_password_var = StringVar()
        mqtt_pwd_entry = ttk.Entry(
            mqtt_pwd_frame,
            textvariable=self.mqtt_password_var,
            show="*",
            font=("Arial", 9),
            width=20,
        )
        mqtt_pwd_entry.pack(side="left", padx=2, fill="x", expand=True)

        # 端口设置
        port_frame = ttk.Frame(mqtt_content)
        port_frame.pack(fill="x", pady=1)

        ttk.Label(port_frame, text="Port:", font=("Arial", 9)).pack(side="left", padx=2)
        self.mqtt_port_var = StringVar(value="1883")
        port_entry = ttk.Entry(
            port_frame, textvariable=self.mqtt_port_var, font=("Arial", 9), width=10
        )
        port_entry.pack(side="left", padx=2)

        # MQTT设置按钮
        mqtt_btn_frame = ttk.Frame(mqtt_content)
        mqtt_btn_frame.pack(fill="x", pady=2)

        self.set_mqtt_btn = ttk.Button(
            mqtt_btn_frame,
            text="Set MQTT",
            command=self.set_mqtt_config,
            state="disabled",
            width=10,
        )
        self.set_mqtt_btn.pack(side="left", padx=2)

        self.read_mqtt_btn = ttk.Button(
            mqtt_btn_frame,
            text="Read MQTT",
            command=self.read_mqtt_config,
            state="disabled",
            width=10,
        )
        self.read_mqtt_btn.pack(side="left", padx=2)
        # =====OTA设置 =====
        OTA_frame = ttk.LabelFrame(
            parent, text="OTA Settings", style="Compact.TLabelframe"
        )
        OTA_frame.pack(fill="x", pady=(0, 5))

        OTA_content = ttk.Frame(OTA_frame)
        OTA_content.pack(fill="x", padx=5, pady=2)

        # URL1设置
        URL1_frame = ttk.Frame(OTA_content)
        URL1_frame.pack(fill="x", pady=1)

        ttk.Label(URL1_frame, text="URL1:", font=("Arial", 9)).pack(side="left", padx=2)
        self.URL1_var = StringVar()
        URL1_entry = ttk.Entry(
            URL1_frame, textvariable=self.URL1_var, font=("Arial", 9), width=20
        )
        URL1_entry.pack(side="left", padx=2, fill="x", expand=True)
        # URL2设置
        URL2_frame = ttk.Frame(OTA_content)
        URL2_frame.pack(fill="x", pady=1)

        ttk.Label(URL2_frame, text="URL2:", font=("Arial", 9)).pack(side="left", padx=2)
        self.URL2_var = StringVar()
        URL2_entry = ttk.Entry(
            URL2_frame, textvariable=self.URL2_var, font=("Arial", 9), width=20
        )
        URL2_entry.pack(side="left", padx=2, fill="x", expand=True)
        # URL3设置
        URL3_frame = ttk.Frame(OTA_content)
        URL3_frame.pack(fill="x", pady=1)

        ttk.Label(URL3_frame, text="URL3:", font=("Arial", 9)).pack(side="left", padx=2)
        self.URL3_var = StringVar()
        URL3_entry = ttk.Entry(
            URL3_frame, textvariable=self.URL3_var, font=("Arial", 9), width=20
        )
        URL3_entry.pack(side="left", padx=2, fill="x", expand=True)
        # URL1设置
        URL4_frame = ttk.Frame(OTA_content)
        URL4_frame.pack(fill="x", pady=1)

        ttk.Label(URL4_frame, text="URL4:", font=("Arial", 9)).pack(side="left", padx=2)
        self.URL4_var = StringVar()
        URL4_entry = ttk.Entry(
            URL4_frame, textvariable=self.URL4_var, font=("Arial", 9), width=20
        )
        URL4_entry.pack(side="left", padx=2, fill="x", expand=True)
        # MQTT设置按钮
        OTA_btn_frame = ttk.Frame(OTA_content)
        OTA_btn_frame.pack(fill="x", pady=2)

        self.set_OTA_btn = ttk.Button(
            OTA_btn_frame,
            text="Set OTA",
            command=self.set_OTA_config,
            state="disabled",
            width=10,
        )
        self.set_OTA_btn.pack(side="left", padx=2)

        self.read_OTA_btn = ttk.Button(
            OTA_btn_frame,
            text="Read OTA",
            command=self.read_OTA_config,
            state="disabled",
            width=10,
        )
        self.read_OTA_btn.pack(side="left", padx=2)

    def set_wifi_config(self):
        """设置WiFi配置"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        ssid = self.ssid_var.get().strip()
        password = self.password_var.get().strip()

        valid, error = validate_ssid(ssid)
        if not valid:
            self.log_message(f"Error: {error}")
            return

        valid, error = validate_password(password)
        if not valid:
            self.log_message(f"Error: {error}")
            return

        wifi_cmd = f"SET:WF,{ssid},{password}"

        self.log_message(f"Setting WiFi configuration: SSID={ssid}")

        # 在新线程中发送命令
        threading.Thread(
            target=self.send_config_command, args=(wifi_cmd, "WiFi"), daemon=True
        ).start()

    def set_OTA_config(self):
        """设置OTA配置"""
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        URL1 = self.URL1_var.get().strip()
        URL2 = self.URL2_var.get().strip()
        URL3 = self.URL3_var.get().strip()
        URL4 = self.URL4_var.get().strip()

        for i, url in enumerate([URL1, URL2, URL3, URL4], 1):
            if url:
                valid, error = validate_url(url)
                if not valid:
                    self.log_message(f"Error: URL{i} {error}")
                    return

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
        else:
            valid, error = validate_port(port)
            if not valid:
                self.log_message(f"Error: {error}")
                return

        valid, error = validate_password(password)
        if not valid:
            self.log_message(f"Error: {error}")
            return

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
            time.sleep(0.5)

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

                time.sleep(0.1)

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

    def setup_compact_stats(self, parent, title, sensor_key):
        """设置紧凑的统计信息显示"""
        ttk.Label(parent, text=title, font=("Arial", 9, "bold")).pack(
            anchor="w", padx=2, pady=2
        )

        axes = ["X", "Y", "Z"]
        for i, axis in enumerate(axes):
            axis_frame = ttk.Frame(parent)
            axis_frame.pack(fill="x", padx=5, pady=1)

            ttk.Label(axis_frame, text=f"{axis}:", width=2, font=("Arial", 8)).pack(
                side="left"
            )

            # 均值标签
            mean_var = StringVar(value="0.000")
            mean_label = ttk.Label(
                axis_frame, textvariable=mean_var, font=("Courier", 9)
            )
            mean_label.pack(side="left", padx=3)

            # 标准差标签
            std_var = StringVar(value="0.000")
            std_label = ttk.Label(axis_frame, textvariable=std_var, font=("Courier", 9))
            std_label.pack(side="left", padx=3)

            # 存储标签引用
            self.stats_labels[f"{sensor_key}_{axis.lower()}_mean"] = mean_var
            self.stats_labels[f"{sensor_key}_{axis.lower()}_std"] = std_var

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

    def setup_plots(self):
        """设置matplotlib图表"""
        self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 9))
        self.fig.suptitle("Sensor Data Visualization with Statistics", fontsize=14)

        # 设置全局字体大小
        plt.rcParams["font.size"] = 10
        plt.rcParams["axes.titlesize"] = 12
        plt.rcParams["axes.labelsize"] = 11
        plt.rcParams["legend.fontsize"] = 10

        self.fig.suptitle("Sensor Data Visualization with Statistics", fontsize=14)

        # 设置子图
        colors = ["#ff4444", "#44ff44", "#4444ff"]  # 红, 绿, 蓝
        labels = ["X", "Y", "Z"]

        # MPU6050加速度计
        self.ax1 = self.axes[0, 0]
        self.ax1.set_title(
            "MPU6050 Accelerometer (m/s²)", fontweight="bold", fontsize=12
        )
        self.ax1.set_ylabel("Acceleration", fontsize=11)
        self.ax1.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        self.ax1.set_facecolor("#ffffff")

        # 添加统计信息文本框
        self.ax1_stats_text = self.ax1.text(
            0.02,
            0.98,
            "",
            transform=self.ax1.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        self.mpu_accel_lines = []
        for i in range(3):
            (line,) = self.ax1.plot(
                [], [], color=colors[i], label=labels[i], linewidth=1.5, alpha=0.8
            )
            self.mpu_accel_lines.append(line)
        self.ax1.legend(loc="upper right", fontsize=10)  # 减小字体

        # ADXL355加速度计
        self.ax2 = self.axes[0, 1]
        self.ax2.set_title(
            "ADXL355 Accelerometer (m/s²)", fontweight="bold", fontsize=12
        )
        self.ax2.set_ylabel("Acceleration", fontsize=11)
        self.ax2.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        self.ax2.set_facecolor("#ffffff")

        self.ax2_stats_text = self.ax2.text(
            0.02,
            0.98,
            "",
            transform=self.ax2.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        self.adxl_accel_lines = []
        for i in range(3):
            (line,) = self.ax2.plot(
                [], [], color=colors[i], label=labels[i], linewidth=1.5, alpha=0.8
            )
            self.adxl_accel_lines.append(line)
        self.ax2.legend(loc="upper right", fontsize=8)

        # MPU6050陀螺仪
        self.ax3 = self.axes[1, 0]
        self.ax3.set_title("MPU6050 Gyroscope (rad/s)", fontweight="bold", fontsize=12)
        self.ax3.set_ylabel("Angular Velocity", fontsize=11)
        self.ax3.set_xlabel("Time (s)", fontsize=11)
        self.ax3.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        self.ax3.set_facecolor("#ffffff")

        self.ax3_stats_text = self.ax3.text(
            0.02,
            0.98,
            "",
            transform=self.ax3.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        self.mpu_gyro_lines = []
        for i in range(3):
            (line,) = self.ax3.plot(
                [], [], color=colors[i], label=labels[i], linewidth=1.5, alpha=0.8
            )
            self.mpu_gyro_lines.append(line)
        self.ax3.legend(loc="upper right", fontsize=8)

        # 重力矢量模长
        self.ax4 = self.axes[1, 1]
        self.ax4.set_title(
            "Gravity Vector Magnitude (m/s²)", fontweight="bold", fontsize=11
        )
        self.ax4.set_ylabel("Magnitude", fontsize=10)
        self.ax4.set_xlabel("Sample", fontsize=10)
        self.ax4.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        self.ax4.set_facecolor("#ffffff")

        self.ax4_stats_text = self.ax4.text(
            0.02,
            0.98,
            "",
            transform=self.ax4.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        (self.gravity_line,) = self.ax4.plot(
            [], [], color="#ff9900", label="Gravity", linewidth=2.0, alpha=0.8
        )
        self.ax4.legend(loc="upper right", fontsize=8)

        # 设置初始坐标轴范围
        self.ax1.set_xlim(0, 10)
        self.ax2.set_xlim(0, 10)
        self.ax3.set_xlim(0, 10)
        self.ax4.set_xlim(0, 200)

        self.ax1.set_ylim(-20, 20)
        self.ax2.set_ylim(-20, 20)
        self.ax3.set_ylim(-10, 10)
        self.ax4.set_ylim(0, 20)

        plt.tight_layout()

    def refresh_ports(self):
        """刷新可用串口列表"""
        ports = []
        try:
            for port in serial.tools.list_ports.comports():
                ports.append(port.device)
        except Exception:
            pass

        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)

    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        self.root.after(0, functools.partial(self._add_log_entry, log_entry))

    def _add_log_entry(self, log_entry):
        """在主线程中添加日志条目"""
        self.log_text.insert(tk.END, log_entry + "\n")
        self.log_text.see(tk.END)

    def toggle_connection(self):
        """切换串口连接"""
        if self.ser is None or not self.ser.is_open:
            self.connect_serial()
            if self.ser is not None and self.ser.is_open:
                self.read_props_btn.config(state="normal")
        else:
            self.disconnect_serial()

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
                time.sleep(0.5)  # 等待断开完成

            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=0.1,
                write_timeout=1,
                rtscts=False,  # 禁用硬件流控制
                dsrdtr=False,  # 禁用硬件流控制
            )

            # 清空缓冲区
            time.sleep(0.5)  # 等待串口稳定
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            self.connect_btn.config(text="Disconnect")
            self.data_btn.config(state="normal")
            self.data_btn2.config(state="normal")
            self.local_coord_btn.config(state="normal")
            self.global_coord_btn.config(state="normal")
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

        self.ser = None
        self.connect_btn.config(text="Connect")
        self.data_btn.config(text="Start Data Stream")
        self.data_btn.config(state="disabled")
        # self.monitor_btn.config(state="disabled")
        self.calibrate_btn.config(state="disabled")
        self.send_btn.config(state="disabled")
        self.local_coord_btn.config(state="disabled")
        self.global_coord_btn.config(state="disabled")
        self.current_coordinate_mode = None
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

    def _start_stream_common(self, cmd: str, btn, calibrate_btn_state: str):
        """Common logic for starting data streams"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(f"{cmd}\n".encode())
                self.ser.flush()

                self.is_reading = True
                btn.config(text="Stop Data Stream")
                self.calibrate_btn.config(state=calibrate_btn_state)

                self.clear_data()
                self.data_start_time = time.time()
                self.packet_count = 0
                self.packets_received = 0

                self.log_message(f"Data stream started with command: {cmd}")

                self.serial_thread = threading.Thread(
                    target=self.read_serial_data, daemon=True
                )
                self.serial_thread.start()
                self.schedule_update_gui()

            except Exception as e:
                self.log_message(f"Error starting data stream: {str(e)}")
                self.is_reading = False
                btn.config(text="Start Data Stream")
                btn.config(state="normal")
        else:
            self.log_message("Error: Not connected to serial port or port not open!")

    def start_data_stream(self):
        """开始原始数据流"""
        self._start_stream_common("SS:0", self.data_btn, "normal")

    def start_data_stream2(self):
        """开始校准数据流"""
        self._start_stream_common("SS:1", self.data_btn2, "disabled")

    def _stop_stream_common(self, btn, log_prefix: str):
        """Common logic for stopping data streams"""
        if not hasattr(self, "is_reading") or not self.is_reading:
            return

        self.is_reading = False

        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b"SS:4\n")
                self.ser.flush()
                self.log_message(f"{log_prefix} stopped with command: SS:4")
            except Exception as e:
                self.log_message(f"Error stopping data stream: {str(e)}")

        if hasattr(self, "data_btn"):
            self.data_btn.config(text="Start Data Stream")
            self.data_btn.config(state="normal")

        if hasattr(btn, "config"):
            btn.config(text="Start Data Stream")
            btn.config(state="normal")

        if hasattr(self, "calibrate_btn"):
            self.calibrate_btn.config(state="disabled")

        if hasattr(self, "capture_btn"):
            self.capture_btn.config(state="disabled")

        self.log_message(f"{log_prefix} stopped")

    def stop_data_stream(self):
        """停止原始数据流"""
        self._stop_stream_common(self.data_btn, "Data stream")

    def stop_data_stream2(self):
        """停止校准数据流"""
        self._stop_stream_common(self.data_btn2, "Data calibration")

    def set_local_coordinate_mode(self):
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        try:
            self.ser.write(b"SS:2\n")
            self.ser.flush()
            self.current_coordinate_mode = 'local'

            self.local_coord_btn.config(state="disabled")
            self.global_coord_btn.config(state="normal")

            self.log_message("Coordinate mode set to: LOCAL (SS:2)")

        except Exception as e:
            self.log_message(f"Error setting local coordinate mode: {str(e)}")

    def set_global_coordinate_mode(self):
        if not self.ser or not self.ser.is_open:
            self.log_message("Error: Not connected to serial port!")
            return

        try:
            self.ser.write(b"SS:3\n")
            self.ser.flush()
            self.current_coordinate_mode = 'global'

            self.local_coord_btn.config(state="normal")
            self.global_coord_btn.config(state="disabled")

            self.log_message("Coordinate mode set to: GLOBAL (SS:3)")

        except Exception as e:
            self.log_message(f"Error setting global coordinate mode: {str(e)}")

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
                time.sleep(0.001)

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
                time.sleep(0.1)  # 错误时等待更长时间
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    self.log_message(f"Unexpected error in serial reading: {str(e)}")
                    break
                time.sleep(0.05)

        # 如果因为错误退出，确保状态正确
        if self.is_reading:
            self.log_message("Serial reading thread exited unexpectedly")
            self.is_reading = False
            if hasattr(self, "data_btn"):
                self.root.after(
                    0, lambda: self.data_btn.config(text="Start Data Stream")
                )

    def parse_sensor_data(self, data_string):
        """解析传感器数据"""
        try:
            parts = data_string.split(",")
            if len(parts) >= 9:
                values = []
                for part in parts[:9]:
                    try:
                        values.append(float(part.strip()))
                    except (ValueError, TypeError):
                        values.append(0.0)

                mpu_accel = values[0:3]
                mpu_gyro = values[3:6]
                adxl_accel = values[6:9]

                return mpu_accel, mpu_gyro, adxl_accel
        except (AttributeError, ValueError, TypeError):
            pass

        return None, None, None

    def clear_data(self):
        """清空所有数据"""
        self.time_data.clear()
        for d in self.mpu_accel_data:
            d.clear()
        for d in self.mpu_gyro_data:
            d.clear()
        for d in self.adxl_accel_data:
            d.clear()
        self.gravity_mag_data.clear()

    def calculate_statistics(self, data_array, start_idx=None, end_idx=None):
        """计算统计信息"""
        if not data_array or len(data_array) == 0:
            return 0, 0

        if start_idx is None:
            start_idx = 0
        if end_idx is None:
            end_idx = len(data_array)

        # 获取数据片段 - convert to list for deque compatibility
        segment = list(data_array)[start_idx:end_idx]

        if len(segment) == 0:
            return 0, 0

        # 计算均值和标准差
        mean_val = np.mean(segment)
        std_val = np.std(segment)

        return mean_val, std_val

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
            time.sleep(0.5)

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

                time.sleep(0.1)

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
            time.sleep(0.5)

            # 发送SS:7命令获取最新属性
            self.ser.write(b"SS:8\n")
            self.ser.flush()

            time.sleep(2.0)

            # 读取响应
            response_bytes = b""
            start_time = time.time()
            timeout = 10.0

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

                time.sleep(0.1)

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
        """更新激活状态显示"""
        if self.sensor_activated:
            self.status_var.set("Activated")
            # 确保status_label存在
            if hasattr(self, "status_label"):
                self.status_label.config(foreground="green")
            if hasattr(self, "activate_btn"):
                self.activate_btn.config(state="disabled")
        else:
            self.status_var.set("Not activated")
            if hasattr(self, "status_label"):
                self.status_label.config(foreground="red")
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
        """更新GUI - 主更新循环"""
        if self.exiting or not hasattr(self, "root") or not self.root:
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

                        processed_count += 1

                    except queue.Empty:
                        break
                    except Exception as e:
                        continue
                # 更新统计信息
                self.safe_update_statistics()

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
        """更新统计信息 - 修复键名访问"""
        if len(self.time_data) < 10:  # 至少有10个数据点
            return

        # 计算最近数据的统计信息
        window_size = min(self.stats_window_size, len(self.time_data))
        start_idx = len(self.time_data) - window_size

        # 定义传感器键名映射
        sensor_key_map = {
            "mpu_accel": "mpu_accel",
            "adxl_accel": "adxl_accel",
            "mpu_gyro": "mpu_gyro",
        }

        axis_names = ["x", "y", "z"]

        # 更新MPU6050加速度计统计
        for i in range(3):
            if len(self.mpu_accel_data[i]) >= window_size:
                mean_val, std_val = self.calculate_statistics(
                    self.mpu_accel_data[i], start_idx
                )
                self.real_time_stats["mpu_accel_mean"][i] = mean_val
                self.real_time_stats["mpu_accel_std"][i] = std_val

                # 使用统一的键名
                sensor_key = "mpu_accel"
                mean_key = f"{sensor_key}_{axis_names[i]}_mean"
                std_key = f"{sensor_key}_{axis_names[i]}_std"

                # 安全访问，避免KeyError
                if mean_key in self.stats_labels:
                    self.stats_labels[mean_key].set(f"Mean: {mean_val:6.3f}")
                if std_key in self.stats_labels:
                    self.stats_labels[std_key].set(f"Std: {std_val:6.3f}")

        # 更新ADXL355加速度计统计
        for i in range(3):
            if len(self.adxl_accel_data[i]) >= window_size:
                mean_val, std_val = self.calculate_statistics(
                    self.adxl_accel_data[i], start_idx
                )
                self.real_time_stats["adxl_accel_mean"][i] = mean_val
                self.real_time_stats["adxl_accel_std"][i] = std_val

                sensor_key = "adxl_accel"
                mean_key = f"{sensor_key}_{axis_names[i]}_mean"
                std_key = f"{sensor_key}_{axis_names[i]}_std"

                if mean_key in self.stats_labels:
                    self.stats_labels[mean_key].set(f"Mean: {mean_val:6.3f}")
                if std_key in self.stats_labels:
                    self.stats_labels[std_key].set(f"Std: {std_val:6.3f}")

        # 更新MPU6050陀螺仪统计
        for i in range(3):
            if len(self.mpu_gyro_data[i]) >= window_size:
                mean_val, std_val = self.calculate_statistics(
                    self.mpu_gyro_data[i], start_idx
                )
                self.real_time_stats["mpu_gyro_mean"][i] = mean_val
                self.real_time_stats["mpu_gyro_std"][i] = std_val

                sensor_key = "mpu_gyro"
                mean_key = f"{sensor_key}_{axis_names[i]}_mean"
                std_key = f"{sensor_key}_{axis_names[i]}_std"

                if mean_key in self.stats_labels:
                    self.stats_labels[mean_key].set(f"Mean: {mean_val:6.3f}")
                if std_key in self.stats_labels:
                    self.stats_labels[std_key].set(f"Std: {std_val:6.3f}")

        # 更新重力矢量统计
        if len(self.gravity_mag_data) >= window_size:
            mean_val, std_val = self.calculate_statistics(
                self.gravity_mag_data, start_idx
            )
            self.real_time_stats["gravity_mean"] = mean_val
            self.real_time_stats["gravity_std"] = std_val

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
        """更新图表 - 安全版本"""
        if (
            self.exiting
            or not hasattr(self, "time_data")
            or not self.time_data
            or len(self.time_data) < 2
        ):
            return

        try:
            # 获取当前时间
            current_time = self.time_data[-1] if self.time_data else 0

            # 设置X轴范围，显示最近10秒的数据
            time_window = 10.0
            x_min = max(0, current_time - time_window)
            x_max = current_time

            # 确保有足够的数据点
            if len(self.time_data) > 1:
                # 更新MPU6050加速度计图表
                for i in range(3):
                    if (
                        len(self.mpu_accel_data[i]) >= len(self.time_data) - 5
                        and len(self.mpu_accel_lines) > i
                    ):
                        self.mpu_accel_lines[i].set_data(
                            self.time_data, self.mpu_accel_data[i]
                        )

                # 更新ADXL355加速度计图表
                for i in range(3):
                    if (
                        len(self.adxl_accel_data[i]) >= len(self.time_data) - 5
                        and len(self.adxl_accel_lines) > i
                    ):
                        self.adxl_accel_lines[i].set_data(
                            self.time_data, self.adxl_accel_data[i]
                        )

                # 更新MPU6050陀螺仪图表
                for i in range(3):
                    if (
                        len(self.mpu_gyro_data[i]) >= len(self.time_data) - 5
                        and len(self.mpu_gyro_lines) > i
                    ):
                        self.mpu_gyro_lines[i].set_data(
                            self.time_data, self.mpu_gyro_data[i]
                        )

                # 更新重力矢量模长图表
                if len(self.gravity_mag_data) >= len(self.time_data) - 5 and hasattr(
                    self, "gravity_line"
                ):
                    display_points = min(len(self.time_data), 200)
                    start_idx = max(0, len(self.time_data) - display_points)
                    sample_numbers = list(range(display_points))
                    self.gravity_line.set_data(
                        sample_numbers, list(self.gravity_mag_data)[start_idx:]
                    )
                    if hasattr(self, "ax4"):
                        self.ax4.set_xlim(0, display_points)

                # 更新X轴范围
                if hasattr(self, "ax1"):
                    self.ax1.set_xlim(x_min, x_max)
                if hasattr(self, "ax2"):
                    self.ax2.set_xlim(x_min, x_max)
                if hasattr(self, "ax3"):
                    self.ax3.set_xlim(x_min, x_max)

                # 动态调整Y轴范围
                self.adjust_y_limits()

                # 更新图表统计信息显示
                self.update_chart_statistics()

                # 重绘画布
                if hasattr(self, "canvas"):
                    self.canvas.draw_idle()

        except Exception as e:
            # 忽略绘图错误
            pass

    def update_chart_statistics(self):
        """更新图表中的统计信息文本"""
        # MPU6050加速度计统计文本
        stats_text1 = f"Recent Stats (last {self.stats_window_size} samples):\n"
        for i, axis in enumerate(["X", "Y", "Z"]):
            stats_text1 += (
                f"{axis}: μ={self.real_time_stats['mpu_accel_mean'][i]:6.3f} "
                f"σ={self.real_time_stats['mpu_accel_std'][i]:6.3f}\n"
            )
        self.ax1_stats_text.set_text(stats_text1)

        # ADXL355加速度计统计文本
        stats_text2 = f"Recent Stats (last {self.stats_window_size} samples):\n"
        for i, axis in enumerate(["X", "Y", "Z"]):
            stats_text2 += (
                f"{axis}: μ={self.real_time_stats['adxl_accel_mean'][i]:6.3f} "
                f"σ={self.real_time_stats['adxl_accel_std'][i]:6.3f}\n"
            )
        self.ax2_stats_text.set_text(stats_text2)

        # MPU6050陀螺仪统计文本
        stats_text3 = f"Recent Stats (last {self.stats_window_size} samples):\n"
        for i, axis in enumerate(["X", "Y", "Z"]):
            stats_text3 += (
                f"{axis}: μ={self.real_time_stats['mpu_gyro_mean'][i]:6.3f} "
                f"σ={self.real_time_stats['mpu_gyro_std'][i]:6.3f}\n"
            )
        self.ax3_stats_text.set_text(stats_text3)

        # 重力矢量统计文本
        stats_text4 = f"Recent Stats (last {self.stats_window_size} samples):\n"
        stats_text4 += f"Mean: {self.real_time_stats['gravity_mean']:6.3f}\n"
        stats_text4 += f"Std: {self.real_time_stats['gravity_std']:6.3f}"
        self.ax4_stats_text.set_text(stats_text4)

    def adjust_y_limits(self):
        """调整Y轴范围"""
        # MPU6050加速度计
        if self.mpu_accel_data[0] and len(self.mpu_accel_data[0]) > 0:
            recent_points = min(200, len(self.mpu_accel_data[0]))
            start_idx = max(0, len(self.mpu_accel_data[0]) - recent_points)

            recent_data = []
            for i in range(3):
                if len(self.mpu_accel_data[i]) >= start_idx + recent_points:
                    recent_data.extend(list(self.mpu_accel_data[i])[start_idx:])

            if recent_data:
                y_min = min(recent_data) - 2
                y_max = max(recent_data) + 2

                # 确保范围合理
                if abs(y_max - y_min) < 1:
                    y_min = -10
                    y_max = 10

                self.ax1.set_ylim(y_min, y_max)

        # ADXL355加速度计
        if self.adxl_accel_data[0] and len(self.adxl_accel_data[0]) > 0:
            recent_points = min(200, len(self.adxl_accel_data[0]))
            start_idx = max(0, len(self.adxl_accel_data[0]) - recent_points)

            recent_data = []
            for i in range(3):
                if len(self.adxl_accel_data[i]) >= start_idx + recent_points:
                    recent_data.extend(list(self.adxl_accel_data[i])[start_idx:])

            if recent_data:
                y_min = min(recent_data) - 2
                y_max = max(recent_data) + 2

                if abs(y_max - y_min) < 1:
                    y_min = -10
                    y_max = 10

                self.ax2.set_ylim(y_min, y_max)

        # MPU6050陀螺仪
        if self.mpu_gyro_data[0] and len(self.mpu_gyro_data[0]) > 0:
            recent_points = min(200, len(self.mpu_gyro_data[0]))
            start_idx = max(0, len(self.mpu_gyro_data[0]) - recent_points)

            recent_data = []
            for i in range(3):
                if len(self.mpu_gyro_data[i]) >= start_idx + recent_points:
                    recent_data.extend(list(self.mpu_gyro_data[i])[start_idx:])

            if recent_data:
                y_min = min(recent_data) - 1
                y_max = max(recent_data) + 1

                if abs(y_max - y_min) < 0.5:
                    y_min = -5
                    y_max = 5

                self.ax3.set_ylim(y_min, y_max)

        # 重力矢量模长
        if self.gravity_mag_data and len(self.gravity_mag_data) > 0:
            recent_points = min(200, len(self.gravity_mag_data))
            start_idx = max(0, len(self.gravity_mag_data) - recent_points)

            recent_data = list(self.gravity_mag_data)[start_idx:]

            if recent_data:
                y_min = max(0, min(recent_data) - 2)
                y_max = max(recent_data) + 2

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
                    data_string = self.data_queue.get(timeout=0.1)
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
                    time.sleep(0.01)  # 短暂休眠
                    continue

            if samples_collected >= 10:  # 至少有10个样本
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
                    except Exception:
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
                    "Parameters also saved to default file: calibration_params.json"
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
            time.sleep(0.5)

            # 第三步：发送SS:7命令获取属性
            self.root.after(0, lambda: self.log_message("Sending SS:8 command..."))
            self.ser.write(b"SS:8\n")
            self.ser.flush()

            # 第四步：等待并读取响应
            time.sleep(2.0)  # 等待设备响应

            response_bytes = b""
            start_time = time.time()
            timeout = 10.0  # 10秒超时

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

                            if 1:
                                self.root.after(0, self.extract_network_config)

                            # 显示网络配置摘要
                            if 1:
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

                time.sleep(0.1)  # 短暂休眠

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

            with open("sensor_properties.json", "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            self.log_message(
                "Sensor properties automatically saved to: sensor_properties.json"
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
