# 主文件拆分重构计划

**Generated**: 2026-02-28
**Estimated Complexity**: 高
**Estimated Duration**: 2-3 周
**当前主文件大小**: 3,687 行
**目标主文件大小**: < 300 行（仅保留协调逻辑）

---

## 概述

将 `StableSensorCalibrator.py` (3,687 行) 拆分为职责单一的模块，解决 God Class 问题。采用**渐进式重构**策略，确保每次修改后程序仍可运行。

### 拆分策略
```
当前架构                          目标架构
┌─────────────────────────┐      ┌─────────────────────────┐
│  StableSensorCalibrator │      │  StableSensorCalibrator │
│  (3,687 lines)          │      │  (~250 lines)           │
│                         │      │  - 初始化协调器          │
│  - GUI (550L)           │      │  - 组件组装             │
│  - Serial (300L)        │  →   │  - 主循环               │
│  - Charts (400L)        │      │                         │
│  - Calibration (300L)   │      │  使用以下组件:          │
│  - Activation (300L)    │      │  - ChartManager         │
│  - Network (200L)       │      │  - CalibrationWorkflow  │
│  - Stats (200L)         │      │  - ActivationWorkflow   │
│  - File I/O (150L)      │      │  - UIManager            │
└─────────────────────────┘      └─────────────────────────┘
```

### 关键原则
1. **渐进式重构** - 每次 Sprint 后程序可运行
2. **利用现有模块** - 使用已提取的 activation.py, calibration.py 等
3. **保持接口兼容** - 不破坏现有功能
4. **测试驱动** - 每阶段添加回归测试

---

## Sprint 0: 准备阶段（1-2天）

**Goal**: 建立安全网，确保重构过程可回滚
**Demo/Validation**: 运行测试确保功能正常

### Task 0.1: 创建功能回归测试
- **Location**: `tests/test_integration.py`
- **Description**: 
  - 创建基础测试框架
  - 添加关键功能的冒烟测试
  - 验证串口连接、数据解析、校准计算
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 测试可以运行
  - 覆盖核心数据流路径
- **Validation**:
  ```bash
  python -m pytest tests/test_integration.py -v
  ```

### Task 0.2: 备份当前工作版本
- **Description**:
  - 创建 git tag: `v1.0-before-refactor`
  - 记录当前功能清单
- **Acceptance Criteria**:
  - 可以回滚到重构前状态
  - 功能清单完整

### Task 0.3: 分析方法依赖关系
- **Location**: `docs/dependency-analysis.md`
- **Description**:
  - 分析方法调用关系
  - 识别共享状态
  - 确定拆分边界
- **Acceptance Criteria**:
  - 生成方法依赖图
  - 识别出 8 个职责边界

---

## Sprint 1: 提取 Chart 管理模块（3-4天）

**Goal**: 将图表相关逻辑（~400行）提取到独立模块
**Demo/Validation**: 
- 图表正常显示和更新
- 性能优化仍然有效
- 窗口移动不卡顿

### Task 1.1: 创建 ChartManager 类骨架
- **Location**: `sensor_calibrator/chart_manager.py`
- **Description**:
  ```python
  class ChartManager:
      """管理matplotlib图表的创建和更新"""
      def __init__(self, parent_widget):
          self.fig = None
          self.axes = {}
          self.lines = {}
          self.canvas = None
          
      def setup_plots(self):
          """初始化4个子图"""
          pass
          
      def update_charts(self, data):
          """更新图表数据"""
          pass
          
      def setup_blit_optimization(self):
          """设置blit优化"""
          pass
  ```
- **Dependencies**: Task 0.1
- **Acceptance Criteria**:
  - 类定义完整
  - 可以通过导入

### Task 1.2: 迁移图表初始化代码
- **Location**: 
  - 从: `StableSensorCalibrator.py` (lines ~1550-1650)
  - 到: `sensor_calibrator/chart_manager.py`
- **Description**:
  - 迁移 `setup_plots()` 方法
  - 迁移图表创建逻辑
  - 保持 matplotlib 配置
- **Acceptance Criteria**:
  - 图表可以正常创建
  - 4个子图布局正确

### Task 1.3: 迁移图表更新逻辑
- **Location**:
  - 从: `StableSensorCalibrator.py` (lines ~2618-2750)
  - 到: `sensor_calibrator/chart_manager.py`
- **Description**:
  - 迁移 `update_charts()`
  - 迁移 `update_chart_statistics()`
  - 迁移 `adjust_y_limits()`
  - 迁移 `_init_blit()` 和 `_update_with_blit()`
- **Acceptance Criteria**:
  - 图表更新正常
  - Blit 优化仍然有效

### Task 1.4: 修改主文件使用 ChartManager
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 替换图表相关代码为 ChartManager 调用
  - 保持公共接口不变
  ```python
  # 修改前
  self.setup_plots()
  self.update_charts()
  
  # 修改后
  self.chart_manager = ChartManager(right_panel)
  self.chart_manager.setup_plots()
  self.chart_manager.update_charts(data)
  ```
- **Dependencies**: Task 1.1, 1.2, 1.3
- **Acceptance Criteria**:
  - 主文件减少 ~400 行
  - 图表功能正常
  - 性能优化保持

### Task 1.5: 验证和回归测试
- **Description**:
  - 运行集成测试
  - 手动测试图表功能
  - 验证性能优化仍然有效
- **Validation**:
  ```bash
  python -m pytest tests/test_integration.py -v
  python StableSensorCalibrator.py  # 手动验证
  ```

---

## Sprint 2: 提取 UI 管理模块（4-5天）

**Goal**: 将 GUI 布局代码（~550行）提取到独立模块
**Demo/Validation**:
- 界面正常显示
- 所有按钮功能正常
- 布局无变化

### Task 2.1: 创建 UIManager 类骨架
- **Location**: `sensor_calibrator/ui_manager.py`
- **Description**:
  ```python
  class UIManager:
      """管理GUI布局和控件"""
      def __init__(self, root, callbacks):
          self.root = root
          self.callbacks = callbacks  # 回调函数字典
          self.widgets = {}
          
      def setup_ui(self):
          """设置完整UI"""
          pass
          
      def setup_left_panel(self, parent):
          """设置左侧面板"""
          pass
          
      def get_widget(self, name):
          """获取控件引用"""
          pass
  ```
- **Dependencies**: Sprint 1
- **Acceptance Criteria**:
  - 类可以实例化
  - 回调机制工作正常

### Task 2.2: 迁移左侧面板代码
- **Location**:
  - 从: `StableSensorCalibrator.py` (lines ~441-1000)
  - 到: `sensor_calibrator/ui_manager.py`
- **Description**:
  - 迁移 `setup_left_panel()`
  - 迁移串口设置、数据流控制、校准控制等
  - 将按钮回调改为传入的回调函数
- **Acceptance Criteria**:
  - 左侧面板可以独立创建
  - 所有控件可访问

### Task 2.3: 迁移统计信息面板
- **Location**:
  - 从: `StableSensorCalibrator.py` (lines ~524-580)
- **Description**:
  - 迁移统计标签创建
  - 保持统计更新接口
- **Acceptance Criteria**:
  - 统计面板显示正常

### Task 2.4: 修改主文件使用 UIManager
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 替换 GUI 初始化代码
  - 注册回调函数
  - 保持按钮命令行为
  ```python
  callbacks = {
      'toggle_connection': self.toggle_connection,
      'toggle_data_stream': self.toggle_data_stream,
      # ...
  }
  self.ui = UIManager(self.root, callbacks)
  self.ui.setup_ui()
  ```
- **Dependencies**: Task 2.1, 2.2, 2.3
- **Acceptance Criteria**:
  - 主文件再减少 ~500 行
  - UI 功能完整
  - 所有按钮正常工作

---

## Sprint 3: 提取工作流程模块（4-5天）

**Goal**: 将校准和激活流程提取为独立工作流类
**Demo/Validation**:
- 6位置校准流程正常
- 传感器激活功能正常

### Task 3.1: 创建 CalibrationWorkflow 类
- **Location**: `sensor_calibrator/calibration_workflow.py`
- **Description**:
  ```python
  class CalibrationWorkflow:
      """管理6位置校准流程"""
      def __init__(self, callbacks):
          self.callbacks = callbacks
          self.current_position = 0
          self.calibration_positions = []
          
      def start_calibration(self):
          """开始校准流程"""
          pass
          
      def capture_position(self, sensor_data):
          """捕获当前位置数据"""
          pass
          
      def finish_calibration(self):
          """完成校准并计算参数"""
          pass
  ```
- **Dependencies**: Sprint 2
- **Acceptance Criteria**:
  - 可以使用 calibration.py 的算法
  - 状态管理正确

### Task 3.2: 创建 ActivationWorkflow 类
- **Location**: `sensor_calibrator/activation_workflow.py`
- **Description**:
  ```python
  class ActivationWorkflow:
      """管理传感器激活流程"""
      def __init__(self, callbacks):
          self.callbacks = callbacks
          
      def activate_sensor(self, mac_address, user_key):
          """激活传感器"""
          pass
          
      def verify_activation(self):
          """验证激活状态"""
          pass
          
      def generate_key(self, mac_address):
          """基于MAC生成密钥"""
          from activation import generate_key_from_mac
          return generate_key_from_mac(mac_address)
  ```
- **Acceptance Criteria**:
  - 使用现有的 activation.py
  - 密钥生成正确

### Task 3.3: 迁移校准流程代码
- **Location**:
  - 从: `StableSensorCalibrator.py` (lines ~2914-3000)
- **Description**:
  - 迁移 `start_calibration()`, `capture_position()`
  - 迁移 `finish_calibration()`
  - 迁移 `update_position_display()`
- **Acceptance Criteria**:
  - 校准流程独立运行
  - 使用 calibration.py 的算法

### Task 3.4: 迁移激活流程代码
- **Location**:
  - 从: `StableSensorCalibrator.py` (lines ~700-900)
- **Description**:
  - 迁移激活相关方法
  - 使用现有的 activation.py
- **Acceptance Criteria**:
  - 激活功能完整
  - 使用提取的模块

### Task 3.5: 修改主文件使用工作流类
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 实例化工作流类
  - 转发相关调用
- **Dependencies**: Task 3.1-3.4
- **Acceptance Criteria**:
  - 主文件再减少 ~400 行
  - 校准和激活功能正常

---

## Sprint 4: 提取数据管理模块（3-4天）

**Goal**: 将数据处理和统计提取到独立模块
**Demo/Validation**:
- 数据处理正常
- 统计信息正确

### Task 4.1: 创建 DataProcessor 类
- **Location**: `sensor_calibrator/data_processor.py`
- **Description**:
  ```python
  class DataProcessor:
      """处理传感器数据，计算统计信息"""
      def __init__(self):
          self.buffers = {
              'time': deque(maxlen=Config.MAX_DATA_POINTS),
              'mpu_accel': [deque(maxlen=Config.MAX_DATA_POINTS) for _ in range(3)],
              # ...
          }
          
      def process_packet(self, data_string):
          """处理单个数据包"""
          pass
          
      def get_statistics(self, window_size):
          """获取统计信息"""
          pass
          
      def clear_data(self):
          """清空所有数据"""
          pass
  ```
- **Dependencies**: Sprint 3
- **Acceptance Criteria**:
  - 数据缓冲区管理正确
  - 统计计算准确

### Task 4.2: 迁移数据处理代码
- **Location**:
  - 从: `StableSensorCalibrator.py` (lines ~2433-2510)
- **Description**:
  - 迁移 `parse_sensor_data()`
  - 迁移 `calculate_statistics()`
  - 迁移 `update_statistics()`
- **Acceptance Criteria**:
  - 数据解析正确
  - 统计计算使用 numpy

### Task 4.3: 修改主文件使用 DataProcessor
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 替换数据处理相关代码
  - 保持数据访问接口
- **Dependencies**: Task 4.1, 4.2
- **Acceptance Criteria**:
  - 主文件再减少 ~300 行
  - 数据处理功能正常

---

## Sprint 5: 整合和清理（2-3天）

**Goal**: 清理主文件，整合所有模块
**Demo/Validation**:
- 主文件 < 300 行
- 所有功能完整
- 代码整洁

### Task 5.1: 清理主文件
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 移除已迁移的代码
  - 整理导入语句
  - 添加模块初始化
  ```python
  from sensor_calibrator import (
      Config, UIConfig, CalibrationConfig, SerialConfig,
      ChartManager, UIManager, 
      CalibrationWorkflow, ActivationWorkflow,
      DataProcessor
  )
  ```
- **Acceptance Criteria**:
  - 主文件简洁清晰
  - 仅保留协调逻辑

### Task 5.2: 更新包导出
- **Location**: `sensor_calibrator/__init__.py`
- **Description**:
  - 导出新的模块
  - 更新 `__all__`
- **Acceptance Criteria**:
  - 可以从包导入所有新模块

### Task 5.3: 创建重构文档
- **Location**: `docs/refactoring-guide.md`
- **Description**:
  - 记录新架构
  - 说明各模块职责
  - 提供开发指南
- **Acceptance Criteria**:
  - 文档完整
  - 有示例代码

### Task 5.4: 最终回归测试
- **Description**:
  - 完整功能测试
  - 性能测试
  - 文档审查
- **Validation**:
  - 所有测试通过
  - 性能不低于重构前
  - 文档完整

---

## 目标架构

重构完成后的文件结构：

```
SensorCalibrator/
├── StableSensorCalibrator.py      # ~250行，仅协调器
├── sensor_calibrator/
│   ├── __init__.py                # 包导出
│   ├── config.py                  # 配置常量
│   ├── validators.py              # 输入验证（从__init__迁移）
│   ├── data_buffer.py             # 数据缓冲区
│   ├── chart_manager.py           # 图表管理（新增）
│   ├── ui_manager.py              # UI管理（新增）
│   ├── calibration_workflow.py    # 校准流程（新增）
│   ├── activation_workflow.py     # 激活流程（新增）
│   └── data_processor.py          # 数据处理（新增）
├── activation.py                  # 激活算法（已存在）
├── calibration.py                 # 校准算法（已存在）
├── network_config.py              # 网络配置（已存在）
├── serial_manager.py              # 串口管理（已存在）
├── data_pipeline.py               # 数据管道（已存在）
└── tests/
    └── test_integration.py        # 集成测试
```

---

## 风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|---------|
| 功能回归 | 高 | 每 Sprint 后全面测试，保持可回滚 |
| 状态共享复杂 | 中 | 明确各模块状态边界，使用回调通信 |
| tkinter 线程问题 | 中 | 保持主线程更新UI，使用 `after()` |
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

| Sprint | 预计行数减少 | 累计减少 | 状态 |
|--------|-------------|---------|------|
| Sprint 0 | 0 | 0 | ⏳ 待开始 |
| Sprint 1 | ~400 | 400 | ⏳ 待开始 |
| Sprint 2 | ~500 | 900 | ⏳ 待开始 |
| Sprint 3 | ~400 | 1300 | ⏳ 待开始 |
| Sprint 4 | ~300 | 1600 | ⏳ 待开始 |
| Sprint 5 | ~200 | 1800 | ⏳ 待开始 |
| **目标** | - | **~3400** | 主文件 < 300行 |

---

**准备开始哪个 Sprint？** 建议从 Sprint 0 开始建立测试基础，或者如果你已有信心，可以直接开始 Sprint 1（图表模块提取，风险较低）。
