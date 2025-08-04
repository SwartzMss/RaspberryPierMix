# 基于 Raspberry Pi 5 的 MQTT 发布/订阅 简易 ROS 框架

> 在树莓派 Pi 5 上构建轻量级的 MQTT 发布/订阅架构，通过模块化、系统服务化、解耦设计，实现传感器采集与执行器控制。

---

## ✨ 核心设计理念

1. **系统服务化**：将各个节点（发布端、订阅端、逻辑处理）打包为 systemd 服务，开机自启、易于监控与管理。
2. **模块化解耦**：硬件驱动、MQTT 通信、业务逻辑严格分离，通过统一的主题层发布与订阅，支持多节点并行扩展。
3. **轻量协议**：采用 MQTT 替代重型 ROS，用最小依赖实现异步分布式通信。
4. **可扩展接口**：预留插件接口，可插拔不同传感器、执行器或算法逻辑。
5. **统一传感器架构**：所有传感器使用标准化的数据格式，通过独立的传感器管理服务实现可配置的业务逻辑绑定。

---

## 📦 环境与依赖概览

- **硬件**：Raspberry Pi 5；DHTxx 温湿度传感器；PIR红外传感器（HC-SR501）；蜂鸣器等（详细接线请参考子项目文档）。
- **Broker**：Mosquitto 或任何兼容 MQTT 的服务端。
- **语言与库**：Python 3.7+；`paho-mqtt`；各类传感器驱动（如 `adafruit-circuitpython-dht`、`gpiozero`）。
- **系统服务**：systemd，用于管理节点进程。

---

## 🔧 快速部署与服务管理

### 传统方式（系统服务）

1. **运行安装脚本**（自动创建虚拟环境、生成并安装 systemd 服务）：
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

2. **卸载服务**（停止、禁用并删除所有 systemd 服务）：
   ```bash
   chmod +x uninstall.sh
   sudo ./uninstall.sh
   ```

2. **调试与管理 systemd 服务**

   - **查看服务状态**
     ```bash
     sudo systemctl status temperature_humidity-publisher.service
     ```
   - **启动服务**
     ```bash
     sudo systemctl start temperature_humidity-publisher.service
     ```
   - **重启服务**
     ```bash
     sudo systemctl restart temperature_humidity-publisher.service
     ```
   - **停止服务**
     ```bash
     sudo systemctl stop temperature_humidity-publisher.service
     ```
   - **实时查看服务日志**
     ```bash
     sudo journalctl -u temperature_humidity-publisher.service -f
     ```
   - **修改服务文件后需重载配置**
     ```bash
     sudo systemctl daemon-reload
     sudo systemctl restart temperature_humidity-publisher.service
     ```

   - **完全卸载服务**
     ```bash
     sudo ./uninstall.sh
     ```

   - **常见问题排查**
     - 服务无法启动，status=203/EXEC：检查服务文件中的 ExecStart 和 WorkingDirectory 是否为绝对路径，且文件存在。
     - 检查虚拟环境 venv/bin/python 是否存在。
     - 检查服务文件属主和权限。
     - 服务启动后无数据发布：查看日志，确认传感器和MQTT连接是否正常。手动激活虚拟环境并运行主程序，排查依赖问题。

3. **手动调试与测试**

   若仅需在命令行下验证发布和订阅，可按以下步骤操作：
   
   ```bash
   mosquitto_sub -t sensor/temperature_humidity -v
   mosquitto_sub -t sensor/pir_motion -v
   ```
   
   ```bash
   mosquitto_pub -t actuator/test -m '{"cmd": "ON", "id": "node1"}'
   ```

---

## 📡 主题层与消息格式规范


所有传感器现在都使用标准化的JSON格式，发布到 `sensor/sensor` topic：

```json
{
    "type": "sensor_type",
    "params": {
        // 传感器特定参数
    },
    "timestamp": 1234567890
}
```

### 各传感器数据格式示例

#### Button 传感器
```json
{
    "type": "button",
    "params": {
        "action": "pressed",
    },
    "timestamp": 1754104570
}
```

#### Volume Knob 传感器
```json
{
    "type": "volume_knob",
    "params": {
        "volume": 75,
    },
    "timestamp": 1754104570
}
```

#### PIR Motion 传感器
```json
{
    "type": "pir_motion",
    "params": {
        "motion": "detected",
    },
    "timestamp": 1754104570
}
```

#### Temperature Humidity 传感器
```json
{
    "type": "temperature_humidity",
    "params": {
        "temperature": 25.5,
        "humidity": 60.2,
    },
    "timestamp": 1754104570
}
```

### 控制消息格式

传感器管理服务发布到对应的控制topic，格式如下：

```json
{
    "action": "action_name",
    "params": {
        // 原始传感器参数
    },
    "source": "sensor_type",
    "timestamp": 1234567890
}
```

### 传统格式（兼容）

| 领域    | 主题前缀              | 格式示例                                 |
| ----- | ----------------- | ------------------------------------ |
| 传感器数据 | `sensor/{type}`   | `{"temperature": 23.5, "humidity": 40.2, "timestamp": 162}` / `{"motion_detected": true, "timestamp": 162}` |
| 通用控制指令 | `sensor/common`   | `{"action": "button_pressed", "params": {"timestamp": 162}}` |
| 执行器命令 | `actuator/{name}` | `{"action": true, "params": {"times": 3}}` |

- **时间戳**：所有消息建议携带单位秒的 UTC 时间戳。

---

## 📋 已实现的传感器与执行器

### 传感器（Publishers）
- `temperature_humidity` - DHT22 温湿度
- `button` - GPIO 按键
- `pir` - PIR 红外运动
- `volume_knob` - 音量旋钮（ADS1115）

### 执行器（Subscribers）
- `buzzer` - 蜂鸣器
- `oled` - OLED 显示屏



#### 优势
- ✅ 传感器只发布原始数据，职责单一
- ✅ 统一的数据格式，便于处理
- ✅ 可配置的业务逻辑绑定
- ✅ 独立的传感器管理服务
- ✅ 易于扩展和维护


```
传感器 → 发布原始数据 → 管理服务 → 业务逻辑绑定 → 执行器
```

### 数据流向
1. **传感器层**: 发布到 `sensor/sensor` topic
2. **管理服务层**: 订阅并处理传感器数据
3. **业务逻辑层**: 根据配置执行绑定动作
4. **执行器层**: 接收控制指令并执行

---

## 🚀 示例脚本概览

### sensors/temperature_humidity/temperature_humidity_pub.py

```python
# 负责读取 DHT22 温湿度并发布到 MQTT
# 引入配置与公用模块，实现可插拔
```
- **消息格式**：

  ```json
  {
    "temperature": 25.1,
    "humidity": 40.2,
    "timestamp": 1710000000
  }
  ```


### sensors/button/button_pub.py

```python
# 负责检测物理按键事件并发布到 MQTT
# 仅在按键被按下时发布事件型消息，结构与温湿度传感器一致
```

- **消息格式**：

  ```json
  {
    "action": "button_pressed",
    "params": {
      "timestamp": 1710000000
    }
  }
  ```

### sensors/pir/pir_pub.py

```python
# 基于 gpiozero.MotionSensor 的 PIR 红外传感器
# 检测运动状态变化并发布到 MQTT，支持运动检测和无运动状态
# 参考用户示例代码实现，简洁高效
```

- **消息格式**：

  ```json
  {
    "motion_detected": true,
    "timestamp": 1710000000
  }
  ```


`motion_detected` 为 `true` 时表示检测到运动，为 `false` 时表示无运动状态。

### sensors/volume_knob/volume_knob_pub.py

```python
# 基于 ADS1115 的旋转电位器传感器，发布音量百分比
# 需要先执行 calibrate.sh 完成校准
```

- **消息格式**：

  ```json
  {
    "action": "set_volume",
    "params": {
      "volume": 75
    }
  }
  ```

### actuators/buzzer/buzzer_sub.py

```python
# 订阅 actuator/buzzer 主题，根据指令控制蜂鸣器鸣叫
```

- **消息格式**：

  ```json
  {
    "action": true,
    "params": {"times": 3, "interval": 0.2}
  }
  ```

  `action` 设为 `true` 时按参数鸣叫，设为 `false` 则停止当前蜂鸣。


---

## 🏗️ 统一校准架构

项目提供了一个统一的传感器校准机制：任何需要校准的模块都包含名为
`calibrate.sh` 的脚本，`install.sh` 会在安装过程中检测校准状态并给出提示。

校准流程和示例可在音量旋钮模块的文档中查看，路径为
[`sensors/volume_knob/README.md`](sensors/volume_knob/README.md)。该文档详细
介绍了如何运行校准脚本以及校准结果如何被服务加载。其他传感器可以按照同
样的流程扩展校准支持。

### 校准结果持久化
- ✅ 校准后自动保存到 `config.ini`
- ✅ 重启程序自动加载校准参数
- ✅ 无需重复校准

---

## 🗑️ 卸载功能

项目提供了完整的卸载脚本 `uninstall.sh`，可以安全地清理所有已安装的服务：

### 卸载功能包括：
- 🛑 **停止所有服务** - 停止所有正在运行的systemd服务
- 🚫 **禁用服务** - 禁用所有服务（开机不自启）
- 🗑️ **删除服务文件** - 从系统删除所有服务文件
- 🧹 **清理缓存** - 自动清理Python缓存文件
- 📁 **可选清理** - 可选择删除services目录

### 使用方法：
```bash
sudo ./uninstall.sh
```

### 安全特性：
- ✅ **权限检查** - 要求sudo权限运行
- ✅ **确认提示** - 显示详细操作说明并要求用户确认
- ✅ **详细日志** - 彩色输出，清晰显示每个步骤
- ✅ **错误处理** - 优雅处理各种异常情况

### 卸载后重新安装：
卸载完成后，如需重新安装，只需再次运行：
```bash
sudo ./install.sh
```

---
