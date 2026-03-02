# 方法依赖关系分析

**Generated**: 2026-03-02  
**分析文件**: `StableSensorCalibrator.py` (2,809 行)

---

## 1. 职责边界识别

根据方法功能，识别出 6 个主要职责边界：

### 1.1 串口通信模块 (Serial Communication)
**方法列表** (12个):
- `toggle_connection()`
- `connect_serial()`
- `disconnect_serial()`
- `refresh_ports()`
- `toggle_data_stream()` / `toggle_data_stream2()`
- `start_data_stream()` / `start_data_stream2()`
- `stop_data_stream()` / `stop_data_stream2()`
- `read_serial_data()`
- `send_ss_command()` / `send_ss0_start_stream()` / `send_ss1_start_calibration()` / `send_ss4_stop_stream()` / `send_ss8_get_properties()`

**依赖状态**:
- `self.ser` - 串口对象
- `self.is_connected` - 连接状态
- `self.is_reading` - 读取状态
- `self.data_queue` - 数据队列

**依赖其他模块**:
- 调用 UI 更新方法显示日志
- 调用数据处理方法解析数据

---

### 1.2 网络配置模块 (Network Configuration)
**方法列表** (12个):
- `set_wifi_config()`
- `set_mqtt_config()`
- `set_ota_config()`
- `read_wifi_config()` / `read_mqtt_config()` / `read_ota_config()`
- `send_config_command()`
- `extract_network_config()`
- `enable_config_buttons()`
- `display_network_summary()`
- `save_network_config()`
- `load_network_config()`
- `set_coordinate_mode()` / `set_local_coordinate_mode()` / `set_global_coordinate_mode()`

**依赖状态**:
- `self.wifi_params` - WiFi配置
- `self.mqtt_params` - MQTT配置
- `self.ota_params` - OTA配置

**依赖其他模块**:
- 依赖 SerialManager 发送命令
- 调用 UI 方法更新显示

---

### 1.3 校准流程模块 (Calibration Workflow)
**方法列表** (8个):
- `start_calibration()`
- `capture_position()`
- `collect_calibration_data()`
- `process_calibration_data()`
- `update_position_display()`
- `finish_calibration()`
- `generate_calibration_commands()`
- `send_all_commands()` / `send_commands_thread()` / `resend_all_commands()`
- `reset_calibration_state()`

**依赖状态**:
- `self.is_calibrating` - 校准状态
- `self.current_position` - 当前位置
- `self.calibration_positions` - 位置数据
- `self.calibration_params` - 校准参数

**依赖其他模块**:
- 依赖 SerialManager 发送 SS1 命令
- 依赖 DataProcessor 获取数据
- 调用 calibration.py 算法
- 调用 UI 更新显示

---

### 1.4 激活流程模块 (Activation Workflow)
**方法列表** (10个):
- `generate_key_from_mac()`
- `verify_key()`
- `extract_mac_from_properties()`
- `validate_mac_address()`
- `check_activation_status()`
- `activate_sensor()` / `activate_sensor_thread()`
- `verify_activation()` / `verify_activation_thread()`
- `update_activation_status()`
- `extract_and_process_mac()`
- `display_activation_info()`

**依赖状态**:
- `self.mac_address` - MAC地址
- `self.generated_key` - 生成的密钥
- `self.sensor_activated` - 激活状态

**依赖其他模块**:
- 调用 activation.py 算法
- 调用 UI 更新显示
- 可能需要 SerialManager 读取属性

---

### 1.5 属性管理模块 (Properties Management)
**方法列表** (6个):
- `ask_read_properties()`
- `read_sensor_properties()` / `read_properties_thread()`
- `auto_save_properties()`
- `display_sensor_properties()`
- `populate_properties_tree()`
- `display_properties_summary()`
- `save_properties_to_file()`

**依赖状态**:
- `self.sensor_properties` - 传感器属性

**依赖其他模块**:
- 依赖 SerialManager 发送 SS8 命令
- 调用 UI 更新属性树
- 调用 ActivationWorkflow 处理 MAC

---

### 1.6 图表管理模块 (Chart Management) - 已提取 ✅
**所在位置**: `sensor_calibrator/chart_manager.py`

**方法**:
- `setup_plots()`
- `update_charts()`
- `_update_chart_statistics_to_manager()`
- `adjust_y_limits()`
- `_init_blit()` / `_update_with_blit()` (如存在)

---

### 1.7 UI 管理模块 (UI Management) - 已提取 ✅
**所在位置**: `sensor_calibrator/ui_manager.py`

**方法**:
- `setup_gui()`
- `setup_left_panel()`
- `setup_stats_grid()`
- `log_message()` / `_add_log_entry()`

---

## 2. 方法调用依赖图

```
StableSensorCalibrator (协调器)
├── SerialManager
│   ├── 发送 SS0/SS1/SS4/SS8 命令
│   ├── 读写串口数据
│   └── 管理连接状态
├── NetworkManager
│   ├── 构建配置命令
│   ├── 发送给 SerialManager
│   └── 保存/加载配置文件
├── CalibrationWorkflow
│   ├── 使用 SerialManager 发送命令
│   ├── 使用 DataProcessor 获取数据
│   ├── 调用 calibration.py 算法
│   └── 更新 UI 显示进度
├── ActivationWorkflow
│   ├── 调用 activation.py 算法
│   ├── 可能需要读取属性
│   └── 更新 UI 显示状态
├── PropertiesManager
│   ├── 使用 SerialManager 读取属性
│   ├── 调用 ActivationWorkflow 处理 MAC
│   └── 更新 UI 属性树
├── ChartManager (已提取)
│   └── 独立更新图表
├── UIManager (已提取)
│   └── 管理所有控件
└── DataProcessor (已提取)
    └── 处理数据解析和统计
```

---

## 3. 共享状态分析

### 3.1 需要共享的状态

| 状态 | 类型 | 共享模块 | 建议方案 |
|------|------|----------|----------|
| `self.ser` | 串口对象 | SerialManager, NetworkManager, PropertiesManager | 通过 SerialManager 提供接口 |
| `self.is_connected` | bool | 多个模块 | 通过回调或属性访问 |
| `self.sensor_properties` | dict | ActivationWorkflow, PropertiesManager | 通过回调传递 |
| `self.calibration_params` | dict | CalibrationWorkflow | 作为返回值 |
| `self.mac_address` | str | ActivationWorkflow, PropertiesManager | 通过回调传递 |

### 3.2 回调函数设计

```python
# 主文件定义的回调字典
callbacks = {
    # UI 更新回调
    'log_message': self.ui_manager.log_message,
    'update_status': self.ui_manager.update_status,
    'update_progress': self.ui_manager.update_progress,
    
    # 数据访问回调
    'get_sensor_data': self.data_processor.get_latest_data,
    'get_statistics': self.data_processor.get_statistics,
    
    # 状态查询回调
    'is_connected': lambda: self.serial_manager.is_connected,
    'is_reading': lambda: self.serial_manager.is_reading,
}
```

---

## 4. 重构顺序建议

基于依赖关系，建议按以下顺序重构：

1. **Sprint 1: SerialManager** (基础依赖)
   - 最少外部依赖
   - 其他模块都依赖它

2. **Sprint 2: NetworkManager** (依赖 SerialManager)
   - 依赖串口发送命令
   - 相对独立的功能

3. **Sprint 3: CalibrationWorkflow + ActivationWorkflow** (依赖以上模块)
   - 依赖 SerialManager 发送命令
   - 依赖 DataProcessor 获取数据

4. **Sprint 4: PropertiesManager** (可选)
   - 可以合并到主文件或独立模块
   - 依赖 SerialManager 和 ActivationWorkflow

5. **Sprint 5: 清理验证** (验证 ChartManager + UIManager)
   - 已提取的模块验证
   - 主文件清理

---

## 5. 风险点

### 5.1 tkinter 线程安全
- 所有 UI 更新必须在主线程
- 解决方案: 使用 `self.root.after()` 调度 UI 更新

### 5.2 循环依赖
- 避免模块间直接引用
- 解决方案: 使用回调函数传递依赖

### 5.3 状态同步
- 多个模块可能同时访问状态
- 解决方案: 通过主文件协调，或使用属性访问器

---

## 6. 模块接口设计

### 6.1 SerialManager 接口
```python
class SerialManager:
    def __init__(self, callbacks): ...
    def connect(self, port, baudrate) -> bool: ...
    def disconnect(self) -> None: ...
    def send_command(self, command: str) -> tuple[bool, str]: ...
    def send_ss_command(self, cmd_id: int, ...) -> bool: ...
    def start_reading(self) -> None: ...
    def stop_reading(self) -> None: ...
    @property
    def is_connected(self) -> bool: ...
    @property
    def is_reading(self) -> bool: ...
```

### 6.2 NetworkManager 接口
```python
class NetworkManager:
    def __init__(self, serial_manager, callbacks): ...
    def set_wifi_config(self, ssid: str, password: str) -> tuple[bool, str]: ...
    def set_mqtt_config(self, ...) -> tuple[bool, str]: ...
    def read_wifi_config(self) -> tuple[bool, dict]: ...
    def save_config_to_file(self, filepath: str) -> bool: ...
    def load_config_from_file(self, filepath: str) -> bool: ...
```

### 6.3 CalibrationWorkflow 接口
```python
class CalibrationWorkflow:
    def __init__(self, serial_manager, data_processor, callbacks): ...
    def start_calibration(self) -> bool: ...
    def capture_position(self) -> bool: ...
    def finish_calibration(self) -> dict: ...  # 返回校准参数
    def reset(self) -> None: ...
    @property
    def is_calibrating(self) -> bool: ...
    @property
    def current_position(self) -> int: ...
```

### 6.4 ActivationWorkflow 接口
```python
class ActivationWorkflow:
    def __init__(self, callbacks): ...
    def generate_key_from_mac(self, mac: str) -> str: ...
    def verify_key(self, input_key: str, mac: str) -> bool: ...
    def activate_sensor(self, mac: str, user_key: str) -> tuple[bool, str]: ...
    def check_activation_status(self) -> bool: ...
    @property
    def mac_address(self) -> str | None: ...
    @property
    def is_activated(self) -> bool: ...
```

---

**分析完成，可以开始 Sprint 1: 提取 SerialManager**
