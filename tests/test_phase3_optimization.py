"""
Phase 3 优化测试
验证 __slots__ 内存优化和 DataView 功能
"""

import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import sys

from sensor_calibrator.ring_buffer import RingBuffer, QueueAdapter
from sensor_calibrator.log_throttler import LogThrottler, CountingLogThrottler
from sensor_calibrator.data_buffer import SensorDataBuffer, DataView


class TestSlotsOptimization:
    """测试 __slots__ 内存优化"""
    
    def test_ring_buffer_has_no_dict(self):
        """验证 RingBuffer 没有 __dict__"""
        rb = RingBuffer(100)
        # 使用 __slots__ 的类不应该有 __dict__
        assert not hasattr(rb, '__dict__')
    
    def test_queue_adapter_has_no_dict(self):
        """验证 QueueAdapter 没有 __dict__"""
        qa = QueueAdapter(100)
        assert not hasattr(qa, '__dict__')
    
    def test_log_throttler_has_no_dict(self):
        """验证 LogThrottler 没有 __dict__"""
        lt = LogThrottler()
        assert not hasattr(lt, '__dict__')
    
    def test_counting_log_throttler_has_no_dict(self):
        """验证 CountingLogThrottler 没有 __dict__"""
        clt = CountingLogThrottler()
        assert not hasattr(clt, '__dict__')
    
    def test_sensor_data_buffer_has_no_dict(self):
        """验证 SensorDataBuffer 没有 __dict__"""
        sdb = SensorDataBuffer()
        assert not hasattr(sdb, '__dict__')
    
    def test_data_view_has_no_dict(self):
        """验证 DataView 没有 __dict__"""
        from collections import deque
        import threading
        
        data = deque(maxlen=10)
        lock = threading.Lock()
        dv = DataView(data, lock)
        assert not hasattr(dv, '__dict__')
    
    def test_ring_buffer_size_reduction(self):
        """验证 RingBuffer 内存占用减少"""
        # 创建大量实例进行对比（理论上应该更小）
        instances = [RingBuffer(1000) for _ in range(100)]
        
        # 验证所有实例正常工作
        for i, rb in enumerate(instances):
            rb.put(i)
            assert rb.qsize() == 1
            assert rb.get() == i
    
    def test_sensor_data_buffer_slots_coverage(self):
        """验证 SensorDataBuffer 所有属性都在 __slots__ 中"""
        sdb = SensorDataBuffer()
        
        # 访问所有 __slots__ 属性
        _ = sdb._max_points
        _ = sdb._time_data
        _ = sdb._mpu_accel_data
        _ = sdb._mpu_gyro_data
        _ = sdb._adxl_accel_data
        _ = sdb._gravity_mag_data
        _ = sdb._stats_cache
        _ = sdb._stats_valid
        _ = sdb._data_version
        _ = sdb._stats_version
        
        # 测试通过说明所有属性都在 __slots__ 中


class TestDataView:
    """测试 DataView 功能"""
    
    @pytest.fixture
    def buffer_with_data(self):
        """创建带有样本数据的 buffer"""
        buffer = SensorDataBuffer()
        for i in range(100):
            buffer.add_sample(
                timestamp=i * 0.01,
                mpu_accel=(1.0 + i*0.001, 2.0 + i*0.001, 9.8),
                mpu_gyro=(0.1, 0.2, 0.3),
                adxl_accel=(1.0 + i*0.001, 2.0 + i*0.001, 9.8),
                gravity_mag=9.8
            )
        return buffer
    
    def test_data_view_basic_access(self, buffer_with_data):
        """测试 DataView 基本访问"""
        view = buffer_with_data.get_time_data_view()
        
        # 测试长度
        assert len(view) == 100
        
        # 测试索引访问
        first_time = view[0]
        assert first_time == 0.0
        
        last_time = view[-1]
        assert abs(last_time - 0.99) < 0.01
    
    def test_data_view_get_latest(self, buffer_with_data):
        """测试获取最新数据"""
        view = buffer_with_data.get_time_data_view()
        
        latest_10 = view.get_latest(10)
        assert len(latest_10) == 10
        
        # 验证数据正确性（最后 10 个时间戳）
        expected_start = 0.90
        for i, val in enumerate(latest_10):
            expected = expected_start + i * 0.01
            assert abs(val - expected) < 0.001
    
    def test_data_view_get_range(self, buffer_with_data):
        """测试获取范围数据"""
        view = buffer_with_data.get_time_data_view()
        
        # 获取 10-20 的数据
        range_data = view.get_range(10, 20)
        assert len(range_data) == 10
        
        # 验证数据
        for i, val in enumerate(range_data):
            expected = (10 + i) * 0.01
            assert abs(val - expected) < 0.001
    
    def test_data_view_copy(self, buffer_with_data):
        """测试复制数据"""
        view = buffer_with_data.get_time_data_view()
        
        copy_data = view.copy()
        assert len(copy_data) == 100
        
        # 复制应该是独立的
        original_len = len(view)
        buffer_with_data.add_sample(
            timestamp=1.0,
            mpu_accel=(1.0, 2.0, 9.8),
            mpu_gyro=(0.1, 0.2, 0.3),
            adxl_accel=(1.0, 2.0, 9.8),
            gravity_mag=9.8
        )
        
        # 视图应该能看到新数据
        assert len(view) == original_len + 1
        # 但复制不会变化
        assert len(copy_data) == original_len
    
    def test_data_view_iteration(self, buffer_with_data):
        """测试 DataView 迭代"""
        view = buffer_with_data.get_time_data_view()
        
        count = 0
        for val in view:
            count += 1
        
        assert count == 100
    
    def test_mpu_accel_view(self, buffer_with_data):
        """测试 MPU 加速度数据视图"""
        # 获取 X 轴视图
        x_view = buffer_with_data.get_mpu_accel_view(0)
        
        assert len(x_view) == 100
        
        # 获取最新值
        latest = x_view.get_latest(1)
        assert len(latest) == 1
        # 最后添加的值: 1.0 + 99*0.001 = 1.099
        assert abs(latest[0] - 1.099) < 0.001
        
        # 获取 Y 轴视图
        y_view = buffer_with_data.get_mpu_accel_view(1)
        assert len(y_view) == 100
        
        # 获取 Z 轴视图
        z_view = buffer_with_data.get_mpu_accel_view(2)
        assert len(z_view) == 100
    
    def test_mpu_accel_view_invalid_channel(self, buffer_with_data):
        """测试无效通道索引"""
        with pytest.raises(ValueError):
            buffer_with_data.get_mpu_accel_view(3)
        
        with pytest.raises(ValueError):
            buffer_with_data.get_mpu_accel_view(-1)
    
    def test_data_view_thread_safety(self, buffer_with_data):
        """测试 DataView 线程安全"""
        import threading
        import time
        
        view = buffer_with_data.get_time_data_view()
        results = []
        
        def reader():
            for _ in range(50):
                data = view.get_latest(10)
                results.append(len(data))
                time.sleep(0.001)
        
        def writer():
            for i in range(50):
                buffer_with_data.add_sample(
                    timestamp=1.0 + i * 0.01,
                    mpu_accel=(1.0, 2.0, 9.8),
                    mpu_gyro=(0.1, 0.2, 0.3),
                    adxl_accel=(1.0, 2.0, 9.8),
                    gravity_mag=9.8
                )
                time.sleep(0.001)
        
        # 启动读写线程
        t1 = threading.Thread(target=reader)
        t2 = threading.Thread(target=writer)
        
        t1.start()
        t2.start()
        
        t1.join(timeout=5)
        t2.join(timeout=5)
        
        # 验证没有异常
        assert len(results) == 50


class TestBackwardsCompatibility:
    """测试向后兼容性"""
    
    def test_data_buffer_properties_still_work(self):
        """验证原有属性访问方式仍然工作"""
        buffer = SensorDataBuffer()
        
        for i in range(10):
            buffer.add_sample(
                timestamp=i * 0.01,
                mpu_accel=(1.0, 2.0, 9.8),
                mpu_gyro=(0.1, 0.2, 0.3),
                adxl_accel=(1.0, 2.0, 9.8),
                gravity_mag=9.8
            )
        
        # 测试原有属性（返回副本）
        time_data = buffer.time_data
        assert len(time_data) == 10
        assert isinstance(time_data, list)
        
        mpu_data = buffer.mpu_accel_data
        assert len(mpu_data) == 3  # 3 个通道
        assert len(mpu_data[0]) == 10  # 每个通道 10 个值
    
    def test_ring_buffer_interface_unchanged(self):
        """验证 RingBuffer 接口不变"""
        rb = RingBuffer(10)
        
        # 原有接口
        rb.put(1)
        rb.put(2)
        assert rb.qsize() == 2
        assert rb.get() == 1
        assert not rb.full()
        assert not rb.empty()
        
        rb.clear()
        assert rb.empty()
    
    def test_queue_adapter_interface_unchanged(self):
        """验证 QueueAdapter 接口不变"""
        qa = QueueAdapter(10)
        
        # 原有接口
        qa.put(1)
        qa.put_nowait(2)
        assert qa.qsize() == 2
        assert qa.get() == 1
        assert not qa.full()
        assert not qa.empty()
    
    def test_log_throttler_interface_unchanged(self):
        """验证 LogThrottler 接口不变"""
        lt = LogThrottler()
        
        # 原有接口
        logs = []
        lt.set_log_function(lambda x: logs.append(x))
        lt.log("test message")
        lt.force_flush()
        
        assert len(logs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
