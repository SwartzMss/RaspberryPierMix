# -*- coding: utf-8 -*-
"""
USB音频控制模块
基于 pi5-usbaudio-tools 项目，提供文字播报功能
"""

import logging
import subprocess
import threading
import time
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AudioController:
    """USB音频控制器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化音频控制器
        
        Args:
            config: 配置字典，包含声卡相关参数
        """
        self.config = config
        self.card_index = config.get('card_index', 2)  # 默认USB声卡索引
        self.audio_dir = config.get('audio_dir', './tmp')  # 临时音频文件目录
        self.current_process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        
        # 确保音频目录存在
        os.makedirs(self.audio_dir, exist_ok=True)
        
        self.control_name = config.get('control_name', 'Headphone')  # 音量控制项名称
        logger.info(f"音频控制器初始化完成: card={self.card_index}, control={self.control_name}")
    
    def set_volume(self, volume: int) -> bool:
        """
        设置音量
        
        Args:
            volume: 音量百分比 (0-100)
            
        Returns:
            设置是否成功
        """
        if not 0 <= volume <= 100:
            logger.error(f"音量值无效: {volume}，应在0-100范围内")
            return False
        
        try:
            cmd = f"amixer -c {self.card_index} sset {self.control_name} {volume}% unmute"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"音量设置成功: {volume}%")
                return True
            else:
                logger.error(f"设置音量失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"设置音量时发生错误: {e}")
            return False
    
    def speak_text(self, text: str) -> bool:
        """
        播报文字
        
        Args:
            text: 要播报的文字
            
        Returns:
            播报是否成功启动
        """
        with self._lock:
            # 停止当前播放
            self.stop_audio()
            
            try:
                # 使用espeak进行文字转语音
                cmd = f"espeak -s 150 -v zh '{text}'"
                
                # 启动播报进程
                self.current_process = subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                
                logger.info(f"开始播报文字: {text}")
                return True
                
            except Exception as e:
                logger.error(f"播报文字时发生错误: {e}")
                return False
    
    def stop_audio(self) -> bool:
        """
        停止音频播放
        
        Returns:
            操作是否成功
        """
        with self._lock:
            if self.current_process and self.current_process.poll() is None:
                try:
                    self.current_process.terminate()
                    # 等待进程结束
                    self.current_process.wait(timeout=2)
                    logger.info("音频播放已停止")
                    return True
                except subprocess.TimeoutExpired:
                    # 强制终止
                    self.current_process.kill()
                    logger.warning("强制终止音频播放")
                    return True
                except Exception as e:
                    logger.error(f"停止音频播放时发生错误: {e}")
                    return False
            
            return True
    

    
    def close(self):
        """关闭音频控制器"""
        self.stop_audio()
        logger.info("音频控制器已关闭") 