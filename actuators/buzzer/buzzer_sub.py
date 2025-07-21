# -*- coding: utf-8 -*-
"""蜂鸣器 MQTT 订阅主程序"""
import logging
import sys
from config import ConfigManager
from controller import BuzzerSubscriber

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
        logger.info("启动蜂鸣器订阅者...")
        subscriber = BuzzerSubscriber(config)
        subscriber.run()
    except FileNotFoundError as e:
        print(f"配置文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
