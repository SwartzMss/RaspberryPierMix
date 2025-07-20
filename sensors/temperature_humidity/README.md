# DHT22 温湿度传感器模块

## 概述

这是一个模块化的DHT22温湿度传感器MQTT发布者，支持配置文件管理和功能分离。

## 文件结构

```
temperature_humidity/
├── config.ini          # 配置文件
├── config.py           # 配置管理模块
├── sensor.py           # 传感器模块
├── publisher.py        # 发布者模块
├── dht22_pub.py        # 主程序
├── requirements.txt    # 依赖文件
└── README.md          # 说明文档
```

## 模块说明

### 1. config.ini - 配置文件
包含所有可配置的参数：
- MQTT代理设置
- 传感器引脚配置

### 2. config.py - 配置管理
负责读取和解析配置文件，提供类型安全的配置访问。

### 3. sensor.py - 传感器模块
专门处理DHT22传感器的读取逻辑，包含重试机制和错误处理。

### 4. publisher.py - 发布者模块
处理MQTT发布逻辑，继承自common模块的MQTT基类。

### 5. dht22_pub.py - 主程序
程序入口点，负责初始化各个模块并启动发布者。

## 配置说明

### MQTT配置
```ini
[mqtt]
broker = localhost
port = 1883
topic_prefix = sensor
publish_interval = 30
```

### 传感器配置
```ini
[dht22]
pin = 4
sensor_type = DHT22
retry_count = 3
retry_delay = 2
```



## 使用方法

1. 修改 `config.ini` 文件中的配置参数
2. 运行主程序：
   ```bash
   python dht22_pub.py
   ```

## 优势

- **模块化设计**：功能分离，易于维护和扩展
- **配置文件管理**：支持外部配置，无需修改代码
- **错误处理**：完善的异常处理和重试机制
- **日志记录**：详细的日志输出，便于调试
- **类型安全**：使用类型注解，提高代码质量 