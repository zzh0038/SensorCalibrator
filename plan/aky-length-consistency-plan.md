# Plan: AKY 密钥长度一致性修复

**Generated**: 2026-03-13
**Estimated Complexity**: Low
**Goal**: 统一 AKY 密钥长度为 7 位（`generated_key[5:12]`），确保激活验证与发送逻辑一致

---

## Overview

当前代码存在 AKY 密钥长度不一致的问题：
- `activation_workflow.py` 使用 `KEY_FRAGMENT_LENGTH = 16`（16位）
- `application.py` 验证时使用 `generated_key[5:12]`（7位）

固件 SS:13 返回的 AKY 是 16 位十六进制字符串，但期望的密钥片段是 7 位。本计划将统一修改为 7 位方案（`[5:12]` 切片）。

---

## Prerequisites

- Python 3.8+
- 项目环境已配置（`.venv` 已激活）
- 固件 SS:13 返回格式确认（当前返回16位 AKY）
- 测试用 MAC 地址和对应的期望 AKY

---

## Sprint 1: 统一 KEY_FRAGMENT_LENGTH 常量

**Goal**: 将 `KEY_FRAGMENT_LENGTH` 从 16 改为 7，并调整切片逻辑

**Demo/Validation**:
- 运行 `python -c "from sensor_calibrator.activation_workflow import ActivationWorkflow; print(ActivationWorkflow.KEY_FRAGMENT_LENGTH)"` 应输出 7
- 检查 `key_fragment` 属性返回正确的 7 位切片

### Task 1.1: 修改 activation_workflow.py 中的 KEY_FRAGMENT_LENGTH

- **Location**: `sensor_calibrator/activation_workflow.py`
- **Line**: 第 68 行
- **Description**: 
  1. 将 `KEY_FRAGMENT_LENGTH: int = 16` 改为 `KEY_FRAGMENT_LENGTH: int = 7`
  2. 将 `key_fragment` 属性（第 71-75 行）的切片从 `[:self.KEY_FRAGMENT_LENGTH]` 改为 `[5:12]`
- **Dependencies**: 无
- **Acceptance Criteria**:
  - `KEY_FRAGMENT_LENGTH = 7`
  - `key_fragment` 属性返回 `generated_key[5:12]`
- **Validation**:
  ```python
  from sensor_calibrator.activation_workflow import ActivationWorkflow
  assert ActivationWorkflow.KEY_FRAGMENT_LENGTH == 7
  
  wf = ActivationWorkflow({})
  wf._generated_key = "0123456789abcdef" * 4  # 64位测试密钥
  assert wf.key_fragment == "5678901"  # [5:12]
  ```

### Task 1.2: 修改 verify_key 方法中的切片逻辑

- **Location**: `sensor_calibrator/activation_workflow.py`
- **Line**: 第 187 行
- **Description**: 
  将 `expected_fragment = expected_key[:self.KEY_FRAGMENT_LENGTH]` 改为 `expected_fragment = expected_key[5:12]`
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - 验证时使用 `[5:12]` 切片
- **Validation**:
  ```python
  # 测试验证逻辑
  wf = ActivationWorkflow({})
  mac = "AA:BB:CC:DD:EE:FF"
  full_key = wf.generate_key_from_mac(mac)
  fragment = full_key[5:12]
  assert wf.verify_key(fragment, mac) is True
  ```

### Task 1.3: 修改 _activate_sensor_thread 方法中的切片逻辑

- **Location**: `sensor_calibrator/activation_workflow.py`
- **Line**: 第 319 行
- **Description**: 
  将 `key_fragment = generated_key[:self.KEY_FRAGMENT_LENGTH]` 改为 `key_fragment = generated_key[5:12]`
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - 发送激活命令时使用 `[5:12]` 切片
- **Validation**:
  - 代码审查确认切片正确

---

## Sprint 2: 修复 application.py 中的验证逻辑

**Goal**: 确保 application.py 中的验证逻辑与 activation_workflow.py 一致

**Demo/Validation**:
- 运行 `test_integration.py` 中的激活相关测试
- 手动验证 `_try_update_activation_status` 方法逻辑正确

### Task 2.1: 统一 _try_update_activation_status 中的切片逻辑

- **Location**: `sensor_calibrator/app/application.py`
- **Line**: 第 1728 行
- **Description**: 
  确认 `expected_key = self.generated_key[5:12]` 保持不变，但移除长度检查中的硬编码 12
- **Current Code**:
  ```python
  if not self.generated_key or len(self.generated_key) < 12:
  ```
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - 长度检查与 `KEY_FRAGMENT_LENGTH` 一致（至少12位才能取[5:12]）
  - 使用 `[5:12]` 切片获取期望的 7 位 AKY
- **Validation**:
  - 代码审查确认逻辑正确
  - 测试边界情况（密钥长度小于12的情况）

### Task 2.2: 更新 UI 显示逻辑

- **Location**: `sensor_calibrator/app/application.py`
- **Line**: 第 1668 行
- **Description**: 
  将 `self.generated_key[:16]` 改为 `self.generated_key[5:12]` 以显示正确的密钥片段
- **Current Code**:
  ```python
  key_display = self.generated_key[:16] + "..."
  ```
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - UI 显示 7 位密钥片段
- **Validation**:
  - 运行应用检查 UI 显示正确

### Task 2.3: 更新 _check_activation_status 方法

- **Location**: `sensor_calibrator/app/application.py`
- **Line**: 第 1766-1768 行
- **Description**: 
  确认该方法使用 `[5:12]` 切片，与 `activation_workflow.py` 一致
- **Current Code**:
  ```python
  if self.generated_key and len(self.generated_key) >= 12:
      expected_key = self.generated_key[5:12]
  ```
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - 使用 `[5:12]` 切片
- **Validation**:
  - 代码审查

---

## Sprint 3: 处理固件返回 16 位 AKY 的适配

**Goal**: 修改代码以正确处理固件返回的 16 位 AKY（取前 7 位或后 7 位进行比对）

**Demo/Validation**:
- 模拟测试：固件返回 16 位 AKY，代码正确提取 7 位进行验证

### Task 3.1: 修改 _save_aky_from_ss13 或 _try_update_activation_status 适配 16 位 AKY

- **Location**: `sensor_calibrator/app/application.py`
- **Line**: 第 1697-1751 行（_save_aky_from_ss13 和 _try_update_activation_status）
- **Description**: 
  固件返回 16 位 AKY，但期望比较 7 位。有两种方案：
  
  **方案 A**（推荐）：假设固件的 16 位 AKY = `generated_key[:16]`，提取固件返回的 `[5:12]` 与期望比较
  
  **方案 B**：如果固件的 16 位 AKY 已经是一个随机值，需要确定取前7位还是后7位
  
  根据日志 `AKY='5645101b7b08c868'`，固件返回的是 16 位十六进制。
  需要确认固件如何生成这 16 位，然后提取正确的 7 位。
  
  如果固件直接存储的是 `generated_key[:16]`，则代码应：
  ```python
  aky_from_device = device_info["sys"]["AKY"]  # 16位
  aky_to_compare = aky_from_device[5:12]  # 取第5-12位（7位）
  ```
- **Dependencies**: Sprint 2 完成
- **Acceptance Criteria**:
  - 正确处理固件返回的 16 位 AKY
  - 提取正确的 7 位进行验证
- **Validation**:
  ```python
  # 模拟测试
  generated_key = "0123456789abcdef" * 4
  device_aky = generated_key[:16]  # 模拟固件返回
  extracted_aky = device_aky[5:12]  # 提取7位
  expected_aky = generated_key[5:12]
  assert extracted_aky == expected_aky
  ```

### Task 3.2: 添加调试日志（可选）

- **Location**: `sensor_calibrator/app/application.py`
- **Description**: 
  添加更详细的调试日志，显示固件返回的完整 AKY 和提取的片段
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - 日志显示完整的 16 位 AKY
  - 日志显示提取的 7 位片段
- **Validation**:
  - 运行应用查看日志输出

---

## Sprint 4: 更新测试文件

**Goal**: 确保测试文件与新的 7 位 AKY 逻辑一致

**Demo/Validation**:
- 运行 `python -m pytest tests/test_commands.py -v` 通过

### Task 4.1: 更新 test_commands.py 中的测试

- **Location**: `tests/test_commands.py`
- **Line**: 第 191 行
- **Description**: 
  将 `full_key[:16]` 改为 `full_key[5:12]`
- **Current Code**:
  ```python
  key_fragment = full_key[:16]  # 16 characters (64-bit key space)
  ```
- **Dependencies**: Sprint 1-3 完成
- **Acceptance Criteria**:
  - 测试使用 `[5:12]` 切片
- **Validation**:
  ```bash
  python -m pytest tests/test_commands.py -v
  ```

### Task 4.2: 运行所有相关测试

- **Location**: `tests/`
- **Description**: 
  运行所有与激活相关的测试
- **Dependencies**: Task 4.1
- **Acceptance Criteria**:
  - 所有测试通过
- **Validation**:
  ```bash
  python -m pytest tests/ -v -k "activation or key or AKY"
  ```

---

## Testing Strategy

### 单元测试

1. **测试密钥生成**：验证 `generate_key_from_mac` 返回 64 位十六进制字符串
2. **测试密钥切片**：验证 `key_fragment` 属性返回正确的 7 位切片 `[5:12]`
3. **测试密钥验证**：验证 `verify_key` 方法正确处理 7 位密钥

### 集成测试

1. **模拟固件响应**：
   ```python
   # 模拟 SS:13 返回的 16 位 AKY
   mock_device_response = {
       "sys": {
           "AKY": "5645101b7b08c868"  # 16位
       }
   }
   ```

2. **验证提取逻辑**：
   - 从 16 位中提取 `[5:12]` 位
   - 与生成的 `generated_key[5:12]` 比较

### 手动测试步骤

1. 连接传感器
2. 读取 User Info（获取 MAC）
3. 读取 Calibration Params（获取 16 位 AKY）
4. 验证激活状态显示正确
5. 发送激活命令确认使用 7 位密钥

---

## Potential Risks & Gotchas

### 风险 1：固件 AKY 格式不明确
**问题**：固件返回的 16 位 AKY 可能不是 `generated_key[:16]`，而是其他格式。
**缓解**：
- 添加详细调试日志
- 与固件开发者确认 16 位 AKY 的生成逻辑
- 准备备用方案（取前7位或后7位）

### 风险 2：切片越界
**问题**：如果 `generated_key` 长度小于 12，`[5:12]` 切片会出错。
**缓解**：
- 保持现有的长度检查：`len(self.generated_key) >= 12`
- 添加边界测试

### 风险 3：多处硬编码切片
**问题**：`[5:12]` 在多处出现，未来修改容易遗漏。
**缓解**：
- 考虑添加常量 `KEY_FRAGMENT_START = 5` 和 `KEY_FRAGMENT_END = 12`
- 或使用 `KEY_FRAGMENT_SLICE = slice(5, 12)`

### 风险 4：与旧版本固件不兼容
**问题**：如果固件版本不同，AKY 格式可能不同。
**缓解**：
- 在代码中添加版本检测逻辑
- 支持多种 AKY 格式（自适应长度）

---

## Rollback Plan

如果需要回滚：

1. **Git 回滚**：
   ```bash
   git checkout HEAD -- sensor_calibrator/activation_workflow.py
   git checkout HEAD -- sensor_calibrator/app/application.py
   git checkout HEAD -- tests/test_commands.py
   ```

2. **手动回滚**：
   - 将 `KEY_FRAGMENT_LENGTH` 改回 16
   - 将所有 `[5:12]` 切片改回 `[:16]`

3. **验证回滚**：
   ```bash
   python -m pytest tests/ -v
   ```

---

## Implementation Checklist

- [ ] Task 1.1: 修改 KEY_FRAGMENT_LENGTH = 7 和 key_fragment 属性
- [ ] Task 1.2: 修改 verify_key 方法切片
- [ ] Task 1.3: 修改 _activate_sensor_thread 方法切片
- [ ] Task 2.1: 确认 _try_update_activation_status 切片逻辑
- [ ] Task 2.2: 修改 UI 显示切片
- [ ] Task 2.3: 确认 _check_activation_status 切片逻辑
- [ ] Task 3.1: 实现固件 16 位 AKY 适配逻辑
- [ ] Task 3.2: 添加调试日志（可选）
- [ ] Task 4.1: 更新 test_commands.py
- [ ] Task 4.2: 运行所有测试
- [ ] 手动测试验证

---

## Notes

- **关键变更点汇总**：
  1. `activation_workflow.py:68` - `KEY_FRAGMENT_LENGTH = 7`
  2. `activation_workflow.py:74` - `key_fragment` 属性切片 `[5:12]`
  3. `activation_workflow.py:187` - `verify_key` 方法切片 `[5:12]`
  4. `activation_workflow.py:319` - `_activate_sensor_thread` 切片 `[5:12]`
  5. `application.py:1668` - UI 显示切片 `[5:12]`
  6. `application.py:1738-1740` - 固件 16 位 AKY 适配逻辑
  7. `test_commands.py:191` - 测试切片 `[5:12]`
