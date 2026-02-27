# Plan: Split StableSensorCalibrator.py Main File

**Generated**: 2026-02-27  
**Estimated Complexity**: Medium-High  
**Timeline**: 4-6 weeks (gradual)  
**Constraint**: Maintain full backward compatibility

---

## Overview

Split the ~3,500 line `StableSensorCalibrator.py` monolith into focused modules while preserving the existing public API. The main class interface remains unchanged; only internal organization improves.

**Approach**: 
- **Extract-and-delegate**: Move code to new modules, keep facade in main file
- **Phase-by-phase**: One functional area at a time
- **Feature flags**: Allow rollback per component
- **Zero breaking changes**: All existing code continues to work

---

## Prerequisites

- [ ] All P0 bugs fixed (duplicate init, URL checks, `if 1:`)
- [ ] Basic test script to verify functionality
- [ ] Git branch: `refactor/modularization`
- [ ] Code review process in place

---

## Sprint 1: Foundation & Configuration
**Goal**: Extract constants and configuration into a dedicated module
**Duration**: Week 1
**Demo/Validation**:
- [ ] Import `Config` from new location works
- [ ] All constants accessible via both old and new paths
- [ ] No behavioral changes in application

### Task 1.1: Create Core Configuration Module
- **Location**: `sensor_calibrator/config.py` (expand existing)
- **Description**: 
  - Move all hardcoded constants from main file
  - Organize into logical classes: `SerialConfig`, `UIConfig`, `CalibrationConfig`, `TimingConfig`
  - Keep deprecated aliases for backward compatibility
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] All magic numbers have named constants
  - [ ] Type hints on all config values
  - [ ] Docstrings explain each config purpose
- **Validation**:
  - [ ] `python -c "from sensor_calibrator.config import Config; print(Config.MAX_DATA_POINTS)"`
  - [ ] Application starts without errors
  - [ ] Config values match original hardcoded values

### Task 1.2: Create Constants Compatibility Layer
- **Location**: `StableSensorCalibrator.py` (top of file)
- **Description**:
  - Import all constants from new config module
  - Add deprecation warnings for direct constant access (optional)
  - Ensure `self.calibration_file` and similar use config
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [ ] No hardcoded numbers remain in main file (except 0, 1, -1)
  - [ ] All timeouts, sizes, intervals use `Config.*`
- **Validation**:
  - [ ] Grep for numbers in main file returns minimal results
  - [ ] Application behavior unchanged

### Task 1.3: Extract Data Buffer Management
- **Location**: `sensor_calibrator/data_buffer.py`
- **Description**:
  - Create `SensorDataBuffer` class to manage:
    - `time_data`, `mpu_accel_data`, `mpu_gyro_data`, `adxl_accel_data`, `gravity_mag_data`
    - Data appending, limiting, slicing operations
    - Statistics calculations
  - Thread-safe operations with locks
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [ ] All data list operations moved to class
  - [ ] Buffer size limiting centralized
  - [ ] Statistics calculation methods included
- **Validation**:
  - [ ] Unit test: buffer add/limit/clear cycle
  - [ ] Thread safety test with concurrent adds

---

## Sprint 2: Serial Communication Layer
**Goal**: Migrate all serial I/O to use `SerialManager` consistently
**Duration**: Week 2
**Demo/Validation**:
- [ ] All serial operations go through `SerialManager`
- [ ] Direct `self.ser` access minimized
- [ ] Connection/disconnection works identically

### Task 2.1: Audit Current Serial Usage
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - Document all direct `self.ser` accesses
  - Categorize: read, write, config, status check
  - Identify patterns for abstraction
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] List of all `self.ser` usages with line numbers
  - [ ] Classification of each usage type
- **Validation**:
  - [ ] `grep -n "self\.ser" StableSensorCalibrator.py > serial_usages.txt`

### Task 2.2: Enhance SerialManager for Full Compatibility
- **Location**: `serial_manager.py`
- **Description**:
  - Add methods needed by main app:
    - `send_command(cmd_id, description, log_success, silent)`
    - `read_properties(timeout)` with JSON parsing
    - `reset_and_wait(delay)`
  - Add `request_response` pattern for command/response flows
  - Add event callbacks: `on_connect`, `on_disconnect`, `on_error`
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - [ ] All serial patterns from main file supported
  - [ ] Async/callback-based response handling
  - [ ] Error propagation to UI layer
- **Validation**:
  - [ ] Mock serial tests for all new methods
  - [ ] Integration test with real device (if available)

### Task 2.3: Migrate to SerialManager (Partial)
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - Replace direct writes with `serial_manager.send_line()`
  - Replace read loops with listener pattern
  - Keep `self.ser` as property delegating to `serial_manager`
  - **Backward compat**: `self.ser` returns wrapper or `serial_manager._ser`
- **Dependencies**: Task 2.2
- **Acceptance Criteria**:
  - [ ] All `ser.write()` calls use manager
  - [ ] Reading uses listener callbacks
  - [ ] Connection state properly synchronized
- **Validation**:
  - [ ] Connect/disconnect cycle works
  - [ ] Data streaming works
  - [ ] Property reading works

---

## Sprint 3: UI Panel Extraction
**Goal**: Extract each UI panel into self-contained classes
**Duration**: Week 3
**Demo/Validation**:
- [ ] Each panel is a separate class file
- [ ] Main file `setup_left_panel` delegates to panel constructors
- [ ] All panels render identically

### Task 3.1: Create Base Panel Class
- **Location**: `sensor_calibrator/gui/base_panel.py`
- **Description**:
  - Abstract base: `BasePanel`
  - Common functionality: title, styling, enable/disable
  - Interface: `create(parent)`, `enable()`, `disable()`, `set_enabled(bool)`
  - Reference to main controller for callbacks
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Base class with common panel methods
  - [ ] Consistent styling across panels
  - [ ] Event binding pattern defined
- **Validation**:
  - [ ] Unit test: panel lifecycle (create/enable/disable)

### Task 3.2: Extract SerialSettingsPanel
- **Location**: `sensor_calibrator/gui/serial_panel.py`
- **Description**:
  - Port selection, baud rate, connect/disconnect button
  - Port refresh functionality
  - Connection status display
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - [ ] All serial UI moved from main file
  - [ ] Callbacks to main controller for connect/disconnect
  - [ ] State synced with SerialManager
- **Validation**:
  - [ ] Port list populates correctly
  - [ ] Connect/disconnect button toggles properly

### Task 3.3: Extract DataStreamPanel
- **Location**: `sensor_calibrator/gui/data_stream_panel.py`
- **Description**:
  - Start/Stop buttons for RawData and CalibData
  - Frequency display label
  - Stream state management
- **Dependencies**: Task 3.1, Task 2.3
- **Acceptance Criteria**:
  - [ ] Both stream buttons work
  - [ ] Frequency display updates
  - [ ] Button states sync with stream state
- **Validation**:
  - [ ] Toggle stream on/off
  - [ ] Verify frequency counter increments

### Task 3.4: Extract CalibrationPanel
- **Location**: `sensor_calibrator/gui/calibration_panel.py`
- **Description**:
  - Start Calib, Capture Position buttons
  - Position display label
  - Progress through 6 positions
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - [ ] Calibration workflow unchanged
  - [ ] Position display updates correctly
  - [ ] Button enable/disable logic preserved
- **Validation**:
  - [ ] Start calibration → position 1 shown
  - [ ] Capture button enables/disables properly

### Task 3.5: Extract NetworkConfigPanel
- **Location**: `sensor_calibrator/gui/network_panel.py`
- **Description**:
  - WiFi settings (SSID, password)
  - MQTT settings (broker, user, pass, port)
  - OTA settings (4 URLs)
  - Set/Read buttons for each
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - [ ] All input fields present
  - [ ] Buttons trigger correct commands
  - [ ] Values populate from sensor properties
- **Validation**:
  - [ ] Enter WiFi settings → Set button sends command
  - [ ] Read populates fields from device

### Task 3.6: Extract ActivationPanel
- **Location**: `sensor_calibrator/gui/activation_panel.py`
- **Description**:
  - MAC address display
  - Activation status
  - Activate/Verify buttons
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - [ ] MAC display updates on connect
  - [ ] Status color changes (red/green)
  - [ ] Buttons enable based on state
- **Validation**:
  - [ ] Connect device → MAC appears
  - [ ] Activation workflow unchanged

### Task 3.7: Extract CommandsPanel
- **Location**: `sensor_calibrator/gui/commands_panel.py`
- **Description**:
  - Send Commands, Save Params, Read Props, Resend buttons
  - Coordinate Mode buttons (Local/Global)
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - [ ] All command buttons present
  - [ ] Coordinate mode buttons work
  - [ ] Command text area updates
- **Validation**:
  - [ ] Click Send Commands → commands sent
  - [ ] Coordinate mode buttons send SS:2/SS:3

---

## Sprint 4: Plotting & Visualization
**Goal**: Extract chart/plot management
**Duration**: Week 4
**Demo/Validation**:
- [ ] Charts render identically
- [ ] Update performance maintained
- [ ] Statistics overlay works

### Task 4.1: Create ChartManager Class
- **Location**: `sensor_calibrator/gui/chart_manager.py`
- **Description**:
  - Encapsulate matplotlib setup and updates
  - Manage 4 subplots: MPU Accel, ADXL Accel, MPU Gyro, Gravity
  - Handle data line updates
  - Statistics text overlays
  - Y-axis auto-scaling
- **Dependencies**: Task 1.3 (for data access)
- **Acceptance Criteria**:
  - [ ] All plotting code moved from main file
  - [ ] Update throttling preserved (20 FPS)
  - [ ] Statistics text updates work
- **Validation**:
  - [ ] Charts display with test data
  - [ ] Update frequency at ~20 FPS

### Task 4.2: Integrate ChartManager
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - Replace `setup_plots()` with `ChartManager` instantiation
  - Replace `update_charts()` with manager call
  - Delegate `adjust_y_limits()` to manager
- **Dependencies**: Task 4.1
- **Acceptance Criteria**:
  - [ ] No matplotlib code in main file except import
  - [ ] Charts update during data streaming
- **Validation**:
  - [ ] Full data streaming cycle with charts

---

## Sprint 5: Calibration Workflow
**Goal**: Extract calibration logic into testable module
**Duration**: Week 5
**Demo/Validation**:
- [ ] 6-position calibration works identically
- [ ] Can run calibration unit tests
- [ ] Command generation unchanged

### Task 5.1: Create CalibrationWorkflow Class
- **Location**: `sensor_calibrator/calibration_workflow.py`
- **Description**:
  - State machine for calibration process
  - Position management (current, total, names)
  - Sample collection coordination
  - Progress callbacks
  - Integration with existing `calibration.py` math functions
- **Dependencies**: `calibration.py` (exists)
- **Acceptance Criteria**:
  - [ ] State: IDLE → CALIBRATING → CAPTURING → COMPLETE
  - [ ] Position transitions: 0 → 1 → ... → 6
  - [ ] Sample buffer management per position
- **Validation**:
  - [ ] Unit test: full calibration state cycle
  - [ ] Mock data produces expected commands

### Task 5.2: Create CalibrationCommandBuilder
- **Location**: `sensor_calibrator/calibration/command_builder.py`
- **Description**:
  - Generate SET:RACKS, SET:RACOF, etc. commands
  - Format floating point values consistently
  - Command batching
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Commands match current format exactly
  - [ ] Handles all 5 command types
- **Validation**:
  - [ ] Test with known calibration data
  - [ ] Verify command string format

### Task 5.3: Integrate Calibration Workflow
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - Replace `start_calibration()`, `capture_position()` with workflow calls
  - Replace `finish_calibration()` with workflow completion handler
  - Keep UI coordination in main file
- **Dependencies**: Task 5.1, Task 5.2
- **Acceptance Criteria**:
  - [ ] Calibration workflow delegates to class
  - [ ] UI updates still work (progress, buttons)
- **Validation**:
  - [ ] Complete 6-position calibration
  - [ ] Verify generated commands

---

## Sprint 6: Main File Cleanup & Final Integration
**Goal**: Reduce main file to coordinator/facade only
**Duration**: Week 6
**Demo/Validation**:
- [ ] Main file < 500 lines
- [ ] All functionality preserved
- [ ] Clean imports and structure

### Task 6.1: Create MainController Class (Facade)
- **Location**: `sensor_calibrator/main_controller.py`
- **Description**:
  - High-level orchestration
  - Delegates to: SerialManager, ChartManager, CalibrationWorkflow, Panels
  - Event handling coordination
  - State management (connected, streaming, calibrating)
- **Dependencies**: All previous sprints
- **Acceptance Criteria**:
  - [ ] All business logic moved from original file
  - [ ] Clear delegation pattern
  - [ ] Event callbacks wired correctly
- **Validation**:
  - [ ] All integration tests pass

### Task 6.2: Reduce StableSensorCalibrator.py to Facade
- **Location**: `StableSensorCalibrator.py`
- **Description**:
  - Keep class name and public methods for backward compatibility
  - All implementations delegate to `MainController`
  - Import and instantiate controller in `__init__`
  - Add deprecation warnings if desired
- **Dependencies**: Task 6.1
- **Acceptance Criteria**:
  - [ ] File under 500 lines
  - [ ] All public methods present
  - [ ] Full backward compatibility
- **Validation**:
  - [ ] Existing scripts using the class still work
  - [ ] All features functional

### Task 6.3: Update Project Structure
- **Location**: Project root
- **Description**:
  - Create `__init__.py` files for all packages
  - Update imports to be clean
  - Add `__all__` exports
  - Create proper package structure
- **Dependencies**: Task 6.2
- **Acceptance Criteria**:
  - [ ] `from sensor_calibrator import StableSensorCalibrator` works
  - [ ] All submodules importable
  - [ ] Clean public API
- **Validation**:
  - [ ] Import test: all modules load without errors

---

## Testing Strategy

### Per-Sprint Testing
Each sprint must include:
1. **Unit tests** for new modules
2. **Integration test** with existing code
3. **Manual smoke test** with real device (if available)

### Final Validation Checklist
- [ ] Connect to device → read properties → display MAC
- [ ] Start data stream → charts update → frequency shows
- [ ] Start calibration → capture 6 positions → generate commands
- [ ] Send commands → verify on device
- [ ] WiFi/MQTT config → set and read back
- [ ] Activation → verify key → activate
- [ ] Disconnect → reconnect → all still works

### Regression Tests
Create a `test_regression.py` that exercises:
1. Full connection lifecycle
2. Data streaming (100 packets)
3. Calibration workflow (mock data)
4. All button clicks

---

## Potential Risks & Gotchas

### Risk 1: tkinter Thread Safety
**Issue**: tkinter is not thread-safe; current code uses `root.after()` for thread marshalling.
**Mitigation**: Keep all UI update logic in main file or use `queue` for thread communication.

### Risk 2: Import Circular Dependencies
**Issue**: Main file and new modules may circularly depend.
**Mitigation**: 
- Use dependency injection (pass controller reference)
- Import at function level where needed
- Clear layering: GUI → Core → Utils

### Risk 3: Event Callback Loss
**Issue**: Button callbacks may not wire correctly after extraction.
**Mitigation**: 
- Explicit callback registration pattern
- Integration test for each panel
- Keep lambda factories in main file initially

### Risk 4: Serial Timing Sensitivity
**Issue**: Device may have timing requirements for commands.
**Mitigation**: 
- Document all delays/timeouts before changing
- Keep timing constants configurable
- Test with real hardware frequently

### Risk 5: State Synchronization
**Issue**: Multiple copies of state (connected, streaming, etc.) may diverge.
**Mitigation**:
- Single source of truth in MainController
- State change events/notifications
- Property pattern for state accessors

---

## Rollback Plan

### Per-Sprint Rollback
Each sprint creates a working state. If issues found:
1. Revert commits for that sprint only
2. Previous sprints remain functional
3. Fix issues in isolation
4. Re-apply sprint

### Emergency Full Rollback
If critical issue in production:
```bash
git checkout main  # or previous stable tag
# Deploy stable version
```

### Feature Flags (Optional)
For gradual migration, add feature flags:
```python
USE_NEW_SERIAL_MANAGER = os.getenv('USE_NEW_SERIAL', 'false').lower() == 'true'

if USE_NEW_SERIAL_MANAGER:
    self.serial = SerialManager()
else:
    self.ser = None  # old way
```

---

## Final Project Structure

```
SensorCalibrator/
├── StableSensorCalibrator.py      # Facade (backward compat)
├── sensor_calibrator/
│   ├── __init__.py
│   ├── config.py                   # All constants
│   ├── activation.py               # (exists)
│   ├── calibration.py              # (exists)
│   ├── data_pipeline.py            # (exists)
│   ├── network_config.py           # (exists)
│   ├── serial_manager.py           # (enhanced)
│   ├── data_buffer.py              # NEW
│   ├── calibration_workflow.py     # NEW
│   └── gui/
│       ├── __init__.py
│       ├── base_panel.py           # NEW
│       ├── chart_manager.py        # NEW
│       ├── serial_panel.py         # NEW
│       ├── data_stream_panel.py    # NEW
│       ├── calibration_panel.py    # NEW
│       ├── network_panel.py        # NEW
│       ├── activation_panel.py     # NEW
│       └── commands_panel.py       # NEW
├── tests/
│   ├── test_data_buffer.py
│   ├── test_calibration_workflow.py
│   ├── test_panels.py
│   └── test_regression.py
└── main.py                         # Optional entry point
```

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Main file lines | ~3,500 | < 500 |
| Average method length | 30+ lines | < 20 lines |
| Cyclomatic complexity | High | Medium |
| Test coverage | 0% | > 60% |
| Import time | Baseline | Similar |
| Runtime performance | Baseline | Similar or better |

---

*Plan created based on gradual refactoring approach, stable codebase status, and backward compatibility requirements.*
