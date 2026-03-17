"""
Phase 3 性能基准测试
验证 __slots__ 内存优化和 DataView 性能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import timeit
import sys

from sensor_calibrator.ring_buffer import RingBuffer, QueueAdapter
from sensor_calibrator.log_throttler import LogThrottler
from sensor_calibrator.data_buffer import SensorDataBuffer, DataView


def benchmark_memory_usage():
    """测试内存占用优化"""
    print("=" * 60)
    print("内存占用测试 (__slots__ 优化)")
    print("=" * 60)
    
    # RingBuffer 内存测试
    print("\n--- RingBuffer ---")
    rb = RingBuffer(1000)
    
    # 使用 __sizeof__ 估算内存（粗略估计）
    rb_size = sys.getsizeof(rb)
    print(f"单个 RingBuffer 大小: ~{rb_size} bytes")
    
    # 创建大量实例
    start = time.perf_counter()
    buffers = [RingBuffer(100) for _ in range(1000)]
    elapsed = time.perf_counter() - start
    print(f"创建 1000 个实例耗时: {elapsed*1000:.2f} ms")
    print(f"平均创建时间: {elapsed/1000*1000:.3f} ms")
    
    # QueueAdapter 内存测试
    print("\n--- QueueAdapter ---")
    qa = QueueAdapter(100)
    qa_size = sys.getsizeof(qa)
    print(f"单个 QueueAdapter 大小: ~{qa_size} bytes")
    
    # LogThrottler 内存测试
    print("\n--- LogThrottler ---")
    lt = LogThrottler()
    lt_size = sys.getsizeof(lt)
    print(f"单个 LogThrottler 大小: ~{lt_size} bytes")
    
    # SensorDataBuffer 内存测试
    print("\n--- SensorDataBuffer ---")
    sdb = SensorDataBuffer()
    sdb_size = sys.getsizeof(sdb)
    print(f"单个 SensorDataBuffer 大小: ~{sdb_size} bytes")
    print()


def benchmark_data_view_performance():
    """测试 DataView 性能优势"""
    print("=" * 60)
    print("DataView 性能测试")
    print("=" * 60)
    
    buffer = SensorDataBuffer()
    
    # 填充数据
    print("填充 1000 个样本...")
    for i in range(1000):
        buffer.add_sample(
            timestamp=i * 0.01,
            mpu_accel=(1.0 + i*0.001, 2.0 + i*0.001, 9.8),
            mpu_gyro=(0.1, 0.2, 0.3),
            adxl_accel=(1.0 + i*0.001, 2.0 + i*0.001, 9.8),
            gravity_mag=9.8
        )
    
    print("\n--- 数据访问性能对比 ---")
    
    # 测试传统属性访问（复制）
    def access_property():
        return buffer.time_data
    
    # 测试视图访问（不复制）
    view = buffer.get_time_data_view()
    def access_view():
        return len(view)
    
    # 预热
    for _ in range(100):
        access_property()
        access_view()
    
    # 测试属性访问
    num_calls = 10000
    prop_time = timeit.timeit(access_property, number=num_calls)
    print(f"属性访问 ({num_calls} 次): {prop_time*1000:.2f} ms")
    
    # 测试视图访问
    view_time = timeit.timeit(access_view, number=num_calls)
    print(f"视图访问 ({num_calls} 次): {view_time*1000:.2f} ms")
    
    if view_time > 0:
        print(f"速度比: {prop_time/view_time:.1f}x")
    
    print("\n--- 获取最新数据性能 ---")
    
    # 测试获取最新 100 个数据
    def get_latest_property():
        return buffer.time_data[-100:]
    
    def get_latest_view():
        return view.get_latest(100)
    
    latest_prop_time = timeit.timeit(get_latest_property, number=1000)
    latest_view_time = timeit.timeit(get_latest_view, number=1000)
    
    print(f"属性切片 (1000 次): {latest_prop_time*1000:.2f} ms")
    print(f"视图 get_latest (1000 次): {latest_view_time*1000:.2f} ms")
    
    if latest_view_time > 0:
        print(f"速度比: {latest_prop_time/latest_view_time:.1f}x")
    print()


def benchmark_data_view_thread_safety():
    """测试 DataView 线程安全性能"""
    print("=" * 60)
    print("DataView 线程安全性能")
    print("=" * 60)
    
    import threading
    
    buffer = SensorDataBuffer()
    view = buffer.get_time_data_view()
    
    # 预填充数据
    for i in range(500):
        buffer.add_sample(
            timestamp=i * 0.01,
            mpu_accel=(1.0, 2.0, 9.8),
            mpu_gyro=(0.1, 0.2, 0.3),
            adxl_accel=(1.0, 2.0, 9.8),
            gravity_mag=9.8
        )
    
    read_count = [0]
    write_count = [0]
    
    def reader():
        for _ in range(500):
            view.get_latest(10)
            read_count[0] += 1
    
    def writer():
        for i in range(500):
            buffer.add_sample(
                timestamp=5.0 + i * 0.01,
                mpu_accel=(1.0, 2.0, 9.8),
                mpu_gyro=(0.1, 0.2, 0.3),
                adxl_accel=(1.0, 2.0, 9.8),
                gravity_mag=9.8
            )
            write_count[0] += 1
    
    start = time.perf_counter()
    
    threads = [
        threading.Thread(target=reader),
        threading.Thread(target=reader),
        threading.Thread(target=writer),
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    
    elapsed = time.perf_counter() - start
    
    print(f"总耗时: {elapsed:.3f} s")
    print(f"读操作: {read_count[0]} 次")
    print(f"写操作: {write_count[0]} 次")
    print(f"总吞吐: {(read_count[0] + write_count[0])/elapsed:.0f} 操作/秒")
    print()


def benchmark_slots_access_speed():
    """测试 __slots__ 属性访问速度"""
    print("=" * 60)
    print("__slots__ 属性访问速度")
    print("=" * 60)
    
    rb = RingBuffer(100)
    
    def access_head():
        return rb._head
    
    def access_tail():
        return rb._tail
    
    def access_size():
        return rb._size
    
    num_calls = 1000000
    
    head_time = timeit.timeit(access_head, number=num_calls)
    tail_time = timeit.timeit(access_tail, number=num_calls)
    size_time = timeit.timeit(access_size, number=num_calls)
    
    print(f"访问 _head ({num_calls} 次): {head_time*1000:.2f} ms")
    print(f"访问 _tail ({num_calls} 次): {tail_time*1000:.2f} ms")
    print(f"访问 _size ({num_calls} 次): {size_time*1000:.2f} ms")
    print(f"平均单次访问: {head_time/num_calls*1000000:.3f} ns")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Phase 3 性能基准测试")
    print("=" * 60 + "\n")
    
    benchmark_memory_usage()
    benchmark_data_view_performance()
    benchmark_data_view_thread_safety()
    benchmark_slots_access_speed()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
