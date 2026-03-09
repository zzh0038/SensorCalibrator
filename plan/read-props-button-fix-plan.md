# Plan: 修复 "Read Props" 按钮状态栏更新问题

**Generated**: 2026-03-09
**Estimated Complexity**: Low

## Overview
修复 "Read Props" 按钮点击后，左侧状态栏（激活状态）没有更新的问题。
当前代码的 `update_activation_status` 方法只打印日志，没有更新 UI 控件。

## Prerequisites
- 代码已修复 `display_sensor_properties` 弹窗功能
- 需要添加对 `activation_status_var` 和 `activation_status_label` 的引用

## Sprint 1: 添加 UI 引用和修复状态更新
**Goal**: 使 "Read Props" 按钮点击后正确更新左侧状态栏
**Demo/Validation**:
- 连接传感器
- 点击 "Read Props" 按钮
- 验证左侧状态栏显示 "Activated"（绿色）或 "Not Activated"（红色）

### Task 1.1: 添加激活状态 UI 引用
- **Location**: `sensor_calibrator/app/application.py`
- **Description**: 在 `_setup_ui_references` 方法中添加对 `activation_status_var` 和 `activation_status_label` 的引用
- **Dependencies**: None
- **Acceptance Criteria**:
  - `self.activation_status_var` 可以访问 `activation_status` 变量
  - `self.activation_status_label` 可以访问 `activation_status_label` 控件
- **Validation**:
  - 运行程序不报错
  - 打印 `self.activation_status_var` 和 `self.activation_status_label` 不为 None

### Task 1.2: 修复 `update_activation_status` 方法
- **Location**: `sensor_calibrator/app/application.py`
- **Description**: 修改 `update_activation_status` 方法，使其更新 UI 控件而不仅是打印日志
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - 已激活时：设置状态栏文本为 "Activated"，颜色为绿色
  - 未激活时：设置状态栏文本为 "Not Activated"，颜色为红色
  - 同时更新激活按钮状态（已激活则禁用，未激活且可激活则启用）
- **Validation**:
  - 点击 "Read Props" 后左侧状态栏正确显示状态和颜色

## Testing Strategy
1. 启动应用程序
2. 连接串口
3. 点击 "Read Props" 按钮
4. 验证：
   - 弹出属性窗口（已修复）
   - 左侧状态栏更新为 "Activated" 或 "Not Activated"
   - 状态栏颜色为绿色（已激活）或红色（未激活）

## Potential Risks & Gotchas
- `activation_status_label` 控件名可能与实际不符，需确认 `ui_manager.py` 中的命名
- 需要确保 `activation_status_var` 是 `StringVar` 类型

## Rollback Plan
- 保留原始代码备份
- 如出现问题，恢复 `update_activation_status` 方法为仅打印日志的版本
