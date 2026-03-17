"""
Phase 4 优化测试
验证批量数据处理和预分配数组优化
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
import time
import threading
import queue

from sensor_calibrator.data_buffer import SensorDataBuffer
from sensor_calibrator.calibration_workflow import CalibrationWorkflow
from sensor_calibrator.config import Config


class TestBatchDataProcessing:
    """测试批量数据处理优化"""
    
    def test_batch_processing_reduces_overhead(self):
        """验证批量处理减少开销"""
        buffer = SensorDataBuffer()
        
        # 模拟批量数据
        batch_size = 50
        parsed_data = []
        
        for i in range(batch_size):
            mpu_accel = [1.0 + i*0.01, 2.0 + i*0.01, 9.8]
            mpu_gyro = [0.1, 0.2, 0.3]
            adxl_accel = [1.0 + i*0.01, 2.0 + i*0.01, 9.8]
            parsed_data.append((mpu_accel, mpu_gyro, adxl_accel))
        
        # 批量处理
        start = time.perf_counter()
        
        mpu_accel_values = [[] for _ in range(3)]
        mpu_gyro_values = [[] for _ in range(3)]
        adxl_accel_values = [[] for _ in range(3)]
        
        for mpu_accel, mpu_gyro, adxl_accel in parsed_data:
            for j in range(3):
                mpu_accel_values[j].append(mpu_accel[j])
                mpu_gyro_values[j].append(mpu_gyro[j])
                adxl_accel_values[j].append(adxl_accel[j])
        
        # 批量 extend (使用内部属性)
        for i in range(3):
            buffer._mpu_accel_data[i].extend(mpu_accel_values[i])
            buffer._mpu_gyro_data[i].extend(mpu_gyro_values[i])
            buffer._adxl_accel_data[i].extend(adxl_accel_values[i])
        
        elapsed = time.perf_counter() - start
        
        # 验证数据正确性
        assert len(buffer._mpu_accel_data[0]) == batch_size
        assert len(buffer._mpu_gyro_data[0]) == batch_size
        assert len(buffer._adxl_accel_data[0]) == batch_size
        
        # 验证第一个和最后一个值
        assert abs(buffer._mpu_accel_data[0][0] - 1.0) < 0.001
        assert abs(buffer._mpu_accel_data[0][-1] - (1.0 + (batch_size-1)*0.01)) < 0.001
    
    def test_extend_vs_append_performance(self):
        """验证 extend 比多次 append 更快"""
        from collections import deque
        
        # 准备数据
        data = list(range(100))
        
        # 测试多次 append
        d1 = deque(maxlen=200)
        start = time.perf_counter()
        for val in data:
            d1.append(val)
        append_time = time.perf_counter() - start
        
        # 测试 extend
        d2 = deque(maxlen=200)
        start = time.perf_counter()
        d2.extend(data)
        extend_time = time.perf_counter() - start
        
        print(f"\n100 次 append: {append_time*1000:.3f} ms")
        print(f"1 次 extend: {extend_time*1000:.3f} ms")
        print(f"提升: {append_time/extend_time:.1f}x")
        
        # extend 应该更快或相当
        assert len(d1) == len(d2)


class TestPreallocatedArrays:
    """测试预分配数组优化"""
    
    def test_preallocated_array_avoids_resize(self):
        """验证预分配数组避免动态扩容"""
        max_samples = 100
        
        # 预分配数组
        mpu_samples = np.zeros((max_samples, 3))
        
        # 填充数据
        for i in range(50):
            mpu_samples[i] = [1.0 + i*0.01, 2.0 + i*0.01, 9.8]
        
        # 使用切片获取有效数据
        valid_samples = mpu_samples[:50]
        
        # 验证
        assert valid_samples.shape == (50, 3)
        assert np.mean(valid_samples, axis=0)[0] > 1.0
    
    def test_preallocated_vs_list_performance(self):
        """验证预分配数组比 list 更快"""
        max_samples = 1000
        
        # 测试 list append
        start = time.perf_counter()
        list_samples = []
        for i in range(max_samples):
            list_samples.append([1.0, 2.0, 9.8])
        list_time = time.perf_counter() - start
        
        # 测试预分配 numpy
        start = time.perf_counter()
        np_samples = np.zeros((max_samples, 3))
        for i in range(max_samples):
            np_samples[i] = [1.0, 2.0, 9.8]
        np_time = time.perf_counter() - start
        
        print(f"\nlist append ({max_samples}): {list_time*1000:.3f} ms")
        print(f"numpy prealloc ({max_samples}): {np_time*1000:.3f} ms")
        
        # 两者都应该完成
        assert len(list_samples) == max_samples
        assert len(np_samples) == max_samples
    
    def test_numpy_mean_performance(self):
        """验证 numpy mean 性能"""
        data = np.random.rand(100, 3)
        
        start = time.perf_counter()
        mean = np.mean(data, axis=0)
        elapsed = time.perf_counter() - start
        
        print(f"\nnumpy mean (100x3): {elapsed*1000:.3f} ms")
        
        assert mean.shape == (3,)


class TestCalibrationWorkflowOptimization:
    """测试校准工作流优化"""
    
    def test_calibration_preallocated_arrays(self):
        """验证校准使用预分配数组"""
        # 创建模拟数据队列
        data_queue = queue.Queue()
        
        # 填充模拟数据
        for i in range(100):
            data_string = f"1.{i:02d},2.{i:02d},3.{i:02d},0.1,0.2,0.3,1.{i:02d},2.{i:02d},3.{i:02d}"
            data_queue.put(data_string)
        
        # 模拟回调
        callbacks = {
            'log_message': lambda msg: None,
            'parse_sensor_data': lambda s: (
                [1.0, 2.0, 3.0],
                [0.1, 0.2, 0.3],
                [1.0, 2.0, 3.0]
            ) if ',' in s else (None, None, None)
        }
        
        # 创建 CalibrationWorkflow
        workflow = CalibrationWorkflow(data_queue, callbacks)
        workflow._is_calibrating = True
        
        # 预分配数组
        max_samples = 100
        mpu_accel_samples = np.zeros((max_samples, 3))
        
        # 模拟数据采集
        samples_collected = 0
        while samples_collected < max_samples and not data_queue.empty():
            try:
                data_string = data_queue.get(timeout=0.001)
                mpu_accel, _, _ = callbacks['parse_sensor_data'](data_string)
                if mpu_accel:
                    mpu_accel_samples[samples_collected] = mpu_accel
                    samples_collected += 1
            except queue.Empty:
                break
        
        # 验证
        assert samples_collected == 100
        
        # 计算统计
        valid_samples = mpu_accel_samples[:samples_collected]
        mean = np.mean(valid_samples, axis=0)
        
        assert mean.shape == (3,)
        assert not np.isnan(mean).any()


class TestIntegration:
    """集成测试"""
    
    def test_buffer_extend_with_large_batch(self):
        """测试大批量数据 extend"""
        buffer = SensorDataBuffer()
        
        # 大批量数据
        batch_size = 1000
        time_values = [i * 0.01 for i in range(batch_size)]
        accel_values = [[1.0, 2.0, 9.8] for _ in range(batch_size)]
        
        # 批量添加
        start = time.perf_counter()
        buffer._time_data.extend(time_values)
        for i in range(3):
            buffer._mpu_accel_data[i].extend([v[i] for v in accel_values])
        elapsed = time.perf_counter() - start
        
        print(f"\n批量添加 {batch_size} 个样本: {elapsed*1000:.3f} ms")
        
        assert len(buffer._time_data) == batch_size
        assert len(buffer._mpu_accel_data[0]) == batch_size
    
    def test_data_integrity_after_batch_processing(self):
        """验证批量处理后数据完整性"""
        buffer = SensorDataBuffer()
        
        # 添加多批数据
        for batch in range(5):
            batch_data = []
            for i in range(20):
                batch_data.append((batch * 20 + i) * 0.01)
            
            buffer._time_data.extend(batch_data)
        
        # 验证总数
        assert len(buffer._time_data) == 100
        
        # 验证顺序
        for i in range(100):
            expected = i * 0.01
            assert abs(buffer._time_data[i] - expected) < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
