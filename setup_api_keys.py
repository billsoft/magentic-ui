#!/usr/bin/env python3
"""
API密钥配置脚本
自动创建.env文件并引导用户配置API密钥
"""

import os
import sys
from pathlib import Path

def main():
    print("🔑 Magentic-UI API密钥配置助手")
    print("=" * 50)
    
    # 检查.env文件是否存在
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env文件已存在")
        
        # 检查是否包含有效的API密钥
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
            has_openrouter = 'OPENROUTER_API_KEY=' in content and 'your-openrouter-api-key-here' not in content
            has_openai = 'OPENAI_API_KEY=' in content and 'your-openrouter-api-key-here' not in content
            
            if has_openrouter and has_openai:
                print("✅ API密钥配置看起来正确")
                print("\n🧪 测试环境变量加载:")
                try:
                    from dotenv import load_dotenv
                    load_dotenv(env_file)
                    
                    openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
                    openai_key = os.getenv('OPENAI_API_KEY', '')
                    
                    if openrouter_key and openrouter_key != 'your-openrouter-api-key-here':
                        print(f"✅ OPENROUTER_API_KEY: {openrouter_key[:20]}...")
                    else:
                        print("❌ OPENROUTER_API_KEY 未正确设置")
                        
                    if openai_key and openai_key != 'your-openrouter-api-key-here':
                        print(f"✅ OPENAI_API_KEY: {openai_key[:20]}...")
                    else:
                        print("❌ OPENAI_API_KEY 未正确设置")
                        
                except ImportError:
                    print("⚠️ python-dotenv 未安装，请运行: uv add python-dotenv")
                    
                return
            else:
                print("⚠️ .env文件存在但API密钥配置不完整")
        except Exception as e:
            print(f"❌ 读取.env文件时出错: {e}")
    
    # 创建或更新.env文件
    print("\n📝 创建API密钥配置...")
    
    openrouter_key = input("\n请输入您的OpenRouter API密钥 (sk-or-v1-...): ").strip()
    if not openrouter_key:
        print("❌ OpenRouter API密钥不能为空")
        sys.exit(1)
    
    if not openrouter_key.startswith('sk-or-v1-'):
        print("⚠️ 警告: OpenRouter API密钥通常以 'sk-or-v1-' 开头")
        confirm = input("是否继续? (y/N): ").strip().lower()
        if confirm != 'y':
            sys.exit(1)
    
    # 询问是否有单独的OpenAI密钥
    has_separate_openai = input("\n您是否有单独的OpenAI API密钥? (y/N): ").strip().lower() == 'y'
    
    if has_separate_openai:
        openai_key = input("请输入您的OpenAI API密钥 (sk-...): ").strip()
        if not openai_key:
            openai_key = openrouter_key
            print("使用OpenRouter密钥作为OpenAI密钥")
    else:
        openai_key = openrouter_key
        print("使用OpenRouter密钥作为OpenAI密钥")
    
    # 创建.env文件内容
    env_content = f"""# =====================================================
# Magentic-UI 环境变量配置
# 由 setup_api_keys.py 自动生成
# =====================================================

# OpenRouter API 密钥 (主要使用)
OPENROUTER_API_KEY={openrouter_key}

# OpenAI API 密钥 (autogen-ext 要求)
OPENAI_API_KEY={openai_key}

# =====================================================
# 说明:
# - OPENROUTER_API_KEY: 用于访问 OpenRouter 的各种模型
# - OPENAI_API_KEY: autogen-ext 内部要求，可以与 OpenRouter 密钥相同
# =====================================================
"""
    
    # 写入.env文件
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"\n✅ .env文件已创建: {env_file.absolute()}")
        print("\n🚨 重要提醒:")
        print("1. .env文件包含敏感信息，请不要提交到版本控制系统")
        print("2. 现在可以重新启动 Magentic-UI:")
        print("   conda activate magentic-ui && python load_env.py --port 8081")
        
    except Exception as e:
        print(f"❌ 创建.env文件时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 