# -*- coding: utf-8 -*-
"""
USB音频控制模块
基于 pi5-usbaudio-tools 项目，提供文字播报功能
"""

import logging
import subprocess
import shlex
import signal
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
        # 播报线程与控制
        self._play_thread: Optional[threading.Thread] = None
        self._generation_id: int = 0
        
        # 确保音频目录存在
        os.makedirs(self.audio_dir, exist_ok=True)
        
        self.control_name = config.get('control_name', 'Headphone')  # 音量控制项名称

        # 仅使用在线 TTS
        self.edge_voice = str(config.get('edge_voice', 'zh-CN-XiaoxiaoNeural'))
        self.edge_rate = str(config.get('edge_rate', '+0%'))
        self.edge_volume = str(config.get('edge_volume', '+0%'))
        try:
            # 与同目录模块相对导入（audio.py 与 edge_tts_api.py 位于同一目录）
            from edge_tts_api import EdgeTTSApi  # type: ignore
        except Exception:
            # 兼容从包外导入的场景
            from actuators.audio.edge_tts_api import EdgeTTSApi  # type: ignore

        self._edge_api = EdgeTTSApi(
            voice=self.edge_voice,
            rate=self.edge_rate,
            volume=self.edge_volume,
        )

        logger.info(
            f"音频控制器初始化完成: card={self.card_index}, control={self.control_name}, tts=edge_tts voice={self.edge_voice}"
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
    
    def _play_text_worker(self, text: str, generation_id: int) -> None:
        """在后台线程中执行文本转音频并播放，避免阻塞MQTT回调线程"""
        try:
            # 文本转音频（在线TTS）
            from typing import Tuple
            import numpy as np
            import tempfile
            import wave

            audio_data, sample_rate = self._edge_api.sync_text_to_audio(text)  # type: ignore
            if audio_data is None or sample_rate is None:
                logger.error("在线TTS转换失败")
                return

            # 若期间被新的任务取代，则丢弃本次结果
            if generation_id != self._generation_id:
                logger.info("检测到新任务取代，放弃当前生成的音频")
                return

            # 写入临时WAV并播放
            tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=self.audio_dir)
            with wave.open(tmp_wav.name, 'wb') as wf:
                channels = audio_data.shape[1] if len(audio_data.shape) > 1 else 1
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(np.asarray(audio_data, dtype=np.int16).tobytes())

            device = f"plughw:{self.card_index},0"
            cmd = f"aplay -q -D {device} {shlex.quote(tmp_wav.name)}"
            with self._lock:
                # 若期间被新的任务取代，则丢弃播放
                if generation_id != self._generation_id:
                    logger.info("检测到新任务取代，取消当前播放")
                    return
                self.current_process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid,
                    start_new_session=True,
                )
            logger.info(f"开始播报文字(在线): {text}")
        except Exception as e:
            logger.error(f"后台播放线程异常: {e}")

    def speak_text(self, text: str) -> bool:
        """
        播报文字
        
        Args:
            text: 要播报的文字
            
        Returns:
            播报是否成功启动
        """
        # 先停止当前播放，避免与新任务冲突
        self.stop_audio()

        try:
            # 增加任务代号，替换旧任务
            with self._lock:
                self._generation_id += 1
                generation_id = self._generation_id

            # 启动后台线程执行TTS与播放
            worker = threading.Thread(
                target=self._play_text_worker, args=(text, generation_id), daemon=True
            )
            self._play_thread = worker
            worker.start()
            logger.info(f"已启动后台播报任务: {text}")
            return True
        except Exception as e:
            logger.error(f"启动后台播报任务失败: {e}")
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