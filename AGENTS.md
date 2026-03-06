# SensorCalibrator - AI Agent Guide

> This file provides essential information for AI coding agents working on the SensorCalibrator project.
> 
> 本文件为在 SensorCalibrator 项目上工作的 AI 编程代理提供关键信息。

## Project Overview / 项目概览

**SensorCalibrator** is a Python desktop application for calibrating MPU6050 (6-axis IMU) and ADXL355 (high-precision accelerometer) sensors. It provides a complete calibration workflow including six-position calibration, real-time data visualization, sensor activation verification, and network configuration.

**SensorCalibrator** 是一个用于校准 MPU6050（6轴IMU）和 ADXL355（高精度加速度计）传感器的 Python 桌面应用程序。它提供完整的校准工作流程，包括六位置校准、实时数据可视化、传感器激活验证和网络配置。

### Key Features / 主要功能

- **Serial Communication / 串口通信**: Multi-baudrate support, auto port detection / 支持多种波特率，自动检测可用串口
- **Real-time Visualization / 实时可视化**: Live charts using matplotlib / 使用 matplotlib 实现实时图表显示
- **Six-Position Calibration / 六位置校准**: Complete accelerometer calibration algorithm / 完整的加速度计校准算法
- **Sensor Activation / 传感器激活**: MAC-based key verification / 基于 MAC 地址的密钥验证机制
- **Network Configuration / 网络配置**: WiFi, MQTT, and OTA firmware update support / 支持 WiFi、MQTT 和 OTA 固件更新
- **Dual Coordinate Modes / 双坐标模式**: Local and global coordinate system support / 支持局部坐标系和全局坐标系

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
├── pyproject.toml                   # Project configuration / 项目配置
├── pytest.ini                       # Test configuration / 测试配置
├── requirements.txt                 # Dependencies / 依赖清单
├── config/
│   └── sensor_properties.json       # Sensor configuration storage / 传感器配置文件
├── sensor_calibrator/               # Core package / 核心包
│   ├── __init__.py                  # Package exports / 包导出
│   ├── app/
│   │   ├── application.py           # Main application class / 主应用类
│   │   └── callbacks.py             # UI callbacks / UI 回调
│   ├── config.py                    # Configuration constants / 配置常量
│   ├── serial_manager.py            # Serial port management / 串口管理
│   ├── data_processor.py            # Data parsing & statistics / 数据解析和统计
│   ├── chart_manager.py             # Matplotlib charts / 图表管理
│   ├── ui_manager.py                # GUI components / UI 组件
│   ├── network_manager.py           # WiFi/MQTT/OTA config / 网络管理
│   ├── calibration_workflow.py      # 6-position calibration / 校准工作流
│   ├── activation_workflow.py       # Sensor activation / 激活工作流
│   ├── data_buffer.py               # Data buffering / 数据缓冲
│   ├── ring_buffer.py               # Ring buffer implementation / 环形缓冲区
│   └── log_throttler.py             # Log rate limiting / 日志限流
├── scripts/                         # Standalone utility scripts / 独立工具脚本
│   ├── calibration.py               # Calibration algorithms / 校准算法
│   ├── activation.py                # Activation key generation / 激活密钥生成
│   ├── network_config.py            # Network command builders / 网络命令构建
│   └── ...
├── tests/                           # Test suite / 测试套件
│   ├── test_data_processor.py       # DataProcessor tests / 数据处理器测试
│   ├── test_serial_manager.py       # SerialManager tests / 串口管理器测试
│   ├── test_integration.py          # Integration tests / 集成测试
│   └── test_commands.py             # Command tests / 命令测试
└── archive/                         # Archived files / 归档文件
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
│UIManager│ │Serial  │ │Data      │ │Chart     │ │Network   │
│         │ │Manager │ │Processor │ │Manager   │ │Manager   │
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
| `SensorCalibratorApp` | Main application orchestration / 主应用编排 |
| `UIManager` | GUI creation and layout / GUI 创建和布局 |
| `SerialManager` | Serial port I/O and threading / 串口 I/O 和线程 |
| `DataProcessor` | Data parsing and statistics / 数据解析和统计 |
| `ChartManager` | Matplotlib visualization / Matplotlib 可视化 |
| `CalibrationWorkflow` | 6-position calibration logic / 六位置校准逻辑 |
| `ActivationWorkflow` | MAC-based activation / 基于 MAC 的激活 |
| `NetworkManager` | WiFi/MQTT/OTA configuration / WiFi/MQTT/OTA 配置 |

### Data Flow / 数据流

1. **SerialManager** reads data from sensor via serial port / 从传感器通过串口读取数据
2. **DataProcessor** parses and stores data in circular buffers / 解析并存储数据到循环缓冲区
3. **ChartManager** displays data using matplotlib / 使用 matplotlib 显示数据
4. **CalibrationWorkflow** processes data for calibration / 处理校准数据

---

## Configuration / 配置

### Key Config Classes / 关键配置类

Located in `sensor_calibrator/config.py`:

```python
class Config:
    """Main configuration / 主配置"""
    MAX_DATA_POINTS = 2000          # Max data points to retain / 最大保留数据点数
    UPDATE_INTERVAL_MS = 100        # GUI update interval / GUI 更新间隔
    CALIBRATION_SAMPLES = 100       # Samples per position / 每位置采样数
    GRAVITY_CONSTANT = 9.8015       # Standard gravity / 标准重力

class SerialConfig:
    """Serial communication / 串口通信"""
    TIMEOUT = 0.1
    BAUD_RATES = [9600, 19200, 38400, 57600, 115200]

class UIConfig:
    """UI settings / UI 设置"""
    WINDOW_WIDTH = 1920
    WINDOW_HEIGHT = 1080
```

### SS Commands / SS 命令

The sensor uses SS command protocol / 传感器使用 SS 命令协议:

| Command | ID | Description |
|---------|-----|-------------|
| SS:0 | 0 | Start data stream / 开始数据流 |
| SS:1 | 1 | Start calibration stream / 开始校准流 |
| SS:2 | 2 | Local coordinate mode / 局部坐标模式 |
| SS:3 | 3 | Global coordinate mode / 全局坐标模式 |
| SS:4 | 4 | Stop stream / 停止数据流 |
| SS:7 | 7 | Save configuration / 保存配置 |
| SS:8 | 8 | Get sensor properties / 获取传感器属性 |
| SS:9 | 9 | Restart sensor / 重启传感器 |

---

## Testing Strategy / 测试策略

### Test Organization / 测试组织

```
tests/
├── test_data_processor.py    # Unit tests for data processing / 数据处理单元测试
├── test_serial_manager.py    # SerialManager unit tests / SerialManager 单元测试
├── test_integration.py       # Integration tests / 集成测试
└── test_commands.py          # Command validation tests / 命令验证测试
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
from sensor_calibrator import Config, DataProcessor
from sensor_calibrator.config import SerialConfig

# For scripts / 对于脚本
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sensor_calibrator import Config
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

1. **MAC Address Handling / MAC 地址处理**: Used for activation key generation / 用于激活密钥生成
2. **Key Verification / 密钥验证**: Uses SHA-256 and constant-time comparison / 使用 SHA-256 和恒定时间比较
3. **Serial Port Security / 串口安全**: Validate port names before connection / 连接前验证端口名称
4. **No Hardcoded Credentials / 无硬编码凭据**: All credentials from user input or config files / 所有凭据来自用户输入或配置文件

---

## Common Tasks / 常见任务

### Adding a New SS Command / 添加新的 SS 命令

1. Add command ID constant to `config.py` / 添加命令 ID 常量到 `config.py`:
   ```python
   CMD_NEW_COMMAND: Final[int] = 10
   ```

2. Add send method to `SerialManager` / 在 `SerialManager` 中添加发送方法:
   ```python
   def send_ss10_new_command(self, description: str = "") -> bool:
       return self.send_ss_command(10, description)
   ```

3. Add tests to `tests/test_integration.py` / 添加测试到 `tests/test_integration.py`

### Adding a New Calibration Feature / 添加新的校准功能

1. Add algorithm to `scripts/calibration.py` / 添加算法到 `scripts/calibration.py`
2. Integrate into `CalibrationWorkflow` / 集成到 `CalibrationWorkflow`
3. Add UI controls to `UIManager` / 在 `UIManager` 中添加 UI 控件
4. Connect callbacks in `application.py` / 在 `application.py` 中连接回调

---

## Troubleshooting / 故障排除

### Common Issues / 常见问题

1. **Serial port permission denied / 串口权限被拒绝**: Run with appropriate permissions / 使用适当权限运行
2. **Matplotlib backend issues / Matplotlib 后端问题**: Ensure `tkinter` support / 确保 `tkinter` 支持
3. **Import errors / 导入错误**: Check virtual environment activation / 检查虚拟环境激活状态

### Debug Logging / 调试日志

Enable verbose logging in callbacks / 在回调中启用详细日志:

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
