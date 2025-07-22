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
from publish import ButtonPublisher, setup_logging

def main():
    try:
        config_manager = ConfigManager()
        config = config_manager.get_all_config()
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("启动Button按键事件传感器发布者...")
        publisher = ButtonPublisher(config)
        publisher.run()
    except FileNotFoundError as e:
        print(f"配置文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 