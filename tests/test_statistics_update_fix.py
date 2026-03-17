"""
测试统计数据正确更新修复
验证批量处理时统计数据能随数据变化正确更新
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np

from sensor_calibrator.data_buffer import SensorDataBuffer


class TestStatisticsUpdateWithBatchProcessing:
    """测试批量处理时统计数据正确更新"""
    
    def test_data_version_increments_on_add_sample(self):
        """测试 add_sample 增加数据版本号"""
        buffer = SensorDataBuffer()
        
        initial_version = buffer._data_version
        
        buffer.add_sample(
            timestamp=0.0,
            mpu_accel=(1.0, 2.0, 9.8),
            mpu_gyro=(0.1, 0.2, 0.3),
            adxl_accel=(1.0, 2.0, 9.8),
            gravity_mag=9.8
        )
        
        assert buffer._data_version == initial_version + 1
        assert not buffer._stats_valid
    
    def test_statistics_cache_invalidated_on_data_change(self):
        """测试数据变化时统计缓存失效"""
        buffer = SensorDataBuffer()
        
        # 添加初始数据并计算统计
        for i in range(50):
            buffer.add_sample(
                timestamp=i * 0.01,
                mpu_accel=(1.0, 2.0, 9.8),
                mpu_gyro=(0.1, 0.2, 0.3),
                adxl_accel=(1.0, 2.0, 9.8),
                gravity_mag=9.8
            )
        
        stats1 = buffer.update_statistics()
        version1 = buffer._stats_version
        assert buffer._stats_valid
        
        # 添加新数据
        buffer.add_sample(
            timestamp=0.5,
            mpu_accel=(5.0, 5.0, 5.0),  # 显著不同的数据
            mpu_gyro=(1.0, 1.0, 1.0),
            adxl_accel=(5.0, 5.0, 5.0),
            gravity_mag=8.66
        )
        
        # 验证缓存已失效
        assert not buffer._stats_valid
        assert buffer._data_version > version1
        
        # 重新计算统计
        stats2 = buffer.update_statistics()
        
        # 统计数据应该变化
        assert stats1 != stats2
        assert stats2["mpu_accel_mean"][0] > stats1["mpu_accel_mean"][0]
    
    def test_direct_data_access_updates_version(self):
        """测试直接访问内部数据时版本号更新（模拟批量处理）"""
        buffer = SensorDataBuffer()
        
        # 添加初始数据
        for i in range(50):
            buffer.add_sample(
                timestamp=i * 0.01,
                mpu_accel=(1.0, 2.0, 9.8),
                mpu_gyro=(0.1, 0.2, 0.3),
                adxl_accel=(1.0, 2.0, 9.8),
                gravity_mag=9.8
            )
        
        stats1 = buffer.update_statistics()
        
        # 模拟批量处理：直接扩展内部数据
        buffer._time_data.extend([0.51, 0.52, 0.53])
        buffer._mpu_accel_data[0].extend([5.0, 5.0, 5.0])
        buffer._mpu_accel_data[1].extend([5.0, 5.0, 5.0])
        buffer._mpu_accel_data[2].extend([5.0, 5.0, 5.0])
        
        # 关键：手动更新版本号（这是批量处理代码应该做的）
        buffer._data_version += 1
        buffer._stats_valid = False
        
        # 重新计算统计
        stats2 = buffer.update_statistics()
        
        # 验证统计已更新
        assert stats2["mpu_accel_mean"][0] > stats1["mpu_accel_mean"][0]
    
    def test_statistics_accuracy_after_batch_update(self):
        """测试批量更新后统计准确性"""
        buffer = SensorDataBuffer()
        
        # 添加 100 个值为 1.0 的样本
        for i in range(100):
            buffer.add_sample(
                timestamp=i * 0.01,
                mpu_accel=(1.0, 1.0, 1.0),
                mpu_gyro=(0.1, 0.1, 0.1),
                adxl_accel=(1.0, 1.0, 1.0),
                gravity_mag=9.8
            )
        
        stats = buffer.update_statistics()
        
        # 均值应该接近 1.0
        assert abs(stats["mpu_accel_mean"][0] - 1.0) < 0.01
        assert abs(stats["mpu_accel_mean"][1] - 1.0) < 0.01
        assert abs(stats["mpu_accel_mean"][2] - 1.0) < 0.01
        
        # 标准差应该接近 0
        assert stats["mpu_accel_std"][0] < 0.01
    
    def test_consecutive_updates_without_data_change(self):
        """测试数据无变化时统计缓存有效"""
        buffer = SensorDataBuffer()
        
        # 添加数据
        for i in range(50):
            buffer.add_sample(
                timestamp=i * 0.01,
                mpu_accel=(1.0, 2.0, 9.8),
                mpu_gyro=(0.1, 0.2, 0.3),
                adxl_accel=(1.0, 2.0, 9.8),
                gravity_mag=9.8
            )
        
        # 第一次计算
        stats1 = buffer.update_statistics()
        version1 = buffer._stats_version
        
        # 第二次计算（数据无变化）
        stats2 = buffer.update_statistics()
        version2 = buffer._stats_version
        
        # 应该返回缓存，版本号不变
        assert version1 == version2
        assert stats1 == stats2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
