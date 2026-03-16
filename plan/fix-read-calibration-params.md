# 修复读取校准参数功能的计划

## 问题分析

用户点击 "Send Commands" 后，弹窗询问是否读取校准参数。点击后显示的是 GID、GED 等传感器属性字段，而不是 RACKS、RACOF 等校准参数字段。

### 根本原因

1. **代码逻辑问题**：`ask_read_properties()` 调用的是 `read_device_info()`，而 `read_device_info()` 发送 SS:13 命令
2. **固件响应问题**：SS:13 命令返回的是传感器属性/网络配置（GID、GED 等），而不是校准参数
3. **缺少专用命令**：目前没有一个专用的命令来获取校准参数（RACKS、RACOF、REACKS、REACOF、VROOF、GROOF）

### 当前代码流程

```
send_all_commands() -> ask_read_properties() -> read_device_info() -> SS:13
                                                          |
                                                          v
                                              _display_device_info()
                                                          |
                                                          v
                                              期望: RACKS/RACOF 等
                                              实际: GID/GED 等
```

## 修改方案

### 方案 A: 修改 SS:13 命令的期望值（推荐）

由于 SS:13 实际上返回的是传感器属性，应该修改 `_display_device_info` 方法，使其：
1. 显示正确的字段（GID、GED 等网络配置）
2. 弹窗标题改为 "Device Info" 而不是 "Calibration Parameters"

### 方案 B: 实现真正的校准参数读取（需要固件支持）

如果固件支持，可以：
1. 发送 SS:13 命令获取校准参数
2. 固件需要返回包含 RACKS、RACOF 等字段的 JSON

### 方案 C: 添加新命令读取校准参数

如果固件有专门的命令（如 SS:14 或 GET:CAL）来获取校准参数：
1. 实现新的命令发送方法
2. 解析返回的校准参数

## 实施步骤

### 步骤 1: 修复弹窗提示信息

修改 `ask_read_properties` 中的提示文字，使其更准确：
- 当前："Do you want to read calibration parameters from device?"
- 建议："Do you want to read device information to verify the configuration?"

### 步骤 2: 修复显示方法

修改 `_display_device_info`：
1. 添加对 GID、GED 等网络配置字段的支持
2. 区分显示 "Network Configuration" 和 "Calibration Parameters"
3. 如果没有找到校准参数，给出明确提示

### 步骤 3: 添加专门的校准参数读取方法（可选）

如果固件支持，实现真正的校准参数读取：
1. 确定固件命令（如 SS:14 或 GET:CAL）
2. 实现 `_read_calibration_params_thread` 方法
3. 修改回调调用链

## 代码修改位置

1. `sensor_calibrator/app/callbacks.py`
   - `ask_read_properties()` - 修改提示文字

2. `sensor_calibrator/app/application.py`
   - `_display_device_info()` - 添加网络配置字段支持
   - `_show_device_info_dialog()` - 优化显示
   - `_read_device_info_thread()` - 修复或替换
   - `read_calibration_params()` - 实现真正的读取逻辑

## 固件要求

要真正实现校准参数读取功能，固件需要：
1. 支持返回校准参数的专用命令
2. 返回格式示例：
   ```json
   {
     "sys": {
       "RACKS": [0.98, 0.99, 0.97],
       "RACOF": [0.5, -0.1, -1.2],
       "REACKS": [0.98, 0.99, 1.0],
       "REACOF": [0.1, -0.2, -0.5],
       "VROOF": [-0.07, 0.02, -0.01]
     }
   }
   ```

## 建议

鉴于当前情况，我建议：
1. **短期修复**：修改显示逻辑，正确显示网络配置信息，并添加提示说明校准参数需要通过其他方式验证
2. **长期方案**：与固件团队协调，实现专门的校准参数读取命令
