# -*- coding: utf-8 -*-
"""
传感器数据管理模块
处理传感器数据并发布业务逻辑相关的消息给执行器
"""

import logging
import json
import time
import sys
import os
from typing import Dict, Any

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from mqtt_base import MQTTSubscriber

class SensorManager(MQTTSubscriber):
    """传感器数据管理器 - 简单版本，无缓存"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 订阅统一的sensor主题
        self.add_subscription('sensor')
        
        # 传感器类型到执行器的映射
        self.sensor_to_actuator = {
            'temperature_humidity': 'oled',
            'pir_motion': 'oled',
            'button': 'buzzer',
            'potentiometer': 'audio'
        }
        
        self.logger = logging.getLogger(__name__)
    
    def handle_message(self, topic: str, payload: Dict[str, Any]):
        """处理接收到的传感器消息 - 统一转发"""
        try:
            # 从payload中获取传感器类型
            sensor_type = payload.get('type')
            if not sensor_type:
                self.logger.warning(f"消息中缺少传感器类型: {payload}")
                return
            
            # 获取传感器数据
            sensor_data = payload.get('params', {})
            
            self.logger.info(f"收到 {sensor_type} 数据: {sensor_data}")
            
            # 统一转发到对应的执行器
            self._forward_to_actuator(sensor_type, payload)
                
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")
    
    def _forward_to_actuator(self, sensor_type: str, payload: Dict[str, Any]):
        """统一转发传感器数据到对应的执行器"""
        # 获取对应的执行器
        actuator = self.sensor_to_actuator.get(sensor_type)
        if not actuator:
            self.logger.warning(f"未知传感器类型: {sensor_type}")
            return
        
        # 构建转发消息 - 只保留关键数据
        message = payload.get('params', {})
        
        # 发布到对应的执行器主题
        topic = f"actuator/{actuator}"
        self._publish_message(topic, message)
        
        self.logger.info(f"转发 {sensor_type} 数据到 {actuator}: {message}")
    
    def _publish_message(self, topic: str, message: Dict[str, Any]):
        """发布消息到指定主题"""
        try:
            payload = json.dumps(message, ensure_ascii=False)
            self.client.publish(topic, payload, qos=1)
            self.logger.debug(f"已发送到 {topic}: {message}")
        except Exception as e:
            self.logger.error(f"发送消息到 {topic} 失败: {e}")

def main():
    """主函数"""
    import configparser
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 读取配置
    config = configparser.ConfigParser()
    config.read('manager/config.ini')
    
    # 构建配置字典
    manager_config = {
        'mqtt_broker': config.get('mqtt', 'broker', fallback='localhost'),
        'mqtt_port': config.getint('mqtt', 'port', fallback=1883),
        'topic_prefix': config.get('mqtt', 'topic_prefix', fallback='sensor'),
        'sensor_type': 'manager'
    }
    
    # 创建并启动管理器
    manager = SensorManager(manager_config)
    
    try:
        manager.run()
    except KeyboardInterrupt:
        logging.info("收到中断信号，正在关闭管理器...")
    except Exception as e:
        logging.error(f"管理器运行出错: {e}")

if __name__ == "__main__":
    main() 