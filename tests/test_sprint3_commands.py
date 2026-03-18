"""
Test Sprint 3 Commands

单元测试：Sprint 3 相机相关指令
- SS:19-26 (相机控制)
- CA:1, CA:2, CA:9, CA:10 (相机专用指令)
"""

import unittest


class TestCameraControlCommands(unittest.TestCase):
    """测试相机控制命令"""
    
    def test_build_ss19_camera_mode_on(self):
        """测试 SS:19 开启拍照模式"""
        from sensor_calibrator.camera.camera_control import build_ss19_camera_mode
        self.assertEqual(build_ss19_camera_mode(True), "SS:19,1")
    
    def test_build_ss19_camera_mode_off(self):
        """测试 SS:19 关闭拍照模式"""
        from sensor_calibrator.camera.camera_control import build_ss19_camera_mode
        self.assertEqual(build_ss19_camera_mode(False), "SS:19,0")
    
    def test_build_ss21_monitoring_mode_on(self):
        """测试 SS:21 开启监测模式"""
        from sensor_calibrator.camera.camera_control import build_ss21_monitoring_mode
        self.assertEqual(build_ss21_monitoring_mode(True), "SS:21,1")
    
    def test_build_ss21_monitoring_mode_off(self):
        """测试 SS:21 关闭监测模式"""
        from sensor_calibrator.camera.camera_control import build_ss21_monitoring_mode
        self.assertEqual(build_ss21_monitoring_mode(False), "SS:21,0")
    
    def test_build_ss22_timelapse_mode_on(self):
        """测试 SS:22 开启时程传输模式"""
        from sensor_calibrator.camera.camera_control import build_ss22_timelapse_mode
        self.assertEqual(build_ss22_timelapse_mode(True), "SS:22,1")
    
    def test_build_ss23_reboot_camera_slave(self):
        """测试 SS:23 重启摄像机下位机"""
        from sensor_calibrator.camera.camera_control import build_ss23_reboot_camera_slave
        self.assertEqual(build_ss23_reboot_camera_slave(), "SS:23")
    
    def test_build_ss25_take_photo(self):
        """测试 SS:25 控制拍照"""
        from sensor_calibrator.camera.camera_control import build_ss25_take_photo
        self.assertEqual(build_ss25_take_photo(), "SS:25")
    
    def test_build_ss26_force_camera_ota(self):
        """测试 SS:26 强制摄像机OTA升级"""
        from sensor_calibrator.camera.camera_control import build_ss26_force_camera_ota
        self.assertEqual(build_ss26_force_camera_ota(), "SS:26")
    
    def test_build_ca2_take_photo(self):
        """测试 CA:2 控制拍照"""
        from sensor_calibrator.camera.camera_control import build_ca2_take_photo
        self.assertEqual(build_ca2_take_photo(), "CA:2")
    
    def test_build_ca9_reboot_camera_module(self):
        """测试 CA:9 重启摄像机模组"""
        from sensor_calibrator.camera.camera_control import build_ca9_reboot_camera_module
        self.assertEqual(build_ca9_reboot_camera_module(), "CA:9")
    
    def test_build_ca10_force_ota_upgrade(self):
        """测试 CA:10 强制ESP32 S3 OTA升级"""
        from sensor_calibrator.camera.camera_control import build_ca10_force_ota_upgrade
        self.assertEqual(build_ca10_force_ota_upgrade(), "CA:10")


class TestStreamCommands(unittest.TestCase):
    """测试视频流命令"""
    
    def test_build_ss24_start_camera_stream(self):
        """测试 SS:24 开启摄像机串流"""
        from sensor_calibrator.camera.stream import build_ss24_start_camera_stream
        self.assertEqual(build_ss24_start_camera_stream(), "SS:24")
    
    def test_build_ca1_start_push_stream(self):
        """测试 CA:1 开启相机推流"""
        from sensor_calibrator.camera.stream import build_ca1_start_push_stream
        self.assertEqual(build_ca1_start_push_stream(), "CA:1")
    
    def test_is_stream_command(self):
        """测试流命令识别"""
        from sensor_calibrator.camera.stream import is_stream_command
        self.assertTrue(is_stream_command("SS:24"))
        self.assertTrue(is_stream_command("CA:1"))
        self.assertFalse(is_stream_command("SS:0"))
        self.assertFalse(is_stream_command("CA:2"))
    
    def test_get_stream_type(self):
        """测试获取流类型"""
        from sensor_calibrator.camera.stream import get_stream_type, StreamType
        self.assertEqual(get_stream_type("SS:24"), StreamType.CAMERA_STREAM)
        self.assertEqual(get_stream_type("CA:1"), StreamType.PUSH_STREAM)
        self.assertIsNone(get_stream_type("SS:0"))


class TestCameraStateManager(unittest.TestCase):
    """测试相机状态管理器"""
    
    def test_initial_state(self):
        """测试初始状态"""
        from sensor_calibrator.camera.camera_control import CameraStateManager
        manager = CameraStateManager()
        status = manager.get_status()
        
        self.assertFalse(status['photo_mode'])
        self.assertFalse(status['monitoring_mode'])
        self.assertFalse(status['timelapse_mode'])
        self.assertFalse(status['streaming'])
        self.assertFalse(status['push_streaming'])
    
    def test_set_photo_mode(self):
        """测试设置拍照模式"""
        from sensor_calibrator.camera.camera_control import CameraStateManager
        manager = CameraStateManager()
        
        manager.set_photo_mode(True)
        self.assertTrue(manager.get_status()['photo_mode'])
        
        manager.set_photo_mode(False)
        self.assertFalse(manager.get_status()['photo_mode'])
    
    def test_set_monitoring_mode(self):
        """测试设置监测模式"""
        from sensor_calibrator.camera.camera_control import CameraStateManager
        manager = CameraStateManager()
        
        manager.set_monitoring_mode(True)
        self.assertTrue(manager.get_status()['monitoring_mode'])
    
    def test_reset(self):
        """测试重置状态"""
        from sensor_calibrator.camera.camera_control import CameraStateManager
        manager = CameraStateManager()
        
        manager.set_photo_mode(True)
        manager.set_monitoring_mode(True)
        manager.reset()
        
        status = manager.get_status()
        self.assertFalse(status['photo_mode'])
        self.assertFalse(status['monitoring_mode'])


class TestStreamManager(unittest.TestCase):
    """测试流管理器"""
    
    def test_initial_state(self):
        """测试初始状态"""
        from sensor_calibrator.camera.stream import StreamManager, StreamState
        # 不需要真实的 serial_manager 来测试初始状态
        manager = StreamManager(None)
        status = manager.get_status()
        
        self.assertEqual(status['camera_stream'], StreamState.STOPPED.value)
        self.assertEqual(status['push_stream'], StreamState.STOPPED.value)


class TestModuleExports(unittest.TestCase):
    """测试模块导出"""
    
    def test_camera_module_exports(self):
        """测试 camera 模块导出"""
        from sensor_calibrator import camera
        
        # 检查导出存在
        self.assertTrue(hasattr(camera, 'build_ss19_camera_mode'))
        self.assertTrue(hasattr(camera, 'build_ss24_start_camera_stream'))
        self.assertTrue(hasattr(camera, 'build_ca1_start_push_stream'))
        self.assertTrue(hasattr(camera, 'CameraController'))
        self.assertTrue(hasattr(camera, 'StreamManager'))
        self.assertTrue(hasattr(camera, 'CameraMode'))
        self.assertTrue(hasattr(camera, 'StreamType'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
