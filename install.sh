#!/bin/bash
# -*- coding: utf-8 -*-
# Raspberry Pier Mix 安装脚本
# 用于部署DHT22温湿度传感器MQTT发布服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查权限
check_root() {
    # 检查是否以sudo运行
    if [[ $EUID -eq 0 ]]; then
        # 如果是以sudo运行，检查SUDO_USER环境变量
        if [[ -n "$SUDO_USER" ]]; then
            log_info "检测到以sudo权限运行"
            return 0
        else
            log_error "请不要直接使用root用户运行此脚本，请使用sudo"
            exit 1
        fi
    else
        log_error "此脚本需要sudo权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检查系统要求
check_system() {
    log_info "检查系统要求..."
    
    # 检查是否为Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        log_warning "此脚本专为Raspberry Pi设计，其他系统可能无法正常工作"
    fi
    
}

# 安装Mosquitto MQTT代理
install_mosquitto() {
    log_info "检查Mosquitto MQTT代理..."
    
    if ! systemctl is-active --quiet mosquitto; then
        log_info "安装Mosquitto MQTT代理..."
        sudo apt update
        sudo apt install -y mosquitto mosquitto-clients
        
        # 启动并启用Mosquitto服务
        sudo systemctl enable mosquitto
        sudo systemctl start mosquitto
        
        log_success "Mosquitto安装并启动完成"
    else
        log_success "Mosquitto已在运行"
    fi
}

# 设置传感器虚拟环境
setup_sensor_venvs() {
    log_info "设置传感器虚拟环境..."
    
    # 检查sensors目录是否存在
    if [[ ! -d "sensors" ]]; then
        log_warning "sensors目录不存在，跳过虚拟环境设置"
        return 0
    fi
    
    # 检查common目录是否存在
    if [[ ! -d "common" ]]; then
        log_warning "common目录不存在，跳过虚拟环境设置"
        return 0
    fi
    
    # 遍历sensors目录下的子目录
    for sensor_dir in sensors/*/; do
        if [[ -d "$sensor_dir" ]]; then
            sensor_name=$(basename "$sensor_dir")
            log_info "处理传感器: $sensor_name"
            
            # 检查requirements.txt是否存在
            if [[ -f "${sensor_dir}requirements.txt" ]]; then
                log_info "在 $sensor_name 中创建虚拟环境..."
                
                # 进入传感器目录
                cd "$sensor_dir"
                
                # 创建虚拟环境
                if [[ ! -d "venv" ]]; then
                    python3 -m venv venv
                    log_success "虚拟环境创建完成: $sensor_name"
                else
                    log_info "虚拟环境已存在: $sensor_name"
                fi
                
                # 激活虚拟环境并安装依赖
                log_info "安装依赖: $sensor_name"
                source venv/bin/activate
                pip install --upgrade pip
                
                # 先安装common的依赖
                if [[ -f "../../common/requirements.txt" ]]; then
                    log_info "安装common模块依赖"
                    pip install -r ../../common/requirements.txt
                fi
                
                # 再安装传感器自身的依赖
                pip install -r requirements.txt
                deactivate
                
                log_success "依赖安装完成: $sensor_name"
                
                # 返回原目录
                cd - > /dev/null
            else
                log_warning "未找到requirements.txt文件: $sensor_name"
            fi
        fi
    done
    
    log_success "传感器虚拟环境设置完成"
}

# 设置执行器虚拟环境
setup_actuator_venvs() {
    log_info "设置执行器虚拟环境..."

    if [[ ! -d "actuators" ]]; then
        log_warning "actuators目录不存在，跳过虚拟环境设置"
        return 0
    fi

    if [[ ! -d "common" ]]; then
        log_warning "common目录不存在，跳过虚拟环境设置"
        return 0
    fi

    for act_dir in actuators/*/; do
        if [[ -d "$act_dir" ]]; then
            act_name=$(basename "$act_dir")
            log_info "处理执行器: $act_name"

            if [[ -f "${act_dir}requirements.txt" ]]; then
                log_info "在 $act_name 中创建虚拟环境..."
                cd "$act_dir"
                if [[ ! -d "venv" ]]; then
                    python3 -m venv venv
                    log_success "虚拟环境创建完成: $act_name"
                else
                    log_info "虚拟环境已存在: $act_name"
                fi
                log_info "安装依赖: $act_name"
                source venv/bin/activate
                pip install --upgrade pip
                if [[ -f "../../common/requirements.txt" ]]; then
                    log_info "安装common模块依赖"
                    pip install -r ../../common/requirements.txt
                fi
                pip install -r requirements.txt
                deactivate
                log_success "依赖安装完成: $act_name"
                cd - > /dev/null
            else
                log_warning "未找到requirements.txt文件: $act_name"
            fi
        fi
    done

    log_success "执行器虚拟环境设置完成"
}

# 生成systemd服务文件
generate_systemd_services() {
    log_info "生成systemd服务文件..."
    
    # 获取当前工作目录的绝对路径
    PROJECT_DIR=$(pwd)
    CURRENT_USER=$(whoami)
    
    log_info "项目目录: $PROJECT_DIR"
    log_info "当前用户: $CURRENT_USER"
    
    # 检查services目录是否存在，不存在则创建
    if [[ ! -d "services" ]]; then
        log_info "创建services目录"
        mkdir -p services
    fi
    
    # 遍历sensors目录，为每个传感器生成对应的服务文件
    for sensor_dir in sensors/*/; do
        if [[ -d "$sensor_dir" ]]; then
            sensor_name=$(basename "$sensor_dir")
            
            # 检查是否有主程序文件
            if [[ -f "${sensor_dir}${sensor_name}_pub.py" ]]; then
                service_file="services/${sensor_name}-publisher.service"
                
                log_info "生成服务文件: $service_file"
                
                # 生成服务文件内容（使用绝对路径）
                abs_sensor_dir="${PROJECT_DIR}/sensors/${sensor_name}"
                abs_python="${abs_sensor_dir}/venv/bin/python"
                abs_entry="${abs_sensor_dir}/${sensor_name}_pub.py"
                cat > "$service_file" << EOF
[Unit]
Description=${sensor_name} MQTT Publisher
Documentation=https://github.com/SwartzMss/RaspberryPierMix
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_USER}
WorkingDirectory=${abs_sensor_dir}
ExecStart=${abs_python} ${abs_entry}
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
EOF
                
                log_success "服务文件生成完成: $service_file"
            else
                log_warning "未找到主程序文件: ${sensor_name}_pub.py"
            fi
        fi
    done

    # 遍历actuators目录，为每个执行器生成对应的服务文件
    for act_dir in actuators/*/; do
        if [[ -d "$act_dir" ]]; then
            act_name=$(basename "$act_dir")

            if [[ -f "${act_dir}${act_name}_sub.py" ]]; then
                service_file="services/${act_name}-subscriber.service"

                log_info "生成服务文件: $service_file"

                abs_act_dir="${PROJECT_DIR}/actuators/${act_name}"
                abs_python="${abs_act_dir}/venv/bin/python"
                abs_entry="${abs_act_dir}/${act_name}_sub.py"
                cat > "$service_file" << EOF
[Unit]
Description=${act_name} MQTT Subscriber
Documentation=https://github.com/SwartzMss/RaspberryPierMix
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_USER}
WorkingDirectory=${abs_act_dir}
ExecStart=${abs_python} ${abs_entry}
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
EOF

                log_success "服务文件生成完成: $service_file"
            else
                log_warning "未找到主程序文件: ${act_name}_sub.py"
            fi
        fi
    done
    
    log_success "systemd服务文件生成完成"
}

# 安装并启动systemd服务
install_and_start_services() {
    log_info "安装并启动systemd服务..."
    
    # 检查services目录是否存在
    if [[ ! -d "services" ]]; then
        log_warning "services目录不存在，跳过服务安装"
        return 0
    fi
    
    # 匹配所有类型的服务文件
    local service_files=(services/*.service)
    if [[ ! -e "${service_files[0]}" ]]; then
        log_warning "未找到任何 .service 文件，跳过服务安装"
        return 0
    fi
    
    for service_file in "${service_files[@]}"; do
        service_name=$(basename "$service_file")
        log_info "安装服务: $service_name"
        sudo cp "$service_file" /etc/systemd/system/
    done
    
    log_info "重新加载systemd服务配置..."
    sudo systemctl daemon-reload
    
    for service_file in "${service_files[@]}"; do
        service_name=$(basename "$service_file")
        log_info "启用并启动服务: $service_name"
        sudo systemctl enable "$service_name"
        sudo systemctl restart "$service_name"
    done
    
    log_success "所有systemd服务已安装并启动"
}

# 主函数
main() {
    # 清理 pyc 缓存和 __pycache__ 目录
    log_info "清理 Python 缓存文件..."
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -r {} +
    log_success "Python 缓存清理完成"

    log_info "开始安装Raspberry Pier Mix 服务..."
    
    check_root
    check_system
    install_mosquitto
    setup_sensor_venvs
    setup_actuator_venvs
    generate_systemd_services
    install_and_start_services
    
    log_success "安装完成！"
}

# 运行主函数
main "$@" 