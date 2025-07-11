# 🚀 Magentic-UI Orchestrator 重构设计方案

## 📋 **重构目标**

基于Munas运行逻辑，重构Orchestrator执行流程，实现：
1. **严格的步骤验证和控制**
2. **智能的Agent分配机制**
3. **完整的工具集成**
4. **防止循环和跳步执行**

## 🔧 **核心重构模块**

### 1️⃣ **执行流程控制器 (ExecutionController)**

```python
# 新增文件: src/magentic_ui/teams/orchestrator/_execution_controller.py

class ExecutionController:
    """严格的步骤执行控制器"""
    
    def __init__(self):
        self.step_validators = {
            'web_search': WebSearchValidator(),
            'image_generation': ImageGenerationValidator(), 
            'document_creation': DocumentCreationValidator(),
            'format_conversion': FormatConversionValidator()
        }
        self.execution_history = []
        self.step_attempts = {}
    
    async def execute_step(self, step_info, agent_response):
        """严格执行单个步骤"""
        step_id = f"{step_info['agent_name']}_{step_info['title']}"
        
        # 1. 记录执行历史
        self.execution_history.append({
            'step_id': step_id,
            'timestamp': datetime.now(),
            'agent': step_info['agent_name'],
            'response': agent_response
        })
        
        # 2. 防重复执行检查
        if self._is_repeated_execution(step_id, agent_response):
            return ExecutionResult(
                success=False,
                reason="检测到重复执行，跳过此步骤",
                action="continue_to_next"
            )
        
        # 3. 步骤完成验证
        validator = self._get_validator(step_info)
        validation_result = await validator.validate_completion(
            step_info, agent_response
        )
        
        # 4. 更新尝试计数
        self.step_attempts[step_id] = self.step_attempts.get(step_id, 0) + 1
        
        return validation_result
    
    def _get_validator(self, step_info):
        """根据步骤类型获取验证器"""
        agent_name = step_info['agent_name']
        step_content = step_info['details'].lower()
        
        if agent_name == 'web_surfer':
            return self.step_validators['web_search']
        elif agent_name == 'image_generator':
            return self.step_validators['image_generation']
        elif 'markdown' in step_content or '文档' in step_content:
            return self.step_validators['document_creation']
        elif 'html' in step_content or 'pdf' in step_content:
            return self.step_validators['format_conversion']
        
        return DefaultValidator()
```

### 2️⃣ **智能验证器系统 (Validation System)**

```python
# 新增文件: src/magentic_ui/teams/orchestrator/_step_validators.py

class WebSearchValidator:
    """网络搜索步骤验证器"""
    
    async def validate_completion(self, step_info, agent_response):
        # 检查完成信号
        completion_signals = [
            '✅ 任务已完成', '✅ TASK COMPLETED',
            '⚠️ 任务因错误完成', '⚠️ TASK COMPLETED WITH ERRORS',
            '🔄 任务通过替代方案完成', '🔄 TASK COMPLETED VIA ALTERNATIVE'
        ]
        
        # 检查是否包含实际信息
        info_indicators = ['产品', '相机', '规格', '功能', '特点']
        
        has_completion_signal = any(signal in agent_response for signal in completion_signals)
        has_useful_info = any(indicator in agent_response for indicator in info_indicators)
        
        if has_completion_signal and has_useful_info:
            return ExecutionResult(
                success=True,
                reason="网络搜索任务已完成，获取到有效信息",
                extracted_data=self._extract_research_data(agent_response)
            )
        
        # 检查是否是无意义的回复
        generic_responses = ['我理解您需要', 'Let me help you', '我可以帮助您']
        if any(generic in agent_response for generic in generic_responses):
            return ExecutionResult(
                success=False,
                reason="检测到通用回复，任务未完成",
                action="retry_with_enhanced_instruction"
            )
        
        return ExecutionResult(success=False, reason="未检测到明确的完成信号")

class ImageGenerationValidator:
    """图像生成步骤验证器"""
    
    async def validate_completion(self, step_info, agent_response):
        # 检查图像生成完成信号
        completion_signals = [
            '图像生成任务已完成', 'image generation complete',
            '图像已成功生成', 'successfully generated',
            '生成完成', 'generation completed'
        ]
        
        # 检查是否有图像文件引用
        image_indicators = ['.png', '.jpg', '.jpeg', 'image', '图像', '图片']
        
        has_completion_signal = any(signal in agent_response for signal in completion_signals)
        has_image_reference = any(indicator in agent_response for indicator in image_indicators)
        
        if has_completion_signal or has_image_reference:
            return ExecutionResult(
                success=True,
                reason="图像生成任务已完成",
                image_info=self._extract_image_info(agent_response)
            )
        
        return ExecutionResult(success=False, reason="图像生成未完成")
```

### 3️⃣ **智能Agent分配器 (Smart Agent Allocator)**

```python
# 修改文件: src/magentic_ui/teams/orchestrator/_orchestrator.py

class SmartAgentAllocator:
    """智能Agent分配器"""
    
    def __init__(self):
        self.agent_capabilities = {
            'web_surfer': {
                'primary': ['网站访问', '在线搜索', '信息收集'],
                'keywords': ['访问', '搜索', '浏览', '网站', 'te720.com'],
                'output_types': ['文本信息', '产品数据', '规格参数']
            },
            'image_generator': {
                'primary': ['图像生成', '视觉创作', 'AI绘图'],
                'keywords': ['生成', '创建', '绘制', '图像', '图片', 'CG', '设计'],
                'output_types': ['图像文件', '视觉内容']
            },
            'coder_agent': {
                'primary': ['文档处理', '格式转换', '代码执行'],
                'keywords': ['markdown', 'html', 'pdf', '文档', '转换', '编程'],
                'output_types': ['文档文件', '格式化内容', '代码输出']
            }
        }
    
    def allocate_agent(self, step_info):
        """智能分配Agent"""
        step_title = step_info['title'].lower()
        step_details = step_info['details'].lower()
        combined_text = f"{step_title} {step_details}"
        
        # 1. 关键词匹配评分
        scores = {}
        for agent_name, capabilities in self.agent_capabilities.items():
            score = 0
            for keyword in capabilities['keywords']:
                if keyword in combined_text:
                    score += 2
            
            # 2. 任务类型匹配
            for task_type in capabilities['primary']:
                if task_type in combined_text:
                    score += 3
            
            scores[agent_name] = score
        
        # 3. 特殊规则检查
        if any(word in combined_text for word in ['生成', '创建', '绘制', '图像', 'CG']):
            if '图像' in combined_text or 'image' in combined_text:
                return 'image_generator'
        
        if any(word in combined_text for word in ['访问', '搜索', 'te720', '网站']):
            return 'web_surfer'
        
        if any(word in combined_text for word in ['markdown', 'html', 'pdf', '转换']):
            return 'coder_agent'
        
        # 4. 返回最高分数的Agent
        best_agent = max(scores.items(), key=lambda x: x[1])
        return best_agent[0] if best_agent[1] > 0 else 'coder_agent'
```

### 4️⃣ **工具集成管理器 (Tool Integration Manager)**

```python
# 新增文件: src/magentic_ui/teams/orchestrator/_tool_manager.py

class ToolIntegrationManager:
    """工具集成管理器"""
    
    def __init__(self):
        self.available_tools = {
            'html_to_pdf': {
                'package': 'weasyprint',
                'install_command': 'pip install weasyprint',
                'usage': 'HTML到PDF转换'
            },
            'markdown_parser': {
                'package': 'markdown',
                'install_command': 'pip install markdown',
                'usage': 'Markdown解析和HTML转换'
            },
            'image_tools': {
                'package': 'Pillow',
                'install_command': 'pip install Pillow',
                'usage': '图像处理和格式转换'
            }
        }
    
    async def ensure_tools_available(self, required_tools):
        """确保所需工具可用"""
        missing_tools = []
        
        for tool_name in required_tools:
            if not self._is_tool_available(tool_name):
                missing_tools.append(tool_name)
        
        if missing_tools:
            await self._install_missing_tools(missing_tools)
        
        return len(missing_tools) == 0
    
    def _is_tool_available(self, tool_name):
        """检查工具是否可用"""
        try:
            if tool_name == 'html_to_pdf':
                import weasyprint
                return True
            elif tool_name == 'markdown_parser':
                import markdown
                return True
            elif tool_name == 'image_tools':
                import PIL
                return True
        except ImportError:
            return False
        
        return False
    
    async def _install_missing_tools(self, missing_tools):
        """安装缺失的工具"""
        for tool_name in missing_tools:
            tool_info = self.available_tools.get(tool_name)
            if tool_info:
                install_cmd = tool_info['install_command']
                # 这里应该通过coder_agent执行安装命令
                print(f"需要安装工具: {install_cmd}")
```

### 5️⃣ **增强的Prompt系统**

```python
# 修改文件: src/magentic_ui/teams/orchestrator/_prompts.py

# 添加更严格的执行控制Prompt
ENHANCED_EXECUTION_CONTROL_PROMPT = """
## 🎯 **严格执行控制规则**

### ✅ **步骤完成判断标准**:
1. **Web搜索步骤**: 必须包含明确完成信号 + 实际产品信息
   - 完成信号: ✅ 任务已完成 / ✅ TASK COMPLETED
   - 信息要求: 包含产品名称、规格、特点等具体信息

2. **图像生成步骤**: 必须包含生成完成确认 + 图像引用
   - 完成信号: 图像生成任务已完成 / image generation complete  
   - 文件引用: 包含图像文件名或路径

3. **文档创建步骤**: 必须包含文件保存确认 + 文件名
   - 完成信号: 文档创建任务已完成 / document creation completed
   - 文件证据: 明确的文件名和保存路径

### 🚫 **严格禁止的完成判断**:
- 通用帮助回复 ("我理解您需要", "Let me help you")
- 规划性回复 ("为了创建", "Let me create") 
- 询问性回复 (问用户更多信息)
- 短于50字符的回复
- 重复相同内容超过2次的回复

### 🔄 **智能Agent分配规则**:
- 🌐 **网站访问/搜索**: 强制使用 "web_surfer"
- 🎨 **图像生成/AI绘图**: 强制使用 "image_generator" 
- 📝 **文档处理/格式转换**: 强制使用 "coder_agent"
- 📁 **文件操作**: 使用 "file_surfer"

### ⚡ **执行效率优化**:
- 每个Agent最多3次尝试机会
- 检测到循环立即切换策略
- 工具缺失时自动安装或提供替代方案
"""

# 添加智能绘图选择Prompt
SMART_DRAWING_SELECTION_PROMPT = """
## 🎨 **智能绘图方式选择**

### 📊 **绘图方式决策树**:

**问题**: 用户需要什么类型的图像？

1. **艺术创作/概念设计** → 使用 AI绘图 (DALL-E)
   - 产品概念图、艺术插画、创意设计
   - 关键词: "设计", "概念", "艺术", "创意", "CG风格"
   - 优势: 创意无限、风格多样、快速生成

2. **数据可视化/技术图表** → 使用 编程绘图 (matplotlib/plotly)
   - 图表、曲线、框图、流程图、数据分析图
   - 关键词: "图表", "曲线", "数据", "分析", "流程图"
   - 优势: 精确数据、可交互、易更新

3. **技术示意图/结构图** → 根据复杂度选择
   - 简单结构 → AI绘图
   - 复杂技术图 → 编程绘图

### 🎯 **当前任务分析**: 360全景相机设计图
- **类型**: 产品概念设计图
- **要求**: 高清CG风格、4个镜头分布
- **选择**: AI绘图 (DALL-E) ✅
- **理由**: 需要艺术性和设计感，不是数据图表
"""
```

## 📈 **重构实施计划**

### 阶段1: 核心控制器重构 (优先级: 高)
1. 创建 `ExecutionController` 类
2. 实现严格的步骤验证机制
3. 添加执行历史追踪

### 阶段2: Agent分配优化 (优先级: 高)  
1. 实现 `SmartAgentAllocator`
2. 更新Prompt系统
3. 添加智能绘图选择逻辑

### 阶段3: 工具集成 (优先级: 中)
1. 创建 `ToolIntegrationManager`
2. 自动安装缺失工具
3. 提供工具替代方案

### 阶段4: 测试和优化 (优先级: 中)
1. 编写单元测试
2. 集成测试
3. 性能优化

## 🎯 **预期效果**

重构后的系统将具备：
- ✅ **严格的步骤控制**: 确保每步真正完成才继续
- ✅ **智能Agent分配**: 自动选择最适合的Agent
- ✅ **完整工具支持**: 自动处理工具依赖
- ✅ **防循环机制**: 智能检测和避免重复操作
- ✅ **Munas风格协作**: 高效的多Agent智能协作

这将解决您遇到的跳步执行、Agent分配错误、工具缺失等问题，实现真正的智能化任务执行。