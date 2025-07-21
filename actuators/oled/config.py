# -*- coding: utf-8 -*-
"""
OLED 配置管理模块
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
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        self.config.read(self.config_file, encoding='utf-8')

    def get_mqtt_config(self) -> Dict[str, Any]:
        return {
            'broker': self.config.get('mqtt', 'broker'),
            'port': self.config.getint('mqtt', 'port'),
            'topic': self.config.get('mqtt', 'topic')
        }

    def get_oled_config(self) -> Dict[str, Any]:
        return {
            'i2c_port': self.config.getint('oled', 'i2c_port'),
            'address': int(self.config.get('oled', 'address'), 16),
            'driver': self.config.get('oled', 'driver'),
            'width': self.config.getint('oled', 'width'),
            'height': self.config.getint('oled', 'height')
        }

    def get_all_config(self) -> Dict[str, Any]:
        config = {}
        config.update(self.get_mqtt_config())
        config.update(self.get_oled_config())
        return config 