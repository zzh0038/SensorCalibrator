# 详细代码修复计划

**Generated**: 2026-03-06
**Source**: External Code Review

## 验证结果摘要

| 优先级 | 类别 | 问题数 | 状态 |
|--------|------|--------|------|
| 🔴 | Bugs | 3 | 已确认 |
| 🟠 | Design Issues | 4 | 已确认 |
| 🟡 | Security | 2 | 已确认 |
| 🔵 | Code Quality | 3 | 已确认 |

---

## Sprint 1: 修复关键 Bugs

### Task 1.1: 修复 OTA 参数初始化错误
- **Location**: `sensor_calibrator/network_manager.py:60`
- **Bug**: `"URL4": "1883"` 应为 `"URL4": ""`
- **Fix**:
  ```python
  self._ota_params: dict = {
      "URL1": "",
      "URL2": "",
      "URL3": "",
      "URL4": "",  # 修复：移除错误的端口默认值
  }
  ```

### Task 1.2: 修复 QueueAdapter 异常类型
- **Location**: `sensor_calibrator/ring_buffer.py:171`
- **Bug**: `raise Exception("Queue is empty")` 应为 `raise queue.Empty`
- **Fix**:
  ```python
  import queue  # 添加导入
  
  def get(self, block=True, timeout=None):
      item = self._buffer.get()
      if item is None:
          raise queue.Empty  # 修复：正确的异常类型
      return item
  ```

### Task 1.3: 添加 SerialManager 线程安全写入方法
- **Location**: `sensor_calibrator/serial_manager.py`
- **Problem**: SerialManager 没有提供线程安全的写锁包装方法
- **Fix**: 添加 `send_line()` 方法
  ```python
  def send_line(self, command: str) -> tuple[bool, str]:
      """线程安全地发送命令行（添加换行符）"""
      if not self.is_connected:
          return False, "Not connected"
      
      with self._write_lock:  # 需要添加锁
          try:
              self._ser.write(f"{command}\n".encode())
              self._ser.flush()
              return True, ""
          except Exception as e:
              return False, str(e)
  ```

### Task 1.4: 修复 NetworkManager 和 ActivationWorkflow 直接写串口
- **Location**: 
  - `sensor_calibrator/network_manager.py:345-346`
  - `sensor_calibrator/activation_workflow.py:312-313`
- **Fix**: 改为使用 SerialManager 的方法
  ```python
  # network_manager.py
  success, error = self.serial_manager.send_line(command)
  if not success:
      self._log_message(f"Error sending command: {error}")
  ```

---

## Sprint 2: 设计重构

### Task 2.1: 重构 CalibrationWorkflow 使用现有校准函数
- **Location**: `sensor_calibrator/calibration_workflow.py:232-326`
- **Refactor**: 使用 `scripts/calibration.py` 中的函数
  ```python
  from ..scripts.calibration import compute_six_position_calibration, compute_gyro_offset
  
  def finish_calibration(self) -> None:
      # 提取样本数据
      mpu_samples = [pos["mpu_accel"] for pos in self._calibration_positions]
      adxl_samples = [pos["adxl_accel"] for pos in self._calibration_positions]
      gyro_samples = [pos["mpu_gyro"] for pos in self._calibration_positions]
      
      # 使用现有函数计算
      mpu_scales, mpu_offsets = compute_six_position_calibration(mpu_samples, Config.GRAVITY_CONSTANT)
      adxl_scales, adxl_offsets = compute_six_position_calibration(adxl_samples, Config.GRAVITY_CONSTANT)
      mpu_gyro_offsets = compute_gyro_offset(gyro_samples)
      
      # 存储结果...
  ```

### Task 2.2: 移除 save_calibration_to_file 中的重复数据
- **Location**: `sensor_calibrator/calibration_workflow.py:396-406`
- **Fix**: 移除 `calibration_info` 字段（与 `calibration_params` 相同）
  ```python
  save_data = {
      "timestamp": datetime.now().isoformat(),
      "calibration_params": self._calibration_params,
      # 移除重复的 calibration_info
  }
  ```

### Task 2.3: 为 CalibrationWorkflow 添加线程安全
- **Location**: `sensor_calibrator/calibration_workflow.py`
- **Fix**: 添加锁保护共享状态
  ```python
  def __init__(self, data_queue, callbacks: dict):
      # ... 现有代码 ...
      self._state_lock = threading.Lock()  # 添加锁
  
  @property
  def current_position(self) -> int:
      with self._state_lock:
          return self._current_position
  
  def _process_calibration_data(self, ...):
      with self._state_lock:
          self._calibration_positions.append({...})
          self._current_position = position + 1
  ```

### Task 2.4: DataProcessor vs SensorDataBuffer 统一（可选）
- **Location**: `sensor_calibrator/data_processor.py` & `sensor_calibrator/data_buffer.py`
- **Note**: 这是一个大型重构，建议作为独立项目处理
- **Options**:
  1. 保留 DataProcessor（当前使用），标记 SensorDataBuffer 为 deprecated
  2. 逐步迁移到 SensorDataBuffer（更好的线程安全设计）

---

## Sprint 3: 安全修复

### Task 3.1: 修复激活密钥时序攻击漏洞
- **Location**: `sensor_calibrator/activation_workflow.py:185-188`
- **Fix**: 将长度检查移到比较之后
  ```python
  def verify_key(self, input_key: str, mac_address: Optional[str] = None) -> bool:
      mac = mac_address or self._mac_address
      if not mac:
          return False
      
      expected_key = self.generate_key_from_mac(mac)
      expected_fragment = expected_key[5:12]
      
      # 修复：始终执行恒定时间比较，无论长度如何
      # 如果长度不匹配，比较会失败，但时间上是恒定的
      try:
          return secrets.compare_digest(input_key.lower(), expected_fragment.lower())
      except TypeError:
          # 长度不匹配时 compare_digest 会抛出 TypeError
          return False
  ```

### Task 3.2: 增强激活密钥安全性（建议）
- **Location**: `sensor_calibrator/activation_workflow.py:70-72`
- **Problem**: 仅使用 7 字符片段（~28位密钥空间）
- **Options**:
  1. 使用更长的片段（如 16 字符 = 64位）
  2. 添加服务器端 secret 使用 HMAC
  3. 添加时间限制/重试限制防止暴力破解

---

## Sprint 4: 代码质量

### Task 4.1: 移除 UIManager 中的死代码
- **Location**: `sensor_calibrator/ui_manager.py:816-1015`
- **Methods to Remove**:
  - `_setup_wifi_section()` (被 `_setup_wifi_tab` 替代)
  - `_setup_mqtt_section()` (被 `_setup_mqtt_tab` 替代)
  - `_setup_ota_section()` (被 `_setup_ota_tab` 替代)

### Task 4.2: 修复 BAUD_RATES 类型注解
- **Location**: `sensor_calibrator/config.py:145`
- **Fix**:
  ```python
  from typing import List
  
  BAUD_RATES: Final[List[int]] = [9600, 19200, 38400, 57600, 115200]
  ```

### Task 4.3: 修复 NetworkManager response_str 潜在未赋值
- **Location**: `sensor_calibrator/network_manager.py:364`
- **Fix**: 初始化变量
  ```python
  response_str = ""  # 初始化
  while time.time() - start_time < timeout:
      # ... 循环体 ...
      response_str = response_bytes.decode("utf-8", errors="ignore")
  ```

---

## 测试策略

### 每轮 Sprint 后测试
```bash
python -m pytest tests/ -v --tb=short
```

### 特定功能测试
- 串口写入线程安全：创建多线程并发写入测试
- 校准流程：完整 6 位置校准流程
- 激活验证：密钥验证逻辑

---

## 执行建议

1. **立即执行**: Sprint 1（Bugs）- 影响稳定性
2. **本周内**: Sprint 3（Security）- 安全风险
3. **下周**: Sprint 2（Design）- 代码质量
4. **可选**: Sprint 4（Quality）- 清理工作

需要我按顺序开始执行这些修复吗？
