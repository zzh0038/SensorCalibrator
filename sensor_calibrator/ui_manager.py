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
        """设置 ttk 样式"""
        style = ttk.Style()
        style.configure("Compact.TLabelframe", padding=12)
    
    def _setup_title(self):
        """设置标题"""
        title_label = ttk.Label(
            self.parent, text="Calibration Panel", font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 6))
    
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
            text="Read Props",
            command=self.callbacks.get('read_properties', lambda: None),
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
            text="Local Coord (SS:2)",
            command=self.callbacks.get('set_local_coordinate_mode', lambda: None),
            state="disabled",
            width=18,
        )
        local_coord_btn.pack(side="left", padx=2, expand=True, fill="x")
        self.widgets['local_coord_btn'] = local_coord_btn
        
        global_coord_btn = ttk.Button(
            coord_row,
            text="Global Coord (SS:3)",
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
        设置网络配置 Notebook 标签页
        
        包含4个标签页：
        - WiFi: WiFi配置
        - MQTT: MQTT配置
        - OTA: OTA配置
        - Alarm & Device: 报警阈值和设备控制
        """
        # 创建 Notebook 容器框架
        notebook_frame = ttk.LabelFrame(
            self.parent, text="Network & Device Configuration", style="Compact.TLabelframe"
        )
        notebook_frame.pack(fill="x", pady=(0, 5))
        
        # 创建 Notebook
        notebook = ttk.Notebook(notebook_frame)
        notebook.pack(fill="x", padx=5, pady=2)
        
        # === Tab 1: WiFi ===
        wifi_tab = ttk.Frame(notebook)
        notebook.add(wifi_tab, text="WiFi")
        self._setup_wifi_tab(wifi_tab)
        
        # === Tab 2: MQTT ===
        mqtt_tab = ttk.Frame(notebook)
        notebook.add(mqtt_tab, text="MQTT")
        self._setup_mqtt_tab(mqtt_tab)
        
        # === Tab 3: OTA ===
        ota_tab = ttk.Frame(notebook)
        notebook.add(ota_tab, text="OTA")
        self._setup_ota_tab(ota_tab)
        
        # === Tab 4: Alarm & Device ===
        alarm_device_tab = ttk.Frame(notebook)
        notebook.add(alarm_device_tab, text="Alarm & Device")
        self._setup_alarm_device_tab(alarm_device_tab)
    
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
    
    # [保留原有的方法作为备份，但不再被调用]
    def _setup_wifi_section(self):
        """设置 WiFi 配置区域"""
        wifi_frame = ttk.LabelFrame(
            self.parent, text="WiFi Settings", style="Compact.TLabelframe"
        )
        wifi_frame.pack(fill="x", pady=(0, 5))
        
        wifi_content = ttk.Frame(wifi_frame)
        wifi_content.pack(fill="x", padx=5, pady=2)
        
        # SSID
        ssid_frame = ttk.Frame(wifi_content)
        ssid_frame.pack(fill="x", pady=1)
        
        ttk.Label(ssid_frame, text="SSID:", font=("Arial", 9)).pack(side="left", padx=2)
        
        ssid_var = StringVar()
        self.vars['ssid'] = ssid_var
        ssid_entry = ttk.Entry(ssid_frame, textvariable=ssid_var, font=("Arial", 9), width=20)
        ssid_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # 密码
        password_frame = ttk.Frame(wifi_content)
        password_frame.pack(fill="x", pady=1)
        
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
        wifi_btn_frame = ttk.Frame(wifi_content)
        wifi_btn_frame.pack(fill="x", pady=2)
        
        set_wifi_btn = ttk.Button(
            wifi_btn_frame,
            text="Set WiFi",
            command=self.callbacks.get('set_wifi_config', lambda: None),
            state="disabled",
            width=10,
        )
        set_wifi_btn.pack(side="left", padx=2)
        self.widgets['set_wifi_btn'] = set_wifi_btn
        
        read_wifi_btn = ttk.Button(
            wifi_btn_frame,
            text="Read WiFi",
            command=self.callbacks.get('read_wifi_config', lambda: None),
            state="disabled",
            width=10,
        )
        read_wifi_btn.pack(side="left", padx=2)
        self.widgets['read_wifi_btn'] = read_wifi_btn
    
    def _setup_mqtt_section(self):
        """设置 MQTT 配置区域"""
        mqtt_frame = ttk.LabelFrame(
            self.parent, text="MQTT Settings", style="Compact.TLabelframe"
        )
        mqtt_frame.pack(fill="x", pady=(0, 5))
        
        mqtt_content = ttk.Frame(mqtt_frame)
        mqtt_content.pack(fill="x", padx=5, pady=2)
        
        # Broker
        broker_frame = ttk.Frame(mqtt_content)
        broker_frame.pack(fill="x", pady=1)
        
        ttk.Label(broker_frame, text="Broker:", font=("Arial", 9)).pack(side="left", padx=2)
        
        broker_var = StringVar()
        self.vars['mqtt_broker'] = broker_var
        broker_entry = ttk.Entry(broker_frame, textvariable=broker_var, font=("Arial", 9), width=20)
        broker_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # Username
        user_frame = ttk.Frame(mqtt_content)
        user_frame.pack(fill="x", pady=1)
        
        ttk.Label(user_frame, text="Username:", font=("Arial", 9)).pack(side="left", padx=2)
        
        user_var = StringVar()
        self.vars['mqtt_user'] = user_var
        user_entry = ttk.Entry(user_frame, textvariable=user_var, font=("Arial", 9), width=20)
        user_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # Password
        pwd_frame = ttk.Frame(mqtt_content)
        pwd_frame.pack(fill="x", pady=1)
        
        ttk.Label(pwd_frame, text="Password:", font=("Arial", 9)).pack(side="left", padx=2)
        
        pwd_var = StringVar()
        self.vars['mqtt_password'] = pwd_var
        pwd_entry = ttk.Entry(pwd_frame, textvariable=pwd_var, show="*", font=("Arial", 9), width=20)
        pwd_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # Port
        port_frame = ttk.Frame(mqtt_content)
        port_frame.pack(fill="x", pady=1)
        
        ttk.Label(port_frame, text="Port:", font=("Arial", 9)).pack(side="left", padx=2)
        
        port_var = StringVar(value="1883")
        self.vars['mqtt_port'] = port_var
        port_entry = ttk.Entry(port_frame, textvariable=port_var, font=("Arial", 9), width=10)
        port_entry.pack(side="left", padx=2)
        
        # 按钮
        mqtt_btn_frame = ttk.Frame(mqtt_content)
        mqtt_btn_frame.pack(fill="x", pady=2)
        
        set_mqtt_btn = ttk.Button(
            mqtt_btn_frame,
            text="Set MQTT",
            command=self.callbacks.get('set_mqtt_config', lambda: None),
            state="disabled",
            width=10,
        )
        set_mqtt_btn.pack(side="left", padx=2)
        self.widgets['set_mqtt_btn'] = set_mqtt_btn
        
        read_mqtt_btn = ttk.Button(
            mqtt_btn_frame,
            text="Read MQTT",
            command=self.callbacks.get('read_mqtt_config', lambda: None),
            state="disabled",
            width=10,
        )
        read_mqtt_btn.pack(side="left", padx=2)
        self.widgets['read_mqtt_btn'] = read_mqtt_btn
    
    def _setup_ota_section(self):
        """设置 OTA 配置区域"""
        ota_frame = ttk.LabelFrame(
            self.parent, text="OTA Settings", style="Compact.TLabelframe"
        )
        ota_frame.pack(fill="x", pady=(0, 5))
        
        ota_content = ttk.Frame(ota_frame)
        ota_content.pack(fill="x", padx=5, pady=2)
        
        # URL1
        url1_frame = ttk.Frame(ota_content)
        url1_frame.pack(fill="x", pady=1)
        
        ttk.Label(url1_frame, text="URL1:", font=("Arial", 9)).pack(side="left", padx=2)
        
        url1_var = StringVar()
        self.vars['url1'] = url1_var
        url1_entry = ttk.Entry(url1_frame, textvariable=url1_var, font=("Arial", 9), width=20)
        url1_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # URL2
        url2_frame = ttk.Frame(ota_content)
        url2_frame.pack(fill="x", pady=1)
        
        ttk.Label(url2_frame, text="URL2:", font=("Arial", 9)).pack(side="left", padx=2)
        
        url2_var = StringVar()
        self.vars['url2'] = url2_var
        url2_entry = ttk.Entry(url2_frame, textvariable=url2_var, font=("Arial", 9), width=20)
        url2_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # URL3
        url3_frame = ttk.Frame(ota_content)
        url3_frame.pack(fill="x", pady=1)
        
        ttk.Label(url3_frame, text="URL3:", font=("Arial", 9)).pack(side="left", padx=2)
        
        url3_var = StringVar()
        self.vars['url3'] = url3_var
        url3_entry = ttk.Entry(url3_frame, textvariable=url3_var, font=("Arial", 9), width=20)
        url3_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # URL4
        url4_frame = ttk.Frame(ota_content)
        url4_frame.pack(fill="x", pady=1)
        
        ttk.Label(url4_frame, text="URL4:", font=("Arial", 9)).pack(side="left", padx=2)
        
        url4_var = StringVar()
        self.vars['url4'] = url4_var
        url4_entry = ttk.Entry(url4_frame, textvariable=url4_var, font=("Arial", 9), width=20)
        url4_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # 按钮
        ota_btn_frame = ttk.Frame(ota_content)
        ota_btn_frame.pack(fill="x", pady=2)
        
        set_ota_btn = ttk.Button(
            ota_btn_frame,
            text="Set OTA",
            command=self.callbacks.get('set_ota_config', lambda: None),
            state="disabled",
            width=10,
        )
        set_ota_btn.pack(side="left", padx=2)
        self.widgets['set_ota_btn'] = set_ota_btn
        
        read_ota_btn = ttk.Button(
            ota_btn_frame,
            text="Read OTA",
            command=self.callbacks.get('read_ota_config', lambda: None),
            state="disabled",
            width=10,
        )
        read_ota_btn.pack(side="left", padx=2)
        self.widgets['read_ota_btn'] = read_ota_btn
    
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
