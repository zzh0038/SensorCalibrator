"""
Unit tests for SerialManager module.

Tests core functionality:
- Serial port open/close
- Connection management
- Callback handling
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import queue
import threading
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_calibrator.serial_manager import SerialManager


def create_mock_callbacks():
    """Create mock callbacks for testing."""
    return {
        "log_message": Mock(),
        "get_data_queue": Mock(return_value=queue.Queue()),
        "update_connection_state": Mock(),
    }


class TestSerialManagerInit(unittest.TestCase):
    """Test SerialManager initialization."""

    def test_initialization_with_callbacks(self):
        """Test that SerialManager initializes with callbacks."""
        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        # Check internal state
        self.assertIsNone(manager._ser)
        self.assertIsNone(manager._serial_thread)
        self.assertFalse(manager._is_connected)
        self.assertFalse(manager._is_reading)

    def test_is_connected_property_closed(self):
        """Test is_connected property when closed."""
        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        self.assertFalse(manager.is_connected)


class TestConnect(unittest.TestCase):
    """Test connection functionality."""

    @patch("serial.Serial")
    def test_connect_success(self, mock_serial):
        """Test successful connection."""
        mock_serial_instance = Mock()
        mock_serial_instance.is_open = True
        mock_serial.return_value = mock_serial_instance

        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        result = manager.connect("COM3", 115200)

        self.assertTrue(result)
        self.assertTrue(manager.is_connected)

    @patch("serial.Serial")
    def test_connect_invalid_port(self, mock_serial):
        """Test connection with invalid port."""
        mock_serial.side_effect = Exception("Port not found")

        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        result = manager.connect("INVALID_PORT", 115200)

        self.assertFalse(result)
        self.assertFalse(manager.is_connected)

    @patch("serial.Serial")
    def test_connect_already_connected(self, mock_serial):
        """Test connecting when already connected."""
        mock_serial_instance = Mock()
        mock_serial_instance.is_open = True
        mock_serial.return_value = mock_serial_instance

        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        # First connection
        manager.connect("COM3", 115200)
        self.assertTrue(manager.is_connected)

        # Second connection should disconnect first
        manager.connect("COM4", 115200)

        # Should have tried to close first
        mock_serial_instance.close.assert_called()


class TestDisconnect(unittest.TestCase):
    """Test disconnection functionality."""

    @patch("serial.Serial")
    def test_disconnect_closes_port(self, mock_serial):
        """Test disconnect closes serial port."""
        mock_serial_instance = Mock()
        mock_serial_instance.is_open = True
        mock_serial.return_value = mock_serial_instance

        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        # Connect first
        manager.connect("COM3", 115200)
        self.assertTrue(manager.is_connected)

        # Disconnect
        manager.disconnect()

        self.assertFalse(manager.is_connected)
        mock_serial_instance.close.assert_called_once()

    @patch("serial.Serial")
    def test_disconnect_callback_called(self, mock_serial):
        """Test that disconnect callback is called."""
        mock_serial_instance = Mock()
        mock_serial_instance.is_open = True
        mock_serial.return_value = mock_serial_instance

        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        manager.connect("COM3", 115200)
        manager.disconnect()

        callbacks["update_connection_state"].assert_called_with(False)


class TestLogMessage(unittest.TestCase):
    """Test logging functionality."""

    @patch("serial.Serial")
    def test_log_message_calls_callback(self, mock_serial):
        """Test that log_message calls the callback."""
        mock_serial_instance = Mock()
        mock_serial_instance.is_open = True
        mock_serial.return_value = mock_serial_instance

        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        manager._log_message("Test message")

        callbacks["log_message"].assert_called_once_with("Test message")


class TestPacketsReceived(unittest.TestCase):
    """Test packet counting."""

    def test_initial_packet_count(self):
        """Test initial packet count is zero."""
        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        self.assertEqual(manager.packets_received, 0)


class TestSerialPortProperty(unittest.TestCase):
    """Test serial_port property."""

    @patch("serial.Serial")
    def test_serial_port_returns_none_when_not_connected(self, mock_serial):
        """Test serial_port returns None when not connected."""
        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        self.assertIsNone(manager.serial_port)

    @patch("serial.Serial")
    def test_serial_port_returns_port_when_connected(self, mock_serial):
        """Test serial_port returns the port when connected."""
        mock_serial_instance = Mock()
        mock_serial_instance.is_open = True
        mock_serial.return_value = mock_serial_instance

        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        manager.connect("COM3", 115200)

        self.assertEqual(manager.serial_port, mock_serial_instance)


class TestIsReadingProperty(unittest.TestCase):
    """Test is_reading property."""

    def test_initial_is_reading_false(self):
        """Test is_reading is initially False."""
        callbacks = create_mock_callbacks()
        manager = SerialManager(callbacks)

        self.assertFalse(manager.is_reading)


if __name__ == "__main__":
    unittest.main()
