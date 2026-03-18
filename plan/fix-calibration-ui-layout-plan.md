# Plan: 修复 Calibration UI 布局显示问题

**Generated**: 2026-03-18
**Estimated Complexity**: 低
**Estimated Time**: 1-2小时

---

## Overview

修复 Calibration 标签页中 Position Guide 区域的显示问题：
1. Canvas 2D 图显示不完整（边缘被截断）
2. 文字描述和提示文字显示不完整（被容器边界截断）

**解决方案**: 综合方案 - 调整 Canvas 尺寸并简化文字描述

---

## Prerequisites

- Python 3.8+ 环境
- tkinter 可用
- 现有代码库可运行

---

## Sprint 1: 调整 Canvas 尺寸和绘制坐标

**Goal**: 缩小 Canvas 并调整所有绘制元素坐标，确保内容在边界内完整显示

**Demo/Validation**:
- 运行应用，切换到 Calibration 标签页
- 验证 6 个位置的 2D 图都能完整显示（无截断）
- 验证重力指示、轴标签、文字都在 Canvas 边界内

### Task 1.1: 修改 Canvas 尺寸

- **Location**: `sensor_calibrator/ui_manager.py`
- **Description**: 缩小 Canvas 容器和画布尺寸
- **Changes**:
  - `canvas_frame`: 240x240 → 200x200
  - `cal_visual_canvas`: 220x220 → 180x180
- **Dependencies**: 无
- **Acceptance Criteria**:
  - Canvas 容器宽度 200px
  - Canvas 画布宽度 180px
- **Validation**: 查看 UI 布局

### Task 1.2: 调整 2D 可视化绘制坐标

- **Location**: `sensor_calibrator/ui/calibration_visualizer.py`
- **Description**: 调整所有绘制方法的坐标，适应新的 Canvas 尺寸
- **Changes**:
  - `_draw_top_view()`: cx, cy 从 100,100 改为 90,90
  - `_draw_side_view()`: cx, cy 从 100,100 改为 90,90
  - `_draw_front_view()`: cx, cy 从 100,100 改为 90,90
  - 所有文字标签位置相应内移
  - 箭头绘制坐标调整
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - 所有绘制元素在 180x180 Canvas 内完整显示
  - 文字标签不超出边界
  - 箭头指示清晰可见
- **Validation**: 运行应用，检查 6 个位置的显示效果

### Task 1.3: 优化重力指示显示

- **Location**: `sensor_calibrator/ui/calibration_visualizer.py`
- **Description**: 简化并优化重力方向的文字指示
- **Changes**:
  - 顶部文字位置调整（y=20）
  - 文字内容简化为短格式
  - 中心点/叉标记位置调整
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - 重力指示文字在 Canvas 顶部居中显示
  - 不超出上边界
- **Validation**: 检查 Z+ 和 Z- 位置的重力指示

---

## Sprint 2: 简化文字描述

**Goal**: 缩短 Position Guide 区域的文字描述，确保在有限空间内完整显示

**Demo/Validation**:
- 验证所有 6 个位置的文字描述都能完整显示
- 验证操作提示文字完整显示

### Task 2.1: 简化位置描述文字

- **Location**: `sensor_calibrator/ui/calibration_visualizer.py` - `POSITIONS` 列表
- **Description**: 将长描述改为简短清晰的格式
- **Changes**:
  - `description`: "X轴朝下（右侧面朝下）" → "右侧面朝下（X+）"
  - `description`: "X轴朝上（左侧面朝下）" → "左侧面朝下（X-）"
  - `description`: "Y轴朝下（前面朝下）" → "前面朝下（Y+）"
  - `description`: "Y轴朝上（后面朝下）" → "后面朝下（Y-）"
  - `description`: "Z轴朝下（顶面朝下）" → "顶面朝下（Z+）"
  - `description`: "Z轴朝上（底面朝下）" → "底面朝下（Z-）"
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 所有描述文字长度 ≤ 15 个字符
  - 保持清晰易懂
- **Validation**: 运行应用，查看文字显示

### Task 2.2: 简化操作提示文字

- **Location**: `sensor_calibrator/ui/calibration_visualizer.py` - `POSITIONS` 列表
- **Description**: 简化 tip 字段的操作提示
- **Changes**:
  - `tip`: "将传感器右侧朝下放置" → "右侧朝下"
  - `tip`: "将传感器左侧朝下放置" → "左侧朝下"
  - `tip`: "将传感器前面朝下放置" → "前面朝下"
  - `tip`: "将传感器后面朝下放置" → "后面朝下"
  - `tip`: "将传感器顶面朝下放置（电路板朝上）" → "顶面朝下"
  - `tip`: "将传感器底面朝下放置（电路板朝下）" → "底面朝下"
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - 所有提示文字长度 ≤ 10 个字符
  - 信息仍然明确
- **Validation**: 运行应用，查看提示文字

### Task 2.3: 调整文字区域布局

- **Location**: `sensor_calibrator/ui_manager.py`
- **Description**: 优化 Position Guide 右侧文字区域的布局
- **Changes**:
  - 减小 `padx` 从 10 改为 5
  - 减小 `wraplength` 从 280 改为 240（适应缩小后的空间）
  - 调整 `pady` 间距
- **Dependencies**: Task 1.1, Task 2.2
- **Acceptance Criteria**:
  - 文字区域与 Canvas 间距合适
  - 文字自动换行正常
- **Validation**: 检查整体布局效果

---

## Testing Strategy

1. **单元测试**:
   - 运行 `tests/test_calibration_ui_enhancement.py`
   - 确保 6 个测试通过

2. **视觉验证**:
   - 启动应用
   - 切换到 Calibration 标签页
   - 点击 Start，依次查看 6 个位置的显示效果
   - 验证：
     - [ ] Canvas 图形完整显示，无截断
     - [ ] 轴标签（X, Y, Z）清晰可见
     - [ ] 重力指示文字完整显示
     - [ ] 位置描述文字完整显示
     - [ ] 操作提示文字完整显示

3. **功能测试**:
   - 验证 Calibration 流程正常工作
   - 验证按钮功能正常

---

## Potential Risks & Gotchas

| 风险 | 影响 | 缓解策略 |
|------|------|---------|
| Canvas 缩小后图形过于拥挤 | 用户体验下降 | 保持关键元素大小，只调整位置 |
| 文字简化后信息不足 | 用户理解困难 | 保持括号内的轴向标记（X+, Y-等） |
| wraplength 调整后仍截断 | 显示问题未解决 | 根据实际效果进一步调整 |
| 不同分辨率/DPI显示差异 | 在某些设备上仍有问题 | 使用相对布局和自动换行 |

---

## Rollback Plan

如果修改后效果不佳，可以回滚：

```bash
git checkout HEAD -- sensor_calibrator/ui_manager.py
git checkout HEAD -- sensor_calibrator/ui/calibration_visualizer.py
```

或手动恢复原始尺寸：
- Canvas: 180x180 → 220x220
- 坐标: 90,90 → 100,100
- 文字: 恢复原始长描述

---

## Summary of Changes

**文件清单**:
1. `sensor_calibrator/ui_manager.py` - Canvas 尺寸和布局
2. `sensor_calibrator/ui/calibration_visualizer.py` - 绘制坐标和文字内容

**关键数值变更**:
| 项目 | 当前值 | 目标值 |
|------|--------|--------|
| canvas_frame 尺寸 | 240x240 | 200x200 |
| Canvas 尺寸 | 220x220 | 180x180 |
| 绘制中心点 | (100, 100) | (90, 90) |
| 描述文字长度 | ~20字 | ~10字 |
| 提示文字长度 | ~15字 | ~5字 |

---

*计划完成。确认后开始实施。*
