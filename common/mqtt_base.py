# -*- coding: utf-8 -*-
"""
MQTT 通用基类
提供发布者和订阅者的共同功能
"""

import json
import time
import logging
import signal
import sys
from typing import Dict, Any, Optional, Callable
import paho.mqtt.client as mqtt

class MQTTBase:
    """MQTT基础类，提供通用功能"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MQTT基础类
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.client = mqtt.Client()
        self.running = False
        
        # MQTT 配置
        self.broker_host = config.get('mqtt_broker', 'localhost')
        self.broker_port = config.get('mqtt_port', 1883)
        self.topic_prefix = config.get('topic_prefix', 'sensor')
        
        # 设置MQTT回调
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调 - 子类可重写"""
        if rc == 0:
            logging.info(f"已连接到MQTT代理: {self.broker_host}:{self.broker_port}")
        else:
            logging.error(f"MQTT连接失败，错误码: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT断开连接回调 - 子类可重写"""
        if rc != 0:
            logging.warning(f"MQTT连接意外断开，错误码: {rc}")
        else:
            logging.info("MQTT连接已断开")
    
    def on_publish(self, client, userdata, mid):
        """MQTT发布回调 - 子类可重写"""
        logging.debug(f"消息已发布，消息ID: {mid}")
    
    def on_message(self, client, userdata, msg):
        """MQTT消息回调 - 子类可重写"""
        logging.debug(f"收到消息: {msg.topic} -> {msg.payload.decode()}")
    
    def signal_handler(self, signum, frame):
        """信号处理函数"""
        logging.info(f"收到信号 {signum}，正在关闭...")
        self.stop()
    
    def publish_message(self, topic: str, message: Dict[str, Any], qos: int = 1, retain: bool = True) -> bool:
        """
        发布消息到指定主题
        
        Args:
            topic: 主题
            message: 消息内容
            qos: 服务质量等级
            retain: 是否保留消息
            
        Returns:
            发布是否成功
        """
        try:
            payload = json.dumps(message, ensure_ascii=False)
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.debug(f"消息已发布到主题 {topic}")
                return True
            else:
                logging.error(f"发布消息失败，错误码: {result.rc}")
                return False
                
        except Exception as e:
            logging.error(f"发布消息时发生错误: {e}")
            return False
    

    
    def subscribe_topic(self, topic: str, qos: int = 1):
        """
        订阅主题
        
        Args:
            topic: 主题
            qos: 服务质量等级
        """
        try:
            result = self.client.subscribe(topic, qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logging.info(f"已订阅主题: {topic}")
            else:
                logging.error(f"订阅主题失败: {topic}, 错误码: {result[0]}")
        except Exception as e:
            logging.error(f"订阅主题时发生错误: {e}")
    
    def connect(self) -> bool:
        """连接到MQTT代理"""
        try:
            logging.info(f"正在连接到MQTT代理: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            logging.error(f"连接MQTT代理失败: {e}")
            return False
    
    def disconnect(self):
        """断开MQTT连接"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logging.info("MQTT连接已断开")
        except Exception as e:
            logging.error(f"断开MQTT连接时发生错误: {e}")
    
    def stop(self):
        """停止MQTT客户端"""
        self.running = False
        self.disconnect()
        logging.info("MQTT客户端已停止")

class MQTTPublisher(MQTTBase):
    """MQTT发布者基类"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.publish_interval = config.get('publish_interval', 30)
        
    

    
    def publish_sensor_data(self, sensor_type: str, data: Dict[str, Any]):
        """
        发布传感器数据
        
        Args:
            sensor_type: 传感器类型
            data: 传感器数据
        """
        try:
            topic = f"{self.topic_prefix}/{sensor_type}"
            self.publish_message(topic, data)
        except Exception as e:
            logging.error(f"发布传感器数据时发生错误: {e}")
    
    def run(self):
        """运行发布者主循环 - 子类需要重写"""
        if not self.connect():
            logging.error("无法连接到MQTT代理，退出")
            return
        
        self.running = True
        logging.info(f"MQTT发布者已启动，发布间隔: {self.publish_interval}秒")
        
        try:
            while self.running:
                # 子类需要重写此方法来实现具体的发布逻辑
                self.publish_cycle()
                time.sleep(self.publish_interval)
                
        except KeyboardInterrupt:
            logging.info("收到键盘中断信号")
        except Exception as e:
            logging.error(f"运行过程中发生错误: {e}")
        finally:
            self.stop()
    
    def publish_cycle(self):
        """发布周期 - 子类需要重写此方法"""
        raise NotImplementedError("子类必须重写 publish_cycle 方法")

class MQTTSubscriber(MQTTBase):
    """MQTT订阅者基类"""
    
    def __init__(self, config: Dict[str, Any], message_handler: Optional[Callable] = None):
        super().__init__(config)
        self.message_handler = message_handler
        self.subscribed_topics = []
    
    def on_message(self, client, userdata, msg):
        """重写消息回调，调用消息处理器"""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            topic = msg.topic
            
            if self.message_handler:
                self.message_handler(topic, payload)
            else:
                self.handle_message(topic, payload)
                
        except json.JSONDecodeError as e:
            logging.error(f"解析JSON消息失败: {e}")
        except Exception as e:
            logging.error(f"处理消息时发生错误: {e}")
    
    def handle_message(self, topic: str, payload: Dict[str, Any]):
        """处理消息 - 子类可重写"""
        logging.info(f"收到消息 [{topic}]: {payload}")
    
    def add_subscription(self, topic: str, qos: int = 1):
        """
        添加订阅
        
        Args:
            topic: 主题
            qos: 服务质量等级
        """
        self.subscribed_topics.append((topic, qos))
    
    def on_connect(self, client, userdata, flags, rc):
        """重写连接回调，自动订阅所有主题"""
        super().on_connect(client, userdata, flags, rc)
        if rc == 0:
            # 连接成功后订阅所有主题
            for topic, qos in self.subscribed_topics:
                self.subscribe_topic(topic, qos)
    
    def run(self):
        """运行订阅者主循环"""
        if not self.connect():
            logging.error("无法连接到MQTT代理，退出")
            return
        
        self.running = True
        logging.info("MQTT订阅者已启动，等待消息...")
        
        try:
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logging.info("收到键盘中断信号")
        except Exception as e:
            logging.error(f"运行过程中发生错误: {e}")
        finally:
            self.stop() 