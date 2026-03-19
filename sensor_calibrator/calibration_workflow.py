"""
Calibration Workflow Module

Manages the 6-position calibration workflow.
"""

import queue
import sys
import threading
import time
from pathlib import Path
import numpy as np
from typing import Callable, Optional

from .config import Config, CalibrationConfig

# 导入现有的校准算法函数 (使用可选导入，失败时提供明确错误)
_calibration_functions_available = False
_import_error_message = None

try:
    scripts_path = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_path))
    from calibration import compute_six_position_calibration, compute_gyro_offset
    _calibration_functions_available = True
except (ImportError, ModuleNotFoundError) as e:
    _import_error_message = str(e)
    compute_six_position_calibration = None
    compute_gyro_offset = None


class CalibrationWorkflow:
    """
    管理6位置校准流程

    负责:
    - 校准流程控制 (开始/采集/完成)
    - 校准数据采集
    - 校准参数计算
    - 校准命令生成和发送
    """

    def __init__(self, data_queue, callbacks: dict):
        """
        初始化 CalibrationWorkflow

        Args:
            data_queue: 数据队列
            callbacks: 回调函数字典，包含:
                - 'log_message': 日志记录函数
                - 'parse_sensor_data': 数据解析函数
                - 'update_position_display': 更新位置显示
                - 'send_ss_command': 发送SS命令
                - 'update_ui_state': 更新UI状态
                
                # 新增实时回调（可选）
                - 'on_collection_start': 采集开始 (position, max_samples)
                - 'on_progress': 进度更新 (position, current, total)
                - 'on_quality_update': 质量更新 (position, score, std_mean)
                - 'on_collection_complete': 采集完成 (position, samples_collected)
                - 'on_capture_error': 采集错误
                - 'on_position_captured': 位置完成 (next_position)
                - 'on_calibration_finished': 校准完成 (params)
                - 'on_calibration_error': 校准错误
        """
        self.data_queue = data_queue
        self.callbacks = callbacks

        # 校准状态
        self._is_calibrating = False
        self._is_paused = False
        self._current_position = 0
        self._calibration_positions = []
        self._calibration_samples = Config.CALIBRATION_SAMPLES

        # 位置名称
        self.position_names = CalibrationConfig.POSITION_NAMES

        # 线程安全锁（保护共享状态）
        self._state_lock = threading.Lock()

        # 校准参数
        self._calibration_params = None
        
        # 自动引导设置
        self.auto_advance = False
        self.auto_advance_delay = 1.0  # 延迟1秒自动进入下一步

    # ==================== 属性 ====================

    @property
    def is_calibrating(self) -> bool:
        """是否正在校准（线程安全）"""
        with self._state_lock:
            return self._is_calibrating

    @property
    def current_position(self) -> int:
        """当前位置索引（线程安全）"""
        with self._state_lock:
            return self._current_position

    @property
    def calibration_params(self) -> Optional[dict]:
        """获取校准参数（线程安全）"""
        with self._state_lock:
            return self._calibration_params.copy() if self._calibration_params else None

    @property
    def position_progress(self) -> str:
        """获取位置进度字符串（线程安全）"""
        with self._state_lock:
            if self._current_position < 6:
                return f"Position {self._current_position + 1}/6: {self.position_names[self._current_position]}"
            return "Calibration complete!"
    
    @property
    def is_paused(self) -> bool:
        """是否已暂停（线程安全）"""
        with self._state_lock:
            return self._is_paused

    # ==================== 校准流程控制 ====================

    def start_calibration(self) -> bool:
        """开始校准流程"""
        with self._state_lock:
            self._is_calibrating = True
            self._current_position = 0
            self._calibration_positions = []
            self._calibration_params = None

        self._log_message("Starting 6-position calibration")
        self._log_message(f"Position 1: {self.position_names[0]}")
        self._log_message("Place sensor in position and click 'Capture Position'")

        return True

    def stop_calibration(self) -> None:
        """停止校准流程"""
        with self._state_lock:
            self._is_calibrating = False
            self._current_position = 0
            self._calibration_positions = []

    def reset(self) -> None:
        """重置校准状态"""
        with self._state_lock:
            self._is_calibrating = False
            self._is_paused = False
            self._current_position = 0
            self._calibration_positions = []
            self._calibration_params = None

    def pause(self) -> None:
        """暂停校准流程"""
        with self._state_lock:
            self._is_paused = True
        self._log_message("校准已暂停")

    def resume(self) -> None:
        """恢复校准流程"""
        with self._state_lock:
            self._is_paused = False
        self._log_message("校准已恢复")

    def set_auto_advance(self, enabled: bool, delay: float = 1.0) -> None:
        """
        设置自动引导模式
        
        Args:
            enabled: 是否启用自动进入下一步
            delay: 延迟时间（秒）
        """
        self.auto_advance = enabled
        self.auto_advance_delay = delay
        if enabled:
            self._log_message(f"已启用自动引导模式（延迟 {delay} 秒）")
        else:
            self._log_message("已禁用自动引导模式")

    def capture_position(self) -> bool:
        """采集当前位置数据"""
        with self._state_lock:
            if not self._is_calibrating or self._current_position >= 6 or self._is_paused:
                if self._is_paused:
                    self._log_message("校准已暂停，无法采集")
                return False
            current_pos = self._current_position  # 在锁内获取位置

        self._log_message(
            f"Capturing data for position {current_pos + 1}..."
        )

        # 在新线程中采集数据
        threading.Thread(
            target=self._collect_calibration_data,
            args=(current_pos,),
            daemon=True,
        ).start()

        return True

    def _collect_calibration_data(self, position: int) -> None:
        """
        采集校准数据 - 优化版本（预分配数组 + 进度回调）
        
        优化点：
        - 使用预分配 numpy 数组避免动态扩容开销
        - 使用索引直接赋值代替 list.append
        - 批量进度回调，减少UI刷新频率（每10个样本）
        """
        try:
            # 优化：预分配 numpy 数组（避免 list 动态扩容）
            max_samples = self._calibration_samples
            mpu_accel_samples = np.zeros((max_samples, 3))
            mpu_gyro_samples = np.zeros((max_samples, 3))
            adxl_accel_samples = np.zeros((max_samples, 3))

            start_time = time.time()
            samples_collected = 0
            last_progress_update = 0
            last_quality_update = 0

            # 通知开始采集
            if "on_collection_start" in self.callbacks:
                self.callbacks["on_collection_start"](position, max_samples)

            # 采集数据
            while (
                samples_collected < max_samples and self._is_calibrating
            ):
                try:
                    # 从队列获取数据
                    data_string = self.data_queue.get(timeout=Config.QUICK_SLEEP)

                    if "parse_sensor_data" in self.callbacks:
                        mpu_accel, mpu_gyro, adxl_accel = self.callbacks[
                            "parse_sensor_data"
                        ](data_string)

                        if mpu_accel and mpu_gyro and adxl_accel:
                            # 优化：直接赋值到预分配数组
                            mpu_accel_samples[samples_collected] = mpu_accel
                            mpu_gyro_samples[samples_collected] = mpu_gyro
                            adxl_accel_samples[samples_collected] = adxl_accel
                            samples_collected += 1
                            
                            # 批量更新进度（每10个样本）
                            if (samples_collected - last_progress_update >= 10 
                                and "on_progress" in self.callbacks):
                                self.callbacks["on_progress"](position, samples_collected, max_samples)
                                last_progress_update = samples_collected
                            
                            # 批量更新数据质量（每20个样本）
                            if (samples_collected - last_quality_update >= 20
                                and "on_quality_update" in self.callbacks):
                                # 计算当前质量（使用最近20个样本）
                                start_idx = max(0, samples_collected - 20)
                                recent_std = np.std(mpu_accel_samples[start_idx:samples_collected], axis=0)
                                quality_score = self._calculate_quality_score(recent_std)
                                self.callbacks["on_quality_update"](position, quality_score, float(np.mean(recent_std)))
                                last_quality_update = samples_collected

                    # 超时保护
                    if time.time() - start_time > 10:
                        self._log_message("Timeout: Stopping data collection")
                        break

                except queue.Empty:
                    # 队列为空，短暂休眠后继续尝试（正常现象）
                    time.sleep(Config.QUICK_SLEEP)
                    continue
                except Exception as e:
                    # 真正的错误才记录
                    self._log_message(f"Error collecting calibration data: {e}")
                    time.sleep(Config.QUICK_SLEEP)
                    continue
            
            # 通知采集完成
            if "on_collection_complete" in self.callbacks:
                self.callbacks["on_collection_complete"](position, samples_collected)

            min_required_samples = int(
                Config.CALIBRATION_SAMPLES * Config.MIN_CALIBRATION_SAMPLE_RATIO
            )
            if samples_collected >= min_required_samples:
                # 优化：使用切片获取实际收集的样本（避免拷贝）
                mpu_accel_valid = mpu_accel_samples[:samples_collected]
                mpu_gyro_valid = mpu_gyro_samples[:samples_collected]
                adxl_accel_valid = adxl_accel_samples[:samples_collected]
                
                # 计算平均值（使用 numpy 向量化操作）
                mpu_accel_avg = np.mean(mpu_accel_valid, axis=0)
                mpu_gyro_avg = np.mean(mpu_gyro_valid, axis=0)
                adxl_accel_avg = np.mean(adxl_accel_valid, axis=0)

                # 计算标准差用于评估数据质量
                mpu_accel_std = np.std(mpu_accel_valid, axis=0)
                adxl_accel_std = np.std(adxl_accel_valid, axis=0)

                # 处理校准数据
                self._process_calibration_data(
                    position,
                    samples_collected,
                    mpu_accel_avg,
                    mpu_gyro_avg,
                    adxl_accel_avg,
                    mpu_accel_std,
                    adxl_accel_std,
                )
            else:
                self._log_message(
                    f"Error: Insufficient data collected for position {position + 1}"
                )
                if "on_capture_error" in self.callbacks:
                    self.callbacks["on_capture_error"]()

        except Exception as e:
            self._log_message(f"Error in data collection: {str(e)}")
            if "on_capture_error" in self.callbacks:
                self.callbacks["on_capture_error"]()

    def _process_calibration_data(
        self,
        position: int,
        samples_collected: int,
        mpu_accel_avg: np.ndarray,
        mpu_gyro_avg: np.ndarray,
        adxl_accel_avg: np.ndarray,
        mpu_accel_std: np.ndarray,
        adxl_accel_std: np.ndarray,
    ) -> None:
        """处理校准数据（线程安全）"""
        with self._state_lock:
            # 存储校准数据
            self._calibration_positions.append(
                {
                    "mpu_accel": mpu_accel_avg,
                    "mpu_gyro": mpu_gyro_avg,
                    "adxl_accel": adxl_accel_avg,
                }
            )

            next_position = position + 1
            self._current_position = next_position

        # 记录数据质量信息（在锁外，因为只是日志）
        self._log_message(
            f"Position {position + 1} captured: {samples_collected} samples"
        )
        self._log_message(
            f"  MPU6050: [{mpu_accel_avg[0]:.3f}, {mpu_accel_avg[1]:.3f}, {mpu_accel_avg[2]:.3f}]"
        )
        self._log_message(
            f"  ADXL355: [{adxl_accel_avg[0]:.3f}, {adxl_accel_avg[1]:.3f}, {adxl_accel_avg[2]:.3f}]"
        )
        self._log_message(
            f"  Data Quality - MPU6050 Noise: [{mpu_accel_std[0]:.4f}, {mpu_accel_std[1]:.4f}, {mpu_accel_std[2]:.4f}]"
        )

        if next_position < 6:
            self._log_message(
                f"Position {next_position + 1}: {self.position_names[next_position]}"
            )
            if "on_position_captured" in self.callbacks:
                self.callbacks["on_position_captured"](next_position)
            
            # 自动引导模式：延迟后自动采集下一个位置
            if self.auto_advance and not self._is_paused:
                self._log_message(f"自动引导：{self.auto_advance_delay} 秒后开始采集位置 {next_position + 1}")
                # 在新线程中执行延迟，避免阻塞
                threading.Thread(
                    target=self._auto_advance_to_next,
                    args=(next_position,),
                    daemon=True
                ).start()
        else:
            self.finish_calibration()
    
    def _auto_advance_to_next(self, position: int):
        """
        自动进入下一个位置的延迟执行
        包含位置稳定性检测：等待传感器位置正确且稳定后才自动采集
        
        Args:
            position: 目标位置索引
        """
        self._log_message(f"自动引导：请放置传感器到位置 {position + 1}")
        
        # 等待位置稳定
        stable = self._wait_for_position_stable(position, timeout=30.0)
        
        if not stable:
            self._log_message("自动引导：位置检测超时，请手动点击 Capture")
            return
        
        # 在锁内读取状态，避免竞态条件
        with self._state_lock:
            is_calibrating = self._is_calibrating
            is_paused = self._is_paused
            current_position = self._current_position
        
        # 检查是否仍然处于校准状态且未被暂停
        if is_calibrating and not is_paused:
            if current_position == position:
                self._log_message(f"自动采集位置 {position + 1}")
                self.capture_position()
        elif is_paused:
            self._log_message("校准已暂停，自动引导等待恢复...")
    
    def _wait_for_position_stable(self, position: int, timeout: float = 30.0) -> bool:
        """
        等待传感器位置稳定
        
        检测逻辑：
        1. 检查传感器朝向是否符合预期位置的重力方向
        2. 等待数据稳定（标准差小于阈值持续2秒）
        
        Args:
            position: 目标位置索引
            timeout: 超时时间（秒）
            
        Returns:
            True: 位置已稳定，可以采集
            False: 超时，位置未稳定
        """
        # 位置对应的重力方向 (X, Y, Z)
        expected_directions = [
            (1, 0, 0),   # +X: X轴朝下 (+g)
            (-1, 0, 0),  # -X: X轴朝上 (-g)
            (0, 1, 0),   # +Y: Y轴朝下 (+g)
            (0, -1, 0),  # -Y: Y轴朝上 (-g)
            (0, 0, 1),   # +Z: Z轴朝下 (+g)
            (0, 0, -1),  # -Z: Z轴朝上 (-g)
        ]
        expected = expected_directions[position]
        
        start_time = time.time()
        stability_start = None
        
        # 滑动窗口用于计算稳定性
        window_size = 20
        recent_samples = []
        
        while time.time() - start_time < timeout:
            # 检查暂停状态
            with self._state_lock:
                if self._is_paused or not self._is_calibrating:
                    return False
            
            try:
                # 从队列获取最新数据（非阻塞）
                data_string = self.data_queue.get(timeout=0.05)
                
                if "parse_sensor_data" in self.callbacks:
                    mpu_accel, _, adxl_accel = self.callbacks["parse_sensor_data"](data_string)
                    
                    if mpu_accel and adxl_accel:
                        # 使用MPU6050数据检测（也可以使用ADXL355）
                        accel = np.array(mpu_accel)
                        
                        # 归一化
                        magnitude = np.linalg.norm(accel)
                        if magnitude > 0.1:
                            normalized = accel / magnitude
                            
                            # 检查方向是否匹配预期（点积接近1表示方向一致）
                            expected_vec = np.array(expected, dtype=float)
                            dot_product = np.dot(normalized, expected_vec)
                            
                            if dot_product > 0.85:  # 约30度以内
                                recent_samples.append(accel)
                                if len(recent_samples) > window_size:
                                    recent_samples.pop(0)
                                
                                # 检查稳定性（标准差）
                                if len(recent_samples) >= window_size:
                                    std = np.std(recent_samples, axis=0)
                                    max_std = np.max(std)
                                    
                                    if max_std < 0.05:  # 稳定性阈值
                                        if stability_start is None:
                                            stability_start = time.time()
                                            self._log_message(f"位置 {position + 1} 接近目标，等待稳定...")
                                        elif time.time() - stability_start >= 2.0:  # 稳定2秒
                                            self._log_message(f"位置 {position + 1} 已稳定，准备采集")
                                            return True
                                    else:
                                        stability_start = None  # 不稳定，重置计时
            except queue.Empty:
                time.sleep(0.01)
                continue
            except Exception:
                continue
        
        return False  # 超时

    def finish_calibration(self) -> None:
        """完成校准并计算参数（线程安全）"""
        self._log_message("Calculating calibration parameters...")

        # 检查校准函数是否可用
        if not _calibration_functions_available:
            error_msg = f"Calibration functions not available: {_import_error_message}"
            self._log_message(f"Error: {error_msg}")
            self._log_message("Please ensure scripts/calibration.py exists and is properly installed.")
            if "on_calibration_error" in self.callbacks:
                self.callbacks["on_calibration_error"]()
            return

        # 在锁内复制数据，然后释放锁进行计算
        with self._state_lock:
            if len(self._calibration_positions) != 6:
                self._log_message("Error: Need exactly 6 positions for calibration!")
                self.reset()
                if "on_calibration_error" in self.callbacks:
                    self.callbacks["on_calibration_error"]()
                return

            # 复制数据（避免在计算时持有锁）
            calibration_positions = self._calibration_positions.copy()

        try:
            # 提取样本数据
            mpu_samples = [pos["mpu_accel"] for pos in calibration_positions]
            adxl_samples = [pos["adxl_accel"] for pos in calibration_positions]
            gyro_samples = [pos["mpu_gyro"] for pos in calibration_positions]

            # 使用现有的校准函数计算参数（避免重复实现）
            mpu_scales, mpu_offsets = compute_six_position_calibration(
                mpu_samples, Config.GRAVITY_CONSTANT
            )
            adxl_scales, adxl_offsets = compute_six_position_calibration(
                adxl_samples, Config.GRAVITY_CONSTANT
            )
            mpu_gyro_offsets = compute_gyro_offset(gyro_samples)

            # 存储校准参数
            with self._state_lock:
                self._calibration_params = {
                    "mpu_accel_scale": mpu_scales,
                    "mpu_accel_offset": mpu_offsets,
                    "adxl_accel_scale": adxl_scales,
                    "adxl_accel_offset": adxl_offsets,
                    "mpu_gyro_offset": mpu_gyro_offsets,
                }
                self._is_calibrating = False

            self._log_message("Calibration parameters calculated successfully!")
            self._log_message(
                f"MPU6050 Scale: [{mpu_scales[0]:.4f}, {mpu_scales[1]:.4f}, {mpu_scales[2]:.4f}]"
            )
            self._log_message(
                f"MPU6050 Offset: [{mpu_offsets[0]:.4f}, {mpu_offsets[1]:.4f}, {mpu_offsets[2]:.4f}]"
            )
            self._log_message(
                f"ADXL355 Scale: [{adxl_scales[0]:.4f}, {adxl_scales[1]:.4f}, {adxl_scales[2]:.4f}]"
            )

            # 通知校准完成
            if "on_calibration_finished" in self.callbacks:
                self.callbacks["on_calibration_finished"](self._calibration_params)

        except Exception as e:
            self._log_message(f"Error calculating calibration parameters: {str(e)}")
            self.reset()
            if "on_calibration_error" in self.callbacks:
                self.callbacks["on_calibration_error"]()

    def generate_calibration_commands(self) -> list:
        """生成校准命令列表"""
        with self._state_lock:
            if not self._calibration_params:
                return []
            # 复制参数到局部变量，避免在锁外访问共享数据
            params = self._calibration_params.copy()

        commands = []

        # MPU6050加速度计校准 - 使用新格式指令
        scale = params["mpu_accel_scale"]
        offset = params["mpu_accel_offset"]
        commands.append(
            f"SET:RACKS,{scale[0]:.6f},{scale[1]:.6f},{scale[2]:.6f}"
        )
        commands.append(
            f"SET:RACOF,{offset[0]:.6f},{offset[1]:.6f},{offset[2]:.6f}"
        )

        # ADXL355加速度计校准 - 使用新格式指令
        scale = params["adxl_accel_scale"]
        offset = params["adxl_accel_offset"]
        commands.append(
            f"SET:REACKS,{scale[0]:.6f},{scale[1]:.6f},{scale[2]:.6f}"
        )
        commands.append(
            f"SET:REACOF,{offset[0]:.6f},{offset[1]:.6f},{offset[2]:.6f}"
        )

        # 陀螺仪校准 - 使用新格式指令
        gyro = params["mpu_gyro_offset"]
        commands.append(f"SET:VROOF,{gyro[0]:.6f},{gyro[1]:.6f},{gyro[2]:.6f}")

        return commands

    # ==================== 文件保存功能 ====================

    def save_calibration_to_file(self, parent_widget=None) -> bool:
        """保存校准参数到用户选择的文件"""
        from tkinter import filedialog
        from datetime import datetime
        import json

        if not self._calibration_params:
            self._log_message("Error: No calibration parameters to save!")
            return False

        # 构建默认文件名
        default_name = (
            f"calibration_params_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # 弹出保存对话框
        filename = filedialog.asksaveasfilename(
            parent=parent_widget,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save Calibration Parameters",
        )

        if not filename:
            self._log_message("Save cancelled by user")
            return False

        # 构建保存数据
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "calibration_params": self._calibration_params,
        }

        # 保存到文件
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            self._log_message(f"Calibration parameters saved to: {filename}")
            return True

        except Exception as e:
            self._log_message(f"Error saving calibration parameters: {str(e)}")
            return False

    # ==================== 辅助方法 ====================

    def _calculate_quality_score(self, std_values) -> int:
        """
        计算数据质量评分
        
        评分标准：
        - 90-100: 优秀 (平均标准差 < 0.01)
        - 70-89:  良好 (平均标准差 < 0.05)
        - 50-69:  一般 (平均标准差 < 0.1)
        - < 50:   差 (平均标准差 >= 0.1)
        
        Args:
            std_values: 三轴标准差数组
            
        Returns:
            质量评分 (0-100)
        """
        mean_std = float(np.mean(std_values))
        
        if mean_std < 0.01:
            score = 90 + int((0.01 - mean_std) * 1000)
            return min(100, score)
        elif mean_std < 0.05:
            score = 70 + int((0.05 - mean_std) * 500)
            return min(89, score)
        elif mean_std < 0.1:
            score = 50 + int((0.1 - mean_std) * 400)
            return min(69, score)
        else:
            return max(0, 50 - int((mean_std - 0.1) * 100))

    def _log_message(self, message: str) -> None:
        """记录日志（通过回调）"""
        if "log_message" in self.callbacks:
            self.callbacks["log_message"](message)
