# -*- coding: utf-8 -*-
"""
DHT22传感器模块（基于adafruit-circuitpython-dht）
"""

import time
import board
import adafruit_dht
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DHT22Sensor:
    """DHT22温湿度传感器类（适配adafruit_dht）"""
    def __init__(self, config: Dict[str, Any]):
        """
        初始化DHT22传感器
        Args:
            config: 传感器配置字典
        """
        self.pin = config.get('pin', 26)
        self.retry_count = config.get('retry_count', 3)
        self.retry_delay = config.get('retry_delay', 2)
        # adafruit_dht 需要board.D{pin}对象
        board_pin = getattr(board, f"D{self.pin}")
        self.sensor = adafruit_dht.DHT22(board_pin)
        logger.info(f"初始化DHT22传感器: board.D{self.pin}")

    def read(self) -> Optional[Dict[str, float]]:
        """
        读取传感器数据，返回{'temperature': float, 'humidity': float}，失败返回None
        """
        for attempt in range(self.retry_count):
            try:
                temperature = self.sensor.temperature
                humidity = self.sensor.humidity
                if temperature is not None and humidity is not None:
                    data = {
                        'temperature': round(temperature, 2),
                        'humidity': round(humidity, 2)
                    }
                    logger.debug(f"传感器数据读取成功: {data}")
                    return data
                else:
                    logger.warning(f"传感器数据读取失败，尝试 {attempt + 1}/{self.retry_count}")
            except RuntimeError as e:
                logger.warning(f"读取传感器数据时发生错误: {e}，尝试 {attempt + 1}/{self.retry_count}")
            except Exception as e:
                logger.error(f"读取传感器数据时发生致命错误: {e}")
                break
            if attempt < self.retry_count - 1:
                time.sleep(self.retry_delay)
        logger.error("所有重试都失败了，无法读取传感器数据")
        return None

    def exit(self):
        """释放传感器资源"""
        try:
            self.sensor.exit()
        except AttributeError:
            pass

    def get_sensor_info(self) -> Dict[str, Any]:
        """获取传感器信息"""
        return {
            'type': 'DHT22',
            'pin': self.pin,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay
        } 