# UI 清屏与刷新功能实现计划

**生成日期**: 2026-03-16
**预计复杂度**: 低
**关联需求**: 点击 Disconnect 按钮或设备断连后清屏，添加页面刷新按钮

---

## 概述

本计划实现在传感器断开连接或用户点击刷新按钮时，将 UI 恢复到初始状态的功能。主要涉及数据缓冲区清空、图表重置、统计信息清零、UI 变量重置等操作。

### 清屏范围
| 组件 | 操作 | 说明 |
|------|------|------|
| 图表数据 | 清空所有曲线 | 4个子图的所有线条数据清空 |
| 统计数据 | 重置为初始值 | μ: 0.000, σ: 0.000 |
| 数据缓冲区 | 清空 | time_data, accel_data, gyro_data, gravity_data |
| 频率显示 | 重置为 "0 Hz" | 数据流频率 |
| 位置显示 | 重置为 "Position: Not calibrating" | 校准状态 |
| 校准命令区 | 清空 | 右侧底部命令文本框 |
| 激活状态 | 重置为初始 | MAC: --, Status: Not Activated |
| 日志区 | **保留** | 不清空，便于问题追溯 |

---

## 前置条件

- Python >= 3.8
- 现有代码结构理解（已阅读 ui_manager.py, application.py, callbacks.py, chart_manager.py, data_buffer.py）
- 了解 tkinter StringVar 和 Widget 的操作方式

---

## Sprint 1: 核心重置功能实现

**目标**: 在 application.py 中实现核心的 UI 重置逻辑

**演示/验证**:
- 能够通过代码调用重置方法
- 数据缓冲区被清空
- 图表数据被清空

### Task 1.1: 添加重置 UI 的核心方法
- **位置**: `sensor_calibrator/app/application.py`
- **描述**: 在 `SensorCalibratorApp` 类中添加 `reset_ui_state()` 方法，用于统一重置所有 UI 状态
- **依赖**: 无
- **实现要点**:
  1. 调用 `data_processor.clear_all()` 清空数据缓冲区
  2. 调用 `chart_manager.clear_data()` 清空图表
  3. 重置频率显示为 "0 Hz"
  4. 重置位置显示为 "Position: Not calibrating"
  5. 清空校准命令文本区
  6. 重置激活状态显示
  7. 记录日志 "UI 已重置"
- **验收标准**:
  - 方法可以被正常调用
  - 不会抛出异常
  - 日志正确输出
- **验证方法**:
  ```python
  # 在测试中调用
  app.reset_ui_state()
  assert app.data_processor.is_empty()
  ```

### Task 1.2: 添加统计标签重置辅助方法
- **位置**: `sensor_calibrator/app/application.py`
- **描述**: 添加 `_reset_statistics_display()` 私有方法，重置所有统计标签为初始值
- **依赖**: Task 1.1
- **实现要点**:
  1. 遍历 `stats_labels` 字典
  2. 将所有 Mean/Std 标签重置为 μ: 0.000, σ: 0.000
  3. 重力统计重置为 Mean: 0.000, Std: 0.000
- **验收标准**:
  - 所有统计标签正确重置
  - 不会遗漏任何标签

### Task 1.3: 添加激活状态重置辅助方法
- **位置**: `sensor_calibrator/app/application.py`
- **描述**: 添加 `_reset_activation_display()` 私有方法，重置激活状态显示
- **依赖**: Task 1.1
- **实现要点**:
  1. MAC 地址显示重置为 "--"
  2. 激活密钥清空
  3. 激活状态重置为 "Not Activated"（红色）
  4. 内部变量 `_aky_from_ss13` 重置为 None
- **验收标准**:
  - 激活区域显示正确重置
  - 内部状态同步更新

---

## Sprint 2: 断开连接时触发清屏

**目标**: 在断开串口连接时自动调用清屏功能

**演示/验证**:
- 点击 Disconnect 按钮后 UI 重置
- 设备异常断连时 UI 重置

### Task 2.1: 修改断开连接回调
- **位置**: `sensor_calibrator/app/callbacks.py`
- **描述**: 在 `disconnect_serial()` 方法末尾添加 `reset_ui_state()` 调用
- **依赖**: Sprint 1 完成
- **实现要点**:
  1. 在原有断开逻辑完成后调用 `self.app.reset_ui_state()`
  2. 确保在按钮状态更新之后调用
- **验收标准**:
  - 点击 Disconnect 后 UI 自动重置
  - 原有断开逻辑不受影响
- **验证方法**:
  1. 连接设备
  2. 开始数据流
  3. 点击 Disconnect
  4. 观察图表和统计是否清空

### Task 2.2: 处理异常断连情况
- **位置**: `sensor_calibrator/serial_manager.py`（检查并修改）
- **描述**: 确保设备异常断连（如拔掉 USB）时也能触发 UI 重置
- **依赖**: Task 2.1
- **实现要点**:
  1. 检查 `SerialManager` 的异常处理逻辑
  2. 确保 `_notify_connection_change(False)` 被正确调用
  3. 确认 `update_connection_state` 回调能传播到 UI 重置
- **验收标准**:
  - 异常断连时 UI 也能重置
  - 不会导致程序崩溃

---

## Sprint 3: 添加刷新页面按钮

**目标**: 在 UI 上添加刷新按钮，允许用户手动重置 UI

**演示/验证**:
- 页面上有刷新按钮
- 点击按钮后 UI 重置

### Task 3.1: 在 Commands 区域添加刷新按钮
- **位置**: `sensor_calibrator/ui_manager.py`
- **描述**: 在 `_setup_commands_section()` 方法中添加 "Reset UI" 按钮
- **依赖**: Sprint 1 完成
- **实现要点**:
  1. 在 Commands 区域底部添加新的一行
  2. 添加 "Reset UI" 按钮，宽度 15
  3. 绑定回调 `reset_ui`
  4. 按钮初始状态为 enabled（始终可用）
- **验收标准**:
  - 按钮正确显示在 Commands 区域
  - 按钮样式与其他按钮一致
  - 点击按钮能触发回调

### Task 3.2: 添加刷新按钮回调
- **位置**: `sensor_calibrator/app/callbacks.py`
- **描述**: 在 `AppCallbacks` 类中添加 `reset_ui()` 方法
- **依赖**: Task 3.1
- **实现要点**:
  1. 创建 `reset_ui()` 方法
  2. 调用 `self.app.reset_ui_state()`
  3. 记录日志 "页面已刷新"
- **验收标准**:
  - 回调方法正确绑定
  - 点击按钮后 UI 重置并记录日志

### Task 3.3: 注册刷新回调到 UIManager
- **位置**: `sensor_calibrator/app/application.py` 的 `_setup_ui_manager()` 方法
- **描述**: 在 callbacks 字典中添加 `reset_ui` 回调
- **依赖**: Task 3.2
- **实现要点**:
  在 `_setup_ui_manager()` 的 callbacks 字典中添加：
  ```python
  'reset_ui': self.ui_callbacks.reset_ui,
  ```
- **验收标准**:
  - 回调正确注册
  - 按钮点击能触发 `AppCallbacks.reset_ui()`

---

## Sprint 4: 测试与验证

**目标**: 确保清屏功能在各种场景下正常工作

**演示/验证**:
- 所有测试用例通过
- 无回归问题

### Task 4.1: 编写单元测试
- **位置**: `tests/test_ui_reset.py`（新建）
- **描述**: 为 reset_ui_state 方法编写单元测试
- **依赖**: Sprint 1-3 完成
- **测试用例**:
  1. `test_reset_ui_clears_data_buffer` - 验证数据缓冲区被清空
  2. `test_reset_ui_clears_chart_data` - 验证图表数据被清空
  3. `test_reset_ui_resets_statistics` - 验证统计标签重置
  4. `test_reset_ui_resets_frequency` - 验证频率显示重置
  5. `test_reset_ui_clears_commands` - 验证命令区清空
- **验收标准**:
  - 所有测试用例通过
  - 覆盖率 > 80%

### Task 4.2: 手动测试场景
- **位置**: 手动测试
- **描述**: 进行端到端的手动测试
- **测试场景**:
  1. **正常断连**: 连接设备 → 开始数据流 → 点击 Disconnect → 验证 UI 重置
  2. **异常断连**: 连接设备 → 开始数据流 → 拔掉 USB → 验证 UI 重置
  3. **手动刷新**: 连接设备 → 开始数据流 → 点击 Reset UI → 验证 UI 重置
  4. **重复刷新**: 多次点击 Reset UI 按钮 → 验证无异常
  5. **无连接刷新**: 未连接设备时点击 Reset UI → 验证正常工作
- **验收标准**:
  - 所有场景测试通过
  - 无异常或崩溃

---

## 测试策略

### 单元测试
- 使用 pytest 框架
- Mock 依赖组件（tkinter, serial）
- 验证状态变化而非 UI 实际显示

### 集成测试
- 运行完整应用流程
- 验证各组件协同工作

### 手动测试
- 真实设备连接测试
- 各种断连场景测试

---

## 潜在风险与注意事项

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| 多线程冲突 | 中 | 确保 `reset_ui_state()` 在主线程调用，使用 `root.after()` 调度 |
| 数据竞争 | 中 | 清空数据缓冲区时使用锁机制（data_buffer 已有锁保护）|
| 图表重绘失败 | 低 | `clear_data()` 使用 `canvas.draw_idle()` 安全重绘 |
| 日志被清空 | 低 | 明确日志区不在清屏范围内，保留历史记录 |
| 校准进行中重置 | 中 | 重置时自动停止校准状态，避免状态混乱 |

---

## 回滚计划

如需回滚更改：

1. **Git 回滚**:
   ```bash
   git revert <commit-hash>
   ```

2. **手动回滚**:
   - 删除 `reset_ui_state()` 方法
   - 删除 `disconnect_serial()` 中的调用
   - 删除 "Reset UI" 按钮相关代码
   - 删除 `reset_ui()` 回调

---

## 文件修改清单

| 文件路径 | 修改类型 | 说明 |
|----------|----------|------|
| `sensor_calibrator/app/application.py` | 新增 | `reset_ui_state()`, `_reset_statistics_display()`, `_reset_activation_display()` |
| `sensor_calibrator/app/callbacks.py` | 修改 | `disconnect_serial()` 添加重置调用，新增 `reset_ui()` |
| `sensor_calibrator/ui_manager.py` | 修改 | `_setup_commands_section()` 添加 Reset UI 按钮 |
| `tests/test_ui_reset.py` | 新增 | 单元测试文件 |

---

## 实施顺序建议

1. **先实现 Sprint 1**（核心功能）- 可以独立测试
2. **再实现 Sprint 2**（自动触发）- 验证断开连接时清屏
3. **再实现 Sprint 3**（手动按钮）- 添加刷新按钮
4. **最后 Sprint 4**（测试）- 全面验证

每个 Sprint 完成后都可以进行演示和验证。
