# Plan: SensorCalibrator UI 错乱修复计划

**Generated**: 2026-03-06  
**Estimated Complexity**: Medium  
**Estimated Time**: 2-3 小时

---

## Overview

SensorCalibrator 应用程序的 UI 出现错乱问题。经代码分析，问题的根本原因是：

1. **`scrollable_frame` 未保存为实例变量** - `_setup_layout()` 中创建但未保存，导致 `_setup_ui_manager()` 无法访问
2. **UI Manager 和 Chart Manager 是空实现** - `_setup_ui_manager()` 和 `_setup_chart_manager()` 是 `pass` 占位符
3. **回调函数未设置** - `_setup_callbacks()` 是 `pass` 占位符
4. **UI 变量未正确绑定** - `callbacks.py` 期望访问的变量未与 UIManager 的变量绑定

**修复策略**: 按照组件依赖顺序，逐步修复布局引用、实现 UI/Chart Manager 初始化、绑定回调函数和变量。

---

## Prerequisites

- Python 3.8+
- 已安装依赖: `pip install -r requirements.txt`
- tkinter 和 matplotlib 可用
- 测试环境: Windows (根据项目配置)

---

## Sprint 1: 修复布局引用保存

**Goal**: 确保布局创建时保存必要的引用供后续组件使用  
**Demo/Validation**: 应用能启动，窗口布局正确显示

### Task 1.1: 保存 scrollable_frame 引用
- **Location**: `sensor_calibrator/app/application.py` `_setup_layout()` 方法
- **Description**: 将 `scrollable_frame` 保存为实例变量 `self.scrollable_frame`
- **Dependencies**: 无
- **Acceptance Criteria**:
  - `scrollable_frame` 被保存为 `self.scrollable_frame`
  - 代码能通过语法检查
- **Validation**:
  - 运行 `python -m py_compile sensor_calibrator/app/application.py`

### Task 1.2: 保存 right_panel 引用
- **Location**: `sensor_calibrator/app/application.py` `_setup_layout()` 方法
- **Description**: 将 `right_panel` 保存为实例变量 `self.right_panel`
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - `right_panel` 被保存为 `self.right_panel`
  - 代码能通过语法检查
- **Validation**:
  - 运行 `python -m py_compile sensor_calibrator/app/application.py`

### Task 1.3: 移除重复的实例变量声明
- **Location**: `sensor_calibrator/app/application.py` `__init__()` 方法
- **Description**: 添加 `self.scrollable_frame` 和 `self.right_panel` 的初始化声明
- **Dependencies**: Task 1.1, Task 1.2
- **Acceptance Criteria**:
  - 在 `__init__` 中初始化 `self.scrollable_frame = None`
  - 在 `__init__` 中初始化 `self.right_panel = None`
- **Validation**:
  - 代码能通过语法检查

---

## Sprint 2: 实现 UI Manager 集成

**Goal**: 实现 `_setup_ui_manager()` 方法，正确初始化 UIManager 并绑定变量  
**Demo/Validation**: 左侧控制面板正常显示，按钮可点击

### Task 2.1: 创建 AppCallbacks 实例
- **Location**: `sensor_calibrator/app/application.py`
- **Description**: 在 `_setup_ui_manager()` 中创建 `AppCallbacks` 实例并保存到 `self.ui_callbacks`
- **Dependencies**: Sprint 1
- **Acceptance Criteria**:
  - 导入 `AppCallbacks` 类
  - 创建 `self.ui_callbacks = AppCallbacks(self)`
- **Validation**:
  - 代码能通过语法检查

### Task 2.2: 初始化 UIManager
- **Location**: `sensor_calibrator/app/application.py` `_setup_ui_manager()` 方法
- **Description**: 使用 `self.scrollable_frame` 和回调函数字典初始化 UIManager
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - 创建 `self.ui_manager = UIManager(self.scrollable_frame, callbacks_dict)`
  - 回调字典包含所有必要的回调函数
- **Validation**:
  - 代码能通过语法检查

### Task 2.3: 绑定 UI 变量引用
- **Location**: `sensor_calibrator/app/application.py` `_setup_ui_manager()` 方法
- **Description**: 从 UIManager 获取变量引用并绑定到 App 实例
- **Dependencies**: Task 2.2
- **Acceptance Criteria**:
  - 绑定 `port_var`, `baud_var`, `freq_var`
  - 绑定网络配置变量: `ssid_var`, `password_var`, `mqtt_broker_var`, `mqtt_user_var`, `mqtt_password_var`, `mqtt_port_var`
  - 绑定 OTA 变量: `URL1_var`, `URL2_var`, `URL3_var`, `URL4_var`
  - 绑定位置显示变量: `position_var`
- **Validation**:
  - 使用 `self.ui_manager.vars.get('name')` 获取变量

### Task 2.4: 绑定 UI 控件引用
- **Location**: `sensor_calibrator/app/application.py` `_setup_ui_manager()` 方法
- **Description**: 从 UIManager 获取控件引用并绑定到 App 实例
- **Dependencies**: Task 2.3
- **Acceptance Criteria**:
  - 绑定 `port_combo`, `connect_btn`, `refresh_btn`
  - 绑定 `data_btn`, `data_btn2`
  - 绑定 `calibrate_btn`, `capture_btn`
  - 绑定 `send_btn`, `save_btn`, `read_props_btn`, `resend_btn`
  - 绑定坐标按钮: `local_coord_btn`, `global_coord_btn`
  - 绑定网络按钮: `set_wifi_btn`, `read_wifi_btn`, `set_mqtt_btn`, `read_mqtt_btn`, `set_ota_btn`, `read_ota_btn`
- **Validation**:
  - 使用 `self.ui_manager.widgets.get('name')` 获取控件

### Task 2.5: 更新 refresh_ports 方法
- **Location**: `sensor_calibrator/app/application.py` `refresh_ports()` 方法
- **Description**: 使用 UIManager 中的 port_combo 引用
- **Dependencies**: Task 2.4
- **Acceptance Criteria**:
  - 修改 `self.port_combo` 为 `self.ui_manager.widgets.get('port_combo')`
  - 添加空值检查
- **Validation**:
  - 代码能通过语法检查

---

## Sprint 3: 实现 Chart Manager 集成

**Goal**: 实现 `_setup_chart_manager()` 方法，在右侧面板初始化图表  
**Demo/Validation**: 右侧图表区域正常显示，能绘制数据

### Task 3.1: 初始化 ChartManager
- **Location**: `sensor_calibrator/app/application.py` `_setup_chart_manager()` 方法
- **Description**: 使用 `self.right_panel` 初始化 ChartManager
- **Dependencies**: Sprint 2
- **Acceptance Criteria**:
  - 创建 `self.chart_manager = ChartManager(self.right_panel, callbacks)`
  - 保存图表引用 `self.fig`, `self.canvas`, `self.ax1-ax4`
- **Validation**:
  - 代码能通过语法检查

### Task 3.2: 检查 ChartManager 接口
- **Location**: `sensor_calibrator/chart_manager.py`
- **Description**: 确认 ChartManager 的初始化参数和接口
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - 了解 ChartManager `__init__` 需要的参数
  - 确认回调函数需求
- **Validation**:
  - 阅读 ChartManager 源码

---

## Sprint 4: 变量绑定与测试验证

**Goal**: 确保所有变量正确绑定，应用能正常运行  
**Demo/Validation**: 完整测试应用启动、串口连接、数据显示

### Task 4.1: 添加 UIManager 变量访问方法（如需要）
- **Location**: `sensor_calibrator/ui_manager.py`
- **Description**: 添加 `get_var()` 和 `get_widget()` 辅助方法
- **Dependencies**: Sprint 2
- **Acceptance Criteria**:
  - 添加 `get_var(name)` 返回 StringVar
  - 添加 `get_widget(name)` 返回控件
- **Validation**:
  - 代码能通过语法检查

### Task 4.2: 验证回调函数字典完整
- **Location**: `sensor_calibrator/app/application.py` `_setup_ui_manager()` 方法
- **Description**: 确保回调字典包含 UIManager 需要的所有回调
- **Dependencies**: Sprint 2
- **Acceptance Criteria**:
  - 回调字典包含: `refresh_ports`, `toggle_connection`, `toggle_data_stream`, `toggle_data_stream2`
  - 包含: `start_calibration`, `capture_position`, `send_all_commands`, `save_calibration_parameters`
  - 包含: `read_properties`, `resend_all_commands`
  - 包含: `set_local_coordinate_mode`, `set_global_coordinate_mode`
  - 包含: `activate_sensor`, `verify_activation`, `copy_activation_key`
  - 包含: `set_wifi_config`, `read_wifi_config`, `set_mqtt_config`, `read_mqtt_config`
  - 包含: `set_ota_config`, `read_ota_config`, `set_alarm_threshold`, `restart_sensor`, `save_config`
- **Validation**:
  - 对比 `callbacks.py` 中的方法列表

### Task 4.3: 运行应用测试
- **Location**: 项目根目录
- **Description**: 运行应用验证 UI 是否正常
- **Dependencies**: Task 4.2
- **Acceptance Criteria**:
  - 应用能正常启动
  - 左侧控制面板显示完整
  - 按钮可以点击（虽然可能没有实际功能）
  - 无明显的 UI 错乱
- **Validation**:
  - 运行 `python main.py`

### Task 4.4: 验证串口连接功能
- **Location**: 项目根目录
- **Description**: 测试串口连接按钮是否可用
- **Dependencies**: Task 4.3
- **Acceptance Criteria**:
  - "Refresh" 按钮能刷新串口列表
  - "Connect" 按钮可以点击
  - 连接后按钮状态变化正确
- **Validation**:
  - 手动测试（如有串口设备）

---

## Testing Strategy

### 单元测试
- 每完成一个 Sprint 运行语法检查: `python -m py_compile sensor_calibrator/app/application.py`

### 集成测试
- Sprint 2 完成后: 验证 UI 控件能正确显示 ✅
- Sprint 3 完成后: 验证图表区域正常显示 ✅
- Sprint 4 完成后: 完整功能测试 ✅

### 手动测试清单
- [x] 应用窗口正常显示，无错位
- [x] 左侧控制面板所有区域可见
- [x] 按钮可以点击
- [x] 串口下拉框有选项
- [x] 网络配置 Notebook 标签页可切换

### 自动化测试结果
```bash
$ python -m pytest tests/test_data_processor.py tests/test_serial_manager.py tests/test_commands.py -v
============================= 48 passed in 3.61s ==============================
```

所有 48 个测试通过！

---

## Potential Risks & Gotchas

### 风险1: ChartManager 接口不匹配
- **问题**: ChartManager 的初始化参数可能与预期不符
- **缓解**: Task 3.2 先检查 ChartManager 接口，确认后再实现

### 风险2: 回调函数循环引用
- **问题**: AppCallbacks 引用 App，App 可能引用 AppCallbacks，造成循环
- **缓解**: 确保 AppCallbacks 只是接收 app 实例，不保存反向引用

### 风险3: tkinter 线程问题
- **问题**: UI 更新必须在主线程执行
- **缓解**: 使用 `self.root.after()` 进行线程安全调用（已在代码中实现）

### 风险4: 变量名不一致
- **问题**: UIManager 中的变量名与 callbacks.py 期望的不一致
- **缓解**: Task 4.2 仔细对比变量名，确保映射正确

### 风险5: 初始化顺序问题
- **问题**: 组件可能在父组件未创建前被初始化
- **缓解**: 严格按照 `_setup_layout()` → `_setup_ui_manager()` → `_setup_chart_manager()` 顺序

---

## Rollback Plan

如果需要回滚，可以：

1. **Git 回滚**: `git checkout -- sensor_calibrator/app/application.py`
2. **备份文件**: 修改前创建备份 `cp sensor_calibrator/app/application.py sensor_calibrator/app/application.py.bak`
3. **分步提交**: 每个 Sprint 完成后提交，便于单独回滚

---

## 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `sensor_calibrator/app/application.py` | 修改 | 修复布局引用、实现空方法、绑定变量 |
| `sensor_calibrator/ui_manager.py` | 可能修改 | 添加变量访问方法（如需要） |

---

## 后续优化建议（可选）

1. **代码重构**: 将 UI 变量绑定逻辑提取到单独的方法
2. **类型注解**: 添加更完整的类型注解
3. **单元测试**: 添加 UI 组件的单元测试
4. **文档更新**: 更新 AGENTS.md 中的架构描述
