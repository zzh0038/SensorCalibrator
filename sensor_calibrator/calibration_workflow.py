"""
Calibration Workflow Module

Manages the 6-position calibration workflow.
"""

import threading
import time
import numpy as np
from typing import Callable, Optional, List, Dict, Any

from .config import Config, CalibrationConfig


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
        """
        self.data_queue = data_queue
        self.callbacks = callbacks
        
        # 校准状态
        self._is_calibrating = False
        self._current_position = 0
        self._calibration_positions: List[Dict[str, Any]] = []
        self._calibration_samples = Config.CALIBRATION_SAMPLES
        
        # 位置名称
        self.position_names = CalibrationConfig.POSITION_NAMES
        
        # 校准参数
        self._calibration_params: Optional[Dict[str, Any]] = None
    
    # ==================== 属性 ====================
    
    @property
    def is_calibrating(self) -> bool:
        """是否正在校准"""
        return self._is_calibrating
    
    @property
    def current_position(self) -> int:
        """当前位置索引"""
        return self._current_position
    
    @property
    def calibration_params(self) -> Optional[Dict[str, Any]]:
        """获取校准参数"""
        return self._calibration_params
    
    @property
    def position_progress(self) -> str:
        """获取位置进度字符串"""
        if self._current_position < 6:
            return f"Position {self._current_position + 1}/6: {self.position_names[self._current_position]}"
        return "Calibration complete!"
    
    # ==================== 校准流程控制 ====================
    
    def start_calibration(self) -> bool:
        """
        开始校准流程
        
        Returns:
            bool: 是否成功启动
        """
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
        self._is_calibrating = False
        self._current_position = 0
        self._calibration_positions = []
    
    def reset(self) -> None:
        """重置校准状态"""
        self._is_calibrating = False
        self._current_position = 0
        self._calibration_positions = []
        self._calibration_params = None
    
    def capture_position(self) -> bool:
        """
        采集当前位置数据
        
        Returns:
            bool: 是否成功启动采集
        """
        if not self._is_calibrating or self._current_position >= 6:
            return False
        
        self._log_message(f"Capturing data for position {self._current_position + 1}...")
        
        # 在新线程中采集数据
        threading.Thread(
            target=self._collect_calibration_data,
            args=(self._current_position,),
            daemon=True
        ).start()
        
        return True
    
    def _collect_calibration_data(self, position: int) -> None:
        """
        采集校准数据
        
        Args:
            position: 位置索引
        """
        try:
            mpu_accel_samples = []
            mpu_gyro_samples = []
            adxl_accel_samples = []
            
            start_time = time.time()
            samples_collected = 0
            
            # 采集数据
            while samples_collected < self._calibration_samples and self._is_calibrating:
                try:
                    # 从队列获取数据
                    data_string = self.data_queue.get(timeout=Config.QUICK_SLEEP)
                    
                    if 'parse_sensor_data' in self.callbacks:
                        mpu_accel, mpu_gyro, adxl_accel = self.callbacks['parse_sensor_data'](data_string)
                        
                        if mpu_accel and mpu_gyro and adxl_accel:
                            mpu_accel_samples.append(mpu_accel)
                            mpu_gyro_samples.append(mpu_gyro)
                            adxl_accel_samples.append(adxl_accel)
                            samples_collected += 1
                    
                    # 超时保护
                    if time.time() - start_time > 10:
                        self._log_message("Timeout: Stopping data collection")
                        break
                        
                except Exception:
                    time.sleep(Config.QUICK_SLEEP)
                    continue
            
            if samples_collected >= Config.CALIBRATION_SAMPLES // 10:  # 至少有10%的样本
                # 计算平均值
                mpu_accel_avg = np.mean(mpu_accel_samples, axis=0)
                mpu_gyro_avg = np.mean(mpu_gyro_samples, axis=0)
                adxl_accel_avg = np.mean(adxl_accel_samples, axis=0)
                
                # 计算标准差用于评估数据质量
                mpu_accel_std = np.std(mpu_accel_samples, axis=0)
                adxl_accel_std = np.std(adxl_accel_samples, axis=0)
                
                # 处理校准数据
                self._process_calibration_data(
                    position, samples_collected,
                    mpu_accel_avg, mpu_gyro_avg, adxl_accel_avg,
                    mpu_accel_std, adxl_accel_std
                )
            else:
                self._log_message(f"Error: Insufficient data collected for position {position + 1}")
                if 'on_capture_error' in self.callbacks:
                    self.callbacks['on_capture_error']()
                    
        except Exception as e:
            self._log_message(f"Error in data collection: {str(e)}")
            if 'on_capture_error' in self.callbacks:
                self.callbacks['on_capture_error']()
    
    def _process_calibration_data(self, position: int, samples_collected: int,
                                  mpu_accel_avg: np.ndarray, mpu_gyro_avg: np.ndarray,
                                  adxl_accel_avg: np.ndarray, mpu_accel_std: np.ndarray,
                                  adxl_accel_std: np.ndarray) -> None:
        """处理校准数据"""
        # 存储校准数据
        self._calibration_positions.append({
            "mpu_accel": mpu_accel_avg,
            "mpu_gyro": mpu_gyro_avg,
            "adxl_accel": adxl_accel_avg,
        })
        
        # 记录数据质量信息
        self._log_message(f"Position {position + 1} captured: {samples_collected} samples")
        self._log_message(
            f"  MPU6050: [{mpu_accel_avg[0]:.3f}, {mpu_accel_avg[1]:.3f}, {mpu_accel_avg[2]:.3f}]"
        )
        self._log_message(
            f"  ADXL355: [{adxl_accel_avg[0]:.3f}, {adxl_accel_avg[1]:.3f}, {adxl_accel_avg[2]:.3f}]"
        )
        self._log_message(
            f"  Data Quality - MPU6050 Noise: [{mpu_accel_std[0]:.4f}, {mpu_accel_std[1]:.4f}, {mpu_accel_std[2]:.4f}]"
        )
        
        self._current_position = position + 1
        
        if self._current_position < 6:
            self._log_message(f"Position {self._current_position + 1}: {self.position_names[self._current_position]}")
            if 'on_position_captured' in self.callbacks:
                self.callbacks['on_position_captured'](self._current_position)
        else:
            self.finish_calibration()
    
    def finish_calibration(self) -> None:
        """完成校准并计算参数"""
        self._log_message("Calculating calibration parameters...")
        
        if len(self._calibration_positions) != 6:
            self._log_message("Error: Need exactly 6 positions for calibration!")
            self.reset()
            if 'on_calibration_error' in self.callbacks:
                self.callbacks['on_calibration_error']()
            return
        
        try:
            g = Config.GRAVITY_CONSTANT
            
            # 计算MPU6050加速度计参数
            mpu_scales = []
            mpu_offsets = []
            
            for axis in range(3):
                pos_idx = axis * 2
                neg_idx = axis * 2 + 1
                
                pos_val = self._calibration_positions[pos_idx]["mpu_accel"][axis]
                neg_val = self._calibration_positions[neg_idx]["mpu_accel"][axis]
                
                offset = (pos_val + neg_val) / 2.0
                delta = pos_val - neg_val
                
                if abs(delta) > 1e-6:
                    scale = delta / (2.0 * g)
                else:
                    scale = 1.0
                
                # 存储为1/scale用于校正
                scale_factor = 1.0 / scale if abs(scale) > 1e-6 else 1.0
                
                mpu_offsets.append(offset)
                mpu_scales.append(scale_factor)
            
            # 计算陀螺仪偏移（所有位置的平均值）
            mpu_gyro_offsets = []
            for axis in range(3):
                gyro_sum = sum(pos["mpu_gyro"][axis] for pos in self._calibration_positions)
                mpu_gyro_offsets.append(gyro_sum / 6.0)
            
            # 计算ADXL355加速度计参数
            adxl_scales = []
            adxl_offsets = []
            
            for axis in range(3):
                pos_idx = axis * 2
                neg_idx = axis * 2 + 1
                
                pos_val = self._calibration_positions[pos_idx]["adxl_accel"][axis]
                neg_val = self._calibration_positions[neg_idx]["adxl_accel"][axis]
                
                offset = (pos_val + neg_val) / 2.0
                delta = pos_val - neg_val
                
                if abs(delta) > 1e-6:
                    scale = delta / (2.0 * g)
                else:
                    scale = 1.0
                
                scale_factor = 1.0 / scale if abs(scale) > 1e-6 else 1.0
                
                adxl_offsets.append(offset)
                adxl_scales.append(scale_factor)
            
            # 存储校准参数
            self._calibration_params = {
                "mpu_accel_scale": mpu_scales,
                "mpu_accel_offset": mpu_offsets,
                "adxl_accel_scale": adxl_scales,
                "adxl_accel_offset": adxl_offsets,
                "mpu_gyro_offset": mpu_gyro_offsets,
            }
            
            self._log_message("Calibration parameters calculated successfully!")
            self._log_message(f"MPU6050 Scale: [{mpu_scales[0]:.4f}, {mpu_scales[1]:.4f}, {mpu_scales[2]:.4f}]")
            self._log_message(f"MPU6050 Offset: [{mpu_offsets[0]:.4f}, {mpu_offsets[1]:.4f}, {mpu_offsets[2]:.4f}]")
            self._log_message(f"ADXL355 Scale: [{adxl_scales[0]:.4f}, {adxl_scales[1]:.4f}, {adxl_scales[2]:.4f}]")
            
            self._is_calibrating = False
            
            # 通知校准完成
            if 'on_calibration_finished' in self.callbacks:
                self.callbacks['on_calibration_finished'](self._calibration_params)
                
        except Exception as e:
            self._log_message(f"Error calculating calibration parameters: {str(e)}")
            self.reset()
            if 'on_calibration_error' in self.callbacks:
                self.callbacks['on_calibration_error']()
    
    def generate_calibration_commands(self) -> List[str]:
        """
        生成校准命令列表
        
        Returns:
            List[str]: 校准命令字符串列表
        """
        if not self._calibration_params:
            return []
        
        commands = []
        
        # MPU6050加速度计校准
        scale = self._calibration_params["mpu_accel_scale"]
        offset = self._calibration_params["mpu_accel_offset"]
        commands.append(f"SET:CAS,MPU,SCAL,{scale[0]:.6f},{scale[1]:.6f},{scale[2]:.6f}")
        commands.append(f"SET:CAS,MPU,OFFS,{offset[0]:.6f},{offset[1]:.6f},{offset[2]:.6f}")
        
        # ADXL355加速度计校准
        scale = self._calibration_params["adxl_accel_scale"]
        offset = self._calibration_params["adxl_accel_offset"]
        commands.append(f"SET:CAS,ADXL,SCAL,{scale[0]:.6f},{scale[1]:.6f},{scale[2]:.6f}")
        commands.append(f"SET:CAS,ADXL,OFFS,{offset[0]:.6f},{offset[1]:.6f},{offset[2]:.6f}")
        
        # 陀螺仪校准
        gyro = self._calibration_params["mpu_gyro_offset"]
        commands.append(f"SET:CAS,GYRO,OFFS,{gyro[0]:.6f},{gyro[1]:.6f},{gyro[2]:.6f}")
        
        return commands
    
    # ==================== 文件保存功能 ====================
    
    def save_calibration_to_file(self, parent_widget=None) -> bool:
        """
        保存校准参数到用户选择的文件
        
        弹出文件选择对话框让用户选择保存位置，并将校准参数保存为 JSON 文件。
        
        Args:
            parent_widget: 父窗口（用于对话框定位）
            
        Returns:
            bool: 是否成功保存
        """
        from tkinter import filedialog
        from datetime import datetime
        import json
        
        if not self._calibration_params:
            self._log_message("Error: No calibration parameters to save!")
            return False
        
        # 构建默认文件名
        default_name = f"calibration_params_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 弹出保存对话框
        filename = filedialog.asksaveasfilename(
            parent=parent_widget,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save Calibration Parameters"
        )
        
        if not filename:
            self._log_message("Save cancelled by user")
            return False
        
        # 构建保存数据
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "calibration_params": self._calibration_params,
            "calibration_info": {
                "mpu_accel_scale": self._calibration_params["mpu_accel_scale"],
                "mpu_accel_offset": self._calibration_params["mpu_accel_offset"],
                "adxl_accel_scale": self._calibration_params["adxl_accel_scale"],
                "adxl_accel_offset": self._calibration_params["adxl_accel_offset"],
                "mpu_gyro_offset": self._calibration_params["mpu_gyro_offset"],
            }
        }
        
        # 保存到文件
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self._log_message(f"Calibration parameters saved to: {filename}")
            return True
            
        except Exception as e:
            self._log_message(f"Error saving calibration parameters: {str(e)}")
            return False
    
    # ==================== 辅助方法 ====================
    
    def _log_message(self, message: str) -> None:
        """记录日志（通过回调）"""
        if 'log_message' in self.callbacks:
            self.callbacks['log_message'](message)
