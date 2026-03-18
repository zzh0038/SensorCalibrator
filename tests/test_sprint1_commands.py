"""
Test Sprint 1 Commands

单元测试：Sprint 1 高优先级指令
- SET:KNS, SET:CMQ (云MQTT)
- SET:PO (位置配置)
- SET:ISG (安装模式)
- SS:11, SS:12, SS:27 (系统配置)
"""

import unittest


class TestCloudMQTTCommands(unittest.TestCase):
    """测试云 MQTT 命令 (SET:KNS, SET:CMQ)"""
    
    def test_build_kns_command_valid(self):
        """测试构建有效的 SET:KNS 命令"""
        from sensor_calibrator.network.cloud_mqtt import build_kns_command
        
        valid, error, cmd = build_kns_command(
            "ha9yyoY8xfJ",
            "ESP23_BHM_000003",
            "cfde2faeaf725ce185f16781ae58f6fc"
        )
        
        self.assertTrue(valid)
        self.assertEqual(error, "")
        self.assertEqual(cmd, "SET:KNS,ha9yyoY8xfJ,ESP23_BHM_000003,cfde2faeaf725ce185f16781ae58f6fc")
    
    def test_build_kns_command_invalid_product_key(self):
        """测试无效 ProductKey 的验证"""
        from sensor_calibrator.network.cloud_mqtt import build_kns_command
        
        # ProductKey 太短
        valid, error, cmd = build_kns_command("short", "device", "secret" * 8)
        self.assertFalse(valid)
        self.assertIn("ProductKey", error)
        
        # ProductKey 包含特殊字符
        valid, error, cmd = build_kns_command("key@123!", "device", "a" * 32)
        self.assertFalse(valid)
    
    def test_build_kns_command_invalid_device_secret(self):
        """测试无效 DeviceSecret 的验证"""
        from sensor_calibrator.network.cloud_mqtt import build_kns_command
        
        # DeviceSecret 长度不对
        valid, error, cmd = build_kns_command("ha9yyoY8xfJ", "device", "tooshort")
        self.assertFalse(valid)
        self.assertIn("DeviceSecret", error)
    
    def test_build_cmq_command_local(self):
        """测试构建局域网 MQTT 模式命令"""
        from sensor_calibrator.network.cloud_mqtt import build_cmq_command, MqttMode
        
        valid, error, cmd = build_cmq_command(MqttMode.LOCAL)
        
        self.assertTrue(valid)
        self.assertEqual(error, "")
        self.assertEqual(cmd, "SET:CMQ,1")
    
    def test_build_cmq_command_aliyun(self):
        """测试构建阿里云 MQTT 模式命令"""
        from sensor_calibrator.network.cloud_mqtt import build_cmq_command, MqttMode
        
        valid, error, cmd = build_cmq_command(MqttMode.ALIYUN)
        
        self.assertTrue(valid)
        self.assertEqual(error, "")
        self.assertEqual(cmd, "SET:CMQ,10")
    
    def test_build_cmq_command_invalid(self):
        """测试无效 MQTT 模式"""
        from sensor_calibrator.network.cloud_mqtt import build_cmq_command
        
        valid, error, cmd = build_cmq_command(99)
        self.assertFalse(valid)
        self.assertIn("Invalid MQTT mode", error)


class TestPositionConfigCommands(unittest.TestCase):
    """测试位置配置命令 (SET:PO)"""
    
    def test_build_po_command_valid(self):
        """测试构建有效的 SET:PO 命令"""
        from sensor_calibrator.network.position_config import build_po_command
        
        valid, error, cmd = build_po_command(
            "/Shandong/RiZhao/Juxian/Guanbao",
            "Zhuzhai",
            "Gonglisuo-201202",
            "HLSYZG-01010001"
        )
        
        self.assertTrue(valid)
        self.assertEqual(error, "")
        self.assertIn("SET:PO,", cmd)
        self.assertIn("/Shandong/RiZhao/Juxian/Guanbao", cmd)
        self.assertIn("Zhuzhai", cmd)
    
    def test_build_po_command_invalid_region(self):
        """测试无效行政区划路径"""
        from sensor_calibrator.network.position_config import build_po_command
        
        # 缺少 /
        valid, error, cmd = build_po_command(
            "Shandong/RiZhao", "Zhuzhai", "user", "device"
        )
        self.assertFalse(valid)
        
        # 层级太少
        valid, error, cmd = build_po_command(
            "/Shandong", "Zhuzhai", "user", "device"
        )
        self.assertFalse(valid)
        self.assertIn("at least 3 levels", error)
    
    def test_validate_region_path_valid(self):
        """测试有效的行政区划路径验证"""
        from sensor_calibrator.network.position_config import validate_region_path
        
        valid, error = validate_region_path("/Shandong/RiZhao/Juxian/Guanbao")
        self.assertTrue(valid)
        self.assertEqual(error, "")
    
    def test_parse_region_path(self):
        """测试行政区划路径解析"""
        from sensor_calibrator.network.position_config import parse_region_path
        
        parts = parse_region_path("/Shandong/RiZhao/Juxian/Guanbao")
        self.assertEqual(parts, ["Shandong", "RiZhao", "Juxian", "Guanbao"])


class TestInstallModeCommands(unittest.TestCase):
    """测试安装模式命令 (SET:ISG)"""
    
    def test_build_isg_command_default(self):
        """测试构建默认安装模式命令"""
        from sensor_calibrator.sensors.install_mode import build_isg_command, InstallMode
        
        valid, error, cmd = build_isg_command(InstallMode.DEFAULT)
        
        self.assertTrue(valid)
        self.assertEqual(error, "")
        self.assertEqual(cmd, "SET:ISG,0")
    
    def test_build_isg_command_ground(self):
        """测试构建地面安装模式命令"""
        from sensor_calibrator.sensors.install_mode import build_isg_command, InstallMode
        
        valid, error, cmd = build_isg_command(InstallMode.GROUND_1)
        
        self.assertTrue(valid)
        self.assertEqual(cmd, "SET:ISG,1")
    
    def test_build_isg_command_invalid(self):
        """测试无效安装模式"""
        from sensor_calibrator.sensors.install_mode import build_isg_command
        
        valid, error, cmd = build_isg_command(99)
        self.assertFalse(valid)
        self.assertIn("between 0 and 12", error)
        
        valid, error, cmd = build_isg_command(-1)
        self.assertFalse(valid)
    
    def test_get_mode_description(self):
        """测试获取模式描述"""
        from sensor_calibrator.sensors.install_mode import (
            get_mode_description, InstallMode
        )
        
        desc = get_mode_description(InstallMode.DEFAULT)
        self.assertIn("默认", desc)
        
        desc = get_mode_description(InstallMode.GROUND_1)
        self.assertIn("地面", desc)
    
    def test_get_mode_category(self):
        """测试获取模式分类"""
        from sensor_calibrator.sensors.install_mode import (
            get_mode_category, InstallMode
        )
        
        self.assertEqual(get_mode_category(InstallMode.DEFAULT), "default")
        self.assertEqual(get_mode_category(InstallMode.GROUND_1), "ground")
        self.assertEqual(get_mode_category(InstallMode.SIDE_1), "side")
        self.assertEqual(get_mode_category(InstallMode.TOP_1), "top")


class TestSystemConfigCommands(unittest.TestCase):
    """测试系统配置命令 (SS:11, SS:12, SS:27)"""
    
    def test_build_ss11_restore_default(self):
        """测试构建 SS:11 命令"""
        from sensor_calibrator.system.config_manager import build_ss11_restore_default
        
        cmd = build_ss11_restore_default()
        self.assertEqual(cmd, "SS:11")
    
    def test_build_ss12_save_sensor_config(self):
        """测试构建 SS:12 命令"""
        from sensor_calibrator.system.config_manager import build_ss12_save_sensor_config
        
        cmd = build_ss12_save_sensor_config()
        self.assertEqual(cmd, "SS:12")
    
    def test_build_ss27_deactivate(self):
        """测试构建 SS:27 命令"""
        from sensor_calibrator.system.config_manager import build_ss27_deactivate
        
        cmd = build_ss27_deactivate()
        self.assertEqual(cmd, "SS:27")
    
    def test_is_dangerous_action(self):
        """测试危险操作判断"""
        from sensor_calibrator.system.config_manager import (
            is_dangerous_action, ConfigAction
        )
        
        self.assertTrue(is_dangerous_action(ConfigAction.RESTORE_DEFAULT))
        self.assertTrue(is_dangerous_action(ConfigAction.DEACTIVATE))
        self.assertFalse(is_dangerous_action(ConfigAction.SAVE_SENSOR_CONFIG))


class TestProtocolConstants(unittest.TestCase):
    """测试协议常量定义"""
    
    def test_ss_constants(self):
        """测试 SS 命令常量值"""
        from sensor_calibrator.serial.protocol import (
            SS_CPU_MONITOR, SS_RESTORE_DEFAULT, SS_DEACTIVATE_SENSOR
        )
        
        self.assertEqual(SS_CPU_MONITOR, 5)
        self.assertEqual(SS_RESTORE_DEFAULT, 11)
        self.assertEqual(SS_DEACTIVATE_SENSOR, 27)
    
    def test_build_ss_commands(self):
        """测试 SS 命令构建函数"""
        from sensor_calibrator.serial.protocol import (
            build_ss5_cpu_monitor,
            build_ss11_restore_default,
            build_ss27_deactivate_sensor
        )
        
        self.assertEqual(build_ss5_cpu_monitor(), "SS:5")
        self.assertEqual(build_ss11_restore_default(), "SS:11")
        self.assertEqual(build_ss27_deactivate_sensor(), "SS:27")
    
    def test_ca_commands(self):
        """测试 CA 命令构建函数"""
        from sensor_calibrator.serial.protocol import (
            build_ca1_start_push_stream,
            build_ca9_reboot_camera_module
        )
        
        self.assertEqual(build_ca1_start_push_stream(), "CA:1")
        self.assertEqual(build_ca9_reboot_camera_module(), "CA:9")


class TestNetworkManagerIntegration(unittest.TestCase):
    """测试 NetworkManager 集成"""
    
    def test_network_manager_has_new_methods(self):
        """测试 NetworkManager 有新方法"""
        from sensor_calibrator.network_manager import NetworkManager
        
        # 检查新方法存在
        self.assertTrue(hasattr(NetworkManager, 'set_aliyun_mqtt_config'))
        self.assertTrue(hasattr(NetworkManager, 'set_mqtt_mode'))
        self.assertTrue(hasattr(NetworkManager, 'set_position_config'))
        self.assertTrue(hasattr(NetworkManager, 'set_install_mode'))


class TestUIManagerIntegration(unittest.TestCase):
    """测试 UIManager 集成 - Sprint 1 UI控件"""
    
    def test_ui_manager_has_new_methods(self):
        """测试 UIManager 有新的标签页设置方法"""
        from sensor_calibrator.ui_manager import UIManager
        
        # UI 重构后的5个主标签页方法
        self.assertTrue(hasattr(UIManager, '_setup_dashboard_tab'))
        self.assertTrue(hasattr(UIManager, '_setup_network_tab'))
        self.assertTrue(hasattr(UIManager, '_setup_sensors_tab'))
        self.assertTrue(hasattr(UIManager, '_setup_system_tab'))
        self.assertTrue(hasattr(UIManager, '_setup_calibration_tab'))
        
        # 二级标签页方法
        self.assertTrue(hasattr(UIManager, '_setup_cloud_tab'))
        self.assertTrue(hasattr(UIManager, '_setup_position_tab'))
        self.assertTrue(hasattr(UIManager, '_setup_wifi_tab'))
        self.assertTrue(hasattr(UIManager, '_setup_mqtt_tab'))
    
    def test_ui_manager_widgets_dict(self):
        """测试 UIManager 有新的控件引用"""
        from sensor_calibrator.ui_manager import UIManager
        import inspect
        
        # UI 重构后使用5个主标签页结构
        # Network 主标签页包含二级标签：WiFi/MQTT/Cloud/Position
        network_source = inspect.getsource(UIManager._setup_network_tab)
        self.assertIn('_setup_cloud_tab', network_source)
        self.assertIn('_setup_position_tab', network_source)
        
        # System 主标签页包含二级标签
        system_source = inspect.getsource(UIManager._setup_system_tab)
        self.assertIn('_setup_camera_tab', system_source)


class TestAppCallbacksIntegration(unittest.TestCase):
    """测试 AppCallbacks 集成 - Sprint 1 回调"""
    
    def test_callbacks_has_new_methods(self):
        """测试 AppCallbacks 有新的回调方法"""
        from sensor_calibrator.app.callback_groups import NetworkCallbacks, SystemCallbacks
        
        # 检查新方法存在于 Callback Groups
        self.assertIn('set_aliyun_mqtt_config', NetworkCallbacks.CALLBACK_NAMES)
        self.assertIn('set_mqtt_local_mode', NetworkCallbacks.CALLBACK_NAMES)
        self.assertIn('set_mqtt_aliyun_mode', NetworkCallbacks.CALLBACK_NAMES)
        self.assertIn('set_position_config', NetworkCallbacks.CALLBACK_NAMES)
        self.assertIn('set_install_mode', SystemCallbacks.CALLBACK_NAMES)
        self.assertIn('save_sensor_config', SystemCallbacks.CALLBACK_NAMES)
        self.assertIn('restore_default_config', SystemCallbacks.CALLBACK_NAMES)
        self.assertIn('deactivate_sensor', SystemCallbacks.CALLBACK_NAMES)


class TestModuleExports(unittest.TestCase):
    """测试模块导出"""
    
    def test_network_module_exports(self):
        """测试 network 模块导出"""
        from sensor_calibrator import network
        
        # 检查新的导出存在
        self.assertTrue(hasattr(network, 'build_kns_command'))
        self.assertTrue(hasattr(network, 'build_cmq_command'))
        self.assertTrue(hasattr(network, 'build_po_command'))
        self.assertTrue(hasattr(network, 'MqttMode'))
    
    def test_sensors_module_exports(self):
        """测试 sensors 模块导出"""
        from sensor_calibrator import sensors
        
        # 检查新的导出存在
        self.assertTrue(hasattr(sensors, 'InstallMode'))
        self.assertTrue(hasattr(sensors, 'build_isg_command'))
        self.assertTrue(hasattr(sensors, 'get_mode_description'))
    
    def test_system_module_exports(self):
        """测试 system 模块导出"""
        from sensor_calibrator import system
        
        # 检查新的导出存在
        self.assertTrue(hasattr(system, 'SystemConfigManager'))
        self.assertTrue(hasattr(system, 'build_ss11_restore_default'))
        self.assertTrue(hasattr(system, 'build_ss27_deactivate'))
        self.assertTrue(hasattr(system, 'ConfigAction'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
