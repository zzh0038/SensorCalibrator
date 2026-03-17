# 修复计划：Reset UI 和 USB 拔出时重置 Connect 按钮状态

## 问题分析

当前代码中，Connect 按钮的状态管理不一致：

| 场景 | 当前行为 | 问题 |
|------|---------|------|
| 点击 **Disconnect** | `disconnect_serial()` 手动设置按钮为 "Connect" | ✅ 正常 |
| 点击 **Reset UI** | 只调用 `reset_ui_state()`，不处理 Connect 按钮 | ⚠️ 按钮状态未重置 |
| **USB 拔出** | 调用 `reset_ui_state()`，但不处理 Connect 按钮 | ❌ 按钮仍显示 "Disconnect"，但连接已断 |

### 根本原因
- `reset_ui_state()` 方法没有处理 Connect 按钮状态
- USB 拔出时，连接已断开，但按钮仍显示 "Disconnect"，造成状态不一致

## 解决方案

将 Connect 按钮状态重置逻辑统一到 `reset_ui_state()` 方法中：
1. 添加 `connect_btn` 状态重置
2. 根据当前连接状态设置正确的按钮文本
3. 移除 `disconnect_serial()` 中的重复逻辑

## 任务列表

### Task 1: 修改 `reset_ui_state()` 方法
**文件**: `sensor_calibrator/app/application.py`

在 `reset_ui_state()` 方法中添加 Connect 按钮状态重置：
```python
def reset_ui_state(self):
    # ... 现有代码 ...
    
    # 新增：重置 Connect 按钮状态
    if self.connect_btn:
        if self.serial_manager.is_connected:
            self.connect_btn.config(text="Disconnect")
        else:
            self.connect_btn.config(text="Connect")
    
    # ... 现有代码 ...
```

### Task 2: 修改 `disconnect_serial()` 方法
**文件**: `sensor_calibrator/app/callbacks.py`

移除手动设置 Connect 按钮的代码（因为 `reset_ui_state()` 已经处理）：
```python
def disconnect_serial(self):
    # ... 现有代码 ...
    
    # 移除以下代码（已在 reset_ui_state 中处理）：
    # if self.app.connect_btn:
    #     self.app.connect_btn.config(text="Connect")
    
    # ... 保留其他按钮的重置 ...
```

### Task 3: 修改 `_show_device_disconnected_dialog()` 方法
**文件**: `sensor_calibrator/app/application.py`

确保断开连接后调用 `reset_ui_state()`：
```python
def _show_device_disconnected_dialog(self):
    # ... 停止数据流 ...
    
    # 确保串口状态已断开
    self.serial_manager._is_connected = False
    self.serial_manager._ser = None
    
    # 显示弹窗
    # ...
    
    # 重置 UI（包含 Connect 按钮）
    self.reset_ui_state()
```

### Task 4: 更新测试
**文件**: `tests/test_ui_reset.py`

添加测试验证 Connect 按钮状态重置：
```python
def test_reset_ui_resets_connect_button(self, mocker):
    """测试重置UI时重置Connect按钮"""
    # 模拟已连接状态
    mock_app.serial_manager.is_connected = True
    mock_app.connect_btn = mocker.MagicMock()
    
    SensorCalibratorApp.reset_ui_state(mock_app)
    
    # 验证按钮设置为 "Disconnect"
    mock_app.connect_btn.config.assert_called_with(text="Disconnect")
```

## 验证清单

- [ ] 点击 Reset UI 后，Connect 按钮状态正确
- [ ] USB 拔出后，Connect 按钮变为 "Connect"
- [ ] 点击 Disconnect 后，Connect 按钮变为 "Connect"
- [ ] 正常连接后，Connect 按钮变为 "Disconnect"
- [ ] 所有现有测试通过

## 注意事项

1. 需要确保 `reset_ui_state()` 能够访问 `serial_manager.is_connected` 状态
2. USB 拔出时需要先更新 `serial_manager` 的连接状态，再调用 `reset_ui_state()`
3. 保持向后兼容，不影响其他按钮的重置逻辑
