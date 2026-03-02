"""
Unit tests for DataProcessor module.

Tests core functionality:
- Data parsing from sensor strings
- Statistics calculation (mean, std)
- Data buffer management
- Clear/reset functionality
"""

import sys
import os
import unittest
from collections import deque

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_calibrator.data_processor import DataProcessor
from sensor_calibrator.config import Config


class TestDataProcessorInit(unittest.TestCase):
    """Test DataProcessor initialization."""

    def test_default_initialization(self):
        """Test that DataProcessor initializes with correct defaults."""
        processor = DataProcessor()

        # Check data buffers are initialized
        self.assertIsInstance(processor.time_data, deque)
        self.assertEqual(processor.time_data.maxlen, Config.MAX_DATA_POINTS)

        # Check sensor data buffers
        self.assertEqual(len(processor.mpu_accel_data), 3)

        # Check statistics are initialized
        self.assertIsInstance(processor.real_time_stats, dict)
        self.assertIn("mpu_accel_mean", processor.real_time_stats)

        # Check time tracking
        self.assertIsNone(processor.data_start_time)
        self.assertEqual(processor.packet_count, 0)


class TestParseSensorData(unittest.TestCase):
    """Test sensor data parsing."""

    def setUp(self):
        self.processor = DataProcessor()

    def test_valid_data_parsing(self):
        """Test parsing valid sensor data string."""
        data_string = "1.0,2.0,3.0,0.1,0.2,0.3,1.1,2.1,3.1"

        mpu_accel, mpu_gyro, adxl_accel = self.processor.parse_sensor_data(data_string)

        self.assertIsNotNone(mpu_accel)
        self.assertEqual(mpu_accel, [1.0, 2.0, 3.0])
        self.assertEqual(mpu_gyro, [0.1, 0.2, 0.3])
        self.assertEqual(adxl_accel, [1.1, 2.1, 3.1])

    def test_invalid_data_too_few_values(self):
        """Test parsing data with too few values."""
        data_string = "1.0,2.0,3.0,0.1,0.2"  # Only 5 values

        mpu_accel, mpu_gyro, adxl_accel = self.processor.parse_sensor_data(data_string)

        self.assertIsNone(mpu_accel)
        self.assertIsNone(mpu_gyro)
        self.assertIsNone(adxl_accel)

    def test_invalid_data_non_numeric(self):
        """Test parsing data with non-numeric values."""
        data_string = "abc,def,ghi,jkl,mno,pqr,stu,vwx,yzz"

        mpu_accel, mpu_gyro, adxl_accel = self.processor.parse_sensor_data(data_string)

        # Should handle gracefully by converting invalid to 0.0
        self.assertEqual(mpu_accel, [0.0, 0.0, 0.0])

    def test_invalid_data_empty_string(self):
        """Test parsing empty string."""
        mpu_accel, mpu_gyro, adxl_accel = self.processor.parse_sensor_data("")

        self.assertIsNone(mpu_accel)

    def test_negative_values(self):
        """Test parsing negative values."""
        data_string = "-1.0,-2.0,-3.0,-0.1,-0.2,-0.3,-1.1,-2.1,-3.1"

        mpu_accel, mpu_gyro, adxl_accel = self.processor.parse_sensor_data(data_string)

        self.assertEqual(mpu_accel, [-1.0, -2.0, -3.0])


class TestCalculateStatistics(unittest.TestCase):
    """Test statistics calculation."""

    def setUp(self):
        self.processor = DataProcessor()

    def test_statistics_empty_data(self):
        """Test statistics with empty data."""
        mean, std = self.processor.calculate_statistics([])

        self.assertEqual(mean, 0.0)
        self.assertEqual(std, 0.0)

    def test_statistics_single_value(self):
        """Test statistics with single value."""
        mean, std = self.processor.calculate_statistics([5.0])

        self.assertEqual(mean, 5.0)
        self.assertEqual(std, 0.0)

    def test_statistics_multiple_values(self):
        """Test statistics with multiple values."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        mean, std = self.processor.calculate_statistics(data)

        self.assertEqual(mean, 3.0)

    def test_statistics_with_deque(self):
        """Test statistics with deque input."""
        data = deque([1.0, 2.0, 3.0, 4.0, 5.0])
        mean, std = self.processor.calculate_statistics(data)

        self.assertEqual(mean, 3.0)

    def test_statistics_with_start_index(self):
        """Test statistics with start index."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        mean, std = self.processor.calculate_statistics(data, start_idx=2)

        self.assertEqual(mean, 4.0)  # Mean of [3.0, 4.0, 5.0]


class TestProcessPacket(unittest.TestCase):
    """Test packet processing."""

    def setUp(self):
        self.processor = DataProcessor()

    def test_process_valid_packet(self):
        """Test processing a valid packet."""
        result = self.processor.process_packet("1.0,2.0,3.0,0.1,0.2,0.3,1.1,2.1,3.1")

        self.assertIsNotNone(result)
        self.assertIn("time", result)
        self.assertIn("mpu_accel", result)

    def test_process_invalid_packet(self):
        """Test processing an invalid packet."""
        result = self.processor.process_packet("invalid data")

        self.assertIsNone(result)

    def test_packet_count_increments(self):
        """Test that packet count increments correctly."""
        self.processor.process_packet("1.0,2.0,3.0,0.1,0.2,0.3,1.1,2.1,3.1")
        self.processor.process_packet("1.0,2.0,3.0,0.1,0.2,0.3,1.1,2.1,3.1")

        self.assertEqual(self.processor.packet_count, 2)


class TestClearAll(unittest.TestCase):
    """Test data clearing functionality."""

    def setUp(self):
        self.processor = DataProcessor()

    def test_clear_all_resets_data(self):
        """Test that clear_all resets all data buffers."""
        # Add some data
        self.processor.process_packet("1.0,2.0,3.0,0.1,0.2,0.3,1.1,2.1,3.1")

        # Verify data exists
        self.assertGreater(len(self.processor.time_data), 0)

        # Clear
        self.processor.clear_all()

        # Verify data is cleared
        self.assertEqual(len(self.processor.time_data), 0)

    def test_clear_all_resets_statistics(self):
        """Test that clear_all resets statistics."""
        # Add data and compute statistics
        for _ in range(20):
            self.processor.process_packet("1.0,2.0,3.0,0.1,0.2,0.3,1.1,2.1,3.1")

        # Clear
        self.processor.clear_all()

        # Verify statistics are reset
        stats = self.processor.real_time_stats
        self.assertEqual(stats["mpu_accel_mean"], [0.0, 0.0, 0.0])


class TestGetDisplayData(unittest.TestCase):
    """Test display data retrieval."""

    def setUp(self):
        self.processor = DataProcessor()

    def test_get_display_data_empty(self):
        """Test get_display_data with no data."""
        data = self.processor.get_display_data()

        self.assertIn("time", data)
        self.assertEqual(len(data["time"]), 0)

    def test_get_display_data_with_data(self):
        """Test get_display_data with data."""
        for i in range(10):
            self.processor.process_packet(
                f"{float(i)},{float(i)},{float(i)},0.1,0.2,0.3,1.1,2.1,3.1"
            )

        data = self.processor.get_display_data()

        self.assertEqual(len(data["time"]), 10)


class TestGetLatestData(unittest.TestCase):
    """Test latest data retrieval."""

    def setUp(self):
        self.processor = DataProcessor()

    def test_get_latest_data_empty(self):
        """Test get_latest_data with no data."""
        data = self.processor.get_latest_data()

        self.assertIsNone(data)

    def test_get_latest_data_with_data(self):
        """Test get_latest_data with data."""
        self.processor.process_packet("1.0,2.0,3.0,0.1,0.2,0.3,1.1,2.1,3.1")

        data = self.processor.get_latest_data()

        self.assertIsNotNone(data)
        self.assertEqual(data["mpu_accel"], [1.0, 2.0, 3.0])


class TestGetDataCount(unittest.TestCase):
    """Test data count methods."""

    def setUp(self):
        self.processor = DataProcessor()

    def test_get_data_count_empty(self):
        """Test get_data_count with no data."""
        count = self.processor.get_data_count()

        self.assertEqual(count, 0)

    def test_get_data_count_with_data(self):
        """Test get_data_count with data."""
        for i in range(5):
            self.processor.process_packet("1.0,2.0,3.0,0.1,0.2,0.3,1.1,2.1,3.1")

        count = self.processor.get_data_count()

        self.assertEqual(count, 5)

    def test_has_data_empty(self):
        """Test has_data with no data."""
        self.assertFalse(self.processor.has_data())

    def test_has_data_with_data(self):
        """Test has_data with data."""
        self.processor.process_packet("1.0,2.0,3.0,0.1,0.2,0.3,1.1,2.1,3.1")

        self.assertTrue(self.processor.has_data())


if __name__ == "__main__":
    unittest.main()
