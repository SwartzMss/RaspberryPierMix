# -*- coding: utf-8 -*-
"""
DHT22发布者模块
专门处理MQTT发布逻辑
"""

import logging
import sys
import os
from typing import Dict, Any

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from mqtt_base import MQTTPublisher
from sensor import DHT22Sensor

logger = logging.getLogger(__name__)

class DHT22Publisher(MQTTPublisher):
    """DHT22温湿度传感器发布者"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化发布者
        
        Args:
            config: 配置字典，包含MQTT和传感器参数
        """
        super().__init__(config)
        
        # 初始化传感器
        sensor_config = {
            'pin': config.get('pin', 4),
            'sensor_type': config.get('sensor_type', 'temperature_humidity'),
            'retry_count': config.get('retry_count', 3),
            'retry_delay': config.get('retry_delay', 2)
        }
        
        self.sensor = DHT22Sensor(sensor_config)
        logger.info("DHT22发布者初始化完成")
    
    def publish_cycle(self):
        """发布周期 - 实现具体的DHT22数据发布逻辑"""
        # 读取传感器数据
        data = self.sensor.read()
        
        if data:
            # 发布传感器数据
            sensor_type = self.config.get('sensor_type', 'temperature_humidity')
            self.publish_sensor_data(sensor_type, data, retain=True)
            logger.info(f"已发布温湿度数据: 温度={data['temperature']}°C, 湿度={data['humidity']}%")
        else:
            logger.warning("跳过本次发布，传感器数据读取失败")
    
    def get_status(self) -> Dict[str, Any]:
        """获取发布者状态"""
        return {
            'sensor_info': self.sensor.get_sensor_info(),
            'mqtt_config': {
                'broker': self.broker_host,
                'port': self.broker_port,
                'topic_prefix': self.topic_prefix,
                'publish_interval': self.publish_interval
            }
        } 