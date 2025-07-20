# -*- coding: utf-8 -*-
"""
DHT22 温湿度传感器 MQTT 发布者
基于 Raspberry Pi 5 的 MQTT 发布/订阅架构
"""

import logging
import sys
import os
from typing import Dict, Any, Optional
import Adafruit_DHT

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from mqtt_base import MQTTPublisher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DHT22Publisher(MQTTPublisher):
    """DHT22 温湿度传感器发布者"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化发布者
        
        Args:
            config: 配置字典，包含MQTT和传感器参数
        """
        super().__init__(config)
        
        # DHT22 传感器配置
        self.sensor = Adafruit_DHT.DHT22
        self.pin = config.get('dht22_pin', 4)  # GPIO4
    

    
    def read_dht22_data(self) -> Optional[Dict[str, float]]:
        """
        读取DHT22传感器数据
        
        Returns:
            包含温度和湿度的字典，读取失败时返回None
        """
        try:
            humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
            
            if humidity is not None and temperature is not None:
                return {
                    'temperature': round(temperature, 2),
                    'humidity': round(humidity, 2)
                }
            else:
                logger.warning("无法读取DHT22传感器数据")
                return None
                
        except Exception as e:
            logger.error(f"读取DHT22数据时发生错误: {e}")
            return None
    
    def publish_cycle(self):
        """发布周期 - 实现具体的DHT22数据发布逻辑"""
        # 读取传感器数据
        data = self.read_dht22_data()
        
        if data:
            # 发布传感器数据
            self.publish_sensor_data('dht22', data)
            logger.info(f"已发布温湿度数据: 温度={data['temperature']}°C, 湿度={data['humidity']}%")
        else:
            logger.warning("跳过本次发布，传感器数据读取失败")

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    return {
        'mqtt_broker': 'localhost',
        'mqtt_port': 1883,
        'topic_prefix': 'sensor',
        'dht22_pin': 4,
        'publish_interval': 30
    }

def main():
    """主函数"""
    try:
        # 加载配置
        config = load_config()
        
        # 创建发布者实例
        publisher = DHT22Publisher(config)
        
        # 运行发布者
        publisher.run()
        
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 