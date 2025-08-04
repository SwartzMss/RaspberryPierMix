# OLED管理器

## 概述

OLED管理器专门处理与OLED显示相关的传感器数据，实现智能显示控制逻辑。

## 功能特性

### 🎯 **核心功能**

1. **温湿度显示控制** - 处理温湿度传感器数据，更新OLED显示
2. **PIR运动检测响应** - 处理PIR传感器数据，实现智能显示切换
3. **定时器管理** - 10分钟自动切换回正常显示模式
4. **状态管理** - 维护OLED显示状态

### 📊 **支持的传感器**

- **`temperature_humidity`** - 温湿度传感器
  - 显示温湿度数据
  - 10分钟自动切换回正常模式
  - 状态管理和定时器控制

- **`pir_motion`** - PIR运动检测传感器
  - 检测到运动时显示提示信息
  - 触发OLED显示模式切换

## 架构设计

### 🔄 **数据流向**

```
温湿度传感器 → OLED管理器 → OLED显示
PIR运动传感器 → OLED管理器 → OLED显示
```

### 📋 **处理逻辑**

1. **接收传感器数据** - 订阅传感器主题
2. **过滤OLED相关传感器** - 只处理温湿度和PIR传感器
3. **业务逻辑处理** - 根据传感器类型进行特殊处理
4. **发送显示命令** - 发送命令到OLED执行器

### 🎯 **代码结构**

```python
class OLEDManager(MQTTSubscriber):
    def __init__(self, config):
        # OLED状态管理
        self.oled_state = {...}
    
    def handle_message(self, topic, payload):
        # 只处理OLED相关的传感器
        if sensor_type in ['temperature_humidity', 'pir_motion']:
            # 进行特殊处理
```

## 使用方法

### 🚀 **启动管理器**

```bash
# 进入OLED管理器目录
cd manager/oled_manager

# 运行OLED管理器
python oled_manager.py

# 后台运行
nohup python oled_manager.py > oled.log 2>&1 &
```

### ⚙️ **配置说明**

编辑 `config.ini` 文件：

```ini
[mqtt]
broker = localhost
port = 1883
topic_prefix = sensor

[oled]
temp_display_duration = 600  # 温湿度显示持续时间（秒）
```

## 业务逻辑详解

### 🌡️ **温湿度处理**

1. **接收数据** - 获取温度和湿度值
2. **更新状态** - 更新OLED状态中的最新数据
3. **启动定时器** - 启动10分钟显示定时器
4. **发送命令** - 发送显示命令到OLED执行器

### 🏃 **运动检测处理**

1. **检测运动** - 接收PIR传感器数据
2. **显示提示** - 发送运动检测提示到OLED
3. **状态切换** - 切换到运动检测显示模式

## 消息格式

### 📤 **发送到OLED的消息**

```json
{
    "mode": "temperature",
    "temperature": 25.5,
    "humidity": 60.2
}
```

```json
{
    "mode": "motion_detected",
    "message": "Motion Detected!"
}
```

```json
{
    "mode": "normal",
    "message": "System Ready"
}
```

## 状态管理

### ⏰ **定时器管理**

- **温湿度显示定时器** - 10分钟后自动切换回正常模式
- **定时器重置** - 每次收到新的温湿度数据时重置定时器
- **定时器取消** - 切换模式时取消当前定时器

### 📊 **状态变量**

```python
oled_state = {
    'show_temp_mode': False,      # 是否显示温湿度模式
    'latest_temperature': None,   # 最新温度值
    'latest_humidity': None,      # 最新湿度值
    'temp_timer': None,           # 温湿度显示定时器
    'temp_display_duration': 600  # 显示持续时间（秒）
}
```

## 故障排除

### 🔍 **常见问题**

1. **MQTT连接失败**
   - 检查MQTT代理是否运行
   - 验证配置文件中的连接参数

2. **消息处理错误**
   - 检查传感器消息格式
   - 查看日志输出

3. **OLED显示异常**
   - 检查OLED执行器是否正常运行
   - 验证消息格式是否正确

### 📝 **日志级别**

- **INFO** - 正常业务操作日志
- **DEBUG** - 详细调试信息
- **WARNING** - 警告信息
- **ERROR** - 错误信息

## 扩展指南

### ➕ **添加新的OLED传感器**

1. 在 `handle_message` 方法中添加新的传感器类型
2. 实现对应的处理方法
3. 更新文档说明

## 版本历史

- **v1.0** - 专门处理OLED相关传感器 