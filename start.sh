#!/bin/bash
# Magentic-UI 启动脚本
# 
# 使用方法:
#   ./start.sh          # 正确的混合模式（本地代码 + Docker 容器）
#   ./start.sh local    # 本地模式（功能受限，仅用于测试）

echo "🚀 Magentic-UI 启动脚本"
echo "========================"

# 检查参数
if [[ "$1" == "local" ]]; then
    echo "🏠 使用本地模式启动（功能受限，仅用于测试）"
    python run_local.py
elif [[ "$1" == "hybrid" ]] || [[ -z "$1" ]]; then
    echo "🎯 使用混合模式启动（本地代码 + Docker 容器）"
    python start_correct.py
else
    echo "❌ 未知参数: $1"
    echo "使用方法:"
    echo "  ./start.sh          # 混合模式（推荐）"
    echo "  ./start.sh hybrid   # 混合模式（推荐）"
    echo "  ./start.sh local    # 本地模式（功能受限）"
    exit 1
fi