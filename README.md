# 基于 Raspberry Pi 5 的 MQTT 发布/订阅 简易 ROS 框架

> 在树莓派 Pi 5 上构建轻量级的 MQTT 发布/订阅架构，通过模块化、系统服务化、解耦设计，实现传感器采集与执行器控制。

---

## ✨ 核心设计理念

1. **系统服务化**：将各个节点（发布端、订阅端、逻辑处理）打包为 systemd 服务，开机自启、易于监控与管理。
2. **模块化解耦**：硬件驱动、MQTT 通信、业务逻辑严格分离，通过统一的主题层发布与订阅，支持多节点并行扩展。
3. **轻量协议**：采用 MQTT 替代重型 ROS，用最小依赖实现异步分布式通信。
4. **可扩展接口**：预留插件接口，可插拔不同传感器、执行器或算法逻辑。

---

## 📦 环境与依赖概览

- **硬件**：Raspberry Pi 5；DHTxx 温湿度传感器；蜂鸣器等（详细接线请参考子项目文档）。
- **Broker**：Mosquitto 或任何兼容 MQTT 的服务端。
- **语言与库**：Python 3.7+；`paho-mqtt`；各类传感器驱动（如 `adafruit-circuitpython-dht`）。
- **系统服务**：systemd，用于管理节点进程。

---

## 🔧 快速部署与服务管理

1. **运行安装脚本**（自动创建虚拟环境、生成并安装 systemd 服务）：
   ```bash
   chmod +x install.sh
   sudo ./install.sh
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

   - **常见问题排查**
     - 服务无法启动，status=203/EXEC：检查服务文件中的 ExecStart 和 WorkingDirectory 是否为绝对路径，且文件存在。
     - 检查虚拟环境 venv/bin/python 是否存在。
     - 检查服务文件属主和权限。
     - 服务启动后无数据发布：查看日志，确认传感器和MQTT连接是否正常。手动激活虚拟环境并运行主程序，排查依赖问题。

3. **手动调试与测试**

   若仅需在命令行下验证发布和订阅，可按以下步骤操作：
   
   ```bash
   mosquitto_sub -t sensor/temperature_humidity -v
   ```
   
   ```bash
   mosquitto_pub -t actuator/test -m '{"cmd": "ON", "id": "node1"}'
   ```

---

## 📡 主题层与消息格式规范

| 领域    | 主题前缀              | 格式示例                                 |
| ----- | ----------------- | ------------------------------------ |
| 传感器数据 | `sensor/{type}`   | `{"value": 23.5, "ts": 162}`         |
| 执行器命令 | `actuator/{name}` | `{"action": true, "params": {"times": 3}}` |


- **时间戳**：所有消息建议携带单位秒的 UTC 时间戳。

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
    "event": "pressed",
    "timestamp": 1710000000
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


