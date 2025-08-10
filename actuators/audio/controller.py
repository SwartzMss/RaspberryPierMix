# -*- coding: utf-8 -*-
"""音频执行器订阅者模块"""
import logging
import os
import sys
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from mqtt_base import MQTTSubscriber
from audio import AudioController

logger = logging.getLogger(__name__)

class AudioSubscriber(MQTTSubscriber):
    """订阅控制音频的MQTT消息"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 音频控制器配置
        audio_conf = {
            'card_index': config.get('card_index', 2),
            'control_name': config.get('control_name', 'Headphone'),
            'audio_dir': config.get('audio_dir', './tmp'),
            'gain_db': config.get('gain_db', 0.0),
        }
        
        # 实例化音频控制器
        self.audio = AudioController(audio_conf)
        
        # 订阅音频控制主题
        self.add_subscription(f"{self.topic_prefix}/audio")
        logger.info("音频订阅者初始化完成")

    def on_message(self, client, userdata, msg):
        """提升可观测性：打印收到的原始消息"""
        try:
            payload_preview = msg.payload.decode('utf-8', errors='ignore')
        except Exception:
            payload_preview = str(msg.payload)
        logger.info(f"收到消息: {msg.topic} -> {payload_preview}")
        super().on_message(client, userdata, msg)
    
    def handle_message(self, topic: str, payload: Dict[str, Any]):
        """处理音频控制消息"""
        action = payload.get('action')
        params = payload.get('params', {})
        logger.info(f"解析消息 action={action}, params={params}")
        
        if action == 'set_volume':
            volume = params.get('volume')
            if volume is not None:
                logger.info(f"准备设置音量: {volume}")
                success = self.audio.set_volume(int(volume))
                logger.info(f"设置音量: {volume}% - {'成功' if success else '失败'}")
            else:
                logger.warning("设置音量缺少volume参数")
        
        elif action == 'speak':
            text = params.get('text')
            if text:
                logger.info(f"准备播报: {text}")
                success = self.audio.speak_text(str(text))
                logger.info(f"播报文字: {text} - {'成功' if success else '失败'}")
            else:
                logger.warning("播报文字缺少text参数")
        
        elif action == 'stop':
            success = self.audio.stop_audio()
            logger.info(f"停止播报 - {'成功' if success else '失败'}")
        
        else:
            logger.warning(f"未知音频指令: {action}")
    
    def stop(self):
        """停止音频订阅者"""
        super().stop()
        try:
            self.audio.close()
        except Exception:
            pass 