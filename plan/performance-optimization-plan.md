# SensorCalibrator 性能优化实施计划

**生成日期**: 2026-03-17
**预计复杂度**: 中等
**预计工期**: 2-3 天

## 概述

本计划针对 SensorCalibrator 项目的性能瓶颈进行系统性优化，分为 5 个阶段实施。每个阶段都是独立的，可以单独测试和回滚。

**核心优化目标**:
- 数据解析速度提升 2-5x
- 减少内存分配和 GC 压力
- 降低锁竞争，提高并发性能
- 整体 UI 响应性提升

---

## 前置条件

- [ ] 项目可以正常编译运行
- [ ] 有性能基准测试数据（建议先运行 `python -m cProfile -o profile.stats main.py` 采集基线）
- [ ] 所有测试用例通过
- [ ] 创建 feature/performance-optimization 分支

---

## Phase 1: 快速收益优化 (1-2 小时)

**目标**: 实施成本低、收益高的优化项
**验证**: 解析和数据处理速度明显提升

### Task 1.1: 替换 np.sqrt 为 math.sqrt
**文件**: `sensor_calibrator/data_processor.py`
**依赖**: 无
**描述**: 
- 在 `process_packet` 方法中，将 `np.sqrt()` 替换为 `math.sqrt()`
- 导入 `math` 模块

**修改代码**:
```python
# 修改前 (line 126-128)
gravity_mag = np.sqrt(
    mpu_accel[0] ** 2 + mpu_accel[1] ** 2 + mpu_accel[2] ** 2
)

# 修改后
import math
gravity_mag = math.sqrt(
    mpu_accel[0] ** 2 + mpu_accel[1] ** 2 + mpu_accel[2] ** 2
)
```

**验收标准**:
- [ ] `math` 模块已导入
- [ ] `np.sqrt` 不再在标量计算中使用
- [ ] 所有测试通过

**验证方法**:
```python
import timeit
# 对比两种方法的性能
timeit.timeit('np.sqrt(1**2 + 2**2 + 3**2)', globals={'np': np})
timeit.timeit('math.sqrt(1**2 + 2**2 + 3**2)', globals={'math': math})
```

---

### Task 1.2: 优化数据解析函数
**文件**: `sensor_calibrator/data_buffer.py`, `sensor_calibrator/data_processor.py`
**依赖**: 无
**描述**:
- 将 `parse_sensor_data` 中的循环解析改为列表推导式
- 使用 `partition` 或 `split` 优化

**修改代码**:
```python
# 修改前 (data_buffer.py:436-451)
parts = data_string.split(",")
if len(parts) >= 9:
    values = []
    for part in parts[:9]:
        try:
            values.append(float(part.strip()))
        except (ValueError, TypeError):
            values.append(0.0)

# 修改后
try:
    parts = data_string.split(",")
    if len(parts) >= 9:
        values = [
            float(part.strip()) if part.strip() else 0.0 
            for part in parts[:9]
        ]
        # 处理转换失败的值
        values = [v if not isinstance(v, str) else 0.0 for v in values]
```

**验收标准**:
- [ ] 解析速度提升 2x 以上
- [ ] 异常处理保持完整
- [ ] 所有测试通过

---

## Phase 2: 锁竞争优化 (2-3 小时)

**目标**: 减少 SensorDataBuffer 的锁持有时间
**验证**: 数据吞吐量和响应延迟改善

### Task 2.1: 分离数据复制和计算
**文件**: `sensor_calibrator/data_buffer.py`
**依赖**: Task 1.1, 1.2
**描述**:
- 在 `calculate_statistics` 和 `update_statistics` 中，最小化临界区
- 只在锁内进行数据复制，计算在锁外进行

**修改代码**:
```python
# update_statistics 方法 (line 339-379)
# 修改前: 计算在锁内进行
with self._lock:
    # ... 大量计算代码

# 修改后:
with self._lock:
    # 只复制数据
    window_size = min(Config.STATS_WINDOW_SIZE, len(self._time_data))
    start_idx = len(self._time_data) - window_size
    
    mpu_accel_data = [
        list(itertools.islice(self._mpu_accel_data[i], start_idx, None))
        for i in range(3)
    ]
    # ... 复制其他数据

# 锁外进行计算
stats = self._get_empty_stats()
for i in range(3):
    if len(mpu_accel_data[i]) >= window_size:
        stats["mpu_accel_mean"][i] = float(np.mean(mpu_accel_data[i]))
        stats["mpu_accel_std"][i] = float(np.std(mpu_accel_data[i]))
# ...
```

**验收标准**:
- [ ] 锁持有时间减少 80% 以上
- [ ] 数据一致性保持
- [ ] 所有测试通过

**验证方法**:
```python
# 添加计时装饰器测量锁持有时间
import time
from contextlib import contextmanager

@contextmanager
def timed_lock(lock, name):
    start = time.perf_counter()
    lock.acquire()
    try:
        yield
    finally:
        lock.release()
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{name}: {elapsed:.2f}ms")
```

---

### Task 2.2: 添加统计缓存机制
**文件**: `sensor_calibrator/data_buffer.py`
**依赖**: Task 2.1
**描述**:
- 添加缓存机制，避免重复计算相同窗口的统计信息
- 使用数据版本号或哈希判断是否需要重新计算

**修改代码**:
```python
class SensorDataBuffer:
    def __init__(self, max_points: Optional[int] = None) -> None:
        # ... 现有代码 ...
        
        # 新增缓存相关字段
        self._stats_cache: Dict[str, Any] = {}
        self._stats_version = 0  # 数据版本号
        self._stats_cache_version = -1  # 缓存版本号
    
    def add_sample(self, ...):
        with self._lock:
            # ... 现有代码 ...
            self._stats_version += 1  # 数据变化时增加版本号
    
    def update_statistics(self) -> Dict[str, Any]:
        # 检查缓存是否有效
        if self._stats_version == self._stats_cache_version:
            return self._stats_cache.copy()
        
        # ... 计算统计信息 ...
        
        # 更新缓存
        self._stats_cache = stats
        self._stats_cache_version = self._stats_version
        return stats.copy()
```

**验收标准**:
- [ ] 连续调用 `update_statistics` 返回缓存结果
- [ ] 数据更新后缓存失效
- [ ] 所有测试通过

---

## Phase 3: 内存和结构优化 (2-3 小时)

**目标**: 减少内存分配，优化对象结构
**验证**: 内存占用降低，GC 频率减少

### Task 3.1: 添加 __slots__ 到高频类
**文件**: 多个文件
**依赖**: 无
**描述**:
- 为高频创建的小型类添加 `__slots__`
- 重点优化数据相关的类

**文件列表**:
1. `sensor_calibrator/ring_buffer.py` - `RingBuffer`, `QueueAdapter`
2. `sensor_calibrator/log_throttler.py` - `LogThrottler`

**修改代码示例**:
```python
# ring_buffer.py
class RingBuffer(Generic[T]):
    __slots__ = ['_capacity', '_buffer', '_head', '_tail', '_size', '_lock']
    # ... 其余代码不变

class QueueAdapter:
    __slots__ = ['_buffer', 'maxsize']
    # ... 其余代码不变
```

**验收标准**:
- [ ] 内存占用减少 30% 以上（可用 `sys.getsizeof` 对比）
- [ ] 功能保持完整
- [ ] 所有测试通过

---

### Task 3.2: 优化数据访问属性
**文件**: `sensor_calibrator/data_buffer.py`
**依赖**: Task 2.2
**描述**:
- 当前每次访问属性都复制整个 deque
- 添加视图模式，延迟复制

**修改代码**:
```python
class SensorDataBuffer:
    def __init__(self, ...):
        # ... 现有代码 ...
        self._view_mode = False
        self._view_snapshot = None
    
    def get_view(self) -> 'DataView':
        """获取数据视图（不复制数据）"""
        with self._lock:
            return DataView(
                self._time_data,
                self._mpu_accel_data,
                self._mpu_gyro_data,
                self._adxl_accel_data,
                self._gravity_mag_data,
                self._lock
            )
    
    # 保留原有 copy 方法用于需要完整副本的场景
    def get_copy(self) -> Dict[str, Any]:
        """获取数据的完整副本"""
        with self._lock:
            return {
                'time': list(self._time_data),
                'mpu_accel': [list(d) for d in self._mpu_accel_data],
                # ...
            }

class DataView:
    """数据视图 - 只读访问，不复制数据"""
    __slots__ = ['_time', '_mpu_accel', '_mpu_gyro', '_adxl_accel', '_gravity', '_lock']
    
    def __init__(self, time_data, mpu_accel, mpu_gyro, adxl_accel, gravity, lock):
        self._time = time_data
        self._mpu_accel = mpu_accel
        self._mpu_gyro = mpu_gyro
        self._adxl_accel = adxl_accel
        self._gravity = gravity
        self._lock = lock
    
    def get_latest(self, n: int = 1):
        with self._lock:
            return {
                'time': list(itertools.islice(self._time, max(0, len(self._time) - n), None)),
                # ...
            }
```

**验收标准**:
- [ ] 添加 `DataView` 类
- [ ] `get_display_data` 可使用视图模式
- [ ] 所有测试通过

---

## Phase 4: 批量处理和预分配 (3-4 小时)

**目标**: 优化高频数据处理和校准流程
**验证**: 批量处理效率提升，校准数据收集更快

### Task 4.1: 实现批量数据处理
**文件**: `sensor_calibrator/app/application.py`
**依赖**: Task 1.1, 2.1
**描述**:
- 当前 `update_gui` 逐包处理数据
- 改为批量解析和批量追加

**修改代码**:
```python
def update_gui(self):
    # ... 前置检查 ...
    
    if hasattr(self, "data_queue"):
        # 批量获取数据
        batch = []
        while (not self.data_queue.empty() and 
               len(batch) < Config.MAX_GUI_UPDATE_BATCH):
            try:
                batch.append(self.data_queue.get_nowait())
            except:
                break
        
        if batch:
            self._process_batch(batch)
        
        # ... 后续更新 ...

def _process_batch(self, batch: List[str]):
    """批量处理数据"""
    # 批量解析
    parsed_data = []
    for data_string in batch:
        result = self.parse_sensor_data(data_string)
        if result[0] is not None:  # mpu_accel
            parsed_data.append(result)
    
    if not parsed_data:
        return
    
    # 初始化时间基准（只需一次）
    if self.data_processor.data_start_time is None:
        self.data_processor.data_start_time = time.time()
    
    # 批量追加到缓冲区（减少锁获取次数）
    start_time = self.data_processor.packet_count / self.data_processor.expected_frequency
    
    with self.data_processor._lock:  # 假设添加批量追加方法
        for i, (mpu_accel, mpu_gyro, adxl_accel) in enumerate(parsed_data):
            current_time = start_time + i / self.data_processor.expected_frequency
            # 直接访问内部 deque，避免重复获取锁
            self.data_processor._time_data.append(current_time)
            for j in range(3):
                self.data_processor._mpu_accel_data[j].append(mpu_accel[j])
                self.data_processor._mpu_gyro_data[j].append(mpu_gyro[j])
                self.data_processor._adxl_accel_data[j].append(adxl_accel[j])
            
            gravity_mag = math.sqrt(
                mpu_accel[0]**2 + mpu_accel[1]**2 + mpu_accel[2]**2
            )
            self.data_processor._gravity_mag_data.append(gravity_mag)
    
    self.data_processor.packet_count += len(parsed_data)
```

**验收标准**:
- [ ] 添加 `_process_batch` 方法
- [ ] 批量处理速度提升 2x 以上
- [ ] 锁获取次数减少
- [ ] 所有测试通过

---

### Task 4.2: 预分配校准样本数组
**文件**: `sensor_calibrator/calibration_workflow.py`
**依赖**: 无
**描述**:
- 当前使用 list 动态扩容存储校准样本
- 改为预分配 numpy 数组

**修改代码**:
```python
def _collect_calibration_data(self, position: int) -> None:
    """采集校准数据 - 预分配版本"""
    try:
        # 预分配数组（避免动态扩容）
        max_samples = self._calibration_samples
        mpu_accel_samples = np.zeros((max_samples, 3))
        mpu_gyro_samples = np.zeros((max_samples, 3))
        adxl_accel_samples = np.zeros((max_samples, 3))
        
        start_time = time.time()
        samples_collected = 0
        
        while (samples_collected < max_samples and self._is_calibrating):
            try:
                data_string = self.data_queue.get(timeout=Config.QUICK_SLEEP)
                
                if "parse_sensor_data" in self.callbacks:
                    mpu_accel, mpu_gyro, adxl_accel = self.callbacks[
                        "parse_sensor_data"
                    ](data_string)
                    
                    if mpu_accel and mpu_gyro and adxl_accel:
                        mpu_accel_samples[samples_collected] = mpu_accel
                        mpu_gyro_samples[samples_collected] = mpu_gyro
                        adxl_accel_samples[samples_collected] = adxl_accel
                        samples_collected += 1
                
                if time.time() - start_time > 10:
                    self._log_message("Timeout: Stopping data collection")
                    break
                    
            except queue.Empty:
                time.sleep(Config.QUICK_SLEEP)
                continue
            except Exception as e:
                self._log_message(f"Error collecting calibration data: {e}")
                continue
        
        # 使用切片获取实际收集的样本
        if samples_collected > 0:
            mpu_accel_samples = mpu_accel_samples[:samples_collected]
            mpu_gyro_samples = mpu_gyro_samples[:samples_collected]
            adxl_accel_samples = adxl_accel_samples[:samples_collected]
            
            # 计算平均值（使用 numpy 向量化操作）
            mpu_accel_avg = np.mean(mpu_accel_samples, axis=0)
            mpu_gyro_avg = np.mean(mpu_gyro_samples, axis=0)
            adxl_accel_avg = np.mean(adxl_accel_samples, axis=0)
            
            mpu_accel_std = np.std(mpu_accel_samples, axis=0)
            adxl_accel_std = np.std(adxl_accel_samples, axis=0)
            
            # ... 后续处理 ...
```

**验收标准**:
- [ ] 预分配数组实现
- [ ] 校准采集速度提升
- [ ] 内存分配次数减少
- [ ] 所有测试通过

---

## Phase 5: 代码清理和回调优化 (1-2 小时)

**目标**: 修复代码异味，优化高频调用路径
**验证**: 代码简洁，回调调用更快

### Task 5.1: 清理重复导入
**文件**: `sensor_calibrator/calibration_workflow.py`
**依赖**: 无
**描述**:
- 移除重复的导入语句
- 简化导入逻辑

**修改代码**:
```python
# 修改前 (line 18-32)
_calibration_functions_available = False
_import_error_message = None

try:
    scripts_path = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_path))
    from calibration import compute_six_position_calibration, compute_gyro_offset
    _calibration_functions_available = True
except (ImportError, ModuleNotFoundError) as e:
    _import_error_message = str(e)
    compute_six_position_calibration = None
    compute_gyro_offset = None
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))
from calibration import compute_six_position_calibration, compute_gyro_offset

# 修改后
try:
    scripts_path = Path(__file__).parent.parent / "scripts"
    if str(scripts_path) not in sys.path:
        sys.path.insert(0, str(scripts_path))
    from calibration import compute_six_position_calibration, compute_gyro_offset
    _calibration_functions_available = True
except (ImportError, ModuleNotFoundError) as e:
    _import_error_message = str(e)
    compute_six_position_calibration = None
    compute_gyro_offset = None
    _calibration_functions_available = False
```

**验收标准**:
- [ ] 重复导入已移除
- [ ] 导入逻辑清晰
- [ ] 所有测试通过

---

### Task 5.2: 缓存回调签名检查结果
**文件**: `sensor_calibrator/serial_manager.py`
**依赖**: 无
**描述**:
- `_log_message` 每次调用都检查回调签名
- 缓存检查结果，避免重复 inspect

**修改代码**:
```python
def __init__(self, callbacks: dict):
    # ... 现有代码 ...
    
    # 新增：缓存回调签名检查结果
    self._callback_signatures: Dict[str, Any] = {}
    self._check_callback_signatures()

def _check_callback_signatures(self):
    """预检查所有回调函数的签名"""
    import inspect
    
    for name, callback in self.callbacks.items():
        if callable(callback):
            sig = inspect.signature(callback)
            param_count = len([
                p for p in sig.parameters.values()
                if p.default is inspect.Parameter.empty 
                or p.default != inspect.Parameter.empty
            ])
            self._callback_signatures[name] = param_count

def _log_message(self, message: str, level: str = "INFO") -> None:
    """记录日志（通过回调）- 优化版本"""
    if self.callbacks.get('log_message') is not None:
        callback = self.callbacks['log_message']
        param_count = self._callback_signatures.get('log_message', 1)
        
        if level != "INFO" and param_count >= 2:
            callback(message, level)
        else:
            callback(message)
```

**验收标准**:
- [ ] 签名检查只执行一次
- [ ] `_log_message` 调用性能提升
- [ ] 所有测试通过

---

## 测试策略

### 每阶段验证清单

1. **单元测试**:
```bash
python -m pytest tests/ -v
```

2. **性能基准**:
```bash
# 基线测试
python -m cProfile -o baseline.prof main.py

# 优化后测试
python -m cProfile -o optimized.prof main.py

# 对比分析
python -m pstats baseline.prof
# 在 pstats 中: sort cumtime, stats 20
```

3. **内存分析**:
```bash
python -m memory_profiler sensor_calibrator/data_buffer.py
```

### 集成测试场景

1. 长时间运行测试（30分钟）
2. 高频数据采集测试（100Hz）
3. 校准流程完整测试
4. 内存泄漏检测

---

## 潜在风险和注意事项

### 风险 1: 锁优化引入竞态条件
**缓解措施**:
- 严格测试多线程场景
- 使用 `threading.Lock` 的上下文管理器
- 添加断言验证数据一致性

### 风险 2: 缓存机制导致数据不一致
**缓解措施**:
- 版本号机制确保缓存失效
- 提供强制刷新接口
- 添加缓存命中率监控

### 风险 3: __slots__ 限制属性动态添加
**缓解措施**:
- 检查是否有动态添加属性的代码
- 保留 `__dict__` 备用方案
- 充分测试所有代码路径

### 风险 4: 批量处理增加延迟
**缓解措施**:
- 设置批量大小上限
- 添加超时机制
- 保留逐包处理回退方案

---

## 回滚计划

每个 Phase 都是独立的 Git commit，可以单独回滚：

```bash
# 回滚 Phase 4
git revert <phase-4-commit-hash>

# 回滚所有优化
git checkout main
```

---

## 实施建议

1. **按 Phase 顺序实施**，每个 Phase 完成后进行充分测试
2. **代码审查**，确保改动符合项目规范
3. **性能监控**，记录每个优化项的实际效果
4. **文档更新**，更新相关代码注释

---

## 预期成果

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 数据解析速度 | 基线 | +200-500% | 2-5x |
| 内存占用 | 基线 | -30% | 30% |
| 锁持有时间 | 基线 | -80% | 80% |
| UI 更新频率 | 10 FPS | 15-20 FPS | 50-100% |
| 校准采集时间 | 基线 | -20% | 20% |
