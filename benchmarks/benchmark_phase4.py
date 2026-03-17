"""
Phase 4 性能基准测试
验证批量数据处理和预分配数组优化
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import timeit
import numpy as np
from collections import deque


def benchmark_batch_vs_single():
    """测试批量 vs 单条处理"""
    print("=" * 60)
    print("批量处理 vs 单条处理")
    print("=" * 60)
    
    batch_size = 100
    data = [[1.0 + i*0.01, 2.0 + i*0.01, 9.8] for i in range(batch_size)]
    
    # 方法 1: 单条 append
    def single_append():
        d0, d1, d2 = deque(maxlen=200), deque(maxlen=200), deque(maxlen=200)
        for val in data:
            d0.append(val[0])
            d1.append(val[1])
            d2.append(val[2])
        return d0, d1, d2
    
    # 方法 2: 批量 extend
    def batch_extend():
        d0, d1, d2 = deque(maxlen=200), deque(maxlen=200), deque(maxlen=200)
        d0.extend([v[0] for v in data])
        d1.extend([v[1] for v in data])
        d2.extend([v[2] for v in data])
        return d0, d1, d2
    
    # 测试
    single_time = timeit.timeit(single_append, number=1000)
    batch_time = timeit.timeit(batch_extend, number=1000)
    
    print(f"\n单条 append ({batch_size} 条 x 1000 次):")
    print(f"  耗时: {single_time*1000:.2f} ms")
    print(f"\n批量 extend ({batch_size} 条 x 1000 次):")
    print(f"  耗时: {batch_time*1000:.2f} ms")
    print(f"\n提升: {single_time/batch_time:.1f}x")
    print()


def benchmark_preallocated_arrays():
    """测试预分配数组性能"""
    print("=" * 60)
    print("预分配数组性能")
    print("=" * 60)
    
    max_samples = 1000
    
    # 方法 1: list append
    def list_append():
        samples = []
        for i in range(max_samples):
            samples.append([1.0, 2.0, 9.8])
        return np.mean(samples, axis=0)
    
    # 方法 2: numpy 预分配
    def numpy_prealloc():
        samples = np.zeros((max_samples, 3))
        for i in range(max_samples):
            samples[i] = [1.0, 2.0, 9.8]
        return np.mean(samples, axis=0)
    
    # 测试
    list_time = timeit.timeit(list_append, number=100)
    np_time = timeit.timeit(numpy_prealloc, number=100)
    
    print(f"\nlist append ({max_samples} 样本 x 100 次):")
    print(f"  耗时: {list_time*1000:.2f} ms")
    print(f"\nnumpy 预分配 ({max_samples} 样本 x 100 次):")
    print(f"  耗时: {np_time*1000:.2f} ms")
    print(f"\n提升: {list_time/np_time:.1f}x")
    print()


def benchmark_batch_data_collection():
    """测试批量数据采集"""
    print("=" * 60)
    print("批量数据采集模拟")
    print("=" * 60)
    
    batch_size = 100
    
    # 模拟数据队列
    class MockQueue:
        def __init__(self, size):
            self.data = [f"1.{i:02d},2.{i:02d},3.{i:02d},0.1,0.2,0.3,1.{i:02d},2.{i:02d},3.{i:02d}" 
                        for i in range(size)]
            self.idx = 0
        
        def empty(self):
            return self.idx >= len(self.data)
        
        def get_nowait(self):
            item = self.data[self.idx]
            self.idx += 1
            return item
    
    queue = MockQueue(batch_size)
    
    def parse_sensor_data(data_string):
        try:
            parts = data_string.split(",")
            if len(parts) >= 9:
                values = [float(p) for p in parts[:9]]
                return values[0:3], values[3:6], values[6:9]
        except:
            pass
        return None, None, None
    
    # 方法 1: 单条处理
    def single_process():
        queue.idx = 0
        mpu_accel_samples = []
        while not queue.empty():
            data_string = queue.get_nowait()
            mpu_accel, _, _ = parse_sensor_data(data_string)
            if mpu_accel:
                mpu_accel_samples.append(mpu_accel)
        return np.mean(mpu_accel_samples, axis=0) if mpu_accel_samples else 0
    
    # 方法 2: 批量收集后处理
    def batch_process():
        queue.idx = 0
        batch = []
        while not queue.empty():
            batch.append(queue.get_nowait())
        
        mpu_accel_samples = []
        for data_string in batch:
            mpu_accel, _, _ = parse_sensor_data(data_string)
            if mpu_accel:
                mpu_accel_samples.append(mpu_accel)
        return np.mean(mpu_accel_samples, axis=0) if mpu_accel_samples else 0
    
    # 测试
    single_time = timeit.timeit(single_process, number=100)
    batch_time = timeit.timeit(batch_process, number=100)
    
    print(f"\n单条处理 ({batch_size} 条 x 100 次):")
    print(f"  耗时: {single_time*1000:.2f} ms")
    print(f"\n批量处理 ({batch_size} 条 x 100 次):")
    print(f"  耗时: {batch_time*1000:.2f} ms")
    print(f"\n提升: {single_time/batch_time:.1f}x")
    print()


def benchmark_large_batch_processing():
    """测试大批量数据处理"""
    print("=" * 60)
    print("大批量数据处理")
    print("=" * 60)
    
    batch_sizes = [100, 500, 1000]
    
    for batch_size in batch_sizes:
        data = [[1.0 + i*0.001, 2.0 + i*0.001, 9.8] for i in range(batch_size)]
        
        def process():
            d0, d1, d2 = deque(maxlen=batch_size*2), deque(maxlen=batch_size*2), deque(maxlen=batch_size*2)
            d0.extend([v[0] for v in data])
            d1.extend([v[1] for v in data])
            d2.extend([v[2] for v in data])
            return d0, d1, d2
        
        elapsed = timeit.timeit(process, number=100)
        
        print(f"\n{batch_size} 条数据 x 100 次:")
        print(f"  平均: {elapsed/100*1000:.3f} ms/次")
        print(f"  吞吐: {batch_size/(elapsed/100):.0f} 条/秒")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Phase 4 性能基准测试")
    print("=" * 60 + "\n")
    
    benchmark_batch_vs_single()
    benchmark_preallocated_arrays()
    benchmark_batch_data_collection()
    benchmark_large_batch_processing()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
