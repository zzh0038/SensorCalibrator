# 修复设备断开连接弹窗问题 - V2

## 问题分析

直接拔掉 USB 数据线后弹窗仍然不出现，根本原因是：

1. **USB 热插拔不会立即抛出 SerialException**：当 USB 线被拔出时，`in_waiting` 和 `read()` 不会立即抛出异常，而是可能返回 0 或 hang 住
2. **被动等待异常不可靠**：之前的实现依赖 `SerialException` 被抛出，但这在 USB 热插拔时不可靠
3. **没有主动健康检查**：无法及时检测到连接实际已断开

## 解决方案

### 1. 添加主动连接健康检查机制

**文件**: `sensor_calibrator/serial_manager.py`

- 添加 `_check_connection_health()` 方法：通过尝试访问 `in_waiting` 属性检测连接状态
- 在读取循环中添加定期检查（每 2 秒）
- 如果超过 5 秒没有数据，强制断开连接

### 2. 区分用户主动断开和异常断开

**文件**: `sensor_calibrator/serial_manager.py`

- 添加 `_user_disconnect` 标志
- `disconnect()` 方法设置标志并传递 `user_initiated=True`
- 读取线程异常退出时检查标志，避免误判

### 3. 更新 UI 回调

**文件**: `sensor_calibrator/app/application.py`

- `_on_connection_state_changed()` 接受 `user_initiated` 参数
- 只有异常断开（非用户主动）时才显示弹窗

## 配置参数

**文件**: `sensor_calibrator/config.py`

```python
# 连接健康检查
HEALTH_CHECK_INTERVAL: Final[float] = 2.0  # 健康检查间隔（秒）
NO_DATA_TIMEOUT: Final[float] = 5.0  # 无数据超时（秒）
```

## 工作流程

### 用户主动断开（点击 Disconnect）
```
用户点击 Disconnect
    ↓
显示"确认重置 UI"弹窗
    ↓
用户确认
    ↓
设置 _user_disconnect = True
    ↓
调用 disconnect()
    ↓
触发 update_connection_state(False, user_initiated=True)
    ↓
不显示异常断开弹窗
```

### 设备异常断开（USB 拔出）
```
USB 数据线被拔出
    ↓
读取线程继续运行但无数据
    ↓
超过 2 秒无数据，执行健康检查
    ↓
_health_check() 访问 in_waiting 抛出异常
    ↓
检测到连接断开，break 循环
    ↓
检查 _user_disconnect 为 False
    ↓
触发 update_connection_state(False, user_initiated=False)
    ↓
显示"设备已断开连接"弹窗
    ↓
重置 UI
```

### 无数据超时断开
```
设备停止发送数据（5秒以上）
    ↓
读取循环检测 time_since_last_data > 5s
    ↓
主动 break 循环
    ↓
检查 _user_disconnect 为 False
    ↓
触发 update_connection_state(False, user_initiated=False)
    ↓
显示"设备已断开连接"弹窗
```

## 测试建议

1. **正常断开测试**：
   - 点击 Disconnect 按钮
   - 应显示"确认重置 UI"弹窗
   - 不应显示"设备已断开连接"弹窗

2. **USB 拔出测试**：
   - 连接设备，开始数据流
   - 直接拔掉 USB 数据线
   - 应在 2-5 秒内显示"设备已断开连接"弹窗
   - 点击确定后 UI 重置

3. **设备断电测试**：
   - 连接设备，开始数据流
   - 关闭设备电源
   - 应在 5 秒内显示"设备已断开连接"弹窗

4. **长时间无数据测试**：
   - 连接设备但不发送数据
   - 5 秒后应触发断开弹窗
