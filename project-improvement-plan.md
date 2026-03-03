# SensorCalibrator 项目改进计划

**生成日期**: 2026-03-02
**预估复杂度**: 中等

## 概述

本计划针对 SensorCalibrator 项目进行系统性改进，基于代码审查发现的问题按优先级排序。计划分为 4 个迭代阶段，每个阶段产生可演示、可测试的增量成果。

## 当前项目状态

- **项目类型**: 传感器校准应用 (MPU6050 & ADXL355)
- **主要组件**: GUI (Tkinter)、串口通信、数据处理、校准算法
- **现有问题**: 缺少依赖管理、测试覆盖不足、文档缺失、代码组织需优化

## 改进优先级

| 优先级 | 问题 | 影响 |
|--------|------|------|
| P0 (阻塞) | 缺少依赖清单 | 无法保证环境一致性，其他开发无法正常运行 |
| P1 (高) | 测试覆盖不足 | 重构风险高，无法验证正确性 |
| P2 (中) | 缺少文档 | 新成员无法上手使用 |
| P3 (中) | 主文件过大 | 维护困难，代码理解成本高 |
| P4 (低) | 类型标注不完整 | 长期可维护性 |
| P5 (低) | Magic Numbers | 长期可维护性 |

---

## Sprint 1: 基础依赖与环境 (第1天)

**目标**: 建立可复现的开发环境，确保项目可运行

**验证方式**:
- [ ] `pip install -r requirements.txt` 成功
- [ ] `python -c "from sensor_calibrator import Config"` 成功
- [ ] 主程序可正常启动 (无导入错误)

### Task 1.1: 创建 requirements.txt

- **位置**: `requirements.txt` (新建)
- **描述**: 根据项目 import 分析，创建完整依赖清单
- **依赖**: 无
- **验收标准**:
  - 包含 pyserial, numpy, matplotlib, tkinter (系统自带)
  - 指定版本范围或最低版本
- **验证方法**:
  ```bash
  pip install -r requirements.txt
  python -c "import serial; import numpy; import matplotlib"
  ```

**需要包含的依赖**:
```
pyserial>=3.5
numpy>=1.21
matplotlib>=3.5
```

### Task 1.2: 创建 pyproject.toml (可选，增强版)

- **位置**: `pyproject.toml` (新建)
- **描述**: 使用现代 Python 项目标准，支持 pip install -e .
- **依赖**: Task 1.1
- **验收标准**:
  - 包含项目元数据 (name, version, authors)
  - 声明 Python 版本要求
  - 指定依赖

---

## Sprint 2: 测试体系建设 (第2-3天)

**目标**: 建立基础测试覆盖，确保后续重构的安全性

**验证方式**:
- [ ] `python -m pytest` 运行无错误
- [ ] 核心类 (DataProcessor, SerialManager) 有单元测试
- [ ] 测试覆盖率 > 60%

### Task 2.1: 补充 DataProcessor 单元测试

- **位置**: `tests/test_data_processor.py` (新建)
- **描述**: 测试数据解析、统计计算、清空等核心功能
- **依赖**: Sprint 1 完成
- **验收标准**:
  - 测试 parse_sensor_data 正常解析
  - 测试 parse_sensor_data 异常输入处理
  - 测试 calculate_statistics 边界情况
  - 测试 update_statistics 更新逻辑
  - 测试 clear_all 重置状态
- **验证方法**:
  ```bash
  python -m pytest tests/test_data_processor.py -v
  ```

### Task 2.2: 补充 SerialManager 单元测试

- **位置**: `tests/test_serial_manager.py` (新建)
- **描述**: 测试串口管理器的连接、发送、监听等核心功能
- **依赖**: Sprint 1 完成
- **验收标准**:
  - 测试 add_listener / remove_listener
  - 测试 send_line 编码处理
  - 测试 request_response 超时逻辑 (使用 mock)
  - 测试多 listener 广播
- **验证方法**:
  ```bash
  python -m pytest tests/test_serial_manager.py -v
  ```

### Task 2.3: 完善现有集成测试

- **位置**: `tests/test_integration.py` (修改)
- **描述**: 将现有的 stub 测试改为实际可运行的测试
- **依赖**: Task 2.1, 2.2
- **验收标准**:
  - calibration.py 的校准算法有实际测试数据验证
  - activation.py 的密钥生成与验证有完整测试
  - 网络命令构建有实际输出验证

### Task 2.4: 配置测试运行器

- **位置**: `pytest.ini` 或 `pyproject.toml` (新建/修改)
- **描述**: 配置 pytest 发现规则、覆盖率报告
- **依赖**: Task 2.1-2.3
- **验收标准**:
  - `python -m pytest --cov=sensor_calibrator` 可运行
  - 生成覆盖率报告

---

## Sprint 3: 文档与上手指南 (第4天)

**目标**: 让新成员能快速上手项目

**验证方式**:
- [ ] README.md 存在且内容完整
- [ ] 新手按文档可完成首次校准操作

### Task 3.1: 创建 README.md

- **位置**: `README.md` (新建)
- **描述**: 项目主文档
- **依赖**: Sprint 1 完成
- **验收标准**:
  - 包含项目简介 (一句话描述)
  - 包含功能列表 (串口通信、六位置校准、图表显示等)
  - 包含安装步骤 (pip install -r requirements.txt)
  - 包含快速开始指南 (连接设备 -> 开始校准)
  - 包含依赖版本要求
  - 包含运行测试的方法

### Task 3.2: 创建 CHANGELOG.md

- **位置**: `CHANGELOG.md` (新建)
- **描述**: 记录版本变更历史
- **依赖**: Task 3.1
- **验收标准**:
  - 包含 v1.0 版本说明
  - 包含未来计划功能列表

---

## Sprint 4: 代码质量提升 (第5-7天)

**目标**: 改进代码组织与长期可维护性

**验证方式**:
- [ ] 主文件行数减少 > 30%
- [ ] 无类型错误 (运行 mypy 或 pyright)

### Task 4.1: 重构主文件 - 提取 UI 回调

- **位置**: `StableSensorCalibrator.py` (重构)
- **描述**: 将回调函数提取到独立的 callback_handler.py
- **依赖**: Sprint 2 完成 (测试保障)
- **验收标准**:
  - 提取所有以 `_on_`, `toggle_`, `set_`, `send_` 开头的回调方法
  - 主文件行数减少 200+ 行
  - 原有功能不受影响

### Task 4.2: 补充类型标注

- **位置**: 多个文件 (修改)
- **描述**: 补充缺失的函数返回类型标注
- **依赖**: Sprint 2 完成
- **验收标准**:
  - `StableSensorCalibrator.py` 所有公共方法有类型标注
  - `sensor_calibrator/` 下模块类型标注完整度 > 80%

### Task 4.3: 提取 Magic Numbers

- **位置**: `sensor_calibrator/config.py` (扩展)
- **描述**: 将散布在代码中的硬编码值提取为配置常量
- **依赖**: Sprint 2 完成
- **验收标准**:
  - OTA 默认端口 "1883" 提取为常量
  - 其他重复出现的硬编码值提取

---

## Sprint 5: 自动化与工具 (可选，第8天)

**目标**: 建立持续质量保障

### Task 5.1: 配置 pre-commit 钩子

- **位置**: `.pre-commit-config.yaml` (新建)
- **描述**: 配置代码格式检查
- **依赖**: Sprint 4 完成
- **验收标准**:
  - 配置 black (格式化)
  - 配置 isort (import 排序)
  - 配置 flake8 (代码检查)

### Task 5.2: 配置 CI/CD

- **位置**: `.github/workflows/test.yml` (新建)
- **描述**: GitHub Actions 自动测试
- **依赖**: Task 5.1
- **验收标准**:
  - Push 时自动运行测试
  - 测试失败时通知

---

## 测试策略

### 单元测试 (Sprint 2)
- **DataProcessor**: 100% 覆盖
- **SerialManager**: 连接/发送/监听核心路径覆盖
- **Calibration**: 边界条件测试
- **Activation**: 各种 MAC 地址格式测试

### 集成测试 (持续)
- **test_integration.py**: 端到端功能测试

### 测试运行命令
```bash
# 运行所有测试
python -m pytest

# 带覆盖率
python -m pytest --cov=sensor_calibrator --cov-report=html

# 仅单元测试
python -m pytest tests/ -k "not integration"
```

---

## 潜在风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 主文件重构破坏现有功能 | 高 | Sprint 2 先建立测试覆盖 |
| 依赖版本冲突 | 中 | 使用虚拟环境测试 |
| 重构工作量超预期 | 中 | 优先保证核心功能可用 |

---

## 回滚计划

- **Sprint 1**: 无需回滚，requirements.txt 可随时修改
- **Sprint 2**: 测试文件独立，不会影响主代码
- **Sprint 3**: README.md 可随时重写
- **Sprint 4**: 
  - 使用 `git diff` 对比改动
  - 每次重构后运行测试验证
  - 必要时 `git checkout` 回退

---

## 预估工时

| Sprint | 任务 | 预估时间 |
|--------|------|----------|
| Sprint 1 | 依赖与环境 | 0.5 天 |
| Sprint 2 | 测试体系 | 2 天 |
| Sprint 3 | 文档 | 0.5 天 |
| Sprint 4 | 代码质量 | 2 天 |
| Sprint 5 | 自动化 (可选) | 0.5 天 |
| **总计** | | **~5 天** |

---

## 开始执行

建议按顺序执行各 Sprint，每个 Sprint 完成后：
1. 运行相关测试验证
2. 提交代码 (`git add . && git commit`)
3. 如有问题，使用 `git checkout` 回退

是否需要我开始执行某个 Sprint？
