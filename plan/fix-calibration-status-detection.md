# 修复 Calibration Status 检测问题

## 问题描述 ✅ 已修复
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

## 根本原因
1. `check_and_display_calibration_status()` 在 `_read_device_info_thread` 的 finally 块中调用
2. 此时 `sensor_properties` 可能还没有被更新（`_display_device_info` 之后执行）
3. 检测时使用的是旧的或未设置的数据

## 修复方案 ✅ 已实施

### Task 1: 添加调试日志 ✅
在 `is_sensor_calibrated()` 中添加详细日志，显示：
- 检测时使用的数据来源
- 每个参数的偏差值
- 判断结果

### Task 2: 修复数据访问逻辑 ✅
- 修改 `is_sensor_calibrated()` 支持直接传入 `device_info` 参数
- 修改 `check_and_display_calibration_status()` 支持直接传入 `device_info`
- 在 `_display_device_info()` 中直接传入 `sys_info` 进行检测

### Task 3: 改进校准状态检测 ✅
- 添加 `float()` 类型转换，处理可能的字符串/数字混合格式
- 确保从 `device_info` 直接检测时正确构建数据结构

### Task 4: 确保调用时机正确 ✅
- 将校准状态检测从 `_read_device_info_thread` 的 finally 块移到 `_display_device_info()` 中
- 确保在数据完全解析并显示后再检测

### Task 5: 添加强制检测按钮 ✅
在 Calibration block 添加 "Check" 按钮，允许用户手动触发检测

## 修改文件
- `sensor_calibrator/app/application.py` - 核心检测逻辑
- `sensor_calibrator/app/callbacks.py` - 添加手动检测回调
- `sensor_calibrator/ui_manager.py` - 添加 Check 按钮
- `tests/test_calibration_status.py` - 更新测试

## 测试 ✅ 全部通过
```
tests/test_calibration_status.py::TestCalibrationStatus::test_is_sensor_calibrated_no_properties PASSED
tests/test_calibration_status.py::TestCalibrationStatus::test_is_sensor_calibrated_empty_sys PASSED
tests/test_calibration_status.py::TestCalibrationStatus::test_is_sensor_calibrated_default_scale PASSED
tests/test_calibration_status.py::TestCalibrationStatus::test_is_sensor_calibrated_scaled PASSED
tests/test_calibration_status.py::TestCalibrationStatus::test_is_sensor_calibrated_offset PASSED
tests/test_calibration_status.py::TestCalibrationStatus::test_is_sensor_calibrated_adxl_calibrated PASSED
tests/test_calibration_status.py::TestCalibrationStatus::test_is_sensor_calibrated_gyro_calibrated PASSED
tests/test_calibration_status.py::TestCalibrationStatus::test_is_sensor_calibrated_with_device_info PASSED
tests/test_calibration_status.py::TestCalibrationQuality::test_get_calibration_quality_no_properties PASSED
tests/test_calibration_status.py::TestCalibrationQuality::test_get_calibration_quality_uncalibrated PASSED
tests/test_calibration_status.py::TestCalibrationQuality::test_get_calibration_quality_calibrated PASSED
tests/test_calibration_status.py::TestCalibrationQuality::test_get_calibration_quality_deviation_values PASSED
tests/test_calibration_status.py::TestCalibrationStatusDisplay::test_update_calibration_status_display_calibrated PASSED
tests/test_calibration_status.py::TestCalibrationStatusDisplay::test_update_calibration_status_display_uncalibrated PASSED
tests/test_calibration_status.py::TestCalibrationStatusDisplay::test_update_calibration_status_display_auto_detect PASSED
```

## 使用说明
1. 点击 "Read Calibration Params" 后，校准状态会自动检测并显示
2. 如果状态显示不正确，可以点击 "Check" 按钮手动触发检测
3. 查看日志中的 "DEBUG" 信息可以了解检测详情

## 提交
```
commit f5c3e34
fix: 修复校准状态检测问题
```
