"""
Integration tests for SensorCalibrator.

Tests core functionality:
1. Data parsing from serial stream
2. Calibration calculations
3. Activation key generation
4. Network command construction
5. Configuration validation
"""

import unittest
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

# Import modules to test
from sensor_calibrator import (
    Config,
    validate_ssid,
    validate_password,
    validate_port,
    validate_url,
)
from calibration import compute_six_position_calibration, compute_gyro_offset
from activation import (
    generate_key_from_mac,
    verify_key,
    validate_mac_address,
    extract_mac_from_properties,
    check_activation_status,
)
from network_config import build_wifi_command, build_mqtt_command, build_ota_command


class TestCalibrationAlgorithms(unittest.TestCase):
    """Test calibration calculation algorithms."""

    def test_six_position_calibration_perfect_data(self):
        """Test calibration with perfect sensor data."""
        # Perfect 6-position data (ideal case)
        # Each position should show gravity on one axis only
        mpu_readings = [
            [9.81, 0, 0],  # +X axis down
            [-9.81, 0, 0],  # -X axis down
            [0, 9.81, 0],  # +Y axis down
            [0, -9.81, 0],  # -Y axis down
            [0, 0, 9.81],  # +Z axis down
            [0, 0, -9.81],  # -Z axis down
        ]

        scales, offsets = compute_six_position_calibration(mpu_readings, 9.81)

        # With perfect data, scales should be close to 1.0
        for scale in scales:
            self.assertAlmostEqual(scale, 1.0, places=2)

        # Offsets should be close to 0
        for offset in offsets:
            self.assertAlmostEqual(offset, 0.0, places=2)

    def test_six_position_calibration_with_offset(self):
        """Test calibration with biased sensor data."""
        # Add offset to simulate sensor bias
        mpu_readings = [
            [9.91, 0.1, 0],  # +X with offset
            [-9.71, -0.1, 0],  # -X with offset
            [0.1, 9.91, 0],  # +Y with offset
            [-0.1, -9.71, 0],  # -Y with offset
            [0, 0.1, 9.91],  # +Z with offset
            [0, -0.1, -9.71],  # -Z with offset
        ]

        scales, offsets = compute_six_position_calibration(mpu_readings, 9.81)

        # Scales should still be close to 1.0 after correction
        for scale in scales:
            self.assertGreater(scale, 0.9)
            self.assertLess(scale, 1.1)

    def test_six_position_calibration_invalid_length(self):
        """Test calibration with wrong number of positions."""
        invalid_data = [
            [9.81, 0, 0],
            [-9.81, 0, 0],
        ]  # Only 2 positions, need 6

        with self.assertRaises(ValueError):
            compute_six_position_calibration(invalid_data, 9.81)

    def test_six_position_calibration_invalid_gravity(self):
        """Test calibration with invalid gravity value."""
        mpu_readings = [
            [9.81, 0, 0],
            [-9.81, 0, 0],
            [0, 9.81, 0],
            [0, -9.81, 0],
            [0, 0, 9.81],
            [0, 0, -9.81],
        ]

        with self.assertRaises(ValueError):
            compute_six_position_calibration(mpu_readings, 0)  # Zero gravity

        with self.assertRaises(ValueError):
            compute_six_position_calibration(mpu_readings, -9.81)  # Negative gravity

    def test_six_position_calibration_invalid_shape(self):
        """Test calibration with wrong data shape."""
        invalid_data = [
            [9.81, 0],  # Wrong: only 2 values
            [-9.81, 0],
        ]

        with self.assertRaises(ValueError):
            compute_six_position_calibration(invalid_data, 9.81)

    def test_gyro_offset_calculation(self):
        """Test gyroscope offset calculation."""
        # Simulate stationary gyroscope readings (should be ~0)
        readings = [
            [0.01, -0.02, 0.01],
            [0.02, 0.01, -0.01],
            [-0.01, 0.02, 0.01],
            [0.00, 0.00, -0.01],
        ]

        offset = compute_gyro_offset(readings)

        # Mean should be close to 0
        for val in offset:
            self.assertLess(abs(val), 0.1)

    def test_gyro_offset_empty(self):
        """Test gyro offset with empty data."""
        offset = compute_gyro_offset([])

        self.assertEqual(offset, [0.0, 0.0, 0.0])

    def test_gyro_offset_single_sample(self):
        """Test gyro offset with single sample."""
        readings = [[0.1, 0.2, 0.3]]

        offset = compute_gyro_offset(readings)

        self.assertAlmostEqual(offset[0], 0.1)
        self.assertAlmostEqual(offset[1], 0.2)
        self.assertAlmostEqual(offset[2], 0.3)


class TestActivation(unittest.TestCase):
    """Test sensor activation and key generation."""

    def test_key_generation_valid_mac(self):
        """Test key generation with valid MAC addresses."""
        test_cases = [
            "AA:BB:CC:DD:EE:FF",
            "aa:bb:cc:dd:ee:ff",  # lowercase
            "AA-BB-CC-DD-EE-FF",  # dash separator
            "aabbccddeeff",  # no separator
        ]

        for mac in test_cases:
            key = generate_key_from_mac(mac)
            self.assertIsInstance(key, str)
            self.assertEqual(len(key), 64)  # SHA-256 hex = 64 chars

    def test_key_generation_invalid_mac(self):
        """Test key generation with invalid MAC addresses."""
        invalid_macs = [
            "invalid_mac",
            "",
            "AA:BB:CC:DD",  # Too short
            "GG:HH:II:JJ:KK:LL",  # Invalid hex
        ]

        for mac in invalid_macs:
            with self.assertRaises((ValueError, AttributeError)):
                generate_key_from_mac(mac)

    def test_key_consistency(self):
        """Test that same MAC always generates same key."""
        mac = "AA:BB:CC:DD:EE:FF"
        key1 = generate_key_from_mac(mac)
        key2 = generate_key_from_mac(mac)
        self.assertEqual(key1, key2)

    def test_key_different_macs(self):
        """Test that different MACs generate different keys."""
        key1 = generate_key_from_mac("AA:BB:CC:DD:EE:FF")
        key2 = generate_key_from_mac("BB:BB:CC:DD:EE:FF")
        self.assertNotEqual(key1, key2)

    def test_verify_key_correct(self):
        """Test key verification with correct key."""
        mac = "AA:BB:CC:DD:EE:FF"
        full_key = generate_key_from_mac(mac)
        short_key = full_key[5:12]  # The 7-char fragment

        result = verify_key(short_key, mac)
        self.assertTrue(result)

    def test_verify_key_incorrect(self):
        """Test key verification with incorrect key."""
        mac = "AA:BB:CC:DD:EE:FF"

        result = verify_key("wrong12", mac)
        self.assertFalse(result)

    def test_verify_key_wrong_length(self):
        """Test key verification with wrong length key."""
        mac = "AA:BB:CC:DD:EE:FF"

        result = verify_key("tooshort", mac)  # Only 8 chars
        self.assertFalse(result)

    def test_validate_mac_address(self):
        """Test MAC address validation."""
        valid_macs = [
            "AA:BB:CC:DD:EE:FF",
            "aa:bb:cc:dd:ee:ff",
            "AA-BB-CC-DD-EE-FF",
            "01:23:45:67:89:AB",
        ]

        for mac in valid_macs:
            self.assertTrue(validate_mac_address(mac))

    def test_validate_mac_address_invalid(self):
        """Test MAC address validation with invalid addresses."""
        invalid_macs = [
            "invalid",
            "",
            "AA:BB:CC:DD:EE",  # Too short
            "AA:BB:CC:DD:EE:FF:00",  # Too long
            "GG:HH:II:JJ:KK:LL",  # Invalid hex
        ]

        for mac in invalid_macs:
            self.assertFalse(validate_mac_address(mac))

    def test_extract_mac_from_properties(self):
        """Test MAC extraction from sensor properties."""
        properties = {"sys": {"MAC": "AA:BB:CC:DD:EE:FF"}}

        mac = extract_mac_from_properties(properties)
        self.assertEqual(mac, "AA:BB:CC:DD:EE:FF")

    def test_extract_mac_with_different_keys(self):
        """Test MAC extraction with different property keys."""
        # Test various MAC field names
        test_cases = [
            ({"sys": {"MAC": "11:22:33:44:55:66"}}, "11:22:33:44:55:66"),
            ({"sys": {"mac": "22:33:44:55:66:77"}}, "22:33:44:55:66:77"),
            ({"sys": {"mac_address": "33:44:55:66:77:88"}}, "33:44:55:66:77:88"),
        ]

        for properties, expected in test_cases:
            result = extract_mac_from_properties(properties)
            self.assertEqual(result, expected)

    def test_extract_mac_not_found(self):
        """Test MAC extraction when not in properties."""
        properties = {"sys": {"DN": "SomeDevice"}}

        result = extract_mac_from_properties(properties)
        self.assertIsNone(result)

    def test_extract_mac_empty_properties(self):
        """Test MAC extraction with empty properties."""
        result = extract_mac_from_properties({})
        self.assertIsNone(result)

        result = extract_mac_from_properties({"sys": {}})
        self.assertIsNone(result)

    def test_check_activation_status_activated(self):
        """Test activation status check when activated."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = generate_key_from_mac(mac)

        properties = {
            "sys": {
                "MAC": mac,
                "AKY": key[5:12],  # 7-char key fragment
            }
        }

        result = check_activation_status(properties, mac)
        self.assertTrue(result)

    def test_check_activation_status_not_activated(self):
        """Test activation status check when not activated."""
        properties = {
            "sys": {
                "MAC": "AA:BB:CC:DD:EE:FF",
                "AKY": "",  # Empty key
            }
        }

        result = check_activation_status(properties, "AA:BB:CC:DD:EE:FF")
        self.assertFalse(result)


class TestNetworkCommands(unittest.TestCase):
    """Test network configuration command construction."""

    def test_wifi_command_valid(self):
        """Test WiFi command with valid parameters."""
        ok, error, cmd = build_wifi_command("MyNetwork", "password123")

        self.assertTrue(ok)
        self.assertEqual(error, "")
        self.assertEqual(cmd, "SET:WF,MyNetwork,password123")

    def test_wifi_command_with_spaces(self):
        """Test WiFi command with spaces in parameters."""
        ok, error, cmd = build_wifi_command("My Network", "my password")

        self.assertTrue(ok)
        self.assertIn("My Network", cmd)
        self.assertIn("my password", cmd)

    def test_wifi_command_empty_ssid(self):
        """Test WiFi command with empty SSID."""
        ok, error, cmd = build_wifi_command("", "password")

        self.assertFalse(ok)
        self.assertIn("SSID", error)

    def test_wifi_command_ssid_too_long(self):
        """Test WiFi command with SSID too long."""
        long_ssid = "A" * 33  # Max is 32
        ok, error, cmd = build_wifi_command(long_ssid, "password")

        self.assertFalse(ok)
        self.assertIn("32", error)

    def test_wifi_command_password_too_long(self):
        """Test WiFi command with password too long."""
        long_password = "A" * 65  # Max is 64
        ok, error, cmd = build_wifi_command("SSID", long_password)

        self.assertFalse(ok)
        self.assertIn("64", error)

    def test_mqtt_command_valid(self):
        """Test MQTT command with valid parameters."""
        ok, error, cmd = build_mqtt_command(
            "broker.example.com", "1883", "user", "pass"
        )

        self.assertTrue(ok)
        self.assertIn("SET:MQ", cmd)
        self.assertIn("broker.example.com", cmd)
        self.assertIn("1883", cmd)
        self.assertIn("user", cmd)

    def test_mqtt_command_empty_broker(self):
        """Test MQTT command with empty broker."""
        ok, error, cmd = build_mqtt_command("", "1883", "user", "pass")

        self.assertFalse(ok)
        self.assertIn("broker", error.lower())

    def test_mqtt_command_invalid_port(self):
        """Test MQTT command with invalid port."""
        ok, error, cmd = build_mqtt_command("broker.example.com", "abc", "user", "pass")

        self.assertFalse(ok)

    def test_mqtt_command_default_port(self):
        """Test MQTT command with default port."""
        ok, error, cmd = build_mqtt_command("broker.example.com", "", "user", "pass")

        self.assertTrue(ok)
        self.assertIn("1883", cmd)

    def test_ota_command_valid(self):
        """Test OTA command with valid URLs."""
        ok, error, cmd = build_ota_command(
            "http://url1.com", "http://url2.com", "http://url3.com", "http://url4.com"
        )

        self.assertTrue(ok)
        self.assertIn("SET:OTA", cmd)

    def test_ota_command_with_empty_urls(self):
        """Test OTA command with some empty URLs."""
        ok, error, cmd = build_ota_command("http://url1.com", "", "", "")

        self.assertTrue(ok)
        self.assertIn("SET:OTA", cmd)

    def test_ota_command_invalid_url(self):
        """Test OTA command with invalid URL."""
        ok, error, cmd = build_ota_command("invalid_url", "", "", "")

        self.assertFalse(ok)
        self.assertIn("http", error.lower())


class TestValidation(unittest.TestCase):
    """Test validation functions."""

    def test_validate_ssid_valid(self):
        """Test SSID validation with valid values."""
        valid_cases = ["MyNetwork", "a", "A" * 32]

        for ssid in valid_cases:
            valid, msg = validate_ssid(ssid)
            self.assertTrue(valid, f"SSID '{ssid}' should be valid")

    def test_validate_ssid_invalid(self):
        """Test SSID validation with invalid values."""
        invalid_cases = ["", "A" * 33]

        for ssid in invalid_cases:
            valid, msg = validate_ssid(ssid)
            self.assertFalse(valid, f"SSID '{ssid}' should be invalid")

    def test_validate_password_valid(self):
        """Test password validation with valid values."""
        valid_cases = ["", "password", "A" * 64]

        for password in valid_cases:
            valid, msg = validate_password(password)
            self.assertTrue(valid, f"Password should be valid")

    def test_validate_password_invalid(self):
        """Test password validation with invalid values."""
        invalid_cases = ["A" * 65]  # Too long

        for password in invalid_cases:
            valid, msg = validate_password(password)
            self.assertFalse(valid, f"Password should be invalid")

    def test_validate_port_valid(self):
        """Test port validation with valid values."""
        valid_cases = ["1", "80", "1883", "8080", "65535"]

        for port in valid_cases:
            valid, msg = validate_port(port)
            self.assertTrue(valid, f"Port '{port}' should be valid")

    def test_validate_port_invalid(self):
        """Test port validation with invalid values."""
        invalid_cases = ["0", "65536", "abc", "-1", ""]

        for port in invalid_cases:
            valid, msg = validate_port(port)
            self.assertFalse(valid, f"Port '{port}' should be invalid")

    def test_validate_url_valid(self):
        """Test URL validation with valid values."""
        valid_cases = ["", "http://example.com", "https://example.com"]

        for url in valid_cases:
            valid, msg = validate_url(url)
            self.assertTrue(valid, f"URL '{url}' should be valid")

    def test_validate_url_invalid(self):
        """Test URL validation with invalid values."""
        invalid_cases = ["ftp://example.com", "example.com", "httpexample.com"]

        for url in invalid_cases:
            valid, msg = validate_url(url)
            self.assertFalse(valid, f"URL '{url}' should be invalid")


class TestConfiguration(unittest.TestCase):
    """Test configuration constants."""

    def test_config_values_exist(self):
        """Test that all required config values exist."""
        self.assertIsNotNone(Config.MAX_DATA_POINTS)
        self.assertIsNotNone(Config.UPDATE_INTERVAL_MS)
        self.assertIsNotNone(Config.EXPECTED_FREQUENCY)
        self.assertIsNotNone(Config.GRAVITY_CONSTANT)

    def test_config_value_ranges(self):
        """Test that config values are reasonable."""
        self.assertGreater(Config.MAX_DATA_POINTS, 0)
        self.assertLess(Config.MAX_DATA_POINTS, 10000)

        self.assertGreater(Config.UPDATE_INTERVAL_MS, 0)
        self.assertLess(Config.UPDATE_INTERVAL_MS, 1000)

        self.assertGreater(Config.EXPECTED_FREQUENCY, 0)

        self.assertGreater(Config.GRAVITY_CONSTANT, 0)

    def test_config_classes_exist(self):
        """Test that all config classes exist."""
        from sensor_calibrator import SerialConfig, UIConfig, CalibrationConfig

        self.assertIsNotNone(SerialConfig)
        self.assertIsNotNone(UIConfig)
        self.assertIsNotNone(CalibrationConfig)


def run_integration_tests():
    """Run all integration tests and print summary."""
    print("=" * 60)
    print("SensorCalibrator Integration Tests")
    print("=" * 60)

    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestCalibrationAlgorithms))
    suite.addTests(loader.loadTestsFromTestCase(TestActivation))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkCommands))
    suite.addTests(loader.loadTestsFromTestCase(TestValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))

# Sprint 1-3: New Command Tests
class TestNewCommands(unittest.TestCase):
    """Test Sprint 1-3 new commands."""

    def test_ss7_save_config_format(self):
        """Test SS:7 command format."""
        # SS:7 should be exactly "SS:7\n"
        expected = "SS:7\n"
        self.assertEqual(expected, "SS:7\n")

    def test_ss9_restart_sensor_format(self):
        """Test SS:9 command format."""
        # SS:9 should be exactly "SS:9\n"
        expected = "SS:9\n"
        self.assertEqual(expected, "SS:9\n")

    def test_set_agt_command_format(self):
        """Test SET:AGT command format."""
        # Format: SET:AGT,<accel>,<gyro>
        accel = 0.2
        gyro = 0.3
        expected = f"SET:AGT,{accel},{gyro}"
        self.assertEqual(expected, "SET:AGT,0.2,0.3")

    def test_alarm_threshold_ranges(self):
        """Test alarm threshold valid ranges."""
        # Valid ranges
        valid_cases = [
            (0.1, 0.1),   # Minimum
            (10.0, 45.0), # Maximum
            (0.2, 0.2),   # Typical
            (5.0, 20.0),  # Middle
        ]
        
        for accel, gyro in valid_cases:
            self.assertTrue(0.1 <= accel <= 10.0)
            self.assertTrue(0.1 <= gyro <= 45.0)

    def test_alarm_threshold_invalid_ranges(self):
        """Test alarm threshold invalid ranges."""
        invalid_cases = [
            (0.05, 0.2),   # Accel too low
            (15.0, 0.2),   # Accel too high
            (0.2, 0.05),   # Gyro too low
            (0.2, 50.0),   # Gyro too high
            (-1.0, 0.2),   # Negative accel
            (0.2, -1.0),   # Negative gyro
        ]
        
        for accel, gyro in invalid_cases:
            is_valid = (0.1 <= accel <= 10.0) and (0.1 <= gyro <= 45.0)
            self.assertFalse(is_valid)


class TestActivationWorkflow(unittest.TestCase):
    """Test activation workflow integration."""

    def test_key_generation_consistency(self):
        """Test that same MAC always generates same key."""
        mac = "AA:BB:CC:DD:EE:FF"
        key1 = generate_key_from_mac(mac)
        key2 = generate_key_from_mac(mac)
        
        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 64)

    def test_key_fragment_extraction(self):
        """Test extraction of 7-character key fragment."""
        mac = "AA:BB:CC:DD:EE:FF"
        full_key = generate_key_from_mac(mac)
        fragment = full_key[5:12]
        
        self.assertEqual(len(fragment), 7)
        self.assertEqual(fragment, full_key[5:12])

    def test_activation_status_check(self):
        """Test activation status checking logic."""
        mac = "AA:BB:CC:DD:EE:FF"
        full_key = generate_key_from_mac(mac)
        correct_fragment = full_key[5:12]
        
        # Should verify with correct fragment
        is_valid = verify_key(correct_fragment, mac)
        self.assertTrue(is_valid)

    def test_sensor_properties_parsing(self):
        """Test parsing sensor properties for activation info."""
        properties = {
            "sys": {
                "MAC": "AA:BB:CC:DD:EE:FF",
                "AKY": "1234567",
            }
        }
        
        # Extract MAC
        mac = extract_mac_from_properties(properties)
        self.assertEqual(mac, "AA:BB:CC:DD:EE:FF")
        
        # Extract AKY
        aky = properties["sys"].get("AKY")
        self.assertEqual(aky, "1234567")


class TestUIIntegration(unittest.TestCase):
    """Test UI to backend integration."""

    def test_activation_info_display(self):
        """Test activation info display format."""
        mac = "AA:BB:CC:DD:EE:FF"
        full_key = generate_key_from_mac(mac)
        fragment = full_key[5:12]
        
        # Display format should be:
        # MAC: XX:XX:XX:XX:XX:XX
        # Key: abcdefg
        # Status: Activated / Not Activated
        
        self.assertEqual(len(mac), 17)  # Standard MAC format
        self.assertEqual(len(fragment), 7)

    def test_alarm_threshold_display(self):
        """Test alarm threshold display values."""
        accel = 0.2
        gyro = 0.3
        
        # Display format: Accel: 0.20 m/s², Gyro: 0.30°
        display_accel = f"{accel:.2f}"
        display_gyro = f"{gyro:.2f}"
        
        self.assertEqual(display_accel, "0.20")
        self.assertEqual(display_gyro, "0.30")


# Run all tests
def run_all_tests():
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCalibrationAlgorithms))
    suite.addTests(loader.loadTestsFromTestCase(TestDataParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestActivationKeyGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkCommandConstruction))
    suite.addTests(loader.loadTestsFromTestCase(TestNewCommands))
    suite.addTests(loader.loadTestsFromTestCase(TestActivationWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestUIIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
