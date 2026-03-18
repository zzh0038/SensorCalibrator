# Plan: Code Cleanup for SensorCalibrator

**Generated**: 2026-03-11
**Estimated Complexity**: Low

## Overview

清理代码库中的死代码和冗余代码，包括：
1. 移除重复的 `pass` 语句
2. 清理冗余的 import 语句
3. 移除未调用的死代码方法

## Sprint 1: Critical Fixes (High Priority)

**Goal**: 修复影响代码质量的明显问题

### Task 1.1: 移除 serial_manager.py 重复的 pass 语句
- **Location**: `sensor_calibrator/serial_manager.py`, lines 539-541
- **Description**: 移除连续重复的两个 `pass` 语句（死代码）
- **Current Code**:
  ```python
  except Exception as e:
      pass  # line 539
      pass  # line 541 (重复)
  ```
- **Fix**: 删除其中一个 `pass` 语句
- **Validation**: 运行 `python -m py_compile sensor_calibrator/serial_manager.py` 验证语法正确

### Task 1.2: 清理 application.py 冗余的 import
- **Location**: `sensor_calibrator/app/application.py`, line 1189
- **Description**: 方法内冗余导入 `json` 和使用 `__import__('datetime')` 
- **Current Code**:
  ```python
  def auto_save_properties(self):
      import json  # 冗余，顶部已导入
      save_data = {
          "timestamp": __import__('datetime').datetime.now().isoformat(),  # 应该用顶部的 datetime
  ```
- **Fix**: 
  1. 删除 line 1189 的 `import json`
  2. 将 `__import__('datetime').datetime.now()` 改为 `datetime.now()`
- **Validation**: 运行 `python -m py_compile sensor_calibrator/app/application.py`

## Sprint 2: Dead Code Removal (Medium Priority)

**Goal**: 移除未被调用的死代码方法

### Task 2.1: 移除 ui_manager.py 死代码方法
- **Location**: `sensor_calibrator/ui_manager.py`
- **Description**: 删除三个已注释为"不再被调用"的旧方法
- **Methods to Remove**:
  1. `_setup_wifi_section` (starts at line 817)
  2. `_setup_mqtt_section` (starts at line 879)  
  3. `_setup_ota_section` (starts at line 957)
  
  These are marked with comment: `# [保留原有的方法作为备份，但不再被调用]`
- **Fix**: 删除这三个完整的方法定义
- **Approximate Lines**: 817-1093 (~276 lines)
- **Validation**: 
  1. 运行 `python -m py_compile sensor_calibrator/ui_manager.py`
  2. 运行 `python -c "from sensor_calibrator.ui_manager import UIManager"` 验证导入成功

### Task 2.2: 移除 ui_manager.py 空方法 _setup_network_section
- **Location**: `sensor_calibrator/ui_manager.py`, lines 479-481
- **Description**: 删除空的 `_setup_network_section` 方法
- **Current Code**:
  ```python
  def _setup_network_section(self):
      """设置网络配置区域框架（具体由子方法填充）"""
      pass  # 由 _setup_network_notebook 处理
  ```
- **Fix**: 删除这个方法定义（3行）
- **Validation**: 同 Task 2.1

## Sprint 3: Verification (Low Priority)

**Goal**: 确保修改没有破坏现有功能

### Task 3.1: 运行单元测试
- **Command**: `python -m pytest tests/ -v`
- **Expected**: 所有测试通过（如果有测试失败需要调查原因）

### Task 3.2: 验证应用可以启动
- **Command**: `python -c "from sensor_calibrator.app import SensorCalibratorApp; print('OK')"`
- **Expected**: 打印 "OK" 无错误

## Testing Strategy

| Phase | What to Test | How |
|-------|--------------|-----|
| Task 1.1 | serial_manager 语法 | py_compile |
| Task 1.2 | application.py 语法 | py_compile |
| Task 2.1 | ui_manager 导入 | import test |
| Sprint 3 | 整体功能 | pytest + import |

## Potential Risks & Gotchas

1. **ui_manager.py 行号变化**: 删除死代码后，行号会变化。需要确保删除完整的方法定义
2. **影响范围**: 这些是简单的删除操作，影响范围极小
3. **执行顺序**: 建议按顺序执行任务，先修复关键问题再删除死代码

## Rollback Plan

如果出现问题，使用 git 回滚：
```bash
git checkout -- sensor_calibrator/serial_manager.py
git checkout -- sensor_calibrator/app/application.py  
git checkout -- sensor_calibrator/ui_manager.py
```
