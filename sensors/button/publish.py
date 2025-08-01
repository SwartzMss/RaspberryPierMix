import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
# -*- coding: utf-8 -*-
"""
Button 按键事件传感器 MQTT 发布者核心逻辑（gpiozero实现）
"""
import logging
import time
from gpiozero import Button
from config import ConfigManager
from mqtt_base import EventPublisher

class ButtonPublisher(EventPublisher):
    def __init__(self, config):
        super().__init__(config)
        self.button_gpio = int(config.get('button_gpio', 17))
        self.button = Button(self.button_gpio, pull_up=True, bounce_time=0.05)
        self.button.when_pressed = self.on_pressed
        logging.info("ButtonPublisher 初始化完成 (gpiozero)")

    def on_pressed(self):
        # 发布控制指令
        action_message = {
            "action": "button_pressed",
            "params": {
                "timestamp": int(time.time())
            }
        }
        topic = f"{self.topic_prefix}/common"
        self.publish_message(topic, action_message, retain=False)
        logging.info("已发布按键控制指令到MQTT")

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ) 