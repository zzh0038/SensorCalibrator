"""
校准UI增强功能测试

测试内容：
1. 2D可视化组件
2. 实时进度回调
3. 数据质量计算
4. 自动引导功能
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
import tkinter as tk


class TestCalibrationVisualizer2D:
    """测试2D可视化组件"""
    
    def test_position_definitions(self):
        """测试6个位置定义完整"""
        from sensor_calibrator.ui.calibration_visualizer import CalibrationVisualizer2D
        
        assert len(CalibrationVisualizer2D.POSITIONS) == 6
        
        # 检查每个位置都有必要的字段
        for pos in CalibrationVisualizer2D.POSITIONS:
            assert 'name' in pos
            assert 'down_axis' in pos
            assert 'view' in pos
            assert 'description' in pos
            assert 'tip' in pos
    
    def test_colors_defined(self):
        """测试颜色配置"""
        from sensor_calibrator.ui.calibration_visualizer import CalibrationVisualizer2D
        
        colors = CalibrationVisualizer2D.COLORS
        assert 'X' in colors
        assert 'Y' in colors
        assert 'Z' in colors
        assert 'sensor' in colors
        assert 'gravity' in colors


class TestCalibrationWorkflowEnhancements:
    """测试CalibrationWorkflow增强功能"""
    
    def test_quality_score_calculation(self):
        """测试质量评分计算"""
        import queue
        from sensor_calibrator.calibration_workflow import CalibrationWorkflow
        
        q = queue.Queue()
        workflow = CalibrationWorkflow(q, {})
        
        # 优秀 (std < 0.01)
        score = workflow._calculate_quality_score([0.005, 0.006, 0.004])
        assert 90 <= score <= 100
        
        # 良好 (std < 0.05)
        score = workflow._calculate_quality_score([0.03, 0.04, 0.02])
        assert 70 <= score < 90
        
        # 一般 (std < 0.1)
        score = workflow._calculate_quality_score([0.08, 0.07, 0.06])
        assert 50 <= score < 70
        
        # 差 (std >= 0.1)
        score = workflow._calculate_quality_score([0.2, 0.15, 0.18])
        assert score < 50
    
    def test_auto_advance_settings(self):
        """测试自动引导设置"""
        import queue
        from sensor_calibrator.calibration_workflow import CalibrationWorkflow
        
        q = queue.Queue()
        workflow = CalibrationWorkflow(q, {})
        
        # 默认关闭
        assert workflow.auto_advance == False
        
        # 启用自动引导
        workflow.set_auto_advance(True, 2.0)
        assert workflow.auto_advance == True
        assert workflow.auto_advance_delay == 2.0
        
        # 禁用自动引导
        workflow.set_auto_advance(False)
        assert workflow.auto_advance == False
    
    def test_pause_resume(self):
        """测试暂停/恢复功能"""
        import queue
        from sensor_calibrator.calibration_workflow import CalibrationWorkflow
        
        q = queue.Queue()
        workflow = CalibrationWorkflow(q, {})
        
        # 初始状态
        assert workflow._is_paused == False
        
        # 暂停
        workflow.pause()
        assert workflow._is_paused == True
        
        # 恢复
        workflow.resume()
        assert workflow._is_paused == False


class TestPositionIndicator:
    """测试位置指示器"""
    
    def test_status_colors(self):
        """测试状态颜色定义"""
        from sensor_calibrator.ui.calibration_visualizer import CalibrationPositionIndicator
        
        colors = CalibrationPositionIndicator.STATUS_COLORS
        assert 'pending' in colors
        assert 'collecting' in colors
        assert 'completed' in colors
        assert 'error' in colors


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
