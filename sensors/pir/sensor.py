# -*- coding: utf-8 -*-
"""
PIR红外传感器模块（基于gpiozero.MotionSensor）
参考用户示例代码实现
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
            self.when_no_motion = None
            self.motion_detected = False
        
        def close(self):
            pass
        
        @property
        def value(self):
            return self.motion_detected
    
    MotionSensor = MockMotionSensor

logger = logging.getLogger(__name__)

class PIRSensor:
    """PIR红外传感器类（基于gpiozero）"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化PIR传感器
        
        Args:
            config: 传感器配置字典
        """
        self.pin = config.get('pin', 18)
        self.sensor_type = config.get('sensor_type', 'pir_motion')
        
        # 状态跟踪
        self.motion_detected = False
        self.last_motion_time = 0
        self.last_no_motion_time = 0
        
        # 回调函数
        self.motion_callback: Optional[Callable] = None
        self.no_motion_callback: Optional[Callable] = None
        
        # 初始化传感器
        self.sensor = MotionSensor(self.pin)
        
        # 设置回调
        self.sensor.when_motion = self._on_motion_detected
        self.sensor.when_no_motion = self._on_no_motion_detected
        
        logger.info(f"初始化PIR传感器: Pin {self.pin}")
        
        # 让传感器稳定
        time.sleep(2)
        logger.info("PIR传感器已就绪")
    
    def _on_motion_detected(self):
        """运动检测回调"""
        current_time = time.time()
        self.motion_detected = True
        self.last_motion_time = current_time
        
        logger.info(f"检测到运动！时间: {time.strftime('%H:%M:%S', time.localtime(current_time))}")
        
        # 调用外部回调函数
        if self.motion_callback:
            try:
                motion_data = self.get_motion_data(motion_detected=True)
                self.motion_callback(motion_data)
            except Exception as e:
                logger.error(f"调用运动检测回调时发生错误: {e}")
    
    def _on_no_motion_detected(self):
        """无运动检测回调"""
        current_time = time.time()
        self.motion_detected = False
        self.last_no_motion_time = current_time
        
        logger.info(f"无运动状态，时间: {time.strftime('%H:%M:%S', time.localtime(current_time))}")
        
        # 调用外部回调函数
        if self.no_motion_callback:
            try:
                no_motion_data = self.get_motion_data(motion_detected=False)
                self.no_motion_callback(no_motion_data)
            except Exception as e:
                logger.error(f"调用无运动回调时发生错误: {e}")
    
    def get_motion_data(self, motion_detected: bool = None) -> Dict[str, Any]:
        """获取运动检测数据"""
        if motion_detected is None:
            motion_detected = self.motion_detected
        
        timestamp = self.last_motion_time if motion_detected else self.last_no_motion_time
        
        return {
            'motion_detected': motion_detected,
            'timestamp': int(timestamp)
        }
    
    def read_current_state(self) -> bool:
        """读取当前传感器状态"""
        try:
            return bool(self.sensor.value)
        except Exception as e:
            logger.error(f"读取传感器状态失败: {e}")
            return False
    
    def set_motion_callback(self, callback: Callable):
        """设置运动检测回调函数"""
        self.motion_callback = callback
        logger.info("运动检测回调已设置")
    
    def set_no_motion_callback(self, callback: Callable):
        """设置无运动检测回调函数"""
        self.no_motion_callback = callback
        logger.info("无运动检测回调已设置")
    
    def cleanup(self):
        """清理资源"""
        try:
            self.sensor.close()
            logger.info("PIR传感器资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")
    
    def get_sensor_info(self) -> Dict[str, Any]:
        """获取传感器信息"""
        return {
            'type': 'PIR',
            'pin': self.pin,
            'sensor_type': self.sensor_type,
            'current_state': self.read_current_state(),
            'last_motion_time': self.last_motion_time,
            'last_no_motion_time': self.last_no_motion_time
        }