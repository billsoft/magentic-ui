# 🚀 Magentic-UI 本地启动指南

## 📊 **启动方式对比**

### ❌ **之前的方式** (已废弃)
```bash
# 这个文件在清理过程中已被删除
python load_env.py --port 8081  # ❌ 文件不存在
```

### ✅ **现在的正确方式**

#### **方式1: 使用 run_local.py (推荐)**
```bash
# 激活环境并使用本地运行脚本
conda activate magentic-ui
python run_local.py --port 8081
```

#### **方式2: 直接使用 magentic-ui 命令**
```bash
# 激活环境并直接运行
conda activate magentic-ui
magentic-ui --port 8081
```

#### **方式3: 使用 uv run (开发模式)**
```bash
# 使用uv直接运行
uv run magentic-ui --port 8081
```

## 🎯 **推荐的启动步骤**

### **第1步: 环境准备**
```bash
# 确保在项目目录
cd /Volumes/D/code/magentic-ui

# 激活虚拟环境
conda activate magentic-ui
```

### **第2步: 检查配置**
```bash
# 确认API密钥配置
cat .env

# 确认配置文件存在
ls -la config.yaml
```

### **第3步: 启动服务**
```bash
# 使用本地运行脚本（推荐）
python run_local.py --port 8081
```

## 📋 **run_local.py 的优势**

### **自动环境检查**
- ✅ 自动加载 `.env` 文件中的环境变量
- ✅ 检查 OPENROUTER_API_KEY 或 OPENAI_API_KEY
- ✅ 验证前端依赖是否安装
- ✅ 处理配置文件中的环境变量替换

### **智能配置处理**
- ✅ 自动处理 `config.yaml` 中的环境变量
- ✅ 创建临时配置文件
- ✅ 清理临时文件

### **本地模式优化**
- ✅ 自动启用 `--run-without-docker` 模式
- ✅ 明确说明功能限制
- ✅ 提供清晰的启动信息

## 🔧 **当前环境状态**

### **已配置的环境**
```bash
✅ 虚拟环境: .venv
✅ API密钥: .env (检测到 OPENROUTER_API_KEY)
✅ 配置文件: config.yaml
✅ 前端依赖: frontend/node_modules
✅ magentic-ui 命令: /Volumes/D/code/magentic-ui/.venv/bin/magentic-ui
```

### **支持的功能**
- ✅ **网页浏览**: Web Surfer Agent
- ✅ **AI对话**: 所有对话功能
- ✅ **图像生成**: OpenAI DALL-E 集成
- ✅ **多轮对话**: 完整对话历史
- ⚠️  **代码执行**: 需要Docker (本地模式不支持)
- ⚠️  **文件浏览**: 需要Docker (本地模式不支持)

## 🎮 **完整启动命令**

### **标准启动** (端口8081)
```bash
conda activate magentic-ui && python run_local.py
```

### **自定义端口启动**
```bash
conda activate magentic-ui && python run_local.py --port 8080
```

### **调试模式启动**
```bash
conda activate magentic-ui && python run_local.py --reload
```

## 📊 **启动过程说明**

### **1. 环境检查阶段**
```
🚀 启动 Magentic-UI (本地模式 - 不使用 Docker)
============================================================
✅ 前端依赖已安装
✅ 已加载环境变量文件: /path/to/.env
✅ 检测到 OPENROUTER_API_KEY
✅ 已处理配置文件: config.yaml
📝 临时配置文件: /tmp/xxxxx.yaml
✅ 使用处理后的配置文件
🏠 启用本地模式（不使用 Docker）
```

### **2. 功能限制说明**
```
📋 本地模式限制说明:
   • 无法使用代码执行功能（Coder Agent）
   • 无法使用文件浏览功能（File Surfer Agent）
   • 无法在界面中显示实时浏览器视图
   • 但仍可使用网页浏览和AI对话功能
```

### **3. 服务启动**
```
🔧 执行命令: uv run magentic-ui --config /tmp/xxxxx.yaml --run-without-docker --port 8081
🌐 启动后访问: http://localhost:8081
⏹️  按 Ctrl+C 停止服务
```

## 🚨 **常见问题解决**

### **问题1: load_env.py 文件不存在**
```bash
# 错误提示
python: can't open file '/path/to/load_env.py': [Errno 2] No such file or directory

# ✅ 解决方案
python run_local.py --port 8081
```

### **问题2: API密钥未配置**
```bash
# 检查.env文件
cat .env

# 确保包含以下之一:
OPENROUTER_API_KEY=your_key_here
# 或
OPENAI_API_KEY=your_key_here
```

### **问题3: 前端依赖缺失**
```bash
# 安装前端依赖
cd frontend
npm install
cd ..
```

### **问题4: 虚拟环境未激活**
```bash
# 激活虚拟环境
conda activate magentic-ui

# 或使用uv
source .venv/bin/activate
```

## 🎯 **最佳实践**

### **推荐工作流程**
```bash
# 1. 进入项目目录
cd /Volumes/D/code/magentic-ui

# 2. 激活环境
conda activate magentic-ui

# 3. 启动服务
python run_local.py

# 4. 访问界面
open http://localhost:8081
```

### **开发模式**
```bash
# 使用reload模式进行开发
python run_local.py --reload --port 8081
```

---

**📝 更新时间**: 2025年1月11日  
**🎯 适用版本**: 清理后的Magentic-UI项目  
**✅ 状态**: 已验证可用 