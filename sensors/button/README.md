# Button 按键事件传感器

## 概述
本模块用于检测物理按键（如接在GPIO17），并通过MQTT发布按键事件，适用于树莓派等设备。

## 目录结构
```
button/
├── config.ini         # 配置文件
├── sensor.py          # 按键读取逻辑
├── publisher.py       # MQTT发布逻辑
├── requirements.txt   # 依赖列表
└── README.md
```

## 配置说明

### MQTT配置
```ini
[mqtt]
broker = localhost
port = 1883
topic_prefix = button
publish_interval = 1
```

### 按键配置
```ini
[button]
button_gpio = 17
gpio_chip = 0
```

## 依赖安装
```bash
pip install lgpio paho-mqtt
```

## 使用方法
1. 修改 `config.ini` 中的参数。
2. 运行发布者：
   ```bash
   python publisher.py
   ```
3. 按下按键时，会向MQTT发布如下事件：
   - topic: `sensor/button`
   - payload: `{ "event": "pressed", "timestamp": 1710000000 }`

## 说明
- 可根据需要修改GPIO编号和MQTT参数。
- 可作为独立传感器进程运行。 