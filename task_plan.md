# Task Plan: SensorCalibrator 项目

## Goal
为 SensorCalibrator 传感器校准软件添加两个坐标模式按钮：局部坐标模式(SS:2)和整体坐标模式(SS:3)。

## Current Phase
Phase 1

## Phases

### Phase 1: 需求分析与探索
- [x] 明确用户具体需求
- [x] 分析现有代码结构和依赖关系
- [x] 识别潜在问题和改进点
- [x] 将发现记录到 findings.md
- **Status:** complete

### Phase 2: 规划与设计
- [x] 确定技术方案：在 Commands 区域添加两个按钮
- [x] 设计代码结构：添加两个发送命令的方法
- [x] 记录决策和理由
- **Status:** complete

### Phase 3: 实现
- [x] 在 UI 的 Commands 区域添加两个按钮
- [x] 实现发送 SS:2 和 SS:3 命令的方法
- [x] 绑定按钮事件
- **Status:** complete

### Phase 3.5: 代码重构
- [x] 提取通用方法 `set_coordinate_mode()`
- [x] 简化 `set_local_coordinate_mode()` 和 `set_global_coordinate_mode()`
- [x] 添加类型注解
- [x] 细化异常处理（区分 SerialException 和通用 Exception）
- **Status:** complete

### Phase 4: 测试与验证
- [x] 验证所有需求已满足
- [x] Python 语法检查通过
- [x] 代码逻辑验证完成
- **Status:** complete

### Phase 5: 交付
- [x] 审查所有输出文件
- [x] 确保交付物完整
- [x] 向用户交付
- **Status:** complete

## Key Questions
1. 用户需要添加什么新功能？
2. 是否需要修复现有问题？
3. 是否有特定的代码重构需求？

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 提取通用方法 `set_coordinate_mode()` | 减少代码重复，提高可维护性，遵循 DRY 原则 |
| 添加类型注解 | 提高代码可读性，增强 IDE 支持 |
| 细化异常处理 | 区分串口特定错误和其他意外错误，便于调试 |
| 不提取类常量 CMD_PREFIX | 当前只有两个命令，提取常量收益有限，保持代码简洁 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|  | 1 |  |

## Notes
- 项目包含 6 个 Python 模块和 1 个 JSON 配置文件
- 主要入口：StableSensorCalibrator.py
- 更新阶段状态时，使用：pending → in_progress → complete
- 记录所有错误以避免重复
