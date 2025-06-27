#!/usr/bin/env python3
"""
Magentic-UI 模型切换工具
友好的界面用于在不同模型配置间切换
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# 可用的配置文件映射
AVAILABLE_CONFIGS = {
    "1": {
        "name": "OpenRouter Claude 3.5 Sonnet",
        "file": "config_examples/openrouter_config.yaml",
        "description": "云端最强模型，支持视觉和函数调用",
        "requirements": ["OPENROUTER_API_KEY"],
        "pros": ["最强推理能力", "支持视觉", "快速响应"],
        "cons": ["需要API费用", "需要网络连接"]
    },
    "2": {
        "name": "Ollama Gemma3 27B (本地)",
        "file": "config_examples/ollama_gemma3_config.yaml", 
        "description": "本地27B大模型，高性能推理",
        "requirements": ["本地Ollama服务", "gemma3:27b模型"],
        "pros": ["完全免费", "数据隐私", "无网络依赖"],
        "cons": ["需要大量内存", "推理较慢"]
    },
    "3": {
        "name": "Ollama Qwen2.5VL 32B (本地)",
        "file": "config_examples/ollama_config.yaml",
        "description": "本地多模态模型，支持视觉",
        "requirements": ["本地Ollama服务", "qwen2.5vl:32b模型"],
        "pros": ["支持视觉", "多模态能力", "免费"],
        "cons": ["需要更多内存", "推理最慢"]
    },
    "4": {
        "name": "Azure OpenAI GPT-4o",
        "file": "config_examples/azure_openai_config.yaml",
        "description": "企业级Azure OpenAI服务",
        "requirements": ["Azure订阅", "OpenAI部署"],
        "pros": ["企业级可靠性", "数据合规", "高性能"],
        "cons": ["需要Azure账户", "配置复杂"]
    }
}

def print_header():
    """打印工具标题"""
    print("=" * 60)
    print("🔄 Magentic-UI 模型切换工具")
    print("=" * 60)
    print()

def check_ollama_service():
    """检查Ollama服务状态"""
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            models = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            available_models = []
            for line in models:
                if line.strip():
                    model_name = line.split()[0]
                    available_models.append(model_name)
            return True, available_models
        return False, []
    except Exception:
        return False, []

def check_current_config():
    """检查当前配置"""
    config_file = Path('config.yaml')
    if not config_file.exists():
        return None, "未找到配置文件"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单检测配置类型
        if 'openrouter.ai' in content:
            return "OpenRouter", "OpenRouter Claude配置"
        elif 'gemma3:27b' in content:
            return "Ollama Gemma3", "本地Gemma3 27B配置"
        elif 'qwen2.5vl' in content:
            return "Ollama Qwen", "本地Qwen2.5VL配置"
        elif 'azure_endpoint' in content:
            return "Azure OpenAI", "Azure OpenAI配置"
        else:
            return "Unknown", "未知配置类型"
    except Exception as e:
        return None, f"读取配置文件出错: {e}"

def backup_current_config():
    """备份当前配置"""
    config_file = Path('config.yaml')
    if config_file.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = Path(f'config_backup_{timestamp}.yaml')
        shutil.copy2(config_file, backup_file)
        return backup_file
    return None

def display_available_configs():
    """显示可用配置"""
    print("🎯 可用的模型配置:")
    print("-" * 60)
    
    for key, config in AVAILABLE_CONFIGS.items():
        print(f"{key}) {config['name']}")
        print(f"   📝 {config['description']}")
        print(f"   ✅ 优点: {', '.join(config['pros'])}")
        print(f"   ⚠️  缺点: {', '.join(config['cons'])}")
        print(f"   🔧 需求: {', '.join(config['requirements'])}")
        print()

def validate_choice(choice):
    """验证用户选择"""
    if choice not in AVAILABLE_CONFIGS:
        return False, "无效选择"
    
    config = AVAILABLE_CONFIGS[choice]
    
    # 特殊验证逻辑
    if choice == "2":  # Gemma3配置
        ollama_running, models = check_ollama_service()
        if not ollama_running:
            return False, "Ollama服务未运行，请先启动: ollama serve"
        if 'gemma3:27b' not in models:
            return False, f"未找到gemma3:27b模型，当前模型: {models}"
    
    elif choice == "3":  # Qwen配置
        ollama_running, models = check_ollama_service()
        if not ollama_running:
            return False, "Ollama服务未运行，请先启动: ollama serve"
        qwen_models = [m for m in models if 'qwen' in m.lower()]
        if not qwen_models:
            return False, f"未找到Qwen模型，当前模型: {models}"
    
    return True, "验证通过"

def switch_config(choice):
    """切换配置"""
    config = AVAILABLE_CONFIGS[choice]
    source_file = Path(config['file'])
    target_file = Path('config.yaml')
    
    if not source_file.exists():
        return False, f"配置文件不存在: {source_file}"
    
    try:
        # 备份当前配置
        backup_file = backup_current_config()
        if backup_file:
            print(f"✅ 已备份当前配置: {backup_file}")
        
        # 复制新配置
        shutil.copy2(source_file, target_file)
        return True, f"已切换到: {config['name']}"
    
    except Exception as e:
        return False, f"切换失败: {e}"

def create_env_template(choice):
    """创建对应的环境变量模板"""
    env_file = Path('.env')
    
    if choice == "1":  # OpenRouter
        env_content = """# OpenRouter API 配置
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-api-key-here
OPENAI_API_KEY=sk-or-v1-your-openrouter-api-key-here
"""
    elif choice in ["2", "3"]:  # Ollama
        env_content = """# Ollama 本地配置
OLLAMA_HOST=http://localhost:11434
"""
    elif choice == "4":  # Azure
        env_content = """# Azure OpenAI 配置
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT=your-deployment-name
AZURE_DEPLOYMENT_MINI=your-mini-deployment-name
"""
    else:
        return False, "未知配置类型"
    
    try:
        if not env_file.exists():
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            os.chmod(env_file, 0o600)  # 设置安全权限
            return True, f"已创建环境变量模板: {env_file}"
        else:
            return True, f"环境变量文件已存在: {env_file}"
    except Exception as e:
        return False, f"创建环境变量文件失败: {e}"

def main():
    """主函数"""
    print_header()
    
    # 检查当前配置
    current_type, current_desc = check_current_config()
    if current_type:
        print(f"📋 当前配置: {current_type}")
        print(f"   {current_desc}")
        print()
    
    # 检查Ollama状态
    ollama_running, ollama_models = check_ollama_service()
    if ollama_running:
        print("✅ Ollama服务运行中")
        print(f"📦 可用模型: {', '.join(ollama_models)}")
        print()
    else:
        print("⚠️  Ollama服务未运行 (本地模型不可用)")
        print()
    
    # 显示可用配置
    display_available_configs()
    
    # 用户选择
    while True:
        try:
            choice = input("请选择要切换的配置 (1-4, q退出): ").strip()
            
            if choice.lower() == 'q':
                print("👋 退出切换工具")
                sys.exit(0)
            
            if choice not in AVAILABLE_CONFIGS:
                print("❌ 无效选择，请输入1-4或q")
                continue
            
            # 验证选择
            valid, message = validate_choice(choice)
            if not valid:
                print(f"❌ {message}")
                continue
            
            # 确认切换
            config_name = AVAILABLE_CONFIGS[choice]['name']
            confirm = input(f"确认切换到 '{config_name}' ? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ 取消切换")
                continue
            
            # 执行切换
            success, message = switch_config(choice)
            if success:
                print(f"✅ {message}")
                
                # 创建环境变量模板
                env_success, env_message = create_env_template(choice)
                if env_success:
                    print(f"✅ {env_message}")
                else:
                    print(f"⚠️  {env_message}")
                
                print()
                print("📋 下一步操作:")
                if choice == "1":
                    print("1. 编辑 .env 文件，填入OpenRouter API密钥")
                    print("2. 运行测试: python test_config.py")
                elif choice in ["2", "3"]:
                    print("1. 确保Ollama服务运行: ollama serve")
                    print("2. 运行测试: python test_config.py")
                elif choice == "4":
                    print("1. 编辑 .env 文件，填入Azure配置")
                    print("2. 配置Azure认证")
                    print("3. 运行测试: python test_config.py")
                
                print("3. 启动应用: python run_local.py")
                print()
                print("🎉 配置切换完成！")
                break
            else:
                print(f"❌ {message}")
                
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出")
            sys.exit(0)
        except Exception as e:
            print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main() 