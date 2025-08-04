# -*- coding: utf-8 -*-
"""
界面显示任务模块
专门处理不同界面的显示事件发布
"""

import logging
import time
from typing import Dict, Any


class InterfaceDisplayTask:
    """界面显示任务 - 发布界面显示事件"""
    
    def __init__(self, oled_manager, config):
        self.oled_manager = oled_manager
        self.logger = logging.getLogger(__name__)
        self.logger.info("界面显示任务已启动")
    
    def show_motion_detected(self):
        """发布运动检测事件 - 切换到温湿度界面10分钟"""
        self.logger.info("发布运动检测事件")
        self._publish_interface_event('switch_to_temperature', {
            'message': 'Motion Detected!',
            'duration': 600  # 10分钟
        })
    
    def show_normal(self):
        """发布正常界面事件"""
        self.logger.info("发布正常界面事件")
        self._publish_interface_event('switch_to_normal', {
            'message': 'System Ready'
        })
    
    def show_custom(self, message: str, duration: int = None):
        """发布自定义界面事件"""
        self.logger.info(f"发布自定义界面事件: {message}")
        params = {'message': message}
        if duration:
            params['duration'] = duration
        self._publish_interface_event('switch_to_custom', params)
    
    def show_warning(self, message: str, duration: int = None):
        """发布警告界面事件"""
        self.logger.info(f"发布警告界面事件: {message}")
        params = {'message': message}
        if duration:
            params['duration'] = duration
        self._publish_interface_event('switch_to_warning', params)
    
    def show_info(self, message: str, duration: int = None):
        """发布信息界面事件"""
        self.logger.info(f"发布信息界面事件: {message}")
        params = {'message': message}
        if duration:
            params['duration'] = duration
        self._publish_interface_event('switch_to_info', params)
    
    def _publish_interface_event(self, action: str, params: Dict[str, Any]):
        """发布界面事件"""
        try:
            # 构建事件消息
            event_message = {
                "action": action,
                "params": {
                    **params,
                    "timestamp": time.time()
                }
            }
            
            # 发送界面事件
            self.oled_manager._send_oled_display_command(event_message)
            self.logger.debug(f"已发布界面事件: {action}")
                
        except Exception as e:
            self.logger.error(f"发布界面事件失败: {e}")
    
    def stop(self):
        """停止界面显示任务"""
        self.logger.info("界面显示任务已停止") 