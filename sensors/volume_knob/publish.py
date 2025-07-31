import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
# -*- coding: utf-8 -*-
"""
音量旋钮 MQTT 发布者核心逻辑
"""
import logging
import time
import threading
from mqtt_base import EventPublisher
from sensor import VolumeKnobSensor

class VolumeKnobPublisher(EventPublisher):
    """音量旋钮事件驱动发布者"""
    
    def __init__(self, config, config_manager=None):
        super().__init__(config)
        
        # 初始化传感器，传递配置管理器以支持校准保存
        self.sensor = VolumeKnobSensor(config, config_manager)
        
        # 配置参数
        self.threshold = config.get('volume_threshold', 2)
        self.read_interval = config.get('read_interval', 0.1)
        self.sensor_type = config.get('sensor_type', 'volume_knob')
        
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
                            # 发布MQTT消息
                            self.publish_sensor_data(self.sensor_type, data, retain=False)
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
    
    def run(self):
        """重写run方法"""
        if not self.connect():
            logging.error("无法连接到MQTT代理，退出")
            return
            
        self.running = True
        self.start_monitoring()
        
        logging.info("音量旋钮发布者已启动，监控音量变化...")
        
        try:
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logging.info("收到键盘中断信号")
        except Exception as e:
            logging.error(f"运行过程中发生错误: {e}")
        finally:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)
            self.stop()

def setup_logging() -> None:
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )