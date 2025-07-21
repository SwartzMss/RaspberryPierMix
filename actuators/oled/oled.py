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
        self.font = ImageFont.truetype(font_path or "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 18)

    def show_temp_humi(self, temperature, humidity):
        image = Image.new("1", (self.width, self.height), "black")
        draw = ImageDraw.Draw(image)
        temp_str = f"温度: {temperature:.1f}°C"
        humi_str = f"湿度: {humidity:.1f}%"
        # 用 textbbox 计算文本宽高，实现居中
        temp_bbox = draw.textbbox((0, 0), temp_str, font=self.font)
        temp_w = temp_bbox[2] - temp_bbox[0]
        temp_h = temp_bbox[3] - temp_bbox[1]
        humi_bbox = draw.textbbox((0, 0), humi_str, font=self.font)
        humi_w = humi_bbox[2] - humi_bbox[0]
        humi_h = humi_bbox[3] - humi_bbox[1]
        temp_x = (self.width - temp_w) // 2
        humi_x = (self.width - humi_w) // 2
        temp_y = 8
        humi_y = self.height // 2 + 4
        draw.text((temp_x, temp_y), temp_str, font=self.font, fill=255)
        draw.text((humi_x, humi_y), humi_str, font=self.font, fill=255)
        self.device.display(image)

    def clear(self):
        image = Image.new("1", (self.width, self.height), "black")
        self.device.display(image) 