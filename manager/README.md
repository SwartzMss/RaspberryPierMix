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

## 运行方式

### 1. 直接运行

```bash
# 在manager目录下运行
python manager_sub.py
```

### 2. 作为系统服务运行

Manager模块可以作为systemd服务运行，实现开机自启动和自动重启功能。

#### 安装步骤

**生成服务文件：**
```bash
# 在项目根目录执行
./install.sh
```

这将在 `services/` 目录下生成所有服务文件，包括 `manager-subscriber.service`。

**安装服务：**
```bash
# 复制服务文件到systemd目录
sudo cp services/manager-subscriber.service /etc/systemd/system/

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务（开机自启动）
sudo systemctl enable manager-subscriber.service

# 启动服务
sudo systemctl start manager-subscriber.service
```

**验证服务状态：**
```bash
# 检查服务状态
sudo systemctl status manager-subscriber.service

# 查看服务日志
sudo journalctl -u manager-subscriber.service -f

# 查看最近的日志
sudo journalctl -u manager-subscriber.service -n 50
```

#### 服务管理命令

```bash
# 启动服务
sudo systemctl start manager-subscriber.service

# 停止服务
sudo systemctl stop manager-subscriber.service

# 重启服务
sudo systemctl restart manager-subscriber.service

# 禁用开机自启动
sudo systemctl disable manager-subscriber.service

# 查看服务状态
sudo systemctl status manager-subscriber.service
```

#### 服务配置说明

服务文件内容：
```ini
[Unit]
Description=Sensor Data Manager MQTT Subscriber
Documentation=https://github.com/SwartzMss/RaspberryPierMix
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_USER}
WorkingDirectory=${PROJECT_DIR}/manager
ExecStart=${PROJECT_DIR}/manager/venv/bin/python ${PROJECT_DIR}/manager/manager_sub.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=${PROJECT_DIR}

[Install]
WantedBy=multi-user.target
```

**关键配置说明：**
- **After=network.target mosquitto.service**: 确保在网络和MQTT代理启动后再启动
- **Wants=mosquitto.service**: 依赖MQTT代理服务
- **Restart=on-failure**: 服务失败时自动重启
- **RestartSec=10**: 重启间隔10秒
- **WorkingDirectory**: 工作目录设置为manager目录
- **ExecStart**: 使用虚拟环境中的Python执行主程序

#### 故障排除

**服务启动失败：**
```bash
# 检查日志
sudo journalctl -u manager-subscriber.service -n 50
```

常见问题：
- Python虚拟环境路径不正确
- 依赖包未安装
- MQTT代理未启动
- 配置文件路径错误

**权限问题：**
```bash
# 检查当前用户
whoami

# 检查用户组
groups
```

**路径问题：**
```bash
# 检查Python路径
ls -la manager/venv/bin/python

# 检查主程序文件
ls -la manager/manager_sub.py
```

#### 与其他服务的关系

Manager服务应该在其他传感器和执行器服务之前启动，因为它负责数据路由：

```bash
# 启动顺序建议
sudo systemctl start mosquitto.service
sudo systemctl start manager-subscriber.service
sudo systemctl start temperature_humidity-publisher.service
sudo systemctl start pir_motion-publisher.service
sudo systemctl start oled-subscriber.service
```

#### 监控和维护

**日志监控：**
```bash
# 实时监控日志
sudo journalctl -u manager-subscriber.service -f

# 查看错误日志
sudo journalctl -u manager-subscriber.service -p err
```

**性能监控：**
```bash
# 查看服务资源使用情况
sudo systemctl status manager-subscriber.service

# 查看系统资源使用
htop
```

#### 卸载服务

```bash
# 停止服务
sudo systemctl stop manager-subscriber.service

# 禁用服务
sudo systemctl disable manager-subscriber.service

# 删除服务文件
sudo rm /etc/systemd/system/manager-subscriber.service

# 重新加载systemd
sudo systemctl daemon-reload
```

## 日志

管理器会输出详细的日志信息，包括：
- 接收到的传感器数据
- 业务逻辑处理过程
- 发送给执行器的消息
- 错误和警告信息

日志级别可以通过配置文件中的 `log_level` 参数调整。 