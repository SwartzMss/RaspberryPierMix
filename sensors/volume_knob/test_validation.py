#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试校准验证功能
"""

from sensor import VolumeKnobSensor
from config import ConfigManager

def test_invalid_calibration():
    """测试无效校准值被正确拒绝"""
    print("🧪 测试校准验证功能...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_all_config()
        
        print(f"当前配置: min_voltage={config['min_voltage']}, max_voltage={config['max_voltage']}")
        print("尝试创建传感器...")
        
        sensor = VolumeKnobSensor(config, config_manager)
        print("❌ 错误：应该拒绝无效配置但却成功了")
        return False
        
    except ValueError as e:
        print(f"✅ 正确拒绝无效配置: {e}")
        return True
        
    except Exception as e:
        print(f"⚠️  其他错误: {e}")
        return False

if __name__ == "__main__":
    success = test_invalid_calibration()
    if success:
        print("\n🎉 测试通过！校准验证功能正常工作")
    else:
        print("\n❌ 测试失败！校准验证功能有问题")
    
    print("\n💡 要使传感器正常工作，请先校准：")
    print("   python volume_pub.py --calibrate")