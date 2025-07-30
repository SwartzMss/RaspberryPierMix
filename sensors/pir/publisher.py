# -*- coding: utf-8 -*-
"""
简化版 PIR发布者模块
只发布人体检测事件
"""

import logging
import sys
import os
import time
from typing import Dict, Any

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from mqtt_base import EventPublisher
from sensor import PIRSensor

logger = logging.getLogger(__name__)

class PIRPublisher(EventPublisher):
    """简化版 PIR红外传感器发布者"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化发布者"""
        super().__init__(config)
        
        # 传感器配置
        sensor_config = {
            'pin': config.get('pin', 23),
            'sensor_type': config.get('sensor_type', 'pir_motion'),
            'stabilize_time': config.get('stabilize_time', 60)
        }
        
        self.sensor = PIRSensor(sensor_config)
        self.sensor_type = config.get('sensor_type', 'pir_motion')
        
        logger.info("PIR发布者初始化完成（稳定期已完成）")
    
    def _on_motion_detected(self, motion_data: Dict[str, Any]):
        """人体检测回调函数 - 简化版，每次检测到都发布"""
        self.publish_sensor_data(self.sensor_type, motion_data, retain=False)
        logger.info(f"检测到人体，已发布: {motion_data}")
    
    def start_sensor(self):
        """启动传感器（稳定期已在初始化时完成）"""
        self.sensor.set_motion_callback(self._on_motion_detected)
        logger.info("PIR传感器已就绪，回调函数已设置")
    
    def run(self):
        """运行发布者"""
        if not self.connect():
            logger.error("无法连接到MQTT代理，退出")
            return
        
        # 启动传感器
        self.start_sensor()
        
        self.running = True
        logger.info("PIR人体检测发布者已启动，等待运动检测...")
        
        try:
            # 主循环
            while self.running:
                time.sleep(1)  # 保持主线程活跃
                
        except KeyboardInterrupt:
            logger.info("收到键盘中断信号")
        except Exception as e:
            logger.error(f"运行过程中发生错误: {e}")
        finally:
            logger.info("正在停止PIR传感器...")
            self.sensor.cleanup()
            self.stop()