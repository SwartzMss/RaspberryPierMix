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
- **语言与库**：Python 3.7+；`paho-mqtt`；各类传感器驱动（如 `Adafruit_DHT`）。
- **系统服务**：systemd，用于管理节点进程。

---

## 🔧 快速部署指南

1. **基础环境**：
   ```bash
   sudo apt update && sudo apt install -y python3-pip mosquitto
   pip3 install paho-mqtt Adafruit_DHT
   ```
2. **项目结构**：
   ```
   pi5-mqtt-ros/
   ├─ services/             # systemd 单元文件
   ├─ sensors/              # 传感器发布脚本
   ├─ actuators/            # 执行器订阅脚本
   └─ common/               # 配置与公用库
   ```
3. **注册服务**（示例）：
   ```ini
   # /etc/systemd/system/temp-pub.service
   [Unit]
   Description=Temperature Publisher
   After=network.target mosquitto.service

   [Service]
   ExecStart=/usr/bin/python3 /opt/pi5-mqtt-ros/sensors/temp_pub.py
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable temp-pub
   sudo systemctl start temp-pub
   ```

---

## 📡 主题层与消息格式规范

| 领域    | 主题前缀              | 格式示例                                 |
| ----- | ----------------- | ------------------------------------ |
| 传感器数据 | `sensor/{type}`   | `{"value": 23.5, "ts": 162}`         |
| 执行器命令 | `actuator/{name}` | `{"cmd": "ON"/"OFF", "id": "node1"}` |
| 状态心跳  | `health/{node}`   | `{"status": "OK", "load": 0.1}`      |

- **时间戳**：所有消息建议携带单位秒的 UTC 时间戳。
- **节点 ID**：区分不同实例，便于日志和故障排查。

---

## 🚀 示例脚本概览

### sensors/temp\_pub.py

```python
# 负责读取 DHT22 温湿度并发布到 MQTT
# 引入配置与公用模块，实现可插拔
```

### actuators/buzzer\_sub.py

```python
# 订阅 actuator/buzzer 主题，控制 GPIO 蜂鸣器
```

*完整示例请见 **`sensors/`** 与 **`actuators/`** 目录*。

---

## 🔄 日志与监控

- **日志输出**：各节点统一输出 JSON 格式日志，便于集中采集（ELK/Grafana）。
- **健康检查**：定期发布心跳，运维脚本可自动重启异常节点。

---

## 💡 扩展与进阶

- **动态配置**：接入配置中心，实现主题和参数在线调优。
- **安全机制**：启用 TLS 和 Token 认证，确保消息安全。
- **分布式协调**：结合轻量级服务发现（如 Consul），实现多机热插拔。

---

> 以系统化思路将 MQTT 节点打包为服务，通过统一主题、健康监控与日志管理，打造可运维、易扩展的轻量级 ROS 样架构。欢迎交流与贡献！

