# -*- coding: utf-8 -*-
"""
OLED 订阅者模块 - 接收manager控制消息
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
        self.control_topic = config['topic']  # 控制消息topic
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
        
        # 设置小猫眨眼回调，用于重新绘制分屏显示
        self.oled.set_blink_callback(self._redraw_split_display)
        
        # 显示状态管理
        self.show_temp_mode = False  # 是否显示温湿度模式
        self.time_timer = None       # 时间显示定时器
        self.time_update_interval = 1  # 时间更新间隔1秒

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("MQTT连接成功，订阅控制主题: %s", self.control_topic)
            client.subscribe(self.control_topic)
            # 初始显示时间（默认无人状态）
            self.oled.show_time()
            self._start_time_display()
        else:
            self.logger.error("MQTT连接失败，返回码: %s", rc)
    
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
    
    def _redraw_split_display(self):
        """重新绘制分屏显示（小猫眨眼时的回调）"""
        if self.show_temp_mode and self.latest_temperature is not None and self.latest_humidity is not None:
            self.oled.show_split_display(self.latest_temperature, self.latest_humidity)
    
    def _stop_time_display(self):
        """停止时间显示定时器"""
        if self.time_timer:
            self.time_timer.cancel()
            self.time_timer = None

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            topic = msg.topic
            
            if topic == self.control_topic:
                # 处理控制消息
                action = payload.get('action')
                data = payload.get('data', {})
                
                self.logger.info(f"收到OLED控制消息: {action} - {data}")
                
                if action == 'show_time':
                    # 显示时间
                    self.show_temp_mode = False
                    self._stop_time_display()  # 停止时间显示
                    self.oled.stop_cat_animation()  # 停止小猫眼睛闪烁
                    self.oled.show_time()
                    self._start_time_display()  # 开始时间显示定时器
                    self.logger.info("切换到时间显示模式")
                    
                elif action == 'show_temp_humi':
                    # 显示温湿度（分屏模式）
                    temperature = data.get('temperature')
                    humidity = data.get('humidity')
                    
                    if temperature is not None and humidity is not None:
                        self.latest_temperature = temperature
                        self.latest_humidity = humidity
                        self.show_temp_mode = True
                        self._stop_time_display()  # 停止时间显示
                        self.oled.start_cat_animation()  # 开始小猫眼睛闪烁动画
                        self.oled.show_split_display(temperature, humidity)
                        self.logger.info(f"切换到温湿度显示模式: {temperature}°C, {humidity}%")
                    else:
                        self.logger.warning(f"温湿度数据无效: {data}")
                        
                elif action == 'update_temp_humi':
                    # 更新温湿度数据（当前在温湿度显示模式）
                    temperature = data.get('temperature')
                    humidity = data.get('humidity')
                    
                    if temperature is not None and humidity is not None:
                        self.latest_temperature = temperature
                        self.latest_humidity = humidity
                        
                        if self.show_temp_mode:
                            self.oled.show_split_display(temperature, humidity)
                            self.logger.info(f"更新温湿度显示: {temperature}°C, {humidity}%")
                        else:
                            self.logger.debug(f"收到温湿度更新但不在显示模式: {temperature}°C, {humidity}%")
                    else:
                        self.logger.warning(f"温湿度更新数据无效: {data}")
                        
                else:
                    self.logger.warning(f"未知的OLED控制动作: {action}")
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
            if self.time_timer:
                self.time_timer.cancel()
                self.logger.info("已取消时间显示定时器")
            self.oled.stop_cat_animation()  # 停止小猫眼睛闪烁
            self.client.disconnect()
            self.logger.info("OLED订阅者已停止") 