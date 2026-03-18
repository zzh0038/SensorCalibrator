# Button Fix Work Plan

## TL;DR

> **Quick Summary**: Fix two critical issues causing buttons to not work: (1) missing callback registration for `read_properties`, (2) CameraManager not initialized causing camera buttons to crash.

> **Deliverables**:
> - Fixed callback registration in `callback_groups.py`
> - CameraManager initialization in `application.py`
> - Verified working buttons: "Read User Info", all Camera tab buttons

> **Estimated Effort**: Short
> **Parallel Execution**: YES - 2 independent waves
> **Critical Path**: Wave 1 → Wave 2

---

## Context

### Original Request
User reported many buttons in the SensorCalibrator application are not working.

### Investigation Findings

| Issue | Location | Root Cause |
|-------|----------|------------|
| Missing callback `read_properties` | `callback_groups.py` | Callback key not registered in `ActivationCallbacks` |
| CameraManager not initialized | `application.py` | Manager never instantiated, causing `AttributeError` when camera buttons clicked |
| Buttons disabled by default | `ui_manager.py` | **Expected behavior** - enabled after connection |

---

## Work Objectives

### Core Objective
Fix button functionality issues identified in code review.

### Concrete Deliverables

1. **Fixed callback registration** - Add `read_properties` callback alias
2. **Initialized CameraManager** - Create and wire CameraManager in application.py

### Definition of Done
- [ ] "Read User Info" button responds to clicks
- [ ] Camera tab buttons (photo, monitor, stream, OTA) do not crash
- [ ] No `AttributeError` in logs when clicking camera buttons

### Must Have
- Fix callback registration without breaking existing callbacks
- Initialize CameraManager with proper dependencies

### Must NOT Have
- Break existing button functionality
- Add unimplemented stub methods

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

- **Manual Testing**: Click each fixed button and verify no errors in log output
- **Code Review**: Verify callback registration present, CameraManager instantiated

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Immediate — foundation):
├── Task 1: Add read_properties callback alias to callback_groups.py
└── Task 2: Verify callback registration in callback_groups.py

Wave 2 (After Wave 1 — integration):
├── Task 3: Find CameraManager implementation location
├── Task 4: Initialize CameraManager in application.py
└── Task 5: Verify camera button click no longer crashes
```

### Dependency Matrix
- **Task 1-2**: No dependencies — can run in parallel
- **Task 3-5**: Depends on Task 1-2 completion

---

## TODOs

- [ ] 1. Add `read_properties` callback alias in `callback_groups.py`

  **What to do**:
  - Find `ActivationCallbacks` class in `sensor_calibrator/app/callback_groups.py`
  - Add `'read_properties': self.read_sensor_properties` to `register_all()` method
  - Add `'read_properties'` to `CALLBACK_NAMES` list

  **References**:
  - `sensor_calibrator/app/callback_groups.py:230-245` - ActivationCallbacks structure
  - Line 243: Example of alias pattern `'verify_activation_status': self.verify_activation_status`

- [ ] 2. Verify callback registration works

  **What to do**:
  - Check that `read_properties` now appears in callbacks dictionary
  - Verify UI button at `ui_manager.py:415` can resolve the callback

  **References**:
  - `sensor_calibrator/ui_manager.py:415` - Button using `read_properties`

- [ ] 3. Find CameraManager implementation

  **What to do**:
  - Search for CameraManager class in `sensor_calibrator/camera/` directory
  - Identify required constructor parameters
  - Find existing manager initialization patterns (serial_manager, network_manager)

  **References**:
  - `sensor_calibrator/callback_groups.py:503-554` - CameraCallbacks using camera_manager

- [ ] 4. Initialize CameraManager in application.py

  **What to do**:
  - Add CameraManager import
  - Add `self.camera_manager = None` to `__init__`
  - Add `_init_camera_manager()` method similar to other managers
  - Call `_init_camera_manager()` in `_init_components()`

  **References**:
  - `sensor_calibrator/app/application.py:426-451` - Manager initialization patterns
  - Line 435: `self.serial_manager = SerialManager(callbacks)`

- [ ] 5. Verify camera buttons work

  **What to do**:
  - Test clicking camera buttons (photo, monitor, stream, OTA)
  - Verify no `AttributeError` in log output
  - Confirm button state changes properly

  **References**:
  - `sensor_calibrator/ui_manager.py:1488-1670` - Camera tab buttons

---

## Commit Strategy

- **1**: `fix(callbacks): add read_properties alias` — callback_groups.py
- **2**: `fix(app): initialize CameraManager` — application.py

---

## Success Criteria

### Verification Commands
```bash
# Test read_properties callback
python -c "from sensor_calibrator.app.callback_groups import CallbackRegistry; print('read_properties' in CallbackRegistry.__init__.__func__.__code__.co_names)"  # Should show callback exists

# Test CameraManager import
python -c "from sensor_calibrator.camera import CameraManager"  # Should not error
```

### Final Checklist
- [ ] read_properties callback registered
- [ ] CameraManager initialized in application.py
- [ ] No crashes when clicking fixed buttons
