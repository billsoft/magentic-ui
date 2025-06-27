#!/bin/bash

# =====================================================
# Magentic-UI OpenAI兼容模型快速设置脚本
# 自动化配置过程，简化部署流程
# =====================================================

set -e  # 遇到错误时退出

echo "🚀 开始 Magentic-UI OpenAI兼容模型配置..."

# 检查Python版本
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python版本: $PYTHON_VERSION"

# 检查uv包管理器
echo "🔍 检查uv包管理器..."
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv未安装，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
fi

# 安装必要依赖
echo "📦 安装必要依赖..."
uv add python-dotenv pyyaml

# 创建配置目录
echo "📁 创建配置目录..."
mkdir -p config_examples
mkdir -p setup_scripts

# 选择配置类型
echo ""
echo "🎯 请选择要配置的模型类型:"
echo "1) OpenRouter (推荐)"
echo "2) Ollama (本地)"
echo "3) Azure OpenAI"
echo "4) 自定义配置"
read -p "请输入选择 (1-4): " choice

case $choice in
    1)
        echo "🔧 配置OpenRouter..."
        CONFIG_FILE="config_examples/openrouter_config.yaml"
        ENV_TEMPLATE="openrouter"
        ;;
    2)
        echo "🔧 配置Ollama..."
        CONFIG_FILE="config_examples/ollama_config.yaml"
        ENV_TEMPLATE="ollama"
        ;;
    3)
        echo "🔧 配置Azure OpenAI..."
        CONFIG_FILE="config_examples/azure_openai_config.yaml"
        ENV_TEMPLATE="azure"
        ;;
    4)
        echo "🔧 使用自定义配置..."
        CONFIG_FILE="config.yaml"
        ENV_TEMPLATE="custom"
        ;;
    *)
        echo "❌ 无效选择，退出"
        exit 1
        ;;
esac

# 复制配置文件
if [ -f "$CONFIG_FILE" ]; then
    echo "📝 复制配置文件..."
    cp "$CONFIG_FILE" config.yaml
    echo "✅ 配置文件已创建: config.yaml"
else
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 创建环境变量文件
echo "🔐 创建环境变量文件..."
if [ ! -f ".env" ]; then
    case $ENV_TEMPLATE in
        "openrouter")
            cat > .env << EOF
# OpenRouter API 配置
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-api-key-here
OPENAI_API_KEY=sk-or-v1-your-openrouter-api-key-here
EOF
            ;;
        "ollama")
            cat > .env << EOF
# Ollama 本地配置
OLLAMA_HOST=http://localhost:11434
EOF
            ;;
        "azure")
            cat > .env << EOF
# Azure OpenAI 配置
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT=your-deployment-name
AZURE_DEPLOYMENT_MINI=your-mini-deployment-name
AZURE_API_KEY=your-azure-api-key
EOF
            ;;
        "custom")
            cat > .env << EOF
# 自定义API配置
CUSTOM_API_KEY=your-api-key-here
CUSTOM_BASE_URL=https://your-api.com/v1
EOF
            ;;
    esac
    echo "✅ 环境变量模板已创建: .env"
    echo "⚠️  请编辑 .env 文件，填入真实的API密钥"
else
    echo "ℹ️  .env 文件已存在，跳过创建"
fi

# 设置文件权限
chmod 600 .env
echo "🔒 已设置环境变量文件权限"

# 创建启动脚本
echo "🚀 创建启动脚本..."
if [ ! -f "load_env.py" ]; then
    echo "⚠️  load_env.py 不存在，请确保从指南中复制该文件"
fi

if [ ! -f "run_local.py" ]; then
    echo "⚠️  run_local.py 不存在，请确保从指南中复制该文件"
fi

# 检查核心代码修改
echo "🔍 检查核心代码修改..."
TEAMMANAGER_FILE="src/magentic_ui/backend/teammanager/teammanager.py"
if [ -f "$TEAMMANAGER_FILE" ]; then
    if grep -q "ModelClientConfigs" "$TEAMMANAGER_FILE"; then
        echo "✅ 核心代码修改已应用"
    else
        echo "⚠️  警告: 核心代码修改可能未应用，请检查 $TEAMMANAGER_FILE"
    fi
else
    echo "❌ 核心文件不存在: $TEAMMANAGER_FILE"
fi

# 完成设置
echo ""
echo "🎉 配置完成！"
echo ""
echo "📋 下一步操作:"
echo "1. 编辑 .env 文件，填入真实的API密钥"
echo "2. 运行测试: python test_config.py"
echo "3. 启动应用: python run_local.py"
echo ""
echo "📖 详细说明请参考: OPENAI_COMPATIBLE_MODELS_SETUP_GUIDE.md"
echo ""
echo "🆘 如遇问题，请检查:"
echo "- API密钥是否正确"
echo "- 网络连接是否正常"
echo "- 配置文件语法是否正确"
echo ""
echo "✨ 祝您使用愉快！" 