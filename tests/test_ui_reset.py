"""
UI 重置功能测试

测试 reset_ui_state 及其相关功能
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUIReset:
    """测试 UI 重置功能"""
    
    def test_reset_ui_clears_data_buffer(self, mocker):
        """测试重置UI清空数据缓冲区"""
        # Mock 应用对象
        mock_app = mocker.MagicMock()
        mock_app.stats_labels = {}
        mock_app.freq_var = mocker.MagicMock()
        mock_app.position_var = mocker.MagicMock()
        mock_app.cmd_text = mocker.MagicMock()
        mock_app.mac_var = mocker.MagicMock()
        mock_app.key_var = mocker.MagicMock()
        mock_app.activation_status_var = mocker.MagicMock()
        mock_app.activation_status_label = mocker.MagicMock()
        mock_app.chart_manager = mocker.MagicMock()
        mock_app.root = mocker.MagicMock()
        
        # 导入并调用方法
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 测试数据处理器被清空
        mock_app.data_processor.clear_all.assert_not_called()
        
        # 调用重置方法
        SensorCalibratorApp.reset_ui_state(mock_app)
        
        # 验证数据处理器被清空
        mock_app.data_processor.clear_all.assert_called_once()
    
    def test_reset_ui_clears_chart_data(self, mocker):
        """测试重置UI清空图表数据"""
        mock_app = mocker.MagicMock()
        mock_app.stats_labels = {}
        mock_app.freq_var = mocker.MagicMock()
        mock_app.position_var = mocker.MagicMock()
        mock_app.cmd_text = mocker.MagicMock()
        mock_app.mac_var = mocker.MagicMock()
        mock_app.key_var = mocker.MagicMock()
        mock_app.activation_status_var = mocker.MagicMock()
        mock_app.activation_status_label = mocker.MagicMock()
        mock_app.chart_manager = mocker.MagicMock()
        mock_app.root = mocker.MagicMock()
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用重置方法
        SensorCalibratorApp.reset_ui_state(mock_app)
        
        # 验证图表数据被清空
        mock_app.chart_manager.clear_data.assert_called_once()
    
    def test_reset_ui_resets_frequency(self, mocker):
        """测试重置UI重置频率显示"""
        mock_app = mocker.MagicMock()
        mock_app.stats_labels = {}
        mock_app.freq_var = mocker.MagicMock()
        mock_app.position_var = mocker.MagicMock()
        mock_app.cmd_text = mocker.MagicMock()
        mock_app.mac_var = mocker.MagicMock()
        mock_app.key_var = mocker.MagicMock()
        mock_app.activation_status_var = mocker.MagicMock()
        mock_app.activation_status_label = mocker.MagicMock()
        mock_app.chart_manager = mocker.MagicMock()
        mock_app.root = mocker.MagicMock()
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用重置方法
        SensorCalibratorApp.reset_ui_state(mock_app)
        
        # 验证频率显示重置为 "0 Hz"
        mock_app.freq_var.set.assert_called_once_with("0 Hz")
    
    def test_reset_ui_resets_position(self, mocker):
        """测试重置UI重置位置显示"""
        mock_app = mocker.MagicMock()
        mock_app.stats_labels = {}
        mock_app.freq_var = mocker.MagicMock()
        mock_app.position_var = mocker.MagicMock()
        mock_app.cmd_text = mocker.MagicMock()
        mock_app.mac_var = mocker.MagicMock()
        mock_app.key_var = mocker.MagicMock()
        mock_app.activation_status_var = mocker.MagicMock()
        mock_app.activation_status_label = mocker.MagicMock()
        mock_app.chart_manager = mocker.MagicMock()
        mock_app.root = mocker.MagicMock()
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用重置方法
        SensorCalibratorApp.reset_ui_state(mock_app)
        
        # 验证位置显示重置
        mock_app.position_var.set.assert_called_once_with("Position: Not calibrating")
    
    def test_reset_ui_clears_commands(self, mocker):
        """测试重置UI清空命令区"""
        mock_app = mocker.MagicMock()
        mock_app.stats_labels = {}
        mock_app.freq_var = mocker.MagicMock()
        mock_app.position_var = mocker.MagicMock()
        mock_app.cmd_text = mocker.MagicMock()
        mock_app.mac_var = mocker.MagicMock()
        mock_app.key_var = mocker.MagicMock()
        mock_app.activation_status_var = mocker.MagicMock()
        mock_app.activation_status_label = mocker.MagicMock()
        mock_app.chart_manager = mocker.MagicMock()
        mock_app.root = mocker.MagicMock()
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用重置方法
        SensorCalibratorApp.reset_ui_state(mock_app)
        
        # 验证命令区被清空
        mock_app.cmd_text.delete.assert_called_once_with(1.0, "end")
    
    def test_reset_ui_resets_activation(self, mocker):
        """测试重置UI重置激活状态"""
        mock_app = mocker.MagicMock()
        mock_app.stats_labels = {}
        mock_app.freq_var = mocker.MagicMock()
        mock_app.position_var = mocker.MagicMock()
        mock_app.cmd_text = mocker.MagicMock()
        mock_app.mac_var = mocker.MagicMock()
        mock_app.key_var = mocker.MagicMock()
        mock_app.activation_status_var = mocker.MagicMock()
        mock_app.activation_status_label = mocker.MagicMock()
        mock_app.chart_manager = mocker.MagicMock()
        mock_app.root = mocker.MagicMock()
        
        # 设置初始值
        mock_app.mac_address = "AA:BB:CC:DD:EE:FF"
        mock_app.generated_key = "some_key"
        mock_app.sensor_activated = True
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用重置方法
        SensorCalibratorApp.reset_ui_state(mock_app)
        
        # 验证激活状态被重置
        assert mock_app.mac_address is None
        assert mock_app.generated_key is None
        assert mock_app.sensor_activated is False
        
        # 验证UI显示被重置
        mock_app.mac_var.set.assert_called_once_with("--")
        mock_app.key_var.set.assert_called_once_with("")
        mock_app.activation_status_var.set.assert_called_once_with("Not Activated")
        mock_app.activation_status_label.config.assert_called_once_with(foreground="red")
    
    def test_reset_ui_resets_internal_state(self, mocker):
        """测试重置UI重置内部状态变量"""
        mock_app = mocker.MagicMock()
        mock_app.stats_labels = {}
        mock_app.freq_var = mocker.MagicMock()
        mock_app.position_var = mocker.MagicMock()
        mock_app.cmd_text = mocker.MagicMock()
        mock_app.mac_var = mocker.MagicMock()
        mock_app.key_var = mocker.MagicMock()
        mock_app.activation_status_var = mocker.MagicMock()
        mock_app.activation_status_label = mocker.MagicMock()
        mock_app.chart_manager = mocker.MagicMock()
        mock_app.root = mocker.MagicMock()
        
        # 设置初始值
        mock_app.packets_received = 100
        mock_app.serial_freq = 50
        mock_app._aky_from_ss13 = "some_aky"
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用重置方法
        SensorCalibratorApp.reset_ui_state(mock_app)
        
        # 验证内部状态被重置
        assert mock_app.packets_received == 0
        assert mock_app.serial_freq == 0
        assert mock_app._aky_from_ss13 is None
    
    def test_reset_ui_logs_message(self, mocker):
        """测试重置UI记录日志"""
        mock_app = mocker.MagicMock()
        mock_app.stats_labels = {}
        mock_app.freq_var = mocker.MagicMock()
        mock_app.position_var = mocker.MagicMock()
        mock_app.cmd_text = mocker.MagicMock()
        mock_app.mac_var = mocker.MagicMock()
        mock_app.key_var = mocker.MagicMock()
        mock_app.activation_status_var = mocker.MagicMock()
        mock_app.activation_status_label = mocker.MagicMock()
        mock_app.chart_manager = mocker.MagicMock()
        mock_app.root = mocker.MagicMock()
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用重置方法
        SensorCalibratorApp.reset_ui_state(mock_app)
        
        # 验证日志记录
        mock_app.log_message.assert_called_with("UI 已重置")


class TestUIResetStatistics:
    """测试统计标签重置功能"""
    
    def test_reset_statistics_display_resets_all_sensors(self, mocker):
        """测试重置所有传感器的统计标签"""
        mock_app = mocker.MagicMock()
        
        # 创建模拟的 StringVar
        mock_vars = {}
        for sensor in ['mpu_accel', 'adxl_accel', 'mpu_gyro']:
            for axis in ['x', 'y', 'z']:
                mock_vars[f"{sensor}_{axis}_mean"] = mocker.MagicMock()
                mock_vars[f"{sensor}_{axis}_std"] = mocker.MagicMock()
        
        mock_vars['gravity_mean'] = mocker.MagicMock()
        mock_vars['gravity_std'] = mocker.MagicMock()
        
        mock_app.stats_labels = mock_vars
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用重置方法
        SensorCalibratorApp._reset_statistics_display(mock_app)
        
        # 验证所有统计标签被重置
        for sensor in ['mpu_accel', 'adxl_accel', 'mpu_gyro']:
            for axis in ['x', 'y', 'z']:
                mock_vars[f"{sensor}_{axis}_mean"].set.assert_called_once_with("μ: 0.000")
                mock_vars[f"{sensor}_{axis}_std"].set.assert_called_once_with("σ: 0.000")
        
        mock_vars['gravity_mean'].set.assert_called_once_with("Mean: 0.000")
        mock_vars['gravity_std'].set.assert_called_once_with("Std: 0.000")


class TestResetConfirmation:
    """测试确认弹窗功能"""
    
    def test_show_reset_confirmation_calls_messagebox(self, mocker):
        """测试确认弹窗调用 messagebox"""
        mock_app = mocker.MagicMock()
        
        # Mock messagebox
        mock_messagebox = mocker.patch('sensor_calibrator.app.application.messagebox')
        mock_messagebox.askokcancel.return_value = True
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用方法
        result = SensorCalibratorApp.show_reset_confirmation(mock_app)
        
        # 验证 messagebox 被调用
        mock_messagebox.askokcancel.assert_called_once()
        assert result is True
    
    def test_reset_ui_with_confirmation_silent_mode(self, mocker):
        """测试静默模式直接重置"""
        mock_app = mocker.MagicMock()
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用静默模式
        result = SensorCalibratorApp.reset_ui_with_confirmation(mock_app, silent=True)
        
        # 验证直接重置，不显示弹窗
        mock_app.reset_ui_state.assert_called_once()
        assert result is True
    
    def test_reset_ui_with_confirmation_shows_dialog(self, mocker):
        """测试非静默模式显示确认弹窗"""
        mock_app = mocker.MagicMock()
        mock_app.show_reset_confirmation.return_value = True
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用方法
        result = SensorCalibratorApp.reset_ui_with_confirmation(mock_app, silent=False)
        
        # 验证显示确认弹窗
        mock_app.show_reset_confirmation.assert_called_once()


class TestDeviceDisconnectedDialog:
    """测试设备断开连接提示框"""
    
    def test_show_device_disconnected_dialog_stops_stream(self, mocker):
        """测试显示断开提示时停止数据流"""
        mock_app = mocker.MagicMock()
        mock_app.is_reading = True
        
        # Mock messagebox
        mock_messagebox = mocker.patch('sensor_calibrator.app.application.messagebox')
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用方法
        SensorCalibratorApp._show_device_disconnected_dialog(mock_app)
        
        # 验证数据流被停止
        assert mock_app.is_reading is False
        mock_app.serial_manager.stop_reading.assert_called_once()
    
    def test_show_device_disconnected_dialog_shows_info(self, mocker):
        """测试显示断开提示框"""
        mock_app = mocker.MagicMock()
        mock_app.is_reading = False
        
        # Mock messagebox
        mock_messagebox = mocker.patch('sensor_calibrator.app.application.messagebox')
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用方法
        SensorCalibratorApp._show_device_disconnected_dialog(mock_app)
        
        # 验证信息提示框被显示
        mock_messagebox.showinfo.assert_called_once()
        # 验证标题和内容
        call_args = mock_messagebox.showinfo.call_args
        assert call_args[0][0] == "设备已断开连接"
    
    def test_show_device_disconnected_dialog_resets_ui(self, mocker):
        """测试显示断开提示后重置UI"""
        mock_app = mocker.MagicMock()
        mock_app.is_reading = False
        
        # Mock messagebox
        mock_messagebox = mocker.patch('sensor_calibrator.app.application.messagebox')
        
        from sensor_calibrator.app.application import SensorCalibratorApp
        
        # 调用方法
        SensorCalibratorApp._show_device_disconnected_dialog(mock_app)
        
        # 验证UI被重置
        mock_app.reset_ui_state.assert_called_once()
        mock_app.log_message.assert_called_with("设备断开连接，UI 已重置")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
