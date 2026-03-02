# SensorCalibrator

MPU6050 & ADXL355 传感器校准应用程序

A professional sensor calibration application for MPU6050 (6-axis IMU) and ADXL355 (high-precision accelerometer) sensors. Provides six-position calibration, real-time data visualization, and network configuration capabilities.

## 功能特性

- **串口通信**: 支持多种波特率，自动检测可用串口
- **实时数据可视化**: 使用 matplotlib 实现实时图表显示
- **六位置校准**: 完整的六位置加速度计校准算法
- **传感器激活**: 基于 MAC 地址的激活验证机制
- **网络配置**: WiFi、MQTT、OTA 固件更新配置
- **多坐标模式**: 支持局部坐标系和全局坐标系

## 系统要求

- Python 3.8+
- Windows 10/11 (串口通信)
- 硬件: MPU6050 + ADXL355 传感器模块

## 安装

### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd SensorCalibrator
```

### 2. 创建虚拟环境 (推荐)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 连接硬件

1. 将传感器模块通过 USB 连接到电脑
2. 记下分配的串口 (如 COM3)

### 2. 运行程序

```bash
python StableSensorCalibrator.py
```

### 3. 基本校准流程

1. **连接串口**: 选择端口，点击 "Connect"
2. **开始数据流**: 点击 "Start Data Stream"
3. **六位置校准**:
   - 将传感器放置在 +X 轴向下位置
   - 点击 "Capture Position"
   - 依次完成 6 个位置的采集
4. **保存参数**: 点击 "Save Calibration Parameters"

## 项目结构

```
SensorCalibrator/
├── StableSensorCalibrator.py    # 主程序入口
├── calibration.py                # 校准算法
├── activation.py                 # 激活验证
├── network_config.py             # 网络配置
├── sensor_calibrator/            # 核心模块包
│   ├── __init__.py
│   ├── config.py                 # 配置常量
│   ├── serial_manager.py         # 串口管理
│   ├── data_processor.py          # 数据处理
│   ├── chart_manager.py          # 图表管理
│   ├── ui_manager.py             # UI管理
│   ├── network_manager.py        # 网络管理
│   ├── calibration_workflow.py   # 校准工作流
│   └── activation_workflow.py    # 激活工作流
└── tests/                        # 测试目录
    ├── test_data_processor.py
    ├── test_serial_manager.py
    └── test_integration.py
```

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 带覆盖率报告
python -m pytest tests/ --cov=sensor_calibrator --cov-report=html

# 运行特定测试文件
python -m pytest tests/test_integration.py -v
```

## 配置说明

### 串口配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 波特率 | 115200 | 支持 9600-115200 |
| 超时 | 0.1s | 串口读取超时 |

### 校准配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 采样数/位置 | 100 | 每个位置采集的样本数 |
| 期望频率 | 100 Hz | 传感器数据频率 |

### 图表配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 最大数据点 | 2000 | 内存保留的最大数据量 |
| 显示数据点 | 200 | 图表显示的数据点数量 |
| 更新间隔 | 100ms | GUI 更新频率 (10 FPS) |

## 校准算法

### 六位置校准原理

六位置校准利用地球重力矢量在不同姿态下的投影来计算传感器的比例因子和偏移量：

```
位置定义:
+ X 轴向下: 重力投影在 X 轴为 +g
- X 轴向下: X 轴为 - 重力投影在g
+ Y 轴向下: 重力投影在 Y 轴为 + 轴向下: 重 轴为 -g力投影在 Y
+ Z 轴g
- Y向下: 重力投影在 Z 轴为 +g (水平放置)
- Z 轴向下: 重力投影在 Z 轴为 -g
```

### 计算公式

```
offset[i] = (pos_val[i] + neg_val[i]) /scale[i] = 2
 gravity / ((pos_val[i] - neg_val[i]) / 2)
```

## 激活机制

传感器激活使用基于 MAC 地址的密钥验证：

1. 从传感器属性中读取 MAC 地址
2. 使用 SHA-256 生成64 字符密钥 
3. 取密钥片段 (位置 5-12) 进行显示和验证

## 常见问题

### Q: 程序无法连接串口
A: 
- 检查串口是否被其他程序占用
- 确认传感器模块已正确连接
- 尝试更换波特率

### Q: 校准结果不理想
A:
- 确保传感器在采集期间保持静止
- 检查是否有振动干扰
- 确认六个位置的角度准确

### Q: 图表不更新
A:
- 检查是否已点击 "Start Data Stream"
- 查看 Log Output 区域是否有错误信息

## 开发指南

### 添加新功能

1. 在 `sensor_calibrator/` 目录下创建新模块
2. 更新 `__init__.py` 导出新模块
3. 在主程序中添加对应的 UI 和回调

### 运行开发测试

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/ -v

# 代码格式化 (如安装了 black)
python -m black sensor_calibrator/
```

## 依赖清单

```
pyserial>=3.5    # 串口通信
numpy>=1.21      # 数值计算
matplotlib>=3.5 # 数据可视化
pytest>=7.0     # 单元测试
```

## 许可证

MIT License

## 作者

SensorCalibrator Team

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)
