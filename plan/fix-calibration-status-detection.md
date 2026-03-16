# 修复 Calibration Status 检测问题

## 问题描述
传感器已校准（从 SS:13 返回的数据可以看出），但 UI 显示 "Not Calibrated"。

## 数据分析
用户提供的 SS:13 响应数据：
```json
{
  "sys": {
    "RACKS": [0.992714, 0.995445, 0.97266],     // 偏差: 0.027 > 0.01 ✓
    "RACOF": [0.36177, 0.02194, -1.362915],      // 偏差: 1.36 > 0.01 ✓
    "GROOF": [0, 0, 0],
    "VROOF": [-0.065315, 0.014625, -0.018325],   // 偏差: 0.065 > 0.01 ✓
    "REACKS": [0.983033, 0.985334, 0.985993],    // 偏差: 0.017 > 0.01 ✓
    "REACOF": [0.04911, -0.062975, -0.30286],    // 偏差: 0.303 > 0.01 ✓
    ...
  }
}
```

所有关键参数都明显偏离默认值，应该显示 "Calibrated"。

## 可能原因
1. `sensor_properties` 数据结构不一致（有时是 `sys`，有时是 `params`）
2. 校准状态检测在 `sensor_properties` 更新前执行
3. `is_sensor_calibrated()` 方法中的类型检查失败
4. UI 更新时 `calibration_status_var` 为 None

## 修复方案

### Task 1: 添加调试日志
在 `is_sensor_calibrated()` 和 `check_and_display_calibration_status()` 中添加详细日志，帮助定位问题。

### Task 2: 修复数据访问逻辑
确保从 `_display_device_info()` 中正确传递校准参数。

### Task 3: 改进校准状态检测
- 支持从 `device_info` 直接检测（不依赖 `self.sensor_properties`）
- 添加类型转换，处理可能的字符串/数字混合格式

### Task 4: 确保调用时机正确
确保 `check_and_display_calibration_status()` 在数据完全解析后调用。

### Task 5: 添加强制检测按钮
在 Calibration block 添加 "Check Calib Status" 按钮，允许用户手动触发检测。

## 实施步骤
