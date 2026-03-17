# 修复设备断开连接弹窗时机问题

## 问题分析

### 当前问题
1. **读取线程异常退出时未通知 UI**：
   - 当设备意外断开（USB 拔出）时，`_read_serial_data()` 线程会捕获 `serial.SerialException` 并退出
   - 但此时**没有**调用 `update_connection_state(False)` 回调，UI 层不知道连接已断开
   - 代码在 `serial_manager.py` 第 319-323 行和第 326-330 行只是记录日志并 `break`，没有通知 UI

2. **异常断连判断逻辑问题**：
   - `application.py` 第 567 行通过 `if self.ser is not None` 判断是否为异常断连
   - 但 `SerialManager.disconnect()` 会将 `_ser = None` 后再调用回调
   - 实际上用户主动断开时 `self.ser` 也是 `None`（在回调触发前已被清空）
   - 这个判断逻辑不可靠

3. **连接状态检测滞后**：
   - `SerialManager.is_connected` 是动态检查 `_ser is not None and _ser.is_open`
   - 但 `_ser.is_open` 可能在 USB 拔出后仍然返回 `True` 直到尝试读写
   - 没有主动检测连接健康状态的机制

## 修复方案

### Task 1: 读取线程退出时通知 UI
**文件**: `sensor_calibrator/serial_manager.py`

在 `_read_serial_data()` 线程退出时，如果是非正常退出（连接仍然标记为连接状态），则触发断开连接回调。

```python
# 在 _read_serial_data 方法末尾（第 333-336 行之后）
# 如果因为错误退出且连接仍被标记为已连接，则通知 UI
if self.is_connected:
    self._log_message("Serial connection lost unexpectedly", "ERROR")
    if self.callbacks.get('update_connection_state') is not None:
        self.callbacks['update_connection_state'](False)
```

### Task 2: 添加明确的异常断连标志
**文件**: `sensor_calibrator/serial_manager.py`

添加一个标志区分用户主动断开和设备异常断开：

1. 添加 `_connection_error` 标志
2. 在 `SerialException` 时设置标志
3. 在回调中传递额外信息或添加新的回调

更简单的方式：修改 `update_connection_state` 回调签名，添加 `reason` 参数：
- `"user_disconnect"` - 用户主动断开
- `"connection_error"` - 连接错误（异常断开）

### Task 3: 修复异常断连判断逻辑
**文件**: `sensor_calibrator/app/application.py`

修改 `_on_connection_state_changed` 方法：

```python
def _on_connection_state_changed(self, connected: bool, reason: str = "user_disconnect"):
    """串口连接状态变化回调
    
    Args:
        connected: 是否已连接
        reason: 断开原因 ("user_disconnect" | "connection_error" | "device_unplugged")
    """
    if connected:
        self.ser = self.serial_manager.serial_port
    else:
        self.ser = None
        # 只有异常断连才显示弹窗
        if reason == "connection_error":
            if self.root:
                self.root.after(0, self._show_device_disconnected_dialog)
```

### Task 4: 添加心跳/健康检查机制（可选增强）
**文件**: `sensor_calibrator/serial_manager.py`

添加定期健康检查，检测串口是否实际可用：

```python
def _check_connection_health(self):
    """检查连接健康状态"""
    if self._ser is None:
        return False
    
    try:
        # 尝试获取输入缓冲区字节数，如果失败说明连接已断开
        _ = self._ser.in_waiting
        return True
    except (serial.SerialException, OSError):
        return False
```

### Task 5: 更新回调调用点
**文件**: `sensor_calibrator/serial_manager.py`

修改所有调用 `update_connection_state` 的地方：

1. `connect()` 成功时: `update_connection_state(True)`
2. `disconnect()` 时: `update_connection_state(False, "user_disconnect")`
3. `_read_serial_data()` 异常退出时: `update_connection_state(False, "connection_error")`

## 最小修复方案（推荐）

如果希望最小改动，只修复核心问题：

1. **只修改 `serial_manager.py`**：
   - 在 `_read_serial_data()` 的异常处理中添加 `update_connection_state(False)` 调用
   - 在 `disconnect()` 中添加标记区分主动/被动断开

2. **只修改 `application.py`**：
   - 修改 `_on_connection_state_changed` 接受 `reason` 参数
   - 只有 `reason != "user_disconnect"` 时才显示弹窗

## 实施步骤

1. 修改 `SerialManager.disconnect()` 添加 `reason` 参数
2. 修改 `SerialManager._read_serial_data()` 异常退出时触发回调
3. 修改 `SensorCalibratorApp._on_connection_state_changed()` 接受 reason 参数
4. 测试：
   - 用户点击 Disconnect：不显示弹窗
   - USB 拔出：显示弹窗
   - 设备断电：显示弹窗

## 文件变更

- `sensor_calibrator/serial_manager.py`
- `sensor_calibrator/app/application.py`
