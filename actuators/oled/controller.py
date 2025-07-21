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
        self.topic = config['topic']
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

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("MQTT连接成功，订阅主题: %s", self.topic)
            client.subscribe(self.topic)
        else:
            self.logger.error("MQTT连接失败，返回码: %s", rc)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            temperature = payload.get('temperature')
            humidity = payload.get('humidity')
            if temperature is not None and humidity is not None:
                self.oled.show_temp_humi(temperature, humidity)
                self.logger.info(f"显示温湿度: {temperature}°C, {humidity}%")
            else:
                self.logger.warning(f"收到无效数据: {payload}")
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")

    def run(self):
        self.logger.info("启动OLED订阅者...")
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever() 