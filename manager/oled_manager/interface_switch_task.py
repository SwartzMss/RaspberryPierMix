# -*- coding: utf-8 -*-
"""
界面显示任务模块
专门处理不同界面的显示，如运动检测、警告等
"""

import logging
import threading
import time
from typing import Dict, Any


class InterfaceDisplayTask:
    """界面显示任务 - 处理不同界面的显示"""
    
    def __init__(self, oled_manager, config):
        self.oled_manager = oled_manager
        self.logger = logging.getLogger(__name__)
        
        # 从配置读取显示持续时间
        self.display_duration = config.getint('oled', 'switch_duration', fallback=5)
        self.auto_restore = config.getboolean('oled', 'auto_restore', fallback=True)
        
        # 当前界面状态
        self.current_interface = 'normal'
        
        self.logger.info("界面显示任务已启动")
    
    def show_motion_detected(self):
        """显示运动检测界面"""
        self.logger.info("显示运动检测界面")
        self._show_interface('motion_detected', 'Motion Detected!')
    
    def show_normal(self):
        """显示正常界面"""
        self.logger.info("显示正常界面")
        self._show_interface('normal', 'System Ready')
    
    def show_custom(self, message: str, duration: int = None):
        """显示自定义界面"""
        self.logger.info(f"显示自定义界面: {message}")
        self._show_interface('custom', message, duration)
    
    def show_warning(self, message: str, duration: int = None):
        """显示警告界面"""
        self.logger.info(f"显示警告界面: {message}")
        self._show_interface('warning', message, duration)
    
    def show_info(self, message: str, duration: int = None):
        """显示信息界面"""
        self.logger.info(f"显示信息界面: {message}")
        self._show_interface('info', message, duration)
    
    def show_error(self, message: str, duration: int = None):
        """显示错误界面"""
        self.logger.info(f"显示错误界面: {message}")
        self._show_interface('error', message, duration)
    
    def _show_interface(self, interface_type: str, message: str, duration: int = None):
        """显示指定界面"""
        try:
            # 构建消息格式
            display_message = {
                "action": "show_interface",
                "params": {
                    "interface": interface_type,
                    "message": message,
                    "timestamp": time.time()
                }
            }
            
            # 发送界面显示命令
            self.oled_manager._send_oled_display_command(display_message)
            
            # 设置定时器恢复正常界面
            if duration is None:
                duration = self.display_duration
            
            if interface_type != 'normal' and self.auto_restore:
                timer = threading.Timer(duration, self.show_normal)
                timer.start()
                self.logger.debug(f"设置 {duration} 秒后恢复正常界面")
                
        except Exception as e:
            self.logger.error(f"界面显示失败: {e}")
    
    def stop(self):
        """停止界面显示任务"""
        self.logger.info("界面显示任务已停止") 