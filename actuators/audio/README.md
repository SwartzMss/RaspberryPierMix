# 音频执行器 (Audio Actuator)

基于 [pi5-usbaudio-tools](https://github.com/SwartzMss/pi5-usbaudio-tools) 项目，为 Raspberry Pi 5 提供 USB 音频控制功能。

## 功能特性

- **文字播报**: 接收文字消息并转换为语音播放
- **音量控制**: 设置音量
- **MQTT 集成**: 通过 MQTT 消息远程控制

## 快速开始

### 1. 安装依赖

项目根目录的 `install.sh` 脚本会自动安装所有依赖：

```bash
sudo ./install.sh
```

### 2. 配置声卡

```bash
cd actuators/audio
nano config.ini
```



### 3. 启动执行器

```bash
# 直接启动
python3 audio_sub.py

# 作为系统服务
sudo systemctl start audio-subscriber
```

## 配置

参考 [pi5-usbaudio-tools](https://github.com/SwartzMss/pi5-usbaudio-tools) 项目配置 USB 声卡参数，编辑 `config.ini` 文件。

## MQTT 消息格式

**订阅主题**: `actuator/audio`

### 音量控制

```json
// 设置音量
{
  "action": "set_volume",
  "params": {
    "volume": 80
  }
}
```

### 文字播报

```json
// 播报文字
{
  "action": "speak",
  "params": {
    "text": "你好，这是一个测试消息"
  }
}

// 停止播报
{
  "action": "stop"
}
```

## 使用示例

### 基本命令

```bash
# 设置音量80%
mosquitto_pub -h localhost -t "actuator/audio" -m '{"action":"set_volume","params":{"volume":80}}'

# 播报文字
mosquitto_pub -h localhost -t "actuator/audio" -m '{"action":"speak","params":{"text":"你好，这是一个测试消息"}}'

# 停止播报
mosquitto_pub -h localhost -t "actuator/audio" -m '{"action":"stop"}'
```

### Python 客户端示例

```python
import json
import paho.mqtt.client as mqtt
import time

class AudioClient:
    def __init__(self, broker='localhost', port=1883):
        self.client = mqtt.Client()
        self.client.connect(broker, port, 60)
        self.client.loop_start()
    
    def send_command(self, action, params=None):
        message = {"action": action}
        if params:
            message["params"] = params
        
        payload = json.dumps(message)
        self.client.publish("actuator/audio", payload)
    
    def set_volume(self, volume):
        self.send_command("set_volume", {"volume": volume})
    
    def speak_text(self, text):
        self.send_command("speak", {"text": text})
    
    def stop_audio(self):
        self.send_command("stop")
    
    def close(self):
        self.client.loop_stop()
        self.client.disconnect()

# 使用示例
client = AudioClient()
client.set_volume(80)
client.speak_text("你好，这是一个测试消息")
time.sleep(3)
client.stop_audio()
client.close()
```

### 与传感器集成

```python
# 按钮按下时播报提示
if data.get('pressed', False):
    self.speak_text("按钮已按下")

# 人体传感器检测到运动时播报警报
if data.get('motion_detected', False):
    self.speak_text("检测到人体运动")

# 温度过高时播报警告
if temperature > 30:
    self.speak_text("温度过高，请注意")

# 音量旋钮变化时调整音频音量
volume = data.get('volume')
if volume is not None:
    self.set_volume(volume)
```

## 测试

### 手动测试

```bash
# 设置音量
mosquitto_pub -h localhost -t "actuator/audio" -m '{"action":"set_volume","params":{"volume":80}}'

# 播报文字
mosquitto_pub -h localhost -t "actuator/audio" -m '{"action":"speak","params":{"text":"测试播报功能"}}'
```

## 语音合成

使用系统内置的文本转语音功能，支持中文和英文播报。

## 故障排除

### 常见问题

1. **无声音输出**
   - 检查 USB 声卡是否正确连接
   - 确认声卡索引配置正确

2. **无法播报文字**
   - 确认系统已安装文本转语音工具
   - 检查文字内容是否包含特殊字符
   - 确认语音合成服务正常运行

3. **音量控制无效**
   - 检查控制项名称是否正确
   - 使用 `amixer -c {card_index} scontrols` 验证可用控制项

### 调试命令

参考 [pi5-usbaudio-tools](https://github.com/SwartzMss/pi5-usbaudio-tools) 项目的调试方法。

## 许可证

本项目基于 MIT 许可证开源。 