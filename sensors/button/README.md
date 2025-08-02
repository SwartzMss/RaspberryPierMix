# Button 按键事件传感器

## 概述
本模块用于检测物理按键（如接在GPIO17），并通过MQTT发布按键事件，适用于树莓派等设备。采用统一的传感器数据格式。

## 目录结构
```
button/
├── config.ini         # 配置文件
├── config.py          # 配置管理
├── publish.py         # MQTT发布逻辑
├── button_pub.py      # 主程序
├── requirements.txt   # 依赖列表
└── README.md
```

## 配置说明

### MQTT配置
```ini
[mqtt]
broker = localhost
port = 1883
topic_prefix = sensor
publish_interval = 1
```

### 按键配置
```ini
[button]
button_gpio = 17
gpio_chip = 0
sensor_type = button
```

## 依赖安装
```bash
pip install gpiozero paho-mqtt
```

## 使用方法
1. 修改 `config.ini` 中的参数。
2. 运行发布者：
   ```bash
   python button_pub.py
   ```
3. 按下按键时，会向MQTT发布标准化的传感器数据：
   - topic: `sensor/sensor`
   - payload: 
   ```json
   {
     "type": "button",
     "params": {
       "action": "pressed",
       "timestamp": 1710000000
     },
     "timestamp": 1710000000
   }
   ```

## 架构说明
- 继承 `EventPublisher` 基类，实现事件驱动型传感器
- 使用统一的传感器数据格式，便于系统集成
- 支持按键按下和释放两种事件
- 自动处理MQTT连接、数据发布和生命周期管理

## 特性
- 支持按键防抖（默认50ms）
- 事件驱动，实时响应
- 统一的错误处理和日志记录
- 优雅的启动和停止机制
- 可作为独立传感器进程运行 