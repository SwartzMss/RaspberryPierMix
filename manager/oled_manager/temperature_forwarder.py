# -*- coding: utf-8 -*-
"""
温湿度数据转发器模块
专门处理温湿度传感器数据的转发到OLED显示
"""

import logging
import time
from typing import Dict, Any


class TemperatureForwarder:
    """温湿度数据转发器 - 直接转发温湿度数据到OLED"""
    
    def __init__(self, oled_manager):
        self.oled_manager = oled_manager
        self.logger = logging.getLogger(__name__)
        self.logger.info("温湿度转发器已启动")
    
    def forward_temperature_humidity(self, temperature: float, humidity: float):
        """直接转发温湿度数据到OLED"""
        try:
            # 按照指定格式发送温湿度显示命令
            display_message = {
                "action": "update_temperature_humidity",
                "params": {
                    "temperature": temperature,
                    "humidity": humidity,
                    "timestamp": time.time()
                }
            }
            
            self.oled_manager._send_oled_display_command(display_message)
            self.logger.debug(f"转发温湿度数据: {temperature}°C, {humidity}%")
        except Exception as e:
            self.logger.error(f"转发温湿度数据失败: {e}")
    
    def stop(self):
        """停止温湿度转发器"""
        self.logger.info("温湿度转发器已停止") 