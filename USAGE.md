# Magentic-UI 使用说明

## 快速开始

### 1. 环境准备

确保你有以下环境：
- Python 3.10+
- Docker Desktop (必须运行)
- conda 或 virtual environment

### 2. 激活环境

```bash
# 如果使用 conda
conda activate magentic-ui

# 如果使用 venv
source .venv/bin/activate
```

### 3. 启动应用

**推荐方式 - 混合模式（本地代码 + Docker 容器）**：
```bash
# 方式 1: 使用启动脚本
./start.sh

# 方式 2: 直接使用 Python
python start_correct.py

# 方式 3: 指定端口
python start_correct.py --port 8081
```

**测试方式 - 本地模式（功能受限）**：
```bash
# 仅用于测试，功能受限
./start.sh local
```

### 4. 访问应用

在浏览器中打开：`http://localhost:8081`

## 架构说明

### 混合模式架构

Magentic-UI 使用混合架构，结合了本地代码和 Docker 容器的优势：

```
┌─────────────────────────────────────────────────────────────┐
│                    本地代码层（协调）                          │
├─────────────────────────────────────────────────────────────┤
│ • FastAPI Web 服务器                                         │
│ • WebSocket 连接管理                                         │
│ • 代理协调和规划                                              │
│ • 数据库和会话管理                                           │
│ • API 密钥管理                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Docker 容器层（执行）                         │
├─────────────────────────────────────────────────────────────┤
│ • VNC 浏览器容器 (magentic-ui-vnc-browser)                   │
│   - Playwright 浏览器自动化                                 │
│   - VNC 服务器和 noVNC 界面                                 │
│   - 端口: 动态分配                                           │
│                                                             │
│ • Python 执行容器 (magentic-ui-python-env)                  │
│   - 代码执行沙盒                                             │
│   - 文件操作和处理                                           │
│   - 数据分析库                                               │
└─────────────────────────────────────────────────────────────┘
```

### 通信机制

- **本地代码 ↔ 浏览器容器**: WebSocket 连接
- **本地代码 ↔ Python 容器**: Docker API (exec 命令)
- **数据共享**: 通过挂载卷 `~/.magentic_ui` 实现文件共享

## 功能对比

| 功能 | 混合模式 | 本地模式 |
|------|---------|----------|
| 网页浏览 | ✅ 完整支持 | ✅ 基本支持 |
| 实时浏览器视图 | ✅ 支持 | ❌ 不支持 |
| 代码执行 | ✅ 沙盒执行 | ❌ 不支持 |
| 文件操作 | ✅ 完整支持 | ❌ 不支持 |
| 安全隔离 | ✅ Docker 沙盒 | ❌ 无隔离 |
| 并发会话 | ✅ 支持 | ⚠️ 有限支持 |

## 故障排除

### 1. Docker 相关问题

**问题**: Docker 容器无法启动
```bash
# 检查 Docker 是否运行
docker --version
docker info

# 检查 Docker 镜像
docker images | grep magentic

# 清理旧容器
docker container prune
```

**问题**: 端口冲突
```bash
# 查看端口占用
lsof -i :8081

# 使用不同端口
python start_correct.py --port 8082
```

### 2. 环境问题

**问题**: 模块未找到
```bash
# 检查环境
which python
pip list | grep magentic

# 重新安装
pip install -e .
```

**问题**: API 密钥未设置
```bash
# 检查 .env 文件
cat .env

# 设置环境变量
export OPENROUTER_API_KEY=your_key_here
```

### 3. 权限问题

**问题**: 文件权限错误
```bash
# 检查工作目录权限
ls -la ~/.magentic_ui

# 修复权限
chmod -R 755 ~/.magentic_ui
```

## 开发模式

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run start
```

前端开发服务器运行在 `http://localhost:8000`

### 后端开发

```bash
# 启动后端服务
python start_correct.py

# 查看日志
tail -f ~/.magentic_ui/logs/*.log
```

## 性能优化

### 1. 容器复用

系统会自动复用现有的 Docker 容器，避免重复创建。

### 2. 资源清理

定期清理不用的容器：
```bash
# 清理停止的容器
docker container prune

# 清理未使用的镜像
docker image prune
```

### 3. 内存管理

根据系统资源调整并发会话数量。

## 高级配置

### 自定义配置文件

创建 `config.yaml` 文件来自定义配置：

```yaml
# 模型配置
model_config: &client
  provider: autogen_ext.models.openai.OpenAIChatCompletionClient
  config:
    model: gpt-4o
    api_key: $OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1

# 代理配置
orchestrator_client: *client
web_surfer_client: *client
# ... 其他配置
```

### 环境变量

在 `.env` 文件中设置：

```env
# API 密钥
OPENROUTER_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# 可选配置
MAGENTIC_UI_PORT=8081
MAGENTIC_UI_HOST=localhost
```

## 支持和帮助

- 查看日志：`~/.magentic_ui/logs/`
- 检查容器状态：`docker ps -a | grep magentic`
- 重启服务：停止后重新运行启动脚本
- 重置环境：删除 `~/.magentic_ui` 目录后重新启动