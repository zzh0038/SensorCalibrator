# SensorCalibrator 性能优化计划

## 问题诊断总结

通过代码审查，发现以下导致卡顿的主要原因：

### 1. **图表频繁全量重绘（最严重）**
- `update_charts()` 每 50ms 被调用一次
- 每次都调用 `canvas.draw_idle()` 重绘整个 matplotlib 画布
- 4个子图（MPU加速度、ADXL加速度、MPU陀螺仪、重力）同时重绘
- **移动窗口时卡顿原因**：每次窗口位置变化都会触发重绘

### 2. **GUI更新频率过高**
- `UPDATE_INTERVAL_MS = 50` (20 FPS)，过于频繁
- 每次更新处理最多100个数据包，可能阻塞主线程
- 统计信息和图表同步更新，计算量大

### 3. **未使用增量绘制技术**
- 没有使用 matplotlib 的 `blit` 技术只更新变化的部分
- 每次更新都重新设置所有线条数据，即使数据变化很小

### 4. **Y轴范围计算效率低**
- `adjust_y_limits()` 每次都要遍历大量数据点找 min/max
- 每次重新计算 Y 轴范围，没有缓存机制

### 5. **统计信息更新过于频繁**
- 每次 GUI 更新都重新计算统计信息
- 标准差/均值计算涉及大量浮点运算

---

## 优化计划

### Phase 1: 图表渲染优化（预期提升 60-80%）

#### 1.1 实现 Blit 增量绘制
```python
# 新增变量
self._blit_cache = None          # 缓存背景
self._blit_axes = []             # 需要刷新的axes
self._blit_lines = []            # 需要刷新的线条
```

- 初始化时缓存静态背景
- 只更新变化的线条，不 redraw 整个 canvas
- 使用 `canvas.blit()` 代替 `draw_idle()`

#### 1.2 降低更新频率
```python
# config.py 修改
UPDATE_INTERVAL_MS = 100         # 50 -> 100 (10 FPS)
CHART_UPDATE_INTERVAL = 0.1      # 0.05 -> 0.1 (10 FPS)
```

#### 1.3 添加数据变化检测
- 只有当新数据到达时才触发图表更新
- 避免空转时的无效重绘

---

### Phase 2: 数据处理优化（预期提升 20-30%）

#### 2.1 数据采样降频显示
```python
# 新增配置
CHART_DECIMATION_FACTOR = 2      # 每2个点显示1个
```
- 当数据点超过阈值时使用采样显示
- 保持视觉效果同时减少绘制负载

#### 2.2 Y轴范围优化
```python
# 新增变量
self._last_y_limits = {}         # 缓存上次的Y轴范围
self._y_limit_update_interval = 0.5  # Y轴更新间隔
```
- 减少 Y 轴范围计算频率（每 0.5 秒一次）
- 使用增量更新，只有变化超过阈值才调整

#### 2.3 统计信息更新分离
- 统计信息更新改为独立定时器
- 降低统计更新频率到 1 秒一次

---

### Phase 3: 窗口交互优化（预期提升 40-50% 移动时）

#### 3.1 窗口移动检测暂停
```python
# 新增变量
self._window_moving = False      # 窗口是否正在移动
self._window_move_timer = None   # 移动检测定时器
```
- 检测窗口移动/调整大小事件
- 移动期间暂停图表更新，移动结束后恢复
- 使用 `<Configure>` 事件监听窗口变化

#### 3.2 响应式布局优化
- 图表区域使用更高效的布局策略
- 减少不必要的 `grid_propagate` 检查

---

### Phase 4: 内存和CPU优化（预期提升 10-20%）

#### 4.1 数据切片优化
```python
# 使用 collections.deque 替代 list
from collections import deque
self.time_data = deque(maxlen=MAX_DATA_POINTS)
```
- 使用 `deque` 自动管理数据长度，避免频繁切片

#### 4.2 Numpy 向量化计算
- 统计计算使用 numpy 向量化操作
- 避免 Python 循环计算均值/标准差

#### 4.3 日志输出限流
- 日志更新添加时间间隔控制
- 避免日志刷屏导致的 UI 卡顿

---

## 预期性能提升

| 场景 | 当前表现 | 优化后预期 | 提升幅度 |
|------|---------|-----------|---------|
| 窗口移动 | 明显卡顿 | 流畅 | 70-80% |
| 数据流运行时 | 帧率不稳定 | 稳定 10 FPS | 50% |
| CPU占用 | 高（单核满载） | 中等 | 40-50% |
| 内存占用 | 持续增长风险 | 稳定 | 20-30% |

---

## 实施优先级

1. **高优先级** - Phase 1（图表渲染优化）
   - 这是卡顿的主要原因，修复后效果最明显

2. **高优先级** - Phase 3（窗口交互优化）
   - 直接解决用户反馈的"移动窗口卡顿"问题

3. **中优先级** - Phase 2（数据处理优化）
   - 进一步降低 CPU 占用

4. **低优先级** - Phase 4（内存和CPU优化）
   - 锦上添花，长期稳定性优化

---

## 回滚策略

每项优化都应：
1. 保留原始代码注释
2. 使用配置开关控制
3. 独立测试验证

```python
# config.py 添加优化开关
ENABLE_BLIT_OPTIMIZATION = True
ENABLE_WINDOW_MOVE_PAUSE = True
ENABLE_DATA_DECIMATION = True
```
