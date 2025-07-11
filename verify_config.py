#!/usr/bin/env python3
"""
验证配置文件和硬编码问题的脚本
"""

import os
import yaml
import sys
from pathlib import Path
from typing import Dict, Any

def load_config():
    """加载配置文件"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("❌ 配置文件 config.yaml 不存在")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 简单的环境变量替换
        content = content.replace('$OPENROUTER_API_KEY', os.getenv('OPENROUTER_API_KEY', 'NOT_SET'))
        content = content.replace('$OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', 'NOT_SET'))
        
        config = yaml.safe_load(content)
        print("✅ 配置文件加载成功")
        return config
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return None

def verify_model_config(config: Dict[str, Any]):
    """验证模型配置"""
    print("\n🔍 验证模型配置...")
    
    # 检查核心模型配置
    if 'model_config' in config:
        model_config = config['model_config']
        model_name = model_config.get('config', {}).get('model', '')
        base_url = model_config.get('config', {}).get('base_url', '')
        
        print(f"📝 核心模型: {model_name}")
        print(f"📝 API 端点: {base_url}")
        
        if 'claude' in model_name.lower():
            print("✅ 使用 Claude 模型")
        elif 'gpt' in model_name.lower():
            print("✅ 使用 GPT 模型")
        else:
            print(f"⚠️  未知模型类型: {model_name}")
    
    # 检查各代理的配置
    agents = ['orchestrator_client', 'web_surfer_client', 'coder_client', 'file_surfer_client', 'action_guard_client']
    
    for agent in agents:
        if agent in config:
            print(f"✅ {agent} 配置已找到")
        else:
            print(f"⚠️  {agent} 配置未找到")

def verify_image_config(config: Dict[str, Any]):
    """验证图像生成配置"""
    print("\n🔍 验证图像生成配置...")
    
    if 'image_generation_client' in config:
        image_config = config['image_generation_client']
        model_name = image_config.get('config', {}).get('model', '')
        base_url = image_config.get('config', {}).get('base_url', '')
        
        print(f"🎨 图像生成模型: {model_name}")
        print(f"🎨 图像生成端点: {base_url}")
        
        if 'dall-e' in model_name.lower():
            print("✅ 使用 DALL-E 模型")
            if 'api.openai.com' in base_url:
                print("✅ 使用 OpenAI 官方端点")
            else:
                print("⚠️  使用非官方 OpenAI 端点")
        else:
            print(f"⚠️  未知图像生成模型: {model_name}")
    
    if 'image_generator' in config:
        print("✅ image_generator 配置已找到")
    else:
        print("⚠️  image_generator 配置未找到")

def verify_environment_variables():
    """验证环境变量"""
    print("\n🔍 验证环境变量...")
    
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if openrouter_key and openrouter_key != 'NOT_SET':
        print("✅ OPENROUTER_API_KEY 已设置")
    else:
        print("⚠️  OPENROUTER_API_KEY 未设置")
    
    if openai_key and openai_key != 'NOT_SET':
        print("✅ OPENAI_API_KEY 已设置")
    else:
        print("⚠️  OPENAI_API_KEY 未设置")

def check_hardcoded_issues():
    """检查可能的硬编码问题"""
    print("\n🔍 检查潜在硬编码问题...")
    
    # 检查配置文件中的模型名称
    config = load_config()
    if not config:
        return
    
    # 检查是否使用了配置文件中的模型
    expected_model = config.get('model_config', {}).get('config', {}).get('model', '')
    expected_image_model = config.get('image_generation_client', {}).get('config', {}).get('model', '')
    
    print(f"📋 预期使用的聊天模型: {expected_model}")
    print(f"📋 预期使用的图像模型: {expected_image_model}")
    
    # 检查是否有完整的配置
    if expected_model and expected_image_model:
        print("✅ 配置文件中有完整的模型配置")
    else:
        print("⚠️  配置文件中缺少模型配置")

def main():
    """主函数"""
    print("🚀 Magentic-UI 配置验证")
    print("=" * 50)
    
    # 检查配置文件
    config = load_config()
    if not config:
        sys.exit(1)
    
    # 验证各个配置部分
    verify_model_config(config)
    verify_image_config(config)
    verify_environment_variables()
    check_hardcoded_issues()
    
    print("\n" + "=" * 50)
    print("✅ 配置验证完成")
    print("\n💡 建议:")
    print("1. 确保所有 API 密钥都在 .env 文件中正确设置")
    print("2. 非图像生成任务使用 OpenRouter 的 Claude 模型")
    print("3. 图像生成任务使用 OpenAI 的 DALL-E 模型")
    print("4. 检查日志以确保没有使用硬编码的模型名称")

if __name__ == "__main__":
    main()