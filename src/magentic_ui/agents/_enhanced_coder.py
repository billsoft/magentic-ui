"""
增强的Coder Agent - 改进HTML和PDF生成功能
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Sequence
from loguru import logger
import tempfile

from ._coder import CoderAgent
from .._enhanced_workflow_coordinator import EnhancedWorkflowCoordinator
from .._enhanced_material_manager import MaterialItem

class EnhancedCoderAgent(CoderAgent):
    """增强的Coder Agent"""
    
    def __init__(self, *args, workflow_coordinator: Optional[EnhancedWorkflowCoordinator] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow_coordinator = workflow_coordinator
        
        # 文档生成配置
        self.doc_config = {
            'auto_install_deps': True,
            'template_support': True,
            'quality_validation': True,
            'multi_format_output': True,
            'include_metadata': True
        }
        
        logger.info(f"📝 增强Coder Agent初始化: {self.name}")
    
    def _detect_document_task(self, messages: Sequence) -> Dict[str, Any]:
        """检测文档任务类型"""
        task_info = {
            'type': 'general',
            'formats': [],
            'has_material_refs': False,
            'material_types': [],
            'content_type': 'text'
        }
        
        # 分析消息内容
        full_content = ""
        for msg in messages:
            if hasattr(msg, 'content'):
                content = msg.content
                if isinstance(content, str):
                    full_content += content.lower() + " "
        
        # 检测输出格式
        if any(keyword in full_content for keyword in ['markdown', 'md', '文档']):
            task_info['formats'].append('markdown')
        if any(keyword in full_content for keyword in ['html', '网页', '排版']):
            task_info['formats'].append('html')
        if any(keyword in full_content for keyword in ['pdf', '文档', '下载']):
            task_info['formats'].append('pdf')
        
        # 检测内容类型
        if any(keyword in full_content for keyword in ['产品', '介绍', 'product', 'introduction']):
            task_info['content_type'] = 'product_introduction'
        elif any(keyword in full_content for keyword in ['报告', 'report', '总结']):
            task_info['content_type'] = 'report'
        elif any(keyword in full_content for keyword in ['文章', 'article', '博客']):
            task_info['content_type'] = 'article'
        
        # 检测素材引用
        if any(keyword in full_content for keyword in ['图', '图像', '照片', 'image']):
            task_info['has_material_refs'] = True
            task_info['material_types'].append('image')
        
        # 确定任务类型
        if task_info['formats']:
            task_info['type'] = 'document_generation'
        
        return task_info
    
    def _get_available_materials(self) -> List[MaterialItem]:
        """获取可用的素材"""
        if not self.workflow_coordinator:
            return []
        
        # 获取当前步骤的所有可用素材
        current_step = self.workflow_coordinator.get_current_step()
        if not current_step:
            return []
        
        # 获取当前步骤及之前步骤的素材
        all_materials = []
        for step_index in range(current_step.index + 1):
            step_materials = self.workflow_coordinator.get_step_materials(step_index)
            all_materials.extend(step_materials)
        
        return all_materials
    
    def _generate_material_references(self, materials: List[MaterialItem]) -> Dict[str, str]:
        """生成素材引用"""
        references = {}
        
        for material in materials:
            if material.type == 'image':
                # 为图像生成引用
                references[material.id] = f"![Generated Image]({material.content})"
            elif material.type == 'markdown':
                # 为markdown生成引用
                references[material.id] = f"[参考文档]({material.content})"
            elif material.type == 'text':
                # 为文本生成引用
                references[material.id] = f"参考: {material.content}"
        
        return references
    
    def _create_enhanced_system_prompt(self, task_info: Dict[str, Any], materials: List[MaterialItem]) -> str:
        """创建增强的系统提示"""
        base_prompt = f"""你是一个专业的文档生成专家。当前任务类型: {task_info['content_type']}

任务要求:
- 输出格式: {', '.join(task_info['formats']) if task_info['formats'] else '通用'}
- 内容类型: {task_info['content_type']}
- 质量要求: 专业、详细、结构化

"""
        
        # 添加素材信息
        if materials:
            base_prompt += f"\\n可用素材 ({len(materials)}个):\\n"
            for material in materials:
                base_prompt += f"- {material.type} ({material.id}): 由 {material.agent_name} 在步骤 {material.step_index + 1} 生成\\n"
        
        # 添加格式特定指导
        if 'markdown' in task_info['formats']:
            base_prompt += """
Markdown 格式要求:
- 使用合适的标题层级 (# ## ###)
- 包含目录结构
- 使用表格、列表等格式化元素
- 如果有图像素材，使用 ![description](path) 语法

"""
        
        if 'html' in task_info['formats']:
            base_prompt += """
HTML 格式要求:
- 使用完整的HTML5结构
- 包含适当的CSS样式
- 响应式设计
- 优化的排版和布局
- 如果有图像素材，使用 <img> 标签

"""
        
        if 'pdf' in task_info['formats']:
            base_prompt += """
PDF 生成要求:
- 先生成HTML版本
- 使用weasyprint转换为PDF
- 确保样式适合打印
- 包含页眉页脚
- 优化字体和布局

"""
        
        base_prompt += """
工作流程:
1. 分析任务需求和可用素材
2. 生成相应格式的内容
3. 保存生成的文件
4. 验证输出质量
5. 提供清晰的完成报告

重要提示:
- 所有文件都应保存在当前工作目录
- 使用描述性的文件名
- 确保内容专业且准确
- 如果转换失败，提供清晰的错误说明
"""
        
        return base_prompt
    
    def _create_document_generation_code(self, task_info: Dict[str, Any], materials: List[MaterialItem], user_request: str) -> str:
        """创建文档生成代码"""
        code_parts = []
        
        # 导入必要的库
        code_parts.append("""
import os
import json
from pathlib import Path
from datetime import datetime
import base64
""")
        
        # 如果需要PDF，添加weasyprint
        if 'pdf' in task_info['formats']:
            code_parts.append("""
# 安装和导入weasyprint
try:
    import weasyprint
    print("✅ weasyprint已安装")
except ImportError:
    print("📦 正在安装weasyprint...")
    import subprocess
    result = subprocess.run(['pip', 'install', 'weasyprint'], capture_output=True, text=True)
    if result.returncode == 0:
        import weasyprint
        print("✅ weasyprint安装成功")
    else:
        print(f"❌ weasyprint安装失败: {result.stderr}")
        print("⚠️ 将跳过PDF生成")
""")
        
        # 创建工作目录
        code_parts.append("""
# 创建工作目录
work_dir = Path(".")
output_dir = work_dir / "generated_documents"
output_dir.mkdir(exist_ok=True)

print(f"📁 工作目录: {work_dir.absolute()}")
print(f"📁 输出目录: {output_dir.absolute()}")
""")
        
        # 加载素材信息
        if materials:
            materials_info = []
            for material in materials:
                materials_info.append({
                    'id': material.id,
                    'type': material.type,
                    'content': material.content,
                    'metadata': material.metadata
                })
            
            code_parts.append(f"""
# 素材信息
materials = {json.dumps(materials_info, ensure_ascii=False, indent=2)}

print(f"📊 可用素材: {len(materials)} 个")
for material in materials:
    print(f"  - {material['type']} ({material['id']})")
""")
        
        # 根据内容类型生成内容
        if task_info['content_type'] == 'product_introduction':
            code_parts.append(self._generate_product_introduction_code(materials))
        else:
            code_parts.append(self._generate_general_document_code(user_request, materials))
        
        # 生成各种格式
        for format_type in task_info['formats']:
            if format_type == 'markdown':
                code_parts.append(self._generate_markdown_code())
            elif format_type == 'html':
                code_parts.append(self._generate_html_code())
            elif format_type == 'pdf':
                code_parts.append(self._generate_pdf_code())
        
        # 添加完成验证
        code_parts.append("""
# 验证输出
generated_files = []
for file_path in output_dir.glob("*"):
    if file_path.is_file():
        file_size = file_path.stat().st_size
        generated_files.append({
            'name': file_path.name,
            'size': file_size,
            'path': str(file_path)
        })

print("\\n📋 生成的文件:")
for file_info in generated_files:
    print(f"  ✅ {file_info['name']} ({file_info['size']} bytes)")

if generated_files:
    print(f"\\n🎉 文档生成任务已完成！生成了 {len(generated_files)} 个文件")
else:
    print("⚠️ 没有生成任何文件")
""")
        
        return "\n".join(code_parts)
    
    def _generate_product_introduction_code(self, materials: List[MaterialItem]) -> str:
        """生成产品介绍代码"""
        return """
# 生成产品介绍内容
product_content = '''# 360度全景相机产品介绍

## 产品概述
基于先进的te720.com技术，我们的360度全景相机采用创新的四镜头设计，每个镜头分布在90度间隔的四个方向，实现真正的360度全景拍摄。

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
*生成时间: ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "'"

print("📝 产品介绍内容已生成")
"""
    
    def _generate_general_document_code(self, user_request: str, materials: List[MaterialItem]) -> str:
        """生成通用文档代码"""
        return f"""
# 生成通用文档内容
document_content = '''# 文档标题

## 概述
根据用户需求: {user_request}

## 详细内容

### 主要信息
基于收集的信息和素材，生成专业的文档内容。

### 相关素材
''' + ("\\n".join([f"- {material.type}: {material.id}" for material in materials]) if materials else "暂无素材") + '''

### 总结
完整的文档内容已根据要求生成。

---
*生成时间: ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "'"

print("📝 文档内容已生成")
"""
    
    def _generate_markdown_code(self) -> str:
        """生成Markdown格式代码"""
        return """
# 生成Markdown文件
markdown_file = output_dir / "document.md"
with open(markdown_file, 'w', encoding='utf-8') as f:
    f.write(document_content)

print(f"📄 Markdown文件已保存: {markdown_file}")
"""
    
    def _generate_html_code(self) -> str:
        """生成HTML格式代码"""
        return """
# 生成HTML文件
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>产品介绍</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .feature {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .specs {{
            background: #e8f5e8;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #27ae60;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        {document_content.replace("### 🎥", '<div class="feature"><h3>🎥').replace("### 📸", '<div class="specs"><h3>📸').replace("### 🔧", '<div class="feature"><h3>🔧').replace("\\n\\n", "</div>\\n\\n")}
        <div class="footer">
            <p>© 2024 360度全景相机产品介绍</p>
        </div>
    </div>
</body>
</html>'''

html_file = output_dir / "document.html"
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"🌐 HTML文件已保存: {html_file}")
"""
    
    def _generate_pdf_code(self) -> str:
        """生成PDF格式代码"""
        return """
# 生成PDF文件
try:
    if 'weasyprint' in globals():
        pdf_file = output_dir / "document.pdf"
        
        # 从HTML生成PDF
        if html_file.exists():
            weasyprint.HTML(filename=str(html_file)).write_pdf(str(pdf_file))
            print(f"📄 PDF文件已保存: {pdf_file}")
            print(f"📊 PDF文件大小: {pdf_file.stat().st_size / 1024:.1f} KB")
        else:
            print("❌ HTML文件不存在，无法生成PDF")
    else:
        print("⚠️ weasyprint未安装，跳过PDF生成")
except Exception as e:
    print(f"❌ PDF生成失败: {e}")
    print("💡 建议检查HTML内容和weasyprint安装")
"""
    
    async def _handle_document_generation(self, messages: Sequence) -> Any:
        """处理文档生成任务"""
        try:
            # 检测任务类型
            task_info = self._detect_document_task(messages)
            logger.info(f"📋 检测到文档任务: {task_info}")
            
            # 获取可用素材
            materials = self._get_available_materials()
            logger.info(f"📊 可用素材: {len(materials)} 个")
            
            # 提取用户请求
            user_request = ""
            for msg in reversed(messages):
                if hasattr(msg, 'source') and msg.source != self.name:
                    if hasattr(msg, 'content') and isinstance(msg.content, str):
                        user_request = msg.content
                        break
            
            # 创建增强的系统提示
            enhanced_prompt = self._create_enhanced_system_prompt(task_info, materials)
            
            # 生成文档代码
            document_code = self._create_document_generation_code(task_info, materials, user_request)
            
            # 创建代码执行消息
            code_message = f"```python\n{document_code}\n```"
            
            # 执行代码
            from autogen_agentchat.messages import TextMessage
            code_msg = TextMessage(content=code_message, source=self.name)
            
            # 调用父类的代码执行逻辑
            response = await super().on_messages(messages + [code_msg], None)
            
            # 更新工作流程状态
            if self.workflow_coordinator:
                current_step = self.workflow_coordinator.get_current_step()
                if current_step:
                    # 存储生成的文档
                    generated_materials = []
                    
                    # 检查生成的文件
                    output_dir = Path(self._work_dir) / "generated_documents"
                    if output_dir.exists():
                        for file_path in output_dir.glob("*"):
                            if file_path.is_file():
                                content = file_path.read_text(encoding='utf-8') if file_path.suffix in ['.md', '.html'] else file_path.read_bytes()
                                
                                content_type = {
                                    '.md': 'markdown',
                                    '.html': 'html',
                                    '.pdf': 'pdf'
                                }.get(file_path.suffix, 'text')
                                
                                material_id = await self.workflow_coordinator.store_step_result(
                                    content=content if isinstance(content, str) else base64.b64encode(content).decode(),
                                    content_type=content_type,
                                    filename=file_path.name
                                )
                                generated_materials.append(material_id)
                    
                    # 完成步骤
                    self.workflow_coordinator.complete_step(
                        result=f"文档生成任务已完成 - 生成了 {len(generated_materials)} 个文件",
                        materials=generated_materials
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ 文档生成失败: {e}")
            if self.workflow_coordinator:
                self.workflow_coordinator.fail_step(error=str(e))
            raise
    
    async def on_messages(self, messages: Sequence, cancellation_token) -> Any:
        """重写消息处理方法"""
        # 检测是否为文档生成任务
        task_info = self._detect_document_task(messages)
        
        if task_info['type'] == 'document_generation':
            logger.info("📝 检测到文档生成任务，使用增强处理")
            return await self._handle_document_generation(messages)
        else:
            # 使用原有的处理逻辑
            return await super().on_messages(messages, cancellation_token)