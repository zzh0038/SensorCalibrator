# SensorCalibrator 依赖关系分析

**分析日期**: 2026-02-28
**目的**: 为主文件拆分重构确定边界

---

## 当前架构概览

```
StableSensorCalibrator (God Class - 3,687 lines)
├── 状态管理 (70+ 实例变量)
├── GUI 初始化 (~550 lines)
│   ├── setup_gui()
│   ├── setup_left_panel()
│   ├── setup_compact_stats()
│   └── 各种 setup_* 方法
├── 串口通信 (~300 lines)
│   ├── toggle_connection()
│   ├── read_serial_data()
│   ├── send_*_commands()
│   └── 回调处理
├── 数据可视化 (~400 lines)
│   ├── setup_plots()
│   ├── update_charts()
│   ├── update_chart_statistics()
│   ├── adjust_y_limits()
│   └── blit 优化相关
├── 校准流程 (~300 lines)
│   ├── start_calibration()
│   ├── capture_position()
│   ├── finish_calibration()
│   └── update_position_display()
├── 激活流程 (~300 lines)
│   ├── activate_sensor()
│   ├── verify_activation()
│   ├── generate_key_from_mac()
│   └── 各种 extract_* 方法
├── 网络配置 (~200 lines)
│   ├── set_wifi_config()
│   ├── set_mqtt_config()
│   ├── set_OTA_config()
│   └── read_*_config()
├── 数据处理 (~200 lines)
│   ├── parse_sensor_data()
│   ├── update_statistics()
│   ├── calculate_statistics()
│   └── clear_data()
└── 文件 I/O (~150 lines)
    ├── save_calibration()
    ├── load_calibration()
    └── save/load properties
```

---

## 共享状态分析

### 核心数据状态 (必须在模块间共享)

```python
# 数据存储 (需要 DataProcessor 管理)
time_data: deque          # X轴时间数据
mpu_accel_data: [deque x3]   # MPU6050 加速度
mpu_gyro_data: [deque x3]   # MPU6050 陀螺仪
adxl_accel_data: [deque x3]  # ADXL355 加速度
gravity_mag_data: deque      # 重力矢量模长

# 统计状态 (Statistics Manager)
real_time_stats: dict     # 实时统计信息
stats_labels: dict        # UI 标签引用

# 校准状态 (Calibration Workflow)
is_calibrating: bool
current_position: int
calibration_positions: list

# 激活状态 (Activation Workflow)
sensor_properties: dict
mac_address: str
sensor_activated: bool

# 串口状态 (Serial Manager)
ser: Serial
is_reading: bool
data_queue: Queue
```

---

## 重构边界建议

### 模块 1: ChartManager
**职责**: 所有 matplotlib 图表相关
**输入**: 数据字典
**输出**: 无 (直接操作 canvas)

```python
class ChartManager:
    def __init__(self, parent_widget):
        self.fig = None
        self.axes = {}
        self.canvas = None
    
    def setup_plots(self):
        """初始化4个子图"""
        pass
    
    def update_charts(self, data_dict):
        """更新图表数据"""
        pass
```

### 模块 2: UIManager
**职责**: 所有 tkinter GUI 组件
**输入**: callbacks 字典
**输出**: 无 (通过回调与 Main 通信)

```python
class UIManager:
    def __init__(self, root, callbacks):
        self.root = root
        self.callbacks = callbacks
        self.widgets = {}
    
    def setup_ui(self):
        """设置完整UI"""
        pass
    
    def get_widget(self, name):
        """获取控件引用"""
        return self.widgets.get(name)
```

### 模块 3: DataProcessor
**职责**: 数据解析、存储、统计计算
**输入**: 原始数据字符串
**输出**: 处理后的数据结构

```python
class DataProcessor:
    def __init__(self):
        self.buffers = {
            'time': deque(maxlen=Config.MAX_DATA_POINTS),
            'mpu_accel': [deque(maxlen=Config.MAX_DATA_POINTS) for _ in range(3)],
            # ...
        }
    
    def process_packet(self, data_string):
        """解析并存储一个数据包"""
        pass
    
    def get_display_data(self, max_points=None):
        """获取用于显示的数据"""
        pass
```

### 模块 4: CalibrationWorkflow
**职责**: 6位置校准流程管理
**输入**: 传感器数据, 用户操作
**输出**: 校准参数

```python
class CalibrationWorkflow:
    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.current_position = 0
        self.calibration_positions = []
    
    def start(self):
        """开始校准流程"""
        pass
    
    def capture_current_position(self, sensor_data):
        """捕获当前位置数据"""
        pass
```

### 模块 5: ActivationWorkflow
**职责**: 传感器激活流程
**输入**: MAC地址, 用户密钥
**输出**: 激活状态

```python
class ActivationWorkflow:
    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.mac_address = None
        self.is_activated = False
    
    def extract_mac_from_properties(self, properties):
        """从设备属性提取MAC"""
        pass
    
    def verify_activation(self, user_key, mac_address):
        """验证用户输入的密钥"""
        pass
```

---

## 重构顺序建议

### Phase 1: 低风险模块 (依赖少)
1. **ChartManager** - 相对独立，只依赖数据输入
2. **UIManager** - 通过回调解耦

### Phase 2: 数据流模块
3. **DataProcessor** - 核心数据管理，其他模块依赖它

### Phase 3: 业务流程模块
4. **CalibrationWorkflow** - 依赖 DataProcessor
5. **ActivationWorkflow** - 相对独立

### Phase 4: 清理
6. **Main** - 简化为协调器

---

## 风险评估

| 模块 | 风险等级 | 原因 | 缓解策略 |
|------|---------|------|---------|
| ChartManager | 低 | 可视化独立 | 保持相同 API |
| UIManager | 中 | tkinter 状态复杂 | 保留 widget 引用 |
| DataProcessor | 高 | 核心数据流 | 充分测试 |
| CalibrationWorkflow | 中 | 状态机复杂 | 保留现有逻辑 |
| ActivationWorkflow | 低 | 算法已提取 | 使用现有模块 |

---

## 回滚检查点

1. **v1.0-before-refactor** (已创建) - 原始状态
2. **v1.1-after-chart** (计划) - ChartManager 完成后
3. **v1.2-after-ui** (计划) - UIManager 完成后
4. **v1.3-after-data** (计划) - DataProcessor 完成后
