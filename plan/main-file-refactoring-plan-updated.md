# 主文件重构计划 (Updated)

**Generated**: 2026-03-02  
**当前主文件大小**: 2,809 行  
**目标主文件大小**: < 300 行（仅保留协调逻辑）  
**预计减少**: ~2,500 行 (90%)  
**预计耗时**: 3-4 周（渐进式重构）

---

## 现状分析

### 当前主文件包含的职责

| 模块 | 方法数量 | 行数估算 | 复杂度 |
|------|----------|----------|--------|
| GUI 布局 | 15+ | ~500 | 中 |
| 图表管理 | 10+ | ~400 | 高 |
| 串口通信 | 12+ | ~350 | 中 |
| 校准流程 | 8+ | ~350 | 高 |
| 激活流程 | 10+ | ~300 | 中 |
| 网络配置 | 12+ | ~300 | 低 |
| 数据处理 | 6+ | ~200 | 中 |
| 统计计算 | 5+ | ~150 | 低 |
| **总计** | **~78** | **~2,809** | - |

### 已提取的模块（无需改动）

- ✅ `sensor_calibrator/config.py` - 配置常量
- ✅ `sensor_calibrator/data_buffer.py` - 数据缓冲区
- ✅ `sensor_calibrator/data_processor.py` - 数据处理
- ✅ `sensor_calibrator/chart_manager.py` - 图表管理
- ✅ `sensor_calibrator/ui_manager.py` - UI管理
- ✅ `activation.py` - 激活算法
- ✅ `calibration.py` - 校准算法

---

## 目标架构

```
重构前                          重构后
┌─────────────────────────┐      ┌─────────────────────────┐
│  StableSensorCalibrator │      │  StableSensorCalibrator │
│  (2,809 lines)          │      │  (~200 lines)           │
│                         │      │  - 初始化协调器          │
│  - GUI 布局              │      │  - 组件组装             │
│  - 图表管理              │  →   │  - 主循环               │
│  - 串口通信              │      │                         │
│  - 校准流程              │      │  使用以下组件:          │
│  - 激活流程              │      │  - ChartManager         │
│  - 网络配置              │      │  - UIManager            │
│  - 数据处理              │      │  - SerialManager        │
│  - ...                  │      │  - CalibrationWorkflow  │
│                         │      │  - ActivationWorkflow   │
│                         │      │  - NetworkManager       │
└─────────────────────────┘      └─────────────────────────┘
```

---

## Sprint 规划

### Sprint 0: 准备阶段（1-2天）

**目标**: 建立安全网，确保重构过程可回滚

#### Task 0.1: 创建功能回归测试
- **Location**: `tests/test_integration.py`
- **Description**: 
  - 创建基础测试框架
  - 添加关键功能的冒烟测试
  - 验证串口连接、数据解析、校准计算
- **Acceptance Criteria**:
  - 测试可以运行
  - 覆盖核心数据流路径
- **Validation**:
  ```bash
  python -m pytest tests/test_integration.py -v
  ```

#### Task 0.2: 备份当前工作版本
- **Description**:
  - 创建 git tag: `v1.0-before-refactor`
  - 记录当前功能清单
- **Acceptance Criteria**:
  - 可以回滚到重构前状态
  - 功能清单完整

#### Task 0.3: 分析方法依赖关系
- **Location**: `docs/dependency-analysis.md`
- **Description**:
  - 分析方法调用关系
  - 识别共享状态
  - 确定拆分边界
- **Acceptance Criteria**:
  - 生成方法依赖图
  - 识别出 6 个职责边界

---

### Sprint 1: 提取串口管理模块（3-4天）

**目标**: 将串口通信逻辑提取到 SerialManager 类
**预计减少**: ~350 行

#### Task 1.1: 创建 SerialManager 类骨架
- **Location**: `sensor_calibrator/serial_manager.py`
- **Description**:
  ```python
  class SerialManager:
      """管理串口连接和通信"""
      def __init__(self, callbacks):
          self.ser = None
          self.callbacks = callbacks
          self.is_connected = False
          self.is_reading = False
          
      def connect(self, port, baudrate):
          """连接串口"""
          pass
          
      def disconnect(self):
          """断开串口"""
          pass
          
      def send_command(self, command):
          """发送命令"""
          pass
          
      def start_reading(self):
          """开始读取数据"""
          pass
          
      def stop_reading(self):
          """停止读取数据"""
          pass
  ```
- **Acceptance Criteria**:
  - 类定义完整
  - 可以通过导入

#### Task 1.2: 迁移串口连接相关方法
- **迁移方法**:
  - `toggle_connection()`
  - `connect_serial()`
  - `disconnect_serial()`
  - `refresh_ports()`
- **Acceptance Criteria**:
  - 串口连接功能完整
  - 错误处理保持

#### Task 1.3: 迁移数据流控制方法
- **迁移方法**:
  - `toggle_data_stream()` / `toggle_data_stream2()`
  - `start_data_stream()` / `start_data_stream2()`
  - `stop_data_stream()` / `stop_data_stream2()`
  - `read_serial_data()`
- **Acceptance Criteria**:
  - 数据流控制正常
  - 线程安全保持

#### Task 1.4: 迁移 SS 命令方法
- **迁移方法**:
  - `send_ss_command()`
  - `send_ss0_start_stream()`
  - `send_ss1_start_calibration()`
  - `send_ss4_stop_stream()`
  - `send_ss8_get_properties()`
- **Acceptance Criteria**:
  - SS 命令功能正常
  - 响应处理正确

#### Task 1.5: 修改主文件使用 SerialManager
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 实例化 SerialManager
  - 转发串口相关调用
- **Dependencies**: Task 1.1-1.4
- **Acceptance Criteria**:
  - 主文件减少 ~350 行
  - 串口功能完整
  - 所有 SS 命令正常工作

---

### Sprint 2: 提取网络配置模块（2-3天）

**目标**: 将网络配置逻辑提取到 NetworkManager 类
**预计减少**: ~300 行

#### Task 2.1: 创建 NetworkManager 类骨架
- **Location**: `sensor_calibrator/network_manager.py`
- **Description**:
  ```python
  class NetworkManager:
      """管理WiFi/MQTT/OTA配置"""
      def __init__(self, serial_manager, callbacks):
          self.serial_manager = serial_manager
          self.callbacks = callbacks
          self.wifi_params = {}
          self.mqtt_params = {}
          self.ota_params = {}
          
      def set_wifi_config(self, ssid, password):
          """设置WiFi配置"""
          pass
          
      def set_mqtt_config(self, broker, username, password, port):
          """设置MQTT配置"""
          pass
          
      def read_wifi_config(self):
          """读取WiFi配置"""
          pass
          
      def save_config_to_file(self):
          """保存配置到文件"""
          pass
          
      def load_config_from_file(self):
          """从文件加载配置"""
          pass
  ```
- **Acceptance Criteria**:
  - 类可以实例化
  - 依赖 SerialManager

#### Task 2.2: 迁移网络配置方法
- **迁移方法**:
  - `set_wifi_config()`
  - `set_mqtt_config()`
  - `set_ota_config()`
  - `read_wifi_config()`
  - `read_mqtt_config()`
  - `read_ota_config()`
  - `send_config_command()`
  - `extract_network_config()`
  - `display_network_summary()`
  - `save_network_config()`
  - `load_network_config()`
- **Acceptance Criteria**:
  - 网络配置功能完整
  - 文件读写正常

#### Task 2.3: 修改主文件使用 NetworkManager
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 实例化 NetworkManager
  - 转发网络配置相关调用
- **Dependencies**: Task 2.1, 2.2
- **Acceptance Criteria**:
  - 主文件减少 ~300 行
  - 网络配置功能完整

---

### Sprint 3: 提取工作流程模块（4-5天）

**目标**: 将校准和激活流程提取为独立工作流类
**预计减少**: ~650 行

#### Task 3.1: 创建 CalibrationWorkflow 类
- **Location**: `sensor_calibrator/calibration_workflow.py`
- **Description**:
  ```python
  class CalibrationWorkflow:
      """管理6位置校准流程"""
      def __init__(self, serial_manager, data_processor, callbacks):
          self.serial_manager = serial_manager
          self.data_processor = data_processor
          self.callbacks = callbacks
          self.current_position = 0
          self.calibration_positions = []
          self.is_calibrating = False
          
      def start_calibration(self):
          """开始校准流程"""
          pass
          
      def capture_position(self):
          """捕获当前位置数据"""
          pass
          
      def collect_calibration_data(self, position):
          """收集校准数据"""
          pass
          
      def process_calibration_data(self, data):
          """处理校准数据"""
          pass
          
      def finish_calibration(self):
          """完成校准并计算参数"""
          pass
          
      def generate_calibration_commands(self):
          """生成校准命令"""
          pass
          
      def send_all_commands(self):
          """发送所有校准命令"""
          pass
          
      def reset_calibration_state(self):
          """重置校准状态"""
          pass
  ```
- **Acceptance Criteria**:
  - 可以使用 calibration.py 的算法
  - 状态管理正确

#### Task 3.2: 创建 ActivationWorkflow 类
- **Location**: `sensor_calibrator/activation_workflow.py`
- **Description**:
  ```python
  class ActivationWorkflow:
      """管理传感器激活流程"""
      def __init__(self, callbacks):
          self.callbacks = callbacks
          self.mac_address = None
          self.generated_key = None
          self.sensor_activated = False
          
      def extract_mac_from_properties(self, properties):
          """从属性中提取MAC地址"""
          pass
          
      def validate_mac_address(self, mac_str):
          """验证MAC地址格式"""
          pass
          
      def generate_key_from_mac(self, mac_address):
          """基于MAC生成密钥"""
          from activation import generate_key_from_mac
          return generate_key_from_mac(mac_address)
          
      def verify_key(self, input_key, mac_address):
          """验证密钥"""
          pass
          
      def check_activation_status(self):
          """检查激活状态"""
          pass
          
      def activate_sensor(self, mac_address, user_key):
          """激活传感器"""
          pass
          
      def verify_activation(self):
          """验证激活"""
          pass
          
      def display_activation_info(self):
          """显示激活信息"""
          pass
  ```
- **Acceptance Criteria**:
  - 使用现有的 activation.py
  - 密钥生成正确

#### Task 3.3: 修改主文件使用工作流类
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 实例化 CalibrationWorkflow 和 ActivationWorkflow
  - 转发相关调用
- **Dependencies**: Task 3.1, 3.2
- **Acceptance Criteria**:
  - 主文件减少 ~650 行
  - 校准和激活功能正常

---

### Sprint 4: 整合图表和UI模块（3-4天）

**目标**: 验证并完善已提取的 ChartManager 和 UIManager
**预计减少**: ~200 行（优化和清理）

#### Task 4.1: 验证 ChartManager 完整性
- **Location**: `sensor_calibrator/chart_manager.py`
- **检查方法**:
  - `setup_plots()` - 初始化4个子图
  - `update_charts()` - 更新图表数据
  - `adjust_y_limits()` - 调整Y轴范围
  - Blit 优化相关方法
- **Acceptance Criteria**:
  - 图表功能完整
  - 性能优化仍然有效
  - 窗口移动不卡顿

#### Task 4.2: 验证 UIManager 完整性
- **Location**: `sensor_calibrator/ui_manager.py`
- **检查内容**:
  - 左侧面板布局
  - 按钮回调绑定
  - 统计标签管理
  - 属性树显示
- **Acceptance Criteria**:
  - UI 布局正确
  - 所有控件可访问
  - 回调机制工作正常

#### Task 4.3: 清理主文件图表/UI代码
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 移除已迁移到模块的代码
  - 更新导入语句
  - 确保主文件仅调用模块接口
- **Acceptance Criteria**:
  - 主文件减少 ~200 行
  - 图表和UI功能正常

---

### Sprint 5: 清理和优化（2-3天）

**目标**: 清理主文件，整合所有模块，优化性能
**预计减少**: ~300 行

#### Task 5.1: 清理主文件剩余方法
- **需要迁移/清理的方法**:
  - `set_coordinate_mode()` / `set_local_coordinate_mode()` / `set_global_coordinate_mode()`
  - `enable_config_buttons()`
  - `ask_read_properties()` / `read_sensor_properties()` / `read_properties_thread()`
  - `auto_save_properties()` / `display_sensor_properties()` / `populate_properties_tree()`
  - `display_properties_summary()` / `save_properties_to_file()`
  - `update_position_display()`
  - `send_commands_thread()` / `resend_all_commands()`
  - `save_calibration_parameters()` / `load_calibration_parameters()`

#### Task 5.2: 优化主类结构
- **Location**: `StableSensorCalibrator.py`
- **目标结构**:
  ```python
  class StableSensorCalibrator:
      """传感器校准应用程序主类 - 仅协调器"""
      
      def __init__(self):
          # 初始化组件
          self.serial_manager = SerialManager(callbacks)
          self.chart_manager = ChartManager(parent)
          self.ui_manager = UIManager(root, callbacks)
          self.network_manager = NetworkManager(self.serial_manager, callbacks)
          self.calibration_workflow = CalibrationWorkflow(...)
          self.activation_workflow = ActivationWorkflow(...)
          
      def run(self):
          """主循环"""
          self.root.mainloop()
  ```
- **Acceptance Criteria**:
  - 主文件 < 300 行
  - 仅保留协调逻辑

#### Task 5.3: 更新包导出
- **Location**: `sensor_calibrator/__init__.py`
- **Description**:
  - 导出新的模块
  - 更新 `__all__`
- **Acceptance Criteria**:
  - 可以从包导入所有新模块

#### Task 5.4: 创建重构文档
- **Location**: `docs/refactoring-guide.md`
- **Description**:
  - 记录新架构
  - 说明各模块职责
  - 提供开发指南
- **Acceptance Criteria**:
  - 文档完整
  - 有示例代码

#### Task 5.5: 最终回归测试
- **Description**:
  - 完整功能测试
  - 性能测试
  - 文档审查
- **Validation**:
  - 所有测试通过
  - 性能不低于重构前
  - 文档完整

---

## 重构后文件结构

```
SensorCalibrator/
├── StableSensorCalibrator.py          # ~200行，仅协调器
├── sensor_calibrator/
│   ├── __init__.py                    # 包导出
│   ├── config.py                      # 配置常量
│   ├── validators.py                  # 输入验证
│   ├── data_buffer.py                 # 数据缓冲区
│   ├── data_processor.py              # 数据处理
│   ├── chart_manager.py               # 图表管理
│   ├── ui_manager.py                  # UI管理
│   ├── serial_manager.py              # 串口管理（新增）
│   ├── network_manager.py             # 网络配置（新增）
│   ├── calibration_workflow.py        # 校准流程（新增）
│   └── activation_workflow.py         # 激活流程（新增）
├── activation.py                      # 激活算法
├── calibration.py                     # 校准算法
├── network_config.py                  # 网络配置（可能合并）
├── serial_manager.py                  # 旧版（可能移除）
├── data_pipeline.py                   # 数据管道
└── tests/
    └── test_integration.py            # 集成测试
```

---

## 风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|---------|
| 功能回归 | 高 | 每 Sprint 后全面测试，保持可回滚 |
| tkinter 线程问题 | 中 | 保持主线程更新UI，使用 `after()` |
| 模块间循环依赖 | 中 | 使用回调机制，避免直接引用 |
| 性能下降 | 低 | 保持性能优化代码，基准测试对比 |
| 时间超期 | 中 | 可分阶段交付，每个 Sprint 独立有价值 |

---

## Rollback 计划

如果重构出现问题：

```bash
# 回滚到重构前版本
git checkout v1.0-before-refactor

# 或者放弃当前修改
git reset --hard v1.0-before-refactor
```

---

## 进度追踪

| Sprint | 预计行数减少 | 累计减少 | 主要产出 | 状态 |
|--------|-------------|---------|----------|------|
| Sprint 0 | 0 | 0 | 测试框架、备份 | ⏳ 待开始 |
| Sprint 1 | ~350 | 350 | SerialManager | ⏳ 待开始 |
| Sprint 2 | ~300 | 650 | NetworkManager | ⏳ 待开始 |
| Sprint 3 | ~650 | 1,300 | CalibrationWorkflow, ActivationWorkflow | ⏳ 待开始 |
| Sprint 4 | ~200 | 1,500 | 验证 ChartManager, UIManager | ⏳ 待开始 |
| Sprint 5 | ~1,109 | 2,609 | 清理优化 | ⏳ 待开始 |
| **目标** | - | **~2,500** | **主文件 < 300行** | - |

---

## 建议的启动策略

1. **保守方案**: 从 Sprint 0 开始，建立完整的测试基础后再进行重构
2. **激进方案**: 跳过 Sprint 0，直接从 Sprint 1 开始（如果你已有信心）
3. **推荐方案**: 先做 Sprint 0 的 Task 0.2（备份），然后开始 Sprint 1

---

**准备开始哪个 Sprint？** 或者你对这个计划有任何问题或建议？
