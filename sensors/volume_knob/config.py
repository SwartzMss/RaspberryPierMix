# -*- coding: utf-8 -*-
"""
音量旋钮配置管理模块
支持校准结果的持久化保存
"""

import os
import configparser
from typing import Dict, Any

class ConfigManager:
    """配置管理器 - 支持保存校准结果"""
    
    def __init__(self, config_file: str = "config.ini"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        
        self.config.read(self.config_file, encoding='utf-8')
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            raise IOError(f"保存配置文件失败: {e}")
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """获取MQTT配置"""
        return {
            'mqtt_broker': self.config.get('mqtt', 'broker'),
            'mqtt_port': self.config.getint('mqtt', 'port'),
            'topic_prefix': self.config.get('mqtt', 'topic_prefix')
        }
    
    def get_volume_knob_config(self) -> Dict[str, Any]:
        """获取音量旋钮配置"""
        return {
            'i2c_address': self.config.get('volume_knob', 'i2c_address'),
            'channel': self.config.getint('volume_knob', 'channel'),
            'gain': eval(self.config.get('volume_knob', 'gain')),  # 处理2/3这样的分数
            'min_voltage': self.config.getfloat('volume_knob', 'min_voltage'),
            'max_voltage': self.config.getfloat('volume_knob', 'max_voltage'),
            'min_volume': self.config.getint('volume_knob', 'min_volume'),
            'max_volume': self.config.getint('volume_knob', 'max_volume'),
            'volume_threshold': self.config.getint('volume_knob', 'volume_threshold'),
            'sensor_type': self.config.get('volume_knob', 'sensor_type'),
            'read_interval': self.config.getfloat('volume_knob', 'read_interval'),
            'stabilize_samples': self.config.getint('volume_knob', 'stabilize_samples')
        }
    
    def update_volume_calibration(self, min_voltage: float, max_voltage: float) -> None:
        """
        更新音量校准结果并保存到配置文件
        
        Args:
            min_voltage: 校准得到的最小电压
            max_voltage: 校准得到的最大电压
            
        Raises:
            ValueError: 如果校准值无效
        """
        # 验证校准值
        # 允许小的负电压值（通常是由于ADC偏移或噪声造成的）
        if min_voltage < -1.0 or max_voltage < -1.0:
            raise ValueError(f"无效的校准值（负电压过大）: {min_voltage:.3f}V - {max_voltage:.3f}V")
            
        if min_voltage >= max_voltage:
            raise ValueError(f"无效的校准值（最小值大于等于最大值）: {min_voltage:.3f}V >= {max_voltage:.3f}V")
            
        voltage_range = max_voltage - min_voltage
        if voltage_range < 0.5:
            raise ValueError(f"无效的校准值（电压范围过小）: {voltage_range:.3f}V")
            
        if voltage_range > 6.0:
            raise ValueError(f"无效的校准值（电压范围过大）: {voltage_range:.3f}V")
        
        # 更新配置对象中的值
        self.config.set('volume_knob', 'min_voltage', str(round(min_voltage, 3)))
        self.config.set('volume_knob', 'max_voltage', str(round(max_voltage, 3)))
        
        # 保存到文件
        self.save_config()
        
        print(f"\n✅ 校准结果已保存到 {self.config_file}")
        print(f"  min_voltage: {min_voltage:.3f}V")
        print(f"  max_voltage: {max_voltage:.3f}V")
        print(f"  电压范围: {voltage_range:.3f}V")
        print("\n✅ 校准完成！现在可以启动服务了：")
        print("   sudo systemctl start volume_knob-publisher")
        print("   sudo systemctl status volume_knob-publisher")
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        config = {}
        config.update(self.get_mqtt_config())
        config.update(self.get_volume_knob_config())
        return config