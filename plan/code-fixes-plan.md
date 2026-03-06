# 代码修复计划

**Generated**: 2026-03-06
**Estimated Complexity**: Low

## 概述

针对代码 review 中确认的问题，制定本修复计划。主要修复一个确认的 bug（错误的发送命令）和多个代码质量问题（裸异常捕获）。

## 已确认的问题

### 1. Bug: 错误的停止命令
- **位置**: `sensor_calibrator/app/application.py:704`
- **问题**: `stop_data_stream_safe()` 调用 `send_ss0_start_stream()` 而非 `send_ss4_stop_stream()`
- **风险**: 应用退出时无法正确停止数据流，可能导致串口资源未释放

### 2. 代码质量: 裸异常捕获
- **位置**: 多处 `except Exception: pass`
- **问题**: 吞掉所有异常，难以排查问题
- **目标**: 添加至少 ERROR 级别的日志记录

### 3. 代码质量: 硬编码数值
- **位置**: `application.py:789` 等
- **问题**: 魔法数字 `100` 等未放入配置
- **目标**: 提取到 `Config` 类

---

## Sprint 1: 修复关键 Bug

**目标**: 修复 `stop_data_stream_safe` 错误命令问题
**Demo/Validation**: 
- 代码审查确认命令正确
- 运行测试确保无回归

### Task 1.1: 修复停止数据流命令
- **Location**: `sensor_calibrator/app/application.py:704`
- **Description**: 将 `send_ss0_start_stream()` 改为 `send_ss4_stop_stream()`
- **Dependencies**: 无
- **变更内容**:
  ```python
  # 修改前
  if self.ser and self.ser.is_open:
      self.send_ss0_start_stream()
  
  # 修改后
  if self.ser and self.ser.is_open:
      self.send_ss4_stop_stream()
  ```
- **Acceptance Criteria**:
  - 方法调用正确
  - 代码语义清晰（停止数据流时发送停止命令）
- **Validation**:
  - 运行 `python -m pytest tests/ -v` 确保无回归
  - 代码审查

---

## Sprint 2: 改进异常处理

**目标**: 消除裸 `except: pass`，添加日志记录
**Demo/Validation**:
- 搜索所有裸异常捕获点
- 确认每个点都有日志记录

### Task 2.1: 识别所有裸异常捕获点
- **Description**: 搜索并列出所有需要改进的异常处理
- **Dependencies**: Task 1.1
- **命令**:
  ```bash
  grep -rn "except Exception:" sensor_calibrator/ --include="*.py"
  grep -rn "except:$" sensor_calibrator/ --include="*.py"
  ```
- **Acceptance Criteria**:
  - 生成完整的问题点列表
  - 按严重程度分类

### Task 2.2: 修复关键路径的异常处理
- **Location**: 
  - `sensor_calibrator/app/application.py:822-823` (update_gui)
  - `sensor_calibrator/serial_manager.py:321-326` (_read_serial_data)
- **Description**: 添加日志记录
- **Dependencies**: Task 2.1
- **变更示例**:
  ```python
  # 修改前
  except Exception:
      break
  
  # 修改后
  except Exception as e:
      self.log_message(f"Error processing data: {e}", "ERROR")
      break
  ```
- **Acceptance Criteria**:
  - 关键路径异常不再静默
  - 日志级别适当

### Task 2.3: 修复数据处理的异常处理
- **Location**: `sensor_calibrator/data_processor.py:81-84`
- **Description**: `parse_sensor_data` 方法
- **Dependencies**: Task 2.1
- **变更示例**:
  ```python
  # 修改前
  except Exception:
      pass
  
  # 修改后（考虑性能，仅在调试时记录）
  except Exception:
      # 数据解析失败是预期情况（垃圾数据），静默处理
      pass
  ```
- **Acceptance Criteria**:
  - 高频调用路径保持性能
  - 异常情况可追踪（可选 DEBUG 日志）

---

## Sprint 3: 提取硬编码配置

**目标**: 将魔法数字提取到 Config 类
**Demo/Validation**:
- 确认所有硬编码值都有配置项
- 测试配置生效

### Task 3.1: 提取 GUI 更新处理数量限制
- **Location**: 
  - `sensor_calibrator/app/application.py:789`
- **Description**: 提取 `processed_count < 100` 中的 `100`
- **Dependencies**: 无
- **变更内容**:
  ```python
  # config.py 添加
  MAX_GUI_UPDATE_BATCH: Final[int] = 100
  
  # application.py 修改
  while not self.data_queue.empty() and processed_count < Config.MAX_GUI_UPDATE_BATCH:
  ```
- **Acceptance Criteria**:
  - 配置项命名清晰
  - 默认值与原值一致

### Task 3.2: 提取校准最小样本比例
- **Location**: `sensor_calibrator/calibration_workflow.py:171`
- **Description**: 提取 `Config.CALIBRATION_SAMPLES // 10` 中的 `10`
- **Dependencies**: 无
- **变更内容**:
  ```python
  # config.py 添加
  MIN_CALIBRATION_SAMPLE_RATIO: Final[float] = 0.1  # 10%
  
  # calibration_workflow.py 修改
  min_samples = int(Config.CALIBRATION_SAMPLES * Config.MIN_CALIBRATION_SAMPLE_RATIO)
  if samples_collected >= min_samples:
  ```
- **Acceptance Criteria**:
  - 配置项命名清晰
  - 浮点比例比整数除法更易理解

---

## 测试策略

### 单元测试
- 运行现有测试：`python -m pytest tests/ -v`
- 确认无回归

### 集成测试
- 启动应用：`python main.py`
- 验证串口连接/断开功能正常
- 验证数据流启停正常

### 代码审查检查项
- [ ] Bug 修复正确
- [ ] 异常处理改进不引入性能问题
- [ ] 配置提取完整
- [ ] 无语法错误

---

## 潜在风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 修改引入回归 | 低 | 中 | 运行完整测试套件 |
| 日志过多影响性能 | 中 | 低 | 高频路径保持静默或 DEBUG 级别 |
| 配置项命名冲突 | 低 | 低 | 检查现有配置命名 |

---

## 回滚计划

如出现问题，按以下顺序回滚：
1. Sprint 3 更改（配置提取）- 不影响功能
2. Sprint 2 更改（异常处理）- 不影响功能
3. Sprint 1 更改（Bug 修复）- 需要验证

---

## 执行顺序

```
Task 1.1 → Task 2.1 → Task 2.2 → Task 2.3 → Task 3.1 → Task 3.2
```

每个 Sprint 完成后运行测试，确保无回归。
