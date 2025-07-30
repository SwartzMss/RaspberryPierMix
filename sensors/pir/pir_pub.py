# -*- coding: utf-8 -*-
"""
简化版 PIR红外传感器 MQTT 发布者
只发布人体检测事件
"""

import logging
import sys

from config import ConfigManager
from publisher import PIRPublisher

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
        
        logger.info("启动PIR人体检测发布者...")
        logger.info(f"传感器配置: Pin {config.get('pin')}, 稳定时间 {config.get('stabilize_time')}秒")
        logger.info(f"MQTT配置: {config.get('mqtt_broker')}:{config.get('mqtt_port')}, 主题前缀: {config.get('topic_prefix')}")
        
        # 创建发布者实例
        publisher = PIRPublisher(config)
        
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