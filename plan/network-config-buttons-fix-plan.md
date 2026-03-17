# Plan: Fix Network & Device Config Buttons Not Working

**Generated**: 2026-03-17
**Estimated Complexity**: Low

## Overview

Network & Device Configuration block 中的所有按钮（Set/Read WiFi、Set/Read MQTT、Set/Read OTA、Set Alarm Threshold、Save Config、Restart Sensor）初始状态为 disabled，但串口连接后没有被启用。

根本原因：
1. `enable_config_buttons()` 方法是空实现，只打印日志
2. `connect_serial()` 没有调用 `enable_config_buttons()`

## Prerequisites

- Python 3.8+
- 工作正常的 SensorCalibrator 环境
- 可连接的传感器设备（用于测试）

## Sprint 1: Fix Button Enable Logic ✅ COMPLETED

**Goal**: 修复按钮启用逻辑，确保串口连接后网络配置按钮可用

**Demo/Validation**:
- 连接串口后，Network & Device Configuration 中的所有按钮变为可点击状态
- 断开串口后，按钮恢复 disabled 状态

### Task 1.1: Implement enable_config_buttons() Method ✅ DONE

- **Location**: `sensor_calibrator/app/application.py` (line ~2532)
- **Description**: 将空的 `enable_config_buttons()` 实现为实际启用所有网络配置按钮
- **Dependencies**: None
- **Acceptance Criteria**:
  - ✅ 方法启用以下按钮：
    - WiFi: set_wifi_btn, read_wifi_btn
    - MQTT: set_mqtt_btn, read_mqtt_btn
    - OTA: set_ota_btn, read_ota_btn
    - Alarm: set_alarm_threshold_btn
    - Device: save_config_btn, restart_sensor_btn
  - ✅ 每个按钮启用前检查是否存在（hasattr + 非空检查）
  - ✅ 添加日志记录 "Network & Device config buttons enabled"
- **Validation**:
  - ✅ 代码审查：确认所有按钮都被覆盖
  - ✅ 单元测试：78 个测试全部通过

### Task 1.2: Call enable_config_buttons() on Serial Connect ✅ DONE

- **Location**: `sensor_calibrator/app/callbacks.py` (line ~64)
- **Description**: 在串口连接成功后调用 `enable_config_buttons()`
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - ✅ 在 `connect_serial()` 方法中，串口连接成功后调用 `self.app.enable_config_buttons()`
  - ✅ 确保调用时机在 `self.app.ser` 赋值之后
- **Validation**:
  - ✅ 代码审查：调用位置正确
  - ✅ 单元测试：78 个测试全部通过

### Task 1.3: Disable Buttons on Serial Disconnect ✅ N/A

- **Status**: 无需修改
- **说明**: 检查现有代码发现 `_reset_button_states()` 方法（line ~2591）已经包含禁用所有网络配置按钮的逻辑，断开连接时会自动调用

## Testing Strategy

### 单元测试
- 测试 `enable_config_buttons()` 正确启用所有按钮
- 测试按钮在连接/断开状态转换时的行为

### 集成测试
1. 启动应用，不连接串口
   - 验证 Network & Device Config 按钮为 disabled
2. 连接串口
   - 验证所有 Set/Read 按钮变为 normal 状态
   - 检查日志输出 "Network & Device config buttons enabled"
3. 断开串口
   - 验证按钮恢复 disabled 状态

### 回归测试
- 确保其他按钮（Data Stream、Calibration、Activation 等）不受影响
- 确保读取传感器属性后按钮状态正确（`_extract_network_config` 已有调用）

## Potential Risks & Gotchas

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 按钮名称拼写错误 | 部分按钮无法启用 | 仔细核对 `ui_manager.py` 中的 widget 名称 |
| 按钮引用未绑定 | AttributeError | 使用 `hasattr()` 和空值检查 |
| 与现有启用逻辑冲突 | 按钮状态不一致 | 保持 `enable_config_buttons()` 为唯一启用入口 |
| UI 变量未初始化 | 启动时崩溃 | 确保在 `setup()` 完成后调用 |

## Rollback Plan

如果修复导致问题：

1. 恢复 `enable_config_buttons()` 为空实现：
   ```python
   def enable_config_buttons(self):
       """启用配置按钮"""
       self.log_message("Config buttons enabled")
   ```

2. 移除 `connect_serial()` 中的调用

3. 用户临时解决方案：
   - 手动点击 "Read User Info" 按钮读取传感器属性后，按钮会被启用（通过 `_extract_network_config` 中的调用）

## Files to Modify

1. `sensor_calibrator/app/application.py`
   - Line ~2532: `enable_config_buttons()` 方法

2. `sensor_calibrator/app/callbacks.py`
   - Line ~48: `connect_serial()` 方法
   - Line ~64: `disconnect_serial()` 方法（可选，增强一致性）

## Estimated Effort

- Task 1.1: 15 分钟
- Task 1.2: 5 分钟
- Task 1.3: 10 分钟
- 测试验证: 20 分钟
- **总计**: ~50 分钟
