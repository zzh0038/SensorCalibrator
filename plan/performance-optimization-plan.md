# SensorCalibrator 性能优化实施计划

**Generated**: 2026-03-03  
**Estimated Complexity**: Medium  
**Estimated Duration**: 2-3 天  
**Risk Level**: Low (有完整回滚方案)

---

## Overview

本计划针对 SensorCalibrator 项目的 6 项性能瓶颈实施渐进式优化。采用**分阶段实施、独立测试、随时回滚**的策略，确保每次优化都能独立验证，不影响现有功能。

### 优化项汇总

| 优先级 | 优化项 | 目标文件 | 预期收益 |
|-------|-------|---------|---------|
| 🔴 P0 | data_buffer.py 改用 deque | `sensor_calibrator/data_buffer.py` | 减少 30% 内存分配 |
| 🔴 P0 | 统计计算避免 list 转换 | `sensor_calibrator/data_processor.py` | 减少 20% CPU 占用 |
| 🟡 P1 | Y 轴范围计算优化 | `sensor_calibrator/chart_manager.py` | 减少 10% 渲染时间 |
| 🟡 P1 | 队列竞争优化 | `sensor_calibrator/serial_manager.py` | 减少 15% 线程开销 |
| 🟢 P2 | 日志限流机制 | `StableSensorCalibrator.py` | 改善 UI 响应性 |
| 🟢 P2 | 主程序模块化拆分 | `sensor_calibrator/ui/` 新目录 | 改善可维护性 |

---

## Prerequisites

### 环境准备
- [ ] Python 3.8+ 环境
- [ ] 现有测试用例通过：`python -m pytest tests/ -v`
- [ ] 备份当前代码：`git stash` 或 `git branch backup-before-optimization`
- [ ] 确保 `performance_profile.py` 可正常运行

### 基准测试数据
```bash
# 运行前记录基准性能
python performance_profile.py > baseline_performance.txt
```

---

## Sprint 1: 数据缓冲区优化 (P0)

**Goal**: 将 `SensorDataBuffer` 从 list 改为 deque，消除频繁切片造成的内存分配

**Demo/Validation**:
- 运行 `test_data_buffer.py` 测试用例通过
- 内存分析显示切片操作减少
- 长时间运行（模拟 1 小时数据）内存稳定

---

### Task 1.1: 修改数据存储结构
- **Location**: `sensor_calibrator/data_buffer.py`
- **Description**: 将所有 list 类型的数据存储改为 deque
- **Dependencies**: 无
- **Acceptance Criteria**:
  - `_time_data`, `_mpu_accel_data`, `_mpu_gyro_data`, `_adxl_accel_data`, `_gravity_mag_data` 全部使用 deque
  - `maxlen` 参数正确设置
  - 删除 `_enforce_size_limit()` 方法（deque 自动处理）
- **Validation**:
  ```bash
  python -m pytest tests/test_data_processor.py -v -k buffer
  ```

**代码变更预览**:
```python
# 修改前
self._time_data: List[float] = []
# ...
def _enforce_size_limit(self) -> None:
    # 复杂的切片逻辑

# 修改后
self._time_data: deque[float] = deque(maxlen=self._max_points)
# 无需 _enforce_size_limit，deque 自动丢弃旧数据
```

---

### Task 1.2: 更新数据访问属性
- **Location**: `sensor_calibrator/data_buffer.py` (lines 98-126)
- **Description**: 修改 property 方法以正确处理 deque 类型
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - `time_data`, `mpu_accel_data` 等属性正确返回 list 副本（向后兼容）
  - `get_latest()` 方法正常工作
  - 线程锁逻辑保持不变
- **Validation**:
  ```python
  # 手动测试
  from sensor_calibrator.data_buffer import SensorDataBuffer
  buf = SensorDataBuffer()
  for i in range(3000):  # 超过 maxlen
      buf.add_sample(i, (1,2,3), (4,5,6), (7,8,9), 10.0)
  assert len(buf.time_data) == 2000  # 保持 maxlen
  ```

---

### Task 1.3: 更新统计计算方法
- **Location**: `sensor_calibrator/data_buffer.py` (lines 155-216)
- **Description**: 优化 `calculate_statistics` 以高效处理 deque
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - 统计计算无需将 deque 转换为 list
  - 使用 `itertools.islice` 获取窗口数据
  - numpy 计算结果正确
- **Validation**:
  ```bash
  python -c "
  from sensor_calibrator.data_buffer import SensorDataBuffer
  import time
  buf = SensorDataBuffer()
  for i in range(1000):
      buf.add_sample(i, (1,2,3), (4,5,6), (7,8,9), 10.0)
  start = time.perf_counter()
  stats = buf.calculate_statistics()
  print(f'Statistics calculation: {(time.perf_counter()-start)*1000:.2f} ms')
  "
  ```

---

## Sprint 2: 统计计算优化 (P0)

**Goal**: 消除 `calculate_statistics` 中的重复类型转换

**Demo/Validation**:
- `DataProcessor.calculate_statistics()` 性能提升 > 20%
- 测试用例全部通过
- 内存分配监控显示无冗余 list 创建

---

### Task 2.1: 优化 calculate_statistics 方法
- **Location**: `sensor_calibrator/data_processor.py` (lines 129-166)
- **Description**: 直接从 deque/slice 计算统计值，避免转换为 list
- **Dependencies**: Sprint 1 完成（或直接基于当前代码）
- **Acceptance Criteria**:
  - 删除 `isinstance(data_array, deque)` 检查
  - 使用 `np.fromiter()` 或切片视图直接计算
  - 保持接口不变（向后兼容）
- **Validation**:
  ```python
  # 性能对比测试
  import timeit
  # 优化前 vs 优化后
  ```

**代码变更预览**:
```python
# 修改前
def calculate_statistics(self, data_array, ...):
    if isinstance(data_array, deque):
        data_array = list(data_array)  # 昂贵的复制
    segment = data_array[start_idx:end_idx]
    mean_val = float(np.mean(segment))

# 修改后  
def calculate_statistics(self, data_array, ...):
    # 直接处理 deque，避免转换
    if isinstance(data_array, deque):
        # 使用切片创建视图而非复制
        segment = list(itertools.islice(data_array, start_idx, end_idx))
    else:
        segment = data_array[start_idx:end_idx]
    mean_val = float(np.mean(segment))
```

---

### Task 2.2: 添加统计缓存机制
- **Location**: `sensor_calibrator/data_processor.py`
- **Description**: 添加增量统计更新，避免每次都重新计算
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - 新增 `_stats_cache` 和 `_stats_version` 字段
  - 数据未变化时直接返回缓存结果
  - 缓存失效逻辑正确（数据追加时）
- **Validation**:
  ```bash
  python -m pytest tests/ -v -k stats
  ```

---

## Sprint 3: 图表渲染优化 (P1)

**Goal**: 优化 Y 轴范围计算，避免重复遍历数据

**Demo/Validation**:
- 图表更新帧率稳定
- `adjust_y_limits` 执行时间减少 > 30%
- 窗口移动时无明显卡顿

---

### Task 3.1: 优化 Y 轴范围计算算法
- **Location**: `sensor_calibrator/chart_manager.py` (lines 444-525)
- **Description**: 使用生成器表达式替代列表扩展，减少内存分配
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 消除 `recent_data.extend()` 导致的列表复制
  - 使用 `min()`/`max()` 配合生成器直接计算
  - 处理空数据边界情况
- **Validation**:
  ```python
  # 手动测试 adjust_y_limits 性能
  import time
  # 模拟 2000 点数据，测量执行时间
  ```

**代码变更预览**:
```python
# 修改前 (MPU 加速度计部分)
recent_data = []
for i in range(3):
    if len(mpu_accel[i]) >= recent_points:
        recent_data.extend(mpu_accel[i][-recent_points:])
if recent_data:
    y_min = float(np.min(recent_data))
    y_max = float(np.max(recent_data))

# 修改后
y_min = float('inf')
y_max = float('-inf')
for i in range(3):
    if len(mpu_accel[i]) >= recent_points:
        ch_min = np.min(mpu_accel[i][-recent_points:])
        ch_max = np.max(mpu_accel[i][-recent_points:])
        y_min = min(y_min, ch_min)
        y_max = max(y_max, ch_max)
if y_min != float('inf'):
    # 应用 padding
```

---

### Task 3.2: 添加 Y 轴范围缓存
- **Location**: `sensor_calibrator/chart_manager.py`
- **Description**: 缓存上次计算的 Y 轴范围，避免频繁重算
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - 新增 `_y_limits_cache` 字典存储各轴范围
  - 仅当数据范围变化超过阈值时才更新
  - 与现有 `y_limit_update_interval` 配合工作
- **Validation**:
  - 连续调用 `adjust_y_limits` 两次，第二次应使用缓存

---

## Sprint 4: 队列竞争优化 (P1)

**Goal**: 优化串口数据队列的并发访问性能

**Demo/Validation**:
- 高频数据流（>100Hz）下无丢包
- CPU 占用降低
- 串口读取线程稳定运行

---

### Task 4.1: 实现环形缓冲区替代 Queue
- **Location**: 新建 `sensor_calibrator/ring_buffer.py`
- **Description**: 创建无锁（或更少锁）的环形缓冲区
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 实现 `RingBuffer` 类，支持 `put()`, `get()`, `full()`, `empty()`
  - 使用 `threading.Lock` 但减少临界区大小
  - 满时自动覆盖最旧数据（无需 pop+put 两次操作）
- **Validation**:
  ```bash
  python -m pytest tests/test_ring_buffer.py -v  # 需新建测试
  ```

---

### Task 4.2: 集成 RingBuffer 到 SerialManager
- **Location**: `sensor_calibrator/serial_manager.py`
- **Description**: 用 RingBuffer 替换 queue.Queue
- **Dependencies**: Task 4.1
- **Acceptance Criteria**:
  - `_read_serial_data()` 使用新缓冲区
  - 回调接口保持不变
  - 满队列处理逻辑正确（自动覆盖）
- **Validation**:
  - 运行完整数据采集测试，验证无丢包

---

## Sprint 5: 日志限流机制 (P2)

**Goal**: 防止高频日志输出导致 UI 卡顿

**Demo/Validation**:
- 数据流全速运行时 UI 响应流畅
- 日志输出频率受控（< 10 条/秒）
- 重要日志不丢失

---

### Task 5.1: 实现日志限流器
- **Location**: 新建 `sensor_calibrator/log_throttler.py`
- **Description**: 创建带缓冲和批量输出的日志限流器
- **Dependencies**: 无
- **Acceptance Criteria**:
  - `LogThrottler` 类支持时间窗口限流
  - 缓冲非紧急日志，定期批量输出
  - 错误级别日志立即输出（不过滤）
- **Validation**:
  ```python
  throttler = LogThrottler(interval_ms=100)
  for i in range(100):
      throttler.log(f"Message {i}")  # 应只输出约 10 次批量日志
  ```

---

### Task 5.2: 集成到主程序
- **Location**: `StableSensorCalibrator.py`
- **Description**: 在 `log_message()` 方法中集成限流器
- **Dependencies**: Task 5.1
- **Acceptance Criteria**:
  - 普通信息日志受限于流控制
  - 错误和警告日志优先输出
  - 日志区域更新频率降低
- **Validation**:
  - 启动数据流，观察日志输出频率
  - 测量 UI 响应延迟

---

## Sprint 6: 主程序模块化拆分 (P2)

**Goal**: 将 `StableSensorCalibrator.py` 拆分为更小的模块

**Demo/Validation**:
- 主程序行数从 2000+ 减少到 < 500
- 所有现有功能正常工作
- 新结构易于扩展和维护

---

### Task 6.1: 创建 UI 组件包结构
- **Location**: 新建 `sensor_calibrator/ui/`
- **Description**: 创建 UI 组件目录结构
- **Dependencies**: 无
- **Acceptance Criteria**:
  ```
  sensor_calibrator/ui/
  ├── __init__.py
  ├── control_panel.py      # 左侧控制面板
  ├── chart_panel.py        # 右侧图表区域
  ├── log_panel.py          # 日志区域
  └── menu_bar.py           # 菜单栏
  ```
- **Validation**:
  - 目录结构创建正确
  - `__init__.py` 导出所有组件

---

### Task 6.2: 迁移控制面板代码
- **Location**: `sensor_calibrator/ui/control_panel.py`
- **Description**: 提取左侧控制面板相关代码
- **Dependencies**: Task 6.1
- **Acceptance Criteria**:
  - 串口控制、校准按钮、网络配置等 UI 组件迁移完成
  - 事件回调通过接口传递
  - 原始代码中保留向后兼容的导入
- **Validation**:
  ```bash
  python -c "from sensor_calibrator.ui.control_panel import ControlPanel; print('OK')"
  ```

---

### Task 6.3: 重构主程序使用新模块
- **Location**: `StableSensorCalibrator.py`
- **Description**: 精简主程序，使用新 UI 组件
- **Dependencies**: Task 6.2
- **Acceptance Criteria**:
  - 主程序仅保留协调逻辑
  - UI 创建委托给各组件
  - 所有测试通过
- **Validation**:
  ```bash
  python -m pytest tests/ -v
  python StableSensorCalibrator.py  # 手动验证 GUI 正常
  ```

---

## Testing Strategy

### 单元测试
每个 Sprint 完成后运行：
```bash
python -m pytest tests/ -v --tb=short
```

### 性能测试
```bash
# Sprint 1-2 后
python performance_profile.py

# Sprint 3-4 后  
python -c "
import cProfile
import pstats
from sensor_calibrator import ChartManager, DataProcessor
# 性能测试代码
"
```

### 集成测试
```bash
# 完整功能测试
python -m pytest tests/test_integration.py -v

# 长时间运行测试（模拟 1 小时）
python tests/test_long_running.py
```

---

## Potential Risks & Gotchas

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| deque 修改后索引访问行为变化 | 高 | 全面测试 `get_latest()` 和切片操作 |
| RingBuffer 引入新并发 Bug | 中 | 增加压力测试，模拟高频数据流 |
| UI 模块化破坏现有回调 | 中 | 保持原方法名，仅内部委托 |
| 性能优化导致精度损失 | 低 | 对比优化前后计算结果 |
| 向后兼容性破坏 | 中 | 每个 Sprint 后运行完整测试套件 |

### 特别注意

1. **deque 切片行为**: `deque` 不支持 `[-n:]` 切片，需使用 `itertools.islice`
2. **线程安全**: RingBuffer 的实现必须正确处理竞态条件
3. **内存监控**: 每个 Sprint 后检查内存使用是否改善
4. **UI 响应**: 窗口移动/缩放时应保持流畅

---

## Rollback Plan

每个 Sprint 都有独立的回滚策略：

### Sprint 1-2 (数据优化)
```bash
# 如需回滚
git checkout sensor_calibrator/data_buffer.py
git checkout sensor_calibrator/data_processor.py
```

### Sprint 3 (图表优化)
```bash
git checkout sensor_calibrator/chart_manager.py
```

### Sprint 4 (队列优化)
```bash
# 切换回使用 Queue
git checkout sensor_calibrator/serial_manager.py
```

### Sprint 5 (日志优化)
```bash
# 禁用限流器（在 Config 中添加开关）
ENABLE_LOG_THROTTLING = False
```

### Sprint 6 (重构)
```bash
# 保留原文件作为备份
git checkout StableSensorCalibrator.py
# 删除 ui/ 目录
```

---

## Performance Metrics Checklist

完成每个 Sprint 后记录以下指标：

- [ ] **内存占用**: `tracemalloc` 峰值内存
- [ ] **CPU 占用**: 数据流运行时的 CPU 使用率
- [ ] **帧率稳定性**: 图表更新频率的方差
- [ ] **响应延迟**: 窗口移动/调整大小时的卡顿程度
- [ ] **测试通过率**: 所有单元测试通过

---

## Next Steps

1. **创建功能分支**: `git checkout -b performance-optimization`
2. **备份当前代码**: `git tag before-optimization`
3. **开始 Sprint 1**: 修改 `data_buffer.py`
4. **每日同步**: 每天结束时运行完整测试并提交

---

*计划创建完成。是否开始实施 Sprint 1？*
