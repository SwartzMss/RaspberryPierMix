# 传感器数据管理模块

## 功能概述

这个管理模块负责处理传感器数据并发布业务逻辑相关的消息给执行器。主要功能包括：

1. **订阅所有传感器数据**：温湿度、PIR运动检测、按钮、电位器
2. **业务逻辑处理**：根据传感器类型进行相应的业务处理
3. **消息路由**：将处理后的消息发送给相应的执行器

## 业务逻辑

### 统一转发机制
管理器订阅 `sensor` 主题，接收所有传感器数据，然后统一转发到对应的执行器。

### 消息格式

#### 输入格式（从传感器）
```json
{
    "type": "temperature_humidity",
    "params": {
        "temperature": 25.5,
        "humidity": 60.2,
    },
    "timestamp": 1234567890
}
```

#### 输出格式（到执行器）
```json
{
    "temperature": 25.5,
    "humidity": 60.2
}
```

### 传感器类型映射
- `temperature_humidity` → `actuator/oled`
- `pir_motion` → `actuator/oled`
- `button` → `actuator/buzzer`
- `potentiometer` → `actuator/audio`


## 配置

配置文件：`manager/config.ini`

```ini
[mqtt]
# MQTT代理配置
broker = localhost
port = 1883
topic_prefix = sensor

[manager]
# 管理器配置
log_level = INFO
```

## 消息流程

1. **传感器发布数据** → `sensor` 主题
2. **管理器订阅数据** → 统一转发
3. **管理器发布消息** → `actuator/{actuator_type}`
4. **执行器订阅消息** → 执行相应动作

## 主题映射

| 传感器类型 | 订阅主题 | 执行器 | 发布主题 |
|------------|----------|--------|----------|
| temperature_humidity | `sensor` | OLED | `actuator/oled` |
| pir_motion | `sensor` | OLED | `actuator/oled` |
| button | `sensor` | 蜂鸣器 | `actuator/buzzer` |
| potentiometer | `sensor` | 音频 | `actuator/audio` |

## 日志

管理器会输出详细的日志信息，包括：
- 接收到的传感器数据
- 业务逻辑处理过程
- 发送给执行器的消息
- 错误和警告信息

日志级别可以通过配置文件中的 `log_level` 参数调整。 