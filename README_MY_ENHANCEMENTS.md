# 🚀 Magentic-UI Enhanced Edition

这是基于微软官方 [Magentic-UI](https://github.com/microsoft/magentic-ui) 的增强版本，专注于提供更好的多模型支持和用户体验。

## ✨ 主要增强功能

### 🔧 多模型支持
- **OpenRouter** - 支持Claude 3.5 Sonnet等云端模型
- **Ollama** - 支持本地模型（Gemma3、Qwen2.5VL等）
- **Azure OpenAI** - 企业级Azure服务
- **自定义API** - 任何OpenAI兼容的API服务

### 📋 配置管理
- **一键设置脚本** - `setup_scripts/quick_setup.sh`
- **配置示例** - `config_examples/` 目录包含4种主要配置
- **环境变量处理** - 智能的API密钥管理
- **配置验证** - 5步验证确保配置正确

### 🛠️ 开发工具
- **智能启动器** - `load_env.py` 和 `run_local.py`
- **模型切换工具** - `switch_model.py` 图形化切换
- **配置测试** - `test_config.py` 全面测试
- **详细文档** - 18KB的完整设置指南

### 🎯 用户体验优化
- **智能超时处理** - 30分钟超时，避免意外中断
- **连续对话支持** - 可选择是否保持会话上下文
- **错误恢复** - 优雅的错误处理和恢复机制
- **端口冲突检测** - 自动处理端口占用问题

## 🔧 核心代码修复

### 关键修复
1. **`src/magentic_ui/backend/teammanager/teammanager.py`**
   - 修复了`model_client_configs`传递断裂问题
   - 添加了`ModelClientConfigs`导入和传递

2. **`src/magentic_ui/backend/web/managers/connection.py`**
   - 优化超时处理从10分钟延长到30分钟
   - 改善用户输入等待机制

3. **前端优化**
   - 更新了依赖包版本
   - 优化了API调用和状态管理

## 📁 新增文件结构

```
magentic-ui-enhanced/
├── config_examples/           # 配置示例
│   ├── openrouter_config.yaml
│   ├── ollama_config.yaml
│   ├── ollama_gemma3_config.yaml
│   └── azure_openai_config.yaml
├── setup_scripts/            # 自动化脚本
│   └── quick_setup.sh
├── load_env.py               # 增强启动器
├── run_local.py              # 本地开发启动器
├── test_config.py            # 配置测试工具
├── switch_model.py           # 模型切换工具
├── .env.example              # 环境变量模板
├── OPENAI_COMPATIBLE_MODELS_SETUP_GUIDE.md  # 详细设置指南
├── README_SETUP.md           # 快速设置说明
└── DEPLOYMENT.md             # 部署指南
```

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/YOUR_USERNAME/magentic-ui-enhanced.git
cd magentic-ui-enhanced
```

### 2. 自动设置
```bash
chmod +x setup_scripts/quick_setup.sh
./setup_scripts/quick_setup.sh
```

### 3. 启动服务
```bash
python load_env.py --port 8081
```

## 🎯 支持的配置

### OpenRouter (推荐)
- **模型**: Claude 3.5 Sonnet, GPT-4等
- **优势**: 快速、稳定、多模型选择
- **设置**: 只需API密钥

### Ollama (本地)
- **模型**: Gemma3, Qwen2.5VL, LLaMA等
- **优势**: 完全本地、无API费用、数据隐私
- **设置**: 需要本地Ollama服务

### Azure OpenAI (企业)
- **模型**: GPT-4, GPT-3.5-turbo等
- **优势**: 企业级支持、合规性
- **设置**: 需要Azure订阅

## 🧪 测试验证

运行完整的5步验证：
```bash
python test_config.py
```

验证步骤：
1. ✅ 环境变量加载
2. ✅ 配置文件语法
3. ✅ API凭据验证
4. ✅ 核心代码修改
5. ✅ 模型连接测试

## 📚 详细文档

- **[完整设置指南](OPENAI_COMPATIBLE_MODELS_SETUP_GUIDE.md)** - 18KB详细说明
- **[快速设置](README_SETUP.md)** - 3分钟快速上手
- **[部署指南](DEPLOYMENT.md)** - 生产环境部署

## 🤝 贡献

这个项目基于微软官方的Magentic-UI，增强了多模型支持。欢迎：
- 🐛 报告问题
- 💡 提出建议
- 🔧 提交改进
- 📖 完善文档

## 📄 许可证

继承原项目的MIT许可证。

## 🙏 致谢

- 微软 Magentic-UI 团队 - 提供了优秀的基础框架
- AutoGen 社区 - 强大的多代理系统
- 开源社区 - 各种模型和工具支持

---

**🎯 这个增强版本让Magentic-UI真正成为了一个通用的AI代理平台，支持任何OpenAI兼容的模型服务！** 