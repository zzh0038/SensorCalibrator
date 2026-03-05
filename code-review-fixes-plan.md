# 代码审查问题修复计划

**Generated**: 2026-03-05
**Estimated Complexity**: Medium
**Priority**: High

## 概述

根据代码审查报告，本计划涵盖 StableSensorCalibrator.py、serial_manager.py 和相关模块中的关键问题修复。所有修复旨在提高代码可靠性、可维护性和性能。

## 修复优先级

| 优先级 | 问题 | 影响 |
|--------|------|------|
| 🔴 P0 | Bare except 块 | 可能捕获 KeyboardInterrupt, SystemExit |
| 🔴 P0 | SerialManager Race Condition | 可能丢失串口响应 |
| 🔴 P0 | 主线程 Sleep 阻塞 UI | UI 无响应 |
| 🟡 P1 | 私有属性访问破坏封装 | 维护困难，易出错 |
| 🟡 P1 | `__del__` 不可靠清理 | 资源泄露风险 |
| 🟢 P2 | 循环导入风险 | 潜在启动问题 |
| 🟢 P2 | 硬编码路径 | 可移植性差 |

---

## Sprint 1: 关键 Bug 修复 (P0)

**Goal**: 修复可能导致运行时错误或数据丢失的关键问题
**Estimated Time**: 1-2 天
**Demo/Validation**: 所有现有测试通过，UI 响应正常

### Task 1.1: 修复 Bare except 块
- **Location**: `StableSensorCalibrator.py`
- **Line Numbers**: 189, 209, 628, 642, 650, 671, 680, 728, 1836
- **Description**: 将 `except:` 改为 `except Exception:` 或更具体的异常类型
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 所有 bare except 被替换
  - 不破坏现有功能
  - 保留 KeyboardInterrupt/SystemExit 的向上传播
- **Validation**:
  - 运行 `ruff check --select=E722` 确认无 bare except
  - 手动测试相关功能路径

**修改示例**:
```python
# Before
except:
    pass

# After
except Exception:
    pass

# Better: 具体异常
except (serial.SerialException, ValueError) as e:
    self.log_message(f"Error: {e}")
```

### Task 1.2: 修复 SerialManager Race Condition
- **Location**: `serial_manager.py`
- **Line Numbers**: 149-155
- **Description**: 调整 `request_response` 中 listener 注册和缓冲区清空的顺序
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 先注册 listener，再清空缓冲区，最后发送命令
  - 确保不会丢失响应数据
- **Validation**:
  - 运行串口通信测试
  - 验证高频率命令/响应场景

**修改方案**:
```python
# Before
self.reset_input_buffer()
self.add_listener(_listener)
self.send_line(command)

# After
self.add_listener(_listener)
try:
    self.reset_input_buffer()
    self.send_line(command)
    # ... wait for response
finally:
    self.remove_listener(_listener)
```

### Task 1.3: 修复主线程 Sleep 阻塞 UI
- **Location**: `StableSensorCalibrator.py`
- **Line Number**: 632
- **Description**: 使用 `self.root.after()` 替代 `time.sleep()` 实现非阻塞延迟
- **Dependencies**: 无
- **Acceptance Criteria**:
  - UI 在清理期间保持响应
  - 清理延迟仍然有效
- **Validation**:
  - 手动测试关闭窗口操作
  - 确认 UI 不卡顿

**修改方案**:
```python
# Before
time.sleep(Config.SERIAL_CLEANUP_DELAY)
self.cleanup()

# After
self.root.after(int(Config.SERIAL_CLEANUP_DELAY * 1000), self._do_cleanup)

# 或重构 cleanup 为异步方式
def cleanup_async(self, callback=None):
    def delayed_cleanup():
        self._actual_cleanup()
        if callback:
            callback()
    self.root.after(int(Config.SERIAL_CLEANUP_DELAY * 1000), delayed_cleanup)
```

---

## Sprint 2: 封装改进 (P1)

**Goal**: 改进类的封装性，减少耦合
**Estimated Time**: 1-2 天
**Demo/Validation**: ActivationWorkflow 接口改进，无直接私有属性访问

### Task 2.1: 重构 ActivationWorkflow 状态管理
- **Location**: 
  - `StableSensorCalibrator.py:1261, 1288`
  - `sensor_calibrator/activation_workflow.py` (如存在)
- **Description**: 
  - 为 ActivationWorkflow 添加 `set_mac_address()` 公共方法
  - 或修改工作流方法接受 MAC 地址参数
  - 移除直接设置 `_mac_address` 的操作
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 无直接访问 `_mac_address` 私有属性
  - 功能保持不变
- **Validation**:
  - 激活功能测试通过
  - 代码搜索确认无 `_mac_address` 直接访问

**修改方案 A - 添加 setter 方法**:
```python
# ActivationWorkflow 类
def set_mac_address(self, mac_address: str) -> None:
    """设置 MAC 地址用于激活验证。"""
    self._mac_address = mac_address

# StableSensorCalibrator
self.activation_workflow.set_mac_address(self.mac_address)
```

**修改方案 B - 方法参数传递** (推荐):
```python
# 修改工作流方法签名
def check_activation(self, mac_address: str) -> bool:
    """检查激活状态，传入 MAC 地址。"""
    # 使用传入的 mac_address，不依赖内部状态
    ...

# 调用方式
result = self.activation_workflow.check_activation(self.mac_address)
```

### Task 2.2: 移除 `__del__` 析构函数
- **Location**: `StableSensorCalibrator.py:2371-2374`
- **Description**: 
  - 移除 `__del__` 方法
  - 确保 `cleanup()` 通过 `atexit` 和 `on_closing` 正确调用
  - 添加警告日志到 cleanup 如果资源未正确释放
- **Dependencies**: 无
- **Acceptance Criteria**:
  - `__del__` 方法被移除
  - 资源清理仍正常工作
- **Validation**:
  - 正常关闭测试
  - 异常关闭测试

**修改方案**:
```python
# 移除整个 __del__ 方法
# 已在 __init__ 中注册: atexit.register(self.cleanup)

# 确保 cleanup  robust
def cleanup(self):
    """清理资源，可安全多次调用。"""
    if self.exiting:
        return
    self.exiting = True
    # ... 清理逻辑
```

---

## Sprint 3: 代码质量改进 (P2)

**Goal**: 改善代码质量和可维护性
**Estimated Time**: 0.5-1 天
**Demo/Validation**: 静态检查通过，无循环导入

### Task 3.1: 解决循环导入风险
- **Location**: `network_config.py`
- **Description**: 
  - 检查 `sensor_calibrator` 模块的导入关系
  - 将验证函数移动到共享工具模块或内联
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 无循环导入风险
  - 功能保持不变
- **Validation**:
  - 导入测试通过
  - `python -c "import network_config"` 成功

**修改方案**:
```python
# 选项 1: 在 network_config.py 内内联验证
from typing import Optional

def _validate_port(port: str) -> Optional[int]:
    """内部验证函数，避免外部依赖。"""
    try:
        p = int(port)
        return p if 1 <= p <= 65535 else None
    except ValueError:
        return None

# 选项 2: 移动验证函数到 utils/validation.py
from utils.validation import validate_port, validate_password
```

### Task 3.2: 修复硬编码路径
- **Location**: `read_docx.py`
- **Description**: 
  - 接受命令行参数作为文件路径
  - 添加参数验证和 usage 提示
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 路径通过 `sys.argv[1]` 传入
  - 提供友好的错误信息
- **Validation**:
  - 测试脚本带参数运行
  - 测试无参数时的错误提示

**修改方案**:
```python
import sys
from docx import Document

def main():
    if len(sys.argv) < 2:
        print("Usage: python read_docx.py <path_to_docx>")
        print("Example: python read_docx.py 'D:\\公司文件\\文档.docx'")
        sys.exit(1)
    
    doc_path = sys.argv[1]
    try:
        doc = Document(doc_path)
        # ... 处理逻辑
    except FileNotFoundError:
        print(f"Error: File not found: {doc_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading document: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 测试策略

### 单元测试
- 每个修复任务添加对应的单元测试
- 测试边界条件和异常处理

### 集成测试
- 完整的激活流程测试
- 串口通信压力测试
- UI 响应性测试

### 静态分析
```bash
# 检查 bare except
ruff check --select=E722 .

# 全面检查
ruff check .

# 类型检查
mypy sensor_calibrator/ stable_sensor_calibrator.py
```

---

## 潜在风险 & 解决方案

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| Bare except 修改引入未捕获异常 | 中 | 高 | 1. 保留通用 Exception 捕获<br>2. 添加详细日志<br>3. 渐进式修改，一次一个 |
| SerialManager 修改破坏现有逻辑 | 低 | 高 | 1. 充分测试各种时序<br>2. 保留回滚方案<br>3. 代码审查 |
| UI 异步修改导致竞态 | 中 | 中 | 1. 使用 Tkinter 的 `after`<br>2. 确保原子性操作<br>3. 测试快速开关场景 |
| ActivationWorkflow API 变更破坏调用 | 低 | 高 | 1. 先添加新方法<br>2. 标记旧方法弃用<br>3. 统一修改调用点 |

---

## 回滚计划

1. **版本控制**: 每个 Sprint 独立分支
2. **测试验证**: 每个 Task 完成后运行完整测试套件
3. **快速回滚**: 如发现问题，立即回滚到上一个稳定提交
4. **功能开关**: 对于复杂修改，考虑使用功能开关控制新行为

---

## 完成检查清单

- [ ] Task 1.1: 所有 bare except 被修复
- [ ] Task 1.2: SerialManager race condition 修复
- [ ] Task 1.3: 主线程 sleep 改为异步
- [ ] Task 2.1: 无直接 `_mac_address` 私有属性访问
- [ ] Task 2.2: `__del__` 方法已移除
- [ ] Task 3.1: 无循环导入风险
- [ ] Task 3.2: 硬编码路径已修复
- [ ] 所有测试通过
- [ ] 静态检查无警告
- [ ] 手动测试验证通过
