# -*- coding: utf-8 -*-
"""
OLED管理器模块
专门处理与OLED显示相关的传感器数据，实现智能显示控制逻辑
将温湿度显示和界面切换分离为两个独立的任务
"""

import logging
import json
import sys
import os
import threading
import time
from typing import Dict, Any

# 添加common目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from mqtt_base import MQTTSubscriber

class TemperatureDisplayTask:
    """温湿度显示任务 - 持续更新温湿度数据"""
    
    def __init__(self, oled_manager, config):
        self.oled_manager = oled_manager
        self.logger = logging.getLogger(__name__)
        
        # 从配置读取更新间隔
        self.update_interval = config.getint('oled', 'temp_update_interval', fallback=30)
        
        # 温湿度状态
        self.temperature = None
        self.humidity = None
        self.last_update_time = None
        
        # 启动温湿度更新线程
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        self.logger.info("温湿度显示任务已启动")
    
    def update_temperature_humidity(self, temperature: float, humidity: float):
        """更新温湿度数据"""
        self.temperature = temperature
        self.humidity = humidity
        self.last_update_time = time.time()
        self.logger.debug(f"更新温湿度数据: {temperature}°C, {humidity}%")
    
    def _update_loop(self):
        """温湿度更新循环"""
        while self.running:
            try:
                if self.temperature is not None and self.humidity is not None:
                    # 发送温湿度显示命令
                    self.oled_manager._send_oled_display_command({
                        'mode': 'temperature',
                        'temperature': self.temperature,
                        'humidity': self.humidity,
                        'timestamp': time.time()
                    })
                    self.logger.debug("发送温湿度显示更新")
                
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"温湿度更新循环出错: {e}")
                time.sleep(5)  # 出错时等待5秒再继续
    
    def stop(self):
        """停止温湿度显示任务"""
        self.running = False
        if self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
        self.logger.info("温湿度显示任务已停止")

class InterfaceSwitchTask:
    """界面切换任务 - 处理一次性的界面切换事件"""
    
    def __init__(self, oled_manager, config):
        self.oled_manager = oled_manager
        self.logger = logging.getLogger(__name__)
        
        # 从配置读取切换持续时间
        self.switch_duration = config.getint('oled', 'switch_duration', fallback=5)
        self.auto_restore = config.getboolean('oled', 'auto_restore', fallback=True)
        
        # 界面切换状态
        self.current_mode = 'normal'
        
        self.logger.info("界面切换任务已启动")
    
    def switch_to_motion_detected(self):
        """切换到运动检测界面"""
        self.logger.info("切换到运动检测界面")
        self._switch_interface('motion_detected', 'Motion Detected!')
    
    def switch_to_normal(self):
        """切换到正常界面"""
        self.logger.info("切换到正常界面")
        self._switch_interface('normal', 'System Ready')
    
    def switch_to_custom(self, message: str, duration: int = None):
        """切换到自定义界面"""
        self.logger.info(f"切换到自定义界面: {message}")
        self._switch_interface('custom', message, duration)
    
    def _switch_interface(self, mode: str, message: str, duration: int = None):
        """执行界面切换"""
        try:
            # 发送界面切换命令
            self.oled_manager._send_oled_display_command({
                'mode': mode,
                'message': message,
                'timestamp': time.time()
            })
            
            # 设置定时器恢复正常界面
            if duration is None:
                duration = self.switch_duration
            
            if mode != 'normal' and self.auto_restore:
                timer = threading.Timer(duration, self.switch_to_normal)
                timer.start()
                self.logger.debug(f"设置 {duration} 秒后恢复正常界面")
                
        except Exception as e:
            self.logger.error(f"界面切换失败: {e}")

class OLEDManager(MQTTSubscriber):
    """OLED显示管理器 - 协调温湿度显示和界面切换任务"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 订阅传感器主题
        self.add_subscription('sensor')
        
        self.logger = logging.getLogger(__name__)
        
        # 保存配置对象供任务使用
        self.config = config
        
        # 创建两个独立的任务
        self.temp_task = TemperatureDisplayTask(self, config)
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
        """处理温湿度传感器数据 - 交给温湿度显示任务"""
        params = payload.get('params', {})
        temperature = params.get('temperature')
        humidity = params.get('humidity')
        
        if temperature is not None and humidity is not None:
            # 更新温湿度显示任务的数据
            self.temp_task.update_temperature_humidity(temperature, humidity)
            self.logger.info(f"温湿度数据已更新: {temperature}°C, {humidity}%")
    
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
        self.temp_task.stop()
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