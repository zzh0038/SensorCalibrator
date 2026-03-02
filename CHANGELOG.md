# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-02

### Added

#### Core Features
- **Six-Position Calibration**: Complete calibration algorithm for MPU6050 and ADXL355 accelerometers
- **Real-time Data Visualization**: Live chart display using matplotlib
- **Sensor Activation**: MAC-based key generation and verification system
- **Network Configuration**: WiFi, MQTT, and OTA firmware update support
- **Dual Coordinate Modes**: Local and global coordinate system support

#### Architecture
- **Modular Package Structure**: `sensor_calibrator/` package with separated concerns
- **Configuration Management**: Centralized config in `config.py`
- **Workflow Modules**: CalibrationWorkflow and ActivationWorkflow for complex operations
- **Data Processing**: Dedicated DataProcessor class for sensor data parsing and statistics
- **Serial Communication**: Robust SerialManager with thread-safe operations

#### Testing
- **Unit Tests**: Test coverage for DataProcessor and SerialManager
- **Integration Tests**: Calibration algorithms, activation logic, network commands
- **Test Infrastructure**: pytest configuration with 80+ test cases

#### Documentation
- **README.md**: Complete project documentation with installation and usage guide
- **Requirements Management**: requirements.txt and pyproject.toml for dependency management
- **Test Configuration**: pytest.ini for standardized test execution

### Known Issues

- Main application file (StableSensorCalibrator.py) is larger than recommended (>1500 lines)
- Some type annotations are incomplete
- No CI/CD pipeline configured yet

---

## [Future Releases]

### Planned Features

#### High Priority
- [ ] Refactor main application file into smaller modules
- [ ] Complete type annotations across all modules
- [ ] Add mypy/pyright type checking to CI

#### Medium Priority
- [ ] Add GitHub Actions CI pipeline
- [ ] Set up pre-commit hooks (black, flake8)
- [ ] Expand test coverage to 80%+
- [ ] Add logging module for better diagnostics

#### Low Priority
- [ ] Dark mode theme support
- [ ] Export calibration data to CSV
- [ ] Multi-language support (English, Chinese)
- [ ] Auto-update functionality

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 1.0.0 | 2026-03-02 | Initial release |

---

## Migration Notes

### From v0.x to v1.0.0

This is the first official release. If upgrading from a pre-1.0 version:

1. **New Dependencies**: Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Module Structure**: Core functionality moved to `sensor_calibrator/` package:
   ```python
   # Old import
   from serial_manager import SerialManager
   
   # New import
   from sensor_calibrator import SerialManager
   ```

3. **Configuration**: All constants now in `sensor_calibrator.config`:
   ```python
   from sensor_calibrator import Config, UIConfig, SerialConfig
   ```

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Code Style**: Follow PEP 8 and use type hints
2. **Testing**: Add tests for new features (target 80% coverage)
3. **Documentation**: Update README.md and this CHANGELOG for significant changes
4. **Commits**: Use clear, descriptive commit messages

---

## Support

For issues and questions:
- Check the README.md troubleshooting section
- Review test cases for expected behavior
- Examine log output for error details

---

*This CHANGELOG was generated as part of the v1.0.0 release improvement sprint.*
