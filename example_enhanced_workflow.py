"""
增强工作流程实际使用示例
专门解决用户提到的360度全景相机任务问题
"""

import asyncio
import os
from pathlib import Path
from loguru import logger
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from magentic_ui.agents._integrated_workflow_manager import IntegratedWorkflowManager
from magentic_ui.agents._enhanced_web_surfer import EnhancedWebSurferAgent
from magentic_ui.agents._enhanced_image_generator import EnhancedImageGeneratorAgent
from magentic_ui.agents._enhanced_coder import EnhancedCoderAgent
from magentic_ui.types import Plan, PlanStep

class MockModelClient:
    """模拟模型客户端"""
    def __init__(self):
        self.model_info = {"vision": False}
    
    async def create_completion(self, messages, **kwargs):
        return {"choices": [{"message": {"content": "模拟响应"}}]}

class MockImageClient:
    """模拟图像客户端"""
    async def generate_image(self, prompt, config):
        # 模拟生成图像
        from magentic_ui.tools.image_generation import ImageGenerationResult
        import base64
        
        # 创建一个简单的1x1像素图像的base64数据
        fake_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jGL7ZgAAAABJRU5ErkJggg=="
        
        return ImageGenerationResult(
            success=True,
            image_data=fake_image_data,
            model_used="dall-e-3",
            generation_time=2.5,
            metadata={"prompt": prompt}
        )

class MockWebSurfer:
    """模拟WebSurfer"""
    def __init__(self):
        self.name = "web_surfer"
        self._model_client = MockModelClient()
        self.description = "Mock WebSurfer"
        self.browser_config = {}
        self.single_tab_mode = True
        self.start_page = "about:blank"
        self.downloads_folder = None
        self.viewport = {'width': 1440, 'height': 900}
        self._playwright_controller = None

class MockCoder:
    """模拟Coder"""
    def __init__(self):
        self.name = "coder"
        self._model_client = MockModelClient()
        self.description = "Mock Coder"
        self._max_debug_rounds = 3
        self._summarize_output = False
        self._work_dir = Path("/tmp")
        self._code_executor = None
        self._approval_guard = None

class MockImageGenerator:
    """模拟ImageGenerator"""
    def __init__(self):
        self.name = "image_generator"
        self._model_client = MockModelClient()
        self.image_client = MockImageClient()

async def create_enhanced_360_camera_workflow():
    """创建增强的360度全景相机工作流程"""
    
    # 设置工作目录
    work_dir = Path("./enhanced_workflow_demo")
    work_dir.mkdir(exist_ok=True)
    
    # 创建集成工作流程管理器
    manager = IntegratedWorkflowManager(work_dir, {})
    
    # 创建模拟的原始代理
    original_agents = {
        'web_surfer': MockWebSurfer(),
        'coder': MockCoder(),
        'image_generator': MockImageGenerator()
    }
    
    # 初始化增强代理
    manager.initialize_enhanced_agents(original_agents)
    
    # 创建详细的计划
    plan = Plan(
        task="生成360度全景相机产品介绍 - 包含图像、HTML和PDF",
        steps=[
            PlanStep(
                title="访问参考网站te720.com",
                details="访问te720.com网站，查找360度全景相机的参考图片和产品信息，重点关注4镜头90度分布的设计",
                agent_name="web_surfer"
            ),
            PlanStep(
                title="生成CG风格全景相机图像",
                details="基于收集的信息，生成高清CG风格的360度全景相机图像，展示4个镜头分别分布在90度间隔的四个方向",
                agent_name="image_generator"
            ),
            PlanStep(
                title="编写产品介绍Markdown文档",
                details="使用收集的信息和生成的图像，创建完整的产品介绍Markdown文档，包括产品特性、技术规格等",
                agent_name="coder"
            ),
            PlanStep(
                title="转换为HTML格式",
                details="将Markdown文档转换为美观的HTML格式，包含样式和布局，整合生成的图像",
                agent_name="coder"
            ),
            PlanStep(
                title="生成PDF版本",
                details="将HTML文档转换为PDF格式供下载，确保排版美观和打印友好",
                agent_name="coder"
            )
        ]
    )
    
    return manager, plan

async def simulate_enhanced_web_surfer_step(manager, agent):
    """模拟增强WebSurfer步骤"""
    logger.info("🌐 开始模拟WebSurfer步骤")
    
    # 模拟WebSurfer的改进行为
    from autogen_agentchat.messages import TextMessage
    
    # 获取当前上下文
    context = manager.get_current_context()
    logger.info(f"📋 上下文: {context}")
    
    # 模拟访问网站的响应
    mock_response = TextMessage(
        content=\"\"\"🌐 已成功访问te720.com网站

📊 收集到的信息:
- 发现了360度全景相机产品页面
- 产品采用4镜头设计，分布在90度间隔
- 支持4K高清录制和8K照片拍摄
- 具有实时拼接功能
- 内置防抖系统

🖼️ 找到了参考图片:
- 相机外观为紧凑型圆形设计
- 4个镜头分别位于前后左右四个方向
- 黑色金属机身，专业外观
- 底部有标准三脚架接口

✅ 当前步骤已完成 - 已收集到足够的产品信息用于后续图像生成\"\"\",
        source=agent.name
    )
    
    # 存储收集到的信息
    await manager.coordinator.store_step_result(
        content=\"\"\"# te720.com收集的信息

## 产品特性
- 4镜头设计，90度间隔分布
- 4K高清录制，8K照片拍摄
- 实时拼接功能
- 内置防抖系统

## 外观设计
- 紧凑型圆形设计
- 黑色金属机身
- 专业外观
- 标准三脚架接口

## 技术规格
- 全景拍摄覆盖360度
- 高质量镜头组件
- 先进的图像处理算法
\"\"\",
        content_type="markdown",
        filename="collected_info.md"
    )
    
    return mock_response

async def simulate_enhanced_image_generator_step(manager, agent):
    """模拟增强ImageGenerator步骤"""
    logger.info("🎨 开始模拟ImageGenerator步骤")
    
    from autogen_agentchat.messages import TextMessage
    
    # 获取上下文，包含之前收集的信息
    context = manager.get_current_context()
    
    # 模拟生成图像
    mock_response = TextMessage(
        content=\"\"\"🎨 图像生成完成！

🎯 风格: cg, technical, product
⚙️ 技术要求: {'quality': 'hd', 'type': 'panoramic'}
📁 素材ID: img_360cam_001
✅ 图像已自动保存到工作流程中

🖼️ 生成的图像展示了:
- 360度全景相机的专业CG渲染
- 4个镜头清晰分布在90度间隔位置
- 高质量的金属质感和专业外观
- 适合产品介绍使用的商业级品质

🔄 图像已准备就绪，可以继续下一步骤\"\"\",
        source=agent.name
    )
    
    # 模拟存储图像
    fake_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jQL7ZgAAAABJRU5ErkJggg=="
    
    await manager.coordinator.store_step_result(
        content=fake_image_data,
        content_type="image",
        filename="360_camera_render.png",
        metadata={
            'style_hints': ['cg', 'technical', 'product'],
            'technical_requirements': {'quality': 'hd', 'type': 'panoramic'},
            'generation_model': 'dall-e-3'
        }
    )
    
    return mock_response

async def simulate_enhanced_coder_step(manager, agent, task_type):
    """模拟增强Coder步骤"""
    logger.info(f"💻 开始模拟Coder步骤: {task_type}")
    
    from autogen_agentchat.messages import TextMessage
    
    if task_type == "markdown":
        # 模拟创建Markdown文档
        mock_response = TextMessage(
            content=\"\"\"📝 产品介绍Markdown文档已创建

📊 生成的文档包含:
- 完整的产品概述
- 详细的技术规格
- 核心特性说明
- 应用场景介绍

📄 Markdown文件已保存: document.md
✅ 文档创建任务已完成\"\"\",
            source=agent.name
        )
        
        # 存储Markdown文档
        markdown_content = \"\"\"# 360度全景相机产品介绍

## 产品概述
基于先进的te720.com技术，我们的360度全景相机采用创新的四镜头设计，每个镜头分布在90度间隔的四个方向，实现真正的360度全景拍摄。

![360度全景相机](360_camera_render.png)

## 核心特性

### 🎥 四镜头设计
- **分布式镜头**: 4个高质量镜头分别位于相机的前、后、左、右四个方向
- **90度间隔**: 精确的90度间隔确保无缝全景拼接
- **同步拍摄**: 所有镜头同步工作，避免拼接错误

### 📸 技术规格
- **分辨率**: 4K高清录制，支持8K照片拍摄
- **视角**: 每个镜头覆盖90度以上视角
- **拼接技术**: 先进的实时拼接算法
- **防抖**: 内置6轴防抖系统

### 🔧 产品优势
1. **专业品质**: 高清CG级别的图像质量
2. **便携设计**: 紧凑的机身设计，便于携带
3. **易用性**: 一键拍摄，自动处理
4. **兼容性**: 支持多种VR设备和平台

## 应用场景
- 虚拟现实内容创作
- 房地产虚拟看房
- 旅游景点展示
- 活动记录和直播
- 教育培训场景

## 技术支持
基于te720.com的技术支持，提供完整的360度全景解决方案。

---
*生成时间: 2024-01-01*
\"\"\"
        
        await manager.coordinator.store_step_result(
            content=markdown_content,
            content_type="markdown",
            filename="product_introduction.md"
        )
        
    elif task_type == "html":
        # 模拟转换为HTML
        mock_response = TextMessage(
            content=\"\"\"🌐 HTML文档已生成

🎨 包含特性:
- 响应式设计
- 专业样式
- 图像整合
- 优化布局

📄 HTML文件已保存: document.html
✅ HTML转换完成\"\"\",
            source=agent.name
        )
        
        # 存储HTML文档
        html_content = \"\"\"<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>360度全景相机产品介绍</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        .hero-image {
            text-align: center;
            margin: 20px 0;
        }
        .hero-image img {
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .feature {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .specs {
            background: #e8f5e8;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #27ae60;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>360度全景相机产品介绍</h1>
        
        <div class="hero-image">
            <img src="360_camera_render.png" alt="360度全景相机">
        </div>
        
        <h2>产品概述</h2>
        <p>基于先进的te720.com技术，我们的360度全景相机采用创新的四镜头设计，每个镜头分布在90度间隔的四个方向，实现真正的360度全景拍摄。</p>
        
        <h2>核心特性</h2>
        
        <div class="feature">
            <h3>🎥 四镜头设计</h3>
            <ul>
                <li><strong>分布式镜头</strong>: 4个高质量镜头分别位于相机的前、后、左、右四个方向</li>
                <li><strong>90度间隔</strong>: 精确的90度间隔确保无缝全景拼接</li>
                <li><strong>同步拍摄</strong>: 所有镜头同步工作，避免拼接错误</li>
            </ul>
        </div>
        
        <div class="specs">
            <h3>📸 技术规格</h3>
            <ul>
                <li><strong>分辨率</strong>: 4K高清录制，支持8K照片拍摄</li>
                <li><strong>视角</strong>: 每个镜头覆盖90度以上视角</li>
                <li><strong>拼接技术</strong>: 先进的实时拼接算法</li>
                <li><strong>防抖</strong>: 内置6轴防抖系统</li>
            </ul>
        </div>
        
        <h2>应用场景</h2>
        <ul>
            <li>虚拟现实内容创作</li>
            <li>房地产虚拟看房</li>
            <li>旅游景点展示</li>
            <li>活动记录和直播</li>
            <li>教育培训场景</li>
        </ul>
        
        <div style="text-align: center; margin-top: 40px; color: #7f8c8d;">
            <p>© 2024 360度全景相机产品介绍</p>
        </div>
    </div>
</body>
</html>\"\"\"
        
        await manager.coordinator.store_step_result(
            content=html_content,
            content_type="html",
            filename="product_introduction.html"
        )
        
    elif task_type == "pdf":
        # 模拟转换为PDF
        mock_response = TextMessage(
            content=\"\"\"📄 PDF文档已生成

✅ 转换成功:
- 使用weasyprint转换
- 保持HTML样式
- 优化打印布局
- 包含所有图像

📄 PDF文件已保存: document.pdf
📊 PDF文件大小: 245.3 KB
✅ PDF生成完成\"\"\",
            source=agent.name
        )
        
        # 模拟存储PDF（实际应该是二进制数据）
        await manager.coordinator.store_step_result(
            content="PDF_BINARY_DATA_PLACEHOLDER",
            content_type="pdf",
            filename="product_introduction.pdf"
        )
    
    return mock_response

async def run_enhanced_workflow_demo():
    """运行增强工作流程演示"""
    logger.info("🚀 开始增强工作流程演示")
    
    # 创建工作流程
    manager, plan = await create_enhanced_360_camera_workflow()
    
    # 启动工作流程
    manager.start_workflow(plan)
    
    # 模拟执行各个步骤
    step_simulations = [
        ("web_surfer", simulate_enhanced_web_surfer_step),
        ("image_generator", simulate_enhanced_image_generator_step),
        ("coder", lambda m, a: simulate_enhanced_coder_step(m, a, "markdown")),
        ("coder", lambda m, a: simulate_enhanced_coder_step(m, a, "html")),
        ("coder", lambda m, a: simulate_enhanced_coder_step(m, a, "pdf"))
    ]
    
    for i, (agent_name, simulation_func) in enumerate(step_simulations):
        logger.info(f"\n🔄 执行步骤 {i + 1}/{len(step_simulations)}")
        
        # 获取当前步骤
        current_step = manager.coordinator.get_current_step()
        if not current_step:
            logger.error("❌ 无法获取当前步骤")
            break
        
        logger.info(f"📋 当前步骤: {current_step.plan_step.title}")
        
        # 开始步骤
        manager.coordinator.start_step()
        
        # 获取对应的增强代理
        agent = manager.enhanced_agents.get(agent_name)
        if not agent:
            logger.warning(f"⚠️ 未找到增强代理: {agent_name}")
            # 创建模拟代理
            if agent_name == "web_surfer":
                agent = MockWebSurfer()
            elif agent_name == "image_generator":
                agent = MockImageGenerator()
            elif agent_name == "coder":
                agent = MockCoder()
        
        # 执行步骤模拟
        try:
            response = await simulation_func(manager, agent)
            
            # 处理响应
            result = manager.process_agent_response(agent_name, response)
            
            if result['success']:
                logger.info(f"✅ 步骤 {i + 1} 完成")
            else:
                logger.error(f"❌ 步骤 {i + 1} 失败: {result.get('error', '未知错误')}")
            
        except Exception as e:
            logger.error(f"❌ 步骤 {i + 1} 执行异常: {e}")
            manager.coordinator.fail_step(error=str(e))
    
    # 获取最终结果
    final_outputs = manager.get_final_outputs()
    
    logger.info("\n🎉 工作流程完成！")
    logger.info(f"📊 最终状态: {final_outputs['status']}")
    logger.info(f"📁 生成素材: {len(final_outputs['materials'])} 个")
    logger.info(f"📄 生成文件: {len(final_outputs['generated_files'])} 个")
    
    # 显示详细结果
    logger.info("\n📋 生成的素材:")
    for material in final_outputs['materials']:
        logger.info(f"  - {material['type']} ({material['id']}): {material['agent_name']}")
    
    logger.info("\n📄 生成的文件:")
    for file_info in final_outputs['generated_files']:
        logger.info(f"  - {file_info['name']} ({file_info['size']} bytes)")
    
    logger.info(f"\n{final_outputs['summary']}")
    
    # 清理
    manager.cleanup()
    
    logger.info("🎯 演示完成！这就是增强工作流程系统解决您提到的问题的方式。")

if __name__ == "__main__":
    asyncio.run(run_enhanced_workflow_demo())