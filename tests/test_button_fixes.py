"""
按钮修复测试

测试所有修复的按钮回调功能，确保：
1. 回调函数存在且可调用
2. 参数从 UI 正确传递到 NetworkManager
3. 命令构建正确
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# 确保可以导入 sensor_calibrator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCameraCallbacks:
    """测试 Camera 按钮回调"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟的应用实例"""
        app = Mock()
        app.camera_manager = Mock()
        app.stream_manager = Mock()
        app.log_message = Mock()
        return app
    
    def test_set_camera_photo_mode_on(self, mock_app):
        """测试开启拍照模式回调"""
        from sensor_calibrator.app.callback_groups import CameraCallbacks
        
        callbacks = CameraCallbacks(mock_app)
        callbacks.set_camera_photo_mode_on()
        
        mock_app.camera_manager.set_photo_mode_on.assert_called_once()
    
    def test_set_camera_photo_mode_off(self, mock_app):
        """测试关闭拍照模式回调"""
        from sensor_calibrator.app.callback_groups import CameraCallbacks
        
        callbacks = CameraCallbacks(mock_app)
        callbacks.set_camera_photo_mode_off()
        
        mock_app.camera_manager.set_photo_mode_off.assert_called_once()
    
    def test_take_photo(self, mock_app):
        """测试拍照回调"""
        from sensor_calibrator.app.callback_groups import CameraCallbacks
        
        callbacks = CameraCallbacks(mock_app)
        callbacks.take_photo()
        
        mock_app.camera_manager.take_photo.assert_called_once()
    
    def test_toggle_camera_stream(self, mock_app):
        """测试切换相机流回调"""
        from sensor_calibrator.app.callback_groups import CameraCallbacks
        
        callbacks = CameraCallbacks(mock_app)
        callbacks.toggle_camera_stream()
        
        mock_app.camera_manager.toggle_camera_stream.assert_called_once()
    
    def test_toggle_push_stream(self, mock_app):
        """测试切换推流回调"""
        from sensor_calibrator.app.callback_groups import CameraCallbacks
        
        callbacks = CameraCallbacks(mock_app)
        callbacks.toggle_push_stream()
        
        mock_app.camera_manager.toggle_push_stream.assert_called_once()


class TestNetworkCallbacks:
    """测试 Network 按钮回调"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟的应用实例"""
        app = Mock()
        app.network_manager = Mock()
        app.log_message = Mock()
        
        # 模拟 UI 管理器
        app.ui_manager = Mock()
        app.ui_manager.get_entry_value = Mock(side_effect=lambda key: {
            'ssid': 'TestWiFi',
            'password': 'TestPass123',
            'mqtt_broker': '192.168.1.100',
            'mqtt_user': 'admin',
            'mqtt_password': 'mqtt_pass',
            'mqtt_port': '1883',
            'url1': 'http://ota1.example.com',
            'url2': 'http://ota2.example.com',
            'url3': '',
            'url4': '',
            'aliyun_product_key': 'a1b2c3d4',
            'aliyun_device_name': 'device_001',
            'aliyun_device_secret': 'secret123456',
            'position_region': '/Province/City/District',
            'position_building': 'Zhuzhai',
            'position_user_attr': 'User-001',
            'position_device_name': 'Device-001',
            'install_mode': '0 - Default',
        }.get(key, ''))
        
        return app
    
    def test_set_wifi_config(self, mock_app):
        """测试设置 WiFi 回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_wifi_config()
        
        mock_app.network_manager.set_wifi_config.assert_called_once_with(
            'TestWiFi', 'TestPass123'
        )
    
    def test_set_wifi_config_empty_ssid(self, mock_app):
        """测试设置 WiFi 回调 - 空 SSID 处理"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        mock_app.ui_manager.get_entry_value = Mock(return_value='')
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_wifi_config()
        
        # 应该记录错误而不调用 network_manager
        mock_app.log_message.assert_called_once()
        mock_app.network_manager.set_wifi_config.assert_not_called()
    
    def test_set_mqtt_config(self, mock_app):
        """测试设置 MQTT 回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_mqtt_config()
        
        mock_app.network_manager.set_mqtt_config.assert_called_once_with(
            '192.168.1.100', 'admin', 'mqtt_pass', '1883'
        )
    
    def test_set_ota_config(self, mock_app):
        """测试设置 OTA 回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_ota_config()
        
        mock_app.network_manager.set_ota_config.assert_called_once_with(
            'http://ota1.example.com',
            'http://ota2.example.com',
            '',
            ''
        )
    
    def test_set_aliyun_mqtt_config(self, mock_app):
        """测试设置阿里云 MQTT 回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_aliyun_mqtt_config()
        
        mock_app.network_manager.set_aliyun_mqtt_config.assert_called_once_with(
            'a1b2c3d4', 'device_001', 'secret123456'
        )
    
    def test_set_mqtt_local_mode(self, mock_app):
        """测试设置 MQTT 本地模式回调"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_mqtt_local_mode()
        
        mock_app.network_manager.set_mqtt_mode.assert_called_once_with(1)
    
    def test_set_mqtt_aliyun_mode(self, mock_app):
        """测试设置 MQTT 阿里云模式回调"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_mqtt_aliyun_mode()
        
        mock_app.network_manager.set_mqtt_mode.assert_called_once_with(10)
    
    def test_set_position_config(self, mock_app):
        """测试设置位置配置回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_position_config()
        
        mock_app.network_manager.set_position_config.assert_called_once_with(
            '/Province/City/District', 'Zhuzhai', 'User-001', 'Device-001'
        )
    
    def test_set_install_mode(self, mock_app):
        """测试设置安装模式回调 - 验证参数解析"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_install_mode()
        
        mock_app.network_manager.set_install_mode.assert_called_once_with(0)
    
    def test_set_install_mode_invalid(self, mock_app):
        """测试设置安装模式回调 - 无效值处理"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks
        
        mock_app.ui_manager.get_entry_value = Mock(return_value='invalid')
        
        callbacks = NetworkCallbacks(mock_app)
        callbacks.set_install_mode()
        
        # 应该记录错误
        mock_app.log_message.assert_called_once()
        mock_app.network_manager.set_install_mode.assert_not_called()


class TestSystemCallbacks:
    """测试 System 按钮回调"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟的应用实例"""
        app = Mock()
        app.network_manager = Mock()
        app.reset_ui_with_confirmation = Mock()
        return app
    
    def test_save_sensor_config(self, mock_app):
        """测试保存传感器配置回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.save_sensor_config()
        
        mock_app.network_manager.save_sensor_config.assert_called_once()
    
    def test_restore_default_config(self, mock_app):
        """测试恢复默认配置回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.restore_default_config()
        
        mock_app.network_manager.restore_default_config.assert_called_once()
    
    def test_deactivate_sensor(self, mock_app):
        """测试停用传感器回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.deactivate_sensor()
        
        mock_app.network_manager.deactivate_sensor.assert_called_once()
    
    def test_set_local_coordinate_mode(self, mock_app):
        """测试设置局部坐标模式回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_local_coordinate_mode()
        
        mock_app.network_manager.set_local_coordinate_mode.assert_called_once()
    
    def test_set_global_coordinate_mode(self, mock_app):
        """测试设置全局坐标模式回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_global_coordinate_mode()
        
        mock_app.network_manager.set_global_coordinate_mode.assert_called_once()
    
    def test_start_cpu_monitor(self, mock_app):
        """测试启动 CPU 监控回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.start_cpu_monitor()
        
        mock_app.network_manager.start_cpu_monitor.assert_called_once()
    
    def test_start_sensor_calibration(self, mock_app):
        """测试启动传感器校准回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.start_sensor_calibration()
        
        mock_app.network_manager.start_sensor_calibration.assert_called_once()
    
    def test_trigger_buzzer(self, mock_app):
        """测试触发蜂鸣器回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.trigger_buzzer()
        
        mock_app.network_manager.trigger_buzzer.assert_called_once()
    
    def test_check_upgrade(self, mock_app):
        """测试检查升级回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.check_upgrade()
        
        mock_app.network_manager.check_upgrade.assert_called_once()
    
    def test_enter_ap_mode(self, mock_app):
        """测试进入 AP 模式回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.enter_ap_mode()
        
        mock_app.network_manager.enter_ap_mode.assert_called_once()


class TestSensorsCallbacks:
    """测试 Sensors 按钮回调"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟的应用实例"""
        app = Mock()
        app.network_manager = Mock()
        app.log_message = Mock()
        
        # 模拟 UI 变量
        app.ui_manager = Mock()
        app.ui_manager.vars = {
            'kf_q': Mock(get=Mock(return_value='0.005')),
            'kf_r': Mock(get=Mock(return_value='15')),
            'gyro_level1': Mock(get=Mock(return_value='0.40107')),
            'gyro_level2': Mock(get=Mock(return_value='0.573')),
            'gyro_level3': Mock(get=Mock(return_value='1.146')),
            'gyro_level4': Mock(get=Mock(return_value='2.292')),
            'gyro_level5': Mock(get=Mock(return_value='4.584')),
            'accel_level1': Mock(get=Mock(return_value='0.2')),
            'accel_level2': Mock(get=Mock(return_value='0.5')),
            'accel_level3': Mock(get=Mock(return_value='1.0')),
            'accel_level4': Mock(get=Mock(return_value='2.0')),
            'accel_level5': Mock(get=Mock(return_value='4.0')),
            'vks_v1': Mock(get=Mock(return_value='1.0')),
            'vks_v2': Mock(get=Mock(return_value='1.0')),
            'tme_offset': Mock(get=Mock(return_value='0.0')),
            'magof_x': Mock(get=Mock(return_value='0.0')),
            'magof_y': Mock(get=Mock(return_value='0.0')),
            'magof_z': Mock(get=Mock(return_value='0.0')),
        }
        
        return app
    
    def test_set_kalman_filter(self, mock_app):
        """测试设置卡尔曼滤波回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_kalman_filter()
        
        mock_app.network_manager.set_kalman_filter.assert_called_once_with(
            0.005, 15.0
        )
    
    def test_set_kalman_filter_invalid(self, mock_app):
        """测试设置卡尔曼滤波回调 - 无效值处理"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        mock_app.ui_manager.vars['kf_q'] = Mock(get=Mock(return_value='invalid'))
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_kalman_filter()
        
        # 应该记录错误
        mock_app.log_message.assert_called_once()
        mock_app.network_manager.set_kalman_filter.assert_not_called()
    
    def test_set_filter_on(self, mock_app):
        """测试开启滤波回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_filter_on()
        
        mock_app.network_manager.set_filter_on.assert_called_once()
    
    def test_set_filter_off(self, mock_app):
        """测试关闭滤波回调"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_filter_off()
        
        mock_app.network_manager.set_filter_off.assert_called_once()
    
    def test_set_gyro_levels(self, mock_app):
        """测试设置陀螺仪报警等级回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_gyro_levels()
        
        mock_app.network_manager.set_gyro_levels.assert_called_once_with(
            0.40107, 0.573, 1.146, 2.292, 4.584
        )
    
    def test_set_accel_levels(self, mock_app):
        """测试设置加速度报警等级回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_accel_levels()
        
        mock_app.network_manager.set_accel_levels.assert_called_once_with(
            0.2, 0.5, 1.0, 2.0, 4.0
        )
    
    def test_set_voltage_scales(self, mock_app):
        """测试设置电压比例回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_voltage_scales()
        
        mock_app.network_manager.set_voltage_scales.assert_called_once_with(
            1.0, 1.0
        )
    
    def test_set_temp_offset(self, mock_app):
        """测试设置温度偏移回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_temp_offset()
        
        mock_app.network_manager.set_temp_offset.assert_called_once_with(0.0)
    
    def test_set_mag_offsets(self, mock_app):
        """测试设置磁力计偏移回调 - 验证参数从 UI 获取"""
        from sensor_calibrator.app.callback_groups import SystemCallbacks
        
        callbacks = SystemCallbacks(mock_app)
        callbacks.set_mag_offsets()
        
        mock_app.network_manager.set_mag_offsets.assert_called_once_with(
            0.0, 0.0, 0.0
        )


class TestNetworkManagerMethods:
    """测试 NetworkManager 新增方法"""
    
    @pytest.fixture
    def mock_serial_manager(self):
        """创建模拟的串口管理器"""
        sm = Mock()
        sm.is_connected = True
        sm.send_line = Mock(return_value=(True, None))
        return sm
    
    @pytest.fixture
    def network_manager(self, mock_serial_manager):
        """创建 NetworkManager 实例"""
        from sensor_calibrator.network_manager import NetworkManager
        
        callbacks = {'log_message': Mock()}
        nm = NetworkManager(mock_serial_manager, callbacks)
        return nm
    
    def test_send_simple_command_not_connected(self, network_manager, mock_serial_manager):
        """测试发送简单命令 - 未连接状态"""
        mock_serial_manager.is_connected = False
        
        result = network_manager._send_simple_command("SS:12", "Test")
        
        assert result is False
        mock_serial_manager.send_line.assert_not_called()
    
    def test_save_sensor_config(self, network_manager, mock_serial_manager):
        """测试保存传感器配置方法"""
        result = network_manager.save_sensor_config()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:12")
    
    def test_restore_default_config(self, network_manager, mock_serial_manager):
        """测试恢复默认配置方法"""
        result = network_manager.restore_default_config()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:11")
    
    def test_deactivate_sensor(self, network_manager, mock_serial_manager):
        """测试停用传感器方法"""
        result = network_manager.deactivate_sensor()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:27")
    
    def test_set_local_coordinate_mode(self, network_manager, mock_serial_manager):
        """测试设置局部坐标模式方法"""
        result = network_manager.set_local_coordinate_mode()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:2")
    
    def test_set_global_coordinate_mode(self, network_manager, mock_serial_manager):
        """测试设置全局坐标模式方法"""
        result = network_manager.set_global_coordinate_mode()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:3")
    
    def test_start_cpu_monitor(self, network_manager, mock_serial_manager):
        """测试启动 CPU 监控方法"""
        result = network_manager.start_cpu_monitor()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:5")
    
    def test_start_sensor_calibration(self, network_manager, mock_serial_manager):
        """测试启动传感器校准方法"""
        result = network_manager.start_sensor_calibration()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:6")
    
    def test_trigger_buzzer(self, network_manager, mock_serial_manager):
        """测试触发蜂鸣器方法"""
        result = network_manager.trigger_buzzer()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:14")
    
    def test_check_upgrade(self, network_manager, mock_serial_manager):
        """测试检查升级方法"""
        result = network_manager.check_upgrade()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:15")
    
    def test_enter_ap_mode(self, network_manager, mock_serial_manager):
        """测试进入 AP 模式方法"""
        result = network_manager.enter_ap_mode()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:16")
    
    def test_set_kalman_filter(self, network_manager, mock_serial_manager):
        """测试设置卡尔曼滤波方法"""
        result = network_manager.set_kalman_filter(0.005, 15.0)
        
        assert result is True
        # 验证发送的命令包含 SET:KFQR
        call_args = mock_serial_manager.send_line.call_args[0][0]
        assert "SET:KFQR" in call_args
        assert "0.005000" in call_args
        assert "15.00" in call_args
    
    def test_set_filter_on(self, network_manager, mock_serial_manager):
        """测试开启滤波方法"""
        result = network_manager.set_filter_on()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:17,1")
    
    def test_set_filter_off(self, network_manager, mock_serial_manager):
        """测试关闭滤波方法"""
        result = network_manager.set_filter_off()
        
        assert result is True
        mock_serial_manager.send_line.assert_called_once_with("SS:17,0")
    
    def test_set_gyro_levels(self, network_manager, mock_serial_manager):
        """测试设置角度报警等级方法"""
        result = network_manager.set_gyro_levels(
            0.40107, 0.573, 1.146, 2.292, 4.584
        )
        
        assert result is True
        # 验证发送的命令
        call_args = mock_serial_manager.send_line.call_args[0][0]
        assert "SET:GROLEVEL" in call_args
    
    def test_set_accel_levels(self, network_manager, mock_serial_manager):
        """测试设置加速度报警等级方法"""
        result = network_manager.set_accel_levels(
            0.2, 0.5, 1.0, 2.0, 4.0
        )
        
        assert result is True
        # 验证发送的命令
        call_args = mock_serial_manager.send_line.call_args[0][0]
        assert "SET:ACCLEVEL" in call_args
    
    def test_set_voltage_scales(self, network_manager, mock_serial_manager):
        """测试设置电压比例方法"""
        result = network_manager.set_voltage_scales(1.0, 1.0)
        
        assert result is True
        # 验证发送的命令
        call_args = mock_serial_manager.send_line.call_args[0][0]
        assert "SET:VKS" in call_args
    
    def test_set_temp_offset(self, network_manager, mock_serial_manager):
        """测试设置温度偏移方法"""
        result = network_manager.set_temp_offset(-15.0)
        
        assert result is True
        # 验证发送的命令
        call_args = mock_serial_manager.send_line.call_args[0][0]
        assert "SET:TME" in call_args
        assert "-15.00" in call_args
    
    def test_set_mag_offsets(self, network_manager, mock_serial_manager):
        """测试设置磁力计偏移方法"""
        result = network_manager.set_mag_offsets(1.0, 2.0, 3.0)
        
        assert result is True
        # 验证发送的命令
        call_args = mock_serial_manager.send_line.call_args[0][0]
        assert "SET:MAGOF" in call_args


class TestApplicationInit:
    """测试 Application 初始化"""
    
    def test_camera_manager_initialized(self):
        """测试 CameraManager 在初始化时被正确创建"""
        # 这里我们只做导入测试，因为完整初始化需要 GUI
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        app = SensorCalibratorApp()
        
        # 验证初始值为 None（在 setup() 之前）
        assert app.camera_manager is None
        assert app.stream_manager is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
