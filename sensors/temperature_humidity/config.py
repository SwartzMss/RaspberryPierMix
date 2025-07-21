# -*- coding: utf-8 -*-
"""
配置管理模块
用于读取和解析传感器配置文件
"""

import os
import configparser
from typing import Dict, Any

class ConfigManager:
    """配置管理器"""
    
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
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """获取MQTT配置"""
        return {
            'mqtt_broker': self.config.get('mqtt', 'broker'),
            'mqtt_port': self.config.getint('mqtt', 'port'),
            'topic_prefix': self.config.get('mqtt', 'topic_prefix'),
            'publish_interval': self.config.getint('mqtt', 'publish_interval')
        }
    
    def get_dht22_config(self) -> Dict[str, Any]:
        """获取DHT22传感器配置"""
        return {
            'pin': self.config.getint('dht22', 'pin'),
            'temperature_humidity': self.config.get('dht22', 'temperature_humidity'),
            'retry_count': self.config.getint('dht22', 'retry_count'),
            'retry_delay': self.config.getint('dht22', 'retry_delay')
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        config = {}
        config.update(self.get_mqtt_config())
        config.update(self.get_dht22_config())
        return config 