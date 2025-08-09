# -*- coding: utf-8 -*-
import asyncio
import logging
from typing import Optional, Tuple

import edge_tts
import miniaudio
import numpy as np
import aiohttp

logger = logging.getLogger(__name__)


class EdgeTTSApi:
    def __init__(
        self,
        *,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        logger.info(
            f"初始化 EdgeTTS API: voice={voice}, rate={rate}, volume={volume}, max_retries={max_retries}"
        )

    async def _create_communicate(self, text: str) -> edge_tts.Communicate:
        try:
            logger.debug(f"创建 Communicate 实例: text={text[:50]}...")
            return edge_tts.Communicate(text=text, voice=self.voice, rate=self.rate, volume=self.volume)
        except Exception as e:
            logger.error(f"创建 Communicate 实例失败: {str(e)}")
            raise

    async def text_to_audio(self, text: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        logger.info(f"开始转换文本: {text[:50]}...")
        comm = None
        for attempt in range(self.max_retries):
            try:
                comm = await self._create_communicate(text)
                mp3_buf = bytearray()
                chunk_count = 0

                async for item in comm.stream():
                    if isinstance(item, (bytes, bytearray)):
                        mp3_buf.extend(item)
                        chunk_count += 1
                    elif isinstance(item, dict) and item.get("type") == "audio":
                        mp3_buf.extend(item["data"])
                        chunk_count += 1

                logger.info(f"收到 {chunk_count} 个音频块，总大小: {len(mp3_buf)} 字节")

                if not mp3_buf:
                    logger.error("EdgeTTS error: empty audio")
                    if attempt < self.max_retries - 1:
                        logger.info(f"重试中 ({attempt + 1}/{self.max_retries})...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    return None, None

                logger.debug("开始解码 MP3 数据")
                snd = miniaudio.decode(bytes(mp3_buf), output_format=miniaudio.SampleFormat.SIGNED16)
                logger.info(
                    f"解码完成: 采样率={snd.sample_rate}Hz, 声道数={snd.nchannels}, 总帧数={len(snd.samples)}"
                )

                audio_data = np.frombuffer(snd.samples, dtype=np.int16)
                audio_data = audio_data.reshape(-1, snd.nchannels)
                audio_data = np.ascontiguousarray(audio_data)

                if np.isnan(audio_data).any() or np.isinf(audio_data).any():
                    logger.error("音频数据包含非法值")
                    if attempt < self.max_retries - 1:
                        logger.info(f"重试中 ({attempt + 1}/{self.max_retries})...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    return None, None

                logger.info("音频数据转换完成")
                return audio_data, snd.sample_rate

            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Edge TTS 请求失败: {str(e)}, 重试中 ({attempt + 1}/{self.max_retries})...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                logger.error(f"Edge TTS 请求失败: {str(e)}")
                return None, None
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Edge TTS 转换出错: {str(e)}, 重试中 ({attempt + 1}/{self.max_retries})...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                logger.error(f"Edge TTS 转换出错: {str(e)}")
                return None, None
            finally:
                sess = getattr(comm, "session", None) or getattr(comm, "_session", None)
                if sess and not sess.closed:
                    await sess.close()

        return None, None

    def sync_text_to_audio(self, text: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        return asyncio.run(self.text_to_audio(text))


