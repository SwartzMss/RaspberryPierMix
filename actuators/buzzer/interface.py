# -*- coding: utf-8 -*-
"""蜂鸣器接口定义"""
from abc import ABC, abstractmethod


class BuzzerInterface(ABC):
    """蜂鸣器接口"""

    @abstractmethod
    def beep(self, duration: float = 0.2, repeat: int = 1) -> None:
        """鸣叫指定时长和次数"""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """释放蜂鸣器资源"""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """停止正在进行的蜂鸣"""
        raise NotImplementedError
