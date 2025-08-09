# -*- coding: utf-8 -*-
"""
USB音频控制模块
基于 pi5-usbaudio-tools 项目，提供文字播报功能
"""

import logging
import subprocess
import shlex
import signal
import shutil
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
        # 使用可重入锁，避免在 speak_text 内部调用 stop_audio 造成死锁
        self._lock = threading.RLock()
        
        # 确保音频目录存在
        os.makedirs(self.audio_dir, exist_ok=True)
        
        self.control_name = config.get('control_name', 'Headphone')  # 音量控制项名称
        # 选择可用的 TTS 命令（离线）
        self.tts_cmd = 'espeak'
        if shutil.which('espeak') is None and shutil.which('espeak-ng') is not None:
            self.tts_cmd = 'espeak-ng'

        # 在线TTS开关与配置
        self.use_online_tts = bool(config.get('use_online_tts', False))
        self.edge_voice = str(config.get('edge_voice', 'zh-CN-XiaoxiaoNeural'))
        self.edge_rate = str(config.get('edge_rate', '+0%'))
        self.edge_volume = str(config.get('edge_volume', '+0%'))
        self._edge_api = None
        if self.use_online_tts:
            try:
                from .edge_tts_api import EdgeTTSApi  # lazy import for optional dep
                self._edge_api = EdgeTTSApi(
                    voice=self.edge_voice,
                    rate=self.edge_rate,
                    volume=self.edge_volume,
                )
            except Exception as e:
                logger.error(f"初始化在线TTS失败，将回退到离线TTS: {e}")
                self.use_online_tts = False

        logger.info(
            f"音频控制器初始化完成: card={self.card_index}, control={self.control_name}, online_tts={self.use_online_tts}"
        )
    
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
            logger.info(f"执行音量命令: {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.returncode == 0:
                logger.info(f"音量设置成功: {volume}%")
                return True
            else:
                logger.error(f"设置音量失败(code={result.returncode}): {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("设置音量命令超时，可能被音频设备占用或ALSA阻塞")
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
        # 先停止当前播放，避免在持锁状态下嵌套调用造成死锁
        self.stop_audio()

        with self._lock:
            try:
                device = f"plughw:{self.card_index},0"
                if self.use_online_tts and self._edge_api is not None:
                    # 在线TTS：获取PCM后写入临时WAV，再用 aplay 播放
                    import tempfile
                    import wave
                    import numpy as np

                    audio_data, sample_rate = self._edge_api.sync_text_to_audio(text)
                    if audio_data is None or sample_rate is None:
                        logger.error("在线TTS转换失败")
                        return False

                    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=self.audio_dir)
                    with wave.open(tmp_wav.name, 'wb') as wf:
                        channels = audio_data.shape[1] if len(audio_data.shape) > 1 else 1
                        wf.setnchannels(channels)
                        wf.setsampwidth(2)
                        wf.setframerate(sample_rate)
                        wf.writeframes(np.asarray(audio_data, dtype=np.int16).tobytes())

                    cmd = f"aplay -q -D {device} {shlex.quote(tmp_wav.name)}"
                    self.current_process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        preexec_fn=os.setsid,
                        start_new_session=True,
                    )
                else:
                    # 离线TTS：通过管道将 espeak 音频输出到 aplay，并指定声卡
                    safe_text = shlex.quote(text)
                    cmd = f"{self.tts_cmd} -s 150 -v zh --stdout {safe_text} | aplay -q -D {device}"
                    self.current_process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        preexec_fn=os.setsid,
                        start_new_session=True,
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
                    # 终止整个进程组，确保管道内进程全部结束
                    try:
                        os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                    except Exception:
                        # 回退到单进程终止
                        self.current_process.terminate()
                    # 等待进程结束
                    self.current_process.wait(timeout=2)
                    logger.info("音频播放已停止")
                    return True
                except subprocess.TimeoutExpired:
                    # 强制终止
                    try:
                        os.killpg(os.getpgid(self.current_process.pid), signal.SIGKILL)
                    except Exception:
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