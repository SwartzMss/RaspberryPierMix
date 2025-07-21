# 蜂鸣器执行器模块

## 概述

该模块通过 MQTT 订阅指令控制蜂鸣器鸣叫，目录结构参考 `sensors/temperature_humidity`。

## 文件结构

```
buzzer/
├── config.ini         # 配置文件
├── config.py          # 配置管理
├── buzzer.py          # 蜂鸣器驱动
├── controller.py      # MQTT 订阅者
├── buzzer_sub.py      # 主程序
├── requirements.txt   # 依赖列表
└── README.md
```

## 配置说明

### MQTT配置
```ini
[mqtt]
broker = localhost
port = 1883
topic_prefix = actuator
```

### 蜂鸣器配置
```ini
[buzzer]
pin = 18
beep_duration = 0.2
repeat = 2
```

## 使用方法

1. 修改 `config.ini` 中的参数。
2. 运行主程序：
   ```bash
   python buzzer_sub.py
   ```

## 接口设计

- **订阅主题**：`{topic_prefix}/buzzer`

  `topic_prefix` 来自 `config.ini` 的 MQTT 配置，默认值 `actuator`。

- **消息格式**：

  ```json
  {
    "action": true,      // true 触发蜂鸣，false 停止
    "params": {
      "times": 3,        // 蜂鸣次数，可选
      "interval": 0.2    // 间隔时长（秒），可选
    }
  }
  ```

  当 `action` 为 `true` 时，按照参数执行蜂鸣；`false` 则立即停止。

- **示例**：

  ```bash
  mosquitto_pub -t actuator/buzzer -m '{"action": true, "params": {"times": 5, "interval": 0.1}}'
  ```
