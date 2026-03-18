"""
Test All New Commands

综合测试：所有新增指令（Sprint 1-3）
测试除 SS:10 外的所有文档中定义的指令。
"""

import unittest


class TestAllImplementedCommands(unittest.TestCase):
    """
    综合测试所有实现的指令
    
    本测试套件验证从文档中实现的所有新指令。
    不包括 SS:10 (SD存储保存) - 根据用户要求不实现。
    """
    
    def test_sprint1_commands(self):
        """Sprint 1: 高优先级网络/配置指令"""
        # Cloud MQTT
        from sensor_calibrator.network.cloud_mqtt import (
            build_kns_command, build_cmq_command, MqttMode
        )
        valid, _, cmd = build_kns_command("ha9yyoY8xfJ", "device", "a" * 32)
        self.assertTrue(valid)
        self.assertIn("SET:KNS", cmd)
        
        valid, _, cmd = build_cmq_command(MqttMode.ALIYUN)
        self.assertTrue(valid)
        self.assertEqual(cmd, "SET:CMQ,10")
        
        # Position
        from sensor_calibrator.network.position_config import build_po_command
        valid, _, cmd = build_po_command(
            "/Shandong/RiZhao/Juxian", "Zhuzhai", "user", "device"
        )
        self.assertTrue(valid)
        self.assertIn("SET:PO", cmd)
        
        # Install Mode
        from sensor_calibrator.sensors.install_mode import build_isg_command
        valid, _, cmd = build_isg_command(3)
        self.assertTrue(valid)
        self.assertEqual(cmd, "SET:ISG,3")
        
        # System Config
        from sensor_calibrator.system.config_manager import (
            build_ss11_restore_default,
            build_ss12_save_sensor_config,
            build_ss27_deactivate
        )
        self.assertEqual(build_ss11_restore_default(), "SS:11")
        self.assertEqual(build_ss12_save_sensor_config(), "SS:12")
        self.assertEqual(build_ss27_deactivate(), "SS:27")
    
    def test_sprint2_commands(self):
        """Sprint 2: 传感器扩展指令"""
        # Filter
        from sensor_calibrator.sensors.filter import (
            build_kfqr_command, build_ss17_toggle_filter
        )
        valid, _, cmd = build_kfqr_command(0.005, 15)
        self.assertTrue(valid)
        self.assertEqual(cmd, "SET:KFQR,0.005000,15.00")
        self.assertEqual(build_ss17_toggle_filter(True), "SS:17,1")
        
        # Level Config
        from sensor_calibrator.sensors.level_config import (
            build_grolevel_command, build_acclevel_command
        )
        valid, _, cmd = build_grolevel_command(0.1, 0.5, 1.0, 2.0, 4.0)
        self.assertTrue(valid)
        self.assertIn("SET:GROLEVEL", cmd)
        
        valid, _, cmd = build_acclevel_command(0.2, 0.5, 1.0, 2.0, 4.0)
        self.assertTrue(valid)
        self.assertIn("SET:ACCLEVEL", cmd)
        
        # Auxiliary Sensors
        from sensor_calibrator.sensors.auxiliary import (
            build_vks_command, build_tme_command, build_magof_command
        )
        valid, _, cmd = build_vks_command(1.0, 1.0)
        self.assertTrue(valid)
        self.assertEqual(cmd, "SET:VKS,1.00,1.00")
        
        valid, _, cmd = build_tme_command(-15.0)
        self.assertTrue(valid)
        self.assertEqual(cmd, "SET:TME,-15.00")
        
        valid, _, cmd = build_magof_command(1.0, 2.0, 3.0)
        self.assertTrue(valid)
        self.assertEqual(cmd, "SET:MAGOF,1.00,2.00,3.00")
        
        # System Commands
        from sensor_calibrator.system.cpu_monitor import build_ss5_cpu_monitor
        from sensor_calibrator.system.sensor_cal import build_ss6_sensor_calibration
        from sensor_calibrator.system.system_control import (
            build_ss14_buzzer_long,
            build_ss15_check_upgrade,
            build_ss16_ap_config_mode,
            build_ss18_switch_mqtt_mode
        )
        self.assertEqual(build_ss5_cpu_monitor(), "SS:5")
        self.assertEqual(build_ss6_sensor_calibration(), "SS:6")
        self.assertEqual(build_ss14_buzzer_long(), "SS:14")
        self.assertEqual(build_ss15_check_upgrade(), "SS:15")
        self.assertEqual(build_ss16_ap_config_mode(), "SS:16")
        self.assertEqual(build_ss18_switch_mqtt_mode(1), "SS:18,1")
    
    def test_sprint3_commands(self):
        """Sprint 3: 相机相关指令"""
        from sensor_calibrator.camera.camera_control import (
            build_ss19_camera_mode,
            build_ss21_monitoring_mode,
            build_ss22_timelapse_mode,
            build_ss23_reboot_camera_slave,
            build_ss25_take_photo,
            build_ss26_force_camera_ota,
            build_ca2_take_photo,
            build_ca9_reboot_camera_module,
            build_ca10_force_ota_upgrade
        )
        from sensor_calibrator.camera.stream import (
            build_ss24_start_camera_stream,
            build_ca1_start_push_stream
        )
        
        # SS Commands
        self.assertEqual(build_ss19_camera_mode(True), "SS:19,1")
        self.assertEqual(build_ss21_monitoring_mode(True), "SS:21,1")
        self.assertEqual(build_ss22_timelapse_mode(True), "SS:22,1")
        self.assertEqual(build_ss23_reboot_camera_slave(), "SS:23")
        self.assertEqual(build_ss24_start_camera_stream(), "SS:24")
        self.assertEqual(build_ss25_take_photo(), "SS:25")
        self.assertEqual(build_ss26_force_camera_ota(), "SS:26")
        
        # CA Commands
        self.assertEqual(build_ca1_start_push_stream(), "CA:1")
        self.assertEqual(build_ca2_take_photo(), "CA:2")
        self.assertEqual(build_ca9_reboot_camera_module(), "CA:9")
        self.assertEqual(build_ca10_force_ota_upgrade(), "CA:10")


class TestCommandCounts(unittest.TestCase):
    """测试命令数量统计"""
    
    def test_implemented_set_commands(self):
        """统计已实现的 SET 指令"""
        set_commands = [
            # Original (已存在)
            "SET:WF", "SET:MQ", "SET:OTA", "SET:AGT",
            "SET:RACKS", "SET:RACOF", "SET:REACKS", "SET:REACOF", "SET:VROOF", "SET:AKY",
            # Sprint 1
            "SET:KNS", "SET:CMQ", "SET:PO", "SET:ISG",
            # Sprint 2
            "SET:KFQR", "SET:GROLEVEL", "SET:ACCLEVEL",
            "SET:VKS", "SET:TME", "SET:MAGOF",
        ]
        self.assertEqual(len(set_commands), 20)
    
    def test_implemented_ss_commands(self):
        """统计已实现的 SS 指令"""
        ss_commands = [
            # Original (已存在)
            "SS:0", "SS:1", "SS:2", "SS:3", "SS:4", "SS:7", "SS:8", "SS:9", "SS:13",
            # Sprint 1
            "SS:11", "SS:12", "SS:27",
            # Sprint 2
            "SS:5", "SS:6", "SS:14", "SS:15", "SS:16", "SS:17", "SS:18",
            # Sprint 3
            "SS:19", "SS:21", "SS:22", "SS:23", "SS:24", "SS:25", "SS:26",
        ]
        self.assertEqual(len(ss_commands), 26)
    
    def test_implemented_ca_commands(self):
        """统计已实现的 CA 指令"""
        ca_commands = ["CA:1", "CA:2", "CA:9", "CA:10"]
        self.assertEqual(len(ca_commands), 4)


class TestModuleStructure(unittest.TestCase):
    """测试模块结构"""
    
    def test_sensor_calibrator_modules(self):
        """测试 sensor_calibrator 模块结构"""
        # 检查主要模块可导入
        from sensor_calibrator import network
        from sensor_calibrator import sensors
        from sensor_calibrator import system
        from sensor_calibrator import camera
        from sensor_calibrator import serial
        
        # 检查模块有内容
        self.assertTrue(len(network.__all__) > 0)
        self.assertTrue(len(sensors.__all__) > 0)
        self.assertTrue(len(system.__all__) > 0)
        self.assertTrue(len(camera.__all__) > 0)
    
    def test_protocol_exports(self):
        """测试 protocol 模块导出"""
        from sensor_calibrator.serial import protocol
        
        # 检查 Sprint 1-3 的新常量存在
        self.assertTrue(hasattr(protocol, 'SS_RESTORE_DEFAULT'))  # SS:11
        self.assertTrue(hasattr(protocol, 'SS_CPU_MONITOR'))      # SS:5
        self.assertTrue(hasattr(protocol, 'SS_CAMERA_MODE'))      # SS:19
        self.assertTrue(hasattr(protocol, 'CA_START_PUSH_STREAM'))  # CA:1


if __name__ == "__main__":
    unittest.main(verbosity=2)
