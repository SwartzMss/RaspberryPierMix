# -*- coding: utf-8 -*-
"""蜂鸣器订阅者模块"""
import logging
import os
import sys
import time
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from mqtt_base import MQTTSubscriber
from buzzer import SimpleBuzzer

logger = logging.getLogger(__name__)

class BuzzerSubscriber(MQTTSubscriber):
    """订阅控制蜂鸣器的MQTT消息"""
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        buzzer_conf = {
            'pin': config.get('pin', 18),
            'beep_duration': config.get('beep_duration', 0.2),
            'repeat': config.get('repeat', 1),
        }
        self.buzzer = SimpleBuzzer(buzzer_conf['pin'])
        self.beep_duration = buzzer_conf['beep_duration']
        self.repeat = buzzer_conf['repeat']
        self.add_subscription(f"{self.topic_prefix}/buzzer")
        logger.info("Buzzer订阅者初始化完成")

    def handle_message(self, topic: str, payload: Dict[str, Any]):
        cmd = payload.get('cmd', 'ON')
        if cmd.upper() == 'ON':
            duration = float(payload.get('duration', self.beep_duration))
            repeat = int(payload.get('repeat', self.repeat))
            logger.info(f"执行蜂鸣指令: duration={duration}, repeat={repeat}")
            self.buzzer.beep(duration=duration, repeat=repeat)
        else:
            logger.warning(f"未知指令: {cmd}")

    def stop(self):
        super().stop()
        try:
            self.buzzer.close()
        except Exception:
            pass
