"""
Phase 1 优化测试
验证 math.sqrt 替换和解析优化后的正确性
"""

import math
import numpy as np
import pytest
import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_calibrator.data_processor import DataProcessor
from sensor_calibrator.data_buffer import SensorDataBuffer


class TestSqrtOptimization:
    """测试 sqrt 优化（Task 1.1）"""
    
    def test_gravity_calculation_equivalence(self):
        """验证 math.sqrt 和 np.sqrt 结果一致"""
        test_cases = [
            [0.0, 0.0, 0.0],
            [1.0, 2.0, 3.0],
            [9.8, 0.1, 0.1],
            [-1.5, 2.5, -3.5],
            [1000.0, 2000.0, 3000.0],
        ]
        
        for accel in test_cases:
            expected = np.sqrt(accel[0]**2 + accel[1]**2 + accel[2]**2)
            actual = math.sqrt(accel[0]**2 + accel[1]**2 + accel[2]**2)
            
            assert abs(expected - actual) < 1e-10, \
                f"结果不一致: np={expected}, math={actual}"
    
    def test_gravity_calculation_edge_cases(self):
        """测试边界情况"""
        # 零值
        result = math.sqrt(0.0**2 + 0.0**2 + 0.0**2)
        assert result == 0.0
        
        # 极大值
        large = [1000.0, 2000.0, 3000.0]
        result = math.sqrt(large[0]**2 + large[1]**2 + large[2]**2)
        expected = np.sqrt(large[0]**2 + large[1]**2 + large[2]**2)
        assert abs(result - expected) < 1e-6


class TestParseOptimization:
    """测试解析优化（Task 1.2）"""
    
    @pytest.fixture
    def processor(self):
        return DataProcessor()
    
    @pytest.fixture
    def buffer(self):
        return SensorDataBuffer()
    
    def test_parse_valid_data(self, processor):
        """测试正常数据解析"""
        data = "1.23,2.34,3.45,4.56,5.67,6.78,7.89,8.90,9.01"
        mpu_a, mpu_g, adxl_a = processor.parse_sensor_data(data)
        
        assert mpu_a == [1.23, 2.34, 3.45]
        assert mpu_g == [4.56, 5.67, 6.78]
        assert adxl_a == [7.89, 8.90, 9.01]
    
    def test_parse_with_whitespace(self, processor):
        """测试带空格的解析"""
        data = "  1.0  ,  2.0  ,  3.0  ,  4.0  ,  5.0  ,  6.0  ,  7.0  ,  8.0  ,  9.0  "
        mpu_a, mpu_g, adxl_a = processor.parse_sensor_data(data)
        
        assert mpu_a == [1.0, 2.0, 3.0]
        assert mpu_g == [4.0, 5.0, 6.0]
        assert adxl_a == [7.0, 8.0, 9.0]
    
    def test_parse_invalid_values(self, processor):
        """测试无效值处理"""
        data = "invalid,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0"
        mpu_a, mpu_g, adxl_a = processor.parse_sensor_data(data)
        
        assert mpu_a[0] == 0.0  # invalid 转为 0.0
        assert mpu_a[1:] == [2.0, 3.0]
    
    def test_parse_empty_values(self, processor):
        """测试空值处理"""
        data = "1.0,,3.0,4.0,5.0,6.0,7.0,8.0,9.0"
        mpu_a, mpu_g, adxl_a = processor.parse_sensor_data(data)
        
        assert mpu_a == [1.0, 0.0, 3.0]  # 空值转为 0.0
    
    def test_parse_insufficient_data(self, processor):
        """测试数据不足"""
        data = "1.0,2.0,3.0,4.0,5.0"  # 只有 5 个值
        result = processor.parse_sensor_data(data)
        
        assert result == (None, None, None)
    
    def test_parse_empty_string(self, processor):
        """测试空字符串"""
        result = processor.parse_sensor_data("")
        assert result == (None, None, None)
    
    def test_parse_command_echo(self, processor):
        """测试命令回显过滤"""
        data = "SS:0"
        result = processor.parse_sensor_data(data)
        assert result == (None, None, None)
    
    def test_processor_and_buffer_parse_equivalence(self, processor, buffer):
        """验证 DataProcessor 和 SensorDataBuffer 解析结果一致"""
        data = "1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5"
        
        result1 = processor.parse_sensor_data(data)
        result2 = buffer.parse_sensor_data(data)
        
        assert result1 == result2


class TestIntegration:
    """集成测试"""
    
    def test_process_packet_with_optimization(self):
        """测试完整的数据包处理流程"""
        dp = DataProcessor()
        
        # 模拟 100 个数据包
        for i in range(100):
            data = f"{i}.0,{i+1}.0,{i+2}.0,{i+3}.0,{i+4}.0,{i+5}.0,{i+6}.0,{i+7}.0,{i+8}.0"
            result = dp.process_packet(data)
            
            assert result is not None
            assert 'gravity' in result
            assert result['gravity'] > 0  # 重力应该为正
        
        assert dp.get_data_count() == 100


class TestParseFloatSafe:
    """测试 _parse_float_safe 辅助函数"""
    
    def test_valid_float(self):
        """测试有效浮点数"""
        assert DataProcessor._parse_float_safe("3.14") == 3.14
        assert DataProcessor._parse_float_safe("  2.5  ") == 2.5
        assert DataProcessor._parse_float_safe("-1.5") == -1.5
        assert DataProcessor._parse_float_safe("100") == 100.0
    
    def test_invalid_float(self):
        """测试无效输入"""
        assert DataProcessor._parse_float_safe("invalid") == 0.0
        assert DataProcessor._parse_float_safe("") == 0.0
        assert DataProcessor._parse_float_safe("abc123") == 0.0
    
    def test_buffer_parse_float_safe(self):
        """测试 SensorDataBuffer 的静态方法"""
        assert SensorDataBuffer._parse_float_safe("3.14") == 3.14
        assert SensorDataBuffer._parse_float_safe("invalid") == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
