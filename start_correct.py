#!/usr/bin/env python3
"""
正确的 Magentic-UI 启动脚本
本地代码 + Docker 容器协同工作
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
                print("⚠️  警告: 未检测到 API 密钥")
        else:
            print("⚠️  警告: 未找到 .env 文件")
            
    except ImportError:
        print("❌ python-dotenv 未安装")
        sys.exit(1)

def check_docker_environment():
    """检查 Docker 环境和现有容器"""
    print("🔍 检查 Docker 环境...")
    
    # 检查 Docker 是否运行
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker 未安装或无法访问")
            return False
        print(f"✅ Docker 版本: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Docker 未安装")
        return False
    
    # 检查 Docker 守护进程
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker 守护进程未运行")
            return False
        print("✅ Docker 守护进程运行正常")
    except:
        print("❌ 无法连接到 Docker 守护进程")
        return False
    
    # 检查 Magentic-UI 镜像
    try:
        result = subprocess.run(['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'], capture_output=True, text=True)
        images = result.stdout.strip().split('\n')
        
        browser_image = any('magentic-ui-vnc-browser' in img for img in images)
        python_image = any('magentic-ui-python-env' in img for img in images)
        
        if browser_image and python_image:
            print("✅ Magentic-UI Docker 镜像已就绪")
            return True
        else:
            print("⚠️  部分 Magentic-UI Docker 镜像缺失")
            if not browser_image:
                print("   - 缺失: magentic-ui-vnc-browser")
            if not python_image:
                print("   - 缺失: magentic-ui-python-env")
            print("   系统将自动构建缺失的镜像")
            return True
    except:
        print("❌ 无法检查 Docker 镜像")
        return False

def check_existing_containers():
    """检查现有容器"""
    print("\n🔍 检查现有容器...")
    try:
        result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}'], capture_output=True, text=True)
        containers = result.stdout.strip().split('\n')
        
        magentic_containers = [c for c in containers if 'magentic' in c.lower()]
        if magentic_containers:
            print(f"✅ 发现 {len(magentic_containers)} 个 Magentic-UI 相关容器")
            
            # 检查运行中的容器
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], capture_output=True, text=True)
            running_containers = result.stdout.strip().split('\n')
            running_magentic = [c for c in running_containers if 'magentic' in c.lower()]
            
            print(f"✅ 其中 {len(running_magentic)} 个正在运行")
            return True
        else:
            print("ℹ️  未发现现有容器，将根据需要创建")
            return True
    except:
        print("⚠️  无法检查现有容器")
        return True

def process_config_file(config_path):
    """处理配置文件中的环境变量替换"""
    if not config_path.exists():
        return None
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        template = Template(config_content)
        env_vars = dict(os.environ)
        processed_content = template.safe_substitute(env_vars)
        
        # 验证 YAML 格式
        yaml.safe_load(processed_content)
        
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        temp_config.write(processed_content)
        temp_config.close()
        
        print(f"✅ 配置文件已处理: {config_path}")
        return temp_config.name
        
    except Exception as e:
        print(f"❌ 处理配置文件时出错: {e}")
        return str(config_path)

def main():
    """主函数"""
    print("🚀 启动 Magentic-UI (本地代码 + Docker 容器协同)")
    print("=" * 60)
    
    # 加载环境变量
    load_env_file()
    
    # 检查 Docker 环境
    if not check_docker_environment():
        print("\n❌ Docker 环境检查失败")
        sys.exit(1)
    
    # 检查现有容器
    check_existing_containers()
    
    # 确定使用的 Python 解释器
    python_executable = sys.executable
    print(f"📍 Python 解释器: {python_executable}")
    
    # 构建启动命令
    cmd = [python_executable, "-m", "magentic_ui.backend.cli"]
    
    # 处理配置文件
    config_path = Path("config.yaml")
    if config_path.exists():
        processed_config = process_config_file(config_path)
        if processed_config:
            cmd.extend(["--config", processed_config])
    
    # 添加端口参数
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    else:
        cmd.extend(["--port", "8081"])
    
    print("\n" + "=" * 60)
    print("🎯 架构说明:")
    print("   🖥️  本地代码: 协调层 (FastAPI、WebSocket、代理管理)")
    print("   🐳 Docker 容器: 执行层 (浏览器、代码执行、文件操作)")
    print("   🔗 通信方式: WebSocket + Docker API")
    print("   📁 数据共享: 挂载卷 (~/.magentic_ui)")
    print("=" * 60)
    
    print(f"🔧 启动命令: {' '.join(cmd)}")
    print("🌐 访问地址: http://localhost:8081")
    print("⏹️  按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 启动服务
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Magentic-UI 已停止")
    finally:
        # 清理临时文件
        if 'processed_config' in locals() and processed_config and processed_config != str(config_path):
            try:
                os.unlink(processed_config)
                print("🧹 已清理临时文件")
            except:
                pass

if __name__ == "__main__":
    main()