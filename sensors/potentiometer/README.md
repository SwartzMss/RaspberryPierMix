# 电位器传感器

## 概述
基于ADS1115和旋转电位器的通用传感器，通过MQTT发布电位器值变化事件。
⚠️ **必须先校准才能启动服务**，默认配置为无效值以强制用户校准。

参考项目: [pi5-potentiometer-tools](https://github.com/SwartzMss/pi5-potentiometer-tools)

## 🔧 硬件连接

### 电位器连接（重要！）
**标准接线**：
- 电位器**引脚1** → **GND** （接地端）
- 电位器**引脚2** → **ADS1115 A2** （滑动触点/信号输出）
- 电位器**引脚3** → **5V** （高电压端）

这样接线后：**顺时针 = 值增大，逆时针 = 值减小** ✅

### ADS1115连接
- ADS1115 VDD → Pi5 3.3V
- ADS1115 GND → Pi5 GND  
- ADS1115 SCL → Pi5 GPIO3 (SCL)
- ADS1115 SDA → Pi5 GPIO2 (SDA)

## ⚙️ 配置说明

### MQTT配置
```ini
[mqtt]
broker = localhost
port = 1883
topic_prefix = sensor
```

### 电位器配置
```ini
[potentiometer]
channel = 2              # A2通道
gain = 2/3              # 支持6.144V满量程
min_voltage = 0.0       # 会在校准后自动更新
max_voltage = 5.0       # 会在校准后自动更新
value_threshold = 2      # 变化2%才发布
```

## 🚀 使用方法

### 1. 安装依赖
```bash
cd sensors/potentiometer
pip install -r requirements.txt
```

### 2. 校准传感器（必须！）
```bash
python potentiometer_pub.py --calibrate
```
⚠️ **注意：没有校准无法启动服务！**

**校准过程**：
1. 程序提示时，将电位器转到最小位置（逆时针到底）
2. 程序提示时，将电位器转到最大位置（顺时针到底）
3. 程序提示时，将电位器转到中间位置验证
4. **校准结果自动保存到 `config.ini`**

### 🚀 快捷校准方式（推荐）
模块目录提供了统一命名的校准脚本：
```bash
# 在模块目录内执行
cd sensors/potentiometer
./calibrate.sh
```
🎆 **统一架构**：所有需要校准的传感器模块都使用相同的 `calibrate.sh` 命名规范

这个脚本会自动：
- 检测模块名称
- 停止对应服务（如果正在运行）
- 进行校准
- 重新启动服务（如果之前在运行）

### 3. 测试读数
```bash
python potentiometer_pub.py --test
```
转动电位器观察实时数值和电位器值条显示。

### 4. 正常运行
```bash
python potentiometer_pub.py
```

## 📡 MQTT消息格式

**主题**: `sensor/potentiometer`

**消息内容**:
```json
{
    "type": "potentiometer",
    "params": {
        "value": 75
    },
    "timestamp": 1703123456
}
```

## ✨ 核心特性

### 🎯 校准结果持久化
- ✅ 校准后自动保存到 `config.ini`
- ✅ 重启程序自动加载校准参数
- ✅ 无需重复校准

### 📊 智能发布
- ✅ 事件驱动（只在电位器值变化时发布）
- ✅ 可配置变化阈值（默认2%）
- ✅ 电压稳定化处理（减少抖动）

### 🔧 硬件优势
- ✅ 高精度16位ADC
- ✅ 支持5V电位器（无需分压电路）
- ✅ 2/3增益，满量程6.144V

## 🔄 校准流程详解

```bash
$ python potentiometer_pub.py --calibrate

🎛️  电位器校准程序
========================================

📍 请将电位器旋转到最小位置（逆时针到底），等待3秒...
  采样 10/10: 0.035V

📍 请将电位器旋转到最大位置（顺时针到底），等待3秒...
  采样 10/10: 4.982V

📍 请将电位器旋转到中间位置，等待3秒...
  采样 10/10: 2.510V

📊 校准结果:
------------------------------
  min_voltage: 0.035V
  max_voltage: 4.982V
  mid_voltage: 2.510V
  voltage_range: 4.947V

✅ 校准结果已保存到 config.ini
  min_voltage: 0.035V
  max_voltage: 4.982V
  电压范围: 4.947V
重启程序后校准结果会自动加载！

✅ 校准完成！校准结果已自动保存到配置文件。
重启程序时会自动使用新的校准参数。
```

## 🔄 校准前后对比

### 初始状态（无效默认值）
```ini
min_voltage = -1.0
max_voltage = -1.0
```
结果：⚠️ **服务拒绝启动**，强制用户先校准

### 校准后（自动更新）
```ini
min_voltage = 0.035
max_voltage = 4.982
```
结果：✅ **服务正常启动**，电位器值范围精确映射到电位器实际输出范围

## 🎵 系统集成示例

### 电位器控制脚本
```python
import os
import json
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    if msg.topic == "sensor/potentiometer":
        data = json.loads(msg.payload.decode())
        value = data['params']['value']
        # 控制任意系统参数
        print(f"电位器值变化: {value}%")

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.subscribe("sensor/potentiometer")
client.loop_forever()
```

## 🔍 故障排除

### 服务无法启动？
检查是否校准：
```bash
# 检查校准状态
cd sensors/potentiometer
python check_calibration.py

# 如果未校准，进行校准
python potentiometer_pub.py --calibrate
```

### install脚本提示未校准？
这是正常的！系统设计为强制校准：
```bash
# 使用统一校准脚本（推荐）
cd sensors/potentiometer
./calibrate.sh

# 或手动校准
python potentiometer_pub.py --calibrate
sudo systemctl start potentiometer-publisher
```

### 🏗️ 统一架构说明
该电位器模块采用了项目的统一校准架构：
- **统一文件名**：`calibrate.sh`（所有需要校准的模块）
- **统一检测**：`check_calibration.py`（install脚本自动检测）
- **统一流程**：未校准拒绝启动服务，并显示校准指南

这样设计的优势：
- ✅ 模块化：每个传感器自包含校准逻辑
- ✅ 可扩展：其他传感器（如温湿度）也可采用相同架构
- ✅ 统一管理：install脚本通用化处理所有校准需求

### 校准结果没有保存？
确保程序有写入配置文件的权限：
```bash
chmod 664 config.ini
```

### 电位器值变化不灵敏？
调整 `value_threshold` 值：
```ini
value_threshold = 1  # 更灵敏
```

### 硬件连接问题？
```bash
# 检查I2C设备
sudo i2cdetect -y 1

# 应该看到ADS1115在地址 0x48

# 测试模式检查读数
python potentiometer_pub.py --test
```

## 📝 技术细节

- **ADC**: ADS1115 16位分辨率
- **采样率**: 100ms间隔
- **稳定化**: 5次采样平均
- **增益**: 2/3x (±6.144V)
- **精度**: 0.1875mV

## 🏗️ 架构扩展

其他传感器模块可以参考该音量旋钮模块的校准架构：

### 添加校准支持的步骤：
1. **创建** `check_calibration.py` - 检测校准状态
2. **创建** `calibrate.sh` - 统一校准脚本
3. **修改** 传感器代码 - 拒绝无效校准值
4. **设置** 无效默认值 - 强制用户校准

install脚本会自动检测并处理所有带有 `check_calibration.py` 的传感器模块。