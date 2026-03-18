# 修复计划：代码审查发现的问题

**Generated**: 2026-03-17  
**Estimated Complexity**: Low  
**Estimated Time**: 2-3 小时  
**Priority**: High (重复导入问题需立即修复)

---

## Overview

根据代码审查报告，修复 4 个发现的问题：
1. 重复导入代码 - calibration_workflow.py 第22-32行
2. MQTT端口验证不完整 - network_manager.py 第141-184行
3. 异常处理过于宽泛 - data_buffer.py 第450-452行
4. 代码重复 - ui_manager.py 第550-948行

---

## Prerequisites

- 项目能正常运行
- 测试环境可用
- git 已配置（建议先提交当前状态）

---

## Sprint 1: 修复重复导入问题 (Critical)

**Goal**: 修复 calibration_workflow.py 中的重复导入代码

**Demo/Validation**:
- 文件能正常导入
- 当 scripts/calibration.py 不存在时，_calibration_functions_available = False
- 单元测试通过

### Task 1.1: 删除重复导入代码
- **Location**: sensor_calibrator/calibration_workflow.py
- **Description**: 删除第30-32行的重复导入代码
- **Acceptance Criteria**:
  - 删除第30行 scripts_path = Path(__file__).parent.parent / "scripts"
  - 删除第31行 sys.path.insert(0, str(scripts_path))
  - 删除第32行 from calibration import ...
  - 保留第22-28行的带 try/except 的导入代码

### Task 1.2: 添加导入失败测试
- **Location**: tests/test_calibration_workflow.py (新建)
- **Description**: 添加测试验证导入失败时的行为
- **Dependencies**: Task 1.1

---

## Sprint 2: 完善端口验证 (Important)

**Goal**: 在 network_manager.py 中添加完整的 MQTT 端口验证

### Task 2.1: 添加端口验证函数
- **Location**: sensor_calibrator/network_manager.py
- **Description**: 添加私有方法验证端口有效性
- **Acceptance Criteria**:
  - 添加 _validate_port(self, port: str) -> tuple[bool, str] 方法
  - 验证端口是否为数字
  - 验证端口范围 1-65535

### Task 2.2: 在 set_mqtt_config 中集成验证
- **Location**: sensor_calibrator/network_manager.py 第141-184行
- **Description**: 调用新的验证方法
- **Dependencies**: Task 2.1

### Task 2.3: 添加端口验证单元测试
- **Location**: tests/test_network_manager.py
- **Description**: 为端口验证添加测试
- **Dependencies**: Task 2.2

---

## Sprint 3: 改进异常处理 (Minor)

**Goal**: 使 data_buffer.py 的异常处理更具体

### Task 3.1: 细化异常捕获
- **Location**: sensor_calibrator/data_buffer.py 第450-452行
- **Description**: 将宽泛的 except Exception 改为具体异常
- **Acceptance Criteria**:
  - 将 except Exception: 改为 except (ValueError, TypeError):

---

## Sprint 4: 清理重复代码 (Minor)

**Goal**: 清理 ui_manager.py 中未使用的重复方法

### Task 4.1: 删除未使用的方法
- **Location**: sensor_calibrator/ui_manager.py
- **Description**: 删除 _setup_wifi_section, _setup_mqtt_section, _setup_ota_section
- **Safety Check**:
  - grep -n "_setup_wifi_section" sensor_calibrator/*.py
  - 确认未被调用后再删除

---

## Sprint 5: 最终验证 (All)

### Task 5.1: 运行所有测试
- 运行完整测试套件
- python -m pytest tests/ -v

### Task 5.2: 功能测试
- 应用能正常启动
- 串口连接功能正常
- 数据流显示正常

### Task 5.3: 代码审查
- 代码风格一致
- 注释完整

---

## Potential Risks

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| 删除重复导入时误删有效代码 | High | 仔细对比第22-28行和第30-32行 |
| 端口验证过于严格 | Medium | 确保空端口仍使用默认值 |
| 删除 UI 方法时破坏功能 | Low | 先搜索所有引用 |

---

## Summary

| Sprint | 问题 | 预计时间 | 优先级 |
|--------|------|----------|--------|
| 1 | 重复导入 | 30 min | High |
| 2 | 端口验证 | 45 min | Medium |
| 3 | 异常处理 | 15 min | Low |
| 4 | 代码清理 | 30 min | Low |
| 5 | 最终验证 | 30 min | High |

---

## 详细修复代码示例

### Sprint 1 修复代码

修复前 (calibration_workflow.py 第22-32行):
```python
# 第22-28行：第一次导入
try:
    scripts_path = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_path))
    from calibration import compute_six_position_calibration, compute_gyro_offset
    _calibration_functions_available = True
except (ImportError, ModuleNotFoundError) as e:
    _import_error_message = str(e)
    compute_six_position_calibration = None
    compute_gyro_offset = None
scripts_path = Path(__file__).parent.parent / "scripts"  # 第30行 - 删除
sys.path.insert(0, str(scripts_path))  # 第31行 - 删除
from calibration import compute_six_position_calibration, compute_gyro_offset  # 第32行 - 删除
```

修复后:
```python
try:
    scripts_path = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_path))
    from calibration import compute_six_position_calibration, compute_gyro_offset
    _calibration_functions_available = True
except (ImportError, ModuleNotFoundError) as e:
    _import_error_message = str(e)
    compute_six_position_calibration = None
    compute_gyro_offset = None
```

### Sprint 2 修复代码

添加验证方法 (network_manager.py):
```python
def _validate_port(self, port: str) -> tuple[bool, str]:
    """验证端口号有效性"""
    if not port:
        return True, ""  # 使用默认值
    try:
        port_num = int(port)
        if not (1 <= port_num <= 65535):
            return False, f"Port must be between 1 and 65535, got {port_num}"
        return True, ""
    except ValueError:
        return False, f"Port must be a number, got '{port}'"
```

在 set_mqtt_config 中使用:
```python
def set_mqtt_config(self, broker: str, username: str, password: str, port: str) -> bool:
    # ... 现有验证 ...
    
    # 验证端口
    is_valid, error_msg = self._validate_port(port)
    if not is_valid:
        self._log_message(f"Error: {error_msg}")
        return False
    
    if not port:
        port = "1883"
    # ... 其余代码 ...
```

### Sprint 3 修复代码

修复前 (data_buffer.py 第450-452行):
```python
except Exception:
    # 数据解析失败（格式错误/无效数据），静默返回 None
    pass
```

修复后:
```python
except (ValueError, TypeError):
    # 数据解析失败（格式错误/无效数据），静默返回 None
    pass
```

---

**计划文件保存位置**: D:\公司文件\监测仪软件\SensorCalibrator\fix-code-review-issues-plan.md
