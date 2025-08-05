# RaspberryPierMix

## 概述

RaspberryPierMix是一个基于Raspberry Pi的传感器数据采集和执行器控制系统，采用MQTT消息传递机制实现模块化设计。

## 项目结构

```
RaspberryPierMix/
├── sensors/                # 传感器模块
│   ├── temperature_humidity/  # 温湿度传感器
│   ├── pir/                  # PIR运动检测传感器
│   ├── button/               # 按钮传感器
│   └── potentiometer/        # 电位器传感器
├── actuators/              # 执行器模块
│   ├── oled/                # OLED显示模块
│   ├── buzzer/              # 蜂鸣器模块
│   └── audio/               # 音频播放模块
├── manager/                # 业务管理器模块
│   ├── oled_manager/        # OLED业务管理器
│   │   ├── __init__.py
│   │   ├── oled_manager.py   # OLED管理器主程序
│   │   ├── config.ini        # OLED业务配置
│   │   └── README.md         # OLED业务说明
├── common/                 # 公共模块
│   ├── mqtt_base.py        # MQTT基础类
│   └── requirements.txt     # 公共依赖
├── services/               # 系统服务文件
├── manager_config.ini      # 全局配置文件
├── install.sh              # 安装脚本
├── uninstall.sh            # 卸载脚本
└── README.md               # 项目说明文档
```

## 架构设计

### 模块化设计

项目采用**按业务划分的模块化设计**：

1. **传感器模块** (`sensors/`) - 数据采集层
   - 温湿度传感器
   - PIR运动检测传感器
   - 按钮传感器
   - 电位器传感器

2. **执行器模块** (`actuators/`) - 控制执行层
   - OLED显示模块
   - 蜂鸣器模块
   - 音频播放模块

3. **业务管理器模块** (`manager/`) - 业务逻辑层
   - **OLED管理器** (`oled_manager/`) - 处理OLED显示相关业务
   - **其他管理器** - 根据业务需求扩展

### 消息流程

```
传感器 → MQTT → 业务管理器 → MQTT → 执行器
```

## 业务管理器

### OLED管理器 (`manager/oled_manager/`)

统一的业务管理器，处理相关传感器数据并根据业务逻辑进行相应的处理。

**支持的传感器：**

#### OLED相关传感器（复杂业务逻辑）
- `temperature_humidity` - 温湿度传感器
- `pir_motion` - PIR运动检测传感器


**主要功能：**
- OLED显示控制（温湿度显示、运动检测响应）
- 定时器管理（10分钟自动切换）
- 状态管理



## 扩展指南

### 添加新的业务管理器

1. 在 `manager/` 目录下创建新的管理器目录
2. 创建标准的模块结构：
   ```
   manager/new_manager/
   ├── __init__.py
   ├── new_manager.py
   ├── config.ini
   └── README.md
   ```
3. 继承 `MQTTSubscriber` 基类
4. 实现特定的业务逻辑
5. 更新 `manager/README.md` 文档

### 示例：LED管理器

```python
class LEDManager(MQTTSubscriber):
    def __init__(self, config):
        super().__init__(config)
        self.add_subscription('sensor')
        
    def handle_message(self, topic: str, payload: Dict[str, Any]):
        # 实现LED特定的业务逻辑
        pass
```

## 故障排除

### 常见问题

1. **MQTT连接失败**
   - 检查MQTT代理是否运行
   - 验证配置文件中的连接参数

2. **消息处理错误**
   - 检查传感器消息格式
   - 查看日志输出

3. **管理器启动失败**
   - 检查Python依赖
   - 验证文件路径

### 测试检查清单

在运行系统之前，请检查：

- [ ] MQTT代理正在运行
- [ ] 所有依赖已安装
- [ ] 配置文件正确
- [ ] 网络连接正常
- [ ] 传感器和执行器正常工作

## 版本历史

- **v3.0** - 创建manager模块，按业务划分管理器
- **v2.0** - 模块化重构，分离OLED和简单管理器
- **v1.0** - 统一管理器，所有逻辑集中在一个文件中

