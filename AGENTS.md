# SensorCalibrator - AI Agent Guide

> This file provides essential information for AI coding agents working on the SensorCalibrator project.
> 
> 本文件为在 SensorCalibrator 项目上工作的 AI 编程代理提供关键信息。

---

## ⚠️ AI Agent 工作规则

### 代码修改前必须获得确认

**在没有获得明确确认之前，不要修改任何代码文件。**

不允许的操作：
- ❌ 执行 `WriteFile` 写入代码文件
- ❌ 执行 `StrReplaceFile` 修改代码文件
- ❌ 删除代码文件
- ❌ 重命名代码文件

允许的操作（无需确认）：
- ✅ 读取文件 (`ReadFile`)
- ✅ 搜索代码 (`Grep`)
- ✅ 列出文件 (`Glob`)
- ✅ 执行 Shell 命令查看信息（如 `git status`、`ls` 等）
- ✅ 网页搜索 (`SearchWeb`)
- ✅ 抓取网页 (`FetchURL`)

例外情况（可跳过确认）：
- 用户明确使用了 `/yolo` 命令
- 用户明确说了 "直接改"、"不需要确认" 等
- 创建新文件（非修改现有文件）

### Git 使用规则

**Git 上传命令需要确认**

需要确认的命令：
- `git push`、`git commit`、`git merge`、`git rebase`、`git reset`

允许的操作（无需确认）：
- ✅ `git status` - 查看状态
- ✅ `git log` - 查看日志
- ✅ `git diff` - 查看差异
- ✅ `git branch` - 查看分支

### 回复风格
- 保持简洁，避免冗长
- 不要重复说明已经清楚的内容
- 代码示例必须带中文注释

### 系统环境
- Windows 11 + PowerShell
- 避免使用 bash/sh 命令

### 代码修改原则
- **最小修改原则**：每次只修改必要的代码
- 不要修改与当前任务无关的文件
- 不要重构未涉及的功能
- 保持现有代码风格，不要批量格式化

### 编码规范
- 所有注释和文档字符串使用中文
- 变量名、函数名使用英文
- 遵循项目的代码风格

---

## Project Overview / 项目概览

**SensorCalibrator** is a Python desktop application for calibrating MPU6050 (6-axis IMU) and ADXL355 (high-precision accelerometer) sensors. It provides a complete calibration workflow including six-position calibration, real-time data visualization, sensor activation verification, and network configuration.

**SensorCalibrator** 是一个用于校准 MPU6050（6轴IMU）和 ADXL355（高精度加速度计）传感器的 Python 桌面应用程序。它提供完整的校准工作流程，包括六位置校准、实时数据可视化、传感器激活验证和网络配置。

### Key Features / 主要功能

- **Serial Communication / 串口通信**: Multi-baudrate support (9600-115200), auto port detection / 支持多种波特率，自动检测可用串口
- **Real-time Visualization / 实时可视化**: Live charts using matplotlib with blit optimization / 使用 matplotlib 实现实时图表显示，支持 blit 优化
- **Six-Position Calibration / 六位置校准**: Complete accelerometer calibration algorithm for both MPU6050 and ADXL355 / 完整的加速度计校准算法
- **Sensor Activation / 传感器激活**: MAC-based SHA-256 key verification (7-char fragment at positions 5-12) / 基于 MAC 地址的密钥验证机制
- **Network Configuration / 网络配置**: WiFi, MQTT, OTA firmware update, and alarm threshold support / 支持 WiFi、MQTT、OTA 固件更新和报警阈值配置
- **Dual Coordinate Modes / 双坐标模式**: Local (SS:2) and global (SS:3) coordinate system support / 支持局部坐标系和全局坐标系

---

## Technology Stack / 技术栈

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | >= 3.8 |
| GUI Framework | tkinter | built-in |
| Visualization | matplotlib | >= 3.5 |
| Serial Communication | pyserial | >= 3.5 |
| Numerical Computing | numpy | >= 1.21 |
| Testing | pytest | >= 7.0 |

---

## Project Structure / 项目结构

```
SensorCalibrator/
├── main.py                          # Application entry point / 应用程序入口
├── pyproject.toml                   # Project configuration (setuptools) / 项目配置
├── pytest.ini                       # Test configuration / 测试配置
├── requirements.txt                 # Dependencies / 依赖清单
├── calibration_params.json          # Default calibration parameters storage / 默认校准参数存储
├── sensor_properties.json           # Default sensor properties storage / 默认传感器属性存储
├── config/                          # Configuration storage directory / 配置存储目录
├── sensor_calibrator/               # Core package / 核心包
│   ├── __init__.py                  # Package exports with lazy loading / 包导出（懒加载）
│   ├── config.py                    # Configuration constants (Config, SerialConfig, UIConfig, CalibrationConfig) / 配置常量
│   ├── data_buffer.py               # SensorDataBuffer - sensor data storage / 传感器数据存储
│   ├── data_processor.py            # DataProcessor (deprecated, use SensorDataBuffer) / 数据处理器（已弃用）
│   ├── ring_buffer.py               # Ring buffer and QueueAdapter implementations / 环形缓冲区实现
│   ├── log_throttler.py             # Log rate limiting for performance / 日志限流
│   ├── serial_manager.py            # Serial port management with threading / 串口管理
│   ├── chart_manager.py             # Matplotlib charts with blit optimization / 图表管理
│   ├── ui_manager.py                # GUI components creation and layout / UI 组件
│   ├── network_manager.py           # WiFi/MQTT/OTA/alarm config management / 网络管理
│   ├── calibration_workflow.py      # 6-position calibration logic / 校准工作流
│   ├── activation_workflow.py       # Sensor activation workflow / 激活工作流
│   ├── app/                         # Application core / 应用核心
│   │   ├── __init__.py              # Exports SensorCalibratorApp, AppCallbacks
│   │   ├── application.py           # Main application class / 主应用类
│   │   └── callbacks.py             # UI callbacks implementation / UI 回调实现
│   ├── serial/                      # Serial protocol module / 串口协议模块
│   │   ├── __init__.py              # Protocol exports
│   │   └── protocol.py              # SS command definitions / SS 命令定义
│   ├── calibration/                 # Calibration module / 校准模块
│   │   ├── __init__.py              # Commands export
│   │   └── commands.py              # Calibration command builders / 校准命令构建
│   ├── network/                     # Network module / 网络模块
│   │   ├── __init__.py              # Network exports
│   │   ├── alarm.py                 # Alarm threshold commands / 报警阈值命令
│   │   ├── cloud_mqtt.py            # Aliyun MQTT (SET:KNS, SET:CMQ) / 阿里云MQTT
│   │   └── position_config.py       # Position config (SET:PO) / 位置配置
│   ├── sensors/                     # Sensors module / 传感器模块
│   │   ├── __init__.py              # Sensors exports
│   │   ├── install_mode.py          # Install mode (SET:ISG) / 安装模式
│   │   ├── filter.py                # Kalman filter (SET:KFQR, SS:17) / 卡尔曼滤波
│   │   ├── level_config.py          # Multi-level alarm (SET:GROLEVEL, SET:ACCLEVEL) / 多级报警
│   │   └── auxiliary.py             # Auxiliary sensors (SET:VKS, TME, MAGOF) / 辅助传感器
│   ├── system/                      # System module / 系统模块
│   │   ├── __init__.py              # System exports
│   │   ├── config_manager.py        # System config (SS:11, SS:12, SS:27) / 系统配置
│   │   ├── cpu_monitor.py           # CPU monitor (SS:5) / CPU监控
│   │   ├── sensor_cal.py            # Sensor calibration (SS:6) / 传感器校准
│   │   └── system_control.py        # System control (SS:14-18) / 系统控制
│   └── camera/                      # Camera module / 相机模块
│       ├── __init__.py              # Camera exports
│       ├── camera_control.py        # Camera control (SS:19-26, CA:2,9,10) / 相机控制
│       └── stream.py                # Video stream (SS:24, CA:1) / 视频流
├── scripts/                         # Standalone utility scripts / 独立工具脚本
│   ├── calibration.py               # Calibration algorithms (compute_six_position_calibration) / 校准算法
│   ├── activation.py                # Activation key generation (SHA-256) / 激活密钥生成
│   ├── network_config.py            # Network command builders / 网络命令构建
│   ├── data_pipeline.py             # Data processing pipeline / 数据处理管道
│   ├── performance_profile.py       # Performance profiling utilities / 性能分析工具
│   ├── read_docx.py                 # Document reading utility / 文档读取工具
│   └── serial_manager.py            # Legacy serial manager / 旧版串口管理
├── tests/                           # Test suite / 测试套件
│   ├── __init__.py
│   ├── test_data_processor.py       # DataProcessor unit tests / 数据处理器单元测试
│   ├── test_serial_manager.py       # SerialManager unit tests / 串口管理器单元测试
│   ├── test_integration.py          # Integration tests for algorithms / 集成测试
│   ├── test_commands.py             # New commands tests (SS:7, SS:9, SET:AGT) / 新命令测试
│   ├── test_calibration_status.py   # Calibration status tests / 校准状态测试
│   ├── test_ui_reset.py             # UI reset functionality tests / UI 重置测试
│   ├── test_sprint1_commands.py     # Sprint 1 commands tests / Sprint 1 指令测试
│   ├── test_sprint2_commands.py     # Sprint 2 commands tests / Sprint 2 指令测试
│   ├── test_sprint3_commands.py     # Sprint 3 commands tests / Sprint 3 指令测试
│   └── test_all_new_commands.py     # All new commands integration test / 所有新指令综合测试
├── archive/                         # Archived files / 归档文件
├── backups/                         # Backup storage / 备份存储
└── reports/                         # Output reports / 输出报告
```

---

## Build and Run Commands / 构建和运行命令

### Setup / 环境设置

```bash
# Create virtual environment / 创建虚拟环境
python -m venv .venv

# Activate (Windows) / 激活（Windows）
.venv\Scripts\activate

# Activate (Linux/Mac) / 激活（Linux/Mac）
source .venv/bin/activate

# Install dependencies / 安装依赖
pip install -r requirements.txt

# Install with dev dependencies / 安装开发依赖
pip install -e ".[dev]"
```

### Run Application / 运行应用程序

```bash
# Run the application / 运行应用程序
python main.py

# Or run as module / 或以模块方式运行
python -m sensor_calibrator
```

### Testing / 测试

```bash
# Run all tests / 运行所有测试
python -m pytest tests/

# Run with verbose output / 详细输出
python -m pytest tests/ -v

# Run specific test file / 运行特定测试文件
python -m pytest tests/test_integration.py -v

# Run with coverage / 带覆盖率报告
python -m pytest tests/ --cov=sensor_calibrator --cov-report=html

# Run unit tests only / 只运行单元测试
python -m pytest -m unit

# Run integration tests / 运行集成测试
python -m pytest -m integration

# Run integration tests directly / 直接运行集成测试
python tests/test_integration.py
```

---

## Code Style Guidelines / 代码风格规范

### Language / 语言

- **Comments and docstrings**: Use Chinese (Simplified) / 使用简体中文
- **Variable names**: Use English / 使用英文
- **String literals**: Use English for code, Chinese for user-facing messages / 代码用英文，用户界面用中文

### Formatting / 格式化

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']
```

```bash
# Format code / 格式化代码
python -m black sensor_calibrator/

# Check style / 检查风格
python -m flake8 sensor_calibrator/

# Type checking / 类型检查
python -m mypy sensor_calibrator/
```

### Type Hints / 类型提示

- Use type hints for function signatures / 为函数签名使用类型提示
- Import from `typing` module / 从 `typing` 模块导入
- Example:

```python
from typing import List, Tuple, Optional, Dict, Any

def process_data(data: List[float]) -> Tuple[float, float]:
    """计算均值和标准差"""
    return mean, std
```

### Docstring Format / 文档字符串格式

```python
def function_name(param: type) -> return_type:
    """
    函数功能的简要描述。
    
    更详细的描述（如需要）。
    
    Args:
        param: 参数描述
        
    Returns:
        返回值描述
        
    Raises:
        ValueError: 错误条件描述
    """
```

---

## Architecture / 架构

### Component Interaction / 组件交互

```
┌─────────────────────────────────────────────────────────────┐
│                    SensorCalibratorApp                       │
│  (Main application class in app/application.py)             │
└──────────────┬──────────────────────────────────────────────┘
               │
    ┌──────────┼──────────┬─────────────┬──────────────┐
    ▼          ▼          ▼             ▼              ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│UIManager│ │Serial  │ │SensorData│ │Chart     │ │Network   │
│         │ │Manager │ │Buffer    │ │Manager   │ │Manager   │
└────────┘ └────────┘ └──────────┘ └──────────┘ └──────────┘
                │            │
                ▼            ▼
          ┌──────────┐  ┌──────────────┐
          │Serial    │  │Calibration   │
          │Port      │  │Workflow      │
          └──────────┘  └──────────────┘
```

### Key Modules / 关键模块

| Module | Responsibility / 职责 |
|--------|----------------------|
| `SensorCalibratorApp` | Main application orchestration in `app/application.py` / 主应用编排 |
| `AppCallbacks` | UI event handlers in `app/callbacks.py` / UI 事件处理 |
| `UIManager` | GUI creation and layout in `ui_manager.py` / GUI 创建和布局 |
| `SerialManager` | Serial port I/O and threading in `serial_manager.py` / 串口 I/O 和线程 |
| `SensorDataBuffer` | Data parsing and storage in `data_buffer.py` / 数据解析和存储 |
| `ChartManager` | Matplotlib visualization with blit optimization in `chart_manager.py` / 图表可视化 |
| `CalibrationWorkflow` | 6-position calibration logic in `calibration_workflow.py` / 六位置校准逻辑 |
| `ActivationWorkflow` | MAC-based activation in `activation_workflow.py` / 基于 MAC 的激活 |
| `NetworkManager` | WiFi/MQTT/OTA/Alarm configuration in `network_manager.py` / 网络配置 |

### Data Flow / 数据流

1. **SerialManager** reads data from sensor via serial port / 从传感器通过串口读取数据
2. **SensorDataBuffer** parses and stores data in circular buffers / 解析并存储数据到循环缓冲区
3. **ChartManager** displays data using matplotlib with blit optimization / 使用 matplotlib 显示数据
4. **CalibrationWorkflow** processes data for calibration / 处理校准数据

---

## Configuration / 配置

### Key Config Classes / 关键配置类

Located in `sensor_calibrator/config.py`:

```python
class Config:
    """Main configuration / 主配置"""
    # Performance
    ENABLE_BLIT_OPTIMIZATION = True   # Enable blit for faster rendering
    ENABLE_WINDOW_MOVE_PAUSE = True   # Pause updates during window move
    ENABLE_DATA_DECIMATION = True     # Enable data sampling for display
    
    # Data Management
    MAX_DATA_POINTS = 2000            # Max data points to retain
    DISPLAY_DATA_POINTS = 200         # Points to display on charts
    STATS_WINDOW_SIZE = 100           # Samples for statistics calculation
    
    # Timing
    UPDATE_INTERVAL_MS = 100          # GUI update interval (milliseconds)
    CHART_UPDATE_INTERVAL = 0.1       # Chart refresh rate (10 FPS)
    
    # Calibration
    CALIBRATION_SAMPLES = 100         # Samples per position
    GRAVITY_CONSTANT = 9.8015         # Standard gravity (m/s)
    
    # UI
    WINDOW_WIDTH = 1920
    WINDOW_HEIGHT = 1080

class SerialConfig:
    """Serial communication / 串口通信"""
    TIMEOUT = 0.1
    BAUD_RATES = [9600, 19200, 38400, 57600, 115200]
    DEFAULT_BAUD = 115200

class UIConfig:
    """UI settings / UI 设置"""
    TITLE = "MPU6050 & ADXL355 Sensor Calibration System"
    SCALING_FACTOR = 1.2
    LEFT_PANEL_WIDTH = 430
```

### SS Commands / SS 命令

The sensor uses SS command protocol / 传感器使用 SS 命令协议:

| Command | ID | Description | Command String |
|---------|-----|-------------|----------------|
| SS:0 | 0 | Start data stream / 开始数据流 | `SS:0\n` |
| SS:1 | 1 | Start calibration stream / 开始校准流 | `SS:1\n` |
| SS:2 | 2 | Local coordinate mode / 局部坐标模式 | `SS:2\n` |
| SS:3 | 3 | Global coordinate mode / 全局坐标模式 | `SS:3\n` |
| SS:4 | 4 | Stop stream / 停止数据流 | `SS:4\n` |
| SS:7 | 7 | Save configuration / 保存配置 | `SS:7\n` |
| SS:8 | 8 | Get sensor properties / 获取传感器属性 | `SS:8\n` |
| SS:9 | 9 | Restart sensor / 重启传感器 | `SS:9\n` |

### Other Commands / 其他命令

| Command | Format | Description |
|---------|--------|-------------|
| SET:WF | `SET:WF,<ssid>,<password>` | Set WiFi configuration |
| SET:MQ | `SET:MQ,<broker>,<port>,<username>,<password>` | Set MQTT configuration |
| SET:OTA | `SET:OTA,<url1>,<url2>,<url3>,<url4>` | Set OTA URLs |
| SET:ALARM | `SET:ALARM,<accel>,<gyro>` | Set alarm thresholds |
| SET:RACKS | `SET:RACKS,<x>,<y>,<z>` | Set MPU6050 accel scale |
| SET:RACOF | `SET:RACOF,<x>,<y>,<z>` | Set MPU6050 accel offset |
| SET:REACKS | `SET:REACKS,<x>,<y>,<z>` | Set ADXL355 accel scale |
| SET:REACOF | `SET:REACOF,<x>,<y>,<z>` | Set ADXL355 accel offset |
| SET:VROOF | `SET:VROOF,<x>,<y>,<z>` | Set MPU6050 gyro offset |

### Sprint 1-3: New Commands / 新增指令

#### SET Commands / SET 指令集

| Command | Format | Description | Status |
|---------|--------|-------------|--------|
| SET:KNS | `SET:KNS,<product_key>,<device_name>,<device_secret>` | Aliyun MQTT configuration / 阿里云MQTT配置 | ✅ Implemented |
| SET:CMQ | `SET:CMQ,<mode>` | MQTT mode (1=local, 10=Aliyun) / MQTT模式切换 | ✅ Implemented |
| SET:PO | `SET:PO,<region>,<building>,<user>,<device>` | Position configuration / 位置配置 | ✅ Implemented |
| SET:ISG | `SET:ISG,<mode>` | Install mode (0-12) / 安装模式 | ✅ Implemented |
| SET:KFQR | `SET:KFQR,<Q>,<R>` | Kalman filter coefficients / 卡尔曼滤波系数 | ✅ Implemented |
| SET:GROLEVEL | `SET:GROLEVEL,<l1>,<l2>,<l3>,<l4>,<l5>` | Gyro 5-level alarm / 角度5级报警 | ✅ Implemented |
| SET:ACCLEVEL | `SET:ACCLEVEL,<l1>,<l2>,<l3>,<l4>,<l5>` | Accel 5-level alarm / 加速度5级报警 | ✅ Implemented |
| SET:VKS | `SET:VKS,<scale1>,<scale2>` | Voltage sensor scale / 电压传感器比例 | ✅ Implemented |
| SET:TME | `SET:TME,<offset>` | Temperature offset / 温度传感器偏移 | ✅ Implemented |
| SET:MAGOF | `SET:MAGOF,<x>,<y>,<z>` | Magnetometer offset / 磁力传感器零偏 | ✅ Implemented |

#### SS Commands / SS 指令集

| Command | ID | Description | Status |
|---------|-----|-------------|--------|
| SS:5 | 5 | CPU monitor mode / CPU监控模式 | ✅ Implemented |
| SS:6 | 6 | Sensor calibration mode / 传感器校准模式 | ✅ Implemented |
| SS:11 | 11 | Restore default config / 恢复默认配置 | ✅ Implemented |
| SS:12 | 12 | Save sensor config / 保存传感器配置 | ✅ Implemented |
| SS:14 | 14 | Buzzer long beep / 喇叭长响 | ✅ Implemented |
| SS:15 | 15 | Check upgrade / 监查升级 | ✅ Implemented |
| SS:16 | 16 | AP config mode / 进入AP配置模式 | ✅ Implemented |
| SS:17 | 17 | Toggle filter / 开启/关闭滤波 | ✅ Implemented |
| SS:18 | 18 | Switch MQTT mode / 切换MQTT模式 | ✅ Implemented |
| SS:19 | 19 | Camera photo mode / 拍照模式 | ✅ Implemented |
| SS:21 | 21 | Monitoring mode / 监测模式 | ✅ Implemented |
| SS:22 | 22 | Timelapse mode / 时程传输模式 | ✅ Implemented |
| SS:23 | 23 | Reboot camera slave / 重启摄像机下位机 | ✅ Implemented |
| SS:24 | 24 | Start camera stream / 开启摄像机串流 | ✅ Implemented |
| SS:25 | 25 | Take photo / 控制拍照 | ✅ Implemented |
| SS:26 | 26 | Force camera OTA / 强制摄像机OTA升级 | ✅ Implemented |
| SS:27 | 27 | Deactivate sensor / 传感器反激活 | ✅ Implemented |

#### CA Commands / CA 指令集 (Camera)

| Command | ID | Description | Status |
|---------|-----|-------------|--------|
| CA:1 | 1 | Start push stream / 开启相机推流 | ✅ Implemented |
| CA:2 | 2 | Take photo / 控制拍照 | ✅ Implemented |
| CA:9 | 9 | Reboot camera module / 重启摄像机模组 | ✅ Implemented |
| CA:10 | 10 | Force ESP32 S3 OTA / 强制ESP32 S3 OTA升级 | ✅ Implemented |

**Note**: SS:10 (SD storage) is not implemented as per user request.

---

## Testing Strategy / 测试策略

### Test Organization / 测试组织

```
tests/
├── test_data_processor.py    # Unit tests for data processing / 数据处理单元测试
├── test_serial_manager.py    # SerialManager unit tests / SerialManager 单元测试
├── test_integration.py       # Integration tests (algorithms, activation, network) / 集成测试
├── test_commands.py          # New command validation tests (SS:7, SS:9, SET:AGT) / 命令测试
├── test_calibration_status.py # Calibration status tests / 校准状态测试
└── test_ui_reset.py          # UI reset functionality tests / UI 重置测试
```

### Test Markers / 测试标记

```ini
# pytest.ini
markers =
    unit: Unit tests / 单元测试
    integration: Integration tests / 集成测试
    slow: Slow running tests / 慢速测试
```

### Running Tests / 运行测试

```bash
# Run unit tests only / 只运行单元测试
python -m pytest -m unit

# Run integration tests / 运行集成测试
python -m pytest -m integration

# Run with coverage / 带覆盖率运行
python -m pytest --cov=sensor_calibrator --cov-report=html
```

---

## Development Conventions / 开发规范

### File Organization / 文件组织

1. **New features** should be added to `sensor_calibrator/` package / 新功能应添加到 `sensor_calibrator/` 包
2. **Utility scripts** can be placed in `scripts/` directory / 工具脚本可放在 `scripts/` 目录
3. **Tests** must be added to `tests/` with `test_` prefix / 测试必须添加到 `tests/` 并以 `test_` 前缀命名

### Import Patterns / 导入模式

```python
# Preferred: Import from package / 推荐：从包导入
from sensor_calibrator import Config, SensorDataBuffer
from sensor_calibrator.config import SerialConfig

# Lazy loading via __getattr__ in __init__.py / 通过 __init__.py 中的 __getattr__ 懒加载
from sensor_calibrator import SerialManager  # Loaded on first access
```

### Error Handling / 错误处理

- Use specific exceptions / 使用具体异常
- Log errors via callbacks / 通过回调记录错误
- Graceful degradation for UI / UI 优雅降级

```python
try:
    result = risky_operation()
except SerialException as e:
    self._log_message(f"Serial error: {e}", "ERROR")
except Exception as e:
    self._log_message(f"Unexpected error: {e}", "ERROR")
```

---

## Security Considerations / 安全考虑

1. **MAC Address Handling / MAC 地址处理**: Used for activation key generation via SHA-256 / 用于激活密钥生成
2. **Key Verification / 密钥验证**: Uses SHA-256 and constant-time comparison via `secrets.compare_digest()` / 使用 SHA-256 和恒定时间比较
3. **Key Fragment / 密钥片段**: Only positions 5-12 (7 chars) of the 64-char SHA-256 hash are used for display/verification / 只使用 64 字符哈希的位置 5-12
4. **Serial Port Security / 串口安全**: Validate port names before connection / 连接前验证端口名称
5. **No Hardcoded Credentials / 无硬编码凭据**: All credentials from user input or config files / 所有凭据来自用户输入或配置文件

---

## Calibration Algorithm / 校准算法

### Six-Position Calibration / 六位置校准

Located in `scripts/calibration.py`:

```python
def compute_six_position_calibration(axis_samples, gravity):
    """
    axis_samples: 6 positions [+X, -X, +Y, -Y, +Z, -Z]
    Returns: (scales, offsets)
    """
    offset = (pos_val + neg_val) / 2.0
    delta = pos_val - neg_val
    scale = 2.0 * gravity / delta
    return scale, offset
```

### Gyro Offset Calculation / 陀螺仪偏移计算

```python
def compute_gyro_offset(samples):
    """Calculate mean offset from stationary samples"""
    return np.mean(samples, axis=0)
```

---

## Common Tasks / 常见任务

### Adding a New SS Command / 添加新的 SS 命令

1. Add command ID constant to `config.py` / 添加命令 ID 常量到 `config.py`:
   ```python
   CMD_NEW_COMMAND: Final[int] = 10
   ```

2. Add constant to `sensor_calibrator/serial/protocol.py` / 添加常量到协议模块:
   ```python
   SS_NEW_COMMAND = 10
   ```

3. Add build function to `protocol.py` / 添加构建函数:
   ```python
   def build_ss10_new_command() -> str:
       return build_ss_command(10, "New Command")
   ```

4. Add send method to `SerialManager` / 在 `SerialManager` 中添加发送方法:
   ```python
   def send_ss10_new_command(self) -> bool:
       return self.send_ss_command(10, "New Command")
   ```

5. Export from `serial/__init__.py` / 从 `serial/__init__.py` 导出

6. Add tests to `tests/test_commands.py` / 添加测试到 `tests/test_commands.py`

### Adding a New Calibration Feature / 添加新的校准功能

1. Add algorithm to `scripts/calibration.py` / 添加算法到 `scripts/calibration.py`
2. Integrate into `CalibrationWorkflow` / 集成到 `CalibrationWorkflow`
3. Add UI controls to `UIManager` / 在 `UIManager` 中添加 UI 控件
4. Connect callbacks in `app/callbacks.py` / 在 `app/callbacks.py` 中连接回调

---

## Troubleshooting / 故障排除

### Common Issues / 常见问题

1. **Serial port permission denied / 串口权限被拒绝**: Run with appropriate permissions / 使用适当权限运行
2. **Matplotlib backend issues / Matplotlib 后端问题**: Ensure `tkinter` support / 确保 `tkinter` 支持
3. **Import errors / 导入错误**: Check virtual environment activation / 检查虚拟环境激活状态
4. **Data not displaying / 数据不显示**: Check if data stream is started (SS:0) / 检查是否已启动数据流

### Debug Logging / 调试日志

Enable verbose logging via callbacks / 通过回调启用详细日志:

```python
self.callbacks['log_message'](f"Debug: {variable}", "DEBUG")
```

---

## Version History / 版本历史

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial release / 初始版本 |

---

## References / 参考资料

- [README.md](README.md) - User documentation / 用户文档
- [CHANGELOG.md](CHANGELOG.md) - Version history / 版本历史
- [pyproject.toml](pyproject.toml) - Project metadata / 项目元数据
