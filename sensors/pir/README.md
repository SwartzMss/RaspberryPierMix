# PIR 红外传感器模块

## 概述

这是一个模块化的PIR红外传感器MQTT发布者，基于gpiozero库实现，支持运动检测和事件驱动的消息发布。适用于HC-SR501等PIR传感器。参考用户示例代码优化实现。

## 文件结构

```
pir/
├── config.ini          # 配置文件
├── config.py           # 配置管理模块
├── sensor.py           # 传感器模块
├── publisher.py        # 发布者模块
├── pir_pub.py          # 主程序
├── requirements.txt    # 依赖文件
└── README.md          # 说明文档
```

## 模块说明

### 1. config.ini - 配置文件
包含所有可配置的参数：
- MQTT代理设置
- 传感器引脚配置
- 检测模式和参数

### 2. config.py - 配置管理
负责读取和解析配置文件，提供类型安全的配置访问。

### 3. sensor.py - 传感器模块
专门处理PIR传感器的运动检测逻辑，基于gpiozero.MotionSensor实现。
- **自动管理**：gpiozero自动处理GPIO设置和事件检测
- **事件回调**：支持when_motion和when_no_motion回调
- **简洁高效**：参考用户示例代码的简洁设计

### 4. publisher.py - 发布者模块
处理MQTT发布逻辑，继承自common模块的EventPublisher基类。
- 事件驱动设计，只在检测到运动时发布消息
- 支持运动保持时间，避免频繁发送重复消息

### 5. pir_pub.py - 主程序
程序入口点，负责初始化各个模块并启动发布者。

## 配置说明

### MQTT配置
```ini
[mqtt]
broker = localhost
port = 1883
# MQTT主题前缀，发布的消息主题格式为: {topic_prefix}/{sensor_type}
topic_prefix = sensor
# 运动检测保持时间（秒） - 检测到运动后多长时间内不重复发送
motion_hold_time = 5
```

### 传感器配置
```ini
[pir]
# BCM GPIO引脚编号，连接到传感器的OUT引脚（默认23，参考用户示例）
pin = 23
# 传感器类型名称
sensor_type = pir_motion
# 传感器稳定时间（秒） - HC-SR501通常需要60秒
stabilize_time = 60
```

## 硬件连接

### PIR传感器 (HC-SR501) 连接方式
```
PIR传感器    →    树莓派
VCC         →    5V 或 3.3V
GND         →    GND
OUT         →    GPIO 23 (BCM编号，物理引脚16，可配置)
```

### 传感器调节
- **敏感度调节**：使用传感器上的电位器调节检测敏感度
- **延时调节**：调节传感器保持高电平的时间
- **触发方式**：单次触发或重复触发（跳线设置）
- **稳定时间**：HC-SR501需要约60秒的预热稳定时间

## 使用方法

1. 安装依赖：
   ```bash
   pip install gpiozero lgpio
   # 或者
   pip install -r requirements.txt
   ```

2. 修改 `config.ini` 文件中的配置参数

3. 运行主程序：
   ```bash
   python pir_pub.py
   ```

## 消息格式

### 运动检测消息
```json
{
    "motion_detected": true,
    "timestamp": 1703123456
}
```

### 无运动状态消息
```json
{
    "motion_detected": false,
    "timestamp": 1703123456
}
```

### 状态消息
```json
{
    "motion_detected": false,
    "timestamp": 1703123456,
    "status": "online"
}
```

## 特性

- **基于gpiozero**：使用简洁高效的gpiozero库，参考用户示例代码
- **事件驱动**：支持运动检测和无运动状态回调
- **防抖处理**：运动保持时间避免频繁触发
- **状态管理**：上线/下线状态通知
- **错误处理**：完善的异常处理和资源清理
- **模拟模式**：在非树莓派环境下可运行（用于开发测试）
- **日志记录**：详细的日志输出，便于调试
- **简洁配置**：精简的配置文件，只保留必要参数

## 注意事项

1. **权限**：需要以适当权限运行以访问GPIO
2. **引脚冲突**：确保配置的GPIO引脚没有被其他程序使用
3. **硬件稳定性**：确保传感器电源稳定，连线牢固
4. **环境因素**：PIR传感器会受到温度变化、阳光等环境因素影响