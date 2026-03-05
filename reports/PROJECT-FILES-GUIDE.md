# 项目文件详细说明

**项目**: SensorCalibrator - 传感器校准工具
**生成日期**: 2026-03-05

---

## 📁 目录结构概览

```
SensorCalibrator/
├── 📄 核心应用文件
├── 📁 sensor_calibrator/    # 核心模块包
├── 📁 tests/                # 测试文件
├── 📁 docs/                 # 文档
├── 📄 配置文件
└── 📄 计划文档
```

---

## 🔧 核心应用文件

### StableSensorCalibrator.py (99.7 KB)
**类型**: 主应用程序入口
**作用**: 
- 传感器校准应用程序的主类
- 集成串口通信、UI、校准、激活、网络配置等功能
- 包含 70+ 个方法，2391+ 行代码
- 当前正在进行重构以解决 God Class 问题

**关键功能**:
- 串口通信管理
- 数据采集与可视化
- 六位置校准算法
- 传感器激活验证
- 网络配置 (WiFi/MQTT)
- 图表显示 (Matplotlib)
- 文件 I/O 操作

---

### serial_manager.py (8.3 KB)
**类型**: 独立模块
**作用**: 
- 早期的串口管理实现
- 当前已被 `sensor_calibrator/serial_manager.py` 替代
- 保留作为参考或向后兼容

---

### activation.py (3.1 KB)
**类型**: 工具模块
**作用**:
- 传感器激活相关的工具函数
- 提供 MAC 地址提取、密钥生成、密钥验证等功能
- 当前主要功能已迁移到 `ActivationWorkflow` 类
- 保留作为底层工具库使用

**主要函数**:
- `generate_key_from_mac()` - 基于 MAC 生成 SHA-256 密钥
- `verify_key()` - 验证激活密钥
- `extract_mac_from_properties()` - 从传感器属性提取 MAC

---

### calibration.py (2.3 KB)
**类型**: 工具模块
**作用**:
- 校准相关的工具函数
- 六位置校准算法实现
- 被 `CalibrationWorkflow` 类使用

---

### data_pipeline.py (2.1 KB)
**类型**: 数据流模块
**作用**:
- 实现发布-订阅模式的数据管道
- 用于传感器数据的广播和分发
- 支持多个订阅者接收数据

---

### network_config.py (3.5 KB)
**类型**: 网络配置工具
**作用**:
- WiFi 和 MQTT 配置的工具函数
- 提供密码和端口验证功能
- 当前主要功能已迁移到 `NetworkManager` 类

---

### performance_profile.py (5.0 KB)
**类型**: 性能分析工具
**作用**:
- 开发工具，用于分析代码性能
- 使用 cProfile 进行 CPU 分析
- 帮助识别性能瓶颈

---

### read_docx.py (1.0 KB)
**类型**: 文档读取工具
**作用**:
- 读取 Word 文档中的指令集表格
- 用于从需求文档提取传感器命令
- 辅助开发工具

---

## 📦 sensor_calibrator/ 核心模块包

### __init__.py (2.5 KB)
**类型**: 包初始化文件
**作用**:
- 导出所有公共类和函数
- 统一包接口
- 简化导入语句

**导出内容**:
```python
from sensor_calibrator import (
    Config, UIConfig, CalibrationConfig, SerialConfig,
    ChartManager, UIManager, DataProcessor,
    SerialManager, NetworkManager,
    CalibrationWorkflow, ActivationWorkflow,
    RingBuffer, QueueAdapter, LogThrottler
)
```

---

### config.py (9.7 KB)
**类型**: 配置模块
**作用**:
- 集中管理所有配置常量
- 使用 `@dataclass` 和 `Final` 类型注解
- 提供类型安全的配置访问

**主要配置类**:
- `Config` - 通用配置 (队列大小、超时、文件路径等)
- `UIConfig` - UI 配置 (窗口尺寸、颜色、字体等)
- `CalibrationConfig` - 校准配置 (位置名称、采样数等)
- `SerialConfig` - 串口配置 (波特率、缓冲区大小等)

---

### activation_workflow.py (16.6 KB)
**类型**: 激活工作流类
**作用**:
- 管理传感器激活完整流程
- MAC 地址提取和验证
- 激活密钥生成 (SHA-256)
- 密钥验证 (恒定时间比较)
- 激活命令发送和响应处理

**主要方法**:
- `extract_mac_from_properties()` - 提取 MAC
- `generate_key_from_mac()` - 生成密钥
- `verify_key()` - 验证密钥
- `activate_sensor()` - 执行激活
- `check_activation_status()` - 检查激活状态

---

### calibration_workflow.py (16.5 KB)
**类型**: 校准工作流类
**作用**:
- 管理六位置校准完整流程
- 数据采集控制
- 校准计算 (最小二乘法)
- 参数保存和加载

**主要方法**:
- `start_calibration()` - 开始校准
- `capture_position()` - 捕获位置数据
- `calculate_calibration()` - 计算校准参数
- `save_calibration()` - 保存参数到文件

---

### chart_manager.py (22.9 KB)
**类型**: 图表管理类
**作用**:
- 管理 Matplotlib 图表
- 实时数据可视化
- 多子图布局管理
- 传感器数据图表 (加速度、陀螺仪)

**主要功能**:
- 创建/销毁图表
- 更新曲线数据
- 自动缩放和格式化
- 暂停/恢复更新

---

### data_processor.py (11.3 KB)
**类型**: 数据处理器类
**作用**:
- 传感器数据解析
- 实时统计计算 (均值、标准差)
- 数据滤波和平滑
- 数据队列管理

**主要方法**:
- `parse_sensor_data()` - 解析 JSON 数据
- `update_statistics()` - 更新统计信息
- `get_statistics()` - 获取当前统计
- `clear_all()` - 清空数据

---

### data_buffer.py (10.4 KB)
**类型**: 数据缓冲区类
**作用**:
- 环形缓冲区实现
- 传感器数据存储
- 支持按时间窗口查询
- 线程安全的数据访问

---

### ring_buffer.py (5.4 KB)
**类型**: 环形缓冲区实现
**作用**:
- 固定容量的循环缓冲区
- 支持 numpy 数组操作
- 高效的数据追加和读取

---

### network_manager.py (20.4 KB)
**类型**: 网络管理类
**作用**:
- WiFi 配置管理 (SSID, 密码)
- MQTT 配置管理 (Broker, 用户名, 密码, 端口)
- OTA 参数管理
- 网络命令生成和发送

**主要方法**:
- `set_wifi_config()` - 设置 WiFi
- `set_mqtt_config()` - 设置 MQTT
- `send_network_config()` - 发送配置到传感器
- `extract_network_info()` - 从属性提取网络信息

---

### serial_manager.py (18.5 KB)
**类型**: 串口管理类
**作用**:
- 统一管理串口打开/关闭
- 读写线程管理
- 监听器模式的数据分发
- 请求-响应模式支持

**主要方法**:
- `open()` - 打开串口
- `close()` - 关闭串口
- `send_line()` - 发送命令
- `add_listener()` - 添加数据监听器
- `request_response()` - 发送并等待响应

---

### ui_manager.py (40.7 KB)
**类型**: UI 管理类
**作用**:
- 管理所有 Tkinter UI 组件
- 布局管理
- 组件状态管理
- 回调函数注册

**主要功能**:
- 创建主窗口布局
- 管理按钮、标签、输入框
- 状态栏更新
- 激活区域 UI
- 网络配置 UI

---

### log_throttler.py (5.4 KB)
**类型**: 日志限流器
**作用**:
- 防止日志重复输出
- 批量处理相似日志
- 减少 UI 日志区域的更新频率

---

## 🧪 tests/ 测试文件

### __init__.py (262 bytes)
**类型**: 测试包初始化
**作用**: 标记 tests 为 Python 包

---

### test_commands.py (8.3 KB)
**类型**: 命令测试
**作用**:
- 测试传感器命令发送
- 验证命令格式
- 测试响应解析

---

### test_data_processor.py (8.8 KB)
**类型**: 数据处理器测试
**作用**:
- 测试数据解析逻辑
- 测试统计计算
- 测试边界条件

---

### test_integration.py (23.7 KB)
**类型**: 集成测试
**作用**:
- 端到端功能测试
- 模块间交互测试
- 完整工作流程测试

---

### test_serial_manager.py (6.5 KB)
**类型**: 串口管理器测试
**作用**:
- 测试串口打开/关闭
- 测试数据监听
- 测试请求-响应模式

---

### e2e_test_checklist.md (5.6 KB)
**类型**: 端到端测试清单
**作用**:
- 手动测试步骤文档
- 功能验证清单
- 发布前检查列表

---

## 📄 配置文件

### requirements.txt (272 bytes)
**类型**: Python 依赖清单
**作用**: 列出项目依赖包

**内容示例**:
```
pyserial>=3.5
numpy>=1.24.0
matplotlib>=3.7.0
```

---

### pyproject.toml (1.0 KB)
**类型**: 项目配置
**作用**:
- 项目元数据
- 构建配置
- 工具配置 (ruff, pytest)

---

### pytest.ini (818 bytes)
**类型**: pytest 配置
**作用**:
- 测试目录配置
- 覆盖率设置
- 测试选项

---

### sensor_properties.json (2.2 KB)
**类型**: 传感器属性模板
**作用**:
- 默认传感器属性
- 属性结构参考
- 开发和测试数据

---

### sensor_calibrator.egg-info/
**类型**: 包元数据目录
**作用**:
- Python 包安装信息
- 自动生成，无需手动修改
- 包含依赖、版本、入口点等信息

---

## 📚 项目文档

### README.md (5.3 KB)
**类型**: 项目说明文档
**作用**:
- 项目简介
- 快速开始指南
- 功能特性说明
- 安装和使用说明

---

### CHANGELOG.md (3.7 KB)
**类型**: 变更日志
**作用**:
- 版本历史记录
- 功能变更说明
- 修复的问题列表

---

### AGENTS.md (386 bytes)
**类型**: AI Agent 规则
**作用**:
- 定义 AI 助手的行为规范
- 代码安全和隐私规则
- 系统环境说明

---

## 📋 计划和报告文档

### code-review-fixes-plan.md (9.7 KB)
**类型**: 代码审查修复计划
**作用**: 针对代码审查问题的修复计划

### detailed-implementation-plan.md (19.9 KB)
**类型**: 详细实施方案
**作用**: Bare except 和激活工作流重构的详细计划

### bare-except-fix-plan.md (15.1 KB)
**类型**: Bare Except 修复计划
**作用**: 专门处理 bare except 的修复步骤

### main-file-refactoring-plan.md (16.2 KB)
**类型**: 主文件重构计划
**作用**: StableSensorCalibrator.py 重构策略

### main-file-refactoring-plan-updated.md (17.8 KB)
**类型**: 更新的重构计划
**作用**: 重构计划的更新版本

### high-priority-commands-plan.md (22.1 KB)
**类型**: 高优先级命令计划
**作用**: 传感器命令实现计划

### performance-optimization-plan.md (15.1 KB)
**类型**: 性能优化计划
**作用**: 代码性能改进策略

### performance_optimization_plan.md (4.8 KB)
**类型**: 早期性能计划
**作用**: 初始性能优化方案

### OPTIMIZATION-REPORT.md (14.2 KB)
**类型**: 优化报告
**作用**: 性能优化结果报告

### project-improvement-plan.md (8.4 KB)
**类型**: 项目改进计划
**作用**: 整体项目改进路线图

### task_plan.md (2.8 KB)
**类型**: 任务计划
**作用**: 当前迭代任务列表

### progress.md (2.2 KB)
**类型**: 进度跟踪
**作用**: 项目进度更新记录

### findings.md (4.9 KB)
**类型**: 研究发现
**作用**: 代码分析和研究发现

---

## 🔧 开发和缓存文件

### .pytest_cache/
**类型**: pytest 缓存目录
**作用**: 存储测试结果缓存，加速后续测试运行
**注意**: 可安全删除，自动生成

### .ruff_cache/
**类型**: ruff 缓存目录
**作用**: 存储 lint 检查结果缓存
**注意**: 可安全删除，自动生成

### .venv/
**类型**: Python 虚拟环境 (未在列表中显示但通常存在)
**作用**: 隔离项目依赖
**注意**: 不应提交到版本控制

---

## 🗄️ 备份文件

### StableSensorCalibrator.py.backup.sprint5 (91.0 KB)
**类型**: Sprint 5 备份
**作用**: Sprint 5 结束时的代码备份
**用途**: 回滚参考

### sensor_calibrator/*.backup
**类型**: 模块备份文件
**作用**: 各模块的重要版本备份
**文件**:
- `chart_manager.py.backup`
- `data_buffer.py.backup`
- `data_processor.py.backup`
- `serial_manager.py.backup`

---

## 📊 文件统计

| 类别 | 文件数 | 总大小 |
|------|--------|--------|
| 核心代码 | 12 | ~350 KB |
| 测试文件 | 4 | ~50 KB |
| 配置文档 | 6 | ~10 KB |
| 计划文档 | 12 | ~150 KB |
| 备份文件 | 5 | ~160 KB |

---

## 🎯 关键文件依赖关系

```
StableSensorCalibrator.py
    ├── sensor_calibrator/
    │   ├── config.py (配置)
    │   ├── activation_workflow.py (激活)
    │   ├── calibration_workflow.py (校准)
    │   ├── serial_manager.py (串口)
    │   ├── network_manager.py (网络)
    │   ├── chart_manager.py (图表)
    │   ├── ui_manager.py (UI)
    │   └── data_processor.py (数据处理)
    └── tests/ (测试)
```

---

**文档版本**: 1.0  
**最后更新**: 2026-03-05
