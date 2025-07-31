#!/bin/bash
# -*- coding: utf-8 -*-
# 音量旋钮校准脚本 - 简化版本（检查+校准一体）

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 模块名称（从目录名自动获取）
MODULE_NAME=$(basename "$(pwd)")
CONFIG_FILE="config.ini"

echo -e "${BLUE}🎛️  $MODULE_NAME 模块校准脚本${NC}"
echo "========================================="

# 检查配置文件是否存在
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${RED}❌ 配置文件 $CONFIG_FILE 不存在${NC}"
    exit 1
fi

# 📋 功能1：检查校准状态（纯shell实现）
check_calibration() {
    echo -e "${BLUE}🔍 检查校准状态...${NC}"
    
    # 读取配置值（使用awk解析ini文件）
    min_voltage=$(awk -F'=' '/^min_voltage/{gsub(/[ \t]/, "", $2); print $2}' "$CONFIG_FILE")
    max_voltage=$(awk -F'=' '/^max_voltage/{gsub(/[ \t]/, "", $2); print $2}' "$CONFIG_FILE")
    
    echo "  当前配置: min_voltage=$min_voltage, max_voltage=$max_voltage"
    
    # 检查是否为无效默认值
    if [[ "$min_voltage" == "-1.0" && "$max_voltage" == "-1.0" ]]; then
        echo -e "${RED}❌ 检测到无效默认值，需要校准${NC}"
        return 1
    fi
    
    # 检查值是否有效（非负数且min < max）
    if (( $(echo "$min_voltage < 0" | bc -l) )) || (( $(echo "$max_voltage < 0" | bc -l) )); then
        echo -e "${RED}❌ 检测到负值，需要重新校准${NC}"
        return 1
    fi
    
    if (( $(echo "$min_voltage >= $max_voltage" | bc -l) )); then
        echo -e "${RED}❌ 最小值大于等于最大值，需要重新校准${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ 校准状态正常${NC}"
    return 0
}

# 📋 功能2：执行校准（调用Python程序）
run_calibration() {
    echo -e "${BLUE}🔧 开始校准...${NC}"
    echo "----------------------------------------"
    
    # 查找校准程序
    POSSIBLE_PROGRAMS=(
        "${MODULE_NAME}_pub.py"
        "publisher.py"
        "${MODULE_NAME}.py"
        "main.py"
    )
    
    CALIBRATE_PROGRAM=""
    for prog in "${POSSIBLE_PROGRAMS[@]}"; do
        if [[ -f "$prog" ]]; then
            CALIBRATE_PROGRAM="$prog"
            break
        fi
    done
    
    if [[ -z "$CALIBRATE_PROGRAM" ]]; then
        echo -e "${RED}❌ 未找到校准程序${NC}"
        return 1
    fi
    
    echo -e "${BLUE}ℹ️ 使用校准程序: $CALIBRATE_PROGRAM${NC}"
    
    # 停止服务（如果在运行）
    SERVICE_NAME="${MODULE_NAME}-publisher"
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        echo -e "${YELLOW}⏸️  停止服务: $SERVICE_NAME${NC}"
        sudo systemctl stop "$SERVICE_NAME"
        SERVICE_WAS_RUNNING=true
    else
        echo -e "${BLUE}📝 服务未运行: $SERVICE_NAME${NC}"
        SERVICE_WAS_RUNNING=false
    fi
    
    # 执行校准
    if python "$CALIBRATE_PROGRAM" --calibrate; then
        echo -e "${GREEN}✅ 校准完成${NC}"
        
        # 重新启动服务（如果之前在运行）
        if [[ "$SERVICE_WAS_RUNNING" == "true" ]]; then
            echo -e "${BLUE}🚀 重新启动服务: $SERVICE_NAME${NC}"
            sudo systemctl start "$SERVICE_NAME"
            
            # 检查服务状态
            sleep 2
            if systemctl is-active --quiet "$SERVICE_NAME"; then
                echo -e "${GREEN}✅ 服务启动成功${NC}"
            else
                echo -e "${RED}❌ 服务启动失败，请检查日志${NC}"
            fi
        fi
        
        return 0
    else
        echo -e "${RED}❌ 校准失败${NC}"
        return 1
    fi
}

# 主逻辑
main() {
    # 首先检查校准状态
    if check_calibration; then
        echo ""
        echo -e "${GREEN}🎉 模块已校准，无需重新校准${NC}"
        echo ""
        echo "💡 如需重新校准，请运行:"
        echo "   $0 --force"
        exit 0
    fi
    
    # 如果未校准，询问是否执行校准
    echo ""
    echo -e "${YELLOW}❓ 检测到模块未校准，是否现在进行校准？ [y/N]${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        run_calibration
        
        if [[ $? -eq 0 ]]; then
            echo ""
            echo -e "${GREEN}🎉 校准完成！模块现在可以正常使用了${NC}"
        else
            echo ""
            echo -e "${RED}❌ 校准失败，请检查硬件连接和配置${NC}"
            exit 1
        fi
    else
        echo ""
        echo -e "${YELLOW}⚠️  校准被取消，模块无法正常启动${NC}"
        echo ""
        echo "💡 要手动校准，请运行:"
        echo "   python ${CALIBRATE_PROGRAM:-MODULE_pub.py} --calibrate"
        exit 1
    fi
}

# 处理命令行参数
case "${1:-}" in
    --check)
        check_calibration
        exit $?
        ;;
    --force)
        echo -e "${YELLOW}🔄 强制重新校准...${NC}"
        run_calibration
        exit $?
        ;;
    --help)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --check    仅检查校准状态"
        echo "  --force    强制重新校准"
        echo "  --help     显示此帮助"
        echo ""
        echo "默认行为: 检查校准状态，如果未校准则提示进行校准"
        exit 0
        ;;
    *)
        main
        ;;
esac