#!/usr/bin/env python3
"""
SensorCalibrator 性能分析脚本
用于识别性能瓶颈和监控资源使用
"""

import cProfile
import pstats
import time
import tracemalloc
from functools import wraps
import sys

# 性能监控装饰器
def benchmark(func):
    """装饰器：测量函数执行时间"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[BENCHMARK] {func.__name__}: {elapsed*1000:.2f} ms")
        return result
    return wrapper


def profile_function(func, *args, **kwargs):
    """使用 cProfile 分析函数性能"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func(*args, **kwargs)
    
    profiler.disable()
    
    # 打印统计信息
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    print(f"\n=== Profile for {func.__name__} ===")
    stats.print_stats(20)
    
    return result


def memory_tracker(func):
    """装饰器：跟踪内存使用情况"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        
        # 记录开始前的内存
        start_mem = tracemalloc.get_traced_memory()
        
        result = func(*args, **kwargs)
        
        # 记录结束后的内存
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"[MEMORY] {func.__name__}:")
        print(f"  Current: {current / 1024 / 1024:.2f} MB")
        print(f"  Peak: {peak / 1024 / 1024:.2f} MB")
        print(f"  Delta: {(current - start_mem[0]) / 1024 / 1024:.2f} MB")
        
        return result
    return wrapper


class PerformanceMonitor:
    """性能监控类"""
    
    def __init__(self):
        self.metrics = {}
        self.frame_times = []
        self.last_frame_time = time.perf_counter()
    
    def record_frame(self):
        """记录帧时间"""
        current = time.perf_counter()
        frame_time = current - self.last_frame_time
        self.frame_times.append(frame_time)
        self.last_frame_time = current
        
        # 只保留最近 100 帧
        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
    
    def get_fps(self):
        """计算平均 FPS"""
        if not self.frame_times:
            return 0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0
    
    def report(self):
        """生成性能报告"""
        if not self.frame_times:
            return "No data"
        
        avg_time = sum(self.frame_times) / len(self.frame_times)
        max_time = max(self.frame_times)
        min_time = min(self.frame_times)
        
        report = f"""
=== Performance Report ===
Frame Count: {len(self.frame_times)}
Average Frame Time: {avg_time*1000:.2f} ms ({1/avg_time:.1f} FPS)
Max Frame Time: {max_time*1000:.2f} ms ({1/max_time:.1f} FPS)
Min Frame Time: {min_time*1000:.2f} ms ({1/min_time:.1f} FPS)
"""
        return report


# 模拟数据处理性能测试
def test_data_processing():
    """测试数据处理性能"""
    import numpy as np
    
    # 模拟传感器数据
    n_samples = 2000
    mpu_accel_data = [np.random.randn(n_samples).tolist() for _ in range(3)]
    
    # 测试 1: 列表切片性能
    print("\n=== Test 1: List Slicing ===")
    start = time.perf_counter()
    for i in range(3):
        data = mpu_accel_data[i]
        sliced = data[-1000:]  # 切片操作
    elapsed = time.perf_counter() - start
    print(f"List slicing: {elapsed*1000:.2f} ms")
    
    # 测试 2: 统计计算性能
    print("\n=== Test 2: Statistics Calculation ===")
    start = time.perf_counter()
    for i in range(3):
        mean_val = np.mean(mpu_accel_data[i][-100:])
        std_val = np.std(mpu_accel_data[i][-100:])
    elapsed = time.perf_counter() - start
    print(f"Statistics (numpy): {elapsed*1000:.2f} ms")
    
    # 测试 3: 重力计算性能
    print("\n=== Test 3: Gravity Calculation ===")
    start = time.perf_counter()
    for j in range(min(100, n_samples)):
        gravity = np.sqrt(
            mpu_accel_data[0][j]**2 +
            mpu_accel_data[1][j]**2 +
            mpu_accel_data[2][j]**2
        )
    elapsed = time.perf_counter() - start
    print(f"Gravity calculation: {elapsed*1000:.2f} ms")


if __name__ == "__main__":
    print("SensorCalibrator Performance Profiler")
    print("=" * 50)
    
    # 运行测试
    test_data_processing()
    
    print("\n" + "=" * 50)
    print("To profile the main application:")
    print("1. Import this module in StableSensorCalibrator.py")
    print("2. Use @benchmark decorator on methods to monitor")
    print("3. Or use profile_function() to analyze specific functions")
