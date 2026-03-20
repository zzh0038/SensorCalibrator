"""
Send 按钮修复验证测试

测试 _current_calibration_commands 缓存同步问题修复
"""

import pytest
import sys
import os
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSendButtonCommandSync:
    """测试 Send 按钮命令同步修复"""
    
    def test_generate_calibration_commands_updates_cache(self, mocker):
        """测试 generate_calibration_commands 更新 _current_calibration_commands"""
        from sensor_calibrator.app.callback_groups import CalibrationCallbacks
        
        # 创建 mock app
        mock_app = mocker.MagicMock()
        mock_app._current_calibration_commands = []
        mock_app.cmd_text = None  # 不测试 UI 部分
        
        # 创建回调组
        callbacks = CalibrationCallbacks(mock_app)
        
        # Mock calibration_workflow 返回测试命令
        test_commands = [
            "SET:RACKS,1.0,1.0,1.0",
            "SET:RACOF,0.1,0.2,0.3",
        ]
        mock_app.calibration_workflow.generate_calibration_commands.return_value = test_commands
        
        # 执行生成命令
        callbacks.generate_calibration_commands()
        
        # 验证缓存被更新
        assert mock_app._current_calibration_commands == test_commands
        mock_app.log_message.assert_any_call("[DEBUG] Commands cached: 2 commands")
    
    def test_generate_calibration_commands_empty_params(self, mocker):
        """测试无校准参数时不更新缓存"""
        from sensor_calibrator.app.callback_groups import CalibrationCallbacks
        
        mock_app = mocker.MagicMock()
        mock_app._current_calibration_commands = ["old_command"]
        mock_app.cmd_text = None
        
        callbacks = CalibrationCallbacks(mock_app)
        
        # 返回空命令列表（无校准参数）
        mock_app.calibration_workflow.generate_calibration_commands.return_value = []
        
        # 执行生成命令
        callbacks.generate_calibration_commands()
        
        # 验证缓存未被更新（保持旧值）
        assert mock_app._current_calibration_commands == ["old_command"]
    
    def test_send_all_commands_priority_displayed(self, mocker):
        """测试 send_all_commands 优先使用文本框中的命令"""
        from sensor_calibrator.app.callback_groups import CalibrationCallbacks
        
        mock_app = mocker.MagicMock()
        mock_app.serial_manager.is_connected = True
        
        # 设置缓存和文本框内容不同
        cached_commands = ["SET:RACKS,1.0,1.0,1.0"]  # 缓存
        displayed_commands = ["SET:RACKS,2.0,2.0,2.0"]  # 文本框（用户修改后的）
        
        mock_app._current_calibration_commands = cached_commands
        mock_app.cmd_text.get.return_value = "\n".join(displayed_commands) + "\n"
        
        callbacks = CalibrationCallbacks(mock_app)
        
        # Mock send_commands_thread 避免实际发送
        mocker.patch.object(callbacks, 'send_commands_thread')
        
        # 执行发送
        callbacks.send_all_commands()
        
        # 验证使用文本框中的命令（而非缓存）
        call_args = callbacks.send_commands_thread.call_args
        sent_commands = call_args[0][0]
        assert sent_commands == displayed_commands
        assert sent_commands != cached_commands
    
    def test_send_all_commands_fallback_to_cache(self, mocker):
        """测试文本框为空时回退到缓存"""
        from sensor_calibrator.app.callback_groups import CalibrationCallbacks
        
        mock_app = mocker.MagicMock()
        mock_app.serial_manager.is_connected = True
        
        cached_commands = ["SET:RACKS,1.0,1.0,1.0"]
        mock_app._current_calibration_commands = cached_commands
        mock_app.cmd_text.get.return_value = ""  # 空文本框
        
        callbacks = CalibrationCallbacks(mock_app)
        mocker.patch.object(callbacks, 'send_commands_thread')
        
        callbacks.send_all_commands()
        
        call_args = callbacks.send_commands_thread.call_args
        sent_commands = call_args[0][0]
        assert sent_commands == cached_commands
    
    def test_send_all_commands_fallback_to_generate(self, mocker):
        """测试缓存也为空时重新生成命令"""
        from sensor_calibrator.app.callback_groups import CalibrationCallbacks
        
        mock_app = mocker.MagicMock()
        mock_app.serial_manager.is_connected = True
        
        generated_commands = ["SET:RACKS,1.0,1.0,1.0"]
        mock_app._current_calibration_commands = []
        mock_app.cmd_text.get.return_value = ""
        mock_app.calibration_workflow.generate_calibration_commands.return_value = generated_commands
        
        callbacks = CalibrationCallbacks(mock_app)
        mocker.patch.object(callbacks, 'send_commands_thread')
        
        callbacks.send_all_commands()
        
        call_args = callbacks.send_commands_thread.call_args
        sent_commands = call_args[0][0]
        assert sent_commands == generated_commands
    
    def test_send_all_commands_warning_on_mismatch(self, mocker):
        """测试命令不一致时显示警告"""
        from sensor_calibrator.app.callback_groups import CalibrationCallbacks
        
        mock_app = mocker.MagicMock()
        mock_app.serial_manager.is_connected = True
        
        # 缓存和文本框内容不同
        mock_app._current_calibration_commands = ["SET:RACKS,1.0,1.0,1.0"]
        mock_app.cmd_text.get.return_value = "SET:RACKS,2.0,2.0,2.0\n"
        
        callbacks = CalibrationCallbacks(mock_app)
        mocker.patch.object(callbacks, 'send_commands_thread')
        
        callbacks.send_all_commands()
        
        # 验证显示警告
        mock_app.log_message.assert_any_call(
            "[WARNING] Displayed commands differ from cached commands!"
        )


class TestLoadCalibrationParameters:
    """测试加载校准参数时的命令同步"""
    
    def test_load_parameters_updates_cache(self, mocker, tmp_path):
        """测试加载参数后直接更新命令缓存"""
        from sensor_calibrator.app.callback_groups import CalibrationCallbacks
        import json
        
        # 创建测试校准文件
        test_params = {
            "calibration_params": {
                "mpu_accel_scale": [1.01, 1.02, 1.03],
                "mpu_accel_offset": [0.1, 0.2, 0.3],
                "adxl_accel_scale": [1.001, 1.002, 1.003],
                "adxl_accel_offset": [0.01, 0.02, 0.03],
                "mpu_gyro_offset": [0.001, 0.002, 0.003],
            }
        }
        test_file = tmp_path / "test_calibration.json"
        with open(test_file, 'w') as f:
            json.dump(test_params, f)
        
        # 创建 mock app
        mock_app = mocker.MagicMock()
        mock_app._current_calibration_commands = ["old_command"]
        mock_app.cmd_text = None
        
        # Mock file dialog 返回测试文件
        mocker.patch('tkinter.filedialog.askopenfilename', return_value=str(test_file))
        
        callbacks = CalibrationCallbacks(mock_app)
        
        # Mock set_calibration_params 返回成功
        mock_app.calibration_workflow.set_calibration_params.return_value = True
        
        # Mock generate_calibration_commands 返回新命令
        new_commands = ["SET:RACKS,1.01,1.02,1.03"]
        mock_app.calibration_workflow.generate_calibration_commands.return_value = new_commands
        
        # 执行加载
        callbacks.load_calibration_parameters()
        
        # 验证缓存被更新为新命令
        assert mock_app._current_calibration_commands == new_commands
        mock_app.log_message.assert_any_call(
            "Generated 1 calibration commands from loaded params"
        )


class TestResetUIState:
    """测试 UI 重置时的命令缓存清理"""
    
    def test_reset_ui_clears_command_cache(self, mocker):
        """测试 reset_ui_state 清空 _current_calibration_commands"""
        from sensor_calibrator.app.application import SensorCalibratorApp
        from unittest.mock import patch, MagicMock
        
        # 直接调用 reset_ui_state 方法
        with patch.object(SensorCalibratorApp, '__init__', lambda x: None):
            app = SensorCalibratorApp.__new__(SensorCalibratorApp)
            app.cmd_text = MagicMock()
            app.freq_var = None
            app.position_var = None
            app._current_calibration_commands = ["SET:RACKS,1.0,1.0,1.0"]
            app.packets_received = 0
            app.serial_freq = 0
            app._aky_from_ss13 = None
            
            # Mock 所有依赖
            app.data_processor = MagicMock()
            app.chart_manager = MagicMock()
            app.connect_btn = None
            app.data_btn = None
            
            def mock_reset_stats():
                pass
            def mock_reset_activation():
                pass
            def mock_reset_buttons():
                pass
            
            app._reset_statistics_display = mock_reset_stats
            app._reset_activation_display = mock_reset_activation
            app._reset_button_states = mock_reset_buttons
            app.log_message = MagicMock()
            
            # 执行重置
            SensorCalibratorApp.reset_ui_state(app)
            
            # 验证缓存被清空
            assert app._current_calibration_commands == []
            app.log_message.assert_any_call("[DEBUG] Calibration commands cache cleared")


class TestCommandSyncIntegration:
    """集成测试：验证完整的工作流程"""
    
    def test_full_workflow_calibration_then_send(self, mocker):
        """测试完整流程：校准 → 生成命令 → 发送"""
        from sensor_calibrator.app.callback_groups import CalibrationCallbacks
        from unittest.mock import MagicMock, patch
        
        mock_app = mocker.MagicMock()
        mock_app.serial_manager.is_connected = True
        mock_app.cmd_text = MagicMock()
        
        callbacks = CalibrationCallbacks(mock_app)
        
        # 步骤 1: 生成命令
        test_commands = [
            "SET:RACKS,1.01,1.02,1.03",
            "SET:RACOF,0.1,0.2,0.3",
        ]
        mock_app.calibration_workflow.generate_calibration_commands.return_value = test_commands
        callbacks.generate_calibration_commands()
        
        # 验证缓存更新
        assert mock_app._current_calibration_commands == test_commands
        
        # 步骤 2: 发送命令 - 验证优先使用文本框
        mock_app.cmd_text.get.return_value = "\n".join(test_commands) + "\n"
        
        with patch.object(callbacks, 'send_commands_thread') as mock_thread:
            callbacks.send_all_commands()
            
            # 验证发送线程被调用，且参数正确
            assert mock_thread.called
            call_args = mock_thread.call_args
            sent_commands = call_args[0][0]
            assert sent_commands == test_commands
    
    def test_full_workflow_load_then_send(self, mocker, tmp_path):
        """测试完整流程：加载参数 → 生成命令 → 发送"""
        from sensor_calibrator.app.callback_groups import CalibrationCallbacks
        import json
        
        # 创建测试文件
        test_params = {
            "calibration_params": {
                "mpu_accel_scale": [1.5, 1.5, 1.5],
                "mpu_accel_offset": [0.5, 0.5, 0.5],
                "adxl_accel_scale": [1.1, 1.1, 1.1],
                "adxl_accel_offset": [0.1, 0.1, 0.1],
                "mpu_gyro_offset": [0.01, 0.01, 0.01],
            }
        }
        test_file = tmp_path / "test_cal.json"
        with open(test_file, 'w') as f:
            json.dump(test_params, f)
        
        mock_app = mocker.MagicMock()
        mock_app.serial_manager.is_connected = True
        mock_app.cmd_text = mocker.MagicMock()
        
        mocker.patch('tkinter.filedialog.askopenfilename', return_value=str(test_file))
        
        callbacks = CalibrationCallbacks(mock_app)
        
        # Mock 加载参数
        mock_app.calibration_workflow.set_calibration_params.return_value = True
        loaded_commands = ["SET:RACKS,1.5,1.5,1.5"]
        mock_app.calibration_workflow.generate_calibration_commands.return_value = loaded_commands
        
        # 步骤 1: 加载参数
        callbacks.load_calibration_parameters()
        
        # 验证缓存是加载后的命令
        assert mock_app._current_calibration_commands == loaded_commands
        
        # 步骤 2: 发送
        mocker.patch.object(callbacks, 'send_commands_thread')
        mock_app.cmd_text.get.return_value = "\n".join(loaded_commands) + "\n"
        
        callbacks.send_all_commands()
        
        call_args = callbacks.send_commands_thread.call_args
        sent_commands = call_args[0][0]
        assert sent_commands == loaded_commands


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
