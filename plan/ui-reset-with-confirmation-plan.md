# UI 清屏与刷新功能实现计划（含确认弹窗）

**生成日期**: 2026-03-16
**预计复杂度**: 低
**关联需求**: 点击 Disconnect/刷新按钮时显示确认弹窗，确认后清屏并初始化UI

---

## 概述

本计划实现带有确认弹窗的UI重置功能：
1. **手动刷新**: 点击 "Reset UI" 按钮 → 显示确认弹窗 → 确认后清屏
2. **自动触发**: 点击 Disconnect 或设备异常断连 → 显示确认弹窗 → 确认后清屏
3. **弹窗内容**: 自定义标题和详细警告信息

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
| **日志区** | **保留** | 不清空，便于问题追溯 |

### 弹窗内容设计

**标题**: `确认重置 UI`

**消息内容**:
```
刷新页面将清空以下数据：
• 所有图表数据
• 实时统计信息
• 校准命令记录
• 传感器激活状态

此操作不可撤销。确定要继续吗？
```

**按钮**: `[确定]` `[取消]`

---

## 前置条件

- Python >= 3.8
- tkinter.messagebox 模块可用
- 已阅读 ui_manager.py, application.py, callbacks.py 代码

---

## Sprint 1: 核心重置功能

**目标**: 实现底层 UI 重置逻辑

**演示/验证**:
- `reset_ui_state()` 方法可正常调用
- 数据缓冲区、图表、统计信息被清空

### Task 1.1: 添加 UI 重置主方法
- **位置**: `sensor_calibrator/app/application.py`
- **描述**: 添加 `reset_ui_state()` 方法，统一重置所有 UI 状态
- **代码实现**:
  ```python
  def reset_ui_state(self):
      """重置UI到初始状态"""
      # 1. 清空数据缓冲区
      if hasattr(self, 'data_processor'):
          self.data_processor.clear_all()
      
      # 2. 清空图表
      if self.chart_manager:
          self.chart_manager.clear_data()
      
      # 3. 重置统计标签显示
      self._reset_statistics_display()
      
      # 4. 重置UI变量
      if self.freq_var:
          self.freq_var.set("0 Hz")
      if self.position_var:
          self.position_var.set("Position: Not calibrating")
      
      # 5. 清空命令区
      if self.cmd_text:
          self.cmd_text.delete(1.0, "end")
      
      # 6. 重置激活状态
      self._reset_activation_display()
      
      # 7. 重置内部状态
      self.packets_received = 0
      self.serial_freq = 0
      self._aky_from_ss13 = None
      
      self.log_message("UI 已重置")
  ```
- **验收标准**:
  - 方法可被正常调用不抛异常
  - 日志输出 "UI 已重置"

### Task 1.2: 添加统计标签重置方法
- **位置**: `sensor_calibrator/app/application.py`
- **描述**: 添加 `_reset_statistics_display()` 私有方法
- **代码实现**:
  ```python
  def _reset_statistics_display(self):
      """重置统计标签显示为初始值"""
      if not self.stats_labels:
          return
      
      # 重置所有轴的统计
      for sensor_key in ['mpu_accel', 'adxl_accel', 'mpu_gyro']:
          for axis in ['x', 'y', 'z']:
              mean_key = f"{sensor_key}_{axis}_mean"
              std_key = f"{sensor_key}_{axis}_std"
              if mean_key in self.stats_labels and self.stats_labels[mean_key]:
                  self.stats_labels[mean_key].set("μ: 0.000")
              if std_key in self.stats_labels and self.stats_labels[std_key]:
                  self.stats_labels[std_key].set("σ: 0.000")
      
      # 重置重力统计
      if 'gravity_mean' in self.stats_labels and self.stats_labels['gravity_mean']:
          self.stats_labels['gravity_mean'].set("Mean: 0.000")
      if 'gravity_std' in self.stats_labels and self.stats_labels['gravity_std']:
          self.stats_labels['gravity_std'].set("Std: 0.000")
  ```
- **验收标准**:
  - 所有统计标签重置为初始值
  - 不会遗漏任何标签

### Task 1.3: 添加激活状态重置方法
- **位置**: `sensor_calibrator/app/application.py`
- **描述**: 添加 `_reset_activation_display()` 私有方法
- **代码实现**:
  ```python
  def _reset_activation_display(self):
      """重置激活状态显示"""
      # 重置变量
      self.sensor_properties = {}
      self.mac_address = None
      self.generated_key = None
      self.sensor_activated = False
      
      # 重置UI显示
      if self.mac_var:
          self.mac_var.set("--")
      if self.key_var:
          self.key_var.set("")
      if self.activation_status_var:
          self.activation_status_var.set("Not Activated")
      if self.activation_status_label:
          self.activation_status_label.config(foreground="red")
  ```
- **验收标准**:
  - MAC显示为 "--"
  - 状态显示为 "Not Activated" 红色
  - 内部状态变量重置

---

## Sprint 2: 确认弹窗功能

**目标**: 实现确认弹窗对话框

**演示/验证**:
- 弹窗样式正确，按钮功能正常

### Task 2.1: 添加确认弹窗方法
- **位置**: `sensor_calibrator/app/application.py`
- **描述**: 添加 `show_reset_confirmation()` 方法显示确认弹窗
- **代码实现**:
  ```python
  def show_reset_confirmation(self, callback=None):
      """
      显示重置确认弹窗
      
      Args:
          callback: 用户点击确定后的回调函数
      
      Returns:
          bool: 用户是否点击了确定
      """
      from tkinter import messagebox
      
      result = messagebox.askokcancel(
          "确认重置 UI",
          "刷新页面将清空以下数据：\n"
          "• 所有图表数据\n"
          "• 实时统计信息\n"
          "• 校准命令记录\n"
          "• 传感器激活状态\n\n"
          "此操作不可撤销。确定要继续吗？",
          icon='warning'
      )
      
      if result and callback:
          callback()
      
      return result
  ```
- **验收标准**:
  - 弹窗标题正确
  - 消息内容格式正确
  - 返回布尔值表示用户选择

### Task 2.2: 添加带确认的重置包装方法
- **位置**: `sensor_calibrator/app/application.py`
- **描述**: 添加 `reset_ui_with_confirmation()` 方法，先弹窗确认再重置
- **代码实现**:
  ```python
  def reset_ui_with_confirmation(self, silent=False):
      """
      带确认弹窗的UI重置
      
      Args:
          silent: 如果为True，不显示确认弹窗直接重置（用于程序内部调用）
      
      Returns:
          bool: 是否执行了重置
      """
      if silent:
          self.reset_ui_state()
          return True
      
      def do_reset():
          self.reset_ui_state()
      
      return self.show_reset_confirmation(do_reset)
  ```
- **验收标准**:
  - 点击确定后执行重置
  - 点击取消不执行任何操作
  - silent模式直接重置不弹窗

---

## Sprint 3: 断开连接触发（带确认）

**目标**: 断开连接时显示确认弹窗

**演示/验证**:
- 点击 Disconnect 后先弹窗，确认后才清屏

### Task 3.1: 修改断开连接回调（带确认）
- **位置**: `sensor_calibrator/app/callbacks.py`
- **描述**: 修改 `disconnect_serial()` 方法，添加确认弹窗
- **依赖**: Sprint 2 完成
- **代码修改**:
  ```python
  def disconnect_serial(self):
      """断开串口连接（带确认弹窗）"""
      # 如果正在读取数据，先停止
      if self.app.is_reading:
          self.stop_data_stream()
      
      # 显示确认弹窗
      if not self.app.reset_ui_with_confirmation():
          # 用户取消，不断开连接
          return
      
      # 用户确认，执行断开
      self.app.serial_manager.disconnect()
      self.app.ser = None
      
      # ... 原有按钮状态更新代码 ...
      if self.app.connect_btn:
          self.app.connect_btn.config(text="Connect")
      # ... 其他按钮状态代码保持不变 ...
      
      self.app._aky_from_ss13 = None
      self.app.log_message("串口已断开连接")
  ```
- **验收标准**:
  - 点击 Disconnect 先显示确认弹窗
  - 点击取消则保持连接状态
  - 点击确定后断开并清屏

### Task 3.2: 处理异常断连（显示提示+重置）
- **位置**: `sensor_calibrator/app/application.py` 的 `_on_connection_state_changed()`
- **描述**: 设备异常断连时显示信息提示框，用户点击确定后重置
- **代码修改**:
  ```python
  def _on_connection_state_changed(self, connected: bool):
      """串口连接状态变化回调"""
      if connected:
          self.ser = self.serial_manager.serial_port
      else:
          # 如果是异常断连（非用户主动点击Disconnect）
          if self.ser is not None:
              self.ser = None
              # 使用 after 确保在主线程显示弹窗
              if self.root:
                  self.root.after(0, self._show_device_disconnected_dialog)
  
  def _show_device_disconnected_dialog(self):
      """显示设备断开连接提示框"""
      from tkinter import messagebox
      
      # 先停止数据流
      if self.is_reading:
          self.is_reading = False
          self.serial_manager.stop_reading()
      
      # 显示信息提示框
      messagebox.showinfo(
          "设备已断开连接",
          "检测到设备已断开连接（USB可能被拔出）。\n\n"
          "点击确定后将重置UI界面。",
          icon='warning'
      )
      
      # 用户点击确定后执行重置
      self.reset_ui_state()
      self.log_message("设备断开连接，UI 已重置")
  ```
- **验收标准**:
  - 异常断连时显示信息提示框
  - 提示框只有"确定"按钮
  - 点击确定后执行清屏
  - 记录日志提示用户

---

## Sprint 4: 刷新按钮（带确认）

**目标**: 添加带确认弹窗的刷新按钮

**演示/验证**:
- 页面上有 "Reset UI" 按钮
- 点击后显示确认弹窗

### Task 4.1: 添加刷新按钮
- **位置**: `sensor_calibrator/ui_manager.py`
- **描述**: 在 Commands 区域底部添加 "Reset UI" 按钮
- **代码修改** (在 `_setup_commands_section` 方法末尾):
  ```python
  # 第四行 - 刷新页面按钮
  row4 = ttk.Frame(cmd_content)
  row4.pack(fill="x", pady=1)
  
  reset_ui_btn = ttk.Button(
      row4,
      text="Reset UI",
      command=self.callbacks.get('reset_ui_with_confirmation', lambda: None),
      width=32,
  )
  reset_ui_btn.pack(side="left", padx=2, expand=True, fill="x")
  self.widgets['reset_ui_btn'] = reset_ui_btn
  ```
- **验收标准**:
  - 按钮显示在 Commands 区域底部
  - 宽度与其他按钮对齐

### Task 4.2: 添加刷新按钮回调
- **位置**: `sensor_calibrator/app/callbacks.py`
- **描述**: 添加 `reset_ui_with_confirmation()` 回调方法
- **代码实现**:
  ```python
  def reset_ui_with_confirmation(self):
      """带确认的刷新页面"""
      # 如果正在读取数据，先停止
      if self.app.is_reading:
          self.stop_data_stream()
      
      # 显示确认弹窗并重置
      self.app.reset_ui_with_confirmation()
  ```
- **验收标准**:
  - 回调正确绑定到按钮
  - 点击按钮显示确认弹窗

### Task 4.3: 注册回调
- **位置**: `sensor_calibrator/app/application.py` 的 `_setup_ui_manager()`
- **描述**: 在 callbacks 字典中添加 `reset_ui_with_confirmation`
- **代码修改**:
  ```python
  callbacks = {
      # ... 原有回调 ...
      'reset_ui_with_confirmation': self.ui_callbacks.reset_ui_with_confirmation,
  }
  ```
- **验收标准**:
  - 回调正确注册
  - 按钮点击能触发回调

---

## Sprint 5: 测试与验证

**目标**: 确保所有功能正常工作

### Task 5.1: 编写单元测试
- **位置**: `tests/test_ui_reset.py`（新建）
- **测试用例**:
  1. `test_reset_ui_clears_all_data` - 验证数据被清空
  2. `test_reset_ui_resets_statistics` - 验证统计重置
  3. `test_reset_ui_resets_activation` - 验证激活状态重置
  4. `test_show_confirmation_dialog` - 验证弹窗显示（mock测试）
- **验收标准**:
  - 所有测试通过

### Task 5.2: 手动测试场景
| 场景 | 操作步骤 | 预期结果 |
|------|----------|----------|
| 正常刷新 | 1. 连接设备<br>2. 开始数据流<br>3. 点击 Reset UI<br>4. 点击确定 | 显示确认弹窗 → 清屏 → 记录日志 |
| 取消刷新 | 1. 点击 Reset UI<br>2. 点击取消 | 弹窗关闭，UI保持不变 |
| 断开连接确认 | 1. 连接设备<br>2. 点击 Disconnect<br>3. 点击确定 | 显示确认弹窗 → 断开 → 清屏 |
| 取消断开 | 1. 点击 Disconnect<br>2. 点击取消 | 弹窗关闭，保持连接 |
| 异常断连 | 1. 连接设备<br>2. 拔掉USB | 显示"设备已断开连接"提示框 → 点击确定 → 清屏 |
| 重复刷新 | 多次点击 Reset UI | 每次都有确认弹窗 |

---

## 潜在风险与缓解策略

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| 弹窗在后台显示 | 高 | 使用 `self.root.lift()` 确保弹窗在前台 |
| 多线程冲突 | 中 | 弹窗在主线程显示，重置操作使用 `root.after()` |
| 取消断开后状态不一致 | 中 | 取消时确保所有状态保持不变 |
| 异常断连检测延迟 | 低 | 依赖 serial_manager 的状态检测机制 |
| 弹窗阻塞主线程 | 中 | 使用 `root.after()` 延迟显示弹窗，避免阻塞 |

---

## 文件修改清单

| 文件路径 | 修改类型 | 修改内容 |
|----------|----------|----------|
| `sensor_calibrator/app/application.py` | 新增 | `reset_ui_state()`, `_reset_statistics_display()`, `_reset_activation_display()`, `show_reset_confirmation()`, `reset_ui_with_confirmation()` |
| `sensor_calibrator/app/callbacks.py` | 修改 | `disconnect_serial()` 添加确认，新增 `reset_ui_with_confirmation()` |
| `sensor_calibrator/ui_manager.py` | 修改 | `_setup_commands_section()` 添加 Reset UI 按钮 |
| `tests/test_ui_reset.py` | 新增 | 单元测试 |

---

## 实施建议

1. **按 Sprint 顺序实施**，每个 Sprint 完成后测试
2. **先实现 Sprint 1-2**（核心功能 + 弹窗），确认弹窗样式符合预期
3. **再实现 Sprint 3-4**（触发逻辑），测试各种场景
4. **最后 Sprint 5**（全面测试）

是否需要我开始 **实施代码修改**？
