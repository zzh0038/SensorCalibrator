"""
传感器校准状态检测测试

测试 is_sensor_calibrated 及其相关功能
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCalibrationStatus:
    """测试传感器校准状态检测功能"""
    
    def test_is_sensor_calibrated_no_properties(self):
        """测试无传感器属性时返回未校准"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 创建模拟对象
        class MockApp:
            sensor_properties = None
        
        mock_app = MockApp()
        result = SensorCalibratorApp.is_sensor_calibrated(mock_app)
        
        assert result is False
    
    def test_is_sensor_calibrated_empty_sys(self):
        """测试 sys 为空时返回未校准"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = {"sys": {}}
        
        mock_app = MockApp()
        result = SensorCalibratorApp.is_sensor_calibrated(mock_app)
        
        assert result is False
    
    def test_is_sensor_calibrated_default_scale(self):
        """测试 Scale 为默认值 [1.0, 1.0, 1.0] 时返回未校准"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = {
                "sys": {
                    "RACKS": [1.0, 1.0, 1.0],  # 默认 Scale
                    "RACOF": [0.0, 0.0, 0.0],  # 默认 Offset
                }
            }
        
        mock_app = MockApp()
        result = SensorCalibratorApp.is_sensor_calibrated(mock_app)
        
        assert result is False
    
    def test_is_sensor_calibrated_scaled(self):
        """测试 Scale 偏离默认值时返回已校准"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = {
                "sys": {
                    "RACKS": [1.02, 0.98, 1.01],  # 偏离默认
                    "RACOF": [0.0, 0.0, 0.0],
                }
            }
        
        mock_app = MockApp()
        result = SensorCalibratorApp.is_sensor_calibrated(mock_app)
        
        assert result is True
    
    def test_is_sensor_calibrated_offset(self):
        """测试 Offset 偏离默认值时返回已校准"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = {
                "sys": {
                    "RACKS": [1.0, 1.0, 1.0],
                    "RACOF": [0.05, -0.03, 0.02],  # 偏离默认
                }
            }
        
        mock_app = MockApp()
        result = SensorCalibratorApp.is_sensor_calibrated(mock_app)
        
        assert result is True
    
    def test_is_sensor_calibrated_adxl_calibrated(self):
        """测试 ADXL355 校准参数有效时返回已校准"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = {
                "sys": {
                    "REACKS": [0.99, 1.01, 0.98],  # 偏离默认
                    "REACOF": [0.0, 0.0, 0.0],
                }
            }
        
        mock_app = MockApp()
        result = SensorCalibratorApp.is_sensor_calibrated(mock_app)
        
        assert result is True
    
    def test_is_sensor_calibrated_gyro_calibrated(self):
        """测试陀螺仪校准参数有效时返回已校准"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = {
                "sys": {
                    "RACKS": [1.0, 1.0, 1.0],
                    "RACOF": [0.0, 0.0, 0.0],
                    "VROOF": [0.05, -0.02, 0.03],  # 偏离默认
                }
            }
        
        mock_app = MockApp()
        result = SensorCalibratorApp.is_sensor_calibrated(mock_app)
        
        assert result is True


class TestCalibrationQuality:
    """测试校准质量评估功能"""
    
    def test_get_calibration_quality_no_properties(self):
        """测试无传感器属性时返回 unknown"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = None
        
        mock_app = MockApp()
        quality = SensorCalibratorApp.get_calibration_quality(mock_app)
        
        assert quality["status"] == "unknown"
        # 无属性时返回的 dict 中没有 is_calibrated 键，状态为 unknown 即可
    
    def test_get_calibration_quality_uncalibrated(self):
        """测试未校准状态的详细信息"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = {
                "sys": {
                    "RACKS": [1.0, 1.0, 1.0],
                    "RACOF": [0.0, 0.0, 0.0],
                    "REACKS": [1.0, 1.0, 1.0],
                    "REACOF": [0.0, 0.0, 0.0],
                }
            }
        
        mock_app = MockApp()
        quality = SensorCalibratorApp.get_calibration_quality(mock_app)
        
        assert quality["status"] == "uncalibrated"
        assert quality["is_calibrated"] is False
        assert "Calibration recommended" in quality["message"]
    
    def test_get_calibration_quality_calibrated(self):
        """测试已校准状态的详细信息"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = {
                "sys": {
                    "RACKS": [1.02, 0.99, 1.01],
                    "RACOF": [0.05, -0.03, 0.02],
                    "REACKS": [1.0, 1.0, 1.0],
                    "REACOF": [0.0, 0.0, 0.0],
                }
            }
        
        mock_app = MockApp()
        quality = SensorCalibratorApp.get_calibration_quality(mock_app)
        
        assert quality["status"] == "calibrated"
        assert quality["is_calibrated"] is True
        assert "has been calibrated" in quality["message"]
        
        # 验证详细信息
        details = quality["details"]
        assert details["mpu_accel_scale_calibrated"] is True
        assert details["mpu_accel_offset_calibrated"] is True
        assert details["adxl_accel_scale_calibrated"] is False
        assert details["adxl_accel_offset_calibrated"] is False
    
    def test_get_calibration_quality_deviation_values(self):
        """测试偏差值计算"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        class MockApp:
            sensor_properties = {
                "sys": {
                    "RACKS": [1.05, 0.95, 1.0],  # max deviation = 0.05
                    "RACOF": [0.1, -0.08, 0.05],  # max offset = 0.1
                }
            }
        
        mock_app = MockApp()
        quality = SensorCalibratorApp.get_calibration_quality(mock_app)
        
        details = quality["details"]
        assert abs(details["mpu_accel_scale_deviation"] - 0.05) < 0.001
        assert abs(details["mpu_accel_offset_max"] - 0.1) < 0.001


class TestCalibrationStatusDisplay:
    """测试校准状态显示功能"""
    
    def test_update_calibration_status_display_calibrated(self, mocker):
        """测试已校准状态的UI更新"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        mock_app = mocker.MagicMock()
        mock_app.calibration_status_var = mocker.MagicMock()
        mock_app.calibration_status_label = mocker.MagicMock()
        
        # 调用方法 - 传入 True 表示已校准
        SensorCalibratorApp.update_calibration_status_display(mock_app, is_calibrated=True)
        
        # 验证UI更新
        mock_app.calibration_status_var.set.assert_called_once_with("Calibrated")
        mock_app.calibration_status_label.config.assert_called_once_with(foreground="green")
    
    def test_update_calibration_status_display_uncalibrated(self, mocker):
        """测试未校准状态的UI更新"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        mock_app = mocker.MagicMock()
        mock_app.calibration_status_var = mocker.MagicMock()
        mock_app.calibration_status_label = mocker.MagicMock()
        
        # 调用方法 - 传入 False 表示未校准
        SensorCalibratorApp.update_calibration_status_display(mock_app, is_calibrated=False)
        
        # 验证UI更新
        mock_app.calibration_status_var.set.assert_called_once_with("Not Calibrated")
        mock_app.calibration_status_label.config.assert_called_once_with(foreground="orange")
    
    def test_update_calibration_status_display_auto_detect(self, mocker):
        """测试自动检测校准状态"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 创建一个带有 sensor_properties 的 mock
        mock_app = mocker.MagicMock()
        mock_app.sensor_properties = {"sys": {"RACKS": [1.02, 1.0, 1.0]}}
        mock_app.calibration_status_var = mocker.MagicMock()
        mock_app.calibration_status_label = mocker.MagicMock()
        
        # 调用方法 - 传入 None 表示自动检测
        SensorCalibratorApp.update_calibration_status_display(mock_app, is_calibrated=None)
        
        # 验证UI更新为已校准状态（因为 sensor_properties 中有偏离的 RACKS）
        mock_app.calibration_status_var.set.assert_called_once_with("Calibrated")
        mock_app.calibration_status_label.config.assert_called_once_with(foreground="green")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
