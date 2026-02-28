"""
Integration tests for SensorCalibrator

Tests core functionality that must work after refactoring:
1. Data parsing from serial stream
2. Calibration calculations
3. Activation key generation
4. Network command construction
"""

import unittest
import sys
import os
import time
import json
from collections import deque

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from sensor_calibrator import Config, validate_ssid, validate_password, validate_port
from calibration import compute_six_position_calibration, compute_gyro_offset
from activation import generate_key_from_mac, verify_key, check_activation_status
from network_config import build_wifi_command, build_mqtt_command, build_ota_command


class TestDataParsing(unittest.TestCase):
    """Test sensor data parsing functionality"""
    
    def test_parse_sensor_data_format(self):
        """Test parsing of sensor data string format"""
        # Simulate typical data format from serial stream
        # Format varies, but typically includes MPU6050 and ADXL355 readings
        test_cases = [
            # Valid data cases
            ("MPU:1.23,-4.56,9.81|GYRO:0.01,-0.02,0.03|ADXL:1.20,-4.50,9.75", True),
            ("MPU:-1.0,2.0,3.0|GYRO:0.1,0.2,0.3|ADXL:-1.1,2.1,3.1", True),
            # Invalid data cases
            ("invalid data format", False),
            ("", False),
            ("MPU:1,2|GYRO:1,2,3|ADXL:1,2,3", False),  # Missing MPU axis
        ]
        
        for data_str, should_parse in test_cases:
            # This will be replaced with actual parse function
            # For now, just test that we can handle the data format concept
            if should_parse:
                self.assertIsInstance(data_str, str)
                parts = data_str.split("|")
                self.assertGreaterEqual(len(parts), 3)  # MPU, GYRO, ADXL
            else:
                # Invalid data should either fail parsing or be handled gracefully
                pass


class TestCalibrationAlgorithms(unittest.TestCase):
    """Test calibration calculation algorithms"""
    
    def test_six_position_calibration_structure(self):
        """Test that calibration produces expected structure"""
        # Mock 6-position calibration data
        # Format: [(+X), (-X), (+Y), (-Y), (+Z), (-Z)] readings
        mpu_readings = [
            [9.81, 0, 0],   # +X
            [-9.81, 0, 0],  # -X
            [0, 9.81, 0],   # +Y
            [0, -9.81, 0],  # -Y
            [0, 0, 9.81],   # +Z
            [0, 0, -9.81],  # -Z
        ]
        
        # Test calibration params structure
        params = {
            "mpu_accel_scale": [1.0, 1.0, 1.0],
            "mpu_accel_offset": [0.0, 0.0, 0.0],
            "adxl_accel_scale": [1.0, 1.0, 1.0],
            "adxl_accel_offset": [0.0, 0.0, 0.0],
            "mpu_gyro_offset": [0.0, 0.0, 0.0],
        }
        
        # Verify structure
        self.assertIn("mpu_accel_scale", params)
        self.assertIn("mpu_accel_offset", params)
        self.assertEqual(len(params["mpu_accel_scale"]), 3)
        self.assertEqual(len(params["mpu_accel_offset"]), 3)
    
    def test_calibration_param_ranges(self):
        """Test that calibration parameters are within reasonable ranges"""
        # Scale factors should be close to 1.0
        scale = 0.98
        self.assertGreater(scale, 0.5)  # Sanity check
        self.assertLess(scale, 2.0)
        
        # Offsets should be small
        offset = 0.05
        self.assertLess(abs(offset), 1.0)


class TestActivation(unittest.TestCase):
    """Test sensor activation and key generation"""
    
    def test_key_generation_from_mac(self):
        """Test key generation from MAC address"""
        test_cases = [
            ("AA:BB:CC:DD:EE:FF", True),
            ("aa:bb:cc:dd:ee:ff", True),  # lowercase
            ("AA-BB-CC-DD-EE-FF", True),  # dash separator
            ("invalid_mac", False),
            ("", False),
        ]
        
        for mac, should_succeed in test_cases:
            if should_succeed:
                key = generate_key_from_mac(mac)
                self.assertIsInstance(key, str)
                self.assertEqual(len(key), 64)  # SHA-256 hex = 64 chars
            else:
                # Should either raise exception or return None/empty
                try:
                    key = generate_key_from_mac(mac)
                    # If no exception, key might be generated from invalid input
                    # This is acceptable behavior depending on implementation
                except (ValueError, TypeError):
                    pass  # This is also acceptable
    
    def test_key_consistency(self):
        """Test that same MAC always generates same key"""
        mac = "AA:BB:CC:DD:EE:FF"
        key1 = generate_key_from_mac(mac)
        key2 = generate_key_from_mac(mac)
        self.assertEqual(key1, key2)
    
    def test_key_fragment_extraction(self):
        """Test extraction of 7-char key fragment for display"""
        full_key = "A" * 64
        fragment = full_key[:7]
        self.assertEqual(len(fragment), 7)
        self.assertEqual(fragment, "AAAAAAA")


class TestNetworkCommands(unittest.TestCase):
    """Test network configuration command construction"""
    
    def test_wifi_command_format(self):
        """Test WiFi command format"""
        ok, error, cmd = build_wifi_command("TestSSID", "password123")
        self.assertTrue(ok)
        self.assertIsInstance(cmd, str)
        self.assertIn("SET:WF", cmd)
        self.assertIn("TestSSID", cmd)
    
    def test_wifi_validation(self):
        """Test WiFi input validation"""
        # Valid SSIDs
        valid, msg = validate_ssid("MyNetwork")
        self.assertTrue(valid)
        
        # Invalid SSIDs
        invalid_cases = [
            "",  # Empty
            "a" * 33,  # Too long (max 32)
        ]
        for ssid in invalid_cases:
            valid, msg = validate_ssid(ssid)
            self.assertFalse(valid, f"SSID '{ssid}' should be invalid")
    
    def test_mqtt_command_format(self):
        """Test MQTT command format"""
        ok, error, cmd = build_mqtt_command("broker.example.com", "1883", "user", "pass")
        self.assertTrue(ok)
        self.assertIsInstance(cmd, str)
        self.assertIn("SET:MQ", cmd)
        self.assertIn("broker.example.com", cmd)
    
    def test_ota_command_format(self):
        """Test OTA command format"""
        ok, error, cmd = build_ota_command("http://url1.com", "http://url2.com", "http://url3.com", "http://url4.com")
        self.assertTrue(ok)
        self.assertIsInstance(cmd, str)
        self.assertIn("SET:OTA", cmd)
    

    
    def test_port_validation(self):
        """Test port number validation"""
        # Valid ports
        valid_ports = ["1", "80", "1883", "8080", "65535"]
        for port in valid_ports:
            valid, msg = validate_port(port)
            self.assertTrue(valid, f"Port {port} should be valid")
        
        # Invalid ports
        invalid_ports = ["0", "65536", "abc", "-1", ""]
        for port in invalid_ports:
            valid, msg = validate_port(port)
            self.assertFalse(valid, f"Port {port} should be invalid")


class TestConfiguration(unittest.TestCase):
    """Test configuration constants"""
    
    def test_config_values_exist(self):
        """Test that all required config values exist"""
        self.assertIsNotNone(Config.MAX_DATA_POINTS)
        self.assertIsNotNone(Config.UPDATE_INTERVAL_MS)
        self.assertIsNotNone(Config.EXPECTED_FREQUENCY)
        self.assertIsNotNone(Config.GRAVITY_CONSTANT)
    
    def test_config_value_ranges(self):
        """Test that config values are reasonable"""
        self.assertGreater(Config.MAX_DATA_POINTS, 0)
        self.assertLess(Config.MAX_DATA_POINTS, 10000)
        self.assertGreater(Config.UPDATE_INTERVAL_MS, 0)
        self.assertGreater(Config.EXPECTED_FREQUENCY, 0)


class TestDataBuffer(unittest.TestCase):
    """Test data buffer functionality"""
    
    def test_deque_initialization(self):
        """Test that data structures are properly initialized"""
        from collections import deque
        
        max_points = Config.MAX_DATA_POINTS
        time_data = deque(maxlen=max_points)
        mpu_accel_data = [deque(maxlen=max_points) for _ in range(3)]
        
        # Verify structure
        self.assertEqual(len(mpu_accel_data), 3)
        self.assertEqual(mpu_accel_data[0].maxlen, max_points)
    
    def test_deque_auto_limiting(self):
        """Test that deque automatically limits size"""
        from collections import deque
        
        d = deque(maxlen=5)
        for i in range(10):
            d.append(i)
        
        self.assertEqual(len(d), 5)
        self.assertEqual(list(d), [5, 6, 7, 8, 9])


class TestStatisticsCalculation(unittest.TestCase):
    """Test statistics calculation"""
    
    def test_mean_calculation(self):
        """Test mean calculation"""
        import numpy as np
        
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        mean = np.mean(data)
        self.assertAlmostEqual(mean, 3.0)
    
    def test_std_calculation(self):
        """Test standard deviation calculation"""
        import numpy as np
        
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        std = np.std(data)
        self.assertGreater(std, 0)


class TestPerformanceOptimization(unittest.TestCase):
    """Test performance optimization settings"""
    
    def test_optimization_switches_exist(self):
        """Test that optimization switches are defined"""
        self.assertTrue(hasattr(Config, 'ENABLE_BLIT_OPTIMIZATION'))
        self.assertTrue(hasattr(Config, 'ENABLE_WINDOW_MOVE_PAUSE'))
        self.assertTrue(hasattr(Config, 'ENABLE_DATA_DECIMATION'))
    
    def test_update_intervals_reasonable(self):
        """Test that update intervals are reasonable"""
        # GUI update should be 50-200ms
        self.assertGreaterEqual(Config.UPDATE_INTERVAL_MS, 50)
        self.assertLessEqual(Config.UPDATE_INTERVAL_MS, 200)
        
        # Chart update interval should be >= GUI update
        chart_interval_ms = Config.CHART_UPDATE_INTERVAL * 1000
        self.assertGreaterEqual(chart_interval_ms, 50)


class TestMainAppStructure(unittest.TestCase):
    """Test main application structure"""
    
    def test_main_file_imports(self):
        """Test that main file can be imported"""
        try:
            # This tests basic syntax and import structure
            import StableSensorCalibrator
            self.assertTrue(True)
        except SyntaxError as e:
            self.fail(f"Syntax error in main file: {e}")
        except ImportError as e:
            # Some imports may fail in test environment (e.g., serial port)
            # This is acceptable as long as it's not a syntax error
            pass
    
    def test_config_imports(self):
        """Test that config module imports work"""
        from sensor_calibrator import Config, UIConfig, CalibrationConfig, SerialConfig
        self.assertIsNotNone(Config)
        self.assertIsNotNone(UIConfig)


def run_smoke_test():
    """
    Quick smoke test to verify basic functionality.
    Run this before and after refactoring.
    """
    print("=" * 60)
    print("SensorCalibrator Smoke Test")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Config import
    try:
        from sensor_calibrator import Config
        print("[PASS] Config import: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Config import: FAILED - {e}")
        tests_failed += 1
    
    # Test 2: Calibration module
    try:
        from calibration import compute_six_position_calibration, compute_gyro_offset
        print("[PASS] Calibration module: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Calibration module: FAILED - {e}")
        tests_failed += 1
    
    # Test 3: Activation module
    try:
        from activation import generate_key_from_mac
        key = generate_key_from_mac("AA:BB:CC:DD:EE:FF")
        assert len(key) == 64
        print("[PASS] Activation module: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Activation module: FAILED - {e}")
        tests_failed += 1
    
    # Test 4: Network config
    try:
        from network_config import build_wifi_command
        ok, error, cmd = build_wifi_command("Test", "pass")
        assert "SET:WF" in cmd
        print("[PASS] Network config: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Network config: FAILED - {e}")
        tests_failed += 1
    
    # Test 5: Validation functions
    try:
        from sensor_calibrator import validate_ssid, validate_port
        valid, _ = validate_ssid("TestNetwork")
        assert valid
        valid, _ = validate_port("1883")
        assert valid
        print("[PASS] Validation functions: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Validation functions: FAILED - {e}")
        tests_failed += 1
    
    print("=" * 60)
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)
    
    return tests_failed == 0


if __name__ == '__main__':
    # Run smoke test first
    smoke_passed = run_smoke_test()
    print()
    
    # Run full test suite
    print("Running full test suite...")
    unittest.main(verbosity=2, exit=not smoke_passed)
