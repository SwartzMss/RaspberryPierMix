## AutoScreenSwitch 管理器（AutoScreenSwitch_Manager）

### 概述

基于 PIR 人体传感事件，管理 Windows 客户端屏幕亮/息逻辑：

- 有人来（检测到运动）→ 立即发布点亮屏幕
- 连续超过 15 分钟无人 → 发布息屏

该管理器订阅统一的传感器主题 `sensor`，并向执行器主题 `actuator/autoScreenSwitch` 发布标准化的 `action/params` 事件，风格与 `oled_manager` 保持一致。

参考的 Windows 端组件（Rust）：`Auto_Screen_Switch`（需配合调整为新主题与 JSON 负载）参见项目说明文档：[Auto_Screen_Switch](https://github.com/SwartzMss/Auto_Screen_Switch)。

### 功能特性

- 订阅 PIR 运动检测传感器（`type=pir_motion`）
- 有人来立刻下发亮屏事件
- 无人 15 分钟自动下发息屏事件（超时可配置）
- 统一的 `action/params` 事件格式，便于跨组件对齐
- 详细日志与简单的容错处理

## 数据流与主题

### 数据流

```
sensor（pir_motion） → AutoScreenSwitch_Manager → actuator/autoScreenSwitch（on/off）
```

### 订阅主题（传感器）

- 主题：`sensor`
- 负载（示例，来自 PIR 发布者）：

```json
{
  "type": "pir_motion",
  "params": {
    "motion_detected": true
  },
  "timestamp": 1710000000
}
```

### 发布主题（执行器）

- 主题：`actuator/autoScreenSwitch`
- 负载（统一采用 `action/params`）：

1) 点亮屏幕（有人）

```json
{
  "action": "on",
  "params": { "source": "pir_motion" }
}
```

2) 息屏（超过设定无人时长）

```json
{
  "action": "off",
  "params": { "source": "idle_timeout" }
}
```

说明：若 Windows 端客户端当前仍按字符串 `on/off` 实现，需要将其升级为订阅 `actuator/autoScreenSwitch` 并解析上述 JSON 负载（或在其侧做向后兼容）。参考项目文档：[Auto_Screen_Switch](https://github.com/SwartzMss/Auto_Screen_Switch)。

## 行为与时序

- 亮屏触发：每次收到 `pir_motion` 且 `motion_detected=true` 时立即发布一次 `on`
  - 可配置轻微去抖与去重，避免短时间内重复下发（见配置）
- 息屏触发：从最近一次 `motion_detected=true` 开始计时；若超过 `idle_off_seconds`（默认 900 秒）未再检测到运动，则发布一次 `off`
- 任意新的 `motion_detected=true` 都会重置计时器

## 目录结构（规划）

```
manager/auto_screen_switch_manager/
├── auto_screen_switch_manager.py   # 主入口（订阅sensor，管理时序）
├── activity_task.py                # 活动/空闲计时与事件下发
├── config.ini                      # 配置文件
├── requirements.txt                # 依赖（若独立运行需要）
└── README.md                       # 使用说明（当前文件）
```

## 配置

### config.ini 示例

```ini
[mqtt]
broker = localhost
port = 1883
# 统一传感器主题（订阅）
topic_prefix = sensor

[auto_screen_switch]
# 无人息屏时长（秒）
idle_off_seconds = 900
# 执行器主题（发布）
publish_topic = actuator/autoScreenSwitch
 # 每次检测到有人是否都发布一次 on（默认 true；若想仅状态变化时发 on，可设为 false）
 emit_on_every_motion = true

[logging]
# 日志级别（默认 INFO；设为 DEBUG 可查看被抑制的重复状态日志）
level = INFO
```


## 测试方法

1) 模拟“有人来”事件（向 `sensor` 发布 pir_motion）：

```bash
mosquitto_pub -h localhost -t sensor -m '{"type":"pir_motion","params":{"motion_detected":true},"timestamp":1710000000}'
```

预期：立即向 `actuator/autoScreenSwitch` 发布 `{"action":"on", ...}`（若 `emit_on_every_motion=true`，每次 PIR 触发都会发一次）。

2) 无人超时测试：

- 触发一次“有人来”后，保持无输入超过 `idle_off_seconds`（默认 900s；任意新的 PIR 事件会重置计时器）
- 预期：发布 `{"action":"off", ...}` 到 `actuator/autoScreenSwitch`

## 故障排除

- 未收到 on/off：
  - 检查 `sensor` 是否有 `pir_motion` 且 `motion_detected=true`
  - 确认 MQTT 连接与主题名一致
  - 查看日志是否触发去抖/去重（`auto_screen_switch_manager` 为避免刷屏，默认仅在状态变化时发布；重复的 on/off 会被 DEBUG 日志提示已抑制）
- Windows 端无响应：
  - 确认其订阅 `actuator/autoScreenSwitch`
  - 确认其解析 `action/params` JSON 负载或做了兼容逻辑

## 参考

- Windows 屏幕控制组件（Rust）：[Auto_Screen_Switch](https://github.com/SwartzMss/Auto_Screen_Switch)


