# Magentic-UI 开发环境部署文档

## 📋 部署概述

Magentic-UI 是微软研究院开发的人机协作 Web 代理研究原型，支持浏览器自动化、代码生成执行和文件分析等功能。

## 🛠️ 系统要求

### 必要条件
- **Python**: >= 3.10 (推荐 3.11)
- **Docker**: 必须安装并运行 Docker Desktop (Mac/Windows) 或 Docker Engine (Linux)
- **Node.js**: >= 16.0 (用于前端开发)
- **操作系统**: macOS, Linux, 或 Windows (需要 WSL2)

### API 密钥
- **OpenAI API Key**: 必须设置 `OPENAI_API_KEY` 环境变量
- **可选**: Azure OpenAI 或 Ollama 配置

## 🚀 安装部署流程

### 1. 环境准备

#### 检查系统环境
```bash
# 检查 Python 版本
python3 --version

# 检查 Docker 状态
docker --version
docker ps

# 检查 conda 环境
conda env list
```

#### 创建专用 Conda 环境
```bash
# 创建新环境 (Python 3.11)
conda create -n magentic-ui python=3.11 -y

# 激活环境
conda activate magentic-ui

# 验证环境
python --version
which python
```

### 2. 依赖安装

#### 安装 uv 包管理器
```bash
# 在 conda 环境中安装 uv
pip install uv

# 验证安装
uv --version
```

#### 安装项目依赖
```bash
# 进入项目目录
cd /path/to/magentic-ui

# 同步安装所有依赖（包含开发依赖）
uv sync --dev

# 验证安装
uv run python -c "import magentic_ui; print('安装成功')"
```

#### 安装 Playwright 浏览器
```bash
# 安装浏览器驱动
uv run playwright install

# 验证 Playwright
uv run python -c "from playwright.sync_api import sync_playwright; print('Playwright 就绪')"
```

### 3. 前端环境设置

#### 安装前端依赖
```bash
# 进入前端目录
cd frontend

# 安装依赖（解决版本冲突）
npm install --legacy-peer-deps

# 构建前端（生产环境）
npm run build

# 返回项目根目录
cd ..
```

### 4. 环境配置

#### 设置 API 密钥

**方法一：使用 .env 文件（推荐）**
```bash
# 从模板复制 .env 文件
cp .env.example .env

# 编辑 .env 文件，填入真实的 API 密钥
# OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
```

**方法二：环境变量**
```bash
# 临时设置
export OPENROUTER_API_KEY="your-openrouter-api-key-here"

# 永久保存到 shell 配置
echo 'export OPENROUTER_API_KEY="your-api-key-here"' >> ~/.zshrc
```

#### 创建配置文件 (可选)
```yaml
# config.yaml
model_config: &client
  provider: autogen_ext.models.openai.OpenAIChatCompletionClient
  config:
    model: gpt-4o
    api_key: ${OPENAI_API_KEY}
    max_retries: 10

orchestrator_client: *client
coder_client: *client
web_surfer_client: *client
file_surfer_client: *client
action_guard_client: *client
```

### 5. 启动验证

#### 构建 Docker 镜像（首次运行）
```bash
# 首次运行会自动构建 Docker 镜像
uv run magentic-ui --port 8081

# 如果构建失败，手动重建
uv run magentic-ui --rebuild-docker --port 8081
```

#### 验证启动
```bash
# 确保在 conda 环境中
conda activate magentic-ui

# 检查命令可用性
uv run magentic-ui --help

# 方法一：完整模式启动脚本（推荐，需要 Docker）
python load_env.py

# 方法二：本地模式启动脚本（不需要 Docker）
python run_local.py

# 方法三：手动启动（需要先手动设置环境变量）
uv run magentic-ui --config config.yaml --port 8081

# 访问: http://localhost:8081
```

## 🎯 常用开发命令

### 环境管理
```bash
# 激活开发环境
conda activate magentic-ui
cd /path/to/magentic-ui

# 查看环境状态
conda env list
conda list
```

### 项目启动
```bash
# 完整模式启动 (推荐，需要 Docker)
python load_env.py

# 本地模式启动 (不需要 Docker，功能受限)
python run_local.py

# 手动启动方式
uv run magentic-ui --port 8081                    # 标准启动
uv run magentic-ui --run-without-docker --port 8081  # 无 Docker 启动
uv run magentic-ui --reload --port 8081            # 开发模式启动

# 命令行界面
uv run magentic-cli --work-dir ./data
```

### 开发工具
```bash
# 代码格式化
uv run poe fmt

# 代码检查
uv run poe lint

# 类型检查
uv run poe pyright

# 运行测试
uv run pytest

# 完整检查
uv run poe check
```

### 前端开发
```bash
# 进入前端目录
cd frontend

# 开发模式启动
npm run dev
# 访问: http://localhost:8000

# 构建生产版本
npm run build

# 类型检查
npm run typecheck
```

## 🔧 故障排除

### 常见问题

#### Docker 相关
```bash
# Docker 未运行
sudo systemctl start docker  # Linux
# 或启动 Docker Desktop

# Docker 权限问题
sudo usermod -aG docker $USER
```

#### 依赖冲突
```bash
# 清理并重新安装
uv sync --reinstall

# 前端依赖冲突
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

#### 环境变量
```bash
# 检查 API 密钥
echo $OPENAI_API_KEY

# 临时设置
export OPENAI_API_KEY="your-key"
```

### 性能优化
```bash
# 预构建 Docker 镜像
docker build -t magentic-ui-vnc-browser:latest ./src/magentic_ui/docker/magentic-ui-browser-docker
docker build -t magentic-ui-python-env:latest ./src/magentic_ui/docker/magentic-ui-python-env
```

## 📁 项目结构

```
magentic-ui/
├── src/magentic_ui/          # 后端源码
│   ├── agents/              # 代理系统
│   ├── backend/             # Web 后端
│   ├── tools/               # 工具集
│   └── docker/              # Docker 配置
├── frontend/                # 前端源码 (React + Gatsby)
├── tests/                   # 测试文件
├── samples/                 # 示例代码
├── pyproject.toml          # Python 项目配置
├── uv.lock                 # uv 锁定文件
└── config.yaml             # 模型配置 (可选)
```

## 🌟 功能特性

- 🧑‍🤝‍🧑 **协作规划**: 与AI共同制定执行计划
- 🤝 **协作任务**: 实时中断和指导任务执行  
- 🛡️ **操作防护**: 敏感操作需要用户确认
- 🧠 **计划学习**: 从历史执行中学习和检索计划
- 🔀 **并行执行**: 支持多任务并行处理

## 🚨 安全注意事项

1. **API 密钥安全**: 不要将 API 密钥提交到版本控制
2. **Docker 权限**: 确保 Docker 运行在安全配置下
3. **网络访问**: Web 代理具有完整网络访问权限
4. **文件权限**: 代码执行容器可访问指定目录

## 📞 技术支持

- **官方文档**: [GitHub Repository](https://github.com/microsoft/magentic-ui)
- **故障排除**: 参考 `TROUBLESHOOTING.md`
- **贡献指南**: 参考 `CONTRIBUTING.md`
- **问题反馈**: 提交 GitHub Issues

---

## 🎉 部署完成检查清单

- [ ] Conda 环境 `magentic-ui` 已创建并激活
- [ ] uv 包管理器已安装 (v0.7.14+)
- [ ] Python 依赖已通过 `uv sync` 安装
- [ ] Playwright 浏览器驱动已安装
- [ ] 前端依赖已安装 (`npm install --legacy-peer-deps`)
- [ ] Docker 服务正在运行
- [ ] OPENAI_API_KEY 环境变量已设置
- [ ] `uv run magentic-ui --help` 命令正常执行
- [ ] 可以访问 http://localhost:8081

**环境隔离确认**: 新环境不影响现有的 `base`, `ainvr`, `llmnvr`, `mycamsms` 环境 ✅ 