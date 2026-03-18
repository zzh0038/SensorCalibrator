"""
Test UI Integration

UI集成测试：验证所有新功能都已正确集成到UI中
"""

import unittest


class TestUIWidgetsExist(unittest.TestCase):
    """测试UI控件存在"""
    
    def test_sprint1_widgets(self):
        """测试Sprint 1控件定义"""
        from sensor_calibrator.ui_manager import UIManager
        import inspect
        
        source = inspect.getsource(UIManager._setup_cloud_tab)
        self.assertIn("set_aliyun_mqtt_btn", source)
        self.assertIn("mqtt_local_mode_btn", source)
        
        source = inspect.getsource(UIManager._setup_position_tab)
        self.assertIn("set_position_btn", source)
        self.assertIn("set_install_mode_btn", source)
        
        source = inspect.getsource(UIManager._setup_system_tab)
        self.assertIn("save_sensor_config_btn", source)
        self.assertIn("restore_default_btn", source)
        self.assertIn("deactivate_sensor_btn", source)
    
    def test_sprint2_widgets(self):
        """测试Sprint 2控件定义"""
        from sensor_calibrator.ui_manager import UIManager
        import inspect
        
        # Advanced tab
        source = inspect.getsource(UIManager._setup_advanced_tab)
        self.assertIn("set_kalman_filter_btn", source)
        self.assertIn("filter_on_btn", source)
        self.assertIn("filter_off_btn", source)
        
        # Alarm Levels tab
        source = inspect.getsource(UIManager._setup_alarm_levels_tab)
        self.assertIn("set_gyro_levels_btn", source)
        self.assertIn("set_accel_levels_btn", source)
        
        # Auxiliary tab
        source = inspect.getsource(UIManager._setup_auxiliary_tab)
        self.assertIn("set_vks_btn", source)
        self.assertIn("set_tme_btn", source)
        self.assertIn("set_magof_btn", source)
        
        # Debug tab
        source = inspect.getsource(UIManager._setup_debug_tab)
        self.assertIn("cpu_monitor_btn", source)
        self.assertIn("sensor_cal_btn", source)
        self.assertIn("buzzer_btn", source)
        self.assertIn("check_upgrade_btn", source)
        self.assertIn("ap_mode_btn", source)
    
    def test_sprint3_widgets(self):
        """测试Sprint 3控件定义"""
        from sensor_calibrator.ui_manager import UIManager
        import inspect
        
        source = inspect.getsource(UIManager._setup_camera_tab)
        self.assertIn("camera_photo_on_btn", source)
        self.assertIn("camera_photo_off_btn", source)
        self.assertIn("monitoring_on_btn", source)
        self.assertIn("monitoring_off_btn", source)
        self.assertIn("timelapse_on_btn", source)
        self.assertIn("timelapse_off_btn", source)
        self.assertIn("take_photo_btn", source)
        self.assertIn("reboot_camera_slave_btn", source)
        self.assertIn("reboot_camera_module_btn", source)
        self.assertIn("toggle_camera_stream_btn", source)
        self.assertIn("toggle_push_stream_btn", source)
        self.assertIn("force_camera_ota_btn", source)
        self.assertIn("force_esp32_ota_btn", source)


class TestCallbacksExist(unittest.TestCase):
    """测试回调函数存在"""
    
    def test_sprint1_callbacks(self):
        """测试Sprint 1回调存在于CallbackRegistry"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks, SystemCallbacks
        
        callbacks = [
            'set_aliyun_mqtt_config',
            'set_mqtt_local_mode',
            'set_mqtt_aliyun_mode',
            'set_position_config',
            'set_install_mode',
            'save_sensor_config',
            'restore_default_config',
            'deactivate_sensor',
        ]
        
        # 检查回调在 CALLBACK_NAMES 中
        all_names = NetworkCallbacks.CALLBACK_NAMES + SystemCallbacks.CALLBACK_NAMES
        
        for cb in callbacks:
            self.assertIn(cb, all_names, f"Missing callback: {cb}")
    
    def test_sprint2_callbacks(self):
        """测试Sprint 2回调存在于CallbackRegistry"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = [
            # Advanced
            'set_kalman_filter', 'set_filter_on', 'set_filter_off',
            # Alarm Levels
            'set_gyro_levels', 'set_accel_levels',
            # Auxiliary
            'set_voltage_scales', 'set_temp_offset', 'set_mag_offsets',
            # Debug
            'start_cpu_monitor', 'start_sensor_calibration',
            'trigger_buzzer', 'check_upgrade', 'enter_ap_mode',
        ]
        
        for cb in callbacks:
            self.assertIn(cb, SystemCallbacks.CALLBACK_NAMES, f"Missing callback: {cb}")
    
    def test_sprint3_callbacks(self):
        """测试Sprint 3回调存在于CallbackRegistry"""
        from sensor_calibrator.app.callback_groups import CameraCallbacks
        
        callbacks = [
            'set_camera_photo_mode_on', 'set_camera_photo_mode_off',
            'set_monitoring_mode_on', 'set_monitoring_mode_off',
            'set_timelapse_mode_on', 'set_timelapse_mode_off',
            'take_photo', 'reboot_camera_slave', 'reboot_camera_module',
            'toggle_camera_stream', 'toggle_push_stream',
            'force_camera_ota', 'force_esp32_ota',
        ]
        
        for cb in callbacks:
            self.assertIn(cb, CameraCallbacks.CALLBACK_NAMES, f"Missing callback: {cb}")


class TestApplicationCallbacks(unittest.TestCase):
    """测试Application回调注册"""
    
    def test_callback_registration_dict(self):
        """测试回调注册字典包含所有新回调"""
        from sensor_calibrator.app.callback_groups import CallbackRegistry
        
        # 检查 CallbackRegistry 包含所有 Sprint 2 和 Sprint 3 回调
        # 获取所有注册的回调名
        callback_names = set()
        for group_class in CallbackRegistry.GROUPS:
            callback_names.update(group_class.CALLBACK_NAMES)
        
        # 检查Sprint 2回调
        self.assertIn('set_kalman_filter', callback_names)
        self.assertIn('set_gyro_levels', callback_names)
        self.assertIn('set_voltage_scales', callback_names)
        self.assertIn('start_cpu_monitor', callback_names)
        
        # 检查Sprint 3回调
        self.assertIn('set_camera_photo_mode_on', callback_names)
        self.assertIn('take_photo', callback_names)
        self.assertIn('toggle_camera_stream', callback_names)


class TestEnableConfigButtons(unittest.TestCase):
    """测试按钮启用方法"""
    
    def test_enable_buttons_includes_new_widgets(self):
        """测试enable_config_buttons方法包含所有新控件"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        import inspect
        
        source = inspect.getsource(SensorCalibratorApp.enable_config_buttons)
        
        # Sprint 2 按钮
        self.assertIn("set_kalman_filter_btn", source)
        self.assertIn("set_gyro_levels_btn", source)
        self.assertIn("set_vks_btn", source)
        self.assertIn("cpu_monitor_btn", source)
        
        # Sprint 3 按钮
        self.assertIn("camera_photo_on_btn", source)
        self.assertIn("take_photo_btn", source)
        self.assertIn("toggle_camera_stream_btn", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
