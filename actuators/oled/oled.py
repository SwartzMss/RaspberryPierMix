# -*- coding: utf-8 -*-
"""
OLED 显示控制模块
"""
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106, ssd1306
from PIL import ImageFont, ImageDraw, Image

class OLEDDisplay:
    def __init__(self, i2c_port, address, driver, width, height, font_path=None):
        serial = i2c(port=i2c_port, address=address)
        if driver == "sh1106":
            self.device = sh1106(serial, width=width, height=height)
        else:
            self.device = ssd1306(serial, width=width, height=height)
        self.width = width
        self.height = height
        self.font = ImageFont.truetype(font_path or "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)

    def show_temp_humi(self, temperature, humidity):
        image = Image.new("1", (self.width, self.height), "black")
        draw = ImageDraw.Draw(image)
        temp_str = f"温度: {temperature:.1f}°C"
        humi_str = f"湿度: {humidity:.1f}%"
        draw.text((0, 0), temp_str, font=self.font, fill=255)
        draw.text((0, 32), humi_str, font=self.font, fill=255)
        self.device.display(image)

    def clear(self):
        image = Image.new("1", (self.width, self.height), "black")
        self.device.display(image) 