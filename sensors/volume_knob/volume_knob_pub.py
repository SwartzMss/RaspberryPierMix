# -*- coding: utf-8 -*-
"""
音量旋钮传感器主程序 - MQTT发布者
支持校准和实时音量监控
"""

import sys
import os
import argparse
import logging
import signal

# 添加common模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from config import ConfigManager
from publish import VolumeKnobPublisher

def setup_logging(level=logging.INFO):
    """设置日志配置"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('volume_knob.log', encoding='utf-8')
        ]
    )

def signal_handler(signum, frame):
    """信号处理器"""
    logging.info(f"收到信号 {signum}，正在退出...")
    sys.exit(0)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='音量旋钮传感器 MQTT 发布者',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python volume_knob_pub.py                    # 启动MQTT发布者
  python volume_knob_pub.py --calibrate        # 校准电位器
  python volume_knob_pub.py --status           # 显示当前状态
  python volume_knob_pub.py --test             # 测试模式
  python volume_knob_pub.py --config config.ini # 使用指定配置文件
        """
    )
    
    parser.add_argument('--calibrate', '-c', action='store_true',
                       help='校准电位器')
    parser.add_argument('--status', '-s', action='store_true',
                       help='显示当前状态')
    parser.add_argument('--test', '-t', action='store_true',
                       help='测试模式，只显示读数')
    parser.add_argument('--config', '-f', default='config.ini',
                       help='配置文件路径 (默认: config.ini)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细日志输出')
    parser.add_argument('--daemon', '-d', action='store_true',
                       help='后台运行模式')
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 加载配置
        config_manager = ConfigManager(args.config)
        config = config_manager.get_all_config()
        
        # 创建发布者实例
        publisher = VolumeKnobPublisher(config, config_manager)
        
        if args.calibrate:
            # 校准模式
            print("🎛️  开始电位器校准...")
            print("请按照提示操作电位器")
            print("-" * 50)
            
            try:
                result = publisher.calibrate_sensor()
                print("\n✅ 校准完成!")
                print(f"最小电压: {result['min_voltage']:.3f}V")
                print(f"最大电压: {result['max_voltage']:.3f}V")
                print(f"电压范围: {result['voltage_range']:.3f}V")
                print(f"中间电压: {result['mid_voltage']:.3f}V")
                
                if result['voltage_range'] < 0.5:
                    print("⚠️  警告: 电压范围较小，可能影响精度")
                elif result['voltage_range'] > 6.0:
                    print("⚠️  警告: 电压范围较大，请检查接线")
                else:
                    print("✅ 电压范围正常")
                    
            except Exception as e:
                logging.error(f"校准失败: {e}")
                sys.exit(1)
                
        elif args.status:
            # 状态模式
            print("📊 当前状态:")
            print("-" * 30)
            
            status = publisher.get_current_status()
            if status:
                print(f"音量: {status['volume']}%")
                print(f"传感器信息: {status['sensor_info']}")
                print(f"时间戳: {status['timestamp']}")
            else:
                print("❌ 无法获取状态")
                
        elif args.test:
            # 测试模式
            print("🧪 测试模式 - 实时显示音量读数")
            print("转动电位器观察数值，按Ctrl+C退出")
            print("-" * 50)
            
            try:
                while True:
                    status = publisher.get_current_status()
                    if status:
                        volume = status['volume']
                        # 显示音量条
                        bar_length = 30
                        filled = int(bar_length * volume / 100)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        print(f"\r🔊 {volume:3d}% [{bar}]", end='', flush=True)
                    else:
                        print("\r❌ 读取失败", end='', flush=True)
                    
                    import time
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                print("\n\n👋 测试结束")
                
        else:
            # 正常MQTT发布模式
            print("🚀 启动音量旋钮 MQTT 发布者...")
            print(f"配置文件: {args.config}")
            print(f"MQTT主题: {config.get('mqtt_topic', 'sensors/volume_knob')}")
            print(f"发布间隔: {config.get('read_interval', 0.1)}秒")
            print(f"变化阈值: {config.get('volume_threshold', 2)}%")
            print("-" * 50)
            
            if args.daemon:
                print("🔄 后台运行模式")
                # 这里可以添加后台运行的逻辑
                
            # 启动发布者
            publisher.run()
            
    except KeyboardInterrupt:
        logging.info("收到中断信号，正在退出...")
    except Exception as e:
        logging.error(f"程序运行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
