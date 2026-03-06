# Plan: SensorCalibrator 项目重构计划

**Generated**: 2026-03-06
**Estimated Complexity**: High

## Overview

将 `StableSensorCalibrator.py` (约2400行) 重构为模块化结构，主入口文件 `main.py` 控制在 **<200行**。

### 重要说明
- **scripts/ 目录不参与重构**：该目录包含独立的工具脚本，它们是独立的 Python 工具，不依赖主应用
- 重构只涉及 `sensor_calibrator/` 包和主入口文件

### 目标
- 主文件 `main.py` < 200行
- 保留所有现有功能
- UI不做任何调整
- 功能模块化组织

### 现有项目结构分析

```
SensorCalibrator/
├── StableSensorCalibrator.py          # 主文件 (约2400行) - 需要重构
├── sensor_calibrator/                  # 现有子模块包
│   ├── __init__.py
│   ├── config.py                       # 配置模块
│   ├── data_processor.py               # 数据处理
│   ├── data_buffer.py                  # 数据缓冲
│   ├── ring_buffer.py                  # 环形缓冲
│   ├── log_throttler.py                # 日志限流
│   ├── chart_manager.py                # 图表管理
│   ├── ui_manager.py                   # UI管理
│   ├── serial_manager.py               # 串口管理
│   ├── network_manager.py              # 网络管理
│   ├── calibration_workflow.py         # 校准工作流
│   └── activation_workflow.py          # 激活工作流
├── scripts/                            # 工具脚本目录 (不参与重构)
│   ├── serial_manager.py               # 独立串口管理示例
│   ├── calibration.py                  # 校准计算工具函数
│   ├── network_config.py               # 网络配置工具函数
│   ├── activation.py                   # 激活密钥生成/验证
│   ├── data_pipeline.py                # 数据分发中心
│   ├── performance_profile.py          # 性能分析工具
│   └── read_docx.py                    # DOCX文档读取工具
└── tests/                              # 测试目录
```

### 目标项目结构

```
SensorCalibrator/
├── main.py                             # 主入口 (<200行)
├── sensor_calibrator/                  # 核心包
│   ├── __init__.py                     # 包导出
│   ├── config.py                       # 配置 (已存在)
│   ├── core/                           # 核心模块
│   │   ├── __init__.py
│   │   ├── data_processor.py           # 数据处理 (已存在)
│   │   ├── data_buffer.py              # 数据缓冲 (已存在)
│   │   └── ring_buffer.py              # 环形缓冲 (已存在)
│   ├── serial/                         # 串口模块
│   │   ├── __init__.py
│   │   ├── serial_manager.py           # 串口管理 (已存在)
│   │   └── protocol.py                 # SS命令协议 (新建)
│   ├── gui/                            # GUI模块
│   │   ├── __init__.py
│   │   ├── ui_manager.py               # UI管理 (已存在)
│   │   ├── chart_manager.py            # 图表管理 (已存在)
│   │   └── log_throttler.py            # 日志限流 (已存在)
│   ├── calibration/                    # 校准模块
│   │   ├── __init__.py
│   │   ├── workflow.py                 # 校准工作流 (已存在)
│   │   └── commands.py                 # 校准命令生成 (新建)
│   ├── network/                        # 网络模块
│   │   ├── __init__.py
│   │   ├── manager.py                  # 网络管理 (已存在)
│   │   └── alarm.py                    # 报警阈值 (新建)
│   ├── activation/                     # 激活模块
│   │   ├── __init__.py
│   │   └── workflow.py                 # 激活工作流 (已存在)
│   └── app/                            # 应用核心
│       ├── __init__.py
│       ├── application.py              # 应用主类 (~150行)
│       └── callbacks.py                # 回调函数集合 (~100行)
├── scripts/                            # 工具脚本目录 (保持不变)
│   ├── serial_manager.py               # 独立串口管理示例
│   ├── calibration.py                  # 校准计算工具函数
│   ├── network_config.py               # 网络配置工具函数
│   ├── activation.py                   # 激活密钥生成/验证
│   ├── data_pipeline.py                # 数据分发中心
│   ├── performance_profile.py          # 性能分析工具
│   └── read_docx.py                    # DOCX文档读取工具
└── tests/                              # 测试目录
```

---

## Sprint 1: 创建应用核心模块

**Goal**: 创建 `app/` 子包，将主类核心逻辑迁移

**Demo/Validation**:
- 运行 `python main.py` 能正常启动
- 所有现有功能正常工作

### Task 1.1: 创建 app 子包结构

- **Location**: `sensor_calibrator/app/`
- **Description**: 创建 `__init__.py` 文件
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 创建 `sensor_calibrator/app/__init__.py`
  - 导出 `SensorCalibratorApp` 类
- **Validation**: `from sensor_calibrator.app import SensorCalibratorApp` 成功

### Task 1.2: 创建 Application 主类

- **Location**: `sensor_calibrator/app/application.py`
- **Description**: 
  - 从 `StableSensorCalibrator.py` 提取核心初始化逻辑
  - 创建 `SensorCalibratorApp` 类
  - 包含: 状态管理、组件初始化、生命周期管理
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - 文件行数 < 200行
  - 包含 `__init__`, `setup`, `run`, `cleanup` 方法
- **Validation**: 类可正常实例化

### Task 1.3: 创建回调函数集合

- **Location**: `sensor_calibrator/app/callbacks.py`
- **Description**:
  - 从主类提取所有回调函数
  - 组织为 `AppCallbacks` 类或字典工厂
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - 文件行数 < 150行
  - 所有回调函数正确连接
- **Validation**: 回调函数可被正确调用

---

## Sprint 2: 重构串口协议模块

**Goal**: 将 SS 命令协议逻辑独立成模块

**Demo/Validation**:
- 串口连接/断开正常
- SS 命令发送正常

### Task 2.1: 创建协议模块

- **Location**: `sensor_calibrator/serial/protocol.py`
- **Description**:
  - 定义 SS 命令常量
  - 创建命令构建函数
  - 创建响应解析函数
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - 文件行数 < 100行
  - 所有 SS 命令 (SS:0-SS:9) 有对应函数
- **Validation**: 命令格式正确

---

## Sprint 3: 重构校准命令模块

**Goal**: 将校准命令生成逻辑独立

**Demo/Validation**:
- 校准流程正常
- 命令生成正确

### Task 3.1: 创建校准命令模块

- **Location**: `sensor_calibrator/calibration/commands.py`
- **Description**:
  - 提取 `generate_calibration_commands` 逻辑
  - 创建命令生成器类
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - 文件行数 < 100行
  - 命令格式与原有一致
- **Validation**: 生成的命令正确

---

## Sprint 4: 重构报警阈值模块

**Goal**: 将报警阈值逻辑独立

**Demo/Validation**:
- 报警阈值设置正常

### Task 4.1: 创建报警模块

- **Location**: `sensor_calibrator/network/alarm.py`
- **Description**:
  - 提取 `set_alarm_threshold` 相关逻辑
  - 创建阈值验证和管理函数
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - 文件行数 < 80行
  - 阈值验证逻辑完整
- **Validation**: 阈值设置正常

---

## Sprint 5: 创建主入口文件

**Goal**: 创建简洁的 `main.py`

**Demo/Validation**:
- `python main.py` 正常启动应用
- 所有功能正常

### Task 5.1: 创建 main.py

- **Location**: `main.py` (项目根目录)
- **Description**:
  - 导入并初始化应用
  - 设置异常处理
  - 启动主循环
- **Dependencies**: Sprint 1-4 完成
- **Acceptance Criteria**:
  - 文件行数 < 50行
  - 包含完整的异常处理
- **Validation**: 应用正常启动和退出

### Task 5.2: 更新包导出

- **Location**: `sensor_calibrator/__init__.py`
- **Description**:
  - 更新导出列表
  - 添加新模块的导出
- **Dependencies**: Task 5.1
- **Acceptance Criteria**:
  - 所有公共 API 正确导出
- **Validation**: 导入测试通过

---

## Sprint 6: 清理和测试

**Goal**: 清理旧文件，确保测试通过

**Demo/Validation**:
- 所有测试通过
- 应用功能完整

### Task 6.1: 备份旧文件

- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - 重命名为 `StableSensorCalibrator.py.bak`
  - 或移动到 `archive/` 目录
  - **注意**: `scripts/` 目录中的文件保持不变
- **Dependencies**: Sprint 5 完成
- **Acceptance Criteria**:
  - 旧文件已备份
  - scripts/ 目录保持原样
- **Validation**: 备份文件存在

### Task 6.2: 运行测试

- **Location**: `tests/`
- **Description**:
  - 运行现有测试
  - 修复失败的测试
- **Dependencies**: Task 6.1
- **Acceptance Criteria**:
  - 所有测试通过
- **Validation**: `pytest tests/` 成功

### Task 6.3: 功能验证

- **Location**: 整个项目
- **Description**:
  - 手动测试所有功能
  - 验证 UI 无变化
- **Dependencies**: Task 6.2
- **Acceptance Criteria**:
  - 所有功能正常
  - UI 显示正确
- **Validation**: 功能检查清单通过

---

## Testing Strategy

### 单元测试
- 每个新模块创建对应的测试文件
- 测试覆盖率 > 80%

### 集成测试
- 使用现有 `tests/test_integration.py`
- 验证模块间交互

### 手动测试清单
- [ ] 串口连接/断开
- [ ] 数据流启动/停止
- [ ] 校准流程完整执行
- [ ] WiFi/MQTT/OTA 配置
- [ ] 报警阈值设置
- [ ] 传感器激活/验证
- [ ] 配置保存/加载
- [ ] 图表正常显示
- [ ] 统计信息更新

---

## Potential Risks & Gotchas

### 风险 1: 循环导入
- **问题**: 模块间相互导入可能导致循环依赖
- **缓解**: 使用延迟导入或依赖注入

### 风险 2: 回调函数丢失
- **问题**: 重构过程中回调函数连接可能断开
- **缓解**: 使用统一的回调注册机制

### 风险 3: UI 状态不同步
- **问题**: 模块化后 UI 状态更新可能不及时
- **缓解**: 保持事件驱动架构

---

## Rollback Plan

1. 保留 `StableSensorCalibrator.py.bak` 备份
2. 使用 Git 分支进行重构
3. 如遇重大问题，恢复备份文件即可

---

## 文件行数预估

| 文件 | 预估行数 |
|------|---------|
| `main.py` | ~30行 |
| `app/application.py` | ~150行 |
| `app/callbacks.py` | ~100行 |
| `serial/protocol.py` | ~80行 |
| `calibration/commands.py` | ~80行 |
| `network/alarm.py` | ~60行 |

**主入口总计**: ~30行 (main.py)
**应用核心总计**: ~250行 (app/)
