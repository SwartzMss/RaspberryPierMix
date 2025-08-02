# -*- coding: utf-8 -*-
"""
传感器基础类
统一管理传感器数据发布，采用标准化的数据格式
"""

import json
import time
import logging
from typing import Dict, Any, Optional
from mqtt_base import MQTTBase

class SensorBase(MQTTBase):
    """传感器基础类，统一数据发布格式"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sensor_type = config.get('sensor_type', 'unknown')
        
    def publish_sensor_data(self, data: Dict[str, Any], retain: bool = False):
        """
        发布标准化的传感器数据
        
        Args:
            data: 传感器原始数据
            retain: 是否保留消息
        """
        try:
            # 构建标准化的传感器数据格式
            sensor_message = {
                "type": self.sensor_type,
                "params": data,
                "timestamp": int(time.time())
            }
            
            # 发布到统一的sensor topic
            topic = f"{self.topic_prefix}/sensor"
            self.publish_message(topic, sensor_message, retain=retain)
            
            logging.info(f"已发布传感器数据 [{self.sensor_type}]: {data}")
            
        except Exception as e:
            logging.error(f"发布传感器数据时发生错误: {e}")
    
    def get_sensor_info(self) -> Dict[str, Any]:
        """获取传感器信息 - 子类可重写"""
        return {
            "type": self.sensor_type,
            "status": "active"
        } 