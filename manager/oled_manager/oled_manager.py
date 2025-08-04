# -*- coding: utf-8 -*-
"""
OLED管理器模块
专门处理与OLED显示相关的传感器数据，实现智能显示控制逻辑
温湿度数据直接转发，界面切换独立处理
"""

import logging
import json
import sys
import os
from typing import Dict, Any

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from mqtt_base import MQTTSubscriber
from temperature_forwarder import TemperatureForwarder
from interface_switch_task import InterfaceSwitchTask

class OLEDManager(MQTTSubscriber):
    """OLED显示管理器 - 协调温湿度转发和界面切换任务"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 订阅传感器主题
        self.add_subscription('sensor')
        
        self.logger = logging.getLogger(__name__)
        
        # 保存配置对象供任务使用
        self.config = config
        
        # 创建两个独立的任务
        self.temp_forwarder = TemperatureForwarder(self)
        self.interface_task = InterfaceSwitchTask(self, config)
        
        self.logger.info("OLED管理器初始化完成")
    
    def handle_message(self, topic: str, payload: Dict[str, Any]):
        """处理接收到的传感器消息"""
        try:
            # 从payload中获取传感器类型
            sensor_type = payload.get('type')
            if not sensor_type:
                self.logger.warning(f"消息中缺少传感器类型: {payload}")
                return
            
            # 只处理OLED相关的传感器
            if sensor_type not in ['temperature_humidity', 'pir_motion']:
                return
            
            self.logger.info(f"收到 {sensor_type} 数据: {payload}")
            
            # 根据传感器类型分发到不同的任务
            if sensor_type == 'temperature_humidity':
                self._handle_temperature_humidity(payload)
            elif sensor_type == 'pir_motion':
                self._handle_pir_motion(payload)
                
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")
    
    def _handle_temperature_humidity(self, payload: Dict[str, Any]):
        """处理温湿度传感器数据 - 直接转发"""
        params = payload.get('params', {})
        temperature = params.get('temperature')
        humidity = params.get('humidity')
        
        if temperature is not None and humidity is not None:
            # 直接转发温湿度数据
            self.temp_forwarder.forward_temperature_humidity(temperature, humidity)
            self.logger.info(f"温湿度数据已转发: {temperature}°C, {humidity}%")
    
    def _handle_pir_motion(self, payload: Dict[str, Any]):
        """处理PIR运动检测传感器数据 - 交给界面切换任务"""
        params = payload.get('params', {})
        motion_detected = params.get('motion_detected', False)
        
        if motion_detected:
            # 触发界面切换任务
            self.interface_task.switch_to_motion_detected()
            self.logger.info("检测到运动，触发界面切换")
    
    def _send_oled_display_command(self, display_data: Dict[str, Any]):
        """发送OLED显示命令"""
        try:
            topic = "actuator/oled"
            self._publish_message(topic, display_data)
            self.logger.debug(f"已发送OLED显示命令: {display_data}")
        except Exception as e:
            self.logger.error(f"发送OLED显示命令失败: {e}")
    
    def _publish_message(self, topic: str, message: Dict[str, Any]):
        """发布消息到指定主题"""
        try:
            payload = json.dumps(message, ensure_ascii=False)
            self.client.publish(topic, payload, qos=1)
            self.logger.debug(f"已发送到 {topic}: {message}")
        except Exception as e:
            self.logger.error(f"发送消息到 {topic} 失败: {e}")
    
    def stop(self):
        """停止OLED管理器"""
        self.logger.info("正在停止OLED管理器...")
        self.temp_forwarder.stop()
        self.interface_task.stop()
        super().stop()

def main():
    """主函数"""
    import configparser
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 读取配置
    config = configparser.ConfigParser()
    config.read('config.ini')  # 现在使用当前目录的配置文件
    
    # 构建配置字典
    manager_config = {
        'mqtt_broker': config.get('mqtt', 'broker', fallback='localhost'),
        'mqtt_port': config.getint('mqtt', 'port', fallback=1883),
        'topic_prefix': config.get('mqtt', 'topic_prefix', fallback='sensor'),
        'sensor_type': 'oled_manager'
    }
    
    # 创建并启动OLED管理器
    manager = OLEDManager(manager_config)
    
    try:
        manager.run()
    except KeyboardInterrupt:
        logging.info("收到中断信号，正在关闭OLED管理器...")
        manager.stop()
    except Exception as e:
        logging.error(f"OLED管理器运行出错: {e}")

if __name__ == "__main__":
    main() 