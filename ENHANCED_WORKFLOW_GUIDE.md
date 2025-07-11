# 增强工作流程系统使用指南

## 概述

增强工作流程系统是对Magentic-UI原有多步骤任务处理的重大改进，专门解决了以下问题：

- 🔄 **WebSurfer循环检测过于严格**
- 🖼️ **图像生成和存储机制不完善**
- 📄 **HTML和PDF输出功能缺陷**
- 🔗 **中间素材传递逻辑不稳定**
- 🎯 **步骤执行状态管理不一致**

## 核心组件

### 1. 增强素材管理器 (`EnhancedMaterialManager`)

负责管理工作流程中的所有素材（图像、文档、数据等）。

**特性：**
- 📁 统一的文件存储和管理
- 🔗 素材间的关联和引用
- 📊 详细的元数据记录
- 🗑️ 自动清理过期素材

### 2. 增强工作流程协调器 (`EnhancedWorkflowCoordinator`)

协调多步骤任务的执行，管理步骤状态和素材传递。

**特性：**
- 📋 详细的步骤状态跟踪
- 🔄 智能的完成信号识别
- 📊 丰富的上下文信息
- 🎯 精确的步骤控制

### 3. 增强的代理组件

#### EnhancedWebSurferAgent
- 🧠 智能循环检测
- 🎯 上下文感知的行为判断
- 📊 详细的操作记录
- ⚡ 自适应的操作策略

#### EnhancedImageGeneratorAgent
- 🎨 增强的提示词构建
- 💾 自动素材存储
- 📊 详细的生成元数据
- 🔗 工作流程集成

#### EnhancedCoderAgent
- 📝 智能文档生成
- 🌐 多格式输出支持
- 🔗 素材引用和整合
- ✅ 质量验证和错误处理

### 4. 集成工作流程管理器 (`IntegratedWorkflowManager`)

整合所有增强组件的统一管理器。

## 使用方法

### 基本用法

```python
from pathlib import Path
from magentic_ui.agents import IntegratedWorkflowManager
from magentic_ui.types import Plan, PlanStep

# 创建工作流程管理器
work_dir = Path("./workflow_data")
manager = IntegratedWorkflowManager(work_dir, team_config)

# 创建计划
plan = Plan(
    task="生成360度全景相机产品介绍",
    steps=[
        PlanStep(
            title="访问参考网站",
            details="访问te720.com收集产品信息",
            agent_name="web_surfer"
        ),
        PlanStep(
            title="生成产品图像",
            details="生成高质量CG风格的360度全景相机图像",
            agent_name="image_generator"
        ),
        PlanStep(
            title="创建产品介绍文档",
            details="使用收集的信息创建markdown格式的产品介绍",
            agent_name="coder"
        ),
        PlanStep(
            title="生成HTML版本",
            details="将markdown转换为HTML格式",
            agent_name="coder"
        ),
        PlanStep(
            title="生成PDF版本",
            details="将HTML转换为PDF格式供下载",
            agent_name="coder"
        )
    ]
)

# 初始化增强代理
manager.initialize_enhanced_agents(original_agents)

# 启动工作流程
manager.start_workflow(plan)

# 执行工作流程
while manager.coordinator.should_continue_workflow():
    # 获取下一个代理
    agent = manager.get_next_agent()
    if not agent:
        break
    
    # 获取当前上下文
    context = manager.get_current_context()
    
    # 执行代理任务
    response = await agent.process_task(context)
    
    # 处理响应
    result = manager.process_agent_response(agent.name, response)
    
    if not result['should_continue']:
        break

# 获取最终输出
final_outputs = manager.get_final_outputs()
```

### 高级配置

#### 自定义循环检测策略

```python
# 配置WebSurfer的循环检测
web_surfer_config = {
    'max_page_visits': 8,  # 增加页面访问次数
    'max_element_interactions': 5,  # 增加元素交互次数
    'adaptive_threshold': True,  # 启用自适应阈值
    'context_aware_detection': True  # 启用上下文感知
}

enhanced_web_surfer = EnhancedWebSurferAgent(
    name="web_surfer",
    model_client=model_client,
    workflow_coordinator=coordinator,
    **web_surfer_config
)
```

#### 自定义文档生成

```python
# 配置Coder的文档生成
coder_config = {
    'auto_install_deps': True,
    'template_support': True,
    'quality_validation': True,
    'multi_format_output': True
}

enhanced_coder = EnhancedCoderAgent(
    name="coder",
    model_client=model_client,
    workflow_coordinator=coordinator,
    **coder_config
)
```

#### 自定义图像生成

```python
# 配置ImageGenerator的增强功能
image_config = {
    'auto_store': True,
    'include_metadata': True,
    'quality_check': True
}

enhanced_image_gen = EnhancedImageGeneratorAgent(
    name="image_generator",
    model_client=model_client,
    image_client=image_client,
    workflow_coordinator=coordinator
)
```

## 最佳实践

### 1. 任务规划

```python
# 良好的任务规划示例
plan = Plan(
    task="完整的产品介绍生成流程",
    steps=[
        # 信息收集阶段
        PlanStep(
            title="收集产品信息",
            details="访问官方网站收集产品规格和特性",
            agent_name="web_surfer"
        ),
        # 素材生成阶段
        PlanStep(
            title="生成产品图像",
            details="基于收集的信息生成高质量产品图像",
            agent_name="image_generator"
        ),
        # 文档创建阶段
        PlanStep(
            title="创建基础文档",
            details="使用markdown格式创建产品介绍文档",
            agent_name="coder"
        ),
        # 格式转换阶段
        PlanStep(
            title="生成最终格式",
            details="转换为HTML和PDF格式",
            agent_name="coder"
        )
    ]
)
```

### 2. 错误处理

```python
try:
    # 启动工作流程
    manager.start_workflow(plan)
    
    # 执行流程
    while manager.coordinator.should_continue_workflow():
        try:
            agent = manager.get_next_agent()
            if not agent:
                break
            
            response = await agent.process_task(context)
            result = manager.process_agent_response(agent.name, response)
            
        except Exception as step_error:
            logger.error(f"步骤执行失败: {step_error}")
            # 可以选择跳过或重试
            manager.skip_current_step(f"执行失败: {step_error}")
            continue
    
except Exception as workflow_error:
    logger.error(f"工作流程失败: {workflow_error}")
    # 获取部分结果
    partial_results = manager.get_final_outputs()
    
finally:
    # 清理资源
    manager.cleanup()
```

### 3. 监控和调试

```python
# 获取实时状态
status = manager.get_workflow_status()
print(f"当前步骤: {status['current_step']}/{status['total_steps']}")
print(f"已完成: {status['completed_steps']}, 失败: {status['failed_steps']}")

# 获取素材信息
materials = manager.get_generated_materials()
for material in materials:
    print(f"素材 {material['id']}: {material['type']} (步骤 {material['step_index']})")

# 获取详细日志
for agent_name, agent in manager.enhanced_agents.items():
    if hasattr(agent, 'get_operation_summary'):
        print(f"{agent_name}: {agent.get_operation_summary()}")
```

## 故障排除

### 常见问题和解决方案

#### 1. WebSurfer循环检测误报

```python
# 方案1: 调整检测参数
web_surfer.config['max_page_visits'] = 10
web_surfer.config['adaptive_threshold'] = True

# 方案2: 重置检测状态
web_surfer.reset_loop_detection()

# 方案3: 强制完成步骤
manager.force_complete_current_step("手动完成网页浏览")
```

#### 2. 图像生成失败

```python
# 检查图像生成状态
if not generation_result.success:
    print(f"生成失败: {generation_result.error_message}")
    
    # 尝试重新生成
    enhanced_prompt = image_gen._build_enhanced_prompt(request_info)
    retry_result = await image_gen.image_client.generate_image(enhanced_prompt)
```

#### 3. PDF生成失败

```python
# 检查weasyprint安装
try:
    import weasyprint
    print("✅ weasyprint已安装")
except ImportError:
    print("❌ weasyprint未安装，正在安装...")
    subprocess.run(['pip', 'install', 'weasyprint'], check=True)

# 检查HTML文件
html_file = Path("document.html")
if html_file.exists():
    print(f"✅ HTML文件存在: {html_file.stat().st_size} bytes")
else:
    print("❌ HTML文件不存在")
```

## 性能优化

### 1. 并行处理

```python
# 对于独立的步骤可以并行执行
async def parallel_generation():
    # 同时生成多个图像
    image_tasks = [
        image_gen.generate_image(prompt1),
        image_gen.generate_image(prompt2)
    ]
    
    results = await asyncio.gather(*image_tasks)
    return results
```

### 2. 缓存机制

```python
# 启用素材缓存
manager.material_manager.config['cache_enabled'] = True
manager.material_manager.config['cache_ttl'] = 3600  # 1小时
```

### 3. 资源管理

```python
# 定期清理过期素材
await manager.material_manager.cleanup_old_materials(days=1)

# 限制素材数量
manager.material_manager.config['max_materials'] = 100
```

## 扩展开发

### 添加新的增强代理

```python
class EnhancedCustomAgent(CustomAgent):
    def __init__(self, *args, workflow_coordinator=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow_coordinator = workflow_coordinator
    
    async def process_task(self, context):
        # 自定义处理逻辑
        result = await super().process_task(context)
        
        # 存储结果
        if self.workflow_coordinator:
            await self.workflow_coordinator.store_step_result(
                content=result,
                content_type='custom',
                metadata={'custom_field': 'value'}
            )
        
        return result
```

### 自定义素材类型

```python
# 扩展素材管理器
class CustomMaterialManager(EnhancedMaterialManager):
    async def store_custom_material(self, data, step_index, agent_name):
        # 自定义存储逻辑
        return await self.store_text(
            content=json.dumps(data),
            step_index=step_index,
            agent_name=agent_name,
            type='custom_type'
        )
```

## 版本兼容性

此增强系统与现有的Magentic-UI系统完全兼容，可以：

1. **渐进式升级**：逐步替换原有组件
2. **向后兼容**：保持原有API接口
3. **配置兼容**：使用现有配置文件
4. **数据兼容**：兼容现有数据格式

## 更新日志

### v1.0.0 (初始版本)
- ✅ 增强的WebSurfer循环检测
- ✅ 改进的图像生成和存储
- ✅ 完善的HTML/PDF输出
- ✅ 统一的素材管理
- ✅ 集成的工作流程管理

### 计划中的功能
- 🔄 更多的并行处理支持
- 🎯 更智能的任务规划
- 📊 更详细的分析报告
- 🔧 更多的自定义选项