import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
# -*- coding: utf-8 -*-
"""
Button 按键事件传感器 MQTT 发布者主程序
"""
import logging
import sys as _sys
from typing import Dict, Any

from config import ConfigManager
from button import ButtonSensor
from mqtt_base import MQTTPublisher

class ButtonPublisher(MQTTPublisher):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sensor = ButtonSensor(config)
        logging.info("ButtonPublisher 初始化完成")

    def publish_cycle(self):
        event = self.sensor.read()
        if event:
            self.publish_sensor_data('button', event, retain=False)
            logging.info(f"已发布按键事件: {event}")
        import time; time.sleep(0.05)

    def get_status(self) -> Dict[str, Any]:
        return {
            'sensor_info': self.sensor.get_sensor_info(),
            'mqtt_config': {
                'broker': self.broker_host,
                'port': self.broker_port,
                'topic_prefix': self.topic_prefix
            }
        }

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