# -*- coding: utf-8 -*-
"""
界面切换任务模块
专门处理一次性的界面切换事件，如运动检测等
"""

import logging
import threading
import time
from typing import Dict, Any


class InterfaceSwitchTask:
    """界面切换任务 - 处理一次性的界面切换事件"""
    
    def __init__(self, oled_manager, config):
        self.oled_manager = oled_manager
        self.logger = logging.getLogger(__name__)
        
        # 从配置读取切换持续时间
        self.switch_duration = config.getint('oled', 'switch_duration', fallback=5)
        self.auto_restore = config.getboolean('oled', 'auto_restore', fallback=True)
        
        # 界面切换状态
        self.current_mode = 'normal'
        
        self.logger.info("界面切换任务已启动")
    
    def switch_to_motion_detected(self):
        """切换到运动检测界面"""
        self.logger.info("切换到运动检测界面")
        self._switch_interface('switch_to_motion', 'Motion Detected!')
    
    def switch_to_normal(self):
        """切换到正常界面"""
        self.logger.info("切换到正常界面")
        self._switch_interface('switch_to_normal', 'System Ready')
    
    def switch_to_custom(self, message: str, duration: int = None):
        """切换到自定义界面"""
        self.logger.info(f"切换到自定义界面: {message}")
        self._switch_interface('switch_to_custom', message, duration)
    
    def switch_to_warning(self, message: str, duration: int = None):
        """切换到警告界面"""
        self.logger.info(f"切换到警告界面: {message}")
        self._switch_interface('switch_to_warning', message, duration)
    
    def switch_to_info(self, message: str, duration: int = None):
        """切换到信息界面"""
        self.logger.info(f"切换到信息界面: {message}")
        self._switch_interface('switch_to_info', message, duration)
    
    def _switch_interface(self, action: str, message: str, duration: int = None):
        """执行界面切换"""
        try:
            # 构建消息格式
            display_message = {
                "action": action,
                "params": {
                    "message": message,
                    "timestamp": time.time()
                }
            }
            
            # 发送界面切换命令
            self.oled_manager._send_oled_display_command(display_message)
            
            # 设置定时器恢复正常界面
            if duration is None:
                duration = self.switch_duration
            
            if action != 'switch_to_normal' and self.auto_restore:
                timer = threading.Timer(duration, self.switch_to_normal)
                timer.start()
                self.logger.debug(f"设置 {duration} 秒后恢复正常界面")
                
        except Exception as e:
            self.logger.error(f"界面切换失败: {e}")
    
    def stop(self):
        """停止界面切换任务"""
        self.logger.info("界面切换任务已停止") 