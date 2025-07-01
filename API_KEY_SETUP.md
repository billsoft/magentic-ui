# 🔑 API 密钥配置指南

## 🚨 问题诊断

您遇到的 `401 Unauthorized` 错误是因为 **API 密钥未正确配置**。

从日志中可以看到：
```
INFO:magentic_ui.task_team:🔑 API密钥已解析: your-openr...
Error code: 401 - {'error': {'message': 'No auth credentials found', 'code': 401}}
```

这说明 API 密钥被解析为占位符 `your-openr...` 而不是真实密钥。

## 🔧 解决步骤

### 1. 创建环境变量文件

在项目根目录创建 `.env` 文件：

```bash
# 在项目根目录执行
touch .env
```

### 2. 配置 API 密钥

编辑 `.env` 文件，添加以下内容：

```bash
# OpenRouter API 密钥 (主要使用)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI API 密钥 (autogen-ext 要求，可以设置为相同的 OpenRouter 密钥)
OPENAI_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 获取 API 密钥

**OpenRouter API 密钥**：
- 访问：https://openrouter.ai/keys
- 注册账户并生成 API 密钥
- 密钥格式：`sk-or-v1-...`

### 4. 重要说明

⚠️ **为什么需要两个密钥设置？**

根据之前的调试经验，`autogen-ext` 的 OpenAI 客户端在内部会检查 `OPENAI_API_KEY` 环境变量，即使实际使用的是 OpenRouter API。因此需要同时设置两个环境变量：

- `OPENROUTER_API_KEY`：配置文件中引用的密钥
- `OPENAI_API_KEY`：autogen-ext 内部要求的密钥

两个可以设置为相同的 OpenRouter 密钥。

### 5. 验证配置

重新启动 Magentic-UI：

```bash
conda activate magentic-ui && python load_env.py --port 8081
```

如果配置正确，您应该看到：
```
✅ 已加载环境变量文件: /path/to/.env
✅ 检测到 OPENROUTER_API_KEY
```

而不是之前的警告信息。

## 🛠️ 故障排除

### 如果仍然出现 401 错误：

1. **检查密钥格式**：确保密钥以 `sk-or-v1-` 开头
2. **检查密钥有效性**：在 OpenRouter 控制台验证密钥状态
3. **检查账户余额**：确保 OpenRouter 账户有足够余额
4. **检查模型权限**：确保您的账户可以访问 `google/gemini-2.5-pro` 模型

### 快速测试命令：

```bash
# 测试环境变量是否正确加载
python -c "import os; print('OPENROUTER_API_KEY:', os.getenv('OPENROUTER_API_KEY', 'NOT_SET')[:20] + '...')"
```

## 📝 配置文件说明

当前 `config.yaml` 使用的模型：
- **主模型**: `google/gemini-2.5-pro`
- **图像生成**: `dall-e-3` (需要真实的 OpenAI API 密钥)

如果您没有 OpenAI API 密钥用于图像生成，可以临时关闭图像生成功能或使用其他配置。 