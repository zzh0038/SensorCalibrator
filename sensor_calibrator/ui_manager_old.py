"""
UIManager - 管理所有 GUI 组件

职责：
- 创建左侧面板的所有控件
- 管理控件状态（启用/禁用）
- 通过回调函数与主程序通信
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, StringVar
from typing import Dict, Callable, Optional, Any

from . import Config, SerialConfig
from .ui.theme import theme_manager, LightTheme


class UIManager:
    """
    管理 SensorCalibrator 的所有 GUI 组件
    
    通过回调函数与主类通信，保持松耦合
    """
    
    def __init__(self, parent: tk.Widget, callbacks: Dict[str, Callable]):
        """
        初始化 UI 管理器
        
        Args:
            parent: 父级容器（滚动框架）
            callbacks: 回调函数字典，包含所有按钮点击的处理函数
        """
        self.parent = parent
        self.callbacks = callbacks
        
        # 存储所有控件的引用
        self.widgets: Dict[str, Any] = {}
        self.vars: Dict[str, StringVar] = {}
        
        # 创建 UI
        self._setup_styles()
        self._setup_title()
        self._setup_serial_section()
        self._setup_data_stream_section()
        self._setup_calibration_section()
        self._setup_statistics_section()
        self._setup_commands_section()
        self._setup_coordinate_section()
        self._setup_activation_section()
        self._setup_network_notebook()  # 使用 Notebook 替代独立的 WiFi/MQTT/OTA 区域
        # 注意: Status section 已删除，状态信息显示在 Activation section 中
    
    def _setup_styles(self):
        """设置 ttk 样式 - 浅色现代主题"""
        style = ttk.Style()
        
        # 应用浅色主题
        t = LightTheme
        
        # 配置主框架
        self.parent.configure(background=t.BG_MAIN)
        
        # 配置主题管理器样式
        theme_manager.configure_styles(style)
        
        # 配置Labelframe样式
        style.configure(
            'Modern.TLabelframe',
            background=t.BG_CARD,
            borderwidth=1,
            relief='solid'
        )
        # 注意：TLabelframe.Label 样式配置在不同平台可能不同
        # 使用tk.Label替代ttk.Label来避免兼容性问题
    
    def _setup_title(self):
        """设置标题 - 现代风格"""
        t = LightTheme
        
        # 标题容器
        title_frame = tk.Frame(self.parent, bg=t.BG_MAIN)
        title_frame.pack(fill="x", pady=(10, 5))
        
        # 主标题
        title_label = tk.Label(
            title_frame,
            text="Sensor Calibration System",
            font=("Segoe UI", 16, "bold"),
            bg=t.BG_MAIN,
            fg=t.TEXT_PRIMARY
        )
        title_label.pack()
        
        # 副标题
        subtitle = tk.Label(
            title_frame,
            text="MPU6050 & ADXL355 Configuration Tool",
            font=("Segoe UI", 9),
            bg=t.BG_MAIN,
            fg=t.TEXT_SECONDARY
        )
        subtitle.pack()
    
    def _setup_serial_section(self):
        """设置串口设置区域"""
        serial_frame = ttk.LabelFrame(
            self.parent, text="Serial Settings", style="Compact.TLabelframe"
        )
        serial_frame.pack(fill="x", pady=(0, 5))
        
        serial_grid = ttk.Frame(serial_frame)
        serial_grid.pack(fill="x", padx=3, pady=2)
        
        # 端口行
        port_row = ttk.Frame(serial_grid)
        port_row.pack(fill="x", pady=1)
        
        ttk.Label(port_row, text="Port:", font=("Arial", 9)).pack(side="left", padx=2)
        
        port_var = StringVar()
        self.vars['port'] = port_var
        port_combo = ttk.Combobox(
            port_row,
            textvariable=port_var,
            width=15,
            state="readonly",
            font=("Arial", 9),
        )
        port_combo.pack(side="left", padx=2, fill="x", expand=True)
        self.widgets['port_combo'] = port_combo
        
        refresh_btn = ttk.Button(
            port_row, text="Refresh", 
            command=self.callbacks.get('refresh_ports', lambda: None),
            width=8
        )
        refresh_btn.pack(side="left", padx=2)
        self.widgets['refresh_btn'] = refresh_btn
        
        # 波特率行
        baud_row = ttk.Frame(serial_grid)
        baud_row.pack(fill="x", pady=1)
        
        ttk.Label(baud_row, text="Baud:", font=("Arial", 9)).pack(side="left", padx=2)
        
        baud_var = StringVar(value=str(Config.BAUDRATE_DEFAULT))
        self.vars['baud'] = baud_var
        baud_combo = ttk.Combobox(
            baud_row,
            textvariable=baud_var,
            values=[str(b) for b in SerialConfig.BAUD_RATES],
            width=8,
            state="readonly",
            font=("Arial", 9),
        )
        baud_combo.pack(side="left", padx=2)
        
        connect_btn = ttk.Button(
            baud_row, text="Connect",
            command=self.callbacks.get('toggle_connection', lambda: None),
            width=8
        )
        connect_btn.pack(side="left", padx=2)
        self.widgets['connect_btn'] = connect_btn
    
    def _setup_data_stream_section(self):
        """设置数据流控制区域"""
        stream_frame = ttk.LabelFrame(
            self.parent, text="Data Stream", style="Compact.TLabelframe"
        )
        stream_frame.pack(fill="x", pady=(0, 5))
        
        stream_content = ttk.Frame(stream_frame)
        stream_content.pack(fill="x", padx=3, pady=2)
        
        stream_row = ttk.Frame(stream_content)
        stream_row.pack(fill="x", pady=2)
        
        # RawData 按钮
        data_btn = ttk.Button(
            stream_row,
            text="Start RawData",
            command=self.callbacks.get('toggle_data_stream', lambda: None),
            state="disabled",
            width=12,
        )
        data_btn.pack(side="left", padx=1)
        self.widgets['data_btn'] = data_btn
        
        # NormalData 按钮
        data_btn2 = ttk.Button(
            stream_row,
            text="Start NormalData",
            command=self.callbacks.get('toggle_data_stream2', lambda: None),
            state="disabled",
            width=12,
        )
        data_btn2.pack(side="left", padx=2)
        self.widgets['data_btn2'] = data_btn2
        
        # 频率显示
        freq_frame = ttk.Frame(stream_row)
        freq_frame.pack(side="left", padx=5)
        
        ttk.Label(freq_frame, text="Rate:", font=("Arial", 9)).pack(side="left", padx=1)
        
        freq_var = StringVar(value="0 Hz")
        self.vars['freq'] = freq_var
        freq_label = ttk.Label(
            freq_frame,
            textvariable=freq_var,
            foreground="green",
            font=("Arial", 9, "bold"),
        )
        freq_label.pack(side="left", padx=3)
        self.widgets['freq_label'] = freq_label
    
    def _setup_calibration_section(self):
        """设置校准控制区域"""
        calib_frame = ttk.LabelFrame(
            self.parent, text="Calibration", style="Compact.TLabelframe"
        )
        calib_frame.pack(fill="x", pady=(0, 5))
        
        calib_content = ttk.Frame(calib_frame)
        calib_content.pack(fill="x", padx=3, pady=2)
        
        # 按钮行
        btn_row = ttk.Frame(calib_content)
        btn_row.pack(fill="x", pady=1)
        
        calibrate_btn = ttk.Button(
            btn_row,
            text="Start Calib",
            command=self.callbacks.get('start_calibration', lambda: None),
            state="disabled",
            width=12,
        )
        calibrate_btn.pack(side="left", padx=2)
        self.widgets['calibrate_btn'] = calibrate_btn
        
        capture_btn = ttk.Button(
            btn_row,
            text="Capture Pos",
            command=self.callbacks.get('capture_position', lambda: None),
            state="disabled",
            width=12,
        )
        capture_btn.pack(side="left", padx=2)
        self.widgets['capture_btn'] = capture_btn
        
        # 位置显示
        position_var = StringVar(value="Position: Not calibrating")
        self.vars['position'] = position_var
        position_label = ttk.Label(
            calib_content,
            textvariable=position_var,
            font=("Arial", 9),
        )
        position_label.pack(fill="x", padx=2, pady=1)
        self.widgets['position_label'] = position_label
        
        # 校准状态显示
        calib_status_frame = ttk.Frame(calib_content)
        calib_status_frame.pack(fill="x", padx=2, pady=1)
        
        ttk.Label(calib_status_frame, text="Status:", font=("Arial", 9)).pack(side="left", padx=2)
        
        calibration_status_var = StringVar(value="Unknown")
        self.vars['calibration_status'] = calibration_status_var
        calibration_status_label = ttk.Label(
            calib_status_frame,
            textvariable=calibration_status_var,
            font=("Arial", 9, "bold"),
            foreground="gray"
        )
        calibration_status_label.pack(side="left", padx=2)
        self.widgets['calibration_status_label'] = calibration_status_label
        
        # 检查校准状态按钮
        check_calib_btn = ttk.Button(
            calib_status_frame,
            text="Check",
            command=self.callbacks.get('check_calibration_status', lambda: None),
            width=8,
        )
        check_calib_btn.pack(side="right", padx=2)
        self.widgets['check_calib_btn'] = check_calib_btn
        
        # 6位置校准顺序指引
        guide_frame = ttk.LabelFrame(calib_content, text="6-Position Order", padding=2)
        guide_frame.pack(fill="x", padx=2, pady=(5, 0))
        
        positions = [
            "1. +X ↓ (X轴朝上)",
            "2. -X ↓ (X轴朝下)", 
            "3. +Y ↓ (Y轴朝上)",
            "4. -Y ↓ (Y轴朝下)",
            "5. +Z ↓ (Z轴朝上)",
            "6. -Z ↓ (Z轴朝下)"
        ]
        
        for pos_text in positions:
            lbl = ttk.Label(guide_frame, text=pos_text, font=("Courier", 8))
            lbl.pack(anchor="w", padx=5)
    
    def _setup_statistics_section(self):
        """设置实时统计信息区域"""
        stats_frame = ttk.LabelFrame(
            self.parent, text="Statistics", style="Compact.TLabelframe"
        )
        stats_frame.pack(fill="x", pady=(0, 5))
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill="x", padx=3, pady=2)
        
        # MPU Accel
        mpu_accel_frame = ttk.LabelFrame(stats_grid, text="MPU Accel", padding=2)
        mpu_accel_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self._setup_compact_stats(mpu_accel_frame, "mpu_accel")
        
        # ADXL Accel
        adxl_accel_frame = ttk.LabelFrame(stats_grid, text="ADXL Accel", padding=2)
        adxl_accel_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        self._setup_compact_stats(adxl_accel_frame, "adxl_accel")
        
        # MPU Gyro
        mpu_gyro_frame = ttk.LabelFrame(stats_grid, text="MPU Gyro", padding=2)
        mpu_gyro_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self._setup_compact_stats(mpu_gyro_frame, "mpu_gyro")
        
        # Gravity
        gravity_frame = ttk.LabelFrame(stats_grid, text="Gravity", padding=2)
        gravity_frame.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
        self._setup_gravity_stats(gravity_frame)
        
        # 配置网格权重
        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)
    
    def _setup_compact_stats(self, parent: tk.Widget, sensor_key: str):
        """设置紧凑统计显示"""
        axis_names = ["x", "y", "z"]
        
        for i, axis in enumerate(axis_names):
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=1)
            
            ttk.Label(row, text=f"{axis.upper()}:", font=("Arial", 8, "bold"), width=3).pack(side="left")
            
            # Mean
            mean_var = StringVar(value="μ: 0.000")
            self.vars[f"{sensor_key}_{axis}_mean"] = mean_var
            ttk.Label(row, textvariable=mean_var, font=("Courier", 8), width=10).pack(side="left", padx=2)
            
            # Std
            std_var = StringVar(value="σ: 0.000")
            self.vars[f"{sensor_key}_{axis}_std"] = std_var
            ttk.Label(row, textvariable=std_var, font=("Courier", 8), width=10).pack(side="left", padx=2)
    
    def _setup_gravity_stats(self, parent: tk.Widget):
        """设置重力统计"""
        ttk.Label(parent, text="Gravity Magnitude:", font=("Arial", 8, "bold")).pack(anchor="w", padx=2, pady=1)
        
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill="x", padx=5, pady=1)
        
        mean_var = StringVar(value="Mean: 0.000")
        self.vars['gravity_mean'] = mean_var
        ttk.Label(stats_frame, textvariable=mean_var, font=("Courier", 8)).pack(anchor="w")
        
        std_var = StringVar(value="Std: 0.000")
        self.vars['gravity_std'] = std_var
        ttk.Label(stats_frame, textvariable=std_var, font=("Courier", 8)).pack(anchor="w")
    
    def _setup_commands_section(self):
        """设置命令控制区域"""
        cmd_frame = ttk.LabelFrame(self.parent, text="Commands", style="Compact.TLabelframe")
        cmd_frame.pack(fill="x", pady=(0, 5))
        
        cmd_content = ttk.Frame(cmd_frame)
        cmd_content.pack(fill="x", padx=3, pady=2)
        
        # 第一行
        row1 = ttk.Frame(cmd_content)
        row1.pack(fill="x", pady=1)
        
        send_btn = ttk.Button(
            row1,
            text="Send Commands",
            command=self.callbacks.get('send_all_commands', lambda: None),
            state="disabled",
            width=15,
        )
        send_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['send_btn'] = send_btn
        
        save_btn = ttk.Button(
            row1,
            text="Save Params",
            command=self.callbacks.get('save_calibration_parameters', lambda: None),
            state="disabled",
            width=15,
        )
        save_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['save_btn'] = save_btn
        
        # 第二行
        row2 = ttk.Frame(cmd_content)
        row2.pack(fill="x", pady=1)
        
        read_btn = ttk.Button(
            row2,
            text="Read User Info",
            command=self.callbacks.get('read_sensor_properties', lambda: None),
            state="disabled",
            width=15,
        )
        read_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['read_props_btn'] = read_btn
        
        resend_btn = ttk.Button(
            row2,
            text="Resend",
            command=self.callbacks.get('resend_all_commands', lambda: None),
            state="disabled",
            width=15,
        )
        resend_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['resend_btn'] = resend_btn
        
        # 第三行 - 设备信息读取
        row3 = ttk.Frame(cmd_content)
        row3.pack(fill="x", pady=1)
        
        read_device_btn = ttk.Button(
            row3,
            text="Read Calibration Params",
            command=self.callbacks.get('read_calibration_params', lambda: None),
            state="disabled",
            width=32,  # 加宽以适应单行
        )
        read_device_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['read_device_btn'] = read_device_btn
        
        # 第四行 - 刷新页面按钮
        row4 = ttk.Frame(cmd_content)
        row4.pack(fill="x", pady=1)
        
        reset_ui_btn = ttk.Button(
            row4,
            text="Reset UI",
            command=self.callbacks.get('reset_ui_with_confirmation', lambda: None),
            width=32,
        )
        reset_ui_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['reset_ui_btn'] = reset_ui_btn
    
    def _setup_coordinate_section(self):
        """设置坐标模式控制区域"""
        coord_frame = ttk.LabelFrame(self.parent, text="Coordinate Mode", style="Compact.TLabelframe")
        coord_frame.pack(fill="x", pady=(0, 5))
        
        coord_content = ttk.Frame(coord_frame)
        coord_content.pack(fill="x", padx=3, pady=2)
        
        coord_row = ttk.Frame(coord_content)
        coord_row.pack(fill="x", pady=1)
        
        local_coord_btn = ttk.Button(
            coord_row,
            text="Local Coord",
            command=self.callbacks.get('set_local_coordinate_mode', lambda: None),
            state="disabled",
            width=18,
        )
        local_coord_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['local_coord_btn'] = local_coord_btn
        
        global_coord_btn = ttk.Button(
            coord_row,
            text="Global Coord",
            command=self.callbacks.get('set_global_coordinate_mode', lambda: None),
            state="disabled",
            width=18,
        )
        global_coord_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['global_coord_btn'] = global_coord_btn
    
    def _setup_activation_section(self):
        """设置激活区域"""
        act_frame = ttk.LabelFrame(
            self.parent, text="Activation", style="Compact.TLabelframe"
        )
        act_frame.pack(fill="x", pady=(0, 5))
        
        act_content = ttk.Frame(act_frame)
        act_content.pack(fill="x", padx=3, pady=2)
        
        # 按钮行
        act_btn_row = ttk.Frame(act_content)
        act_btn_row.pack(fill="x", pady=1)
        
        activate_btn = ttk.Button(
            act_btn_row,
            text="Activate",
            command=self.callbacks.get('activate_sensor', lambda: None),
            state="disabled",
            width=10,
        )
        activate_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['activate_btn'] = activate_btn
        
        verify_btn = ttk.Button(
            act_btn_row,
            text="Verify",
            command=self.callbacks.get('verify_activation', lambda: None),
            state="disabled",
            width=10,
        )
        verify_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['verify_btn'] = verify_btn
        
        # === 激活信息显示区域 ===
        info_frame = ttk.Frame(act_content)
        info_frame.pack(fill="x", pady=(5, 0))
        
        # MAC 地址显示
        mac_frame = ttk.Frame(info_frame)
        mac_frame.pack(fill="x", pady=1)
        
        ttk.Label(mac_frame, text="MAC:", font=("Arial", 8)).pack(side="left", padx=2)
        
        mac_var = StringVar(value="--")
        self.vars['activation_mac'] = mac_var
        mac_label = ttk.Label(
            mac_frame, 
            textvariable=mac_var, 
            font=("Courier", 8),
            foreground="gray"
        )
        mac_label.pack(side="left", padx=2)
        
        # 密钥片段显示（7字符）+ Copy 按钮
        key_frame = ttk.Frame(info_frame)
        key_frame.pack(fill="x", pady=1)
        
        ttk.Label(key_frame, text="Key:", font=("Arial", 8)).pack(side="left", padx=2)
        
        key_var = StringVar()
        self.vars['activation_key'] = key_var
        key_entry = ttk.Entry(
            key_frame,
            textvariable=key_var,
            font=("Courier", 8),
            state="readonly",
            width=10
        )
        key_entry.pack(side="left", padx=2)
        self.widgets['activation_key_entry'] = key_entry
        
        # 复制密钥按钮
        copy_key_btn = ttk.Button(
            key_frame,
            text="Copy",
            command=self.callbacks.get('copy_activation_key', lambda: None),
            state="disabled",
            width=6
        )
        copy_key_btn.pack(side="left", padx=2)
        self.widgets['copy_key_btn'] = copy_key_btn
        
        # 激活状态显示
        status_frame = ttk.Frame(info_frame)
        status_frame.pack(fill="x", pady=1)
        
        ttk.Label(status_frame, text="Status:", font=("Arial", 8)).pack(side="left", padx=2)
        
        status_var = StringVar(value="Not Activated")
        self.vars['activation_status'] = status_var
        status_label = ttk.Label(
            status_frame,
            textvariable=status_var,
            font=("Arial", 8, "bold"),
            foreground="red"
        )
        status_label.pack(side="left", padx=2)
        self.widgets['activation_status_label'] = status_label
    
    def _setup_network_section(self):
        """设置网络配置区域框架（具体由子方法填充）"""
        pass  # 由 _setup_network_notebook 处理
    
    def _setup_network_notebook(self):
        """
        设置主配置 Notebook - 重构为5个主标签页
        
        5个主标签页：
        - Dashboard: 仪表盘，系统状态总览
        - Network: 网络配置（二级标签：WiFi/MQTT/Cloud/Position）
        - Sensors: 传感器配置（二级标签：Filter/Alarm/Auxiliary）
        - System: 系统控制（二级标签：Control/Camera/OTA/Debug）
        - Calibration: 六位置校准
        """
        t = LightTheme
        
        # 创建主 Notebook 容器
        notebook_frame = tk.Frame(self.parent, bg=t.BG_MAIN)
        notebook_frame.pack(fill="x", pady=(10, 5))
        
        # 创建主 Notebook（5个标签）
        notebook = ttk.Notebook(notebook_frame, style='Custom.TNotebook')
        notebook.pack(fill="x", padx=10, pady=5)
        
        # === Tab 1: Dashboard ===
        dashboard_tab = tk.Frame(notebook, bg=t.BG_MAIN)
        notebook.add(dashboard_tab, text=" Dashboard ")
        self._setup_dashboard_tab(dashboard_tab)
        
        # === Tab 2: Network ===
        network_tab = tk.Frame(notebook, bg=t.BG_MAIN)
        notebook.add(network_tab, text=" Network ")
        self._setup_network_tab(network_tab)
        
        # === Tab 3: Sensors ===
        sensors_tab = tk.Frame(notebook, bg=t.BG_MAIN)
        notebook.add(sensors_tab, text=" Sensors ")
        self._setup_sensors_tab(sensors_tab)
        
        # === Tab 4: System ===
        system_tab = tk.Frame(notebook, bg=t.BG_MAIN)
        notebook.add(system_tab, text=" System ")
        self._setup_system_main_tab(system_tab)
        
        # === Tab 5: Calibration ===
        calibration_tab = tk.Frame(notebook, bg=t.BG_MAIN)
        notebook.add(calibration_tab, text=" Calibration ")
        self._setup_calibration_main_tab(calibration_tab)
    
    def _setup_wifi_tab(self, parent):
        """设置 WiFi 标签页内容"""
        # SSID
        ssid_frame = ttk.Frame(parent)
        ssid_frame.pack(fill="x", pady=2)
        
        ttk.Label(ssid_frame, text="SSID:", font=("Arial", 9)).pack(side="left", padx=2)
        
        ssid_var = StringVar()
        self.vars['ssid'] = ssid_var
        ssid_entry = ttk.Entry(ssid_frame, textvariable=ssid_var, font=("Arial", 9), width=20)
        ssid_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # 密码
        password_frame = ttk.Frame(parent)
        password_frame.pack(fill="x", pady=2)
        
        ttk.Label(password_frame, text="Password:", font=("Arial", 9)).pack(side="left", padx=2)
        
        password_var = StringVar()
        self.vars['password'] = password_var
        password_entry = ttk.Entry(
            password_frame,
            textvariable=password_var,
            show="*",
            font=("Arial", 9),
            width=20,
        )
        password_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # 按钮
        wifi_btn_frame = ttk.Frame(parent)
        wifi_btn_frame.pack(fill="x", pady=5)
        
        set_wifi_btn = ttk.Button(
            wifi_btn_frame,
            text="Set WiFi",
            command=self.callbacks.get('set_wifi_config', lambda: None),
            state="disabled",
            width=12,
        )
        set_wifi_btn.pack(side="left", padx=2)
        self.widgets['set_wifi_btn'] = set_wifi_btn
        
        read_wifi_btn = ttk.Button(
            wifi_btn_frame,
            text="Read WiFi",
            command=self.callbacks.get('read_wifi_config', lambda: None),
            state="disabled",
            width=12,
        )
        read_wifi_btn.pack(side="left", padx=2)
        self.widgets['read_wifi_btn'] = read_wifi_btn
    
    def _setup_mqtt_tab(self, parent):
        """设置 MQTT 标签页内容"""
        # Broker
        broker_frame = ttk.Frame(parent)
        broker_frame.pack(fill="x", pady=2)
        
        ttk.Label(broker_frame, text="Broker:", font=("Arial", 9)).pack(side="left", padx=2)
        
        broker_var = StringVar()
        self.vars['mqtt_broker'] = broker_var
        broker_entry = ttk.Entry(broker_frame, textvariable=broker_var, font=("Arial", 9), width=20)
        broker_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # Username
        user_frame = ttk.Frame(parent)
        user_frame.pack(fill="x", pady=2)
        
        ttk.Label(user_frame, text="Username:", font=("Arial", 9)).pack(side="left", padx=2)
        
        user_var = StringVar()
        self.vars['mqtt_user'] = user_var
        user_entry = ttk.Entry(user_frame, textvariable=user_var, font=("Arial", 9), width=20)
        user_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # Password
        pwd_frame = ttk.Frame(parent)
        pwd_frame.pack(fill="x", pady=2)
        
        ttk.Label(pwd_frame, text="Password:", font=("Arial", 9)).pack(side="left", padx=2)
        
        pwd_var = StringVar()
        self.vars['mqtt_password'] = pwd_var
        pwd_entry = ttk.Entry(pwd_frame, textvariable=pwd_var, show="*", font=("Arial", 9), width=20)
        pwd_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # Port
        port_frame = ttk.Frame(parent)
        port_frame.pack(fill="x", pady=2)
        
        ttk.Label(port_frame, text="Port:", font=("Arial", 9)).pack(side="left", padx=2)
        
        port_var = StringVar(value="1883")
        self.vars['mqtt_port'] = port_var
        port_entry = ttk.Entry(port_frame, textvariable=port_var, font=("Arial", 9), width=10)
        port_entry.pack(side="left", padx=2)
        
        # 按钮
        mqtt_btn_frame = ttk.Frame(parent)
        mqtt_btn_frame.pack(fill="x", pady=5)
        
        set_mqtt_btn = ttk.Button(
            mqtt_btn_frame,
            text="Set MQTT",
            command=self.callbacks.get('set_mqtt_config', lambda: None),
            state="disabled",
            width=12,
        )
        set_mqtt_btn.pack(side="left", padx=2)
        self.widgets['set_mqtt_btn'] = set_mqtt_btn
        
        read_mqtt_btn = ttk.Button(
            mqtt_btn_frame,
            text="Read MQTT",
            command=self.callbacks.get('read_mqtt_config', lambda: None),
            state="disabled",
            width=12,
        )
        read_mqtt_btn.pack(side="left", padx=2)
        self.widgets['read_mqtt_btn'] = read_mqtt_btn
    
    def _setup_ota_tab(self, parent):
        """设置 OTA 标签页内容"""
        # URL1
        url1_frame = ttk.Frame(parent)
        url1_frame.pack(fill="x", pady=2)
        
        ttk.Label(url1_frame, text="URL1:", font=("Arial", 9)).pack(side="left", padx=2)
        
        url1_var = StringVar()
        self.vars['url1'] = url1_var
        url1_entry = ttk.Entry(url1_frame, textvariable=url1_var, font=("Arial", 9), width=20)
        url1_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # URL2
        url2_frame = ttk.Frame(parent)
        url2_frame.pack(fill="x", pady=2)
        
        ttk.Label(url2_frame, text="URL2:", font=("Arial", 9)).pack(side="left", padx=2)
        
        url2_var = StringVar()
        self.vars['url2'] = url2_var
        url2_entry = ttk.Entry(url2_frame, textvariable=url2_var, font=("Arial", 9), width=20)
        url2_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # URL3
        url3_frame = ttk.Frame(parent)
        url3_frame.pack(fill="x", pady=2)
        
        ttk.Label(url3_frame, text="URL3:", font=("Arial", 9)).pack(side="left", padx=2)
        
        url3_var = StringVar()
        self.vars['url3'] = url3_var
        url3_entry = ttk.Entry(url3_frame, textvariable=url3_var, font=("Arial", 9), width=20)
        url3_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # URL4
        url4_frame = ttk.Frame(parent)
        url4_frame.pack(fill="x", pady=2)
        
        ttk.Label(url4_frame, text="URL4:", font=("Arial", 9)).pack(side="left", padx=2)
        
        url4_var = StringVar()
        self.vars['url4'] = url4_var
        url4_entry = ttk.Entry(url4_frame, textvariable=url4_var, font=("Arial", 9), width=20)
        url4_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # 按钮
        ota_btn_frame = ttk.Frame(parent)
        ota_btn_frame.pack(fill="x", pady=5)
        
        set_ota_btn = ttk.Button(
            ota_btn_frame,
            text="Set OTA",
            command=self.callbacks.get('set_ota_config', lambda: None),
            state="disabled",
            width=12,
        )
        set_ota_btn.pack(side="left", padx=2)
        self.widgets['set_ota_btn'] = set_ota_btn
        
        read_ota_btn = ttk.Button(
            ota_btn_frame,
            text="Read OTA",
            command=self.callbacks.get('read_ota_config', lambda: None),
            state="disabled",
            width=12,
        )
        read_ota_btn.pack(side="left", padx=2)
        self.widgets['read_ota_btn'] = read_ota_btn
    
    def _setup_alarm_device_tab(self, parent):
        """
        设置 Alarm & Device 标签页内容
        
        包含：
        - 报警阈值设置
        - 设备控制按钮（Save Config, Restart Sensor）
        - 当前阈值显示
        """
        # === Alarm Threshold Section ===
        alarm_frame = ttk.LabelFrame(parent, text="Alarm Threshold", padding=5)
        alarm_frame.pack(fill="x", pady=(0, 5))
        
        # 加速度阈值
        accel_frame = ttk.Frame(alarm_frame)
        accel_frame.pack(fill="x", pady=2)
        
        ttk.Label(accel_frame, text="Accel (m/s²):", font=("Arial", 9)).pack(side="left", padx=2)
        
        accel_var = StringVar(value="0.2")
        self.vars['alarm_accel_threshold'] = accel_var
        accel_entry = ttk.Entry(accel_frame, textvariable=accel_var, font=("Arial", 9), width=10)
        accel_entry.pack(side="left", padx=2)
        
        # 倾角阈值
        gyro_frame = ttk.Frame(alarm_frame)
        gyro_frame.pack(fill="x", pady=2)
        
        ttk.Label(gyro_frame, text="Gyro (°):", font=("Arial", 9)).pack(side="left", padx=2)
        
        gyro_var = StringVar(value="0.2")
        self.vars['alarm_gyro_threshold'] = gyro_var
        gyro_entry = ttk.Entry(gyro_frame, textvariable=gyro_var, font=("Arial", 9), width=10)
        gyro_entry.pack(side="left", padx=2)
        
        # Set Alarm Threshold 按钮
        set_alarm_btn = ttk.Button(
            alarm_frame,
            text="Set Alarm Threshold",
            command=self.callbacks.get('set_alarm_threshold', lambda: None),
            state="disabled",
            width=20,
        )
        set_alarm_btn.pack(fill="x", pady=5)
        self.widgets['set_alarm_threshold_btn'] = set_alarm_btn
        
        # === Device Control Section ===
        device_frame = ttk.LabelFrame(parent, text="Device Control", padding=5)
        device_frame.pack(fill="x", pady=(0, 5))
        
        device_btn_frame = ttk.Frame(device_frame)
        device_btn_frame.pack(fill="x", pady=2)
        
        # Save Config 按钮 (SS:7)
        save_config_btn = ttk.Button(
            device_btn_frame,
            text="Save Config",
            command=self.callbacks.get('save_config', lambda: None),
            state="disabled",
            width=15,
        )
        save_config_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['save_config_btn'] = save_config_btn
        
        # Restart Sensor 按钮 (SS:9)
        restart_btn = ttk.Button(
            device_btn_frame,
            text="Restart Sensor",
            command=self.callbacks.get('restart_sensor', lambda: None),
            state="disabled",
            width=15,
        )
        restart_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['restart_sensor_btn'] = restart_btn
        
        # === Current Status Section ===
        status_frame = ttk.LabelFrame(parent, text="Current Thresholds", padding=5)
        status_frame.pack(fill="x", pady=(0, 5))
        
        # 当前加速度阈值显示
        accel_status_var = StringVar(value="Accel: -- m/s²")
        self.vars['current_accel_threshold'] = accel_status_var
        accel_status_label = ttk.Label(
            status_frame,
            textvariable=accel_status_var,
            font=("Arial", 9),
        )
        accel_status_label.pack(anchor="w", padx=2, pady=1)
        
        # 当前倾角阈值显示
        gyro_status_var = StringVar(value="Gyro: -- °")
        self.vars['current_gyro_threshold'] = gyro_status_var
        gyro_status_label = ttk.Label(
            status_frame,
            textvariable=gyro_status_var,
            font=("Arial", 9),
        )
        gyro_status_label.pack(anchor="w", padx=2, pady=1)
    
    # ============== 公共方法 ==============
    
    def get_widget(self, name: str) -> Optional[Any]:
        """获取控件引用"""
        return self.widgets.get(name)
    
    def get_var(self, name: str) -> Optional[StringVar]:
        """获取变量引用"""
        return self.vars.get(name)
    
    def set_widget_state(self, name: str, state: str):
        """设置控件状态 (normal/disabled)"""
        widget = self.widgets.get(name)
        if widget and hasattr(widget, 'config'):
            widget.config(state=state)
    
    def update_status(self, text: str, color: str = "blue"):
        """更新状态文本和颜色"""
        status_var = self.vars.get('status')
        if status_var:
            status_var.set(text)
        status_label = self.widgets.get('status_label')
        if status_label:
            status_label.config(foreground=color)
    
    def update_frequency(self, freq: int):
        """更新频率显示"""
        freq_var = self.vars.get('freq')
        if freq_var:
            freq_var.set(f"{freq} Hz")
    
    def update_position(self, text: str):
        """更新位置显示"""
        position_var = self.vars.get('position')
        if position_var:
            position_var.set(text)
    
    def set_button_text(self, name: str, text: str):
        """设置按钮文本"""
        widget = self.widgets.get(name)
        if widget:
            widget.config(text=text)
    
    def get_entry_value(self, name: str) -> str:
        """获取输入框值"""
        var = self.vars.get(name)
        return var.get() if var else ""
    
    def set_entry_value(self, name: str, value: str):
        """设置输入框值"""
        var = self.vars.get(name)
        if var:
            var.set(value)
    
    def update_statistics_label(self, name: str, text: str):
        """更新统计标签文本"""
        var = self.vars.get(name)
        if var:
            var.set(text)
    
    # ============================================================================
    # Sprint 1: 新增标签页设置方法
    # ============================================================================
    
    def _setup_cloud_tab(self, parent):
        """
        设置 Cloud 标签页内容 - 阿里云MQTT配置
        
        Sprint 1 新增：支持 SET:KNS 和 SET:CMQ 命令
        """
        # === 阿里云三元组配置 ===
        aliyun_frame = ttk.LabelFrame(parent, text="Aliyun IoT Configuration", padding=5)
        aliyun_frame.pack(fill="x", pady=(0, 5))
        
        # ProductKey
        pk_frame = ttk.Frame(aliyun_frame)
        pk_frame.pack(fill="x", pady=2)
        
        ttk.Label(pk_frame, text="ProductKey:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        pk_var = StringVar()
        self.vars['aliyun_product_key'] = pk_var
        pk_entry = ttk.Entry(pk_frame, textvariable=pk_var, font=("Courier", 9), width=25)
        pk_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # DeviceName
        dn_frame = ttk.Frame(aliyun_frame)
        dn_frame.pack(fill="x", pady=2)
        
        ttk.Label(dn_frame, text="DeviceName:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        dn_var = StringVar()
        self.vars['aliyun_device_name'] = dn_var
        dn_entry = ttk.Entry(dn_frame, textvariable=dn_var, font=("Courier", 9), width=25)
        dn_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # DeviceSecret
        ds_frame = ttk.Frame(aliyun_frame)
        ds_frame.pack(fill="x", pady=2)
        
        ttk.Label(ds_frame, text="DeviceSecret:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        ds_var = StringVar()
        self.vars['aliyun_device_secret'] = ds_var
        ds_entry = ttk.Entry(ds_frame, textvariable=ds_var, font=("Courier", 9), width=25, show="*")
        ds_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # 设置阿里云配置按钮
        set_aliyun_btn = ttk.Button(
            aliyun_frame,
            text="Set Aliyun MQTT",
            command=self.callbacks.get('set_aliyun_mqtt_config', lambda: None),
            state="disabled",
            width=20,
        )
        set_aliyun_btn.pack(fill="x", pady=5)
        self.widgets['set_aliyun_mqtt_btn'] = set_aliyun_btn
        
        # === MQTT 模式切换 ===
        mode_frame = ttk.LabelFrame(parent, text="MQTT Mode Switch", padding=5)
        mode_frame.pack(fill="x", pady=(0, 5))
        
        mode_btn_frame = ttk.Frame(mode_frame)
        mode_btn_frame.pack(fill="x", pady=2)
        
        # 局域网模式
        local_mode_btn = ttk.Button(
            mode_btn_frame,
            text="Local Mode (1)",
            command=self.callbacks.get('set_mqtt_local_mode', lambda: None),
            state="disabled",
            width=15,
        )
        local_mode_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['mqtt_local_mode_btn'] = local_mode_btn
        
        # 阿里云模式
        aliyun_mode_btn = ttk.Button(
            mode_btn_frame,
            text="Aliyun Mode (10)",
            command=self.callbacks.get('set_mqtt_aliyun_mode', lambda: None),
            state="disabled",
            width=15,
        )
        aliyun_mode_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['mqtt_aliyun_mode_btn'] = aliyun_mode_btn
    
    def _setup_position_tab(self, parent):
        """
        设置 Position 标签页内容 - 位置配置和安装模式
        
        Sprint 1 新增：支持 SET:PO 和 SET:ISG 命令
        """
        # === 行政区划和属性配置 ===
        position_frame = ttk.LabelFrame(parent, text="Position Configuration", padding=5)
        position_frame.pack(fill="x", pady=(0, 5))
        
        # 行政区划路径
        region_frame = ttk.Frame(position_frame)
        region_frame.pack(fill="x", pady=2)
        
        ttk.Label(region_frame, text="Region:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        region_var = StringVar(value="/Province/City/District/Street")
        self.vars['position_region'] = region_var
        region_entry = ttk.Entry(region_frame, textvariable=region_var, font=("Courier", 9), width=25)
        region_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # 建筑类型
        building_frame = ttk.Frame(position_frame)
        building_frame.pack(fill="x", pady=2)
        
        ttk.Label(building_frame, text="Building:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        building_var = StringVar(value="Zhuzhai")
        self.vars['position_building'] = building_var
        building_combo = ttk.Combobox(
            building_frame,
            textvariable=building_var,
            values=["Zhuzhai", "Shangye", "Gongye", "Bangong", "Qita"],
            font=("Arial", 9),
            width=15,
            state="readonly"
        )
        building_combo.pack(side="left", padx=2, fill="x", expand=True)
        
        # 用户属性
        user_attr_frame = ttk.Frame(position_frame)
        user_attr_frame.pack(fill="x", pady=2)
        
        ttk.Label(user_attr_frame, text="User Attr:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        user_attr_var = StringVar()
        self.vars['position_user_attr'] = user_attr_var
        user_attr_entry = ttk.Entry(user_attr_frame, textvariable=user_attr_var, font=("Courier", 9), width=25)
        user_attr_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # 设备名称
        device_name_frame = ttk.Frame(position_frame)
        device_name_frame.pack(fill="x", pady=2)
        
        ttk.Label(device_name_frame, text="Device Name:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        device_name_var = StringVar()
        self.vars['position_device_name'] = device_name_var
        device_name_entry = ttk.Entry(device_name_frame, textvariable=device_name_var, font=("Courier", 9), width=25)
        device_name_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # 设置位置配置按钮
        set_position_btn = ttk.Button(
            position_frame,
            text="Set Position Config",
            command=self.callbacks.get('set_position_config', lambda: None),
            state="disabled",
            width=20,
        )
        set_position_btn.pack(fill="x", pady=5)
        self.widgets['set_position_btn'] = set_position_btn
        
        # === 安装模式配置 ===
        install_frame = ttk.LabelFrame(parent, text="Install Mode", padding=5)
        install_frame.pack(fill="x", pady=(0, 5))
        
        install_row = ttk.Frame(install_frame)
        install_row.pack(fill="x", pady=2)
        
        ttk.Label(install_row, text="Mode:", font=("Arial", 9), width=8).pack(side="left", padx=2)
        
        install_var = StringVar(value="0")
        self.vars['install_mode'] = install_var
        install_combo = ttk.Combobox(
            install_row,
            textvariable=install_var,
            values=[
                "0 - Default",
                "1 - Ground 1", "2 - Ground 2",
                "3 - Side 1", "4 - Side 2", "5 - Side 3", "6 - Side 4",
                "7 - Top 1", "8 - Top 2", "9 - Top 3", "10 - Top 4", "11 - Top 5", "12 - Top 6"
            ],
            font=("Courier", 9),
            width=20,
            state="readonly"
        )
        install_combo.pack(side="left", padx=2, fill="x", expand=True)
        
        set_install_btn = ttk.Button(
            install_row,
            text="Set",
            command=self.callbacks.get('set_install_mode', lambda: None),
            state="disabled",
            width=6,
        )
        set_install_btn.pack(side="left", padx=2)
        self.widgets['set_install_mode_btn'] = set_install_btn
        
        # 安装模式说明
        mode_hint = ttk.Label(
            install_frame,
            text="0=Default, 1-2=Ground, 3-6=Side, 7-12=Top",
            font=("Arial", 8),
            foreground="gray"
        )
        mode_hint.pack(anchor="w", padx=2, pady=(2, 0))
    
    def _setup_system_tab(self, parent):
        """
        设置 System 标签页内容 - 系统控制和配置管理
        
        Sprint 1 新增：支持 SS:11, SS:12, SS:27 等命令
        """
        # === 配置管理 ===
        config_frame = ttk.LabelFrame(parent, text="Configuration Management", padding=5)
        config_frame.pack(fill="x", pady=(0, 5))
        
        config_btn_frame = ttk.Frame(config_frame)
        config_btn_frame.pack(fill="x", pady=2)
        
        # 保存传感器配置 (SS:12)
        save_sensor_btn = ttk.Button(
            config_btn_frame,
            text="Save Sensor Config",
            command=self.callbacks.get('save_sensor_config', lambda: None),
            state="disabled",
            width=18,
        )
        save_sensor_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['save_sensor_config_btn'] = save_sensor_btn
        
        # 恢复默认配置 (SS:11) - 危险操作，红色样式
        restore_default_btn = ttk.Button(
            config_btn_frame,
            text="Restore Default",
            command=self.callbacks.get('restore_default_config', lambda: None),
            state="disabled",
            width=18,
        )
        restore_default_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['restore_default_btn'] = restore_default_btn
        
        # === 系统控制 ===
        control_frame = ttk.LabelFrame(parent, text="System Control", padding=5)
        control_frame.pack(fill="x", pady=(0, 5))
        
        control_btn_frame = ttk.Frame(control_frame)
        control_btn_frame.pack(fill="x", pady=2)
        
        # 重启传感器 (SS:9)
        restart_sensor_btn = ttk.Button(
            control_btn_frame,
            text="Restart Sensor",
            command=self.callbacks.get('restart_sensor', lambda: None),
            state="disabled",
            width=18,
        )
        restart_sensor_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['restart_sensor_system_btn'] = restart_sensor_btn
        
        # 反激活传感器 (SS:27) - 危险操作
        deactivate_btn = ttk.Button(
            control_btn_frame,
            text="Deactivate Sensor",
            command=self.callbacks.get('deactivate_sensor', lambda: None),
            state="disabled",
            width=18,
        )
        deactivate_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['deactivate_sensor_btn'] = deactivate_btn
        
        # === 警告提示 ===
        warning_frame = ttk.Frame(parent)
        warning_frame.pack(fill="x", pady=(5, 0))
        
        warning_text = ttk.Label(
            warning_frame,
            text="⚠️ Warning: Restore Default and Deactivate will reset all settings!",
            font=("Arial", 8),
            foreground="red",
            wraplength=350
        )
        warning_text.pack(anchor="w", padx=2)

    
    # ============================================================================
    # Sprint 2: 新增标签页
    # ============================================================================
    
    def _setup_advanced_tab(self, parent):
        """
        设置 Advanced 标签页内容 - 卡尔曼滤波配置
        
        Sprint 2 新增：支持 SET:KFQR 和 SS:17 命令
        """
        # === 卡尔曼滤波系数配置 ===
        filter_frame = ttk.LabelFrame(parent, text="Kalman Filter Configuration", padding=5)
        filter_frame.pack(fill="x", pady=(0, 5))
        
        # 过程噪声 Q
        q_frame = ttk.Frame(filter_frame)
        q_frame.pack(fill="x", pady=2)
        
        ttk.Label(q_frame, text="Process Noise (Q):", font=("Arial", 9), width=18).pack(side="left", padx=2)
        
        q_var = StringVar(value="0.005")
        self.vars['kf_q'] = q_var
        q_entry = ttk.Entry(q_frame, textvariable=q_var, font=("Courier", 9), width=12)
        q_entry.pack(side="left", padx=2)
        
        ttk.Label(q_frame, text="(0.001-1.0)", font=("Arial", 8), foreground="gray").pack(side="left", padx=2)
        
        # 测量噪声 R
        r_frame = ttk.Frame(filter_frame)
        r_frame.pack(fill="x", pady=2)
        
        ttk.Label(r_frame, text="Measurement Noise (R):", font=("Arial", 9), width=18).pack(side="left", padx=2)
        
        r_var = StringVar(value="15")
        self.vars['kf_r'] = r_var
        r_entry = ttk.Entry(r_frame, textvariable=r_var, font=("Courier", 9), width=12)
        r_entry.pack(side="left", padx=2)
        
        ttk.Label(r_frame, text="(1.0-100.0)", font=("Arial", 8), foreground="gray").pack(side="left", padx=2)
        
        # 设置按钮
        set_kf_btn = ttk.Button(
            filter_frame,
            text="Set Filter Coefficients",
            command=self.callbacks.get('set_kalman_filter', lambda: None),
            state="disabled",
            width=25,
        )
        set_kf_btn.pack(fill="x", pady=5)
        self.widgets['set_kalman_filter_btn'] = set_kf_btn
        
        # === 滤波开关 ===
        toggle_frame = ttk.LabelFrame(parent, text="Filter Toggle", padding=5)
        toggle_frame.pack(fill="x", pady=(0, 5))
        
        toggle_btn_frame = ttk.Frame(toggle_frame)
        toggle_btn_frame.pack(fill="x", pady=2)
        
        filter_on_btn = ttk.Button(
            toggle_btn_frame,
            text="Filter ON",
            command=self.callbacks.get('set_filter_on', lambda: None),
            state="disabled",
            width=15,
        )
        filter_on_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['filter_on_btn'] = filter_on_btn
        
        filter_off_btn = ttk.Button(
            toggle_btn_frame,
            text="Filter OFF",
            command=self.callbacks.get('set_filter_off', lambda: None),
            state="disabled",
            width=15,
        )
        filter_off_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['filter_off_btn'] = filter_off_btn
    
    def _setup_alarm_levels_tab(self, parent):
        """
        设置 Alarm Levels 标签页内容 - 多级报警阈值配置
        
        Sprint 2 新增：支持 SET:GROLEVEL 和 SET:ACCLEVEL 命令
        """
        # === 角度报警等级 ===
        gyro_frame = ttk.LabelFrame(parent, text="Gyro Alarm Levels (°)", padding=5)
        gyro_frame.pack(fill="x", pady=(0, 5))
        
        self._create_level_inputs(gyro_frame, "gyro", 
                                  [0.40107, 0.573, 1.146, 2.292, 4.584])
        
        set_gyro_btn = ttk.Button(
            gyro_frame,
            text="Set Gyro Levels",
            command=self.callbacks.get('set_gyro_levels', lambda: None),
            state="disabled",
            width=20,
        )
        set_gyro_btn.pack(fill="x", pady=5)
        self.widgets['set_gyro_levels_btn'] = set_gyro_btn
        
        # === 加速度报警等级 ===
        accel_frame = ttk.LabelFrame(parent, text="Accel Alarm Levels (m/s²)", padding=5)
        accel_frame.pack(fill="x", pady=(0, 5))
        
        self._create_level_inputs(accel_frame, "accel",
                                  [0.2, 0.5, 1.0, 2.0, 4.0])
        
        set_accel_btn = ttk.Button(
            accel_frame,
            text="Set Accel Levels",
            command=self.callbacks.get('set_accel_levels', lambda: None),
            state="disabled",
            width=20,
        )
        set_accel_btn.pack(fill="x", pady=5)
        self.widgets['set_accel_levels_btn'] = set_accel_btn
    
    def _create_level_inputs(self, parent, prefix, defaults):
        """创建5级报警输入框"""
        for i in range(1, 6):
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=1)
            
            ttk.Label(row, text=f"Level {i}:", font=("Arial", 9), width=8).pack(side="left", padx=2)
            
            var = StringVar(value=str(defaults[i-1]))
            self.vars[f'{prefix}_level{i}'] = var
            entry = ttk.Entry(row, textvariable=var, font=("Courier", 9), width=10)
            entry.pack(side="left", padx=2)
    
    def _setup_auxiliary_tab(self, parent):
        """
        设置 Auxiliary 标签页内容 - 辅助传感器配置
        
        Sprint 2 新增：支持 SET:VKS, SET:TME, SET:MAGOF 命令
        """
        # === 电压传感器配置 ===
        voltage_frame = ttk.LabelFrame(parent, text="Voltage Sensor (VKS)", padding=5)
        voltage_frame.pack(fill="x", pady=(0, 5))
        
        v1_frame = ttk.Frame(voltage_frame)
        v1_frame.pack(fill="x", pady=2)
        
        ttk.Label(v1_frame, text="Voltage 1 Scale:", font=("Arial", 9), width=14).pack(side="left", padx=2)
        v1_var = StringVar(value="1.0")
        self.vars['vks_v1'] = v1_var
        ttk.Entry(v1_frame, textvariable=v1_var, font=("Courier", 9), width=10).pack(side="left", padx=2)
        
        v2_frame = ttk.Frame(voltage_frame)
        v2_frame.pack(fill="x", pady=2)
        
        ttk.Label(v2_frame, text="Voltage 2 Scale:", font=("Arial", 9), width=14).pack(side="left", padx=2)
        v2_var = StringVar(value="1.0")
        self.vars['vks_v2'] = v2_var
        ttk.Entry(v2_frame, textvariable=v2_var, font=("Courier", 9), width=10).pack(side="left", padx=2)
        
        set_vks_btn = ttk.Button(
            voltage_frame,
            text="Set Voltage Scales",
            command=self.callbacks.get('set_voltage_scales', lambda: None),
            state="disabled",
            width=20,
        )
        set_vks_btn.pack(fill="x", pady=5)
        self.widgets['set_vks_btn'] = set_vks_btn
        
        # === 温度传感器配置 ===
        temp_frame = ttk.LabelFrame(parent, text="Temperature Sensor (TME)", padding=5)
        temp_frame.pack(fill="x", pady=(0, 5))
        
        tme_frame = ttk.Frame(temp_frame)
        tme_frame.pack(fill="x", pady=2)
        
        ttk.Label(tme_frame, text="Offset (°C):", font=("Arial", 9), width=12).pack(side="left", padx=2)
        tme_var = StringVar(value="0.0")
        self.vars['tme_offset'] = tme_var
        ttk.Entry(tme_frame, textvariable=tme_var, font=("Courier", 9), width=10).pack(side="left", padx=2)
        
        set_tme_btn = ttk.Button(
            temp_frame,
            text="Set Temperature Offset",
            command=self.callbacks.get('set_temp_offset', lambda: None),
            state="disabled",
            width=20,
        )
        set_tme_btn.pack(fill="x", pady=5)
        self.widgets['set_tme_btn'] = set_tme_btn
        
        # === 磁力传感器配置 ===
        mag_frame = ttk.LabelFrame(parent, text="Magnetometer (MAGOF)", padding=5)
        mag_frame.pack(fill="x", pady=(0, 5))
        
        for axis in ['X', 'Y', 'Z']:
            row = ttk.Frame(mag_frame)
            row.pack(fill="x", pady=2)
            
            ttk.Label(row, text=f"{axis} Offset:", font=("Arial", 9), width=10).pack(side="left", padx=2)
            
            var = StringVar(value="0.0")
            self.vars[f'magof_{axis.lower()}'] = var
            ttk.Entry(row, textvariable=var, font=("Courier", 9), width=10).pack(side="left", padx=2)
        
        set_magof_btn = ttk.Button(
            mag_frame,
            text="Set Mag Offsets",
            command=self.callbacks.get('set_mag_offsets', lambda: None),
            state="disabled",
            width=20,
        )
        set_magof_btn.pack(fill="x", pady=5)
        self.widgets['set_magof_btn'] = set_magof_btn
    
    def _setup_camera_tab(self, parent):
        """
        设置 Camera 标签页内容 - 相机控制
        
        Sprint 3 新增：支持 SS:19-26 和 CA 命令
        """
        # === 相机模式控制 ===
        mode_frame = ttk.LabelFrame(parent, text="Camera Modes", padding=5)
        mode_frame.pack(fill="x", pady=(0, 5))
        
        # 拍照模式
        photo_row = ttk.Frame(mode_frame)
        photo_row.pack(fill="x", pady=2)
        
        ttk.Label(photo_row, text="Photo Mode:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        photo_on_btn = ttk.Button(
            photo_row,
            text="ON",
            command=self.callbacks.get('set_camera_photo_mode_on', lambda: None),
            state="disabled",
            width=6,
        )
        photo_on_btn.pack(side="left", padx=2)
        self.widgets['camera_photo_on_btn'] = photo_on_btn
        
        photo_off_btn = ttk.Button(
            photo_row,
            text="OFF",
            command=self.callbacks.get('set_camera_photo_mode_off', lambda: None),
            state="disabled",
            width=6,
        )
        photo_off_btn.pack(side="left", padx=2)
        self.widgets['camera_photo_off_btn'] = photo_off_btn
        
        # 监测模式
        monitor_row = ttk.Frame(mode_frame)
        monitor_row.pack(fill="x", pady=2)
        
        ttk.Label(monitor_row, text="Monitor Mode:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        monitor_on_btn = ttk.Button(
            monitor_row,
            text="ON",
            command=self.callbacks.get('set_monitoring_mode_on', lambda: None),
            state="disabled",
            width=6,
        )
        monitor_on_btn.pack(side="left", padx=2)
        self.widgets['monitoring_on_btn'] = monitor_on_btn
        
        monitor_off_btn = ttk.Button(
            monitor_row,
            text="OFF",
            command=self.callbacks.get('set_monitoring_mode_off', lambda: None),
            state="disabled",
            width=6,
        )
        monitor_off_btn.pack(side="left", padx=2)
        self.widgets['monitoring_off_btn'] = monitor_off_btn
        
        # 时程传输模式
        timelapse_row = ttk.Frame(mode_frame)
        timelapse_row.pack(fill="x", pady=2)
        
        ttk.Label(timelapse_row, text="Timelapse:", font=("Arial", 9), width=12).pack(side="left", padx=2)
        
        timelapse_on_btn = ttk.Button(
            timelapse_row,
            text="ON",
            command=self.callbacks.get('set_timelapse_mode_on', lambda: None),
            state="disabled",
            width=6,
        )
        timelapse_on_btn.pack(side="left", padx=2)
        self.widgets['timelapse_on_btn'] = timelapse_on_btn
        
        timelapse_off_btn = ttk.Button(
            timelapse_row,
            text="OFF",
            command=self.callbacks.get('set_timelapse_mode_off', lambda: None),
            state="disabled",
            width=6,
        )
        timelapse_off_btn.pack(side="left", padx=2)
        self.widgets['timelapse_off_btn'] = timelapse_off_btn
        
        # === 相机操作 ===
        action_frame = ttk.LabelFrame(parent, text="Camera Actions", padding=5)
        action_frame.pack(fill="x", pady=(0, 5))
        
        action_btn_frame = ttk.Frame(action_frame)
        action_btn_frame.pack(fill="x", pady=2)
        
        # 拍照按钮
        take_photo_btn = ttk.Button(
            action_btn_frame,
            text="Take Photo",
            command=self.callbacks.get('take_photo', lambda: None),
            state="disabled",
            width=12,
        )
        take_photo_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['take_photo_btn'] = take_photo_btn
        
        # 重启相机下位机
        reboot_slave_btn = ttk.Button(
            action_btn_frame,
            text="Reboot Slave",
            command=self.callbacks.get('reboot_camera_slave', lambda: None),
            state="disabled",
            width=12,
        )
        reboot_slave_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['reboot_camera_slave_btn'] = reboot_slave_btn
        
        # 重启相机模组
        reboot_module_btn = ttk.Button(
            action_btn_frame,
            text="Reboot Module",
            command=self.callbacks.get('reboot_camera_module', lambda: None),
            state="disabled",
            width=12,
        )
        reboot_module_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['reboot_camera_module_btn'] = reboot_module_btn
        
        # === 视频流控制 ===
        stream_frame = ttk.LabelFrame(parent, text="Video Stream", padding=5)
        stream_frame.pack(fill="x", pady=(0, 5))
        
        stream_btn_frame = ttk.Frame(stream_frame)
        stream_btn_frame.pack(fill="x", pady=2)
        
        # 开启/关闭串流
        toggle_stream_btn = ttk.Button(
            stream_btn_frame,
            text="Toggle Stream",
            command=self.callbacks.get('toggle_camera_stream', lambda: None),
            state="disabled",
            width=15,
        )
        toggle_stream_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['toggle_camera_stream_btn'] = toggle_stream_btn
        
        # 开启/关闭推流
        toggle_push_btn = ttk.Button(
            stream_btn_frame,
            text="Toggle Push",
            command=self.callbacks.get('toggle_push_stream', lambda: None),
            state="disabled",
            width=15,
        )
        toggle_push_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['toggle_push_stream_btn'] = toggle_push_btn
        
        # === OTA 升级 ===
        ota_frame = ttk.LabelFrame(parent, text="Camera OTA", padding=5)
        ota_frame.pack(fill="x", pady=(0, 5))
        
        ota_btn_frame = ttk.Frame(ota_frame)
        ota_btn_frame.pack(fill="x", pady=2)
        
        camera_ota_btn = ttk.Button(
            ota_btn_frame,
            text="Camera OTA",
            command=self.callbacks.get('force_camera_ota', lambda: None),
            state="disabled",
            width=15,
        )
        camera_ota_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['force_camera_ota_btn'] = camera_ota_btn
        
        esp32_ota_btn = ttk.Button(
            ota_btn_frame,
            text="ESP32 OTA",
            command=self.callbacks.get('force_esp32_ota', lambda: None),
            state="disabled",
            width=15,
        )
        esp32_ota_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['force_esp32_ota_btn'] = esp32_ota_btn
    
    def _setup_debug_tab(self, parent):
        """
        设置 Debug 标签页内容 - 调试和控制命令
        
        Sprint 2 新增：支持 SS:5, SS:6, SS:14-18 命令
        """
        # === 系统监控 ===
        monitor_frame = ttk.LabelFrame(parent, text="System Monitor", padding=5)
        monitor_frame.pack(fill="x", pady=(0, 5))
        
        monitor_btn_frame = ttk.Frame(monitor_frame)
        monitor_btn_frame.pack(fill="x", pady=2)
        
        cpu_monitor_btn = ttk.Button(
            monitor_btn_frame,
            text="CPU Monitor (SS:5)",
            command=self.callbacks.get('start_cpu_monitor', lambda: None),
            state="disabled",
            width=20,
        )
        cpu_monitor_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['cpu_monitor_btn'] = cpu_monitor_btn
        
        sensor_cal_btn = ttk.Button(
            monitor_btn_frame,
            text="Sensor Cal (SS:6)",
            command=self.callbacks.get('start_sensor_calibration', lambda: None),
            state="disabled",
            width=20,
        )
        sensor_cal_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['sensor_cal_btn'] = sensor_cal_btn
        
        # === 系统控制 ===
        control_frame = ttk.LabelFrame(parent, text="System Control", padding=5)
        control_frame.pack(fill="x", pady=(0, 5))
        
        control_btn_frame1 = ttk.Frame(control_frame)
        control_btn_frame1.pack(fill="x", pady=2)
        
        buzzer_btn = ttk.Button(
            control_btn_frame1,
            text="Buzzer (SS:14)",
            command=self.callbacks.get('trigger_buzzer', lambda: None),
            state="disabled",
            width=18,
        )
        buzzer_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['buzzer_btn'] = buzzer_btn
        
        check_upgrade_btn = ttk.Button(
            control_btn_frame1,
            text="Check Upgrade (SS:15)",
            command=self.callbacks.get('check_upgrade', lambda: None),
            state="disabled",
            width=18,
        )
        check_upgrade_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['check_upgrade_btn'] = check_upgrade_btn
        
        control_btn_frame2 = ttk.Frame(control_frame)
        control_btn_frame2.pack(fill="x", pady=2)
        
        ap_mode_btn = ttk.Button(
            control_btn_frame2,
            text="AP Mode (SS:16)",
            command=self.callbacks.get('enter_ap_mode', lambda: None),
            state="disabled",
            width=18,
        )
        ap_mode_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['ap_mode_btn'] = ap_mode_btn
        
        # SS:18 已经在 Cloud 标签页中有 MQTT 模式切换按钮
        # 这里不再重复添加
        
        # === 提示信息 ===
        hint_frame = ttk.Frame(parent)
        hint_frame.pack(fill="x", pady=(5, 0))
        
        hint_text = ttk.Label(
            hint_frame,
            text="Note: SS:18 (MQTT Mode) is available in Cloud tab",
            font=("Arial", 8),
            foreground="gray"
        )
        hint_text.pack(anchor="w", padx=2)

    
    # ============================================================================
    # 重构后的5个主标签页
    # ============================================================================
    
    def _setup_dashboard_tab(self, parent):
        """
        Dashboard标签页 - 系统状态总览和快速操作
        """
        t = LightTheme
        
        # 主容器
        main_frame = tk.Frame(parent, bg=t.BG_MAIN)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === 上部：状态卡片和快速操作 ===
        top_frame = tk.Frame(main_frame, bg=t.BG_MAIN)
        top_frame.pack(fill="x", pady=(0, 10))
        
        # 左侧：系统状态
        status_card = tk.LabelFrame(
            top_frame,
            text=" System Status ",
            bg=t.BG_CARD,
            fg=t.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        status_card.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        status_items = [
            ("connection_status", "Connection:", "Disconnected", t.TEXT_SECONDARY),
            ("calibration_status", "Calibration:", "Unknown", t.TEXT_SECONDARY),
            ("activation_status", "Activation:", "Not Activated", t.ERROR),
            ("network_status", "Network:", "Not Configured", t.TEXT_SECONDARY),
        ]
        
        for var_name, label, default, color in status_items:
            row = tk.Frame(status_card, bg=t.BG_CARD)
            row.pack(fill="x", pady=3)
            
            tk.Label(row, text=f"● {label}", bg=t.BG_CARD, fg=t.TEXT_PRIMARY,
                    font=("Segoe UI", 9)).pack(side="left")
            
            var = StringVar(value=default)
            self.vars[var_name] = var
            lbl = tk.Label(row, textvariable=var, bg=t.BG_CARD, fg=color,
                          font=("Segoe UI", 9, "bold"))
            lbl.pack(side="right")
            self.widgets[f'{var_name}_label'] = lbl
        
        # 右侧：快速操作
        actions_card = tk.LabelFrame(
            top_frame,
            text=" Quick Actions ",
            bg=t.BG_CARD,
            fg=t.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        actions_card.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        action_buttons = [
            ("Connect Serial", "toggle_connection", t.PRIMARY),
            ("Start Stream", "toggle_data_stream", t.SUCCESS),
            ("Read Config", "read_device_info", t.INFO),
            ("Save Config", "save_sensor_config", t.WARNING),
        ]
        
        for i, (text, callback_key, color) in enumerate(action_buttons):
            if i % 2 == 0:
                row = tk.Frame(actions_card, bg=t.BG_CARD)
                row.pack(fill="x", pady=3)
            
            btn = tk.Button(
                row,
                text=text,
                command=self.callbacks.get(callback_key, lambda: None),
                bg=color,
                fg=t.TEXT_ON_PRIMARY if color != t.BG_CARD else t.TEXT_PRIMARY,
                font=("Segoe UI", 9),
                relief="flat",
                padx=15,
                pady=5,
                cursor="hand2"
            )
            btn.pack(side="left" if i % 2 == 0 else "right", expand=True, fill="x", padx=2)
            self.widgets[f'dashboard_{callback_key}_btn'] = btn
        
        # === 中部：实时数据预览 ===
        data_card = tk.LabelFrame(
            main_frame,
            text=" Real-time Overview ",
            bg=t.BG_CARD,
            fg=t.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        data_card.pack(fill="x", pady=10)
        
        data_hint = tk.Label(
            data_card,
            text="Charts will be displayed here when data stream is active",
            bg=t.BG_CARD,
            fg=t.TEXT_SECONDARY,
            font=("Segoe UI", 9, "italic")
        )
        data_hint.pack(pady=20)
        
        # === 下部：最近活动日志 ===
        log_card = tk.LabelFrame(
            main_frame,
            text=" Recent Activity ",
            bg=t.BG_CARD,
            fg=t.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        log_card.pack(fill="both", expand=True)
        
        # 活动日志文本框
        self.widgets['activity_log'] = scrolledtext.ScrolledText(
            log_card,
            height=6,
            bg=t.BG_MAIN,
            fg=t.TEXT_PRIMARY,
            font=("Consolas", 9),
            relief="flat",
            state="disabled"
        )
        self.widgets['activity_log'].pack(fill="both", expand=True)
    
    def _setup_network_tab(self, parent):
        """
        Network标签页 - 二级标签：WiFi/MQTT/Cloud/Position
        """
        t = LightTheme
        
        main_frame = tk.Frame(parent, bg=t.BG_MAIN)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建二级Notebook
        notebook = ttk.Notebook(main_frame, style='Secondary.TNotebook')
        notebook.pack(fill="both", expand=True)
        
        # WiFi标签
        wifi_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(wifi_tab, text=" WiFi ")
        self._setup_wifi_tab(wifi_tab)
        
        # MQTT标签
        mqtt_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(mqtt_tab, text=" MQTT ")
        self._setup_mqtt_tab(mqtt_tab)
        
        # Cloud标签
        cloud_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(cloud_tab, text=" Cloud ")
        self._setup_cloud_tab(cloud_tab)
        
        # Position标签
        position_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(position_tab, text=" Position ")
        self._setup_position_tab(position_tab)
    
    def _setup_sensors_tab(self, parent):
        """
        Sensors标签页 - 二级标签：Filter/Alarm/Auxiliary
        """
        t = LightTheme
        
        main_frame = tk.Frame(parent, bg=t.BG_MAIN)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建二级Notebook
        notebook = ttk.Notebook(main_frame, style='Secondary.TNotebook')
        notebook.pack(fill="both", expand=True)
        
        # Filter标签
        filter_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(filter_tab, text=" Filter ")
        self._setup_advanced_tab(filter_tab)
        
        # Alarm Levels标签
        alarm_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(alarm_tab, text=" Alarm Levels ")
        self._setup_alarm_levels_tab(alarm_tab)
        
        # Auxiliary标签
        aux_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(aux_tab, text=" Auxiliary ")
        self._setup_auxiliary_tab(aux_tab)
    
    def _setup_system_main_tab(self, parent):
        """
        System标签页 - 二级标签：Control/Camera/OTA/Debug
        """
        t = LightTheme
        
        main_frame = tk.Frame(parent, bg=t.BG_MAIN)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建二级Notebook
        notebook = ttk.Notebook(main_frame, style='Secondary.TNotebook')
        notebook.pack(fill="both", expand=True)
        
        # Control标签
        control_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(control_tab, text=" Control ")
        self._setup_system_tab(control_tab)
        
        # Camera标签
        camera_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(camera_tab, text=" Camera ")
        self._setup_camera_tab(camera_tab)
        
        # OTA标签
        ota_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(ota_tab, text=" OTA ")
        self._setup_ota_tab(ota_tab)
        
        # Debug标签
        debug_tab = tk.Frame(notebook, bg=t.BG_CARD)
        notebook.add(debug_tab, text=" Debug ")
        self._setup_debug_tab(debug_tab)
    
    def _setup_calibration_main_tab(self, parent):
        """
        Calibration标签页 - 完整的六位置校准流程
        """
        t = LightTheme
        
        main_frame = tk.Frame(parent, bg=t.BG_MAIN)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === 进度显示 ===
        progress_card = tk.LabelFrame(
            main_frame,
            text=" Calibration Progress ",
            bg=t.BG_CARD,
            fg=t.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        progress_card.pack(fill="x", pady=(0, 10))
        
        # 6位置状态
        positions_frame = tk.Frame(progress_card, bg=t.BG_CARD)
        positions_frame.pack(fill="x", pady=5)
        
        positions = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
        for i, pos in enumerate(positions):
            pos_frame = tk.Frame(positions_frame, bg=t.BG_CARD)
            pos_frame.pack(side="left", expand=True, padx=2)
            
            lbl = tk.Label(
                pos_frame,
                text=f"{i+1}. {pos}",
                bg=t.BG_CARD,
                fg=t.TEXT_SECONDARY,
                font=("Segoe UI", 9)
            )
            lbl.pack()
            
            status_lbl = tk.Label(
                pos_frame,
                text="○",
                bg=t.BG_CARD,
                fg=t.TEXT_SECONDARY,
                font=("Segoe UI", 14)
            )
            status_lbl.pack()
            self.widgets[f'cal_pos_{i}_status'] = status_lbl
        
        # 进度条
        progress_row = tk.Frame(progress_card, bg=t.BG_CARD)
        progress_row.pack(fill="x", pady=5)
        
        tk.Label(
            progress_row,
            text="Progress:",
            bg=t.BG_CARD,
            fg=t.TEXT_PRIMARY,
            font=("Segoe UI", 9)
        ).pack(side="left")
        
        self.vars['cal_progress'] = StringVar(value="0%")
        tk.Label(
            progress_row,
            textvariable=self.vars['cal_progress'],
            bg=t.BG_CARD,
            fg=t.PRIMARY,
            font=("Segoe UI", 9, "bold")
        ).pack(side="right")
        
        # === 当前位置操作 ===
        current_card = tk.LabelFrame(
            main_frame,
            text=" Current Position ",
            bg=t.BG_CARD,
            fg=t.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        current_card.pack(fill="x", pady=10)
        
        self.vars['current_cal_position'] = StringVar(value="Ready to start calibration")
        tk.Label(
            current_card,
            textvariable=self.vars['current_cal_position'],
            bg=t.BG_CARD,
            fg=t.TEXT_PRIMARY,
            font=("Segoe UI", 10)
        ).pack(pady=5)
        
        # 控制按钮
        btn_frame = tk.Frame(current_card, bg=t.BG_CARD)
        btn_frame.pack(fill="x", pady=10)
        
        buttons = [
            ("Start Calibration", "start_calibration", t.PRIMARY),
            ("Capture", "capture_position", t.SUCCESS),
            ("Stop", "stop_calibration", t.ERROR),
        ]
        
        for text, key, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=text,
                command=self.callbacks.get(key, lambda: None),
                bg=color,
                fg=t.TEXT_ON_PRIMARY,
                font=("Segoe UI", 9),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2"
            )
            btn.pack(side="left", expand=True, fill="x", padx=5)
            self.widgets[f'cal_{key}_btn'] = btn
        
        # === 校准结果 ===
        result_card = tk.LabelFrame(
            main_frame,
            text=" Calibration Results ",
            bg=t.BG_CARD,
            fg=t.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        result_card.pack(fill="both", expand=True, pady=(10, 0))
        
        result_hint = tk.Label(
            result_card,
            text="Calibration parameters will be displayed here after completion",
            bg=t.BG_CARD,
            fg=t.TEXT_SECONDARY,
            font=("Segoe UI", 9, "italic")
        )
        result_hint.pack(pady=20)
