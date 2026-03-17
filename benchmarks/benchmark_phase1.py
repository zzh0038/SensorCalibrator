"""
Phase 1 性能基准测试
"""

import timeit
import numpy as np
import math
import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_calibrator.data_processor import DataProcessor


def benchmark_sqrt():
    """sqrt 性能对比"""
    print("=" * 50)
    print("sqrt 性能对比 (100万次调用)")
    print("=" * 50)
    
    setup_np = "import numpy as np; x = 1.5**2 + 2.5**2 + 9.8**2"
    setup_math = "import math; x = 1.5**2 + 2.5**2 + 9.8**2"
    
    np_time = timeit.timeit("np.sqrt(x)", setup=setup_np, number=1000000)
    math_time = timeit.timeit("math.sqrt(x)", setup=setup_math, number=1000000)
    
    print(f"np.sqrt:    {np_time*1000:.2f} ms")
    print(f"math.sqrt:  {math_time*1000:.2f} ms")
    print(f"提升:       {np_time/math_time:.2f}x")
    print()


def benchmark_parse():
    """解析性能测试"""
    print("=" * 50)
    print("解析性能测试")
    print("=" * 50)
    
    dp = DataProcessor()
    test_data = "1.23,2.34,3.45,4.56,5.67,6.78,7.89,8.90,9.01"
    
    def parse():
        return dp.parse_sensor_data(test_data)
    
    # 预热
    for _ in range(1000):
        parse()
    
    # 测试
    time = timeit.timeit(parse, number=100000)
    
    print(f"100000 次解析耗时: {time*1000:.2f} ms")
    print(f"单次耗时: {time*1000/100000*1000:.3f} μs")
    print(f"每秒可处理: {100000/time:.0f} 个数据包")
    print()


def benchmark_process_packet():
    """完整处理流程测试"""
    print("=" * 50)
    print("完整数据包处理测试")
    print("=" * 50)
    
    dp = DataProcessor()
    test_data = "1.23,2.34,3.45,4.56,5.67,6.78,7.89,8.90,9.01"
    
    def process():
        dp.process_packet(test_data)
    
    # 预热
    for _ in range(1000):
        process()
        dp.clear_all()
    
    # 测试
    dp.clear_all()
    time = timeit.timeit(process, number=10000)
    
    print(f"10000 次完整处理耗时: {time*1000:.2f} ms")
    print(f"单次耗时: {time*1000/10000*1000:.3f} μs")
    print(f"每秒可处理: {10000/time:.0f} 个数据包")
    print()


def benchmark_throughput():
    """吞吐量测试"""
    print("=" * 50)
    print("吞吐量模拟测试 (1秒)")
    print("=" * 50)
    
    dp = DataProcessor()
    test_data = "1.23,2.34,3.45,4.56,5.67,6.78,7.89,8.90,9.01"
    
    import time
    
    start = time.perf_counter()
    count = 0
    duration = 1.0  # 测试 1 秒
    
    while time.perf_counter() - start < duration:
        dp.process_packet(test_data)
        count += 1
        if count % 1000 == 0:
            dp.clear_all()  # 避免内存无限增长
    
    elapsed = time.perf_counter() - start
    print(f"1 秒内处理: {count} 个数据包")
    print(f"平均速率: {count/elapsed:.0f} 包/秒")
    print()


def benchmark_parse_comparison():
    """对比优化前后的解析性能"""
    print("=" * 50)
    print("解析方式对比")
    print("=" * 50)
    
    test_data = "1.23,2.34,3.45,4.56,5.67,6.78,7.89,8.90,9.01"
    
    # 旧版本：循环解析
    def parse_loop():
        parts = test_data.split(",")
        if len(parts) >= 9:
            values = []
            for part in parts[:9]:
                try:
                    values.append(float(part.strip()))
                except (ValueError, TypeError):
                    values.append(0.0)
            return values
    
    # 新版本：推导式解析
    def parse_comprehension():
        parts = test_data.split(",")
        if len(parts) >= 9:
            return [
                float(p.strip()) if p.strip() else 0.0
                for p in parts[:9]
            ]
    
    loop_time = timeit.timeit(parse_loop, number=100000)
    comp_time = timeit.timeit(parse_comprehension, number=100000)
    
    print(f"循环解析:     {loop_time*1000:.2f} ms (10万次)")
    print(f"推导式解析:   {comp_time*1000:.2f} ms (10万次)")
    print(f"提升:         {loop_time/comp_time:.2f}x")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Phase 1 性能基准测试")
    print("=" * 50 + "\n")
    
    benchmark_sqrt()
    benchmark_parse()
    benchmark_process_packet()
    benchmark_throughput()
    benchmark_parse_comparison()
    
    print("=" * 50)
    print("测试完成！")
    print("=" * 50)
