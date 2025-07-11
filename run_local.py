#!/usr/bin/env python3
"""
Magentic-UI 本地运行脚本（不使用 Docker）
适用于没有 Docker 或希望完全本地运行的情况
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
        print("❌ python-dotenv 未安装，请运行: pip install python-dotenv")
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

def check_frontend():
    """检查前端是否需要构建"""
    frontend_dir = Path("frontend")
    if frontend_dir.exists():
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print("⚠️  前端依赖未安装，请先运行:")
            print("   cd frontend && npm install")
            return False
        else:
            print("✅ 前端依赖已安装")
            return True
    return True

def main():
    """主函数"""
    print("🚀 启动 Magentic-UI (本地模式 - 不使用 Docker)")
    print("=" * 60)
    
    # 检查前端
    check_frontend()
    
    # 加载环境变量
    load_env_file()
    
    # 检查是否可以直接导入 magentic_ui
    try:
        import magentic_ui
        print("✅ 检测到 magentic_ui 模块")
        # 直接使用 Python 模块方式启动
        cmd = [sys.executable, "-m", "magentic_ui.backend.cli"]
    except ImportError:
        print("⚠️  magentic_ui 未安装，尝试使用 uv run")
        # 回退到 uv run 方式
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
    
    # 添加本地运行参数
    cmd.append("--run-without-docker")
    print("🏠 启用本地模式（不使用 Docker）")
    
    # 添加其他命令行参数
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    else:
        cmd.extend(["--port", "8081"])
    
    print("=" * 60)
    print("📋 本地模式限制说明:")
    print("   • 无法使用代码执行功能（Coder Agent）")
    print("   • 无法使用文件浏览功能（File Surfer Agent）")
    print("   • 无法在界面中显示实时浏览器视图")
    print("   • 但仍可使用网页浏览和AI对话功能")
    print("=" * 60)
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    print("🌐 启动后访问: http://localhost:8081")
    print("⏹️  按 Ctrl+C 停止服务")
    print("=" * 60)
    
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