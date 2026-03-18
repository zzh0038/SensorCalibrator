# Plan: 添加缺失的传感器指令集

**Generated**: 2026-03-17  
**Estimated Complexity**: High  
**Status**: Draft

---

## Overview

根据 `房屋安全智能监测系统搭建与开发.docx` 文档中的指令集规范，当前 Python 项目中缺失多个指令。本计划将实现除 SS:10 外的所有缺失指令，包括：

- **SET 指令**: PO, KNS, CMQ, ISG, KFQR, GROLEVEL, ACCLEVEL, VKS, TME, MAGOF (10个)
- **SS 指令**: 5, 6, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27 (18个)
- **CA 指令**: 1, 2, 9, 10 (4个)

**总计**: 32个新指令

---

## Prerequisites

- Python 3.8+
- 项目环境已配置（`.venv` 已激活）
- 现有串口通信框架正常运行
- 固件版本支持所有新指令

---

## Architecture Overview

### 文件结构变更

```
sensor_calibrator/
├── network/
│   ├── __init__.py
│   ├── alarm.py           # 已存在 - SET:AGT
│   ├── cloud_mqtt.py      # 新增 - SET:KNS, SET:CMQ
│   └── position_config.py # 新增 - SET:PO
├── sensors/
│   ├── __init__.py        # 新增
│   ├── filter.py          # 新增 - SET:KFQR, SS:17
│   ├── install_mode.py    # 新增 - SET:ISG
│   ├── level_config.py    # 新增 - SET:GROLEVEL, SET:ACCLEVEL
│   └── auxiliary.py       # 新增 - SET:VKS, SET:TME, SET:MAGOF
├── system/
│   ├── __init__.py        # 新增
│   ├── cpu_monitor.py     # 新增 - SS:5
│   ├── sensor_cal.py      # 新增 - SS:6
│   ├── config_manager.py  # 新增 - SS:11, SS:12
│   ├── buzzer.py          # 新增 - SS:14
│   ├── upgrade.py         # 新增 - SS:15
│   ├── ap_mode.py         # 新增 - SS:16
│   └── mqtt_mode.py       # 新增 - SS:18
├── camera/
│   ├── __init__.py        # 新增
│   ├── camera_control.py  # 新增 - SS:19-26, CA:1-10
│   └── stream.py          # 新增 - SS:24, CA:1
└── serial/
    └── protocol.py        # 修改 - 添加所有 SS 命令常量
```

---

## Sprint 1: 高优先级网络/配置指令

**Goal**: 实现核心的网络和位置配置指令，包括阿里云MQTT、行政区划配置等
**Estimated Duration**: 1-2 weeks
**Demo/Validation**:
- 能够通过 UI 配置阿里云 MQTT (SET:KNS)
- 能够设置行政区划和建筑属性 (SET:PO)
- 能够切换 MQTT 模式 (SET:CMQ)
- 能够配置安装模式 (SET:ISG)
- 能够执行恢复默认配置 (SS:11) 和保存传感器配置 (SS:12)
- 能够执行传感器反激活 (SS:27)

### Task 1.1: 扩展协议定义
- **Location**: `sensor_calibrator/serial/protocol.py`
- **Description**: 添加所有缺失的 SS 命令常量
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] 添加 SS:5 - SS:27 的常量定义
  - [ ] 添加对应的 build 函数
  - [ ] 更新 COMMAND_DESCRIPTIONS 字典
- **Validation**:
  ```python
  # 测试所有新常量存在
  from sensor_calibrator.serial.protocol import SS_CPU_MONITOR, SS_RESTORE_DEFAULT, SS_DEACTIVATE
  assert SS_CPU_MONITOR == 5
  assert SS_RESTORE_DEFAULT == 11
  assert SS_DEACTIVATE == 27
  ```

### Task 1.2: 创建云 MQTT 模块
- **Location**: `sensor_calibrator/network/cloud_mqtt.py` (新建)
- **Description**: 实现阿里云 MQTT 配置 (SET:KNS, SET:CMQ)
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [ ] 实现 `build_kns_command(product_key, device_name, device_secret)`
  - [ ] 实现 `build_cmq_command(mode)` (10=阿里云, 1=局域网)
  - [ ] 实现参数验证函数
  - [ ] 添加完整的类型注解和文档字符串
- **Validation**:
  ```python
  from sensor_calibrator.network.cloud_mqtt import build_kns_command, build_cmq_command
  cmd = build_kns_command("ha9yyoY8xfJ", "ESP23_BHM_000003", "cfde2faeaf725ce185f16781ae58f6fc")
  assert cmd == "SET:KNS,ha9yyoY8xfJ,ESP23_BHM_000003,cfde2faeaf725ce185f16781ae58f6fc"
  ```

### Task 1.3: 创建设备位置配置模块
- **Location**: `sensor_calibrator/network/position_config.py` (新建)
- **Description**: 实现行政区划和建筑属性配置 (SET:PO)
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [ ] 实现 `build_po_command(region, building_type, user_attr, device_name)`
  - [ ] 实现行政区划路径验证 (格式: /省/市/县/街道)
  - [ ] 实现建筑属性验证 (住宅/商业/工业等)
  - [ ] 支持中文编码处理
- **Validation**:
  ```python
  from sensor_calibrator.network.position_config import build_po_command
  cmd = build_po_command("/Shandong/RiZhao/Juxian/Guanbao", "Zhuzhai", "Gonglisuo-201202", "HLSYZG-01010001")
  assert "SET:PO," in cmd
  ```

### Task 1.4: 创建安装模式配置模块
- **Location**: `sensor_calibrator/sensors/install_mode.py` (新建)
- **Description**: 实现安装模式配置 (SET:ISG)
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [ ] 实现 `build_isg_command(mode)`
  - [ ] 定义安装模式常量 (0=默认, 1-12=地/侧/顶等)
  - [ ] 添加模式说明文档
- **Validation**:
  ```python
  from sensor_calibrator.sensors.install_mode import build_isg_command, INSTALL_MODE_DEFAULT
  cmd = build_isg_command(INSTALL_MODE_DEFAULT)
  assert cmd == "SET:ISG,0"
  ```

### Task 1.5: 创建系统配置管理模块
- **Location**: `sensor_calibrator/system/config_manager.py` (新建)
- **Description**: 实现配置管理指令 (SS:11, SS:12)
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [ ] 实现 SS:11 (恢复默认配置) 的发送函数
  - [ ] 实现 SS:12 (保存传感器配置) 的发送函数
  - [ ] 添加确认对话框防止误操作
  - [ ] 实现 SS:27 (传感器反激活)
- **Validation**:
  ```python
  from sensor_calibrator.system.config_manager import build_ss11_restore_default, build_ss27_deactivate
  assert build_ss11_restore_default() == "SS:11"
  assert build_ss27_deactivate() == "SS:27"
  ```

### Task 1.6: 在 NetworkManager 中集成新指令
- **Location**: `sensor_calibrator/network_manager.py`
- **Description**: 将新的网络相关指令集成到 NetworkManager
- **Dependencies**: Task 1.2, Task 1.3, Task 1.4
- **Acceptance Criteria**:
  - [ ] 添加阿里云 MQTT 配置方法
  - [ ] 添加位置配置方法
  - [ ] 添加 MQTT 模式切换方法
  - [ ] 添加安装模式配置方法
  - [ ] 所有方法都通过 callbacks 记录日志
- **Validation**:
  - 单元测试覆盖所有新方法
  - 集成测试验证命令格式正确

### Task 1.7: 创建高优先级指令的 UI 控件
- **Location**: `sensor_calibrator/ui_manager.py`, `sensor_calibrator/app/callbacks.py`
- **Description**: 为 Sprint 1 的所有指令添加 UI 控件
- **Dependencies**: Task 1.1 - Task 1.6
- **Acceptance Criteria**:
  - [ ] 在 Network Notebook 中添加 "云配置" 标签页
    - 阿里云三元组输入 (ProductKey, DeviceName, DeviceSecret)
    - MQTT 模式选择 (下拉框: 阿里云/局域网)
  - [ ] 在 Network Notebook 中添加 "位置配置" 标签页
    - 行政区划路径输入
    - 建筑属性选择
    - 用户属性输入
    - 监测仪名称输入
  - [ ] 在 Calibration 区域添加安装模式选择
  - [ ] 在 Commands 区域添加：
    - "恢复默认配置" 按钮 (带确认对话框)
    - "保存传感器配置" 按钮
    - "反激活传感器" 按钮 (带确认对话框)
  - [ ] 所有输入框都有适当的验证和默认值
- **Validation**:
  - UI 测试验证所有控件存在且可交互
  - 端到端测试验证命令正确发送

### Task 1.8: 添加 Sprint 1 的单元测试
- **Location**: `tests/test_sprint1_commands.py` (新建)
- **Description**: 为所有 Sprint 1 指令添加单元测试
- **Dependencies**: Task 1.1 - Task 1.7
- **Acceptance Criteria**:
  - [ ] 测试所有命令构建函数
  - [ ] 测试参数验证函数
  - [ ] 测试 NetworkManager 集成
  - [ ] 测试覆盖率 > 80%
- **Validation**:
  ```bash
  python -m pytest tests/test_sprint1_commands.py -v --cov=sensor_calibrator
  ```

---

## Sprint 2: 传感器扩展指令

**Goal**: 实现传感器的高级配置，包括滤波、多级报警、辅助传感器等
**Estimated Duration**: 2-3 weeks
**Demo/Validation**:
- 能够配置卡尔曼滤波系数 (SET:KFQR)
- 能够配置角度和加速度的5级报警阈值
- 能够配置电压、温度、磁力传感器
- 能够使用 CPU 监控模式和传感器校准模式

### Task 2.1: 创建滤波配置模块
- **Location**: `sensor_calibrator/sensors/filter.py` (新建)
- **Description**: 实现卡尔曼滤波配置 (SET:KFQR) 和滤波开关 (SS:17)
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - [ ] 实现 `build_kfqr_command(process_noise, measurement_noise)`
  - [ ] 实现 `build_ss17_filter_toggle(enable)`
  - [ ] 添加滤波参数验证
- **Validation**:
  ```python
  from sensor_calibrator.sensors.filter import build_kfqr_command
  cmd = build_kfqr_command(0.005, 15)
  assert cmd == "SET:KFQR,0.005,15"
  ```

### Task 2.2: 创建多级报警配置模块
- **Location**: `sensor_calibrator/sensors/level_config.py` (新建)
- **Description**: 实现角度和加速度的5级报警配置
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - [ ] 实现 `build_grolevel_command(level1, level2, level3, level4, level5)`
  - [ ] 实现 `build_acclevel_command(level1, level2, level3, level4, level5)`
  - [ ] 添加阈值递增验证 (level1 < level2 < ... < level5)
  - [ ] 添加合理的阈值范围验证
- **Validation**:
  ```python
  from sensor_calibrator.sensors.level_config import build_grolevel_command
  cmd = build_grolevel_command(0.40107, 0.573, 1.146, 2.292, 4.584)
  assert "SET:GROLEVEL," in cmd
  ```

### Task 2.3: 创建辅助传感器配置模块
- **Location**: `sensor_calibrator/sensors/auxiliary.py` (新建)
- **Description**: 实现电压、温度、磁力传感器配置
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - [ ] 实现 `build_vks_command(voltage1_scale, voltage2_scale)`
  - [ ] 实现 `build_tme_command(temp_offset)`
  - [ ] 实现 `build_magof_command(x_offset, y_offset, z_offset)`
  - [ ] 添加所有参数的合理范围验证
- **Validation**:
  ```python
  from sensor_calibrator.sensors.auxiliary import build_vks_command, build_tme_command
  assert build_vks_command(1.0, 1.0) == "SET:VKS,1.0,1.0"
  assert build_tme_command(-15.0) == "SET:TME,-15.0"
  ```

### Task 2.4: 创建系统监控模块
- **Location**: `sensor_calibrator/system/cpu_monitor.py` (新建)
- **Description**: 实现 CPU 监控模式 (SS:5)
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - [ ] 实现 `build_ss5_cpu_monitor()` 命令
  - [ ] 实现 CPU 数据解析函数
  - [ ] 添加 CPU 使用率显示逻辑
- **Validation**:
  ```python
  from sensor_calibrator.system.cpu_monitor import build_ss5_cpu_monitor
  assert build_ss5_cpu_monitor() == "SS:5"
  ```

### Task 2.5: 创建传感器校准控制模块
- **Location**: `sensor_calibrator/system/sensor_cal.py` (新建)
- **Description**: 实现传感器校准指令 (SS:6)
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - [ ] 实现 `build_ss6_sensor_cal()` 命令
  - [ ] 与现有的 CalibrationWorkflow 集成
  - [ ] 添加校准状态显示
- **Validation**:
  ```python
  from sensor_calibrator.system.sensor_cal import build_ss6_sensor_cal
  assert build_ss6_sensor_cal() == "SS:6"
  ```

### Task 2.6: 创建系统控制模块
- **Location**: `sensor_calibrator/system/buzzer.py`, `sensor_calibrator/system/upgrade.py`, `sensor_calibrator/system/ap_mode.py`, `sensor_calibrator/system/mqtt_mode.py` (新建)
- **Description**: 实现喇叭、升级、AP模式、MQTT切换等功能
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - [ ] SS:14 - 喇叭长响控制
  - [ ] SS:15 - 监查升级命令
  - [ ] SS:16 - 进入AP配置模式
  - [ ] SS:18 - 切换MQTT模式
- **Validation**:
  ```python
  from sensor_calibrator.system.buzzer import build_ss14_buzzer
  from sensor_calibrator.system.ap_mode import build_ss16_ap_mode
  assert build_ss14_buzzer() == "SS:14"
  assert build_ss16_ap_mode() == "SS:16"
  ```

### Task 2.7: 创建传感器扩展指令的 UI 控件
- **Location**: `sensor_calibrator/ui_manager.py`, `sensor_calibrator/app/callbacks.py`
- **Description**: 为 Sprint 2 的所有指令添加 UI 控件
- **Dependencies**: Task 2.1 - Task 2.6
- **Acceptance Criteria**:
  - [ ] 新增 "高级配置" Notebook 标签页
    - 卡尔曼滤波系数输入 (两个数值输入框)
    - 滤波开关 (复选框)
  - [ ] 新增 "报警等级配置" 标签页
    - 角度报警5级阈值输入
    - 加速度报警5级阈值输入
    - 阈值递增验证提示
  - [ ] 新增 "辅助传感器" 标签页
    - 电压传感器比例 (2个输入框)
    - 温度传感器偏移 (1个输入框)
    - 磁力传感器零偏 (X/Y/Z 3个输入框)
  - [ ] 在 Commands 区域添加：
    - "CPU监控模式" 按钮 (带状态显示)
    - "传感器校准" 按钮
    - "喇叭测试" 按钮
    - "检查升级" 按钮
    - "进入AP模式" 按钮
    - "切换MQTT模式" 按钮
- **Validation**:
  - UI 测试验证所有控件存在
  - 端到端测试验证命令格式

### Task 2.8: 添加 Sprint 2 的单元测试
- **Location**: `tests/test_sprint2_commands.py` (新建)
- **Description**: 为所有 Sprint 2 指令添加单元测试
- **Dependencies**: Task 2.1 - Task 2.7
- **Acceptance Criteria**:
  - [ ] 测试所有命令构建函数
  - [ ] 测试参数验证函数 (特别是多级阈值的递增验证)
  - [ ] 测试辅助传感器的范围验证
  - [ ] 测试覆盖率 > 80%
- **Validation**:
  ```bash
  python -m pytest tests/test_sprint2_commands.py -v --cov=sensor_calibrator
  ```

---

## Sprint 3: 相机相关指令

**Goal**: 实现摄像机的完整控制功能，包括推流、拍照、OTA升级等
**Estimated Duration**: 2 weeks
**Demo/Validation**:
- 能够控制相机推流和串流
- 能够控制拍照
- 能够重启摄像机下位机和模组
- 能够执行摄像机的OTA升级

### Task 3.1: 创建相机控制模块
- **Location**: `sensor_calibrator/camera/camera_control.py` (新建)
- **Description**: 实现所有相机相关指令
- **Dependencies**: Sprint 2 完成
- **Acceptance Criteria**:
  - [ ] SS:19 - 拍照模式开关
  - [ ] SS:21 - 监测模式开关
  - [ ] SS:22 - 时程传输模式开关
  - [ ] SS:23 - 重启摄像机下位机
  - [ ] SS:25 - 控制拍照
  - [ ] SS:26 - 强制摄像机OTA升级
  - [ ] SS:27 - 已在 Sprint 1 实现
  - [ ] CA:2 - 控制拍照 (CA指令)
  - [ ] CA:9 - 重启摄像机模组
  - [ ] CA:10 - ESP32 S3强制OTA升级
- **Validation**:
  ```python
  from sensor_calibrator.camera.camera_control import build_ss23_reboot_camera_slave, build_ca9_reboot_camera
  assert build_ss23_reboot_camera_slave() == "SS:23"
  assert build_ca9_reboot_camera() == "CA:9"
  ```

### Task 3.2: 创建视频流模块
- **Location**: `sensor_calibrator/camera/stream.py` (新建)
- **Description**: 实现视频流相关指令
- **Dependencies**: Sprint 2 完成
- **Acceptance Criteria**:
  - [ ] SS:24 - 开启摄像机串流
  - [ ] CA:1 - 开启相机推流
  - [ ] 添加流状态管理
  - [ ] 添加流控制按钮状态联动
- **Validation**:
  ```python
  from sensor_calibrator.camera.stream import build_ss24_start_stream, build_ca1_start_push
  assert build_ss24_start_stream() == "SS:24"
  assert build_ca1_start_push() == "CA:1"
  ```

### Task 3.3: 创建相机控制的 UI 控件
- **Location**: `sensor_calibrator/ui_manager.py`, `sensor_calibrator/app/callbacks.py`
- **Description**: 为所有相机指令添加 UI 控件
- **Dependencies**: Task 3.1, Task 3.2
- **Acceptance Criteria**:
  - [ ] 新增 "相机控制" Notebook 标签页
    - 拍照模式开关 (复选框)
    - 监测模式开关 (复选框)
    - 时程传输模式开关 (复选框)
  - [ ] 相机控制按钮组：
    - "开启串流" / "关闭串流" 切换按钮
    - "开启推流" / "停止推流" 切换按钮
    - "拍照" 按钮
    - "重启下位机" 按钮 (带确认)
    - "重启模组" 按钮 (带确认)
    - "摄像机OTA升级" 按钮 (带确认和进度显示)
- **Validation**:
  - UI 测试验证所有控件存在
  - 流状态切换测试

### Task 3.4: 添加 Sprint 3 的单元测试
- **Location**: `tests/test_sprint3_commands.py` (新建)
- **Description**: 为所有 Sprint 3 指令添加单元测试
- **Dependencies**: Task 3.1 - Task 3.3
- **Acceptance Criteria**:
  - [ ] 测试所有 SS 和 CA 命令构建函数
  - [ ] 测试流状态管理
  - [ ] 测试覆盖率 > 80%
- **Validation**:
  ```bash
  python -m pytest tests/test_sprint3_commands.py -v --cov=sensor_calibrator
  ```

---

## Sprint 4: 集成测试与优化

**Goal**: 确保所有指令正常工作，优化UI和性能
**Estimated Duration**: 1 week

### Task 4.1: 创建综合测试套件
- **Location**: `tests/test_all_new_commands.py` (新建)
- **Description**: 创建涵盖所有新指令的综合测试
- **Dependencies**: Sprint 1-3 完成
- **Acceptance Criteria**:
  - [ ] 集成测试所有 SET 指令
  - [ ] 集成测试所有 SS 指令 (除 SS:10)
  - [ ] 集成测试所有 CA 指令
  - [ ] 测试命令序列的正确执行
  - [ ] 模拟固件响应测试
- **Validation**:
  ```bash
  python -m pytest tests/test_all_new_commands.py -v
  ```

### Task 4.2: UI 优化和一致性检查
- **Location**: `sensor_calibrator/ui_manager.py`
- **Description**: 优化 UI 布局，确保一致性
- **Dependencies**: Sprint 1-3 完成
- **Acceptance Criteria**:
  - [ ] 所有 Notebook 标签页布局一致
  - [ ] 输入框有合适的宽度
  - [ ] 按钮有统一的样式
  - [ ] 所有控件有适当的间距
  - [ ] 滚动区域正确处理溢出
- **Validation**:
  - UI 截图对比检查
  - 不同分辨率测试

### Task 4.3: 错误处理和日志优化
- **Location**: 所有新模块
- **Description**: 添加完善的错误处理和日志
- **Dependencies**: Sprint 1-3 完成
- **Acceptance Criteria**:
  - [ ] 所有命令发送前进行参数验证
  - [ ] 验证失败时有清晰的错误信息
  - [ ] 命令发送后有确认日志
  - [ ] 响应解析失败时有错误日志
  - [ ] 所有危险操作 (恢复默认、OTA升级等) 有确认对话框
- **Validation**:
  - 错误注入测试
  - 边界条件测试

### Task 4.4: 更新文档
- **Location**: `AGENTS.md`, `README.md`, 新增 `docs/commands.md`
- **Description**: 更新项目文档
- **Dependencies**: Sprint 1-3 完成
- **Acceptance Criteria**:
  - [ ] 更新 AGENTS.md 中的指令列表
  - [ ] 更新 README.md 的功能描述
  - [ ] 创建完整的指令参考文档
  - [ ] 添加 UI 截图说明
- **Validation**:
  - 文档审查
  - 链接检查

### Task 4.5: 端到端测试
- **Location**: `tests/e2e/test_new_commands.py` (新建)
- **Description**: 端到端测试验证完整工作流
- **Dependencies**: Task 4.1 - Task 4.4
- **Acceptance Criteria**:
  - [ ] 完整配置流程测试 (WiFi + MQTT + 位置 + 校准)
  - [ ] 传感器校准流程测试
  - [ ] 相机控制流程测试
  - [ ] 错误恢复测试
- **Validation**:
  ```bash
  python -m pytest tests/e2e/test_new_commands.py -v
  ```

---

## Testing Strategy

### 单元测试
- 每个命令构建函数都有对应的单元测试
- 参数验证函数的边界条件测试
- 覆盖率目标: > 80%

### 集成测试
- 命令序列的正确执行顺序
- 与 SerialManager 的集成
- 与 UIManager 的集成

### UI 测试
- 所有控件可交互
- 状态正确更新
- 确认对话框正确显示

### 端到端测试
- 完整工作流测试
- 错误恢复测试
- 不同固件响应模拟

---

## Potential Risks & Gotchas

### 风险 1: 固件兼容性
- **风险**: 不同固件版本可能支持的指令不同
- **缓解**: 
  - 实现固件版本检测
  - 在 UI 中禁用不支持的指令
  - 添加固件版本说明文档

### 风险 2: 命令冲突
- **风险**: 某些命令不能同时执行 (如 SS:0 和 SS:1)
- **缓解**:
  - 实现命令状态管理
  - 在发送冲突命令前自动停止当前流
  - 添加命令队列机制

### 风险 3: UI 复杂度增加
- **风险**: 新增32个指令会大幅增加 UI 复杂度
- **缓解**:
  - 使用 Notebook 组织相关功能
  - 添加功能分组标签
  - 提供搜索/过滤功能

### 风险 4: 中文编码问题
- **风险**: SET:PO 指令包含中文行政区划，可能出现编码问题
- **缓解**:
  - 使用 UTF-8 编码发送所有命令
  - 添加编码测试用例
  - 文档中说明编码要求

### 风险 5: SS:20 与 SS:8 的重复
- **风险**: 文档中 SS:20 和 SS:8 都描述为"获取传感器属性"
- **缓解**:
  - 与固件团队确认两者的区别
  - 如果功能相同，只在协议层添加 SS:20 常量
  - 如果不同，分别实现并文档说明

---

## Rollback Plan

如果某个 Sprint 出现问题需要回滚：

1. **代码回滚**: 使用 git 回滚到上一个 Sprint 的 tag
2. **配置回滚**: 提供恢复默认配置的快捷方式 (SS:11)
3. **UI 降级**: 保留基本功能 UI，隐藏高级功能
4. **数据备份**: 实施前备份现有配置

---

## Timeline Summary

| Sprint | Duration | Key Deliverables |
|--------|----------|------------------|
| Sprint 1 | 1-2 weeks | 网络/配置指令 + UI |
| Sprint 2 | 2-3 weeks | 传感器扩展指令 + UI |
| Sprint 3 | 2 weeks | 相机指令 + UI |
| Sprint 4 | 1 week | 集成测试 + 文档 |
| **Total** | **6-8 weeks** | 32个新指令完整实现 |

---

## Next Steps

1. 审查并批准本计划
2. 创建 Sprint 1 的详细任务分配
3. 设置开发分支
4. 开始 Task 1.1: 扩展协议定义
