# -*- coding: utf-8 -*-
"""
DHT22发布者模块
改造为统一传感器数据格式
"""

import logging
import sys
import os
from typing import Dict, Any
import time

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from sensor_base import SensorBase
from sensor import DHT22Sensor

logger = logging.getLogger(__name__)

class DHT22Publisher(SensorBase):
    """DHT22温湿度传感器发布者 - 统一数据格式"""

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
        self.sensor_type = config.get('sensor_type', 'temperature_humidity')
        self.publish_interval = config.get('publish_interval', 30)
        
        logger.info("DHT22发布者初始化完成")

    def publish_cycle(self):
        """发布周期 - 实现具体的DHT22数据发布逻辑"""
        # 读取传感器数据
        data = self.sensor.read()

        if data:
            # 构建标准化的温湿度数据
            temp_humidity_data = {
                "temperature": data['temperature'],
                "humidity": data['humidity'],
                "timestamp": data.get('timestamp', int(time.time()))
            }
            
            # 发布传感器数据
            self.publish_sensor_data(temp_humidity_data, retain=True)
            logger.info(f"已发布温湿度数据: 温度={data['temperature']}°C, 湿度={data['humidity']}%")        
        else:
            logger.warning("跳过本次发布，传感器数据读取失败")

    def run(self):
        """运行发布者"""
        if not self.connect():
            logging.error("无法连接到MQTT代理，退出")
            return

        self.running = True
        logging.info(f"周期性发布者已启动，发布间隔: {self.publish_interval}秒")
        
        try:
            while self.running:
                self.publish_cycle()
                time.sleep(self.publish_interval)
        except KeyboardInterrupt:
            logging.info("收到键盘中断信号")
        except Exception as e:
            logging.error(f"运行过程中发生错误: {e}")
        finally:
            self.stop()

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