# -*- coding: utf-8 -*-
"""蜂鸣器控制模块"""
import time
import threading
from typing import Optional
from .interface import BuzzerInterface

try:
    from gpiozero import Buzzer
except ImportError:  # 在没有硬件的环境下兼容
    Buzzer = None

class SimpleBuzzer(BuzzerInterface):
    """简单蜂鸣器控制类"""

    def __init__(self, pin: int):
        if Buzzer is None:
            raise RuntimeError("未安装gpiozero库，无法控制蜂鸣器")
        self.buzzer = Buzzer(pin)
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _beep_loop(self, duration: float, repeat: int) -> None:
        self._running = True
        for _ in range(repeat):
            if not self._running:
                break
            self.buzzer.on()
            time.sleep(duration)
            self.buzzer.off()
            time.sleep(duration)
        self._running = False

    def beep(self, duration: float = 0.2, repeat: int = 1) -> None:
        """同步蜂鸣，阻塞当前线程"""
        self._beep_loop(duration, repeat)

    def beep_async(self, duration: float = 0.2, repeat: int = 1) -> None:
        """异步蜂鸣，在独立线程中执行"""
        if self._thread and self._thread.is_alive():
            self.stop()
            self._thread.join()
        self._thread = threading.Thread(target=self._beep_loop,
                                        args=(duration, repeat),
                                        daemon=True)
        self._thread.start()

    def close(self):
        if hasattr(self.buzzer, 'close'):
            self.buzzer.close()

    def stop(self) -> None:
        self._running = False
        self.buzzer.off()
        if self._thread and self._thread.is_alive():
            self._thread.join()
