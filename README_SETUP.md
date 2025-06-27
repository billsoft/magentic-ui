# 🚀 Magentic-UI OpenAI兼容模型快速设置

## 📁 文件结构

本配置包含以下文件：

```
magentic-ui/
├── OPENAI_COMPATIBLE_MODELS_SETUP_GUIDE.md  # 详细配置指南
├── README_SETUP.md                          # 本文件 - 快速设置说明
├── test_config.py                           # 配置测试脚本
├── config_examples/                         # 配置示例文件夹
│   ├── openrouter_config.yaml              # OpenRouter配置示例
│   ├── ollama_config.yaml                  # Ollama本地配置示例
│   └── azure_openai_config.yaml            # Azure OpenAI配置示例
└── setup_scripts/
    └── quick_setup.sh                       # 自动化设置脚本
```

## ⚡ 快速开始

### 方法1: 自动化设置 (推荐)

```bash
# 运行自动化设置脚本
bash setup_scripts/quick_setup.sh

# 按提示选择配置类型：
# 1) OpenRouter (推荐)
# 2) Ollama (本地)  
# 3) Azure OpenAI
# 4) 自定义配置

# 编辑生成的 .env 文件，填入真实API密钥
nano .env

# 测试配置
python test_config.py

# 启动应用
python run_local.py
```

### 方法2: 手动设置

```bash
# 1. 选择并复制配置文件
cp config_examples/openrouter_config.yaml config.yaml

# 2. 创建环境变量文件
cp .env.example .env
nano .env  # 填入真实API密钥

# 3. 测试配置
python test_config.py

# 4. 启动应用
python run_local.py
```

## 🔧 核心代码修改

**重要**: 必须先修改核心代码，否则配置不会生效！

修改文件: `src/magentic_ui/backend/teammanager/teammanager.py`

### 第30行添加导入:
```python
from ...magentic_ui_config import MagenticUIConfig, ModelClientConfigs
```

### 第202行添加配置传递:
```python
config_params = {
    # ... 其他配置 ...
    "model_client_configs": model_client_configs,  # 🔑 添加这行
    # ... 其他配置 ...
}
```

详细修改说明请参考: `OPENAI_COMPATIBLE_MODELS_SETUP_GUIDE.md`

## 🧪 测试验证

运行测试脚本验证配置：

```bash
python test_config.py
```

测试内容包括：
- ✅ 环境变量加载
- ✅ 配置文件语法
- ✅ API凭据验证
- ✅ 核心代码修改
- ✅ 模型连接测试

## 🎯 支持的模型服务

| 服务 | 配置文件 | 环境变量 |
|------|----------|----------|
| OpenRouter | `openrouter_config.yaml` | `OPENROUTER_API_KEY` |
| Ollama | `ollama_config.yaml` | `OLLAMA_HOST` |
| Azure OpenAI | `azure_openai_config.yaml` | `AZURE_ENDPOINT`, `AZURE_DEPLOYMENT` |
| 自定义API | 手动配置 | 根据需要设置 |

## 🔐 环境变量示例

### OpenRouter
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENAI_API_KEY=sk-or-v1-your-key-here  # 兼容性
```

### Ollama
```bash
OLLAMA_HOST=http://localhost:11434
```

### Azure OpenAI
```bash
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT=your-deployment-name
AZURE_DEPLOYMENT_MINI=your-mini-deployment-name
```

## 🆘 常见问题

### 1. 配置不生效，仍然使用OpenAI
- 检查核心代码修改是否正确应用
- 重启应用服务
- 运行 `python test_config.py` 验证

### 2. 401认证错误
- 检查API密钥是否正确
- 确认环境变量已正确设置
- 验证API密钥权限

### 3. 端口被占用
- 使用 `python run_local.py --port 8082` 指定其他端口
- 或杀死占用进程: `lsof -i :8081`

## 📖 详细说明

完整的配置说明、故障排除和高级配置请参考:
**`OPENAI_COMPATIBLE_MODELS_SETUP_GUIDE.md`**

## 🎉 成功标志

当看到以下输出时，说明配置成功：

```
🎉 所有测试通过！配置正确，可以启动 Magentic-UI
💡 运行命令: python run_local.py
```

然后访问 `http://localhost:8081` 开始使用！ 