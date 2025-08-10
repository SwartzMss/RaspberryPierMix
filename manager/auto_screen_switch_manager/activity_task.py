# -*- coding: utf-8 -*-
"""
活动/空闲检测任务（可选拆分）
当前暂未被主文件引用，预留结构以便未来扩展：
 - 将空闲检测与消息下发逻辑独立到任务类
 - 便于单元测试与复用
"""

import logging
import time
from typing import Optional, Callable


class ActivityIdleTask:
    """活动/空闲检测状态机（供未来扩展）"""

    def __init__(self, idle_off_seconds: int, on_on: Callable[[], None], on_off: Callable[[], None]):
        self.logger = logging.getLogger(__name__)
        self.idle_off_seconds = int(idle_off_seconds)
        self.on_on = on_on
        self.on_off = on_off
        self._last_motion_ts: Optional[float] = None
        self._last_state: Optional[str] = None

    def notify_motion(self):
        self._last_motion_ts = time.time()
        if self._last_state != 'on':
            self.on_on()
            self._last_state = 'on'

    def tick(self):
        if self._last_motion_ts is None:
            return
        if (time.time() - self._last_motion_ts) >= self.idle_off_seconds:
            if self._last_state != 'off':
                self.on_off()
                self._last_state = 'off'
            self._last_motion_ts = None


