"""
SensorCalibrator Calibration Commands

校准命令生成器。
"""

from typing import List, Dict, Tuple


def generate_calibration_commands(
    calibration_params: Dict[str, List[float]]
) -> List[str]:
    """
    生成校准命令
    
    Args:
        calibration_params: 校准参数字典，包含:
            - mpu_accel_scale: MPU6050加速度计缩放系数 [x, y, z]
            - mpu_accel_offset: MPU6050加速度计偏移量 [x, y, z]
            - adxl_accel_scale: ADXL355加速度计缩放系数 [x, y, z]
            - adxl_accel_offset: ADXL355加速度计偏移量 [x, y, z]
            - mpu_gyro_offset: MPU6050陀螺仪偏移量 [x, y, z]
            
    Returns:
        校准命令列表
    """
    commands = []
    
    # MPU6050 加速度计缩放系数
    if "mpu_accel_scale" in calibration_params:
        scale = calibration_params["mpu_accel_scale"]
        cmd = f"SET:RACKS,{scale[0]:.6f},{scale[1]:.6f},{scale[2]:.6f}"
        commands.append(cmd)
    
    # MPU6050 加速度计偏移量
    if "mpu_accel_offset" in calibration_params:
        offset = calibration_params["mpu_accel_offset"]
        cmd = f"SET:RACOF,{offset[0]:.6f},{offset[1]:.6f},{offset[2]:.6f}"
        commands.append(cmd)
    
    # ADXL355 加速度计缩放系数
    if "adxl_accel_scale" in calibration_params:
        scale = calibration_params["adxl_accel_scale"]
        cmd = f"SET:REACKS,{scale[0]:.6f},{scale[1]:.6f},{scale[2]:.6f}"
        commands.append(cmd)
    
    # ADXL355 加速度计偏移量
    if "adxl_accel_offset" in calibration_params:
        offset = calibration_params["adxl_accel_offset"]
        cmd = f"SET:REACOF,{offset[0]:.6f},{offset[1]:.6f},{offset[2]:.6f}"
        commands.append(cmd)
    
    # MPU6050 陀螺仪偏移量
    if "mpu_gyro_offset" in calibration_params:
        offset = calibration_params["mpu_gyro_offset"]
        cmd = f"SET:VROOF,{offset[0]:.6f},{offset[1]:.6f},{offset[2]:.6f}"
        commands.append(cmd)
    
    return commands


def parse_calibration_params(commands: List[str]) -> Dict[str, List[float]]:
    """
    解析校准命令，提取校准参数
    
    Args:
        commands: 校准命令列表
        
    Returns:
        校准参数字典
    """
    params = {
        "mpu_accel_scale": [1.0, 1.0, 1.0],
        "mpu_accel_offset": [0.0, 0.0, 0.0],
        "adxl_accel_scale": [1.0, 1.0, 1.0],
        "adxl_accel_offset": [0.0, 0.0, 0.0],
        "mpu_gyro_offset": [0.0, 0.0, 0.0],
    }
    
    for cmd in commands:
        cmd = cmd.strip()
        
        if cmd.startswith("SET:RACKS,"):
            values = cmd[10:].split(",")
            if len(values) == 3:
                params["mpu_accel_scale"] = [float(v) for v in values]
        
        elif cmd.startswith("SET:RACOF,"):
            values = cmd[10:].split(",")
            if len(values) == 3:
                params["mpu_accel_offset"] = [float(v) for v in values]
        
        elif cmd.startswith("SET:REACKS,"):
            values = cmd[11:].split(",")
            if len(values) == 3:
                params["adxl_accel_scale"] = [float(v) for v in values]
        
        elif cmd.startswith("SET:REACOF,"):
            values = cmd[11:].split(",")
            if len(values) == 3:
                params["adxl_accel_offset"] = [float(v) for v in values]
        
        elif cmd.startswith("SET:VROOF,"):
            values = cmd[10:].split(",")
            if len(values) == 3:
                params["mpu_gyro_offset"] = [float(v) for v in values]
    
    return params
