# Bare Except 修复实施计划

**Generated**: 2026-03-05
**Complexity**: Medium
**Strategy**: 方案 B - 具体异常类型分析

---

## Overview

将 `StableSensorCalibrator.py` 中的 9 处 bare except 修复为捕获具体的异常类型。修复遵循从低风险到高风险的顺序，确保每一步都可验证、可回滚。

**目标**:
- 消除 `ruff E722` 警告 (bare except)
- 保持原有功能不变
- 不引入新的异常处理漏洞
- 提高代码可维护性

---

## Prerequisites

- [ ] Python 3.8+ 环境
- [ ] 项目依赖已安装 (`pip install -r requirements.txt`)
- [ ] 现有测试可运行 (`pytest tests/`)
- [ ] ruff 已安装 (`pip install ruff`)
- [ ] 代码备份或版本控制 (git)

---

## Sprint 1: 低风险 Bare Except 修复

**Goal**: 修复最简单、风险最低的 4 处 bare except
**Estimated Time**: 30-45 分钟
**Risk Level**: Low

### Task 1.1: 修复 Windows DPI 设置 (第 189 行)

- **Location**: `StableSensorCalibrator.py:186-190`
- **Description**: 修复 Windows DPI 感知的异常处理，精确捕获 ImportError、AttributeError、OSError
- **Dependencies**: 无
- **Acceptance Criteria**:
  - `except:` 改为 `except (ImportError, AttributeError, OSError):`
  - Windows 上 DPI 功能正常工作
  - 非 Windows 平台静默失败
- **Validation**:
  ```bash
  # 检查修复
  ruff check --select=E722 StableSensorCalibrator.py
  
  # 手动测试: Windows 启动
  python -c "from StableSensorCalibrator import StableSensorCalibrator; c = StableSensorCalibrator()"
  ```

**修改前**:
```python
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass
```

**修改后**:
```python
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except (ImportError, AttributeError, OSError):
    # DPI awareness 仅在 Windows 可用，失败不影响核心功能
    pass
```

---

### Task 1.2: 修复窗口图标设置 (第 210 行)

- **Location**: `StableSensorCalibrator.py:207-210`
- **Description**: 修复 Tkinter 图标加载的异常处理
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - `except:` 改为 `except tk.TclError:`
  - 图标文件缺失时程序正常启动
  - 图标存在时正确显示
- **Validation**:
  ```bash
  # 检查修复
  ruff check --select=E722 StableSensorCalibrator.py
  
  # 手动测试: 无图标文件启动
  # 手动测试: 有图标文件启动
  ```

**修改前**:
```python
try:
    self.root.iconbitmap(default="icon.ico")
except:
    pass
```

**修改后**:
```python
try:
    self.root.iconbitmap(default="icon.ico")
except tk.TclError:
    # 图标文件缺失或损坏不影响核心功能
    pass
```

---

### Task 1.3: 修复 Matplotlib 图表关闭 (第 628 行)

- **Location**: `StableSensorCalibrator.py:625-629`
- **Description**: 修复图表关闭异常处理，添加引用清理
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - `except:` 改为 `except (ValueError, AttributeError):`
  - 添加 `finally` 块清理 `self.fig`
  - 程序关闭时无 Matplotlib 相关错误
- **Validation**:
  ```bash
  # 检查修复
  ruff check --select=E722 StableSensorCalibrator.py
  
  # 手动测试: 连接设备后关闭窗口
  # 手动测试: 未连接直接关闭窗口
  ```

**修改前**:
```python
if hasattr(self, "fig"):
    try:
        plt.close(self.fig)
    except:
        pass
```

**修改后**:
```python
if hasattr(self, "fig") and self.fig is not None:
    try:
        plt.close(self.fig)
    except (ValueError, AttributeError):
        # Figure 可能已被关闭或无效
        pass
    finally:
        self.fig = None  # 确保清理引用
```

---

### Task 1.4: 修复数据队列清空 (第 728 行)

- **Location**: `StableSensorCalibrator.py:723-729`
- **Description**: 修复队列清空的异常处理，处理竞态条件
- **Dependencies**: Task 1.3
- **Acceptance Criteria**:
  - `except:` 改为嵌套的 `except queue.Empty` 和 `except AttributeError`
  - 队列为空时安全处理
  - 无无限循环风险
- **Validation**:
  ```bash
  # 检查修复
  ruff check --select=E722 StableSensorCalibrator.py
  
  # 手动测试: 接收数据后关闭窗口
  # 检查无数据泄漏
  ```

**修改前**:
```python
if hasattr(self, "data_queue"):
    try:
        while not self.data_queue.empty():
            self.data_queue.get_nowait()
    except:
        pass
```

**修改后**:
```python
if hasattr(self, "data_queue") and self.data_queue is not None:
    try:
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                # 竞态条件：empty() 检查后变为空
                break
    except AttributeError:
        # data_queue 可能已被设置为 None
        pass
```

---

## Sprint 2: Tkinter After 任务取消修复

**Goal**: 修复 3 处 Tkinter after_cancel 相关的 bare except
**Estimated Time**: 30-45 分钟
**Risk Level**: Low-Medium

### Task 2.1: 修复 After 任务列表取消 (第 642 行)

- **Location**: `StableSensorCalibrator.py:639-644`
- **Description**: 修复 after_tasks 列表中任务取消的异常处理
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - `except:` 改为 `except tk.TclError:`
  - 迭代时使用 `list(self.after_tasks)` 创建副本
  - 任务取消失败不影响其他任务
- **Validation**:
  ```bash
  ruff check --select=E722 StableSensorCalibrator.py
  pytest tests/ -k "cleanup" -v  # 如果有相关测试
  ```

**修改前**:
```python
for task_id in self.after_tasks:
    try:
        self.root.after_cancel(task_id)
    except:
        pass
self.after_tasks.clear()
```

**修改后**:
```python
for task_id in list(self.after_tasks):  # 创建副本
    try:
        self.root.after_cancel(task_id)
    except tk.TclError:
        # 任务可能已执行或无效 ID，安全忽略
        pass
self.after_tasks.clear()
```

---

### Task 2.2: 修复窗口移动定时器取消 (第 650 行)

- **Location**: `StableSensorCalibrator.py:647-652`
- **Description**: 修复 _window_move_timer 取消的异常处理
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - `except:` 改为 `except tk.TclError:`
  - 添加 `finally` 确保 `_window_move_timer = None`
- **Validation**:
  ```bash
  ruff check --select=E722 StableSensorCalibrator.py
  # 手动测试: 拖动窗口后关闭
  ```

**修改前**:
```python
if self._window_move_timer:
    try:
        self.root.after_cancel(self._window_move_timer)
    except:
        pass
    self._window_move_timer = None
```

**修改后**:
```python
if self._window_move_timer:
    try:
        self.root.after_cancel(self._window_move_timer)
    except tk.TclError:
        pass
    finally:
        self._window_move_timer = None
```

---

### Task 2.3: 修复窗口移动事件中的定时器取消 (第 671 行)

- **Location**: `StableSensorCalibrator.py:668-672`
- **Description**: 修复 _on_window_move 中的定时器取消
- **Dependencies**: Task 2.2
- **Acceptance Criteria**:
  - `except:` 改为 `except tk.TclError:`
- **Validation**:
  ```bash
  ruff check --select=E722 StableSensorCalibrator.py
  # 手动测试: 快速拖动窗口
  ```

**修改前**:
```python
if self._window_move_timer and self.root is not None:
    try:
        self.root.after_cancel(self._window_move_timer)
    except:
        pass
```

**修改后**:
```python
if self._window_move_timer and self.root is not None:
    try:
        self.root.after_cancel(self._window_move_timer)
    except tk.TclError:
        pass
```

---

## Sprint 3: 复杂 Bare Except 修复

**Goal**: 修复最复杂的 2 处 bare except（窗口移动事件、串口读取）
**Estimated Time**: 45-60 分钟
**Risk Level**: Medium

### Task 3.1: 修复窗口移动事件处理 (第 680 行)

- **Location**: `StableSensorCalibrator.py:657-681`
- **Description**: 重构 _on_window_move 的分层异常处理
- **Dependencies**: Sprint 2 完成
- **Acceptance Criteria**:
  - 使用分层 try-except 结构
  - 每个可能失败的操作有独立异常处理
  - 最外层使用 `except Exception` 作为保险
  - 窗口移动时数据更新正确暂停/恢复
- **Validation**:
  ```bash
  ruff check --select=E722 StableSensorCalibrator.py
  
  # 手动测试:
  # 1. 连接设备，开始数据采集
  # 2. 拖动窗口，观察数据更新暂停
  # 3. 停止拖动，观察数据更新恢复
  # 4. 关闭窗口，无异常
  ```

**修改前**:
```python
def _on_window_move(self, event=None):
    try:
        # ... 完整的事件处理逻辑 ...
        if self._window_move_timer and self.root is not None:
            try:
                self.root.after_cancel(self._window_move_timer)
            except:
                pass
        # ...
    except:
        pass
```

**修改后**:
```python
def _on_window_move(self, event=None):
    """窗口移动事件处理 - 暂停数据更新以提高性能"""
    try:
        if not hasattr(self, 'root') or self.root is None:
            return
        
        # 获取当前窗口位置
        try:
            current_pos = (self.root.winfo_x(), self.root.winfo_y())
        except tk.TclError:
            # 窗口可能已销毁
            return
        
        # 检查位置是否变化
        if not hasattr(self, '_last_window_pos'):
            self._last_window_pos = current_pos
            return
        
        if current_pos == self._last_window_pos:
            return
        
        self._last_window_pos = current_pos
        self._chart_update_paused = True
        
        # 取消之前的定时器
        if self._window_move_timer and self.root is not None:
            try:
                self.root.after_cancel(self._window_move_timer)
            except tk.TclError:
                pass
        
        # 设置新的定时器
        if self.root is not None:
            try:
                self._window_move_timer = self.root.after(
                    Config.WINDOW_MOVE_PAUSE_DELAY,
                    self._on_window_move_end
                )
            except tk.TclError:
                pass
    except Exception:
        # 最后一层保险：窗口移动优化失败不应影响核心功能
        pass
```

---

### Task 3.2: 修复串口响应读取 (第 1836 行)

- **Location**: `StableSensorCalibrator.py:1828-1837`
- **Description**: 修复串口读取的异常处理，区分 SerialException 和 UnicodeDecodeError
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - `except:` 改为 `except serial.SerialException` 和 `except UnicodeDecodeError`
  - 收到非 UTF-8 数据时记录十六进制
  - 串口断开时正确处理
- **Validation**:
  ```bash
  ruff check --select=E722 StableSensorCalibrator.py
  
  # 手动测试:
  # 1. 正常发送命令，接收响应
  # 2. 断开设备，观察错误处理
  # 3. 重连设备，恢复通信
  ```

**修改前**:
```python
if self.ser and self.ser.is_open:
    try:
        response = self.ser.readline().decode().strip()
        if response:
            self.root.after(
                0, lambda r=response: self.log_message(f"Response: {r}")
            )
    except:
        pass
```

**修改后**:
```python
if self.ser and self.ser.is_open:
    try:
        response = self.ser.readline().decode().strip()
        if response:
            self.root.after(
                0, lambda r=response: self.log_message(f"Response: {r}")
            )
    except serial.SerialException:
        # 串口错误已在其他地方处理
        pass
    except UnicodeDecodeError:
        # 收到非 UTF-8 数据，记录原始字节
        try:
            raw_data = self.ser.readline()
            self.log_message(f"Received non-UTF8 data: {raw_data.hex()}")
        except serial.SerialException:
            pass
```

---

## Testing Strategy

### 静态分析
```bash
# 每次修改后运行
ruff check --select=E722 StableSensorCalibrator.py

# 全部检查
ruff check StableSensorCalibrator.py
```

### 单元测试
```bash
# 运行现有测试
pytest tests/ -v

# 如果有异常相关测试
pytest tests/ -k "exception" -v
```

### 手动测试清单

#### Sprint 1 验证
- [ ] Windows: DPI 感知正常工作
- [ ] 无 icon.ico 时程序正常启动
- [ ] 有 icon.ico 时图标显示正确
- [ ] 连接设备后关闭窗口无 Matplotlib 错误
- [ ] 接收数据后关闭窗口无队列错误

#### Sprint 2 验证
- [ ] 定时任务取消无异常
- [ ] 拖动窗口时定时器正确处理

#### Sprint 3 验证
- [ ] 拖动窗口时数据更新暂停
- [ ] 停止拖动后数据更新恢复
- [ ] 串口命令/响应正常
- [ ] 串口断开时优雅处理

---

## Potential Risks & Gotchas

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 遗漏某种异常类型 | 程序崩溃 | 保留 `except Exception` 作为最外层保险 |
| 竞态条件 (fig/queue 为 None) | AttributeError | 添加 `is not None` 检查 |
| UnicodeDecodeError 处理复杂 | 代码臃肿 | 仅记录十六进制，不阻断流程 |
| _on_window_move 重构引入新 Bug | 窗口移动问题 | 保持原逻辑，仅分层异常处理 |

### 关键注意事项

1. **不要过度处理**: 保持 "早失败" 原则，只在边界处捕获
2. **保留原始行为**: 每个 bare except 原本就是忽略错误，修复后也应如此
3. **测试覆盖**: 每处修改都需要手动测试异常路径

---

## Rollback Plan

1. **版本控制**: 每个 Sprint 完成后提交
   ```bash
   git add StableSensorCalibrator.py
   git commit -m "Sprint 1: Fix low-risk bare except (4 locations)"
   ```

2. **快速回滚**: 如果发现问题
   ```bash
   git checkout HEAD~1  # 回退一个 Sprint
   # 或
   git checkout main    # 回退到原始状态
   ```

3. **热修复**: 如果生产环境出问题
   ```bash
   git revert <commit-hash>
   ```

---

## Success Criteria

- [ ] 所有 9 处 bare except 已修复
- [ ] `ruff check --select=E722 .` 返回 0 警告
- [ ] 所有现有测试通过
- [ ] 手动测试清单全部完成
- [ ] 代码审查通过

---

## 实施顺序建议

**推荐顺序** (按风险递增):
1. ✅ Sprint 1 - 低风险 (Task 1.1 → 1.2 → 1.3 → 1.4)
2. ✅ Sprint 2 - 中低风险 (Task 2.1 → 2.2 → 2.3)
3. ✅ Sprint 3 - 中风险 (Task 3.1 → 3.2)

**时间估算**:
- Sprint 1: 30-45 分钟
- Sprint 2: 30-45 分钟
- Sprint 3: 45-60 分钟
- **总计**: 约 2-2.5 小时
