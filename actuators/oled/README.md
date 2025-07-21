# OLED 显示屏执行器模块

## 概述

该模块通过 MQTT 订阅温湿度传感器数据，并在 OLED 屏幕上实时显示，适用于树莓派 Pi5 I2C OLED 屏（如 SSD1306/SH1106）。

## 文件结构

```
oled/
├── config.ini         # 配置文件
├── config.py          # 配置管理
├── oled.py            # OLED 驱动/显示控制
├── controller.py      # MQTT 订阅者
├── oled_sub.py        # 主程序
├── requirements.txt   # 依赖列表
└── README.md
```

## 配置说明

### MQTT配置
```ini
[mqtt]
broker = localhost
port = 1883
topic = sensor/temperature_humidity
```

### OLED配置
```ini
[oled]
i2c_port = 1
address = 0x3C
driver = sh1106
width = 128
height = 64
```

## 使用方法

1. 修改 `config.ini` 中的参数。
2. 运行主程序：
   ```bash
   python oled_sub.py
   ```

## 功能说明

- **订阅主题**：`sensor/temperature_humidity`
- **消息格式**：
  ```json
  {
    "temperature": 25.1,
    "humidity": 40.2,
    "timestamp": 1710000000
  }
  ```
- **显示内容**：
  - 第一行：温度（如 `25.1°C`）
  - 第二行：湿度（如 `40.2%`）

## 依赖安装

```bash
pip install luma.oled Pillow paho-mqtt configparser
```

如需显示中文，请先安装中文字体：
```bash
sudo apt-get install fonts-wqy-zenhei
```

## 参考
- [pi5-oled-i2c-tools 示例代码](https://github.com/SwartzMss/pi5-oled-i2c-tools) 