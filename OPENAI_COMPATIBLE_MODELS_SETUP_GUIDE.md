# Magentic-UI 支持OpenAI兼容模型完整配置指南

本指南详细说明如何将原始的Magentic-UI项目修改为支持OpenAI以外的模型（如OpenRouter、Ollama、Azure OpenAI等）。

## 📋 目录

1. [环境准备](#环境准备)
2. [核心代码修改](#核心代码修改)
3. [配置文件创建](#配置文件创建)
4. [环境变量设置](#环境变量设置)
5. [启动脚本创建](#启动脚本创建)
6. [Docker配置](#docker配置)
7. [前端配置支持](#前端配置支持)
8. [测试验证](#测试验证)
9. [常见问题解决](#常见问题解决)

---

## 🔧 环境准备

### 1. 确认Python环境
```bash
# 确保使用Python 3.11+
python --version

# 安装必要依赖
uv add python-dotenv pyyaml
```

### 2. 项目结构检查
确保项目根目录包含以下文件结构：
```
magentic-ui/
├── src/magentic_ui/backend/teammanager/teammanager.py
├── config.yaml (需要创建)
├── .env.example (需要创建)
├── load_env.py (需要创建)
└── run_local.py (需要创建)
```

---

## 🛠️ 核心代码修改

### 1. 修改 TeamManager 配置传递逻辑

**文件**: `src/magentic_ui/backend/teammanager/teammanager.py`

**问题**: 原版代码中模型客户端配置传递存在断裂，导致配置文件中的OpenRouter等设置被忽略。

**修改位置**: 第30行和第161-202行

#### 第30行添加导入:
```python
from ..datamodel.types import EnvironmentVariable
from ...magentic_ui_config import MagenticUIConfig, ModelClientConfigs  # 添加这行
from ...types import RunPaths
```

#### 第161-202行恢复配置逻辑:
```python
# 在 _create_team 方法中，找到 if not self.load_from_config: 部分
# 恢复被注释的模型客户端配置代码

# Use settings_config values if available, otherwise fall back to instance defaults (self.config)
model_client_configs = ModelClientConfigs(
    orchestrator=settings_model_configs.get(
        "orchestrator_client",
        self.config.get("orchestrator_client", None),
    ),
    web_surfer=settings_model_configs.get(
        "web_surfer_client",
        self.config.get("web_surfer_client", None),
    ),
    coder=settings_model_configs.get(
        "coder_client", self.config.get("coder_client", None)
    ),
    file_surfer=settings_model_configs.get(
        "file_surfer_client",
        self.config.get("file_surfer_client", None),
    ),
    action_guard=settings_model_configs.get(
        "action_guard_client",
        self.config.get("action_guard_client", None),
    ),
)

config_params = {
    # Lowest priority defaults
    **self.config,  # type: ignore
    # Provided settings override defaults
    **settings_config,  # type: ignore,
    "model_client_configs": model_client_configs,  # 🔑 关键修复
    # These must always be set to the values computed above
    "playwright_port": playwright_port,
    "novnc_port": novnc_port,
    # Defer to self for inside_docker
    "inside_docker": self.inside_docker,
}
```

**为什么需要这个修改**:
- 原代码中`model_client_configs`被创建但没有传递给`config_params`
- 导致系统使用默认的OpenAI配置而不是配置文件中的设置
- 这是OpenRouter配置不生效的根本原因

---

## 📝 配置文件创建

### 1. 创建主配置文件 `config.yaml`

```yaml
# =====================================================
# Magentic-UI OpenAI兼容模型配置文件
# 支持: OpenRouter, Ollama, Azure OpenAI, 自定义API
# =====================================================

######################################
# 核心模型配置 - OpenRouter Claude    #
######################################
model_config: &client
  provider: autogen_ext.models.openai.OpenAIChatCompletionClient
  config:
    model: anthropic/claude-3-5-sonnet-20241022
    api_key: $OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1
    timeout: 120.0
    max_retries: 3
    model_info:
      vision: true
      function_calling: true
      json_output: false
      family: claude-3-5-sonnet
      structured_output: false
      multiple_system_messages: false
    default_headers:
      HTTP-Referer: https://magentic-ui.local
      X-Title: Magentic-UI-Development
    extra_body:
      temperature: 0.7
      max_tokens: 4096
      top_p: 0.9

######################################
# 各代理专用配置                      #
######################################

# 协调器 - 使用最强模型
orchestrator_client: *client

# 编程代理 - 代码生成优化
coder_client: *client

# 网页浏览代理
web_surfer_client: *client

# 文件浏览代理
file_surfer_client: *client

# 动作守卫 - 可使用更快的模型
action_guard_client: *client

######################################
# 应用程序配置                        #
######################################

# 协作模式
cooperative_planning: true
autonomous_execution: false
allow_follow_up_input: true

# 性能配置
max_actions_per_step: 8
multiple_tools_per_call: true
max_turns: 50
model_context_token_limit: 200000

# 安全配置
approval_policy: auto-conservative
action_guard_enabled: true
require_authentication: false

# 网络配置
allowed_websites: []
browser_headless: false
browser_local: false
playwright_port: -1
novnc_port: -1

# Docker配置
inside_docker: true
run_without_docker: false

# 高级配置
allow_for_replans: true
do_bing_search: false
websurfer_loop: false
retrieve_relevant_plans: never
```

### 2. 其他模型配置示例

#### OpenAI 官方配置:
```yaml
model_config: &client
  provider: autogen_ext.models.openai.OpenAIChatCompletionClient
  config:
    model: gpt-4o-2024-08-06
    api_key: $OPENAI_API_KEY
    max_retries: 3
```

#### Ollama 本地配置:
```yaml
model_config: &client
  provider: autogen_ext.models.ollama.OllamaChatCompletionClient
  config:
    model: qwen2.5vl:32b
    host: http://localhost:11434
    model_info:
      vision: true
      function_calling: true
      json_output: false
      family: qwen
      structured_output: false
    max_retries: 5
```

#### Azure OpenAI 配置:
```yaml
model_config: &client
  provider: AzureOpenAIChatCompletionClient
  config:
    model: gpt-4o
    azure_endpoint: $AZURE_ENDPOINT
    azure_deployment: $AZURE_DEPLOYMENT
    api_version: "2024-10-21"
    azure_ad_token_provider:
      provider: autogen_ext.auth.azure.AzureTokenProvider
      config:
        provider_kind: DefaultAzureCredential
        scopes:
          - https://cognitiveservices.azure.com/.default
    max_retries: 10
```

---

## 🔐 环境变量设置

### 1. 创建 `.env.example` 模板文件

```bash
# ==============================================
# Magentic-UI 环境变量配置模板
# 使用方法: 复制为 .env 文件并填入真实值
# ==============================================

# OpenRouter API 密钥 (推荐)
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-api-key-here

# OpenAI API 密钥 (可选，兼容性)
OPENAI_API_KEY=sk-or-v1-your-openrouter-api-key-here

# Azure OpenAI 配置 (如果使用Azure)
# AZURE_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_DEPLOYMENT=your-deployment-name
# AZURE_API_KEY=your-azure-api-key

# Ollama 配置 (如果使用本地Ollama)
# OLLAMA_HOST=http://localhost:11434

# 自定义API配置
# CUSTOM_API_KEY=your-custom-api-key
# CUSTOM_BASE_URL=https://your-custom-api.com/v1

# 调试选项
# DEBUG=true
# LOG_LEVEL=INFO
```

### 2. 用户配置步骤

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件，填入真实的API密钥
nano .env

# 3. 确保文件权限安全
chmod 600 .env
```

---

## 🚀 启动脚本创建

### 1. 创建 `load_env.py` 环境变量处理脚本

```python
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
                print("⚠️  警告: 未检测到 API 密钥")
        else:
            print("⚠️  警告: 未找到 .env 文件")
            
    except ImportError:
        print("❌ python-dotenv 未安装，请运行: uv add python-dotenv")
        sys.exit(1)

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
        
        # 创建临时配置文件
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        temp_config.write(processed_content)
        temp_config.close()
        
        print(f"✅ 已处理配置文件: {config_path}")
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
    
    # 添加命令行参数
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    else:
        cmd.extend(["--port", "8081"])
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    
    # 启动应用
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
            except:
                pass

if __name__ == "__main__":
    main()
```

### 2. 创建 `run_local.py` 简化启动脚本

```python
#!/usr/bin/env python3
"""
Magentic-UI 本地开发启动脚本
简化的启动方式，自动处理端口冲突
"""

import subprocess
import sys
import socket
from pathlib import Path

def check_port(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def find_free_port(start_port=8081):
    """寻找可用端口"""
    port = start_port
    while port < start_port + 100:
        if check_port(port):
            return port
        port += 1
    return None

def main():
    """主函数"""
    print("🚀 启动 Magentic-UI 本地开发服务器...")
    
    # 检查配置文件
    if not Path("config.yaml").exists():
        print("❌ 未找到 config.yaml 配置文件")
        print("请先创建配置文件，参考 OPENAI_COMPATIBLE_MODELS_SETUP_GUIDE.md")
        sys.exit(1)
    
    # 寻找可用端口
    port = find_free_port(8081)
    if not port:
        print("❌ 无法找到可用端口")
        sys.exit(1)
    
    if port != 8081:
        print(f"⚠️  端口 8081 被占用，使用端口 {port}")
    
    # 构建启动命令
    cmd = ["python", "load_env.py", "--port", str(port)]
    
    # 添加其他参数
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    print(f"🌐 访问地址: http://localhost:{port}")
    
    # 启动应用
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Magentic-UI 已停止")

if __name__ == "__main__":
    main()
```

---

## 🐳 Docker配置

### 1. 检查现有Docker配置

确保以下Docker相关文件存在并配置正确：

- `src/magentic_ui/docker/magentic-ui-browser-docker/Dockerfile`
- `src/magentic_ui/docker/magentic-ui-python-env/Dockerfile`

### 2. 环境变量传递到Docker

在Docker启动时确保环境变量正确传递：

```bash
# 如果使用Docker Compose
docker-compose up -d

# 如果手动启动Docker
docker run -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
           -e OPENAI_API_KEY=$OPENAI_API_KEY \
           -v $(pwd)/config.yaml:/app/config.yaml \
           magentic-ui
```

---

## 🖥️ 前端配置支持

### 1. 模型选择器配置

**文件**: `frontend/src/components/settings/tabs/agentSettings/modelSelector/ModelSelector.tsx`

确保OpenRouter预设配置存在：

```typescript
"OpenRouter": {
  ...DEFAULT_OPENAI,
  config: {
    ...DEFAULT_OPENAI.config,
    base_url: "https://openrouter.ai/api/v1"
  }
}
```

### 2. 设置界面配置模板

**文件**: `frontend/src/components/settings.tsx`

确保包含OpenRouter配置模板：

```typescript
const OPENROUTER_YAML = `model_config: &client
  provider: OpenAIChatCompletionClient
  config:
    model: "anthropic/claude-3-5-sonnet-20241022"
    base_url: "https://openrouter.ai/api/v1"
    api_key: "YOUR_OPENROUTER_API_KEY"
    model_info:
       vision: true 
       function_calling: true
       json_output: false
       family: claude-3-5-sonnet
       structured_output: false
  max_retries: 5

orchestrator_client: *client
coder_client: *client
web_surfer_client: *client
file_surfer_client: *client
action_guard_client: *client
`;
```

---

## 🧪 测试验证

### 1. 创建配置测试脚本

```python
# test_config.py
import yaml
import asyncio
from autogen_core.models import ChatCompletionClient, UserMessage

async def test_openrouter_config():
    """测试OpenRouter配置"""
    print("🧪 测试OpenRouter配置...")
    
    # 加载配置
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # 获取orchestrator客户端配置
    client_config = config.get("orchestrator_client")
    print(f"客户端配置: {client_config}")
    
    # 初始化客户端
    client = ChatCompletionClient.load_component(client_config)
    
    # 测试简单对话
    response = await client.create(
        messages=[UserMessage(content="Hello, please respond with 'Configuration test successful!'", source="user")]
    )
    
    print(f"✅ 响应内容: {response.content}")
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_openrouter_config())
```

### 2. 运行测试

```bash
# 1. 测试配置文件
python test_config.py

# 2. 测试完整启动
python run_local.py

# 3. 检查日志
tail -f ~/.magentic-ui/logs/magentic-ui.log
```

### 3. 验证清单

- [ ] 环境变量正确加载
- [ ] 配置文件语法正确
- [ ] API密钥有效
- [ ] 模型响应正常
- [ ] 前端界面显示正确
- [ ] 会话创建成功
- [ ] 对话功能正常

---

## 🔧 常见问题解决

### 1. 401 认证错误

**问题**: `Error code: 401 - Incorrect API key provided`

**解决方案**:
```bash
# 检查环境变量
echo $OPENROUTER_API_KEY

# 检查 .env 文件
cat .env

# 重新加载环境变量
source .env
```

### 2. 配置不生效

**问题**: 仍然使用OpenAI官方API

**解决方案**:
1. 确认 `teammanager.py` 的修改已应用
2. 重启应用服务
3. 检查配置文件路径
4. 验证YAML语法

### 3. 端口占用

**问题**: `Address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8081

# 杀死进程
kill -9 <PID>

# 或使用不同端口
python run_local.py --port 8082
```

### 4. Docker相关问题

**问题**: 浏览器功能不可用

**解决方案**:
```bash
# 检查Docker服务
docker ps

# 重启Docker容器
docker-compose restart

# 检查端口映射
docker port <container_name>
```

### 5. 模型兼容性问题

**问题**: 某些功能不支持

**解决方案**:
1. 检查模型的 `model_info` 配置
2. 确认模型支持的功能（vision, function_calling等）
3. 调整配置以匹配模型能力

---

## 📚 进阶配置

### 1. 多模型配置

```yaml
# 不同代理使用不同模型
orchestrator_client:
  provider: autogen_ext.models.openai.OpenAIChatCompletionClient
  config:
    model: anthropic/claude-3-5-sonnet-20241022
    base_url: https://openrouter.ai/api/v1
    api_key: $OPENROUTER_API_KEY

action_guard_client:
  provider: autogen_ext.models.openai.OpenAIChatCompletionClient
  config:
    model: anthropic/claude-3-haiku-20240307  # 更快的模型
    base_url: https://openrouter.ai/api/v1
    api_key: $OPENROUTER_API_KEY
```

### 2. 成本优化配置

```yaml
# 成本控制配置
daily_token_limit: 1000000
cost_tracking: true
budget_alerts: true

# 性能优化
max_concurrent_requests: 3
rate_limit_per_minute: 30
```

### 3. 安全配置

```yaml
# 安全设置
allowed_origins:
  - "http://localhost:8081"
  - "https://your-domain.com"

content_filtering: true
safe_mode: true
```

---

## 🎯 总结

通过以上步骤，您可以成功将Magentic-UI从仅支持OpenAI模型扩展为支持任何OpenAI兼容的API服务。关键修改点包括：

1. **核心修复**: `teammanager.py` 中的配置传递逻辑
2. **配置系统**: 完整的YAML配置文件和环境变量管理
3. **启动脚本**: 自动化的环境处理和启动流程
4. **测试验证**: 完整的测试和验证流程

这些修改确保了配置的正确传递和模型的正常工作，同时保持了系统的稳定性和可扩展性。

记住：配置的核心是确保模型客户端配置能够正确从配置文件传递到实际的代理实例中。 