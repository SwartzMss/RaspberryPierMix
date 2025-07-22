import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
# -*- coding: utf-8 -*-
"""
Button 按键事件传感器 MQTT 发布者主程序（gpiozero实现）
"""
import logging
import time
from gpiozero import Button
from config import ConfigManager
from mqtt_base import MQTTPublisher

class ButtonPublisher(MQTTPublisher):
    def __init__(self, config):
        super().__init__(config)
        self.button_gpio = int(config.get('button_gpio', 17))
        self.button = Button(self.button_gpio, pull_up=True, bounce_time=0.05)
        self.button.when_pressed = self.on_pressed
        logging.info("ButtonPublisher 初始化完成 (gpiozero)")

    def on_pressed(self):
        payload = {
            "event": "pressed",
            "timestamp": int(time.time())
        }
        self.publish_sensor_data('button', payload, retain=False)
        logging.info("已发布按键事件到MQTT")

    def run(self):
        logging.info("ButtonPublisher 事件监听中...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    try:
        config_manager = ConfigManager()
        config = config_manager.get_all_config()
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("启动Button按键事件传感器发布者...")
        publisher = ButtonPublisher(config)
        status = publisher.get_status()
        logger.info(f"传感器信息: {status['sensor_info']}")
        logger.info(f"MQTT配置: {status['mqtt_config']}")
        publisher.run()
    except FileNotFoundError as e:
        print(f"配置文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 