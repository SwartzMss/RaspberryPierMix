# -*- coding: utf-8 -*-
"""
DHT22 数据监控订阅者
用于接收和显示DHT22传感器数据
"""

import time
import logging
import sys
import os
from typing import Dict, Any

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from mqtt_base import MQTTSubscriber

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DHT22Monitor(MQTTSubscriber):
    """DHT22数据监控订阅者"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化监控者
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        
        # 数据统计
        self.message_count = 0
        self.last_temperature = None
        self.last_humidity = None
        
        # 添加订阅
        self.add_subscription(f"{self.topic_prefix}/dht22")
    
    def handle_message(self, topic: str, payload: Dict[str, Any]):
        """处理消息 - 重写基类方法"""
        if topic == f"{self.topic_prefix}/dht22":
            self.handle_sensor_data(payload)
        else:
            logger.debug(f"收到未知主题消息: {topic}")
    
    def handle_sensor_data(self, data: Dict[str, Any]):
        """处理传感器数据"""
        self.message_count += 1
        
        try:
            sensor_data = data.get('data', {})
            temperature = sensor_data.get('temperature')
            humidity = sensor_data.get('humidity')
            timestamp = data.get('timestamp')
            
            # 更新最新数据
            if temperature is not None:
                self.last_temperature = temperature
            if humidity is not None:
                self.last_humidity = humidity
            
            # 显示数据
            print(f"\n{'='*50}")
            print(f"📊 DHT22 传感器数据 (消息 #{self.message_count})")
            print(f"{'='*50}")
            print(f"时间戳: {timestamp}")
            print(f"温度: {temperature}°C")
            print(f"湿度: {humidity}%")
            print(f"数据时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
            print(f"{'='*50}")
            
            # 简单的数据验证
            if temperature is not None:
                if temperature < -40 or temperature > 80:
                    logger.warning(f"温度值异常: {temperature}°C")
                elif temperature < 0:
                    logger.info("温度较低，注意保暖")
                elif temperature > 30:
                    logger.info("温度较高，注意防暑")
            
            if humidity is not None:
                if humidity < 0 or humidity > 100:
                    logger.warning(f"湿度值异常: {humidity}%")
                elif humidity < 30:
                    logger.info("湿度较低，注意保湿")
                elif humidity > 70:
                    logger.info("湿度较高，注意防潮")
                    
        except Exception as e:
            logger.error(f"处理传感器数据时发生错误: {e}")
    

    
    def run(self):
        """运行监控者主循环"""
        logger.info("DHT22监控者已启动，等待数据...")
        print("\n🔍 正在监控DHT22传感器数据...")
        print("按 Ctrl+C 退出")
        
        super().run()
        
        # 显示统计信息
        print(f"\n📈 统计信息:")
        print(f"接收消息数: {self.message_count}")
        if self.last_temperature is not None:
            print(f"最新温度: {self.last_temperature}°C")
        if self.last_humidity is not None:
            print(f"最新湿度: {self.last_humidity}%")

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    return {
        'mqtt_broker': 'localhost',
        'mqtt_port': 1883,
        'topic_prefix': 'sensor'
    }

def main():
    """主函数"""
    try:
        # 加载配置
        config = load_config()
        
        # 创建监控者实例
        monitor = DHT22Monitor(config)
        
        # 运行监控者
        monitor.run()
        
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 