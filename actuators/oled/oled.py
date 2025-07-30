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
            " ( ^.^ ) ",
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
        """显示当前时间（只显示时分秒和星期）"""
        image = Image.new("1", (self.width, self.height), "black")
        draw = ImageDraw.Draw(image)
        
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M:%S")
        weekday_str = now.strftime("%A")
        
        try:
            # 时间用大字体
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 28)
            # 星期用中等字体
            week_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 16)
        except:
            time_font = week_font = self.font
        
        # 计算时间位置（居中显示，更靠上一点）
        time_bbox = draw.textbbox((0, 0), time_str, font=time_font)
        time_w = time_bbox[2] - time_bbox[0]
        time_x = (self.width - time_w) // 2
        time_y = 12  # 往上移动
        
        # 星期位置（更靠下一点）
        week_bbox = draw.textbbox((0, 0), weekday_str, font=week_font)
        week_w = week_bbox[2] - week_bbox[0]
        week_x = (self.width - week_w) // 2
        week_y = 48  # 往下移动
        
        # 绘制文本
        draw.text((time_x, time_y), time_str, font=time_font, fill=255)
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
            " ( ^.^ ) " if self.cat_eyes_open else " ( -.- ) ",
            "  > ^ <  "
        ]
        
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 14)
        except:
            small_font = self.font
        
        # 在左半边垂直居中绘制小猫，适度往左移
        line_height = 14
        total_height = len(cat_lines) * line_height
        start_y = (self.height - total_height) // 2
        
        for i, line in enumerate(cat_lines):
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=small_font)
                text_width = bbox[2] - bbox[0]
                # 往左移4个像素，为右边留出更多空间
                x = max(2, (cat_width - text_width) // 2 - 4)
                y = start_y + i * line_height
                draw.text((x, y), line, font=small_font, fill=255)
        
        # === 右边绘制温湿度 ===
        temp_label = "温度:"
        humi_label = "湿度:"
        temp_value = f"{temperature:.1f}°C"
        humi_value = f"{humidity:.1f}%"
        
        try:
            # 标签用小字体
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 10)
            # 数值用中等字体，避免超出边界
            value_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 12)
        except:
            label_font = value_font = self.font
        
        # 右半边起始位置和可用宽度
        right_start_x = cat_width + 1  # 减少间距
        available_width = self.width - right_start_x - 2  # 右边留2像素边距
        
        # 计算各部分宽度
        temp_label_bbox = draw.textbbox((0, 0), temp_label, font=label_font)
        humi_label_bbox = draw.textbbox((0, 0), humi_label, font=label_font)
        temp_value_bbox = draw.textbbox((0, 0), temp_value, font=value_font)
        humi_value_bbox = draw.textbbox((0, 0), humi_value, font=value_font)
        
        max_label_w = max(temp_label_bbox[2] - temp_label_bbox[0], 
                         humi_label_bbox[2] - humi_label_bbox[0])
        max_value_w = max(temp_value_bbox[2] - temp_value_bbox[0],
                         humi_value_bbox[2] - humi_value_bbox[0])
        
        # 确保不超出边界，如果空间不够就紧凑排列
        gap = 2
        total_needed = max_label_w + gap + max_value_w
        if total_needed > available_width:
            gap = max(1, available_width - max_label_w - max_value_w)
        
        # 温度行 - 往上移一点，增加与湿度的间距
        temp_y = 12
        draw.text((right_start_x, temp_y), temp_label, font=label_font, fill=255)
        temp_value_x = right_start_x + max_label_w + gap
        # 确保数值不超出右边界
        max_temp_x = self.width - temp_value_bbox[2] + temp_value_bbox[0] - 2
        temp_value_x = min(temp_value_x, max_temp_x)
        draw.text((temp_value_x, temp_y), temp_value, font=value_font, fill=255)
        
        # 湿度行 - 往下移一点，增加与温度的间距
        humi_y = 45
        draw.text((right_start_x, humi_y), humi_label, font=label_font, fill=255)
        humi_value_x = right_start_x + max_label_w + gap
        # 确保数值不超出右边界
        max_humi_x = self.width - humi_value_bbox[2] + humi_value_bbox[0] - 2
        humi_value_x = min(humi_value_x, max_humi_x)
        draw.text((humi_value_x, humi_y), humi_value, font=value_font, fill=255)
        
        self.device.display(image)

    def _blink_eyes(self):
        """眼睛闪烁回调"""
        self.cat_eyes_open = not self.cat_eyes_open
        # 如果有回调函数，调用它来重新绘制屏幕
        if hasattr(self, '_blink_callback') and self._blink_callback:
            self._blink_callback()
        # 设置下次闪烁
        self._schedule_blink()

    def _schedule_blink(self):
        """安排下次眼睛闪烁"""
        # 随机间隔0.5-1秒闪烁一次（超高频率眨眼）
        import random
        interval = random.uniform(0.5, 1.0)
        if self.blink_timer:
            self.blink_timer.cancel()
        self.blink_timer = threading.Timer(interval, self._blink_eyes)
        self.blink_timer.start()

    def set_blink_callback(self, callback):
        """设置眨眼时的回调函数"""
        self._blink_callback = callback

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