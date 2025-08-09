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
    """加载配置文件并扁平化为程序需要的键名与类型"""
    parser = configparser.ConfigParser()
    parser.read(config_file, encoding='utf-8')

    cfg: Dict[str, Any] = {}

    # MQTT 配置
    if parser.has_section('mqtt'):
        cfg['mqtt_broker'] = parser.get('mqtt', 'broker', fallback='localhost')
        cfg['mqtt_port'] = parser.getint('mqtt', 'port', fallback=1883)
        cfg['topic_prefix'] = parser.get('mqtt', 'topic_prefix', fallback='actuator')

    # 音频配置
    if parser.has_section('audio'):
        cfg['card_index'] = parser.getint('audio', 'card_index', fallback=2)
        cfg['control_name'] = parser.get('audio', 'control_name', fallback='Headphone')
        cfg['audio_dir'] = parser.get('audio', 'audio_dir', fallback='./tmp')
        # 在线 TTS 配置（强制在线）
        cfg['edge_voice'] = parser.get('audio', 'edge_voice', fallback='zh-CN-XiaoxiaoNeural')
        cfg['edge_rate'] = parser.get('audio', 'edge_rate', fallback='+0%')
        cfg['edge_volume'] = parser.get('audio', 'edge_volume', fallback='+0%')

    return cfg

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