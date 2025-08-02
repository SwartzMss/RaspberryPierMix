#!/bin/bash
# -*- coding: utf-8 -*-
# Raspberry Pier Mix 卸载脚本
# 用于卸载所有已安装的systemd服务

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

# 停止并卸载systemd服务
uninstall_services() {
    log_info "开始卸载systemd服务..."
    
    # 检查services目录是否存在
    if [[ ! -d "services" ]]; then
        log_warning "services目录不存在，跳过服务卸载"
        return 0
    fi
    
    # 匹配所有类型的服务文件
    local service_files=(services/*.service)
    if [[ ! -e "${service_files[0]}" ]]; then
        log_warning "未找到任何 .service 文件，跳过服务卸载"
        return 0
    fi
    
    local stopped_services=()
    local disabled_services=()
    local removed_services=()
    
    # 第一步：停止所有服务
    log_info "停止所有服务..."
    for service_file in "${service_files[@]}"; do
        service_name=$(basename "$service_file")
        
        # 检查服务是否正在运行
        if systemctl is-active --quiet "$service_name" 2>/dev/null; then
            log_info "停止服务: $service_name"
            sudo systemctl stop "$service_name"
            stopped_services+=("$service_name")
        else
            log_info "服务未运行: $service_name"
        fi
    done
    
    # 第二步：禁用所有服务
    log_info "禁用所有服务..."
    for service_file in "${service_files[@]}"; do
        service_name=$(basename "$service_file")
        
        # 检查服务是否已启用
        if systemctl is-enabled --quiet "$service_name" 2>/dev/null; then
            log_info "禁用服务: $service_name"
            sudo systemctl disable "$service_name"
            disabled_services+=("$service_name")
        else
            log_info "服务未启用: $service_name"
        fi
    done
    
    # 第三步：删除服务文件
    log_info "删除服务文件..."
    for service_file in "${service_files[@]}"; do
        service_name=$(basename "$service_file")
        service_path="/etc/systemd/system/$service_name"
        
        if [[ -f "$service_path" ]]; then
            log_info "删除服务文件: $service_name"
            sudo rm -f "$service_path"
            removed_services+=("$service_name")
        else
            log_warning "服务文件不存在: $service_name"
        fi
    done
    
    # 重新加载systemd配置
    log_info "重新加载systemd服务配置..."
    sudo systemctl daemon-reload
    
    # 显示卸载结果
    echo ""
    log_success "服务卸载完成！"
    echo ""
    
    if [[ ${#stopped_services[@]} -gt 0 ]]; then
        echo "🛑 已停止的服务："
        for service in "${stopped_services[@]}"; do
            echo "   - $service"
        done
        echo ""
    fi
    
    if [[ ${#disabled_services[@]} -gt 0 ]]; then
        echo "🚫 已禁用的服务："
        for service in "${disabled_services[@]}"; do
            echo "   - $service"
        done
        echo ""
    fi
    
    if [[ ${#removed_services[@]} -gt 0 ]]; then
        echo "🗑️  已删除的服务文件："
        for service in "${removed_services[@]}"; do
            echo "   - $service"
        done
        echo ""
    fi
}



# 清理services目录（可选）
cleanup_services_dir() {
    log_info "是否要删除services目录？(y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "删除services目录..."
        if [[ -d "services" ]]; then
            rm -rf services
            log_success "services目录已删除"
        else
            log_warning "services目录不存在"
        fi
    else
        log_info "保留services目录"
    fi
}

# 清理Python缓存
cleanup_python_cache() {
    log_info "清理Python缓存文件..."
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    log_success "Python缓存清理完成"
}

# 显示卸载确认
show_uninstall_confirmation() {
    echo ""
    echo "🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨"
    echo "⚠️  即将卸载Raspberry Pier Mix服务"
    echo "🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨"
    echo ""
    echo "此操作将："
    echo "1️⃣  停止所有正在运行的服务"
    echo "2️⃣  禁用所有服务（开机不自启）"
    echo "3️⃣  删除systemd服务文件"
    echo "4️⃣  清理Python缓存文件"
    echo ""
    echo "可选操作："
    echo "5️⃣  删除services目录（可选）"
    echo ""
    echo "⚠️  注意：此操作不可逆！"
    echo ""
    
    log_info "确认要卸载吗？(y/N)"
    read -r response
    
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "取消卸载操作"
        exit 0
    fi
}

# 主函数
main() {
    log_info "开始卸载Raspberry Pier Mix 服务..."
    
    show_uninstall_confirmation
    check_root
    uninstall_services
    cleanup_python_cache
    cleanup_services_dir
    
    echo ""
    log_success "卸载完成！"
    echo ""
    echo "📋 卸载总结："
    echo "✅ 所有systemd服务已停止并删除"
    echo "✅ Python缓存已清理"
    echo ""
    echo "💡 如需重新安装，请运行: sudo ./install.sh"
    echo ""
}

# 运行主函数
main "$@" 