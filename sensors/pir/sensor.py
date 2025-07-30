# -*- coding: utf-8 -*-
"""
简化版 PIR红外传感器模块
只处理人体检测事件
"""

import time
import logging
from typing import Dict, Any, Optional, Callable

try:
    from gpiozero import MotionSensor
except ImportError:
    # 在非树莓派环境下的模拟模块
    import warnings
    warnings.warn("gpiozero不可用，使用模拟模式")
    
    class MockMotionSensor:
        def __init__(self, pin):
            self.pin = pin
            self.when_motion = None
            self.motion_detected = False
        
        def close(self):
            pass
        
        @property
        def value(self):
            return self.motion_detected
    
    MotionSensor = MockMotionSensor

logger = logging.getLogger(__name__)

class PIRSensor:
    """简化版 PIR红外传感器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化PIR传感器"""
        self.pin = config.get('pin', 23)
        self.sensor_type = config.get('sensor_type', 'pir_motion')
        self.stabilize_time = config.get('stabilize_time', 60)
        
        # 只保留运动检测回调
        self.motion_callback: Optional[Callable] = None
        
        # 初始化传感器
        self.sensor = MotionSensor(self.pin)
        self.sensor.when_motion = self._on_motion_detected
        
        logger.info(f"初始化PIR传感器: Pin {self.pin}")
        
        # 让传感器稳定 - PIR传感器需要预热时间
        logger.info(f"PIR传感器稳定中，请等待约{self.stabilize_time}秒...")
        time.sleep(self.stabilize_time)
        logger.info("PIR传感器已就绪")
    
    def _on_motion_detected(self):
        """人体检测回调 - 简化版"""
        current_time = time.time()
        logger.info(f"检测到人体！时间: {time.strftime('%H:%M:%S', time.localtime(current_time))}")
        
        if self.motion_callback:
            try:
                motion_data = {
                    'motion_detected': True,
                    'timestamp': int(current_time)
                }
                self.motion_callback(motion_data)
            except Exception as e:
                logger.error(f"调用运动检测回调时发生错误: {e}")
    
    def set_motion_callback(self, callback: Callable):
        """设置运动检测回调函数"""
        self.motion_callback = callback
        logger.info("运动检测回调已设置")
    
    def cleanup(self):
        """清理资源"""
        try:
            self.sensor.close()
            logger.info("PIR传感器资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")