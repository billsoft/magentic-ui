#!/usr/bin/env python3
"""
Magentic-UI 启动脚本
自动加载 .env 文件中的环境变量，并处理 config.yaml 中的环境变量替换
智能检测Docker问题并自动切换到无Docker模式
"""

import os
import sys
import subprocess
import tempfile
import yaml
import docker
import socket
from pathlib import Path
from string import Template
from docker.errors import DockerException, APIError, ImageNotFound

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

def check_port_available(port: int) -> bool:
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result != 0  # 0表示连接成功，即端口被占用
    except Exception:
        return False

def find_available_port(start_port: int = 8081, max_tries: int = 50) -> int:
    """寻找可用端口"""
    for port in range(start_port, start_port + max_tries):
        if check_port_available(port):
            return port
    raise RuntimeError(f"无法在 {start_port}-{start_port + max_tries} 范围内找到可用端口")

def get_optimal_port(preferred_port: int = 8081) -> tuple[int, str]:
    """获取最优端口并返回状态信息"""
    if check_port_available(preferred_port):
        return preferred_port, f"✅ 使用首选端口 {preferred_port}"
    
    try:
        available_port = find_available_port(preferred_port + 1)
        return available_port, f"⚠️ 端口 {preferred_port} 被占用，自动使用端口 {available_port}"
    except RuntimeError as e:
        return preferred_port, f"❌ {e}，尝试使用端口 {preferred_port}（可能失败）"

def check_docker_health():
    """
    检查Docker健康状态
    返回: (is_healthy, should_use_docker, message)
    """
    try:
        client = docker.from_env()
        client.ping()
        
        # 检查关键镜像是否可用
        try:
            client.images.get("magentic-ui-vnc-browser")
            return True, True, "Docker运行正常，镜像可用"
        except ImageNotFound:
            return True, True, "Docker运行正常，需要构建镜像"
        except APIError as e:
            if "500 Server Error" in str(e) or "input/output error" in str(e):
                return False, False, f"Docker存储损坏: {str(e)[:100]}..."
            else:
                return True, True, f"Docker运行正常: {e}"
                
    except DockerException as e:
        return False, False, f"Docker未运行或无法访问: {e}"
    except Exception as e:
        return False, False, f"Docker检测失败: {e}"

def process_config_file(config_path: Path):
    """处理配置文件中的环境变量替换"""
    if not config_path.exists():
        return None
        
    try:
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # 添加调试信息
        print(f"🔍 DEBUG: 配置文件大小: {len(config_content)} 字符")
        if '$OPENROUTER_API_KEY' in config_content:
            print("🔍 DEBUG: 配置文件包含 $OPENROUTER_API_KEY 占位符")
        else:
            print("🔍 DEBUG: 配置文件不包含 $OPENROUTER_API_KEY 占位符")
        
        # 🔧 第一步：解析原始配置并进行结构转换
        original_config = yaml.safe_load(config_content)
        
        # 如果没有model_client_configs字段，进行结构转换
        if 'model_client_configs' not in original_config:
            print("🔧 检测到平铺配置结构，正在转换为嵌套结构...")
            
            # 提取所有模型客户端配置
            model_configs = {}
            client_keys = ['orchestrator_client', 'coder_client', 'web_surfer_client', 'file_surfer_client', 'action_guard_client', 'image_generator']
            
            for key in client_keys:
                if key in original_config:
                    # 移除_client后缀（除了image_generator）
                    clean_key = key.replace('_client', '') if key != 'image_generator' else key
                    model_configs[clean_key] = original_config.pop(key)
                    print(f"  ✅ 迁移配置: {key} -> model_client_configs.{clean_key}")
            
            # 添加到新结构中
            original_config['model_client_configs'] = model_configs
            print(f"🎯 配置结构转换完成，模型配置数量: {len(model_configs)}")
        
        # 🔧 第二步：将转换后的配置转换为字符串
        restructured_content = yaml.safe_dump(original_config, default_flow_style=False)
        
        # 🔧 第三步：使用 Template 进行环境变量替换
        template = Template(restructured_content)
        
        # 🔧 关键修复：强制重新加载环境变量
        # 确保.env文件中的变量能正确读取到当前进程
        from dotenv import load_dotenv
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file, override=True)  # override=True 强制覆盖现有变量
            print("🔧 DEBUG: 强制重新加载 .env 文件")
        
        # 获取所有环境变量
        env_vars = dict(os.environ)
        
        # 调试环境变量
        openrouter_key = env_vars.get('OPENROUTER_API_KEY', '')
        openai_key = env_vars.get('OPENAI_API_KEY', '')
        print(f"🔍 DEBUG: OPENROUTER_API_KEY = {openrouter_key[:20]}..." if openrouter_key else "🔍 DEBUG: OPENROUTER_API_KEY 未设置")
        print(f"🔍 DEBUG: OPENAI_API_KEY = {openai_key[:20]}..." if openai_key else "🔍 DEBUG: OPENAI_API_KEY 未设置")
        
        # 执行替换
        processed_content = template.safe_substitute(env_vars)
        
        # 检查替换结果
        if '$OPENROUTER_API_KEY' in processed_content:
            print("🔍 DEBUG: 替换后仍包含 $OPENROUTER_API_KEY 占位符")
        else:
            print("🔍 DEBUG: $OPENROUTER_API_KEY 已被替换")
        
        # 验证最终配置格式和image_generator配置
        final_config = yaml.safe_load(processed_content)
        if 'model_client_configs' in final_config and 'image_generator' in final_config['model_client_configs']:
            print("🎨 DEBUG: image_generator配置检查通过")
        else:
            print("❌ DEBUG: image_generator配置缺失")
        
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
    print("=" * 50)
    
    # 加载环境变量
    load_env_file()
    
    # 智能检测Docker状态
    _, should_use_docker, docker_message = check_docker_health()
    print(f"🐳 Docker状态: {docker_message}")
    
    # 强制端口处理 - 必须使用8081端口
    target_port = 8081
    user_args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # 从命令行参数中提取用户指定的端口
    for i, arg in enumerate(user_args):
        if arg == "--port" and i + 1 < len(user_args):
            try:
                target_port = int(user_args[i + 1])
                break
            except ValueError:
                pass
    
    # 强制清理目标端口占用
    if not check_port_available(target_port):
        print(f"⚠️ 端口 {target_port} 被占用，正在强制清理...")
        try:
            # 强制杀死占用端口的进程
            result = subprocess.run(f"lsof -ti:{target_port} | xargs -r kill -9", 
                                  shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ 已清理端口 {target_port} 的占用程序")
                import time
                time.sleep(2)  # 等待端口释放
            else:
                print(f"⚠️ 清理端口时出现问题，但将继续尝试启动")
        except Exception as e:
            print(f"⚠️ 清理端口时出错: {e}")
    
    print(f"🔌 目标端口: {target_port} (强制使用)")
    
    # 构建启动命令
    cmd = ["uv", "run", "magentic-ui"]
    
    # 处理配置文件
    config_path = Path("config.yaml")
    processed_config = None
    if config_path.exists():
        processed_config = process_config_file(config_path)
        if processed_config:
            cmd.extend(["--config", processed_config])
            print("✅ 使用处理后的配置文件")
    else:
        print("ℹ️  未找到 config.yaml，使用默认配置")
    
    # 处理命令行参数
    if user_args:
        # 用户提供了参数，处理端口参数
        args = []
        skip_next = False
        port_found = False
        for i, arg in enumerate(user_args):
            if skip_next:
                skip_next = False
                continue
            
            if arg == "--port":
                args.extend(["--port", str(target_port)])
                skip_next = True
                port_found = True
            else:
                args.append(arg)
        
        # 如果用户没有指定端口，添加目标端口
        if not port_found:
            args.extend(["--port", str(target_port)])
    else:
        # 用户没有提供参数，使用默认设置
        args = ["--port", str(target_port)]
    
    # 如果Docker不健康且用户没有手动指定Docker选项，自动添加无Docker模式
    has_docker_option = any("--run-without-docker" in arg or "--docker" in arg for arg in args)
    if not should_use_docker and not has_docker_option:
        print("⚠️  检测到Docker问题，自动切换到无Docker模式")
        args.insert(0, "--run-without-docker")
    
    cmd.extend(args)
    
    print("=" * 50)
    print(f"🔧 执行命令: {' '.join(cmd)}")
    print(f"🌐 启动后访问: http://localhost:{target_port}")
    print("⏹️  按 Ctrl+C 停止服务")
    print("=" * 50)
    
    # ✅ 关键修复：显式传递环境变量给子进程
    # 确保所有环境变量（特别是API密钥）正确传递给uv run进程
    current_env = os.environ.copy()
    
    # 调试：打印关键环境变量
    print("🔍 DEBUG: 准备传递给子进程的环境变量:")
    for key in ["OPENROUTER_API_KEY", "OPENAI_API_KEY"]:
        value = current_env.get(key, "NOT_FOUND")
        if value != "NOT_FOUND":
            print(f"  {key} = {value[:20]}...")
        else:
            print(f"  {key} = 未设置")
    
    # 启动 Magentic-UI
    try:
        subprocess.run(cmd, check=True, env=current_env)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n🛠️ 故障排除建议:")
        print(f"1. 检查端口 {target_port} 是否真的可用")
        print("2. 尝试使用不同端口: python load_env.py --port 8082")
        print("3. 检查Docker状态: docker --version")
        print("4. 查看详细日志获取更多信息")
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