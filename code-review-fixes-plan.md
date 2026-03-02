# Plan: Code Review Fixes

**Generated**: 2026-03-02
**Estimated Complexity**: Low

## Overview
根据 Code Review 发现的问题，修复代码中的错误、不一致性和潜在 bug。主要涉及：
1. 修复属性名大小写不匹配问题（高优先级）
2. 修复不存在的控件引用（高优先级）
3. 修正错误注释和命名
4. 统一代码风格

## Prerequisites
- 现有测试套件通过
- Python 环境已配置
- 代码备份或版本控制

---

## Sprint 1: 修复高优先级 Bug
**Goal**: 修复会导致功能失效的属性名错误和控件引用错误
**Demo/Validation**:
- 运行测试套件确保全部通过
- 验证 OTA 配置按钮状态可以正常切换
- 验证串口断开时按钮状态正确更新

### Task 1.1: 修复 `set_OTA_btn` 属性名大小写不匹配
- **Location**: `StableSensorCalibrator.py`
- **Description**: 
  - UIManager 中定义的是 `set_ota_btn`（小写）
  - StableSensorCalibrator 中使用的是 `set_OTA_btn`（大写）
  - 需要统一为小写 `set_ota_btn`
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 所有 `set_OTA_btn` 引用改为 `set_ota_btn`
  - `read_OTA_btn` 引用改为 `read_ota_btn`
- **Validation**:
  - 搜索确认没有大写引用残留
  - 运行测试 `python tests/test_integration.py`

**具体修改位置**：
1. Line ~350: `self.set_OTA_btn` → `self.set_ota_btn`
2. Line ~354: `self.set_OTA_btn` → `self.set_ota_btn`
3. Line ~859: `set_OTA_btn` → `set_ota_btn`
4. Line ~861: `set_OTA_btn` → `set_ota_btn`
5. Line ~860: `read_OTA_btn` → `read_ota_btn`
6. Line ~862: `read_OTA_btn` → `read_ota_btn`

### Task 1.2: 修复 `read_btn` 引用错误
- **Location**: `StableSensorCalibrator.py`
- **Description**: 
  - `_setup_ui_references()` 中引用了 `read_btn`
  - 但 UIManager 中定义的是 `read_props_btn`
  - 需要统一为 `read_props_btn`
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 将 `self.read_btn` 改为 `self.read_props_btn`
- **Validation**:
  - 确认没有 `read_btn` 引用残留
  - 运行测试

**具体修改位置**：
- Line ~323: `self.read_btn = self.ui_manager.get_widget('read_btn')` → `self.read_props_btn`

### Task 1.3: 修复 `disconnect_serial` 中引用问题
- **Location**: `StableSensorCalibrator.py`
- **Description**: 
  - `disconnect_serial` 方法引用了 `self.read_btn`，应该是 `self.read_props_btn`
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - 修复引用错误
- **Validation**:
  - 代码审查确认

---

## Sprint 2: 修正注释和文档
**Goal**: 修复错误的注释和文档字符串
**Demo/Validation**:
- 代码审查确认注释与功能匹配

### Task 2.1: 修正 `set_OTA_config` 方法的文档字符串
- **Location**: `StableSensorCalibrator.py` Line ~566
- **Description**: 
  - 当前注释是 `"""设置MQTT配置"""`
  - 应该改为 `"""设置OTA配置"""`
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 文档字符串与功能匹配
- **Validation**:
  - 代码审查

### Task 2.2: 统一方法命名风格
- **Location**: `StableSensorCalibrator.py`
- **Description**: 
  - `set_OTA_config` 应该改为 `set_ota_config`（小写）
  - `read_OTA_config` 应该改为 `read_ota_config`（小写）
  - 同步更新所有调用点
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - 方法名符合 Python 命名规范（snake_case，全小写）
  - 所有调用点已更新
- **Validation**:
  - 运行测试
  - 搜索确认没有大写方法名残留

**需要修改的位置**：
1. 方法定义：
   - `def set_OTA_config` → `def set_ota_config`
   - `def read_OTA_config` → `def read_ota_config`
2. 回调函数字典（Line ~225-226）：
   - `'set_OTA_config'` → `'set_ota_config'`
   - `'read_OTA_config'` → `'read_ota_config'`
3. UIManager 中的回调引用：
   - 检查 `ui_manager.py` Line ~619, 628

---

## Sprint 3: 代码风格统一
**Goal**: 统一硬编码值，减少 magic numbers
**Demo/Validation**:
- 代码审查确认无硬编码问题
- 测试通过

### Task 3.1: 统一图表 Y 轴 padding 配置
- **Location**: `sensor_calibrator/chart_manager.py`
- **Description**: 
  - Line ~462-463, 482-483 使用硬编码值 `-2` 和 `+2`
  - 应该使用 `Config.CHART_Y_PADDING` 或其他配置常量
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 移除硬编码值
  - 使用配置常量替代
- **Validation**:
  - 代码审查
  - 运行测试

### Task 3.2: 移除重复赋值
- **Location**: `StableSensorCalibrator.py` Line ~1078-1080
- **Description**: 
  - `self.is_reading = False` 重复赋值
  - 移除重复行
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 移除重复代码
- **Validation**:
  - 代码审查

### Task 3.3: 优化导入顺序
- **Location**: `data_pipeline.py` Line ~148
- **Description**: 
  - `import queue` 是局部导入，移到文件顶部
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 导入语句位于文件顶部
- **Validation**:
  - 代码审查

---

## Sprint 4: 可选改进
**Goal**: 提升代码质量（可选，视时间而定）
**Demo/Validation**:
- 类型检查工具通过（如有配置）

### Task 4.1: 补充类型注解
- **Location**: `StableSensorCalibrator.py`
- **Description**: 
  - 为主要方法添加类型注解
  - 优先处理公共 API 方法
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 关键方法有类型注解
- **Validation**:
  - 代码审查

### Task 4.2: 收紧异常捕获范围
- **Location**: `serial_manager.py` Line ~72
- **Description**: 
  - `except Exception` 改为 `except serial.SerialException`
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 只捕获预期的异常类型
- **Validation**:
  - 代码审查
  - 运行测试

---

## Testing Strategy

### 每 Sprint 验证
1. **单元测试**: `python tests/test_integration.py`
2. **冒烟测试**: 确认所有模块可导入
3. **代码审查**: 检查修改点

### 最终验证
- [ ] 所有测试通过
- [ ] 代码审查无问题
- [ ] 无属性名大小写不匹配问题
- [ ] 无不存在的控件引用

---

## Potential Risks & Gotchas

### 风险 1: 属性名替换遗漏
**问题**: `set_OTA_btn` 替换可能遗漏某些引用
**缓解**: 
- 使用全局搜索（大小写敏感）确认
- 搜索关键词：`OTA_btn`、`set_OTA`

### 风险 2: 方法重命名影响回调
**问题**: `set_OTA_config` 重命名后，回调字典需要同步更新
**缓解**:
- 同时检查 UIManager 中的回调绑定
- 搜索所有 `'set_OTA'` 字符串引用

### 风险 3: 串口相关功能回退
**问题**: 修复可能意外影响串口通信功能
**缓解**:
- 保持 `SerialManager` 模块不变
- 仅修改 UI 层面的引用

### 风险 4: 大小写敏感文件系统
**问题**: Windows 不区分大小写，但 Linux/Mac 区分
**缓解**:
- 确保所有引用统一为小写
- 在大小写敏感的环境中测试（如有条件）

---

## Rollback Plan

如果需要回滚：
1. 使用 git 回滚到修改前版本：`git checkout -- <files>`
2. 或从备份恢复文件

---

## 实施检查清单

- [ ] Sprint 1: 高优先级 Bug 修复
  - [ ] Task 1.1: 修复 `set_OTA_btn` 大小写
  - [ ] Task 1.2: 修复 `read_btn` 引用
  - [ ] Task 1.3: 修复 `disconnect_serial` 引用
- [ ] Sprint 2: 注释和文档修正
  - [ ] Task 2.1: 修正 docstring
  - [ ] Task 2.2: 统一方法命名
- [ ] Sprint 3: 代码风格统一
  - [ ] Task 3.1: 统一 Y 轴 padding
  - [ ] Task 3.2: 移除重复赋值
  - [ ] Task 3.3: 优化导入顺序
- [ ] Sprint 4: 可选改进（可选）
  - [ ] Task 4.1: 类型注解
  - [ ] Task 4.2: 收紧异常捕获
- [ ] 最终验证
  - [ ] 所有测试通过
  - [ ] 代码审查完成
