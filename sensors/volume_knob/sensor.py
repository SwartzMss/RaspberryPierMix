# -*- coding: utf-8 -*-
"""
音量旋钮传感器模块（基于ADS1115和电位器）
参考: https://github.com/SwartzMss/pi5-potentiometer-tools
支持校准结果的持久化保存
"""

import time
import logging
from typing import Dict, Any, Optional
from collections import deque

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError as e:
    logging.warning(f"ADS1115库导入失败: {e}，使用模拟模式")
    
    # 模拟模式用于开发测试
    class MockAnalogIn:
        def __init__(self, ads, channel):
            self.channel = channel
            self._voltage = 2.5  # 模拟中间值
            
        @property
        def voltage(self):
            # 模拟电压变化
            import random
            self._voltage += random.uniform(-0.1, 0.1)
            return max(0, min(5.0, self._voltage))
            
        @property
        def value(self):
            return int(self.voltage / 5.0 * 65535)
    
    class MockADS:
        def __init__(self, i2c, address=0x48):
            self.gain = 2/3
        
        P0 = 0
        P1 = 1 
        P2 = 2
        P3 = 3
            
    # 创建模拟ADS模块
    class MockADSModule:
        ADS1115 = MockADS
        P0 = 0
        P1 = 1
        P2 = 2 
        P3 = 3
    
    # 创建模拟board模块
    class MockBoard:
        SCL = "SCL"
        SDA = "SDA"
    
    # 创建模拟busio模块 
    class MockBusio:
        @staticmethod
        def I2C(scl, sda):
            return "mock_i2c"
    
    AnalogIn = MockAnalogIn
    ADS = MockADSModule
    board = MockBoard
    busio = MockBusio

logger = logging.getLogger(__name__)

class VolumeKnobSensor:
    """音量旋钮传感器类（基于ADS1115）"""
    
    def __init__(self, config: Dict[str, Any], config_manager=None):
        """
        初始化音量旋钮传感器
        
        Args:
            config: 传感器配置字典
            config_manager: 配置管理器实例（用于保存校准结果）
        """
        self.config = config
        self.config_manager = config_manager
        
        # 电位器配置
        self.channel = config.get('channel', 2)  # A2通道
        self.min_voltage = config.get('min_voltage', -1.0)
        self.max_voltage = config.get('max_voltage', -1.0)
        self.min_volume = config.get('min_volume', 0)
        self.max_volume = config.get('max_volume', 100)
        self.stabilize_samples = config.get('stabilize_samples', 5)
        
        # 历史值缓存用于稳定性处理
        self.voltage_history = deque(maxlen=self.stabilize_samples)
        self.last_volume = None
        
        # 🔥 关键：检查校准状态，拒绝无效值
        if not self._validate_calibration():
            logger.error("❌ 音量旋钮未校准或校准值无效！")
            logger.error("📋 请先进行校准：")
            logger.error("   python volume_pub.py --calibrate")
            logger.error("💡 或者参考文档： cat README.md")
            raise ValueError("音量旋钮未校准，无法启动服务")
        
        # 初始化ADS1115
        self._init_ads1115(config)
        
        logger.info(f"✅ 音量旋钮传感器初始化完成: 通道A{self.channel}")
        logger.info(f"✅ 校准电压范围: {self.min_voltage:.3f}V - {self.max_voltage:.3f}V (范围: {self.max_voltage - self.min_voltage:.3f}V)")
    
    def _init_ads1115(self, config: Dict[str, Any]):
        """初始化ADS1115"""
        try:
            # I2C总线初始化
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # ADS1115初始化
            ads = ADS.ADS1115(i2c, address=int(config.get('i2c_address', '0x48'), 16))
            
            # 设置增益 - 2/3x 支持 ±6.144V
            ads.gain = config.get('gain', 2/3)
            
            # 选择通道
            channel_map = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}
            if self.channel not in channel_map:
                raise ValueError(f"无效的通道号: {self.channel}")
                
            self.ads_channel = AnalogIn(ads, channel_map[self.channel])
            
            logger.info(f"ADS1115初始化成功，增益: {ads.gain}x")
            
        except Exception as e:
            logger.error(f"ADS1115初始化失败: {e}")
            raise
    
    def read_raw_data(self) -> Dict[str, Any]:
        """
        读取原始传感器数据
        
        Returns:
            包含原始ADC值和电压的字典
        """
        try:
            voltage = self.ads_channel.voltage
            raw_value = self.ads_channel.value
            
            return {
                'voltage': round(voltage, 3),
                'raw_value': raw_value,
                'timestamp': int(time.time())
            }
            
        except Exception as e:
            logger.error(f"读取ADS1115数据失败: {e}")
            return None
    
    def _stabilize_reading(self, voltage: float) -> float:
        """
        稳定读数，减少抖动
        
        Args:
            voltage: 当前电压读数
            
        Returns:
            稳定后的电压值
        """
        self.voltage_history.append(voltage)
        
        if len(self.voltage_history) < self.stabilize_samples:
            return voltage
            
        # 计算平均值，去除异常值
        sorted_values = sorted(self.voltage_history)
        # 去掉最高和最低值，取平均
        stable_values = sorted_values[1:-1] if len(sorted_values) > 2 else sorted_values
        
        return sum(stable_values) / len(stable_values)
    
    def voltage_to_volume(self, voltage: float) -> int:
        """
        将电压值转换为音量百分比
        
        Args:
            voltage: 电压值
            
        Returns:
            音量百分比 (0-100)
        """
        # 限制电压范围
        voltage = max(self.min_voltage, min(self.max_voltage, voltage))
        
        # 线性映射到音量范围
        voltage_range = self.max_voltage - self.min_voltage
        volume_range = self.max_volume - self.min_volume
        
        if voltage_range == 0:
            return self.min_volume
            
        volume = self.min_volume + (voltage - self.min_voltage) * volume_range / voltage_range
        
        return max(self.min_volume, min(self.max_volume, round(volume)))
    
    def read_volume(self) -> Optional[Dict[str, Any]]:
        """
        读取音量数据
        
        Returns:
            音量数据字典，包含音量百分比、电压等信息
        """
        raw_data = self.read_raw_data()
        if not raw_data:
            return None
            
        # 稳定化处理
        stable_voltage = self._stabilize_reading(raw_data['voltage'])
        
        # 转换为音量百分比
        volume = self.voltage_to_volume(stable_voltage)
        
        return {
            'volume': volume,
            'timestamp': raw_data['timestamp']
        }
    
    def has_significant_change(self, current_volume: int, threshold: int = 2) -> bool:
        """
        检查音量是否有显著变化
        
        Args:
            current_volume: 当前音量
            threshold: 变化阈值
            
        Returns:
            是否有显著变化
        """
        if self.last_volume is None:
            self.last_volume = current_volume
            return True
            
        if abs(current_volume - self.last_volume) >= threshold:
            self.last_volume = current_volume
            return True
            
        return False
    
    def calibrate(self) -> Dict[str, float]:
        """
        电位器校准功能 - 支持结果持久化保存
        
        Returns:
            校准结果
        """
        logger.info("开始电位器校准...")
        
        def read_stable_voltage(prompt: str, samples: int = 10) -> float:
            print(prompt)
            time.sleep(3)  # 给用户时间调整
            
            readings = []
            for i in range(samples):
                data = self.read_raw_data()
                if data:
                    readings.append(data['voltage'])
                    print(f"  采样 {i+1}/{samples}: {data['voltage']:.3f}V", end='\r')
                time.sleep(0.1)
                
            print()  # 换行
            return sum(readings) / len(readings) if readings else 0.0
        
        # 校准最小值
        min_voltage = read_stable_voltage("📍 请将电位器旋转到最小位置（逆时针到底），等待3秒...")
        
        # 校准最大值
        max_voltage = read_stable_voltage("📍 请将电位器旋转到最大位置（顺时针到底），等待3秒...")
        
        # 校准中间值验证
        mid_voltage = read_stable_voltage("📍 请将电位器旋转到中间位置，等待3秒...")
        
        result = {
            'min_voltage': round(min_voltage, 3),
            'max_voltage': round(max_voltage, 3),
            'mid_voltage': round(mid_voltage, 3),
            'voltage_range': round(max_voltage - min_voltage, 3)
        }
        
        logger.info(f"校准完成: {result}")
        
        # 🔥 关键：更新内存中的配置
        self.min_voltage = min_voltage
        self.max_voltage = max_voltage
        
        # 🔥 关键：如果有配置管理器，保存到文件
        if self.config_manager:
            try:
                self.config_manager.update_volume_calibration(min_voltage, max_voltage)
                logger.info("校准结果已保存到配置文件")
            except Exception as e:
                logger.error(f"保存校准结果失败: {e}")
        else:
            print("⚠️  注意: 校准结果未保存到配置文件，重启后会丢失")
        
        return result
    
    def _validate_calibration(self) -> bool:
        """
        验证校准值是否有效
        
        Returns:
            bool: True=校准值有效, False=校准值无效
        """
        # 检查是否为无效默认值
        if self.min_voltage == -1.0 and self.max_voltage == -1.0:
            logger.warning("⚠️  检测到无效默认值（-1.0V, -1.0V）")
            return False
        
        # 检查是否为其他无效值
        if self.min_voltage < 0 or self.max_voltage < 0:
            logger.warning(f"⚠️  检测到负电压值: {self.min_voltage:.3f}V, {self.max_voltage:.3f}V")
            return False
            
        if self.min_voltage >= self.max_voltage:
            logger.warning(f"⚠️  最小电压大于等于最大电压: {self.min_voltage:.3f}V >= {self.max_voltage:.3f}V")
            return False
            
        # 检查电压范围是否合理
        voltage_range = self.max_voltage - self.min_voltage
        
        if voltage_range < 0.5:
            logger.warning(f"⚠️  电压范围过小: {voltage_range:.3f}V （少于0.5V）")
            return False
        
        if voltage_range > 6.0:
            logger.warning(f"⚠️  电压范围过大: {voltage_range:.3f}V （大于6.0V）")
            return False
        
        logger.info(f"✅ 校准值验证通过: {self.min_voltage:.3f}V - {self.max_voltage:.3f}V")
        return True
        
    def get_sensor_info(self) -> Dict[str, Any]:
        """获取传感器信息"""
        return {
            'type': 'VolumeKnob',
            'channel': f'A{self.channel}',
            'voltage_range': f'{self.min_voltage}V - {self.max_voltage}V',
            'volume_range': f'{self.min_volume}% - {self.max_volume}%',
            'i2c_address': self.config.get('i2c_address', '0x48')
        }