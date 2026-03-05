# SensorCalibrator 项目文件详细说明

**生成日期**: 2026-03-05  
**版本**: v2.0 (整理后)

---

## 📂 目录结构总览

```
SensorCalibrator/
├── 📁 backups/              # 备份文件 (不提交到Git)
├── 📁 config/               # 配置文件
├── 📁 plan/                 # 计划和文档
├── 📁 reports/              # 报告文档
├── 📁 scripts/              # 工具脚本
├── 📁 sensor_calibrator/    # 核心Python包
├── 📁 src/                  # 源代码 (待重构)
├── 📁 tests/                # 测试文件
├── 📁 sensor_calibrator.egg-info/  # 包元数据
└── 📄 根目录文件            # 项目入口和配置
```

---

## 🔧 根目录文件 (项目入口和配置)

### StableSensorCalibrator.py (97.3KB)
**类型**: 主应用程序入口  
**作用**: 
- 传感器校准应用程序的主类
- 集成串口通信、UI、校准、激活、网络配置等功能
- 包含70+方法，是项目的核心入口点
- 当前正在进行重构以解决God Class问题

**关键功能**:
- 串口通信管理
- 数据采集与可视化
- 六位置校准算法
- 传感器激活验证
- 网络配置(WiFi/MQTT)

---

### README.md (5.2KB)
**类型**: 项目说明文档  
**作用**: 
- 项目简介和功能特性
- 快速开始指南
- 安装和使用说明
- 项目入口文档

---

### CHANGELOG.md (3.6KB)
**类型**: 变更日志  
**作用**: 
- 版本历史记录
- 功能变更说明
- 修复的问题列表

---

### AGENTS.md (0.4KB)
**类型**: AI助手规则  
**作用**: 
- 定义AI助手的行为规范
- 代码安全和隐私规则
- 系统环境说明

---

### requirements.txt (0.3KB)
**类型**: Python依赖清单  
**作用**: 
- 列出项目所有依赖包
- 用于 `pip install -r requirements.txt`

**主要内容**:
```
pyserial>=3.5
numpy>=1.24.0
matplotlib>=3.7.0
```

---

### pyproject.toml (1.0KB)
**类型**: 现代Python项目配置  
**作用**: 
- 项目元数据(名称、版本、作者)
- 构建系统配置
- 工具配置(ruff、pytest、black等)

---

### pytest.ini (0.8KB)
**类型**: pytest测试配置  
**作用**: 
- 测试目录配置
- 覆盖率设置
- 测试选项和插件

---

---

## 📦 sensor_calibrator/ - 核心Python包

这是项目的核心包，包含所有主要功能模块。

### __init__.py (2.4KB)
**类型**: 包初始化文件  
**作用**: 
- 导出所有公共类和函数
- 统一包接口，简化导入
- 定义 `__all__` 列表

**导出的主要类**:
- `Config`, `UIConfig`, `CalibrationConfig`, `SerialConfig`
- `ChartManager`, `UIManager`, `DataProcessor`
- `SerialManager`, `NetworkManager`
- `CalibrationWorkflow`, `ActivationWorkflow`
- `RingBuffer`, `QueueAdapter`, `LogThrottler`

---

### config.py (9.5KB)
**类型**: 配置管理模块  
**作用**: 
- 集中管理所有配置常量
- 使用 `@dataclass` 和 `Final` 类型注解
- 提供类型安全的配置访问

**主要配置类**:
| 类名 | 用途 |
|------|------|
| `Config` | 通用配置(队列大小、超时、文件路径) |
| `UIConfig` | UI配置(窗口尺寸、颜色、字体) |
| `CalibrationConfig` | 校准配置(位置名称、采样数) |
| `SerialConfig` | 串口配置(波特率、缓冲区大小) |
| `NetworkConfig` | 网络配置(端口范围、超时) |

---

### activation_workflow.py (16.2KB)
**类型**: 激活工作流类  
**作用**: 
- 管理传感器激活完整流程
- MAC地址提取和验证
- 激活密钥生成(SHA-256)
- 密钥验证(恒定时间比较)
- 激活命令发送和响应处理

**主要方法**:
| 方法 | 功能 |
|------|------|
| `extract_mac_from_properties()` | 从传感器属性提取MAC地址 |
| `generate_key_from_mac()` | 基于MAC生成64字符SHA-256密钥 |
| `verify_key()` | 验证输入密钥(防时序攻击) |
| `activate_sensor()` | 执行激活流程 |
| `check_activation_status()` | 检查传感器激活状态 |

---

### calibration_workflow.py (16.1KB)
**类型**: 校准工作流类  
**作用**: 
- 管理六位置校准完整流程
- 数据采集控制
- 校准计算(最小二乘法)
- 参数保存和加载

**主要方法**:
| 方法 | 功能 |
|------|------|
| `start_calibration()` | 开始校准流程 |
| `capture_position()` | 捕获单个位置数据 |
| `calculate_calibration()` | 计算校准参数 |
| `save_calibration()` | 保存参数到文件 |
| `load_calibration()` | 从文件加载参数 |

---

### serial_manager.py (18.1KB)
**类型**: 串口管理类  
**作用**: 
- 统一管理串口打开/关闭
- 读写线程管理
- 监听器模式的数据分发
- 请求-响应模式支持

**主要方法**:
| 方法 | 功能 |
|------|------|
| `open()` | 打开串口连接 |
| `close()` | 关闭串口连接 |
| `send_line()` | 发送一行命令 |
| `add_listener()` | 添加数据监听器 |
| `remove_listener()` | 移除数据监听器 |
| `request_response()` | 发送命令并等待响应 |

---

### network_manager.py (19.9KB)
**类型**: 网络管理类  
**作用**: 
- WiFi配置管理(SSID、密码)
- MQTT配置管理(Broker、用户名、密码、端口)
- OTA参数管理
- 网络命令生成和发送

**主要方法**:
| 方法 | 功能 |
|------|------|
| `set_wifi_config()` | 设置WiFi配置 |
| `set_mqtt_config()` | 设置MQTT配置 |
| `set_ota_params()` | 设置OTA参数 |
| `send_network_config()` | 发送配置到传感器 |
| `extract_network_info()` | 从传感器属性提取网络信息 |

---

### chart_manager.py (22.4KB)
**类型**: 图表管理类  
**作用**: 
- 管理Matplotlib图表
- 实时数据可视化
- 多子图布局管理
- 传感器数据图表(加速度、陀螺仪)

**主要功能**:
- 创建/销毁图表
- 更新曲线数据
- 自动缩放和格式化
- 暂停/恢复更新

---

### ui_manager.py (39.7KB)
**类型**: UI管理类  
**作用**: 
- 管理所有Tkinter UI组件
- 布局管理
- 组件状态管理
- 回调函数注册

**主要功能**:
- 创建主窗口布局
- 管理按钮、标签、输入框
- 状态栏更新
- 激活区域UI
- 网络配置UI
- 统计信息UI

---

### data_processor.py (11.0KB)
**类型**: 数据处理器类  
**作用**: 
- 传感器数据解析
- 实时统计计算(均值、标准差)
- 数据滤波和平滑
- 数据队列管理

**主要方法**:
| 方法 | 功能 |
|------|------|
| `parse_sensor_data()` | 解析JSON格式传感器数据 |
| `update_statistics()` | 更新统计信息 |
| `get_statistics()` | 获取当前统计值 |
| `clear_all()` | 清空所有数据 |

---

### data_buffer.py (10.1KB)
**类型**: 数据缓冲区类  
**作用**: 
- 环形缓冲区实现
- 传感器数据存储
- 支持按时间窗口查询
- 线程安全的数据访问

---

### ring_buffer.py (5.3KB)
**类型**: 环形缓冲区实现  
**作用**: 
- 固定容量的循环缓冲区
- 支持numpy数组操作
- 高效的数据追加和读取

---

### log_throttler.py (5.3KB)
**类型**: 日志限流器  
**作用**: 
- 防止日志重复输出
- 批量处理相似日志
- 减少UI日志区域的更新频率
- 提高性能

---

---

## 🧪 tests/ - 测试文件

### __init__.py (0.3KB)
**类型**: 测试包初始化  
**作用**: 标记tests为Python包

---

### test_commands.py (8.1KB)
**类型**: 命令测试  
**作用**: 
- 测试传感器命令发送
- 验证命令格式
- 测试响应解析

---

### test_data_processor.py (8.6KB)
**类型**: 数据处理器测试  
**作用**: 
- 测试数据解析逻辑
- 测试统计计算
- 测试边界条件

---

### test_integration.py (23.2KB)
**类型**: 集成测试  
**作用**: 
- 端到端功能测试
- 模块间交互测试
- 完整工作流程测试

---

### test_serial_manager.py (6.3KB)
**类型**: 串口管理器测试  
**作用**: 
- 测试串口打开/关闭
- 测试数据监听
- 测试请求-响应模式

---

### e2e_test_checklist.md (5.5KB)
**类型**: 端到端测试清单  
**作用**: 
- 手动测试步骤文档
- 功能验证清单
- 发布前检查列表

---

---

## 🛠️ scripts/ - 工具脚本

### activation.py (3.0KB)
**类型**: 激活工具函数  
**作用**: 
- 传感器激活相关的底层工具函数
- MAC地址提取、密钥生成、密钥验证
- 被 `ActivationWorkflow` 类使用

**主要函数**:
- `generate_key_from_mac()` - 基于MAC生成SHA-256密钥
- `verify_key()` - 验证激活密钥
- `extract_mac_from_properties()` - 从传感器属性提取MAC

---

### calibration.py (2.3KB)
**类型**: 校准工具函数  
**作用**: 
- 校准相关的工具函数
- 六位置校准算法实现
- 被 `CalibrationWorkflow` 类使用

---

### data_pipeline.py (2.1KB)
**类型**: 数据流模块  
**作用**: 
- 实现发布-订阅模式的数据管道
- 用于传感器数据的广播和分发
- 支持多个订阅者接收数据

---

### network_config.py (3.4KB)
**类型**: 网络配置工具  
**作用**: 
- WiFi和MQTT配置的工具函数
- 提供密码和端口验证功能
- 被 `NetworkManager` 类使用

---

### performance_profile.py (4.9KB)
**类型**: 性能分析工具  
**作用**: 
- 开发工具，用于分析代码性能
- 使用cProfile进行CPU分析
- 帮助识别性能瓶颈

---

### read_docx.py (1.0KB)
**类型**: 文档读取工具  
**作用**: 
- 读取Word文档中的指令集表格
- 用于从需求文档提取传感器命令
- 辅助开发工具

---

### serial_manager.py (8.2KB)
**类型**: 旧版串口管理器  
**作用**: 
- 早期的串口管理实现
- 当前已被 `sensor_calibrator/serial_manager.py` 替代
- 保留作为参考或向后兼容

---

---

## 📋 plan/ - 计划和文档

### README.md (1.3KB)
**类型**: 文件夹说明  
**作用**: plan文件夹的索引和说明

---

### bare-except-fix-plan.md (14.7KB)
**类型**: Bare Except修复计划  
**作用**: 详细说明如何修复9处bare except问题

---

### code-review-fixes-plan.md (9.4KB)
**类型**: 代码审查修复计划  
**作用**: 代码审查问题的修复计划总览

---

### detailed-implementation-plan.md (19.4KB)
**类型**: 详细实施方案  
**作用**: Bare except和激活工作流重构的详细实施步骤

---

### high-priority-commands-plan.md (21.6KB)
**类型**: 高优先级命令计划  
**作用**: 传感器命令实现计划

---

### main-file-refactoring-plan.md (15.8KB)
**类型**: 主文件重构计划  
**作用**: StableSensorCalibrator.py重构策略

---

### main-file-refactoring-plan-updated.md (17.4KB)
**类型**: 更新的重构计划  
**作用**: 重构计划的更新版本

---

### performance-optimization-plan.md (14.8KB)
**类型**: 性能优化计划  
**作用**: 代码性能改进策略

---

### performance_optimization_plan.md (4.7KB)
**类型**: 早期性能计划  
**作用**: 初始性能优化方案

---

### project-improvement-plan.md (8.2KB)
**类型**: 项目改进计划  
**作用**: 整体项目改进路线图

---

### task_plan.md (2.8KB)
**类型**: 任务计划  
**作用**: 当前迭代任务列表

---

### progress.md (2.2KB)
**类型**: 进度跟踪  
**作用**: 项目进度更新记录

---

### findings.md (4.8KB)
**类型**: 研究发现  
**作用**: 代码分析和研究发现

---

### dependency-analysis.md (9.5KB)
**类型**: 依赖分析  
**作用**: 项目依赖关系分析

---

### refactoring-summary.md (5.7KB)
**类型**: 重构摘要  
**作用**: 重构工作摘要说明

---

---

## 📊 reports/ - 报告文档

### OPTIMIZATION-REPORT.md (13.8KB)
**类型**: 优化报告  
**作用**: 
- 性能优化结果报告
- 优化前后的对比
- 优化建议

---

### PROJECT-FILES-GUIDE.md (12.3KB)
**类型**: 项目文件指南  
**作用**: 
- 项目文件详细说明
- 文件作用和依赖关系
- 项目结构文档

---

---

## ⚙️ config/ - 配置文件

### sensor_properties.json (2.2KB)
**类型**: 传感器属性模板  
**作用**: 
- 默认传感器属性
- 属性结构参考
- 开发和测试数据

**内容示例**:
```json
{
  "sys": {
    "MAC": "AA:BB:CC:DD:EE:FF",
    "DN": "Sensor-001"
  }
}
```

---

---

## 💾 backups/ - 备份文件

**注意**: 此目录不应提交到Git

### StableSensorCalibrator.py.backup.sprint5 (88.8KB)
**类型**: Sprint 5备份  
**作用**: Sprint 5结束时的代码备份

---

### chart_manager.py.backup (21.5KB)
**类型**: 图表管理器备份  
**作用**: 重要版本的备份

---

### data_buffer.py.backup (9.5KB)
**类型**: 数据缓冲区备份  
**作用**: 重要版本的备份

---

### data_processor.py.backup (10.2KB)
**类型**: 数据处理器备份  
**作用**: 重要版本的备份

---

### serial_manager.py.backup (15.7KB)
**类型**: 串口管理器备份  
**作用**: 重要版本的备份

---

---

## 📦 sensor_calibrator.egg-info/ - 包元数据

**说明**: 此目录由 `setuptools` 自动生成，包含包的安装信息

### PKG-INFO (6.0KB)
**类型**: 包信息  
**作用**: 包的元数据信息

---

### SOURCES.txt (0.7KB)
**类型**: 源文件列表  
**作用**: 包含在包中的文件列表

---

### requires.txt (0.1KB)
**类型**: 依赖列表  
**作用**: 包的依赖要求

---

### dependency_links.txt (0.0KB)
**类型**: 依赖链接  
**作用**: 额外的依赖链接

---

### top_level.txt (0.0KB)
**类型**: 顶级包名  
**作用**: 顶级包名称

---

---

## 📁 src/ - 源代码 (待重构)

**说明**: 此目录结构用于未来的代码重构，目前为空

```
src/
└── sensor_calibrator/
    ├── core/       # 核心功能 (待创建)
    ├── utils/      # 工具函数 (待创建)
    └── workflows/  # 工作流 (待创建)
```

**计划用途**:
- 将 `sensor_calibrator/` 中的代码按功能分类
- `core/`: 核心数据结构和算法
- `utils/`: 辅助工具函数
- `workflows/`: 业务流程实现

---

## 📊 文件统计

| 目录 | 文件数 | 总大小 | 说明 |
|------|--------|--------|------|
| `sensor_calibrator/` | 13 | ~180KB | 核心Python包 |
| `tests/` | 5 | ~52KB | 测试文件 |
| `scripts/` | 7 | ~25KB | 工具脚本 |
| `plan/` | 15 | ~150KB | 计划文档 |
| `reports/` | 2 | ~26KB | 报告文档 |
| `backups/` | 5 | ~155KB | 备份文件 |
| `config/` | 1 | ~2KB | 配置文件 |
| 根目录 | 7 | ~110KB | 项目入口和配置 |

**总计**: ~55个文件，~700KB

---

## 🔗 关键文件依赖关系

```
StableSensorCalibrator.py (主程序)
    ├── sensor_calibrator/
    │   ├── config.py (配置常量)
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

## 📝 维护建议

1. **定期清理 backups/**: 保留最近的2-3个版本备份即可
2. **更新 plan/**: 已完成的计划文档可以归档或删除
3. **保持 sensor_calibrator/**: 核心代码应保持稳定
4. **完善 tests/**: 提高测试覆盖率

---

**文档版本**: 1.0  
**最后更新**: 2026-03-05
