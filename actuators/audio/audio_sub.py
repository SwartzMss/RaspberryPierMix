# -*- coding: utf-8 -*-
"""
音频执行器主程序
订阅MQTT消息控制USB音频设备
"""

import logging
import configparser
import os
import sys
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from controller import AudioSubscriber

def load_config(config_file: str) -> Dict[str, Any]:
    """加载配置文件"""
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')
    
    # 转换为字典格式
    config_dict = {}
    for section in config.sections():
        config_dict[section] = dict(config[section])
    
    return config_dict

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('audio_actuator.log', encoding='utf-8')
        ]
    )

def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 加载配置
        config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
        config = load_config(config_file)
        
        logger.info("音频执行器启动中...")
        
        # 创建音频订阅者
        subscriber = AudioSubscriber(config)
        
        # 运行订阅者
        subscriber.run()
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在退出...")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 