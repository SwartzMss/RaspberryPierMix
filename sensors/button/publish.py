import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

# -*- coding: utf-8 -*-
"""
Button 按键事件传感器 MQTT 发布者逻辑（gpiozero实现）
改造为统一传感器数据格式
"""
import logging
import time
import threading
from gpiozero import Button
from mqtt_base import EventPublisher

class ButtonPublisher(EventPublisher):
    """Button按键事件发布者 - 统一数据格式"""

    def __init__(self, config):
        super().__init__(config)
        
        # Button配置
        self.button_pin = config.get('button_pin', 17)
        self.bounce_time = config.get('bounce_time', 0.05)
        
        # 初始化Button
        self.button = Button(self.button_pin, bounce_time=self.bounce_time)
        
        # 监控控制
        self.monitoring = True
        self.monitor_thread = None
        
        logging.info("ButtonPublisher 初始化完成 (gpiozero)")

    def _on_button_pressed(self):
        """按钮按下回调"""
        try:
            # 构建标准化的按钮数据
            button_data = {
                "action": "pressed"
            }
            
            # 发布传感器数据
            self.publish_sensor_data(button_data, retain=True)
            
        except Exception as e:
            logging.error(f"处理按钮按下事件时发生错误: {e}")

    def _on_button_released(self):
        """按钮释放回调"""
        try:
            # 构建标准化的按钮数据
            button_data = {
                "action": "released"
            }
            
            # 发布传感器数据
            self.publish_sensor_data(button_data, retain=True)
            
        except Exception as e:
            logging.error(f"处理按钮释放事件时发生错误: {e}")

    def start_monitoring(self):
        """启动按钮监控"""
        # 设置按钮事件回调
        self.button.when_pressed = self._on_button_pressed
        self.button.when_released = self._on_button_released
        
        logging.info("Button监控已启动")

    def init_sensor(self):
        """初始化传感器 - 重写父类方法"""
        self.start_monitoring()

    def cleanup_sensor(self):
        """清理传感器 - 重写父类方法"""
        self.monitoring = False
        logging.info("Button监控已停止")

    def start(self):
        """启动发布者 - 使用父类的标准实现"""
        super().start()

def setup_logging() -> None:
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ) 