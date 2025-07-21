# -*- coding: utf-8 -*-
"""蜂鸣器控制模块"""
import time
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

    def beep(self, duration: float = 0.2, repeat: int = 1) -> None:
        self._running = True
        for _ in range(repeat):
            if not self._running:
                break
            self.buzzer.on()
            time.sleep(duration)
            self.buzzer.off()
            time.sleep(duration)
        self._running = False

    def close(self):
        if hasattr(self.buzzer, 'close'):
            self.buzzer.close()

    def stop(self) -> None:
        self._running = False
        self.buzzer.off()
