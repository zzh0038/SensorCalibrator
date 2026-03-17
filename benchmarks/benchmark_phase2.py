"""
Phase 2 性能基准测试
验证锁竞争优化和统计缓存机制的效果
"""

import timeit
import time
import threading
import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_calibrator.data_buffer import SensorDataBuffer


def benchmark_cache_performance():
    """测试缓存性能提升"""
    print("=" * 60)
    print("统计缓存性能测试")
    print("=" * 60)
    
    buffer = SensorDataBuffer()
    
    # 填充数据
    print("填充 200 个样本...")
    for i in range(200):
        buffer.add_sample(
            timestamp=i * 0.01,
            mpu_accel=(1.0 + i*0.001, 2.0 + i*0.001, 9.8),
            mpu_gyro=(0.1, 0.2, 0.3),
            adxl_accel=(1.0 + i*0.001, 2.0 + i*0.001, 9.8),
            gravity_mag=9.8
        )
    
    # 测试 update_statistics
    print("\n--- update_statistics 性能 ---")
    
    # 第一次调用（无缓存）
    start = time.perf_counter()
    result1 = buffer.update_statistics()
    time_no_cache = time.perf_counter() - start
    print(f"无缓存 (第1次): {time_no_cache*1000:.3f} ms")
    
    # 后续调用（有缓存）
    times_with_cache = []
    for _ in range(10):
        start = time.perf_counter()
        result = buffer.update_statistics()
        times_with_cache.append(time.perf_counter() - start)
    
    avg_with_cache = sum(times_with_cache) / len(times_with_cache)
    print(f"有缓存 (平均):  {avg_with_cache*1000:.3f} ms")
    print(f"缓存提升:       {time_no_cache/avg_with_cache:.1f}x")
    
    # 验证缓存命中率
    assert result1 == result, "缓存结果应一致"
    print("[OK] 缓存结果验证通过")
    print()


def benchmark_calculate_statistics():
    """测试 calculate_statistics 性能"""
    print("=" * 60)
    print("calculate_statistics 性能测试")
    print("=" * 60)
    
    buffer = SensorDataBuffer()
    
    # 填充数据
    for i in range(200):
        buffer.add_sample(
            timestamp=i * 0.01,
            mpu_accel=(1.0 + i*0.001, 2.0 + i*0.001, 9.8),
            mpu_gyro=(0.1, 0.2, 0.3),
            adxl_accel=(1.0 + i*0.001, 2.0 + i*0.001, 9.8),
            gravity_mag=9.8
        )
    
    def calc_stats():
        return buffer.calculate_statistics()
    
    # 预热
    for _ in range(100):
        calc_stats()
    
    # 测试
    num_calls = 1000
    total_time = timeit.timeit(calc_stats, number=num_calls)
    
    print(f"{num_calls} 次调用耗时: {total_time*1000:.2f} ms")
    print(f"单次平均耗时: {total_time/num_calls*1000:.3f} ms")
    print(f"每秒可计算: {num_calls/total_time:.0f} 次")
    print()


def benchmark_concurrent_access():
    """测试并发访问性能"""
    print("=" * 60)
    print("并发访问性能测试")
    print("=" * 60)
    
    buffer = SensorDataBuffer()
    num_writes = 1000
    num_reads = 500
    
    write_times = []
    read_times = []
    
    def writer():
        for i in range(num_writes):
            start = time.perf_counter()
            buffer.add_sample(
                timestamp=i * 0.01,
                mpu_accel=(1.0, 2.0, 9.8),
                mpu_gyro=(0.1, 0.2, 0.3),
                adxl_accel=(1.0, 2.0, 9.8),
                gravity_mag=9.8
            )
            write_times.append(time.perf_counter() - start)
            time.sleep(0.0001)  # 模拟实际间隔
    
    def reader():
        for _ in range(num_reads):
            start = time.perf_counter()
            buffer.calculate_statistics()
            read_times.append(time.perf_counter() - start)
            time.sleep(0.0002)
    
    start = time.perf_counter()
    
    # 启动线程
    writer_thread = threading.Thread(target=writer)
    reader_thread = threading.Thread(target=reader)
    
    writer_thread.start()
    reader_thread.start()
    
    writer_thread.join()
    reader_thread.join()
    
    elapsed = time.perf_counter() - start
    
    avg_write = sum(write_times) / len(write_times) * 1000
    avg_read = sum(read_times) / len(read_times) * 1000
    
    print(f"总耗时: {elapsed:.3f} s")
    print(f"写入次数: {num_writes}, 平均耗时: {avg_write:.3f} ms")
    print(f"读取次数: {num_reads}, 平均耗时: {avg_read:.3f} ms")
    print(f"并发吞吐量: {(num_writes + num_reads)/elapsed:.0f} 操作/秒")
    print("[OK] 并发测试完成，无死锁或错误")
    print()


def benchmark_cache_invalidation():
    """测试缓存失效性能开销"""
    print("=" * 60)
    print("缓存失效性能测试")
    print("=" * 60)
    
    buffer = SensorDataBuffer()
    
    # 填充初始数据
    for i in range(100):
        buffer.add_sample(
            timestamp=i * 0.01,
            mpu_accel=(1.0, 2.0, 9.8),
            mpu_gyro=(0.1, 0.2, 0.3),
            adxl_accel=(1.0, 2.0, 9.8),
            gravity_mag=9.8
        )
    
    # 计算统计（建立缓存）
    buffer.update_statistics()
    
    # 添加新数据（使缓存失效）
    start = time.perf_counter()
    buffer.add_sample(
        timestamp=1.0,
        mpu_accel=(5.0, 5.0, 5.0),
        mpu_gyro=(1.0, 1.0, 1.0),
        adxl_accel=(5.0, 5.0, 5.0),
        gravity_mag=8.66
    )
    add_time = time.perf_counter() - start
    
    # 验证缓存已失效
    assert not buffer._stats_valid, "缓存应已失效"
    
    # 重新计算
    start = time.perf_counter()
    buffer.update_statistics()
    recalc_time = time.perf_counter() - start
    
    print(f"添加样本耗时: {add_time*1000:.3f} ms")
    print(f"重新计算耗时: {recalc_time*1000:.3f} ms")
    print(f"版本号变化: {buffer._data_version}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Phase 2 性能基准测试")
    print("=" * 60 + "\n")
    
    benchmark_cache_performance()
    benchmark_calculate_statistics()
    benchmark_concurrent_access()
    benchmark_cache_invalidation()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
