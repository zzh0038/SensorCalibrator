#!/usr/bin/env python3
"""
SensorCalibrator Main Entry Point

主程序入口，启动传感器校准应用程序。
"""

import sys
from sensor_calibrator.app import SensorCalibratorApp


def main():
    """主函数"""
    try:
        app = SensorCalibratorApp()
        app.setup()
        app.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
