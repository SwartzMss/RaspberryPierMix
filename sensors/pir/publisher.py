# -*- coding: utf-8 -*-
"""
PIR发布者模块
专门处理MQTT发布逻辑，使用事件驱动方式
"""

import logging
import sys
import os
import time
import threading
from typing import Dict, Any

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from mqtt_base import EventPublisher
from sensor import PIRSensor

logger = logging.getLogger(__name__)

class PIRPublisher(EventPublisher):
    """PIR红外传感器发布者（事件驱动）"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化发布者
        
        Args:
            config: 配置字典，包含MQTT和传感器参数
        """
        super().__init__(config)
        
        # 运动保持时间（避免频繁发送相同消息）
        self.motion_hold_time = config.get('motion_hold_time', 5)
        self.last_publish_time = 0
        
        # 无运动状态发布控制
        self.publish_no_motion = config.get('publish_no_motion', True)
        self.no_motion_delay = config.get('no_motion_delay', 300)
        self.no_motion_timer = None
        
        # 初始化传感器
        sensor_config = {
            'pin': config.get('pin', 23),
            'sensor_type': config.get('sensor_type', 'pir_motion')
        }
        
        self.sensor = PIRSensor(sensor_config)
        self.sensor_type = config.get('sensor_type', 'pir_motion')
        
        # 设置运动检测和无运动回调
        self.sensor.set_motion_callback(self._on_motion_detected)
        if self.publish_no_motion:
            self.sensor.set_no_motion_callback(self._on_no_motion_detected)
        else:
            logger.info("配置为不发布无运动状态，跳过无运动回调设置")
        
        logger.info("PIR发布者初始化完成")
    
    def _on_motion_detected(self, motion_data: Dict[str, Any]):
        """运动检测回调函数"""
        current_time = time.time()
        
        # 检查是否在保持时间内
        if current_time - self.last_publish_time < self.motion_hold_time:
            logger.debug(f"运动检测在保持时间内，跳过发布（剩余: {self.motion_hold_time - (current_time - self.last_publish_time):.1f}秒）")
            return
        
        # 发布运动检测数据
        self.publish_sensor_data(self.sensor_type, motion_data, retain=True)
        self.last_publish_time = current_time
        
        logger.info(f"已发布运动检测数据: {motion_data}")
        
    def _on_no_motion_detected(self, no_motion_data: Dict[str, Any]):
        """无运动检测回调函数"""
        if not self.publish_no_motion:
            logger.debug("无运动状态检测到，但配置为不发布，跳过")
            return
        
        # 发布无运动状态数据
        self.publish_sensor_data(self.sensor_type, no_motion_data, retain=False)
        logger.info(f"已发布无运动状态数据: {no_motion_data}")
    
    def start_sensor(self):
        """启动传感器（基于gpiozero，无需手动启动）"""
        logger.info("PIR传感器已就绪（gpiozero自动管理）")
    
    def stop_sensor(self):
        """停止传感器"""
        logger.info("PIR传感器停止中...")
    
    def run(self):
        """运行发布者"""
        if not self.connect():
            logger.error("无法连接到MQTT代理，退出")
            return
        
        # 启动传感器
        self.start_sensor()
        
        self.running = True
        logger.info("PIR事件驱动发布者已启动，等待运动检测...")
        
        try:
            # 发布初始状态
            initial_data = {
                'motion_detected': False,
                'timestamp': int(time.time()),
                'status': 'online'
            }
            self.publish_sensor_data(self.sensor_type, initial_data, retain=True)
            
            # 主循环
            while self.running:
                time.sleep(1)  # 保持主线程活跃
                
        except KeyboardInterrupt:
            logger.info("收到键盘中断信号")
        except Exception as e:
            logger.error(f"运行过程中发生错误: {e}")
        finally:
            # 发布离线状态
            offline_data = {
                'motion_detected': False,
                'timestamp': int(time.time()),
                'status': 'offline'
            }
            self.publish_sensor_data(self.sensor_type, offline_data, retain=True)
            
            self.stop_sensor()
            self.sensor.cleanup()
            self.stop()
    
    def get_status(self) -> Dict[str, Any]:
        """获取发布者状态"""
        return {
            'sensor_info': self.sensor.get_sensor_info(),
            'mqtt_config': {
                'broker': self.broker_host,
                'port': self.broker_port,
                'topic_prefix': self.topic_prefix,
                'motion_hold_time': self.motion_hold_time
            },
            'last_publish_time': self.last_publish_time
        }