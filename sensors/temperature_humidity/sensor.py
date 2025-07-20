# -*- coding: utf-8 -*-
"""
DHT22传感器模块
专门处理DHT22温湿度传感器的读取逻辑
"""

import time
import logging
from typing import Dict, Any, Optional
import Adafruit_DHT

logger = logging.getLogger(__name__)

class DHT22Sensor:
    """DHT22温湿度传感器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化DHT22传感器
        
        Args:
            config: 传感器配置字典
        """
        self.pin = config.get('pin', 4)
        self.sensor_type = config.get('sensor_type', 'DHT22')
        self.retry_count = config.get('retry_count', 3)
        self.retry_delay = config.get('retry_delay', 2)
        
        # 设置传感器类型
        if self.sensor_type.upper() == 'DHT22':
            self.sensor = Adafruit_DHT.DHT22
        elif self.sensor_type.upper() == 'DHT11':
            self.sensor = Adafruit_DHT.DHT11
        else:
            raise ValueError(f"不支持的传感器类型: {self.sensor_type}")
        
        logger.info(f"初始化DHT22传感器: GPIO{self.pin}")
    
    def read_data(self) -> Optional[Dict[str, float]]:
        """
        读取传感器数据
        
        Returns:
            包含温度和湿度的字典，读取失败时返回None
        """
        for attempt in range(self.retry_count):
            try:
                humidity, temperature = Adafruit_DHT.read_retry(
                    self.sensor, 
                    self.pin,
                    retries=1,
                    delay_seconds=self.retry_delay
                )
                
                if humidity is not None and temperature is not None:
                    data = {
                        'temperature': round(temperature, 2),
                        'humidity': round(humidity, 2)
                    }
                    logger.debug(f"传感器数据读取成功: {data}")
                    return data
                else:
                    logger.warning(f"传感器数据读取失败，尝试 {attempt + 1}/{self.retry_count}")
                    if attempt < self.retry_count - 1:
                        time.sleep(self.retry_delay)
                        
            except Exception as e:
                logger.error(f"读取传感器数据时发生错误: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        
        logger.error("所有重试都失败了，无法读取传感器数据")
        return None
    
    def get_sensor_info(self) -> Dict[str, Any]:
        """获取传感器信息"""
        return {
            'type': self.sensor_type,
            'pin': self.pin,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay
        } 