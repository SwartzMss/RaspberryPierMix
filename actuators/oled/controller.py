# -*- coding: utf-8 -*-
"""
OLED 订阅者模块
"""
import logging
import json
import paho.mqtt.client as mqtt
from oled import OLEDDisplay

class OLEDSubscriber:
    def __init__(self, config):
        self.broker = config['broker']
        self.port = config['port']
        self.temp_humid_topic = config['topic']     # 温湿度topic
        self.pir_topic = config['pir_topic']  # PIR topic
        self.oled = OLEDDisplay(
            i2c_port=config['i2c_port'],
            address=config['address'],
            driver=config['driver'],
            width=config['width'],
            height=config['height']
        )
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.logger = logging.getLogger(__name__)
        
        # 保存最新数据
        self.latest_temperature = None
        self.latest_humidity = None
        self.motion_detected = False  # 默认无人状态，显示小猫

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("MQTT连接成功，订阅主题: %s 和 %s", self.temp_humid_topic, self.pir_topic)
            client.subscribe(self.temp_humid_topic)
            client.subscribe(self.pir_topic)
            # 初始显示小猫（默认无人状态）
            self.oled.show_cat()
        else:
            self.logger.error("MQTT连接失败，返回码: %s", rc)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            topic = msg.topic
            
            if topic == self.temp_humid_topic:
                # 处理温湿度数据
                temperature = payload.get('temperature')
                humidity = payload.get('humidity')
                if temperature is not None and humidity is not None:
                    self.latest_temperature = temperature
                    self.latest_humidity = humidity
                    self.logger.info(f"收到温湿度数据: {temperature}°C, {humidity}%")
                    # 如果当前有人，立即显示温湿度
                    if self.motion_detected:
                        self.oled.show_temp_humi(temperature, humidity)
                        self.logger.info(f"显示温湿度: {temperature}°C, {humidity}%")
                else:
                    self.logger.warning(f"收到无效温湿度数据: {payload}")
                    
            elif topic == self.pir_topic:
                # 处理PIR运动检测数据
                motion_detected = payload.get('motion_detected', False)
                self.motion_detected = motion_detected
                self.logger.info(f"收到PIR数据: motion_detected={motion_detected}")
                
                if motion_detected:
                    # 有人时显示温湿度（如果有数据的话）
                    if self.latest_temperature is not None and self.latest_humidity is not None:
                        self.oled.show_temp_humi(self.latest_temperature, self.latest_humidity)
                        self.logger.info(f"有人，显示温湿度: {self.latest_temperature}°C, {self.latest_humidity}%")
                    else:
                        self.logger.info("有人但无温湿度数据，等待温湿度数据...")
                else:
                    # 无人时显示小猫
                    self.oled.show_cat()
                    self.logger.info("无人，显示小猫")
            else:
                self.logger.warning(f"收到未知topic的消息: {topic}")
                
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")

    def run(self):
        self.logger.info("启动OLED订阅者...")
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever() 