# 详细实施方案

**生成日期**: 2026-03-05
**决策**: 
- 激活工作流: 方案 B（方法参数传递）
- Bare except: 方案 B（具体异常类型分析）

---

## 第一部分: Bare Except 修复详情

### 分析方法

对每个 bare except 位置，我分析了：
1. 被保护的代码上下文
2. 可能抛出的异常类型
3. 最佳捕获策略

### 修复明细

#### 1. Windows DPI 设置 (第 189 行)

**位置**: `StableSensorCalibrator.py:186-190`

**当前代码**:
```python
def setup_gui(self):
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
```

**异常分析**:
| 异常类型 | 场景 | 概率 |
|----------|------|------|
| `ImportError` | 非 Windows 平台（Linux/Mac）| 高 |
| `AttributeError` | Windows 但无 shcore 模块 | 中 |
| `OSError` | Windows API 调用失败 | 低 |

**推荐修复**:
```python
def setup_gui(self):
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        # DPI awareness 仅在 Windows 可用，失败不影响核心功能
        pass
```

**理由**: 精确捕获预期的三种异常，不屏蔽其他意外错误。

---

#### 2. 设置窗口图标 (第 210 行)

**位置**: `StableSensorCalibrator.py:207-210`

**当前代码**:
```python
try:
    self.root.iconbitmap(default="icon.ico")
except:
    pass
```

**异常分析**:
| 异常类型 | 场景 | 概率 |
|----------|------|------|
| `tk.TclError` | 图标文件不存在/损坏/格式不对 | 高 |
| `FileNotFoundError` | tkinter 内部可能抛出 | 中 |

**推荐修复**:
```python
try:
    self.root.iconbitmap(default="icon.ico")
except tk.TclError:
    # 图标文件缺失或损坏不影响核心功能
    pass
```

**额外改进** (可选): 添加日志记录
```python
try:
    self.root.iconbitmap(default="icon.ico")
except tk.TclError:
    self.log_message("Warning: 图标文件加载失败，使用默认图标")
```

---

#### 3. 关闭 Matplotlib 图表 (第 628 行)

**位置**: `StableSensorCalibrator.py:625-629`

**当前代码**:
```python
if hasattr(self, "fig"):
    try:
        plt.close(self.fig)
    except:
        pass
```

**异常分析**:
| 异常类型 | 场景 | 概率 |
|----------|------|------|
| `ValueError` | Figure 已被关闭或不存在 | 高 |
| `AttributeError` | self.fig 为 None | 中 |
| `TypeError` | plt.close() 参数类型错误 | 低 |

**推荐修复**:
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

**重要改进**: 
1. 添加 `self.fig is not None` 检查
2. 添加 `finally` 块确保引用被清理
3. 防止内存泄漏

---

#### 4-6. 取消 Tkinter After 任务 (第 642, 650, 671 行)

这三处是相同模式，一并修复。

**位置**:
- `StableSensorCalibrator.py:640-643` (after_tasks 循环)
- `StableSensorCalibrator.py:647-651` (_window_move_timer)
- `StableSensorCalibrator.py:668-672` (_on_window_move 中)

**当前代码** (以第 642 行为例):
```python
for task_id in self.after_tasks:
    try:
        self.root.after_cancel(task_id)
    except:
        pass
self.after_tasks.clear()
```

**异常分析**:
| 异常类型 | 场景 | 概率 |
|----------|------|------|
| `tk.TclError` | 任务 ID 无效或已执行 | 高 |
| `ValueError` | after_cancel 参数问题 | 低 |
| `RuntimeError` | Tkinter 已销毁 | 低 |

**推荐修复**:
```python
for task_id in list(self.after_tasks):  # 创建副本避免修改迭代
    try:
        self.root.after_cancel(task_id)
    except tk.TclError:
        # 任务可能已执行或无效 ID，安全忽略
        pass
self.after_tasks.clear()
```

**第 650 行的特殊处理**:
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

#### 7. 窗口移动事件处理 (第 680 行)

**位置**: `StableSensorCalibrator.py:657-681`

**当前代码**:
```python
def _on_window_move(self, event=None):
    try:
        # ... 完整的事件处理逻辑
        if self._window_move_timer and self.root is not None:
            try:
                self.root.after_cancel(self._window_move_timer)
            except:
                pass
        # ...
    except:
        pass
```

**异常分析**: 这是一个大 try 块，包含多种操作

| 操作 | 可能异常 |
|------|----------|
| `self.root.winfo_x()` | `tk.TclError` (窗口已销毁) |
| `self.root.after_cancel()` | `tk.TclError` |
| `self.root.after()` | `tk.TclError` |
| 访问 `self._last_window_pos` | `AttributeError` (初始化时) |

**推荐修复 - 分层处理**:
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
        
        # 暂停更新
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

#### 8. 清空数据队列 (第 728 行)

**位置**: `StableSensorCalibrator.py:723-729`

**当前代码**:
```python
if hasattr(self, "data_queue"):
    try:
        while not self.data_queue.empty():
            self.data_queue.get_nowait()
    except:
        pass
```

**异常分析**:
| 异常类型 | 场景 | 概率 |
|----------|------|------|
| `queue.Empty` | `get_nowait()` 时队列为空（竞态）| 中 |
| `AttributeError` | data_queue 为 None | 低 |

**推荐修复**:
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

#### 9. 串口响应读取 (第 1836 行)

**位置**: `StableSensorCalibrator.py:1828-1837`

**当前代码**:
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

**异常分析**:
| 异常类型 | 场景 | 概率 |
|----------|------|------|
| `serial.SerialException` | 串口断开/错误 | 高 |
| `UnicodeDecodeError` | 收到非 UTF-8 数据 | 中 |
| `AttributeError` | self.ser 变为 None (竞态) | 低 |

**推荐修复**:
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

## 第二部分: 激活工作流重构详情

### 2.1 修改 `ActivationWorkflow` 类

#### 修改 1: `check_activation_status` 方法

**文件**: `sensor_calibrator/activation_workflow.py:199-238`

**当前代码**:
```python
def check_activation_status(self, sensor_properties: Dict[str, Any]) -> bool:
    """
    检查传感器激活状态
    
    Args:
        sensor_properties: 传感器属性字典
        
    Returns:
        bool: 是否已激活
    """
    self._log_message(f"[DEBUG] check_activation_status called")
    self._log_message(f"[DEBUG] MAC in workflow: {self._mac_address}")
    
    if not sensor_properties or not self._mac_address:
        self._log_message(f"[DEBUG] Missing data: properties={bool(sensor_properties)}, mac={bool(self._mac_address)}")
        return False
    
    # ... 后续逻辑
    self._is_activated = self.verify_key(aks_value)
```

**新代码**:
```python
def check_activation_status(
    self, 
    sensor_properties: Dict[str, Any],
    mac_address: Optional[str] = None
) -> bool:
    """
    检查传感器激活状态
    
    Args:
        sensor_properties: 传感器属性字典
        mac_address: MAC地址（可选，优先于内部状态）
        
    Returns:
        bool: 是否已激活
    """
    # 优先使用传入的参数，保持向后兼容
    mac = mac_address or self._mac_address
    
    if not sensor_properties or not mac:
        return False
    
    # 从属性中获取AKY字段
    aks_value = None
    if "sys" in sensor_properties:
        sys_info = sensor_properties["sys"]
        aks_value = (
            sys_info.get("AKY") or sys_info.get("aky") or sys_info.get("ak_key")
        )
    
    if not aks_value:
        self._is_activated = False
        return False
    
    # 验证密钥（传入 MAC 地址）
    try:
        self._is_activated = self.verify_key(aks_value, mac_address=mac)
        return self._is_activated
    except Exception as e:
        self._log_message(f"Error verifying activation key: {str(e)}")
        return False
```

**变更点**:
1. 添加 `mac_address` 参数
2. 使用 `mac = mac_address or self._mac_address` 保持向后兼容
3. 移除所有 `[DEBUG]` 日志
4. 向 `verify_key` 传递 `mac_address` 参数

---

#### 修改 2: `activate_sensor` 方法

**文件**: `sensor_calibrator/activation_workflow.py:242-262`

**当前代码**:
```python
def activate_sensor(self) -> bool:
    """
    激活传感器
    
    Returns:
        bool: 是否成功启动激活流程
    """
    if 'is_connected' in self.callbacks and not self.callbacks['is_connected']():
        self._log_message("Error: Not connected to serial port!")
        return False
    
    if not self._mac_address or not self._generated_key:
        self._log_message("Error: MAC address or generated key not available!")
        return False
    
    # ... 启动线程
```

**新代码**:
```python
def activate_sensor(
    self,
    mac_address: Optional[str] = None,
    generated_key: Optional[str] = None
) -> bool:
    """
    激活传感器
    
    Args:
        mac_address: MAC地址（可选，优先于内部状态）
        generated_key: 生成的密钥（可选，优先于内部状态）
        
    Returns:
        bool: 是否成功启动激活流程
    """
    if 'is_connected' in self.callbacks and not self.callbacks['is_connected']():
        self._log_message("Error: Not connected to serial port!")
        return False
    
    # 优先使用传入的参数
    mac = mac_address or self._mac_address
    key = generated_key or self._generated_key
    
    if not mac or not key:
        self._log_message("Error: MAC address or generated key not available!")
        return False
    
    # 保存到内部状态（供线程使用）
    self._mac_address = mac
    self._generated_key = key
    
    self._log_message("Starting sensor activation process...")
    
    # 在新线程中激活传感器，传递参数
    threading.Thread(
        target=self._activate_sensor_thread,
        args=(mac, key),  # 传递参数到线程
        daemon=True
    ).start()
    
    return True
```

---

#### 修改 3: `_activate_sensor_thread` 方法

**文件**: `sensor_calibrator/activation_workflow.py:264-336`

**变更**: 修改签名接收参数

```python
def _activate_sensor_thread(
    self,
    mac_address: str,
    generated_key: str
) -> None:
    """
    在新线程中激活传感器
    
    Args:
        mac_address: MAC地址
        generated_key: 生成的密钥
    """
    try:
        # ... 原有逻辑，使用传入的参数
        activation_cmd = f"SET:AKY,{generated_key[5:12]}"
        ser.write(activation_cmd.encode())
        ser.flush()
        
        self._log_message(f"Sent activation command: SET:AKY,{generated_key[5:12]}")
        # ...
```

---

#### 修改 4: 移除 `[DEBUG]` 日志

**文件**: `sensor_calibrator/activation_workflow.py`

**需要移除的行**:
- 第 176: `[DEBUG] verify_key called...`
- 第 180: `[DEBUG] No MAC address...`
- 第 187: `[DEBUG] Expected fragment...`
- 第 188: `[DEBUG] Input key...`
- 第 196: `[DEBUG] Compare result...`
- 第 209: `[DEBUG] check_activation_status called`
- 第 210: `[DEBUG] MAC in workflow...`
- 第 213: `[DEBUG] Missing data...`
- 第 224: `[DEBUG] AKY value...`
- 第 229: `[DEBUG] No AKY value...`
- 第 234: `[DEBUG] verify_key result...`

**替代方案**: 使用 Python `logging` 模块（可选）

```python
import logging

logger = logging.getLogger(__name__)

# 在关键位置使用
logger.debug("verify_key called with input: %s", input_key)
```

---

### 2.2 修改 `StableSensorCalibrator` 类

#### 修改 1: `check_activation_status` 调用

**文件**: `StableSensorCalibrator.py:1256-1282`

**当前代码**:
```python
def check_activation_status(self):
    # ...
    # 同步 MAC 地址到 ActivationWorkflow
    if self.mac_address:
        self.activation_workflow._mac_address = self.mac_address
    # ...
    is_activated = self.activation_workflow.check_activation_status(self.sensor_properties)
    self.sensor_activated = is_activated
```

**新代码**:
```python
def check_activation_status(self):
    """检查激活状态 - 委托给 ActivationWorkflow"""
    if not self.sensor_properties:
        return
    
    is_activated = self.activation_workflow.check_activation_status(
        self.sensor_properties,
        mac_address=self.mac_address
    )
    self.sensor_activated = is_activated
    
    if 'activation_status_var' in dir(self) and self.activation_status_var:
        status_text = "已激活" if is_activated else "未激活"
        self.activation_status_var.set(status_text)
```

---

#### 修改 2: `activate_sensor` 调用

**文件**: `StableSensorCalibrator.py:1284-1295`

**当前代码**:
```python
def activate_sensor(self):
    """激活传感器 - 委托给 ActivationWorkflow"""
    # 同步参数
    self.activation_workflow._mac_address = self.mac_address
    self.activation_workflow._generated_key = self.generated_key
    self.activation_workflow.activate_sensor()
```

**新代码**:
```python
def activate_sensor(self):
    """激活传感器 - 委托给 ActivationWorkflow"""
    if not self.mac_address or not self.generated_key:
        self.log_message("Error: MAC address or key not available")
        return
    
    self.activation_workflow.activate_sensor(
        mac_address=self.mac_address,
        generated_key=self.generated_key
    )
```

---

## 第三部分: 其他关键修复

### 3.1 SerialManager Race Condition

**文件**: `serial_manager.py:149-155`

**当前代码**:
```python
self.reset_input_buffer()
self.add_listener(_listener)
self.send_line(command)
```

**新代码**:
```python
self.add_listener(_listener)
try:
    self.reset_input_buffer()
    self.send_line(command)
    # ... 后续等待逻辑
finally:
    self.remove_listener(_listener)
```

### 3.2 移除 `__del__` 方法

**文件**: `StableSensorCalibrator.py:2371-2374`

**操作**: 删除整个 `__del__` 方法

**验证 `atexit` 已注册**:
```python
# 在 __init__ 中确保
atexit.register(self.cleanup)
```

### 3.3 主线程 Sleep 改为异步

**文件**: `StableSensorCalibrator.py:632`

**当前代码**:
```python
time.sleep(Config.SERIAL_CLEANUP_DELAY)
```

**新代码**:
```python
# 方案 A: 如果 cleanup 可以在 after 回调中完成
def cleanup_async(self):
    """异步清理，不阻塞主线程"""
    self.log_message("清理完成，程序即将退出")
    delay_ms = int(Config.SERIAL_CLEANUP_DELAY * 1000)
    self.root.after(delay_ms, self._finish_cleanup)

def _finish_cleanup(self):
    """完成清理并退出"""
    self.root.destroy()

# 方案 B: 如果必须同步等待，使用非阻塞方式
def cleanup(self):
    # ... 其他清理 ...
    self.log_message("清理完成，程序即将退出")
    # 使用 after 延迟退出
    self.root.after(
        int(Config.SERIAL_CLEANUP_DELAY * 1000),
        self._do_final_cleanup
    )

def _do_final_cleanup(self):
    self.root.quit()
    self.root.destroy()
```

---

## 实施顺序建议

### Phase 1: 准备 (30 分钟)
1. 创建功能分支
2. 运行现有测试，建立基线
3. 准备代码审查

### Phase 2: Bare Except 修复 (1-2 小时)
按风险从低到高:
1. DPI 设置 (189)
2. 窗口图标 (210)
3. Matplotlib 关闭 (628)
4. 队列清空 (728)
5. After 取消 (642, 650, 671)
6. 串口读取 (1836)
7. 窗口移动 (680) - 最复杂，最后处理

### Phase 3: 激活工作流重构 (1-2 小时)
1. 修改 `ActivationWorkflow` 方法签名
2. 更新 `StableSensorCalibrator` 调用点
3. 移除 DEBUG 日志
4. 运行激活相关测试

### Phase 4: 其他关键修复 (30 分钟)
1. SerialManager race condition
2. 移除 `__del__`
3. 主线程 sleep 修复

### Phase 5: 验证 (30 分钟)
1. 运行完整测试套件
2. 静态分析检查
3. 手动功能测试

---

## 验证检查清单

- [ ] `ruff check --select=E722 .` 无 bare except
- [ ] `mypy sensor_calibrator/` 类型检查通过
- [ ] 所有单元测试通过
- [ ] 手动测试: 激活流程
- [ ] 手动测试: 串口通信
- [ ] 手动测试: 窗口操作
- [ ] 手动测试: 程序正常关闭

---

## 回滚策略

1. **分支策略**: 在 `fix/code-review-issues` 分支工作
2. **提交粒度**: 每个文件/每个修复点独立提交
3. **回滚命令**:
   ```bash
   # 如果出现问题，回滚到主分支
   git checkout main
   git branch -D fix/code-review-issues
   ```
