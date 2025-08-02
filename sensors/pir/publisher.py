# -*- coding: utf-8 -*-
"""
简化版 PIR发布者模块
改造为统一传感器数据格式
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
    """简化版 PIR红外传感器发布者 - 统一数据格式"""

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
        """人体检测回调函数 - 统一数据格式"""
        try:
            # 构建标准化的PIR数据
            pir_data = {
                "motion": "detected",
                "timestamp": int(time.time())
            }
            
            # 发布传感器数据
            self.publish_sensor_data(pir_data, retain=True)
            logger.info(f"检测到人体，已发布: {pir_data}")
            
        except Exception as e:
            logger.error(f"处理PIR检测事件时发生错误: {e}")

    def init_sensor(self):
        """初始化传感器（稳定期已在初始化时完成）"""
        self.sensor.set_motion_callback(self._on_motion_detected)
        logger.info("PIR传感器已就绪，回调函数已设置")

    def cleanup_sensor(self):
        """清理传感器"""
        logger.info("PIR传感器已清理")

    def start(self):
        """启动发布者 - 使用父类的标准实现"""
        super().start()