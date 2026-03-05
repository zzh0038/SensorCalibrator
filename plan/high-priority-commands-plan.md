# 高优先级指令功能实施计划（已更新）

**Generated**: 2026-03-03  
**Updated**: 2026-03-03  
**Estimated Complexity**: Medium  
**Estimated Duration**: 2-3 天  

---

## 概述

本计划针对**4个**高优先级指令功能进行实施（SS:6 传感器校准已存在，本次跳过）：

1. **SET:AGT** - 报警阈值设置（加速度/倾角阈值）
2. **SS:7** - 保存配置到传感器 + 保存校准参数到文件（用户选择位置）
3. **SS:9** - 重启传感器
4. **SET:AKY** - 激活密钥（已存在，需修改为发送完整64字符密钥）

### 技术方案
- 使用 **Notebook 标签页** 重构 Network Config 区域
- 扩展 `SerialManager` 添加 SS:7, SS:9 方法
- 扩展 `NetworkManager` 添加 SET:AGT 支持
- 修改 `CalibrationWorkflow` 支持文件选择保存
- 修改 `ActivationWorkflow` 使用完整64字符密钥

---

## Sprint 1: 核心指令功能实现

**Goal**: 在 SerialManager 和 NetworkManager 中实现所有缺失的指令方法
**Demo/Validation**: 可以通过代码调用发送所有新指令

### Task 1.1: 扩展 SerialManager - 添加 SS 指令
- **Location**: `sensor_calibrator/serial_manager.py`
- **Description**: 添加 SS:7（保存配置）和 SS:9（重启传感器）的支持
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 添加 `send_ss7_save_config()` 方法
  - 添加 `send_ss9_restart_sensor()` 方法
  - 每个方法都有完整的 docstring 和日志记录
- **Validation**:
  - 代码审查确认方法签名正确
  - 单元测试验证命令格式（如 `SS:7\n`）

**实现细节**:
```python
def send_ss7_save_config(self, description: str = "Save Configuration") -> bool:
    """发送 SS:7 指令 - 保存配置到传感器"""
    return self.send_ss_command(7, description)

def send_ss9_restart_sensor(self, description: str = "Restart Sensor") -> bool:
    """发送 SS:9 指令 - 重启传感器"""
    return self.send_ss_command(9, description)
```

### Task 1.2: 扩展 NetworkManager - 添加 SET:AGT 支持
- **Location**: `sensor_calibrator/network_manager.py`
- **Description**: 添加报警阈值设置功能
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - 添加 `set_alarm_threshold(accel_threshold: float, gyro_threshold: float)` 方法
  - 构建正确的命令格式：`SET:AGT,{accel},{gyro}`
  - 添加参数验证（阈值范围检查）
  - 支持从传感器属性读取当前阈值
- **Validation**:
  - 单元测试验证命令格式
  - 验证参数边界检查

**实现细节**:
```python
def set_alarm_threshold(self, accel_threshold: float, gyro_threshold: float) -> bool:
    """
    设置报警阈值
    
    Args:
        accel_threshold: 加速度报警阈值 (m/s²)，范围 0.1-10.0
        gyro_threshold: 倾角报警阈值 (°)，范围 0.1-45.0
    """
    # 验证范围
    if not (0.1 <= accel_threshold <= 10.0):
        raise ValueError("加速度阈值必须在 0.1-10.0 m/s² 范围内")
    if not (0.1 <= gyro_threshold <= 45.0):
        raise ValueError("倾角阈值必须在 0.1-45.0° 范围内")
    
    cmd = f"SET:AGT,{accel_threshold},{gyro_threshold}"
    # 发送命令...
```

### Task 1.3: SS:7 保存配置命令（仅发送命令）
- **Location**: `sensor_calibrator/serial_manager.py`（已在 Task 1.1 中添加）
- **Description**: SS:7 命令仅发送给传感器，由传感器内部处理配置保存
- **注意**: 此功能已在 Task 1.1 中通过 `send_ss7_save_config()` 实现，无需额外修改
- **命令行为**: 
  - 发送 `SS:7\n` 到传感器
  - 传感器接收后自行保存配置到内部存储
  - PC端不需要处理响应（或仅做简单日志记录）

---

### Task 1.4: 修改 CalibrationWorkflow - 校准参数文件保存（用户选择位置）
- **Location**: `sensor_calibrator/calibration_workflow.py`
- **Description**: 修改 Calibration 区域的 "Save Params" 按钮功能，让用户选择文件保存位置
- **Dependencies**: 无
- **重要说明**: 
  - 此功能与 SS:7 完全独立！
  - SS:7 是发送命令给传感器保存配置
  - 此功能是将校准参数保存到 PC 本地文件
- **Acceptance Criteria**:
  - 添加 `save_calibration_to_file()` 方法
  - 使用 `filedialog.asksaveasfilename` 让用户选择保存位置
  - 默认文件名格式：`calibration_params_YYYYMMDD_HHMMSS.json`
  - 保存内容包括：校准参数、时间戳、传感器信息
- **Validation**:
  - 点击 "Save Params" 按钮弹出文件选择对话框
  - 选择的文件路径正确保存数据

**实现细节**:
```python
import json
from tkinter import filedialog
from datetime import datetime

def save_calibration_to_file(self, parent_widget=None) -> bool:
    """
    保存校准参数到用户选择的文件
    （注意：这与 SS:7 命令完全不同，SS:7 是发送给传感器，这是保存到本地文件）
    
    Args:
        parent_widget: 父窗口（用于对话框定位）
        
    Returns:
        bool: 是否成功保存
    """
    if not self._calibration_params:
        self._log_message("Error: No calibration parameters to save!")
        return False
    
    # 构建默认文件名
    default_name = f"calibration_params_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 弹出保存对话框
    filename = filedialog.asksaveasfilename(
        parent=parent_widget,
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        initialfile=default_name,
        title="Save Calibration Parameters"
    )
    
    if not filename:
        self._log_message("Save cancelled by user")
        return False
    
    # 保存数据到本地文件
    try:
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "calibration_params": self._calibration_params,
            # 可选：添加传感器属性信息
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        self._log_message(f"Calibration parameters saved to: {filename}")
        return True
        
    except Exception as e:
        self._log_message(f"Error saving calibration parameters: {str(e)}")
        return False
```

### Task 1.5: 更新 Config 常量定义
- **Location**: `sensor_calibrator/config.py`
- **Description**: 添加新的 SS 命令 ID 和报警阈值默认值
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 添加 `CMD_SAVE_CONFIG = 7`
  - 添加 `CMD_RESTART_SENSOR = 9`
  - 添加报警阈值默认值常量
- **Validation**:
  - 所有常量值正确无误
  - 代码可以通过导入测试

---

## Sprint 2: UI 界面设计与实现

**Goal**: 创建 Notebook 标签页，整合所有网络配置和设备控制功能
**Demo/Validation**: 运行应用可以看到新的控制面板并能交互

### Task 2.1: 重构 Network Config 为 Notebook 标签页
- **Location**: `sensor_calibrator/ui_manager.py`
- **Description**: 将 WiFi/MQTT/OTA 重构为 Notebook，新增 "Alarm & Device" 标签页
- **Dependencies**: Sprint 1 完成
- **Acceptance Criteria**:
  - 创建 `_setup_network_notebook()` 方法替换原有的独立区域
  - Notebook 包含 4 个标签页：
    - **WiFi** - 原有 WiFi Settings 内容
    - **MQTT** - 原有 MQTT Settings 内容  
    - **OTA** - 原有 OTA Settings 内容
    - **Alarm & Device** - 新增功能：
      - 报警阈值设置（加速度/倾角输入框 + Set 按钮）
      - 设备控制按钮（Restart Sensor）
      - 当前阈值显示
  - 移除原有的 `_setup_wifi_section()`、`_setup_mqtt_section()`、`_setup_ota_section()` 独立调用
  - 保持所有控件回调绑定
- **Validation**:
  - 运行应用可以看到 Notebook 组件
  - 4 个标签页可以正常切换
  - 原有功能在新布局中正常工作

**UI 布局设计**:
```
┌─ Network & Device Configuration ──────────────┐
│  [WiFi] [MQTT] [OTA] [Alarm & Device]        │
│ ═══════════════════════════════════════════  │
│                                               │
│ Tab: Alarm & Device                           │
│ ┌─ Alarm Threshold ───────────────────────┐  │
│ │  Accel (m/s²): [________]               │  │
│ │  Gyro  (°):    [________]               │  │
│ │           [Set Alarm Threshold]         │  │
│ └─────────────────────────────────────────┘  │
│ ┌─ Device Control ────────────────────────┐  │
│ │  [Save Config]  [Restart Sensor]        │  │
│ │   (SS:7)         (SS:9)                 │  │
│ └─────────────────────────────────────────┘  │
│ ┌─ Current Status ────────────────────────┐  │
│ │  Accel Threshold: -- m/s²               │  │
│ │  Gyro Threshold:  -- °                  │  │
│ └─────────────────────────────────────────┘  │
└───────────────────────────────────────────────┘

按钮命名规范:
- 按钮文本使用描述性功能名称（英文）
- 避免使用指令代码（如SS:7, SS:9）作为按钮文本
- 可以在按钮下方/旁边用小字体标注对应指令（可选）
```

### Task 2.2: 修改 Calibration 区域的 Save 按钮（文件保存）
- **Location**: `sensor_calibrator/ui_manager.py`, `sensor_calibrator/calibration_workflow.py`
- **Description**: 修改 "Save Params" 按钮行为，使用文件选择对话框保存校准参数到本地文件
- **Dependencies**: Task 1.4
- **重要说明**: 此按钮保存校准参数到 **PC本地文件**，与 SS:7（传感器配置保存）完全独立！
- **按钮命名**: 保持现有的 "Save Params"（已符合描述性命名规范）
- **Acceptance Criteria**:
  - "Save Params" 按钮调用新的 `save_calibration_to_file()` 方法
  - 弹出文件选择对话框让用户选择保存位置
  - 保存成功后在日志中显示完整路径
- **Validation**:
  - 点击 "Save Params" 弹出文件选择对话框
  - 选择位置后文件正确保存

### Task 2.3: 添加回调函数到主应用
- **Location**: `sensor_calibrator/__init__.py` (主应用文件)
- **Description**: 实现 UI 回调函数，连接 UI 和底层管理器
- **Dependencies**: Task 2.1
- **注意**: 
  - SS:7 不需要额外的 UI 回调，因为它只是简单的命令发送（已在 SerialManager 中实现）
  - 按钮名称与回调对应关系:
    - "Restart Sensor" 按钮 → `on_restart_sensor()` 回调
    - "Save Config" 按钮 → `on_save_config()` 回调
    - "Set Alarm Threshold" 按钮 → `on_set_alarm_threshold()` 回调
- **Acceptance Criteria**:
  - 添加 `on_restart_sensor()` 回调（对应 "Restart Sensor" 按钮）
  - 添加 `on_set_alarm_threshold()` 回调（对应 "Set Alarm Threshold" 按钮）
  - 所有回调正确调用对应的 Manager 方法
- **Validation**:
  - 点击按钮可以在日志中看到正确的命令发送
- **Location**: `sensor_calibrator/__init__.py` (主应用文件)
- **Description**: 实现 UI 回调函数，连接 UI 和底层管理器
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - 添加 `on_set_alarm_threshold()` 回调
  - 添加 `on_restart_sensor()` 回调
  - 所有回调正确调用对应的 Manager 方法
- **Validation**:
  - 点击按钮可以在日志中看到正确的命令发送

### Task 2.4: 集成阈值显示到 Alarm & Device 标签页
- **Location**: `sensor_calibrator/ui_manager.py`, `sensor_calibrator/network_manager.py`
- **Description**: 从传感器属性中提取并在 Notebook 标签页中显示当前报警阈值
- **Dependencies**: Task 2.3
- **Acceptance Criteria**:
  - 添加 `extract_alarm_threshold()` 方法到 NetworkManager
  - 在 "Alarm & Device" 标签页的 Current Status 区域显示当前阈值
  - 读取属性后自动更新 Notebook 中的显示
- **Validation**:
  - 读取传感器属性后，Notebook 中的阈值显示更新

---

## Sprint 3: 激活流程集成与完善

**Goal**: 确保 SET:AKY 发送完整64字符密钥
**Demo/Validation**: 激活流程发送完整的64字符密钥

### Task 3.1: 修改 ActivationWorkflow 发送完整64字符密钥
- **Location**: `sensor_calibrator/activation_workflow.py`
- **Description**: 修改 `_activate_sensor_thread()` 中的 SET:AKY 命令
- **Dependencies**: 无
- **Acceptance Criteria**:
  - 将 `SET:AKY,{key_fragment}` 修改为 `SET:AKY,{full_key}`
  - 发送完整的64字符 SHA-256 密钥
  - 更新日志输出显示完整密钥
- **Validation**:
  - 代码审查确认发送完整密钥
  - 日志显示完整64字符密钥

**修改前**:
```python
activation_cmd = f"SET:AKY,{self._generated_key[5:12]}"  # 7字符片段
```

**修改后**:
```python
activation_cmd = f"SET:AKY,{self._generated_key}"  # 完整64字符密钥
```

### Task 3.2: 在 UI 添加激活信息显示增强
- **Location**: `sensor_calibrator/ui_manager.py`
- **Description**: 在 Activation 区域显示更多信息
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - 在 Activation 区域下方添加信息显示框：
    - 传感器 MAC 地址
    - 生成的64字符密钥（带滚动条或折叠）
    - 激活状态（已激活/未激活，带颜色标识）
  - 添加复制密钥按钮
- **Validation**:
  - UI 正确显示所有信息
  - 密钥显示格式符合64字符要求

---

## Sprint 4: 测试与验证

**Goal**: 确保所有功能正常工作并编写测试
**Demo/Validation**: 所有测试通过，功能演示正常

### Task 4.1: 编写单元测试
- **Location**: `tests/test_commands.py` (新建或更新)
- **Description**: 为新指令编写单元测试
- **Dependencies**: Sprint 1-3 完成
- **Acceptance Criteria**:
  - 测试 `send_ss7_save_config()` 命令格式
  - 测试 `send_ss9_restart_sensor()` 命令格式
  - 测试 `set_alarm_threshold()` 参数验证
  - 测试 `set_alarm_threshold()` 命令格式
  - 测试 `save_calibration_to_file()` 文件保存
- **Validation**:
  - 运行 `pytest tests/test_commands.py` 全部通过

### Task 4.2: 集成测试
- **Location**: `tests/test_integration.py` (新建或更新)
- **Description**: 测试从 UI 到指令发送的完整流程
- **Dependencies**: Task 4.1
- **Acceptance Criteria**:
  - 测试 UI 按钮点击触发正确命令
  - 测试阈值设置流程
  - 测试文件保存流程
- **Validation**:
  - 集成测试全部通过

### Task 4.3: 端到端功能测试
- **Location**: 实际硬件环境
- **Description**: 在实际传感器上测试所有功能
- **Dependencies**: Task 4.2
- **Acceptance Criteria**:
  - SET:AGT 命令被传感器正确接收
  - SS:7 命令成功保存配置
  - SS:9 命令成功重启传感器
  - 激活流程成功发送完整64字符 SET:AKY
- **Validation**:
  - 在真实传感器上验证所有功能

---

## 文件修改清单

| 文件路径 | 修改类型 | Sprint | 说明 |
|---------|---------|--------|------|
| `sensor_calibrator/serial_manager.py` | 修改 | 1 | 添加 SS:7, SS:9 方法 |
| `sensor_calibrator/network_manager.py` | 修改 | 1, 2 | 添加 SET:AGT 方法和阈值提取 |
| `sensor_calibrator/calibration_workflow.py` | 修改 | 1 | **添加文件选择保存功能（与SS:7无关）** |
| `sensor_calibrator/config.py` | 修改 | 1 | 添加新常量定义 |
| `sensor_calibrator/ui_manager.py` | **重构** | 2 | **重大修改：使用 Notebook 重构 Network Config 区域** |
| `sensor_calibrator/activation_workflow.py` | 修改 | 3 | 修改为发送完整64字符密钥 |
| `sensor_calibrator/__init__.py` | 修改 | 2 | 添加新回调函数 |
| `tests/test_commands.py` | 新建/修改 | 4 | 单元测试 |
| `tests/test_integration.py` | 新建/修改 | 4 | 集成测试 |

### UI 重构详细说明

**修改前**（独立区域）：
```python
self._setup_wifi_section()
self._setup_mqtt_section()
self._setup_ota_section()
```

**修改后**（Notebook 标签页）：
```python
self._setup_network_notebook()  # 包含4个标签页
# - WiFi 标签页
# - MQTT 标签页
# - OTA 标签页
# - Alarm & Device 标签页（新增）
```

**涉及移除/合并的方法**：
- 移除独立的 `_setup_wifi_section()`、`_setup_mqtt_section()`、`_setup_ota_section()` 调用
- 新增 `_setup_network_notebook()` 方法
- 原有 WiFi/MQTT/OTA 内容作为内部方法被 Notebook 调用

---

## 测试策略

### 单元测试覆盖
- SS 命令格式验证
- SET:AGT 参数边界检查
- 回调函数调用验证
- 配置常量验证
- 文件保存功能测试

### 集成测试
- UI 到 Manager 的调用链
- 属性解析和显示更新
- 错误处理和日志记录

### 手动测试清单
1. 连接传感器，验证串口通信正常
2. 设置报警阈值，验证命令发送正确
3. 点击 "Save Params"，验证弹出文件选择对话框
4. 选择位置保存，验证文件内容正确
5. 点击 "Restart Sensor"，验证 SS:9 发送
6. 执行激活流程，验证 SET:AKY 发送完整64字符密钥
7. 读取属性，验证阈值显示正确

---

## 潜在风险与注意事项

### 风险 1: 阈值范围不明确
- **问题**: 文档未明确 SET:AGT 的参数范围
- **缓解**: 参考传感器规格书，暂定加速度 0.1-10.0 m/s²，倾角 0.1-45.0°
- **验证**: 在实际传感器上测试有效范围

### 风险 2: 命令响应格式未知
- **问题**: 不清楚传感器对 SS:7, SS:9 的响应格式
- **缓解**: 实现通用的响应处理，支持 "success"/"ok"/无响应 多种情况
- **验证**: 实际测试确认响应格式

### 风险 3: SET:AKY 64字符密钥兼容性
- **问题**: 现有代码发送7字符片段，修改为64字符后需要确认传感器支持
- **缓解**: 保持原有响应处理逻辑，仅修改发送的密钥长度
- **验证**: 在实际传感器上测试完整密钥激活

### 风险 4: UI 重构复杂度
- **问题**: 使用 Notebook 重构现有 UI 可能影响原有功能
- **缓解**: 
  - 保留原有 WiFi/MQTT/OTA 的设置逻辑
  - 仅改变布局方式，不改变控件变量名和回调
  - 分步测试：先确保原有功能正常，再添加新标签页
- **备选**: 如果 Notebook 实现有问题，回退到独立区域布局

### 风险 5: 文件选择对话框在不同系统的兼容性
- **问题**: `filedialog.asksaveasfilename` 在不同操作系统上行为可能不同
- **缓解**: 使用标准 tkinter filedialog，已在多平台测试
- **验证**: 在目标平台（Windows）上测试文件选择功能

---

## 回滚计划

如果出现问题需要回滚：

1. **代码回滚**: 使用 git 回退到实施前的版本
2. **配置恢复**: 备份的 sensor_properties.json 和 calibration_params.json
3. **紧急修复**: 如果某个指令有问题，可以单独禁用该功能
4. **UI 回滚**: 如果 Notebook 布局有问题，可以回退到原有的独立区域布局

### UI 重构回滚策略
- 保留原有 `_setup_wifi_section()` 等方法作为备份
- 新增 `_setup_network_notebook()` 方法
- 在 `__init__` 中可以通过开关选择使用哪种布局
```python
# 在 __init__ 中
if USE_NOTEBOOK_LAYOUT:
    self._setup_network_notebook()
else:
    # 原有布局（备份）
    self._setup_wifi_section()
    self._setup_mqtt_section()
    self._setup_ota_section()
```

---

## 下一步行动

1. **✅ 已确认**: SET:AKY 使用64字符完整密钥
2. **✅ 已确认**: 阈值范围按暂定值（加速度 0.1-10.0 m/s²，倾角 0.1-45.0°）
3. **✅ 已确认**: UI 使用 Notebook 标签页方案
4. **✅ 已确认**: SS:6 跳过（已存在）
5. **✅ 已确认**: 保存功能支持用户选择位置
6. **开始 Sprint 1**: 实现核心指令功能
7. **定期同步**: 每完成一个 Sprint 进行一次演示和反馈

### 立即开始的任务

**Sprint 1 - Task 1.1**: 扩展 SerialManager 添加 SS:7, SS:9 方法
- 预计耗时: 1-2 小时
- 产出: `sensor_calibrator/serial_manager.py` 新增方法

**Sprint 1 - Task 1.2**: 扩展 NetworkManager 添加 SET:AGT 支持
- 预计耗时: 2-3 小时
- 产出: `sensor_calibrator/network_manager.py` 新增方法

**Sprint 1 - Task 1.4**: 修改 CalibrationWorkflow 添加文件选择保存（与SS:7无关）
- 预计耗时: 1-2 小时
- 产出: `sensor_calibrator/calibration_workflow.py` 新增方法
- **重要**: 这是修改 "Save Params" 按钮的功能，让用户选择位置保存校准参数文件

---

## 附录：指令参考

### 文档指令集摘要

**SET:AGT** - 设置报警阈值
```
格式: SET:AGT,<加速度阈值>,<倾角阈值>
示例: SET:AGT,0.2,0.2
参数: 
  - 加速度阈值: 0.1-10.0 m/s²
  - 倾角阈值: 0.1-45.0°
```

**SS:7** - 保存配置
```
格式: SS:7
功能: 将当前配置保存到传感器非易失性存储
```

**SS:9** - 重启传感器
```
格式: SS:9
功能: 重启传感器设备
```

**SET:AKY** - 设置激活密钥（完整64字符）
```
格式: SET:AKY,<64字符密钥>
示例: SET:AKY,352450f3ecebd2d1fc6e17889a8155ff2c6fe307eecb6e1e7b56262cbfa7e3af
注意: 使用完整64字符SHA-256密钥
```
