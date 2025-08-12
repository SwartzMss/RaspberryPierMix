# -*- coding: utf-8 -*-
"""
AutoScreenSwitch 管理器
订阅统一传感器主题，基于 PIR 人体检测事件发布屏幕亮/息指令：
 - 检测到人体 → 立即发布 on
 - 超过配置的无人时长 → 发布 off
"""

import logging
import json
import time
import threading
import sys
import os
from typing import Dict, Any, Optional

# 添加 common 目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from mqtt_base import MQTTSubscriber


class AutoScreenSwitchManager(MQTTSubscriber):
    """屏幕亮/息管理器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # 订阅统一传感器主题
        self.add_subscription('sensor')

        self.logger = logging.getLogger(__name__)
        self.config = config

        # 行为配置
        auto_cfg = {
            'idle_off_seconds': 900,
            'publish_topic': 'actuator/autoScreenSwitch'
        }
        if isinstance(config, dict):
            # 允许通过构建时直接传入配置覆盖
            auto_cfg.update({
                'idle_off_seconds': config.get('idle_off_seconds', auto_cfg['idle_off_seconds']),
                'publish_topic': config.get('publish_topic', auto_cfg['publish_topic']),
            })

        self.idle_off_seconds: int = int(auto_cfg['idle_off_seconds'])
        self.publish_topic: str = str(auto_cfg['publish_topic'])

        # 活动/空闲状态
        self._last_motion_ts: Optional[float] = None
        self._last_state: Optional[str] = None  # 'on' 或 'off'
        self._lock = threading.Lock()

        # 后台空闲检测线程
        self._idle_thread: Optional[threading.Thread] = None
        self._idle_thread_stop = threading.Event()

        self.logger.info(
            f"AutoScreenSwitchManager 初始化完成（idle_off_seconds={self.idle_off_seconds}, publish_topic={self.publish_topic}）"
        )

    def on_connect(self, client, userdata, flags, rc):
        """连接建立后，启动空闲检测线程"""
        super().on_connect(client, userdata, flags, rc)
        if rc == 0 and (self._idle_thread is None or not self._idle_thread.is_alive()):
            self._idle_thread_stop.clear()
            self._idle_thread = threading.Thread(target=self._idle_watch_loop, name='idle-watch', daemon=True)
            self._idle_thread.start()

    def handle_message(self, topic: str, payload: Dict[str, Any]):
        """处理传感器消息"""
        try:
            sensor_type = payload.get('type')
            if sensor_type != 'pir_motion':
                return

            params = payload.get('params', {})
            motion_detected = bool(params.get('motion_detected'))
            if not motion_detected:
                return

            # 与 OLEDManager 对齐：记录收到的 PIR 事件，便于观察频次
            self.logger.info(f"收到 pir_motion 数据: {payload}")

            # 有人来：立刻上报 on，并记录最近活动时间
            with self._lock:
                self._last_motion_ts = time.time()
            self._send_switch_command(action='on', source='pir_motion')

        except Exception as exc:
            self.logger.error(f"处理消息出错: {exc}")

    def _idle_watch_loop(self):
        """后台循环：检查无人超时，触发 off"""
        self.logger.info("空闲检测线程已启动")
        try:
            while not self._idle_thread_stop.is_set():
                now = time.time()
                last_motion: Optional[float]
                with self._lock:
                    last_motion = self._last_motion_ts

                if last_motion is not None:
                    idle_seconds = now - last_motion
                    if idle_seconds >= self.idle_off_seconds:
                        # 触发 off 并清空 last_motion，避免重复下发
                        self._send_switch_command(action='off', source='idle_timeout')
                        with self._lock:
                            # 重置为 None，直到下次检测到运动
                            self._last_motion_ts = None

                # 低频轮询足矣
                self._idle_thread_stop.wait(1.0)
        except Exception as exc:
            self.logger.error(f"空闲检测线程异常: {exc}")
        finally:
            self.logger.info("空闲检测线程已退出")

    def _send_switch_command(self, action: str, source: str):
        """向执行器发布 on/off 指令，params 仅包含 source"""
        try:
            if action not in ('on', 'off'):
                self.logger.warning(f"忽略未知 action: {action}")
                return

            message = {
                'action': action,
                'params': {
                    'source': source
                }
            }

            # 避免无谓的重复下发：只有状态变化时才发
            if self._last_state == action:
                # 打印为 DEBUG，默认 INFO 级别不会刷屏；若需要可将服务日志级别调至 DEBUG
                self.logger.debug(f"状态未变化，跳过重复发布: {action}（source={source}）")
                return

            ok = self.publish_message(self.publish_topic, message, qos=1, retain=False)
            if ok:
                self._last_state = action
                self.logger.info(f"已发布 {action} 至 {self.publish_topic}: {json.dumps(message, ensure_ascii=False)}")
            else:
                self.logger.error(f"发布失败: {action} → {self.publish_topic}")

        except Exception as exc:
            self.logger.error(f"发送指令失败: {exc}")

    def stop(self):
        """停止管理器"""
        self.logger.info("正在停止 AutoScreenSwitchManager …")
        try:
            self._idle_thread_stop.set()
            if self._idle_thread and self._idle_thread.is_alive():
                self._idle_thread.join(timeout=3)
        finally:
            super().stop()


def main():
    import configparser

    # 日志级别可通过配置文件 logging.level 覆盖，默认 INFO
    config = configparser.ConfigParser()
    config.read('config.ini')
    level_name = config.get('logging', 'level', fallback='INFO').upper()
    log_level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    manager_config = {
        'mqtt_broker': config.get('mqtt', 'broker', fallback='localhost'),
        'mqtt_port': config.getint('mqtt', 'port', fallback=1883),
        'topic_prefix': config.get('mqtt', 'topic_prefix', fallback='sensor'),
        # 行为参数（允许直接覆盖）
        'idle_off_seconds': config.getint('auto_screen_switch', 'idle_off_seconds', fallback=900),
        'publish_topic': config.get('auto_screen_switch', 'publish_topic', fallback='actuator/autoScreenSwitch'),
    }

    manager = AutoScreenSwitchManager(manager_config)
    try:
        manager.run()
    except KeyboardInterrupt:
        logging.info("收到中断信号，退出管理器…")
        manager.stop()
    except Exception as exc:
        logging.error(f"运行出错: {exc}")


if __name__ == '__main__':
    main()


