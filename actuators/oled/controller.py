# -*- coding: utf-8 -*-
"""
OLED 订阅者模块
"""
import logging
import json
import time
import threading
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
        
        # 显示状态管理
        self.show_temp_mode = False  # 是否显示温湿度模式
        self.temp_timer = None       # 10分钟定时器
        self.time_timer = None       # 时间显示定时器
        self.temp_display_duration = 10 * 60  # 10分钟 = 600秒
        self.time_update_interval = 1  # 时间更新间隔1秒

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("MQTT连接成功，订阅主题: %s 和 %s", self.temp_humid_topic, self.pir_topic)
            client.subscribe(self.temp_humid_topic)
            client.subscribe(self.pir_topic)
            # 初始显示时间（默认无人状态）
            self.oled.show_time()
            self._start_time_display()
        else:
            self.logger.error("MQTT连接失败，返回码: %s", rc)
    
    def _switch_to_time_display(self):
        """定时器回调：切换回时间显示"""
        self.show_temp_mode = False
        self.oled.stop_cat_animation()  # 停止小猫眼睛闪烁
        self.oled.show_time()
        self._start_time_display()  # 开始时间显示定时器
        self.logger.info("10分钟到期，切换回时间显示")
    
    def _start_temp_display_timer(self):
        """启动10分钟温湿度显示定时器"""
        # 取消之前的定时器
        if self.temp_timer:
            self.temp_timer.cancel()
        
        # 启动新的定时器
        self.temp_timer = threading.Timer(self.temp_display_duration, self._switch_to_time_display)
        self.temp_timer.start()
        self.logger.info(f"启动温湿度显示定时器，{self.temp_display_duration}秒后切换回时间显示")
    
    def _start_time_display(self):
        """启动时间显示定时器（每秒更新）"""
        # 取消之前的时间定时器
        if self.time_timer:
            self.time_timer.cancel()
        
        # 启动时间更新定时器
        self.time_timer = threading.Timer(self.time_update_interval, self._update_time_display)
        self.time_timer.start()
    
    def _update_time_display(self):
        """更新时间显示"""
        if not self.show_temp_mode:  # 只有在非温湿度模式下才更新时间
            self.oled.show_time()
            # 继续下次更新
            self._start_time_display()
    
    def _stop_time_display(self):
        """停止时间显示定时器"""
        if self.time_timer:
            self.time_timer.cancel()
            self.time_timer = None

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
                    # 如果当前在温湿度显示模式，立即更新分屏显示
                    if self.show_temp_mode:
                        self.oled.show_split_display(temperature, humidity)
                        self.logger.info(f"更新分屏显示: {temperature}°C, {humidity}%")
                else:
                    self.logger.warning(f"收到无效温湿度数据: {payload}")
                    
            elif topic == self.pir_topic:
                # 处理PIR运动检测数据
                motion_detected = payload.get('motion_detected', False)
                self.logger.info(f"收到PIR数据: motion_detected={motion_detected}")
                
                if motion_detected:
                    # 只处理有人的消息
                    self.show_temp_mode = True
                    self._stop_time_display()  # 停止时间显示
                    self._start_temp_display_timer()  # 启动10分钟定时器
                    self.oled.start_cat_animation()  # 开始小猫眼睛闪烁动画
                    
                    # 立即显示分屏（如果有温湿度数据的话）
                    if self.latest_temperature is not None and self.latest_humidity is not None:
                        self.oled.show_split_display(self.latest_temperature, self.latest_humidity)
                        self.logger.info(f"检测到有人，分屏显示: {self.latest_temperature}°C, {self.latest_humidity}%")
                    else:
                        self.logger.info("检测到有人但无温湿度数据，等待温湿度数据...")
                else:
                    # 忽略无人消息
                    self.logger.debug("收到无人消息，忽略处理")
            else:
                self.logger.warning(f"收到未知topic的消息: {topic}")
                
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")

    def run(self):
        self.logger.info("启动OLED订阅者...")
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号")
        finally:
            # 清理所有定时器
            if self.temp_timer:
                self.temp_timer.cancel()
                self.logger.info("已取消温湿度显示定时器")
            if self.time_timer:
                self.time_timer.cancel()
                self.logger.info("已取消时间显示定时器")
            self.oled.stop_cat_animation()  # 停止小猫眼睛闪烁
            self.client.disconnect()
            self.logger.info("OLED订阅者已停止") 