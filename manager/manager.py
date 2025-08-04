# -*- coding: utf-8 -*-
"""
传感器数据管理模块
处理传感器数据并发布业务逻辑相关的消息给执行器
"""

import logging
import json
import time
import sys
import os
import threading
from typing import Dict, Any

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from mqtt_base import MQTTSubscriber

class SensorManager(MQTTSubscriber):
    """传感器数据管理器 - 增强版本，支持OLED状态管理"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 订阅统一的sensor主题
        self.add_subscription('sensor')
        
        # 传感器类型到执行器的映射
        self.sensor_to_actuator = {
            'temperature_humidity': 'oled',
            'pir_motion': 'oled',
            'button': 'buzzer',
            'potentiometer': 'audio'
        }
        
        # OLED状态管理
        self.oled_state = {
            'show_temp_mode': False,  # 是否显示温湿度模式
            'latest_temperature': None,
            'latest_humidity': None,
            'temp_timer': None,  # 10分钟定时器
            'temp_display_duration': 10 * 60  # 10分钟 = 600秒
        }
        
        self.logger = logging.getLogger(__name__)
    
    def handle_message(self, topic: str, payload: Dict[str, Any]):
        """处理接收到的传感器消息 - 增强版本"""
        try:
            # 从payload中获取传感器类型
            sensor_type = payload.get('type')
            if not sensor_type:
                self.logger.warning(f"消息中缺少传感器类型: {payload}")
                return
            
            # 获取传感器数据
            sensor_data = payload.get('params', {})
            
            self.logger.info(f"收到 {sensor_type} 数据: {sensor_data}")
            
            # 根据传感器类型进行特殊处理
            if sensor_type == 'temperature_humidity':
                self._handle_temperature_humidity(sensor_data)
            elif sensor_type == 'pir_motion':
                self._handle_pir_motion(sensor_data)
            else:
                # 其他传感器直接转发
                self._forward_to_actuator(sensor_type, payload)
                
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")
    
    def _handle_temperature_humidity(self, sensor_data: Dict[str, Any]):
        """处理温湿度数据"""
        temperature = sensor_data.get('temperature')
        humidity = sensor_data.get('humidity')
        
        if temperature is not None and humidity is not None:
            # 更新最新温湿度数据
            self.oled_state['latest_temperature'] = temperature
            self.oled_state['latest_humidity'] = humidity
            
            self.logger.info(f"更新温湿度数据: {temperature}°C, {humidity}%")
            
            # 如果当前在温湿度显示模式，发送更新消息
            if self.oled_state['show_temp_mode']:
                self._send_oled_action('update_temp_humi', {
                    'temperature': temperature,
                    'humidity': humidity
                })
    
    def _handle_pir_motion(self, sensor_data: Dict[str, Any]):
        """处理PIR运动检测数据"""
        motion_detected = sensor_data.get('motion_detected', False)
        
        if motion_detected:
            # 检测到有人
            self.logger.info("检测到有人，切换到温湿度显示模式")
            self.oled_state['show_temp_mode'] = True
            
            # 启动10分钟定时器
            self._start_temp_display_timer()
            
            # 发送显示温湿度消息
            if self.oled_state['latest_temperature'] is not None and self.oled_state['latest_humidity'] is not None:
                self._send_oled_action('show_temp_humi', {
                    'temperature': self.oled_state['latest_temperature'],
                    'humidity': self.oled_state['latest_humidity']
                })
            else:
                # 没有温湿度数据，发送显示时间消息
                self._send_oled_action('show_time', {})
        else:
            # 无人状态，忽略
            self.logger.debug("收到无人消息，忽略处理")
    
    def _start_temp_display_timer(self):
        """启动10分钟温湿度显示定时器"""
        # 取消之前的定时器
        if self.oled_state['temp_timer']:
            self.oled_state['temp_timer'].cancel()
        
        # 启动新的定时器
        self.oled_state['temp_timer'] = threading.Timer(
            self.oled_state['temp_display_duration'], 
            self._switch_to_time_display
        )
        self.oled_state['temp_timer'].start()
        self.logger.info(f"启动温湿度显示定时器，{self.oled_state['temp_display_duration']}秒后切换回时间显示")
    
    def _switch_to_time_display(self):
        """定时器回调：切换回时间显示"""
        self.oled_state['show_temp_mode'] = False
        self.logger.info("10分钟到期，切换回时间显示")
        
        # 发送显示时间消息
        self._send_oled_action('show_time', {})
    
    def _send_oled_action(self, action: str, data: Dict[str, Any]):
        """发送OLED控制消息"""
        message = {
            'action': action,
            'data': data
        }
        
        topic = 'actuator/oled'
        self._publish_message(topic, message)
        self.logger.info(f"发送OLED控制消息: {action} - {data}")
    
    def _forward_to_actuator(self, sensor_type: str, payload: Dict[str, Any]):
        """统一转发传感器数据到对应的执行器"""
        # 获取对应的执行器
        actuator = self.sensor_to_actuator.get(sensor_type)
        if not actuator:
            self.logger.warning(f"未知传感器类型: {sensor_type}")
            return
        
        # 构建转发消息 - 只保留关键数据
        message = payload.get('params', {})
        
        # 发布到对应的执行器主题
        topic = f"actuator/{actuator}"
        self._publish_message(topic, message)
        
        self.logger.info(f"转发 {sensor_type} 数据到 {actuator}: {message}")
    
    def _publish_message(self, topic: str, message: Dict[str, Any]):
        """发布消息到指定主题"""
        try:
            payload = json.dumps(message, ensure_ascii=False)
            self.client.publish(topic, payload, qos=1)
            self.logger.debug(f"已发送到 {topic}: {message}")
        except Exception as e:
            self.logger.error(f"发送消息到 {topic} 失败: {e}")

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
    config.read('manager/config.ini')
    
    # 构建配置字典
    manager_config = {
        'mqtt_broker': config.get('mqtt', 'broker', fallback='localhost'),
        'mqtt_port': config.getint('mqtt', 'port', fallback=1883),
        'topic_prefix': config.get('mqtt', 'topic_prefix', fallback='sensor'),
        'sensor_type': 'manager'
    }
    
    # 创建并启动管理器
    manager = SensorManager(manager_config)
    
    try:
        manager.run()
    except KeyboardInterrupt:
        logging.info("收到中断信号，正在关闭管理器...")
    except Exception as e:
        logging.error(f"管理器运行出错: {e}")

if __name__ == "__main__":
    main() 