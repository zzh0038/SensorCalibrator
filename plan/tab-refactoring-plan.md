# 标签重构方案 (Tab Refactoring Plan)

**日期**: 2026-03-17  
**主题**: 浅色现代主题  
**目标**: 将11个拥挤标签页重构为5个清晰的分类标签

---

## 当前问题分析

### 现有11个标签页
```
[WiFi] [MQTT] [Cloud] [Position] [OTA] [System] [Advanced] [Alarm] [Aux] [Camera] [Debug]
 ↑1     ↑2     ↑3      ↑4        ↑5     ↑6       ↑7         ↑8      ↑9    ↑10     ↑11
```

**问题**:
- 标签过多，难以快速定位
- 相关功能分散在不同标签
- 重要功能（如校准）没有独立标签
- 缺乏整体状态概览

---

## 重构方案：5个主标签页

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [ Dashboard ]  [ Network ]  [ Sensors ]  [ System ]  [ Calibration ]        │
│      ↑1            ↑2          ↑3           ↑4           ↑5                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 标签页详细设计

### Tab 1: Dashboard (仪表盘) ⭐ 新增

**定位**: 应用入口，整体状态概览，快速操作

**布局**:
```
┌──────────────────────────────────────────────────────────────────────┐
│  Dashboard                                                           │
├──────────────────────────────────────────────────────────────────────┤
│  ┌─ System Status ────────────┐  ┌─ Quick Actions ──────────────────┐│
│  │  ● Connection: Connected   │  │  [Connect Serial] [Start Stream] ││
│  │  ● Calibration: Complete   │  │  [Read Config]    [Save Config]  ││
│  │  ● Activation: Active      │  │                                  ││
│  │  ● Network: WiFi+MQTT OK   │  │  [Quick Calibrate]  [Take Photo] ││
│  │                            │  │                                  ││
│  │  Last Update: 14:32:05     │  │  [⚠️ Restore Default]            ││
│  └────────────────────────────┘  └──────────────────────────────────┘│
│                                                                      │
│  ┌─ Real-time Overview ────────────────────────────────────────────┐│
│  │                                                                  ││
│  │   [Chart: Accel X/Y/Z]      [Chart: Gyro X/Y/Z]    [Status Map] ││
│  │                                                                  ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─ Recent Activity ───────────────────────────────────────────────┐│
│  │  14:32:05  [INFO] Calibration completed                          ││
│  │  14:30:12  [INFO] Connected to COM3                              ││
│  │  14:28:45  [INFO] Configuration saved                            ││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

**功能**:
| 区域 | 功能 | 原有来源 |
|------|------|----------|
| System Status | 显示连接、校准、激活、网络状态 | 新增汇总 |
| Quick Actions | 常用操作快捷按钮 | 分散在各标签 |
| Real-time Overview | 实时数据图表预览 | Data Stream |
| Recent Activity | 最近操作日志 | Log窗口 |

---

### Tab 2: Network (网络) 🌐 合并4个标签

**定位**: 所有网络相关配置集中管理

**布局 - 二级标签设计**:
```
┌──────────────────────────────────────────────────────────────────────┐
│  Network                                                             │
├──────────────────────────────────────────────────────────────────────┤
│  [WiFi] [MQTT] [Cloud MQTT] [Position] ← 二级标签栏                  │
│                                                                       │
│  ┌─ WiFi Configuration ────────────────────────────────────────────┐│
│  │                                                                  ││
│  │  SSID:     [____________________]    [Scan Networks]            ││
│  │  Password: [____________________]    [Show Password 👁]         ││
│  │                                                                  ││
│  │  [Connect WiFi]  [Test Connection]  [Disconnect]                ││
│  │                                                                  ││
│  │  Status: ● Connected to "MyNetwork"  Signal: ████████░░ 80%     ││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

**二级标签内容**:

| 二级标签 | 包含功能 | 原标签来源 |
|----------|----------|------------|
| **WiFi** | SSID/密码输入、连接状态、信号强度、网络扫描 | WiFi |
| **MQTT** | Broker地址、端口、用户名/密码、连接测试 | MQTT |
| **Cloud MQTT** | 阿里云三元组配置、MQTT模式切换 | Cloud |
| **Position** | 行政区划、建筑类型、设备名称、安装模式 | Position |

**优化点**:
- WiFi添加网络扫描功能
- MQTT添加连接测试按钮
- Cloud显示当前MQTT模式状态
- Position集成地图选择器（可选）

---

### Tab 3: Sensors (传感器) 🔧 合并3个标签

**定位**: 传感器参数配置和校准

**布局**:
```
┌──────────────────────────────────────────────────────────────────────┐
│  Sensors                                                             │
├──────────────────────────────────────────────────────────────────────┤
│  [Filter] [Alarm Levels] [Auxiliary] [Calibration Params]           │
│                                                                       │
│  ┌─ Kalman Filter Configuration ───────────────────────────────────┐│
│  │                                                                  ││
│  │  Process Noise (Q):      [0.005    ]  ← Slider + Input         ││
│  │  Measurement Noise (R):  [15       ]  ← Slider + Input         ││
│  │                                                                  ││
│  │  [Apply Filter]  [Reset to Default]  [Filter: ON 🔵]            ││
│  │                                                                  ││
│  │  Presets: [Default ▼] [Smooth] [Responsive] [Balanced]          ││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

**二级标签内容**:

| 二级标签 | 包含功能 | 原标签来源 |
|----------|----------|------------|
| **Filter** | 卡尔曼滤波系数、开关、预设方案 | Advanced |
| **Alarm Levels** | 角度/加速度5级报警阈值、图表预览 | Alarm Levels |
| **Auxiliary** | 电压、温度、磁力传感器配置 | Auxiliary |
| **Calibration Params** | 当前校准参数显示、手动调整 | 新增 |

**优化点**:
- 使用滑块+输入框组合控件
- 添加参数图表实时预览
- 校准参数可视化显示

---

### Tab 4: System (系统) ⚙️ 合并4个标签

**定位**: 系统控制、调试、相机、OTA

**布局**:
```
┌──────────────────────────────────────────────────────────────────────┐
│  System                                                              │
├──────────────────────────────────────────────────────────────────────┤
│  [Control] [Camera] [OTA/Update] [Debug/Tools]                      │
│                                                                       │
│  ┌─ System Control ────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │  Configuration:                                                  ││
│  │    [💾 Save Config]  [🔄 Restore Default]  [📥 Load Config]     ││
│  │                                                                  ││
│  │  Device Control:                                                 ││
│  │    [🔄 Restart Sensor]  [📡 Enter AP Mode]  [⚠️ Deactivate]    ││
│  │                                                                  ││
│  │  Notifications:                                                  ││
│  │    [🔔 Test Buzzer]  [📢 Speaker Test]                         ││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

**二级标签内容**:

| 二级标签 | 包含功能 | 原标签来源 |
|----------|----------|------------|
| **Control** | 保存配置、恢复默认、重启、反激活、喇叭测试 | System |
| **Camera** | 拍照模式、监测模式、时程传输、推流控制 | Camera |
| **OTA/Update** | 固件检查、OTA升级、版本信息 | OTA + SS:15 |
| **Debug/Tools** | CPU监控、传感器校准、AP模式 | Debug |

**优化点**:
- 危险操作（恢复默认、反激活）添加红色警告样式
- 使用图标按钮增强可读性
- 添加操作确认对话框

---

### Tab 5: Calibration (校准) 📐 独立标签

**定位**: 六位置校准流程专用页面

**布局**:
```
┌──────────────────────────────────────────────────────────────────────┐
│  Calibration                                                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─ Calibration Progress ───────────────────────────────────────────┐│
│  │                                                                  ││
│  │   1. +X    2. -X    3. +Y    4. -Y    5. +Z    6. -Z           ││
│  │   [✓]     [✓]     [✓]     [✓]     [◐]     [○]                  ││
│  │   Done    Done    Done    Done    Capturing...  Pending          ││
│  │                                                                  ││
│  │   Progress: ████████████████████░░░░  67%                        ││
│  │                                                                  ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─ Current Position ───────────────────────────────────────────────┐│
│  │                                                                  ││
│  │   Position 5: +Z axis down (Z = +9.81 m/s²)                     ││
│  │                                                                  ││
│  │   [📊 Live Data]  [📷 Visual Guide]                             ││
│  │                                                                  ││
│  │   ┌─ Real-time Readings ───────────────────────────────────────┐││
│  │   │  MPU Accel:  X: 0.12  Y: 0.05  Z: 9.78                     │││
│  │   │  ADXL Accel: X: 0.08  Y: 0.03  Z: 9.82                     │││
│  │   └────────────────────────────────────────────────────────────┘││
│  │                                                                  ││
│  │   [◀ Previous]  [⏹ Stop]  [⏺ Capture Position]  [Next ▶]       ││
│  │                                                                  ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─ Calibration Results ────────────────────────────────────────────┐│
│  │  Last Calibration: 2026-03-17 14:32:05                          ││
│  │  Status: ● Calibrated                                           ││
│  │  [View Parameters]  [Export Report]  [Recalibrate]               ││
│  └───────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

**功能**:
| 区域 | 功能描述 |
|------|----------|
| Progress | 6位置进度可视化，带状态指示 |
| Current Position | 当前位置和实时数据 |
| Visual Guide | 传感器方向3D示意图（可选） |
| Results | 校准结果和历史记录 |

**优化点**:
- 6位置进度条，直观显示完成状态
- 添加3D方向引导图
- 校准结果报告导出
- 历史校准记录

---

## 浅色主题配色方案

```python
# sensor_calibrator/config.py 更新

class UITheme:
    """浅色现代主题配置"""
    
    # 主色调
    PRIMARY = "#0078d4"           # 微软蓝
    PRIMARY_HOVER = "#106ebe"     # 悬停蓝
    PRIMARY_LIGHT = "#e5f1fb"     # 浅蓝背景
    
    # 背景色
    BG_MAIN = "#f8f9fa"           # 主背景（淡灰白）
    BG_CARD = "#ffffff"           # 卡片背景（纯白）
    BG_SIDEBAR = "#f3f4f6"        # 侧边栏背景
    BG_INPUT = "#ffffff"          # 输入框背景
    
    # 文字色
    TEXT_PRIMARY = "#202124"      # 主要文字（深灰黑）
    TEXT_SECONDARY = "#5f6368"    # 次要文字（中灰）
    TEXT_DISABLED = "#9aa0a6"     # 禁用文字（浅灰）
    
    # 边框色
    BORDER = "#dadce0"            # 默认边框
    BORDER_HOVER = "#bdc1c6"      # 悬停边框
    BORDER_FOCUS = "#0078d4"      # 聚焦边框（蓝）
    
    # 状态色
    SUCCESS = "#137333"           # 成功绿
    SUCCESS_BG = "#e6f4ea"        # 成功背景
    WARNING = "#f9ab00"           # 警告黄
    WARNING_BG = "#fef3e8"        # 警告背景
    ERROR = "#d93025"             # 错误红
    ERROR_BG = "#fce8e6"          # 错误背景
    INFO = "#0078d4"              # 信息蓝
    INFO_BG = "#e8f0fe"           # 信息背景
    
    # 图表色
    CHART_X = "#ea4335"           # 红
    CHART_Y = "#34a853"           # 绿
    CHART_Z = "#4285f4"           # 蓝
    CHART_GRAVITY = "#fbbc04"     # 黄
```

### 视觉层次

```
背景层级（从低到高）:
┌─────────────────────────────────────┐  ← Level 0: BG_MAIN #f8f9fa (页面背景)
│  ┌─────────────────────────────┐   │  ← Level 1: BG_SIDEBAR #f3f4f6 (侧边栏)
│  │  ┌─────────────────────┐   │   │  ← Level 2: BG_CARD #ffffff (卡片)
│  │  │  ┌─────────────┐   │   │   │  ← Level 3: BG_INPUT (输入框)
│  │  │  │   Content   │   │   │   │
│  │  │  └─────────────┘   │   │   │
│  │  └─────────────────────┘   │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘

阴影效果:
- 卡片: 0 1px 3px rgba(0,0,0,0.12)
- 悬停: 0 4px 12px rgba(0,0,0,0.15)
- 弹窗: 0 8px 24px rgba(0,0,0,0.2)
```

---

## 组件样式规范

### 按钮样式

```python
BUTTON_STYLES = {
    'primary': {
        'bg': '#0078d4',
        'fg': '#ffffff',
        'hover_bg': '#106ebe',
        'active_bg': '#005a9e',
        'border': 0,
        'radius': 4,
        'padding': (10, 16),
    },
    'secondary': {
        'bg': '#ffffff',
        'fg': '#202124',
        'hover_bg': '#f8f9fa',
        'active_bg': '#f3f4f6',
        'border': 1,
        'border_color': '#dadce0',
        'radius': 4,
        'padding': (10, 16),
    },
    'danger': {
        'bg': '#ffffff',
        'fg': '#d93025',
        'hover_bg': '#fce8e6',
        'active_bg': '#fad2cf',
        'border': 1,
        'border_color': '#fad2cf',
        'radius': 4,
        'padding': (10, 16),
    },
    'ghost': {
        'bg': 'transparent',
        'fg': '#5f6368',
        'hover_bg': '#f3f4f6',
        'active_bg': '#e8eaed',
        'border': 0,
        'radius': 4,
        'padding': (8, 12),
    }
}
```

### 输入框样式

```python
INPUT_STYLES = {
    'bg': '#ffffff',
    'fg': '#202124',
    'border': 1,
    'border_color': '#dadce0',
    'focus_border': '#0078d4',
    'hover_border': '#bdc1c6',
    'radius': 4,
    'padding': (8, 12),
    'placeholder_color': '#9aa0a6',
}
```

### 卡片样式

```python
CARD_STYLES = {
    'bg': '#ffffff',
    'border': 0,
    'radius': 8,
    'padding': 20,
    'shadow': '0 1px 3px rgba(0,0,0,0.12)',
    'hover_shadow': '0 4px 12px rgba(0,0,0,0.15)',
}
```

---

## 实施步骤

### Step 1: 更新配置 (1小时)
- [ ] 在 `config.py` 中添加 `UITheme` 类
- [ ] 创建 `theme_manager.py` 主题管理器

### Step 2: 重构Notebook (2-3小时)
- [ ] 创建新的 `_setup_dashboard_tab()`
- [ ] 重构 `_setup_network_notebook()` → 二级标签
- [ ] 重构 `Sensors` 和 `System` 标签
- [ ] 创建 `_setup_calibration_tab()`

### Step 3: 应用样式 (2-3小时)
- [ ] 更新 `_setup_styles()` 方法
- [ ] 应用浅色主题配色
- [ ] 添加卡片样式

### Step 4: 迁移回调 (1小时)
- [ ] 更新回调函数注册
- [ ] 测试所有按钮功能

---

## 最终效果预览

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 🔷 Sensor Calibration System                                      🌙 ⚙️ 🔔  │
├──────────────────────────────────────────────────────────────────────────────┤
│  [Dashboard] [Network] [Sensors] [System] [Calibration]                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─ System Status ─────────────┐  ┌─ Quick Actions ───────────────────────┐  │
│  │                             │  │                                        │  │
│  │  ● Connection: Connected    │  │  [Connect] [Start Stream] [Calibrate]  │  │
│  │  ● Calibration: Complete    │  │                                        │  │
│  │  ● Network: WiFi + MQTT OK  │  │  [Read Config] [Save Config]           │  │
│  │                             │  │                                        │  │
│  └─────────────────────────────┘  └────────────────────────────────────────┘  │
│                                                                              │
│  浅色背景 #f8f9fa  +  白色卡片  +  蓝色强调色  +  圆角阴影效果                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 确认事项

1. **5个主标签是否满意？**
   - Dashboard / Network / Sensors / System / Calibration

2. **二级标签分类是否合理？**
   - Network: WiFi/MQTT/Cloud/Position
   - Sensors: Filter/Alarm/Auxiliary/Params
   - System: Control/Camera/OTA/Debug

3. **浅色主题配色是否满意？**
   - 背景: #f8f9fa (淡灰白)
   - 强调: #0078d4 (微软蓝)
   - 卡片: #ffffff (纯白)

请确认后，我立即开始实施！
