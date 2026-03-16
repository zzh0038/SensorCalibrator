# Plan: 修复 SS:13 校准参数读取

**方案**: C - 校准参数在 SS:13 响应中
**问题**: 当前只读取到 GID/GED 等网络字段，没有读取到 RACKS/RACOF 等校准参数

---

## 诊断步骤

### 步骤 1: 添加完整响应调试日志
**目的**: 查看 SS:13 实际返回的完整 JSON 结构
**文件**: `sensor_calibrator/app/application.py`
**位置**: `_read_device_info_thread` 方法

**修改**:
```python
# 在解析 JSON 成功后，添加调试日志
self.root.after(0, lambda d=device_info: self.log_message(f"Full SS:13 response: {json.dumps(d, indent=2)}"))
```

**验证**: 运行应用，查看日志中的完整响应

---

## 可能的场景 & 修复方案

### 场景 A: 字段名不同
**例如**: 固件使用 `racks` (小写) 或 `RAC` (缩写) 而不是 `RACKS`

**修复**:
```python
# 添加字段名映射
field_mappings = {
    # 可能的小写变体
    "racks": "RACKS",
    "racof": "RACOF",
    "reacks": "REACKS",
    "reacof": "REACOF",
    "vroof": "VROOF",
    # 其他可能的命名
    "mpu_scale": "RACKS",
    "mpu_offset": "RACOF",
    "adxl_scale": "REACKS",
    "adxl_offset": "REACOF",
    "gyro_offset": "VROOF",
}

# 在 sys_info 中查找时，同时检查原始字段名和映射
for key, label in calibration_fields.items():
    value = None
    if key in sys_info:
        value = sys_info[key]
    elif key.lower() in sys_info:
        value = sys_info[key.lower()]
    # ... 其他变体
```

---

### 场景 B: 嵌套结构
**例如**: 校准参数在子对象中
```json
{
  "sys": {
    "GID": 57,
    "GED": 1
  },
  "calibration": {
    "RACKS": [0.98, 0.99, 0.97],
    "RACOF": [0.5, -0.1, -1.2]
  }
}
```

**修复**:
```python
# 合并多个可能的字段来源
all_data = {}

# 从 sys 或 params 获取
if "sys" in device_info:
    all_data.update(device_info["sys"])
if "params" in device_info:
    all_data.update(device_info["params"])

# 从 calibration 字段获取
if "calibration" in device_info:
    all_data.update(device_info["calibration"])
    self.log_message(f"Found 'calibration' field with {len(device_info['calibration'])} fields")

# 从其他可能的字段获取
for field in ["cal", "params", "config", "settings"]:
    if field in device_info and isinstance(device_info[field], dict):
        all_data.update(device_info[field])
        self.log_message(f"Found '{field}' field with {len(device_info[field])} fields")

sys_info = all_data
```

---

### 场景 C: 固件版本问题
**可能**: 当前固件版本没有在 SS:13 中包含校准参数

**检查**:
- 查看固件版本字段（可能在 `VER`, `version`, `fw_version` 等字段中）
- 确认固件文档，哪个版本开始支持 SS:13 返回校准参数

---

## 实施步骤

### Sprint 1: 添加调试信息
**文件**: `sensor_calibrator/app/application.py`
**行号**: ~1393（JSON 解析成功后）

```python
# 添加完整响应日志
import json
self.root.after(0, lambda d=device_info: self.log_message(f"SS:13 Full Response:\n{json.dumps(d, indent=2)}"))
```

**验证**: 
- [ ] 运行应用，发送 SS:13
- [ ] 查看日志中的完整 JSON 结构
- [ ] 确认校准参数是否存在，字段名是什么

---

### Sprint 2: 根据实际字段名修复
**根据 Sprint 1 的结果选择修复方案：**

#### 如果字段名不同（场景 A）:
**文件**: `sensor_calibrator/app/application.py`
**行号**: ~1464（查找字段的循环）

修改查找逻辑，支持多种字段名变体。

#### 如果嵌套结构（场景 B）:
**文件**: `sensor_calibrator/app/application.py`
**行号**: ~1432-1442（提取 sys_info 的逻辑）

修改数据提取逻辑，合并多个来源。

#### 如果固件不支持（场景 C）:
需要固件更新，或者改用其他命令读取校准参数。

---

### Sprint 3: 验证修复
**验证清单**:
- [ ] 发送 SS:13 后能读取到 RACKS 值
- [ ] 发送 SS:13 后能读取到 RACOF 值
- [ ] 发送 SS:13 后能读取到 REACKS 值
- [ ] 发送 SS:13 后能读取到 REACOF 值
- [ ] 发送 SS:13 后能读取到 VROOF 值
- [ ] 弹窗正确显示所有校准参数
- [ ] 日志正确显示所有校准参数

---

## 临时调试代码

你可以先添加这段代码来诊断问题：

```python
def _display_device_info(self, device_info):
    """显示校准参数"""
    import json
    
    # 打印完整响应到日志
    self.log_message("=" * 60)
    self.log_message("SS:13 RAW RESPONSE:")
    self.log_message(json.dumps(device_info, indent=2))
    self.log_message("=" * 60)
    
    # 打印所有字段名
    def extract_keys(obj, prefix=""):
        keys = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{prefix}.{k}" if prefix else k
                keys.append(full_key)
                if isinstance(v, dict):
                    keys.extend(extract_keys(v, full_key))
        return keys
    
    all_keys = extract_keys(device_info)
    self.log_message(f"All available fields: {all_keys}")
    
    # 原有逻辑...
```

这段代码会帮助你看到 SS:13 返回的完整结构和所有可用字段。

---

## 下一步

请运行添加了调试日志的代码，然后把日志中的完整 SS:13 响应发给我，我会根据实际的字段名和结构给你具体的修复代码。
