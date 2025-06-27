#!/usr/bin/env python3
"""
Magentic-UI 启动脚本
自动加载 .env 文件中的环境变量，并处理 config.yaml 中的环境变量替换
"""

import os
import sys
import subprocess
import tempfile
import yaml
from pathlib import Path
from string import Template

def load_env_file():
    """加载 .env 文件中的环境变量"""
    try:
        from dotenv import load_dotenv
        
        # 寻找 .env 文件
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ 已加载环境变量文件: {env_file.absolute()}")
            
            # 检查关键环境变量
            if os.getenv('OPENROUTER_API_KEY'):
                print("✅ 检测到 OPENROUTER_API_KEY")
            elif os.getenv('OPENAI_API_KEY'):
                print("✅ 检测到 OPENAI_API_KEY")
            else:
                print("⚠️  警告: 未检测到 API 密钥，请确保 .env 文件中设置了正确的 API 密钥")
        else:
            print("⚠️  警告: 未找到 .env 文件，请从 .env.example 复制并配置")
            
    except ImportError:
        print("❌ python-dotenv 未安装，请运行: uv add python-dotenv")
        sys.exit(1)

def process_config_file(config_path):
    """处理配置文件中的环境变量替换"""
    if not config_path.exists():
        return None
        
    try:
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # 使用 Template 进行环境变量替换
        template = Template(config_content)
        
        # 获取所有环境变量
        env_vars = dict(os.environ)
        
        # 执行替换
        processed_content = template.safe_substitute(env_vars)
        
        # 验证 YAML 格式
        yaml.safe_load(processed_content)
        
        # 创建临时配置文件
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        temp_config.write(processed_content)
        temp_config.close()
        
        print(f"✅ 已处理配置文件: {config_path}")
        print(f"📝 临时配置文件: {temp_config.name}")
        
        return temp_config.name
        
    except Exception as e:
        print(f"❌ 处理配置文件时出错: {e}")
        return str(config_path)

def main():
    """主函数"""
    print("🚀 启动 Magentic-UI...")
    
    # 加载环境变量
    load_env_file()
    
    # 构建启动命令
    cmd = ["uv", "run", "magentic-ui"]
    
    # 处理配置文件
    config_path = Path("config.yaml")
    if config_path.exists():
        processed_config = process_config_file(config_path)
        if processed_config:
            cmd.extend(["--config", processed_config])
            print("✅ 使用处理后的配置文件")
    else:
        print("ℹ️  未找到 config.yaml，使用默认配置")
    
    # 添加其他命令行参数
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    else:
        cmd.extend(["--port", "8081"])
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    
    # 启动 Magentic-UI
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Magentic-UI 已停止")
    finally:
        # 清理临时文件
        if 'processed_config' in locals() and processed_config and processed_config != str(config_path):
            try:
                os.unlink(processed_config)
                print("🧹 已清理临时配置文件")
            except:
                pass

if __name__ == "__main__":
    main() 