import sys
import os 
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
# -*- coding: utf-8 -*-
"""
音量旋钮 MQTT 发布者核心逻辑
改造为统一传感器数据格式
"""
import logging
import time
import threading
from mqtt_base import EventPublisher
from sensor import VolumeKnobSensor

class VolumeKnobPublisher(EventPublisher):
    """音量旋钮事件驱动发布者 - 统一数据格式"""

    def __init__(self, config, config_manager=None):
        super().__init__(config)

        # 初始化传感器，传递配置管理器以支持校准保存
        self.sensor = VolumeKnobSensor(config, config_manager)

        # 配置参数
        self.threshold = config.get('volume_threshold', 2)
        self.read_interval = config.get('read_interval', 0.1)

        # 监控控制
        self.monitoring = True
        self.monitor_thread = None

        logging.info("音量旋钮发布者初始化完成")

    def start_monitoring(self):
        """启动后台监控线程"""
        def monitor():
            logging.info("音量旋钮监控线程已启动")

            while self.monitoring and self.running:
                try:
                    # 读取音量数据
                    data = self.sensor.read_volume()

                    if data:
                        # 检查是否有显著变化
                        if self.sensor.has_significant_change(data['volume'], self.threshold):
                            # 构建标准化的音量数据
                            volume_data = {
                                "volume": data['volume'],
                                "timestamp": data['timestamp']
                            }
                            
                            # 发布传感器数据
                            self.publish_sensor_data(volume_data, retain=True)
                            logging.info(f"音量变化: {data['volume']}%")
                    else:
                        logging.warning("读取音量数据失败")

                except Exception as e:
                    logging.error(f"监控音量旋钮时发生错误: {e}")

                time.sleep(self.read_interval)

            logging.info("音量旋钮监控线程已停止")

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def calibrate_sensor(self):
        """传感器校准"""
        return self.sensor.calibrate()

    def get_current_status(self):
        """获取当前状态"""
        data = self.sensor.read_volume()
        if data:
            return {
                'volume': data['volume'],
                'sensor_info': self.sensor.get_sensor_info(),
                'timestamp': data['timestamp']
            }
        return None

    def init_sensor(self):
        """初始化传感器 - 重写父类方法"""
        self.start_monitoring()

    def cleanup_sensor(self):
        """清理传感器 - 重写父类方法"""
        self.monitoring = False
        logging.info("音量旋钮监控已停止")

    def start(self):
        """启动发布者 - 使用父类的标准实现"""
        super().start()

def setup_logging() -> None:
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )