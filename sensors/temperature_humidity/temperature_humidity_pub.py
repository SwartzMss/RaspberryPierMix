# -*- coding: utf-8 -*-
"""
温湿度传感器 MQTT 发布者主程序
基于 Raspberry Pi 5 的 MQTT 发布/订阅架构
"""

import logging
import sys
from typing import Dict, Any

from config import ConfigManager
from publisher import DHT22Publisher

def setup_logging() -> None:
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """主函数"""
    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.get_all_config()
        
        # 设置日志
        setup_logging()
        logger = logging.getLogger(__name__)
        
        logger.info("启动温湿度传感器发布者...")
        
        # 创建发布者实例
        publisher = DHT22Publisher(config)
        
        # 显示状态信息
        status = publisher.get_status()
        logger.info(f"传感器信息: {status['sensor_info']}")
        logger.info(f"MQTT配置: {status['mqtt_config']}")
        
        # 运行发布者
        publisher.run()
        
    except FileNotFoundError as e:
        print(f"配置文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 