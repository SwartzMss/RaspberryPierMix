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
        self.margin = 8  # 上下左右边距

    def show_temp_humi(self, temperature, humidity):
        image = Image.new("1", (self.width, self.height), "black")
        draw = ImageDraw.Draw(image)
        temp_str = f"温度: {temperature:.1f}°C"
        humi_str = f"湿度: {humidity:.1f}%"
        # 用 textbbox 计算文本宽高，实现居中且留边距
        temp_bbox = draw.textbbox((0, 0), temp_str, font=self.font)
        temp_w = temp_bbox[2] - temp_bbox[0]
        temp_h = temp_bbox[3] - temp_bbox[1]
        humi_bbox = draw.textbbox((0, 0), humi_str, font=self.font)
        humi_w = humi_bbox[2] - humi_bbox[0]
        humi_h = humi_bbox[3] - humi_bbox[1]
        # 水平居中且左右留边距
        temp_x = max(self.margin, (self.width - temp_w) // 2)
        humi_x = max(self.margin, (self.width - humi_w) // 2)
        # 上下留边距，两行内容垂直居中分布
        total_text_height = temp_h + humi_h + self.margin
        temp_y = self.margin
        humi_y = self.height - humi_h - self.margin
        draw.text((temp_x, temp_y), temp_str, font=self.font, fill=255)
        draw.text((humi_x, humi_y), humi_str, font=self.font, fill=255)
        self.device.display(image)

    def show_cat(self):
        """显示可爱的小猫图案"""
        image = Image.new("1", (self.width, self.height), "black")
        draw = ImageDraw.Draw(image)
        
        # 小猫ASCII艺术图案，适合128x64的屏幕
        cat_lines = [
            "  /\\_/\\  ",
            " ( o.o ) ",
            "  > ^ <  ",
            "",
            "   喵~   ",
            "  无人   "
        ]
        
        # 使用较小的字体绘制小猫
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 12)
        except:
            small_font = self.font
        
        # 计算总高度来垂直居中
        line_height = 12
        total_height = len(cat_lines) * line_height
        start_y = (self.height - total_height) // 2
        
        for i, line in enumerate(cat_lines):
            if line.strip():  # 跳过空行
                # 计算水平居中位置
                bbox = draw.textbbox((0, 0), line, font=small_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                y = start_y + i * line_height
                draw.text((x, y), line, font=small_font, fill=255)
        
        self.device.display(image)

    def clear(self):
        image = Image.new("1", (self.width, self.height), "black")
        self.device.display(image) 