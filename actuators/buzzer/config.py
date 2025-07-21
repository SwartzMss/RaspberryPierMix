# -*- coding: utf-8 -*-
"""
蜂鸣器配置管理模块
"""
import os
import configparser
from typing import Dict, Any

class ConfigManager:
    """配置管理器"""
    def __init__(self, config_file: str = "config.ini"):
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
            'topic_prefix': self.config.get('mqtt', 'topic_prefix')
        }

    def get_buzzer_config(self) -> Dict[str, Any]:
        """获取蜂鸣器配置"""
        return {
            'pin': self.config.getint('buzzer', 'pin'),
            'beep_duration': self.config.getfloat('buzzer', 'beep_duration'),
            'repeat': self.config.getint('buzzer', 'repeat')
        }

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        config = {}
        config.update(self.get_mqtt_config())
        config.update(self.get_buzzer_config())
        return config
