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

# 主函数
main() {
    log_info "开始安装Raspberry Pier Mix 服务..."
    
    check_root
    check_system
    install_mosquitto
    
    log_success "安装完成！"
}

# 运行主函数
main "$@" 