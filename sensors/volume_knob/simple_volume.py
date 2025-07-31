#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单音量控制 - 直接本地控制，无MQTT
基于 https://github.com/SwartzMss/pi5-potentiometer-tools
"""

import time
import os
import logging

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError:
    print("请安装依赖: pip install adafruit-circuitpython-ads1x15")
    exit(1)

class SimpleVolumeControl:
    """简单音量控制器"""
    
    def __init__(self, channel=2):
        """
        初始化音量控制器
        
        Args:
            channel: ADS1115通道 (0-3，对应A0-A3)
        """
        self.channel = channel
        self.last_volume = None
        
        # 初始化ADS1115
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = 2/3  # 支持0-6.144V
        
        channel_map = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}
        self.ads_channel = AnalogIn(ads, channel_map[channel])
        
        print(f"✅ 音量控制器初始化完成，使用通道A{channel}")
    
    def read_volume(self):
        """读取音量百分比 (0-100)"""
        voltage = self.ads_channel.voltage
        # 简单线性映射：0V=0%, 5V=100%
        volume = max(0, min(100, int(voltage / 5.0 * 100)))
        return volume, voltage
    
    def set_system_volume(self, volume):
        """设置系统音量"""
        try:
            # 使用amixer控制ALSA音量
            cmd = f"amixer set Master {volume}%"
            result = os.system(cmd)
            if result == 0:
                return True
            else:
                # 尝试pulseaudio
                cmd = f"pactl set-sink-volume @DEFAULT_SINK@ {volume}%"
                return os.system(cmd) == 0
        except Exception as e:
            print(f"设置音量失败: {e}")
            return False
    
    def run(self, threshold=2):
        """
        运行音量控制循环
        
        Args:
            threshold: 音量变化阈值，超过此值才更新系统音量
        """
        print("🎛️  简单音量控制已启动")
        print("转动电位器控制音量，按Ctrl+C退出")
        print("-" * 40)
        
        try:
            while True:
                volume, voltage = self.read_volume()
                
                # 只在有显著变化时更新
                if self.last_volume is None or abs(volume - self.last_volume) >= threshold:
                    if self.set_system_volume(volume):
                        # 显示音量条
                        bar_length = 20
                        filled = int(bar_length * volume / 100)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        
                        print(f"\r🔊 {volume:3d}% [{bar}] {voltage:.2f}V", end='', flush=True)
                        self.last_volume = volume
                    else:
                        print(f"\r❌ 音量设置失败: {volume}%", end='', flush=True)
                
                time.sleep(0.1)  # 100ms检查间隔
                
        except KeyboardInterrupt:
            print("\n\n👋 音量控制已停止")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='简单音量控制器')
    parser.add_argument('--channel', '-c', type=int, default=2, 
                       help='ADS1115通道 (0-3，默认2=A2)')
    parser.add_argument('--threshold', '-t', type=int, default=2,
                       help='音量变化阈值 (默认2%%)')
    parser.add_argument('--test', action='store_true',
                       help='测试模式，只显示读数不控制音量')
    
    args = parser.parse_args()
    
    # 创建音量控制器
    controller = SimpleVolumeControl(channel=args.channel)
    
    if args.test:
        # 测试模式
        print("🧪 测试模式 - 只显示读数")
        print("转动电位器观察数值，按Ctrl+C退出")
        print("-" * 40)
        
        try:
            while True:
                volume, voltage = controller.read_volume()
                print(f"\r音量: {volume:3d}% | 电压: {voltage:.3f}V", end='', flush=True)
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\n测试结束")
    else:
        # 正常模式
        controller.run(threshold=args.threshold)

if __name__ == "__main__":
    main()