# Calibration Block UI 优化计划

**生成日期**: 2026-03-18
**预计复杂度**: 中等
**预计工期**: 3-5 天

---

## 概述

优化六位置校准界面的用户体验，通过添加3D可视化指引、增强实时反馈、数据质量提示和自动引导流程，使校准操作更加直观和可靠。

## 当前问题分析

1. **缺乏视觉指引**: 用户需要通过文字理解传感器放置方位，容易混淆
2. **反馈不足**: 采集过程中不知道当前进度和数据质量
3. **操作不连贯**: 每个位置需要手动点击，流程不够顺畅
4. **数据质量不可见**: 用户无法判断采集的数据是否稳定可靠

---

## Sprint 1: 2D可视化指引系统

**目标**: 实现传感器方位的轻量级2D可视化显示
**演示验证**: 
- 打开Calibration标签页能看到2D示意图
- 当前位置对应的轴以高亮显示
- 示意图随位置切换自动更新
- 保持10 FPS性能不受影响

### Task 1.1: 创建 CalibrationVisualizer2D 组件
- **位置**: `sensor_calibrator/ui/calibration_visualizer.py` (新建)
- **描述**: 使用 tkinter Canvas 创建轻量级2D传感器示意图
- **依赖**: 无
- **功能**:
  - 绘制2D坐标系投影 (X-红, Y-绿, Z-蓝)
  - 绘制传感器矩形/立方体投影
  - 高亮当前需要朝下的轴（加粗+闪烁）
  - 显示重力方向箭头（↓）
  - 文字提示当前方位
- **性能优化**:
  - 使用 Canvas 而非 matplotlib，更轻量
  - 静态元素预绘制，只更新高亮部分
  - 不占用 blit 资源
- **验收标准**:
  - 2D图形能正确显示6种方位
  - 渲染不占用主线程超过 5ms
  - 10 FPS 图表更新不受影响
- **验证**: 
  ```python
  # 测试代码
  viz = CalibrationVisualizer2D(canvas)
  viz.set_position(0)  # 显示 +X 朝下
  viz.set_position(4)  # 显示 +Z 朝下
  ```

### Task 1.2: 集成2D可视化到校准标签页
- **位置**: `sensor_calibrator/ui_manager.py`, `_setup_calibration_tab()`
- **描述**: 在Calibration标签页添加2D显示区域
- **依赖**: Task 1.1
- **修改内容**:
  - 在进度显示下方添加2D可视化卡片（约 200x200 像素）
  - 使用 tk.Canvas 替代 FigureCanvasTkAgg
  - 实现位置切换时更新2D显示
- **验收标准**:
  - 2D显示区域与现有UI风格一致
  - 位置切换时示意图实时更新
  - 窗口大小变化时自适应
  - CPU占用增加 < 5%
- **验证**: 手动测试6个位置的2D显示是否正确

---

## Sprint 2: 增强实时反馈系统

**目标**: 提供采集过程的实时进度和状态反馈
**演示验证**:
- 点击Capture后显示实时进度条
- 显示已采集样本数和剩余时间
- 采集完成后有视觉提示

### Task 2.1: 创建实时进度显示组件
- **位置**: `sensor_calibrator/ui/calibration_progress.py` (新建)
- **描述**: 实现采集进度实时监控UI
- **依赖**: 无
- **功能**:
  - 圆形或条形进度条显示
  - 实时样本计数器 (current/total)
  - 预计剩余时间显示
  - 采集状态文字 (准备/采集中/完成/超时)
- **验收标准**:
  - 进度更新频率 >= 10 FPS
  - UI响应流畅，不卡顿
  - 支持取消/中断操作
- **验证**: 
  ```python
  # 模拟采集测试
  progress.start_collection(target=100)
  for i in range(100):
      progress.update(i+1)
      time.sleep(0.01)
  progress.complete()
  ```

### Task 2.2: 修改采集流程以支持实时回调
- **位置**: `sensor_calibrator/calibration_workflow.py`
- **描述**: 修改 `_collect_calibration_data()` 添加进度回调
- **依赖**: Task 2.1
- **修改内容**:
  - 添加 `on_progress_callback` 参数
  - 每采集10个样本触发一次回调
  - 添加采集开始/完成/错误的事件通知
- **关键代码**:
  ```python
  def _collect_calibration_data(self, position: int, 
                                progress_callback=None,
                                status_callback=None):
      # 每10个样本报告进度
      if samples_collected % 10 == 0 and progress_callback:
          progress_callback(samples_collected, max_samples)
  ```
- **验收标准**:
  - 回调函数正确触发
  - 不影响采集性能
  - 支持空回调（向后兼容）

### Task 2.3: 更新位置状态指示器
- **位置**: `sensor_calibrator/ui_manager.py`
- **描述**: 改进6位置状态显示，添加颜色和动画
- **依赖**: Task 2.1, Task 2.2
- **修改内容**:
  - ○ 未开始 → 灰色
  - ◐ 采集中 → 黄色动画
  - ● 已完成 → 绿色
  - ✗ 失败 → 红色
- **验收标准**:
  - 状态变化清晰可见
  - 动画效果流畅
  - 颜色符合UI主题

---

## Sprint 3: 数据质量指示器

**目标**: 实时显示采集数据的质量指标
**演示验证**:
- 采集过程中显示标准差
- 数据稳定性达到阈值时提示
- 数据质量差时警告用户

### Task 3.1: 实现数据质量计算器
- **位置**: `sensor_calibrator/calibration_quality.py` (新建)
- **描述**: 实时计算数据质量指标
- **依赖**: 无
- **功能**:
  - 计算滑动窗口标准差
  - 计算数据方差和噪声水平
  - 评估数据稳定性 (稳定/波动/异常)
  - 提供质量评分 (0-100)
- **关键算法**:
  ```python
  def calculate_quality_score(samples, window_size=20):
      """
      质量评分标准:
      - 90-100: 优秀 (标准差 < 0.01)
      - 70-89:  良好 (标准差 < 0.05)
      - 50-69:  一般 (标准差 < 0.1)
      - < 50:   差 (标准差 >= 0.1)
      """
  ```
- **验收标准**:
  - 计算准确，与事后统计一致
  - 计算开销低，不影响采集
  - 提供清晰的质量等级

### Task 3.2: 创建数据质量显示组件
- **位置**: `sensor_calibrator/ui/quality_indicator.py` (新建)
- **描述**: 设计数据质量可视化组件
- **依赖**: Task 3.1
- **功能**:
  - 三色LED式指示器 (绿/黄/红)
  - 实时标准差数值显示
  - 稳定性文字提示
  - 质量评分条
- **UI布局**:
  ```
  ┌─ Data Quality ───────────┐
  │  [●] Excellent    85/100 │
  │  σ: 0.003  Stable        │
  └──────────────────────────┘
  ```
- **验收标准**:
  - 颜色变化及时准确
  - 数值刷新频率 >= 5 FPS
  - 阈值可配置

### Task 3.3: 集成数据质量反馈到采集流程
- **位置**: `sensor_calibrator/calibration_workflow.py`
- **描述**: 在采集中实时计算和显示数据质量
- **依赖**: Task 3.1, Task 3.2
- **修改内容**:
  - 在 `_collect_calibration_data()` 中添加质量计算
  - 每20个样本更新一次质量显示
  - 质量差时自动延长采集时间
- **验收标准**:
  - 质量指示器正确反映数据状态
  - 采集时间根据质量自动调整
  - 低质量数据有警告提示

---

## Sprint 4: 自动引导流程

**目标**: 实现一键式自动引导校准流程
**演示验证**:
- 点击Start后系统自动引导完成6个位置
- 每个位置采集完成自动提示下一个
- 支持暂停和重新开始

### Task 4.1: 创建引导状态机
- **位置**: `sensor_calibrator/calibration_guide.py` (新建)
- **描述**: 实现校准流程的状态管理
- **依赖**: 无
- **状态定义**:
  ```python
  class GuideState:
      IDLE = "idle"           # 等待开始
      PROMPT = "prompt"       # 提示放置传感器
      READY = "ready"         # 等待用户确认
      COLLECTING = "collecting" # 采集中
      REVIEW = "review"       # 采集完成，等待确认
      COMPLETE = "complete"   # 全部完成
  ```
- **功能**:
  - 管理6位置的自动流转
  - 支持暂停/继续/跳过
  - 记录每个位置的重试次数
- **验收标准**:
  - 状态转换正确无误
  - 支持用户中断和恢复
  - 提供清晰的状态查询接口

### Task 4.2: 实现语音/声音提示（可选）
- **位置**: `sensor_calibrator/ui/audio_feedback.py` (新建)
- **描述**: 添加声音反馈增强引导效果
- **依赖**: Task 4.1
- **功能**:
  - 采集开始/完成提示音
  - 位置切换语音提示
  - 错误警告音
- **验收标准**:
  - 声音清晰可辨
  - 支持静音选项
  - 不干扰正常操作

### Task 4.3: 集成自动引导到UI
- **位置**: `sensor_calibrator/ui_manager.py`, `sensor_calibrator/app/callback_groups.py`
- **描述**: 在界面上实现自动引导控制
- **依赖**: Task 4.1, Sprint 1-3
- **修改内容**:
  - 添加 "Auto Guide" 复选框开关
  - 采集完成自动进入下一步（延迟1秒）
  - 显示下一个位置的预览
  - 添加暂停/继续按钮
- **新的按钮布局**:
  ```
  [Start] [Auto Guide ☑] [Capture] [Pause] [Reset]
  ```
- **性能考虑**:
  - 自动切换使用 `after()` 而非线程，避免同步问题
  - 延迟时间可配置，给用户准备时间
  - 每个位置最大停留时间限制（防止无限等待）
- **验收标准**:
  - 自动模式流程顺畅，不卡顿
  - 手动模式不受影响
  - 随时可以切换模式
  - 10 FPS 性能不受影响

---

## Sprint 5: 整合测试与优化

**目标**: 确保所有组件协同工作，优化性能
**演示验证**:
- 完整运行一次6位置校准
- 验证所有反馈机制正常工作
- 性能测试无卡顿

### Task 5.1: 创建集成测试
- **位置**: `tests/test_calibration_ui.py` (新建)
- **描述**: 测试校准UI的完整流程
- **依赖**: Sprint 1-4
- **测试内容**:
  - 3D可视化正确性
  - 进度更新准确性
  - 数据质量计算正确性
  - 状态机转换正确性
- **验收标准**:
  - 测试覆盖率 >= 80%
  - 所有测试通过
  - 模拟传感器数据测试

### Task 5.2: 性能优化
- **位置**: 多个文件
- **描述**: 优化渲染和计算性能
- **依赖**: Sprint 1-4
- **优化点**:
  - 3D图形使用blit缓存
  - 减少不必要的重绘
  - 使用线程池处理计算
- **验收标准**:
  - UI刷新率 >= 30 FPS
  - CPU占用增加 < 10%
  - 内存占用稳定

### Task 5.3: 用户文档更新
- **位置**: `AGENTS.md`, `README.md`
- **描述**: 更新文档说明新的校准流程
- **依赖**: Sprint 1-4
- **内容**:
  - 新的操作步骤说明
  - 3D视图解读指南
  - 数据质量指标说明
  - 故障排除指南

---

## 技术实现细节

### 2D可视化方案（轻量级）

```python
# sensor_calibrator/ui/calibration_visualizer.py
import tkinter as tk

class CalibrationVisualizer2D:
    """2D传感器方位可视化 - 轻量级实现"""
    
    POSITIONS = [
        {'name': '+X', 'down_axis': 'X+', 'view': 'side', 'highlight': 'right'},
        {'name': '-X', 'down_axis': 'X-', 'view': 'side', 'highlight': 'left'},
        {'name': '+Y', 'down_axis': 'Y+', 'view': 'front', 'highlight': 'up'},
        {'name': '-Y', 'down_axis': 'Y-', 'view': 'front', 'highlight': 'down'},
        {'name': '+Z', 'down_axis': 'Z+', 'view': 'top', 'highlight': 'out'},  # 俯视图
        {'name': '-Z', 'down_axis': 'Z-', 'view': 'top', 'highlight': 'in'},   # 仰视图
    ]
    
    COLORS = {
        'X': '#ff4444',  # 红色
        'Y': '#44ff44',  # 绿色
        'Z': '#4444ff',  # 蓝色
        'sensor': '#666666',
        'gravity': '#ff9900',
        'text': '#333333'
    }
    
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.current_idx = 0
        self.width = 200
        self.height = 200
        
    def set_position(self, position_idx: int):
        """设置当前显示的位置"""
        self.current_idx = position_idx
        self._draw()
        
    def _draw(self):
        """绘制2D示意图 - 优化：只更新必要元素"""
        self.canvas.delete("all")
        pos = self.POSITIONS[self.current_idx]
        
        # 绘制传感器立方体投影
        if pos['view'] == 'top':
            self._draw_top_view(pos)
        elif pos['view'] == 'side':
            self._draw_side_view(pos)
        else:  # front
            self._draw_front_view(pos)
            
    def _draw_top_view(self, pos):
        """俯视图 - Z轴相关"""
        # 绘制传感器矩形（顶面）
        self.canvas.create_rectangle(60, 60, 140, 140, 
                                     fill='#888888', outline='black', width=2)
        # X轴（水平）
        self.canvas.create_line(60, 100, 140, 100, fill=self.COLORS['X'], width=3)
        # Y轴（垂直）
        self.canvas.create_line(100, 60, 100, 140, fill=self.COLORS['Y'], width=3)
        # Z轴（点/圆圈表示方向）
        self.canvas.create_oval(90, 90, 110, 110, fill=self.COLORS['Z'])
        # 重力箭头
        if pos['down_axis'] == 'Z+':
            self.canvas.create_text(100, 30, text="↓ 重力", fill=self.COLORS['gravity'], font=('Arial', 10, 'bold'))
            self.canvas.create_text(100, 170, text="朝上 (+Z)", fill=self.COLORS['Z'])
        else:
            self.canvas.create_text(100, 170, text="↑ 重力", fill=self.COLORS['gravity'], font=('Arial', 10, 'bold'))
            self.canvas.create_text(100, 30, text="朝下 (-Z)", fill=self.COLORS['Z'])
```

### 实时进度回调设计

```python
# 在 CalibrationWorkflow 中
class CalibrationWorkflow:
    def __init__(self, ...):
        self.callbacks = {
            'on_progress': None,      # 进度更新 (current, total)
            'on_quality_update': None, # 质量更新 (score, std)
            'on_position_complete': None,  # 位置完成 (position_idx)
            'on_state_change': None,   # 状态变化 (old_state, new_state)
        }
```

### 性能保证措施（10 FPS）

```python
# sensor_calibrator/calibration_workflow.py

class CalibrationWorkflow:
    # 性能优化参数
    PROGRESS_UPDATE_INTERVAL = 10  # 每10个样本更新一次进度
    QUALITY_UPDATE_INTERVAL = 20   # 每20个样本更新一次质量
    
    def _collect_calibration_data(self, position: int):
        """采集数据 - 优化版本"""
        samples_collected = 0
        last_progress_update = 0
        last_quality_update = 0
        
        while samples_collected < max_samples:
            # ... 采集样本 ...
            samples_collected += 1
            
            # 批量更新进度，减少UI刷新频率
            if (samples_collected - last_progress_update >= self.PROGRESS_UPDATE_INTERVAL 
                and self.callbacks.get('on_progress')):
                self.callbacks['on_progress'](samples_collected, max_samples)
                last_progress_update = samples_collected
            
            # 批量更新质量
            if (samples_collected - last_quality_update >= self.QUALITY_UPDATE_INTERVAL
                and self.callbacks.get('on_quality_update')):
                quality_score = self._calculate_quality_score(samples_collected)
                self.callbacks['on_quality_update'](quality_score)
                last_quality_update = samples_collected
```

### 线程安全设计

```python
# sensor_calibrator/ui/calibration_updater.py
import tkinter as tk
from typing import Callable

class UICalibrationUpdater:
    """线程安全的UI更新器 - 确保10 FPS不受影响"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.pending_updates = []
        self.update_scheduled = False
        
    def schedule_update(self, update_func: Callable):
        """调度UI更新到主线程"""
        self.pending_updates.append(update_func)
        
        if not self.update_scheduled:
            self.update_scheduled = True
            # 使用 after(0) 尽快执行，但不阻塞
            self.root.after(0, self._process_updates)
    
    def _process_updates(self):
        """批量处理待更新项"""
        self.update_scheduled = False
        
        # 一次性处理所有待更新项
        for update_func in self.pending_updates:
            try:
                update_func()
            except Exception as e:
                print(f"UI update error: {e}")
        
        self.pending_updates.clear()
```

### 数据质量阈值配置

```python
# sensor_calibrator/config.py
class CalibrationConfig:
    # 数据质量阈值
    QUALITY_THRESHOLDS = {
        'excellent': {'std': 0.01, 'score': 90},
        'good': {'std': 0.05, 'score': 70},
        'fair': {'std': 0.1, 'score': 50},
        'poor': {'std': float('inf'), 'score': 0},
    }
    
    # 自动采集设置
    AUTO_GUIDE_ENABLED = True
    AUTO_ADVANCE_DELAY = 1.0  # 采集完成后自动进入下一步的延迟
    MIN_QUALITY_FOR_AUTO_ADVANCE = 70  # 自动进入下一步的最小质量分
```

---

## 测试策略

### 单元测试
- 3D可视化位置计算正确性
- 数据质量评分算法准确性
- 状态机转换逻辑

### 集成测试
- 完整6位置校准流程
- 自动引导模式测试
- 手动/自动切换测试

### 用户测试清单
- [ ] 首次用户能否不看文档完成校准
- [ ] 3D视图是否能正确理解方位
- [ ] 数据质量提示是否清晰有用
- [ ] 自动引导流程是否顺畅

---

## 潜在风险与解决方案

| 风险 | 影响 | 解决方案 |
|-----|------|---------|
| 3D渲染性能问题 | UI卡顿 | 使用blit缓存，降低渲染频率 |
| 数据质量计算延迟 | 影响采集实时性 | 使用滑动窗口，异步计算 |
| 自动引导干扰用户 | 体验差 | 提供暂停和手动模式 |
| matplotlib兼容性问题 | 某些系统无法显示 | 提供降级方案（2D示意图） |
| 线程安全问题 | 崩溃或数据错误 | 使用锁保护共享状态 |

---

## 回滚计划

如需回滚：
1. 保留新代码，添加功能开关
2. 默认使用旧版界面
3. 通过配置启用新功能
4. 逐步替换，确保稳定性

---

## 文件清单

### 新建文件
- `sensor_calibrator/ui/calibration_visualizer.py` - 3D可视化
- `sensor_calibrator/ui/calibration_progress.py` - 进度显示
- `sensor_calibrator/ui/quality_indicator.py` - 质量指示器
- `sensor_calibrator/calibration_quality.py` - 质量计算
- `sensor_calibrator/calibration_guide.py` - 引导状态机
- `sensor_calibrator/ui/audio_feedback.py` - 声音反馈
- `tests/test_calibration_ui.py` - 集成测试

### 修改文件
- `sensor_calibrator/ui_manager.py` - 集成新组件
- `sensor_calibrator/calibration_workflow.py` - 添加回调
- `sensor_calibrator/config.py` - 添加配置
- `sensor_calibrator/app/callback_groups.py` - 添加回调

---

*计划完成。请审查并提出修改意见。*
