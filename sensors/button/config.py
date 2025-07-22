# -*- coding: utf-8 -*-
"""
配置管理模块（Button 按键传感器）
"""
import os
import configparser
from typing import Dict, Any

class ConfigManager:
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
            'topic_prefix': self.config.get('mqtt', 'topic_prefix')
        }

    def get_button_config(self) -> Dict[str, Any]:
        return {
            'button_gpio': self.config.getint('button', 'button_gpio'),
            'gpio_chip': self.config.getint('button', 'gpio_chip')
        }

    def get_all_config(self) -> Dict[str, Any]:
        config = {}
        config.update(self.get_mqtt_config())
        config.update(self.get_button_config())
        return config 