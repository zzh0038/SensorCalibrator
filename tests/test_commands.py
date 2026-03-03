"""
Unit tests for new commands (Sprint 1-3).

Tests:
- SS:7 Save Config command
- SS:9 Restart Sensor command
- SET:AGT Alarm Threshold command
- Activation key generation and verification
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_calibrator.serial_manager import SerialManager
from sensor_calibrator.network_manager import NetworkManager
from sensor_calibrator.activation_workflow import ActivationWorkflow
from sensor_calibrator.config import Config


def create_mock_serial_manager():
    """Create SerialManager with mocked serial port."""
    callbacks = {
        "log_message": Mock(),
        "get_data_queue": Mock(return_value=Mock()),
        "update_connection_state": Mock(),
    }
    manager = SerialManager(callbacks)
    # Mock the serial port
    manager._ser = Mock()
    manager._ser.is_open = True
    return manager


def create_mock_network_manager():
    """Create NetworkManager with mocked serial manager."""
    serial_manager = create_mock_serial_manager()
    callbacks = {
        "log_message": Mock(),
        "get_wifi_params": Mock(return_value={}),
        "set_wifi_params": Mock(),
        "get_mqtt_params": Mock(return_value={}),
        "set_mqtt_params": Mock(),
        "get_ota_params": Mock(return_value={}),
        "set_ota_params": Mock(),
        "enable_config_buttons": Mock(),
    }
    return NetworkManager(serial_manager, callbacks)


class TestSSCommands(unittest.TestCase):
    """Test SS command methods."""

    def test_send_ss7_save_config(self):
        """Test SS:7 Save Config command format."""
        manager = create_mock_serial_manager()
        
        # Call the method
        result = manager.send_ss7_save_config()
        
        # Verify command was sent correctly
        manager._ser.write.assert_called_once_with(b"SS:7\n")
        manager._ser.flush.assert_called_once()
        self.assertTrue(result)

    def test_send_ss9_restart_sensor(self):
        """Test SS:9 Restart Sensor command format."""
        manager = create_mock_serial_manager()
        
        # Call the method
        result = manager.send_ss9_restart_sensor()
        
        # Verify command was sent correctly
        manager._ser.write.assert_called_once_with(b"SS:9\n")
        manager._ser.flush.assert_called_once()
        self.assertTrue(result)

    def test_ss_command_when_not_connected(self):
        """Test SS commands fail when not connected."""
        callbacks = {
            "log_message": Mock(),
        }
        manager = SerialManager(callbacks)
        manager._ser = None  # Not connected
        
        result = manager.send_ss7_save_config()
        self.assertFalse(result)


class TestAlarmThresholdCommand(unittest.TestCase):
    """Test SET:AGT Alarm Threshold command."""

    @patch('sensor_calibrator.network_manager.threading.Thread')
    def test_set_alarm_threshold_format(self, mock_thread):
        """Test SET:AGT command format."""
        manager = create_mock_network_manager()
        
        # Set threshold
        result = manager.set_alarm_threshold(0.2, 0.3)
        
        # Verify thread was started
        self.assertTrue(result)
        mock_thread.assert_called_once()

    def test_set_alarm_threshold_range_validation(self):
        """Test alarm threshold range validation."""
        manager = create_mock_network_manager()
        
        # Test valid range
        with patch('sensor_calibrator.network_manager.threading.Thread'):
            result = manager.set_alarm_threshold(0.1, 0.1)
            self.assertTrue(result)
            
            result = manager.set_alarm_threshold(10.0, 45.0)
            self.assertTrue(result)
        
        # Test invalid accel threshold (too low)
        result = manager.set_alarm_threshold(0.05, 0.2)
        self.assertFalse(result)
        
        # Test invalid accel threshold (too high)
        result = manager.set_alarm_threshold(15.0, 0.2)
        self.assertFalse(result)
        
        # Test invalid gyro threshold (too low)
        result = manager.set_alarm_threshold(0.2, 0.05)
        self.assertFalse(result)
        
        # Test invalid gyro threshold (too high)
        result = manager.set_alarm_threshold(0.2, 50.0)
        self.assertFalse(result)

    def test_extract_alarm_threshold(self):
        """Test extracting alarm threshold from sensor properties."""
        manager = create_mock_network_manager()
        
        # Test with valid properties
        sensor_properties = {
            "sys": {
                "AT": 0.25,  # Accel threshold
                "GT": 0.35,  # Gyro threshold
            }
        }
        result = manager.extract_alarm_threshold(sensor_properties)
        
        self.assertEqual(result["accel_threshold"], 0.25)
        self.assertEqual(result["gyro_threshold"], 0.35)
        
        # Test with missing properties
        result = manager.extract_alarm_threshold({})
        self.assertEqual(result, {})


class TestActivationKey(unittest.TestCase):
    """Test activation key generation and verification."""

    def setUp(self):
        """Set up test fixtures."""
        callbacks = {"log_message": Mock()}
        self.workflow = ActivationWorkflow(callbacks)
        self.workflow._mac_address = "AA:BB:CC:DD:EE:FF"

    def test_generate_key_from_mac(self):
        """Test key generation from MAC address."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = self.workflow.generate_key_from_mac(mac)
        
        # Should be 64 characters (SHA-256 hex)
        self.assertEqual(len(key), 64)
        
        # Should be hexadecimal
        self.assertTrue(all(c in "0123456789abcdef" for c in key.lower()))
        
        # Same MAC should generate same key
        key2 = self.workflow.generate_key_from_mac(mac)
        self.assertEqual(key, key2)
        
        # Different MAC should generate different key
        mac2 = "11:22:33:44:55:66"
        key3 = self.workflow.generate_key_from_mac(mac2)
        self.assertNotEqual(key, key3)

    def test_verify_key_correct_fragment(self):
        """Test key verification with correct fragment."""
        mac = "AA:BB:CC:DD:EE:FF"
        full_key = self.workflow.generate_key_from_mac(mac)
        key_fragment = full_key[5:12]  # 7 characters
        
        # Should verify successfully
        result = self.workflow.verify_key(key_fragment)
        self.assertTrue(result)

    def test_verify_key_incorrect_fragment(self):
        """Test key verification with incorrect fragment."""
        mac = "AA:BB:CC:DD:EE:FF"
        self.workflow.generate_key_from_mac(mac)
        
        # Wrong fragment
        result = self.workflow.verify_key("1234567")
        self.assertFalse(result)

    def test_verify_key_wrong_length(self):
        """Test key verification with wrong length."""
        mac = "AA:BB:CC:DD:EE:FF"
        self.workflow.generate_key_from_mac(mac)
        
        # Too short
        result = self.workflow.verify_key("123456")
        self.assertFalse(result)
        
        # Too long
        result = self.workflow.verify_key("12345678")
        self.assertFalse(result)


class TestConfigConstants(unittest.TestCase):
    """Test configuration constants."""

    def test_ss_command_ids(self):
        """Test SS command ID constants."""
        self.assertEqual(Config.CMD_SAVE_CONFIG, 7)
        self.assertEqual(Config.CMD_RESTART_SENSOR, 9)

    def test_alarm_threshold_ranges(self):
        """Test alarm threshold range constants."""
        # Accel range
        self.assertEqual(Config.ALARM_THRESHOLD_ACCEL_MIN, 0.1)
        self.assertEqual(Config.ALARM_THRESHOLD_ACCEL_MAX, 10.0)
        
        # Gyro range
        self.assertEqual(Config.ALARM_THRESHOLD_GYRO_MIN, 0.1)
        self.assertEqual(Config.ALARM_THRESHOLD_GYRO_MAX, 45.0)


if __name__ == "__main__":
    unittest.main()
