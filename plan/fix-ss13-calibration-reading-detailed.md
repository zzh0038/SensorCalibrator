# 详细修复计划：SS:13 校准参数读取问题

## 问题诊断

### 当前现象
1. 发送 SS:13 命令后，日志显示 `Using 'params' field with 9 fields`
2. 可用字段是 `['GID', 'GED', 'GTP', 'GLV', 'GDT', 'GMP', 'GNUM', 'LAT', 'LON']`
3. 这些是 **SS:8** 返回的网络配置字段，不是 SS:13 的校准参数字段

### 代码分析
- 代码逻辑已经修改为优先使用 `sys` 字段（已验证）
- 但仍然显示使用 `params` 字段
- 说明 `device_info` 中可能没有 `sys` 字段，或者数据不是来自 SS:13

### 可能原因
1. **串口缓冲区残留**：SS:8 的响应残留在缓冲区，被 SS:13 读取到了
2. **响应解析错误**：读取到的 JSON 不是 SS:13 的响应
3. **固件响应格式问题**：SS:13 实际返回的格式与预期不同
4. **并发问题**：其他线程同时发送了命令导致混淆

---

## 修复步骤

### Step 1: 添加详细调试日志（已完成）
**文件**: `sensor_calibrator/app/application.py`
**修改**: `_display_device_info` 方法

添加了以下调试输出：
- 打印 `device_info` 的所有键
- 打印完整的 `device_info` JSON 内容

**验证**: 重新运行应用，查看日志中 SS:13 的实际响应内容

---

### Step 2: 根据调试结果修复

根据 Step 1 的日志，会有以下几种情况：

#### 情况 A: SS:13 响应中有 `sys` 字段但代码没选到
**现象**: 日志显示 `sys` 键存在，但代码选择了 `params`
**原因**: 代码修改未生效或缓存问题
**修复**:
1. 强制清理所有 Python 缓存
2. 重启应用
3. 如果仍有问题，检查是否有其他 `application.py` 文件被加载

#### 情况 B: SS:13 响应中确实没有 `sys` 字段
**现象**: 日志显示 `sys` 键不存在
**可能原因**:
1. 读取到的是 SS:8 的缓存响应
2. 固件 SS:13 返回的格式不同

**修复 - 清理串口缓冲区（更彻底）**:
```python
def _read_device_info_thread(self):
    """在线程中读取校准参数"""
    original_reading_state = self.is_reading

    try:
        if self.is_reading:
            self.root.after(0, lambda: self.log_message("Stopping data stream..."))
            self.root.after(0, self.stop_data_stream)
            time.sleep(1.0)

        # 彻底清空缓冲区
        if self.serial_manager.serial_port:
            self.serial_manager.serial_port.reset_input_buffer()
            self.serial_manager.serial_port.reset_output_buffer()
            # 多次读取确保清空
            while self.serial_manager.serial_port.in_waiting > 0:
                self.serial_manager.serial_port.read(self.serial_manager.serial_port.in_waiting)
                time.sleep(0.1)
        time.sleep(0.5)

        self.root.after(0, lambda: self.log_message("Sending SS:13 command for calibration params..."))
        self.serial_manager.serial_port.write(b"SS:13\n")
        self.serial_manager.serial_port.flush()
        
        # 等待响应前清空任何残留数据
        time.sleep(0.5)
        while self.serial_manager.serial_port.in_waiting > 0:
            self.serial_manager.serial_port.read(self.serial_manager.serial_port.in_waiting)
        
        time.sleep(1.0)
        # ... 后续代码不变
```

#### 情况 C: SS:13 响应格式完全不同
**现象**: 响应中没有 `sys` 也没有 `params`，或者有其他嵌套结构
**修复**: 根据实际格式调整解析逻辑

---

### Step 3: 验证修复

**验证清单**:
- [ ] 日志显示 `Using 'sys' field with X fields`
- [ ] 可用字段包含 `RACKS`, `RACOF`, `REACKS`, `REACOF`, `VROOF`
- [ ] 弹窗正确显示所有校准参数
- [ ] 校准参数值与设备实际值一致

---

## 立即测试步骤

1. **确保代码已更新**（我已完成修改）

2. **清理缓存并重启**:
   ```bash
   # 清理所有 Python 缓存
   Get-ChildItem -Path "sensor_calibrator" -Recurse -Filter "*.pyc" | Remove-Item -Force
   Get-ChildItem -Path "sensor_calibrator" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
   
   # 重启应用
   python main.py
   ```

3. **执行测试**:
   - 连接设备
   - 点击 "Read Device Info" 按钮
   - 查看日志输出

4. **查看调试日志**:
   你应该看到类似以下的输出：
   ```
   [INFO] DEBUG: Full device_info keys: ['sys', ...]
   [INFO] DEBUG: Full device_info content:
   {
     "sys": {
       "RACKS": [...],
       "RACOF": [...],
       ...
     }
   }
   [INFO] Using 'sys' field with X fields
   ```

5. **如果仍有问题**，请复制完整的日志给我

---

## 备选方案

如果 SS:13 确实无法返回校准参数，备选方案：

### 方案 B: 使用 SS:8 读取（如果固件支持）
修改代码，通过 SS:8 读取校准参数（如果固件在 SS:8 中包含校准参数）

### 方案 C: 本地缓存
校准完成后，将参数保存在本地，不提供从设备读取的功能
（当前代码在发送命令后已经保存了参数）

---

## 当前状态

- ✅ 代码已修改为优先使用 `sys` 字段
- ✅ 添加了详细调试日志
- ⏳ 等待用户测试并查看日志
