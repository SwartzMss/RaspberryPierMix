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
        action = payload.get('action')
        if action is True:
            params = payload.get('params', {})
            interval = float(params.get('interval', self.beep_duration))
            times = int(params.get('times', self.repeat))
            logger.info(
                f"执行蜂鸣指令: interval={interval}, times={times}")
            self.buzzer.beep(duration=interval, repeat=times)
        elif action is False:
            logger.info("停止蜂鸣指令")
            self.buzzer.stop()
        else:
            logger.warning(f"未知指令: {payload}")

    def stop(self):
        super().stop()
        try:
            self.buzzer.close()
        except Exception:
            pass
