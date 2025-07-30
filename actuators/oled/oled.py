# -*- coding: utf-8 -*-
"""
OLED 显示控制模块
"""
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106, ssd1306
from PIL import ImageFont, ImageDraw, Image
import datetime
import threading
import time

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
        
        # 小猫眼睛闪烁状态
        self.cat_eyes_open = True
        self.blink_timer = None

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
        
        # 小猫头部图案，简洁可爱
        cat_lines = [
            "  /\\_/\\  ",
            " ( o.o ) ",
            "  > ^ <  "
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

    def show_time(self):
        """显示当前时间"""
        image = Image.new("1", (self.width, self.height), "black")
        draw = ImageDraw.Draw(image)
        
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        weekday_str = now.strftime("%A")
        
        try:
            # 时间用大字体
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
            # 日期用中等字体
            date_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 16)
            # 星期用小字体
            week_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 12)
        except:
            time_font = date_font = week_font = self.font
        
        # 计算时间位置（居中显示）
        time_bbox = draw.textbbox((0, 0), time_str, font=time_font)
        time_w = time_bbox[2] - time_bbox[0]
        time_x = (self.width - time_w) // 2
        time_y = 15
        
        # 日期位置
        date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
        date_w = date_bbox[2] - date_bbox[0]
        date_x = (self.width - date_w) // 2
        date_y = 35
        
        # 星期位置
        week_bbox = draw.textbbox((0, 0), weekday_str, font=week_font)
        week_w = week_bbox[2] - week_bbox[0]
        week_x = (self.width - week_w) // 2
        week_y = 52
        
        # 绘制文本
        draw.text((time_x, time_y), time_str, font=time_font, fill=255)
        draw.text((date_x, date_y), date_str, font=date_font, fill=255)
        draw.text((week_x, week_y), weekday_str, font=week_font, fill=255)
        
        self.device.display(image)

    def show_split_display(self, temperature, humidity):
        """分屏显示：左边小猫，右边温湿度"""
        image = Image.new("1", (self.width, self.height), "black")
        draw = ImageDraw.Draw(image)
        
        # 屏幕分成左右两部分，左边64像素，右边64像素
        cat_width = 64
        temp_width = 64
        
        # === 左边绘制小猫 ===
        cat_lines = [
            "  /\\_/\\  ",
            " ( o.o ) " if self.cat_eyes_open else " ( -.-))",
            "  > ^ <  "
        ]
        
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 10)
        except:
            small_font = self.font
        
        # 在左半边垂直居中绘制小猫
        line_height = 10
        total_height = len(cat_lines) * line_height
        start_y = (self.height - total_height) // 2
        
        for i, line in enumerate(cat_lines):
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=small_font)
                text_width = bbox[2] - bbox[0]
                x = (cat_width - text_width) // 2  # 在左半边居中
                y = start_y + i * line_height
                draw.text((x, y), line, font=small_font, fill=255)
        
        # === 右边绘制温湿度 ===
        temp_str = f"{temperature:.1f}°C"
        humi_str = f"{humidity:.1f}%"
        
        try:
            temp_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 14)
        except:
            temp_font = self.font
        
        # 温度位置（右半边）
        temp_bbox = draw.textbbox((0, 0), temp_str, font=temp_font)
        temp_w = temp_bbox[2] - temp_bbox[0]
        temp_x = cat_width + (temp_width - temp_w) // 2  # 在右半边居中
        temp_y = 20
        
        # 湿度位置
        humi_bbox = draw.textbbox((0, 0), humi_str, font=temp_font)
        humi_w = humi_bbox[2] - humi_bbox[0]
        humi_x = cat_width + (temp_width - humi_w) // 2
        humi_y = 40
        
        # 绘制温湿度
        draw.text((temp_x, temp_y), temp_str, font=temp_font, fill=255)
        draw.text((humi_x, humi_y), humi_str, font=temp_font, fill=255)
        
        # 绘制分割线
        draw.line([(cat_width, 0), (cat_width, self.height)], fill=255, width=1)
        
        self.device.display(image)

    def _blink_eyes(self):
        """眼睛闪烁回调"""
        self.cat_eyes_open = not self.cat_eyes_open
        # 设置下次闪烁
        self._schedule_blink()

    def _schedule_blink(self):
        """安排下次眼睛闪烁"""
        # 随机间隔2-5秒闪烁一次
        import random
        interval = random.uniform(2.0, 5.0)
        if self.blink_timer:
            self.blink_timer.cancel()
        self.blink_timer = threading.Timer(interval, self._blink_eyes)
        self.blink_timer.start()

    def start_cat_animation(self):
        """开始小猫眼睛闪烁动画"""
        self.cat_eyes_open = True
        self._schedule_blink()

    def stop_cat_animation(self):
        """停止小猫眼睛闪烁动画"""
        if self.blink_timer:
            self.blink_timer.cancel()
            self.blink_timer = None
        self.cat_eyes_open = True

    def clear(self):
        image = Image.new("1", (self.width, self.height), "black")
        self.device.display(image) 