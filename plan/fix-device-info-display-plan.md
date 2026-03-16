# Plan: 修复设备信息显示功能（方案A详细实施计划）

**Generated**: 2026-03-16
**Estimated Complexity**: Low
**Estimated Time**: 30-45 分钟

## Overview

修复 "Send Commands" 后弹窗显示错误信息的问题。当前显示的是 GID/GED 等网络配置字段，但弹窗标题和提示文字都说是 "Calibration Parameters"，造成用户困惑。

本计划将：
1. 修改提示文字，使其准确反映实际功能
2. 添加网络配置字段的显示支持
3. 优化弹窗布局，区分显示不同类型的信息
4. 添加友好的提示信息

## Prerequisites

- 了解当前代码结构
- 熟悉 tkinter 基本操作
- 测试时需要连接实际设备验证

---

## Sprint 1: 修改提示文字和弹窗标题

**Goal**: 使提示信息准确反映实际功能（读取设备信息/网络配置）
**Demo/Validation**: 发送命令后弹窗显示正确的标题和提示

### Task 1.1: 修改 ask_read_properties 方法
- **Location**: `sensor_calibrator/app/callbacks.py`, lines 385-393
- **Description**: 修改弹窗标题和提示文字
- **Dependencies**: 无
- **Changes**:
  ```python
  # 修改前
  def ask_read_properties(self):
      response = messagebox.askyesno(
          "Read Calibration Parameters",
          "All calibration commands have been sent successfully.\n\n"
          "Do you want to read calibration parameters from device?",
      )
  
  # 修改后
  def ask_read_properties(self):
      response = messagebox.askyesno(
          "Read Device Information",
          "All calibration commands have been sent successfully.\n\n"
          "Do you want to read device information to verify the configuration?",
      )
  ```
- **Acceptance Criteria**:
  - 弹窗标题显示 "Read Device Information"
  - 提示文字说明是读取设备信息用于验证配置
- **Validation**:
  - 运行应用，发送命令后检查弹窗文字

---

## Sprint 2: 添加网络配置字段支持

**Goal**: 在 _display_device_info 中添加对 GID/GED 等网络配置字段的支持
**Demo/Validation**: 日志中显示网络配置信息

### Task 2.1: 添加网络配置字段定义
- **Location**: `sensor_calibrator/app/application.py`, after line 1457
- **Description**: 添加网络配置字段字典
- **Dependencies**: Task 1.1 完成
- **Changes**:
  ```python
  # 在网络配置字段后添加
  network_fields = {
      "GID": "Gateway ID",
      "GED": "Gateway Enable",
      "GTP": "Gateway Type",
      "GLV": "Gateway Level",
      "GDT": "Gateway Data Type",
      "GMP": "Gateway Map",
      "GNUM": "Gateway Number",
      "LAT": "Latitude",
      "LON": "Longitude",
  }
  ```

### Task 2.2: 修改 _display_device_info 显示逻辑
- **Location**: `sensor_calibrator/app/application.py`, lines 1459-1479
- **Description**: 分别显示校准参数和网络配置
- **Dependencies**: Task 2.1
- **Changes**:
  ```python
  # 修改日志输出部分
  self.log_message("\n" + "=" * 50)
  self.log_message("DEVICE INFORMATION")
  self.log_message("=" * 50)
  
  # 显示校准参数（如果存在）
  calibration_found = 0
  for key, label in calibration_fields.items():
      if key in sys_info:
          value = sys_info[key]
          if isinstance(value, list):
              value_str = f"[{', '.join(str(v) for v in value)}]"
          else:
              value_str = str(value)
          self.log_message(f"{label}: {value_str}")
          calibration_found += 1
  
  if calibration_found == 0:
      self.log_message("Calibration parameters: Not available in device response")
      self.log_message("(Parameters were sent successfully but cannot be read back)")
  
  # 显示网络配置
  self.log_message("\n--- Network Configuration ---")
  network_found = 0
  for key, label in network_fields.items():
      if key in sys_info:
          value = sys_info[key]
          value_str = str(value)
          self.log_message(f"{label}: {value_str}")
          network_found += 1
  
  if network_found == 0:
      self.log_message("No network configuration found")
  
  self.log_message("=" * 50)
  ```
- **Acceptance Criteria**:
  - 日志标题改为 "DEVICE INFORMATION"
  - 分别显示校准参数和网络配置
  - 如果没有校准参数，显示友好提示
- **Validation**:
  - 运行应用，检查日志输出格式

---

## Sprint 3: 优化弹窗显示

**Goal**: 优化弹窗布局，区分显示校准参数和网络配置
**Demo/Validation**: 弹窗中正确显示设备信息，分区域展示

### Task 3.1: 修改 _show_device_info_dialog 方法签名
- **Location**: `sensor_calibrator/app/application.py`, line 1489
- **Description**: 添加 network_fields 参数
- **Dependencies**: Task 2.2
- **Changes**:
  ```python
  # 修改前
  def _show_device_info_dialog(self, sys_info, calibration_fields):
  
  # 修改后
  def _show_device_info_dialog(self, sys_info, calibration_fields, network_fields=None):
      if network_fields is None:
          network_fields = {}
  ```

### Task 3.2: 修改弹窗标题和内容
- **Location**: `sensor_calibrator/app/application.py`, lines 1494-1558
- **Description**: 修改弹窗标题，添加分区域显示
- **Dependencies**: Task 3.1
- **Changes**:
  ```python
  # 修改窗口标题
  info_window.title("Device Information")
  
  # 修改标题标签
  title_label = ttk.Label(main_frame, text="Device Information", font=("Arial", 14, "bold"))
  
  # 添加说明标签
  note_label = ttk.Label(
      main_frame, 
      text="Note: Calibration parameters were sent to device but may not be readable.",
      font=("Arial", 9, "italic"),
      foreground="gray"
  )
  note_label.pack(pady=(0, 5))
  
  # 修改树形视图列宽
  info_tree.column("#0", width=200, minwidth=150)
  info_tree.column("value", width=300, minwidth=200)
  
  # 修改数据填充逻辑，按类别分组
  inserted_count = 0
  
  # 校准参数组
  calibration_items = []
  for key, label in calibration_fields.items():
      if key in sys_info:
          value = sys_info[key]
          if isinstance(value, list):
              value_str = f"[{', '.join(str(v) for v in value)}]"
          else:
              value_str = str(value)
          calibration_items.append((label, value_str))
          inserted_count += 1
  
  if calibration_items:
      calib_parent = info_tree.insert("", "end", text="📊 Calibration Parameters", values=("",), open=True)
      for label, value_str in calibration_items:
          info_tree.insert(calib_parent, "end", text=label, values=(value_str,))
  
  # 网络配置组
  network_items = []
  for key, label in network_fields.items():
      if key in sys_info:
          value = sys_info[key]
          value_str = str(value)
          network_items.append((label, value_str))
          inserted_count += 1
  
  if network_items:
      network_parent = info_tree.insert("", "end", text="🌐 Network Configuration", values=("",), open=True)
      for label, value_str in network_items:
          info_tree.insert(network_parent, "end", text=label, values=(value_str,))
  
  # 其他字段组
  other_items = []
  known_keys = set(calibration_fields.keys()) | set(network_fields.keys())
  for key, value in sys_info.items():
      if key not in known_keys:
          value_str = str(value)[:50]
          other_items.append((key, value_str))
          inserted_count += 1
  
  if other_items:
      other_parent = info_tree.insert("", "end", text="📋 Other Fields", values=("",), open=False)
      for key, value_str in other_items:
          info_tree.insert(other_parent, "end", text=key, values=(value_str,))
  
  # 修改空数据提示
  if inserted_count == 0:
      info_tree.insert("", "end", text="[No Data]", values=("No device information available",))
  ```

### Task 3.3: 更新 _display_device_info 中的调用
- **Location**: `sensor_calibrator/app/application.py`, line 1483
- **Description**: 更新方法调用，传入 network_fields
- **Dependencies**: Task 3.2
- **Changes**:
  ```python
  # 修改前
  self._show_device_info_dialog(sys_info, calibration_fields)
  
  # 修改后
  self._show_device_info_dialog(sys_info, calibration_fields, network_fields)
  ```
- **Acceptance Criteria**:
  - 弹窗标题改为 "Device Information"
  - 显示分组信息（校准参数、网络配置、其他字段）
  - 添加说明文字
- **Validation**:
  - 运行应用，检查弹窗显示效果

---

## Sprint 4: 添加成功提示

**Goal**: 在发送命令后添加成功提示，让用户知道校准参数已发送
**Demo/Validation**: 发送命令后显示成功提示

### Task 4.1: 修改 send_commands_thread 成功提示
- **Location**: `sensor_calibrator/app/callbacks.py`, lines 286-291
- **Description**: 添加更详细的成功提示
- **Dependencies**: 无
- **Changes**:
  ```python
  # 在发送成功后添加提示
  self.app.root.after(
      0,
      lambda: self.app.log_message("All calibration commands sent successfully!")
  )
  self.app.root.after(
      0,
      lambda: self.app.log_message("Note: Device may not support reading back calibration parameters.")
  )
  ```
- **Acceptance Criteria**:
  - 发送成功后显示明确的提示
  - 提示用户设备可能不支持读取校准参数
- **Validation**:
  - 运行应用，发送命令后检查日志

---

## Testing Strategy

### 单元测试
- 验证 `ask_read_properties` 方法调用正确的应用方法

### 集成测试
1. **测试场景1**: 发送校准命令后点击"Yes"
   - 预期: 弹窗标题为 "Device Information"
   - 预期: 日志显示 "DEVICE INFORMATION" 标题
   - 预期: 显示网络配置字段（GID, GED等）

2. **测试场景2**: 检查弹窗布局
   - 预期: 分组显示（校准参数、网络配置、其他字段）
   - 预期: 有说明文字提示

3. **测试场景3**: 没有数据的情况
   - 预期: 显示 "No device information available"

### 手动验证步骤
1. 启动应用
2. 连接设备
3. 执行完整的 6 位置校准
4. 点击 "Send Commands"
5. 点击弹窗 "Yes"
6. 验证：
   - [ ] 弹窗标题是 "Device Information"
   - [ ] 日志标题是 "DEVICE INFORMATION"
   - [ ] 显示网络配置（GID, GED, LAT, LON等）
   - [ ] 弹窗中有分组显示
   - [ ] 有说明文字提示

---

## Potential Risks & Gotchas

1. **tkinter Treeview 分组显示问题**
   - 风险: 在某些系统上emoji可能显示为方框
   - 缓解: 使用简单的文本前缀如 "[CAL]" 和 "[NET]" 代替emoji

2. **字段名称不一致**
   - 风险: 不同固件版本可能使用不同的字段名
   - 缓解: 保持对未知字段的显示（放在"其他字段"组）

3. **空数据情况**
   - 风险: 设备可能返回空数据
   - 缓解: 已添加空数据处理和提示

4. **向后兼容性**
   - 风险: 修改方法签名可能影响其他调用
   - 检查: 确保 `_show_device_info_dialog` 只在 `_display_device_info` 中被调用

---

## Rollback Plan

如果需要回滚：
1. 恢复 `ask_read_properties` 方法的原始文字
2. 恢复 `_display_device_info` 的日志输出格式
3. 恢复 `_show_device_info_dialog` 的方法签名和内容

所有修改都是局部化的，不会影响核心功能。

---

## Summary

| Sprint | Task | File | Line | Est. Time |
|--------|------|------|------|-----------|
| 1 | 1.1 | callbacks.py | 385-393 | 5 min |
| 2 | 2.1 | application.py | 1458 | 5 min |
| 2 | 2.2 | application.py | 1459-1479 | 10 min |
| 3 | 3.1 | application.py | 1489 | 2 min |
| 3 | 3.2 | application.py | 1494-1558 | 15 min |
| 3 | 3.3 | application.py | 1483 | 2 min |
| 4 | 4.1 | callbacks.py | 286-291 | 5 min |

**Total Estimated Time**: 30-45 分钟
