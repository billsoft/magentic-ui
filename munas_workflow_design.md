# 🚀 Magentic-UI: Munas风格智能协作系统设计

## 📋 完整工作流程设计

### 1️⃣ **用户问题理解阶段 (Problem Understanding)**

**入口**: `Orchestrator.handle_start()` 
**文件**: `/src/magentic_ui/teams/orchestrator/_orchestrator.py:1220`

```python
# 用户请求解析流程
async def handle_start(self, message: GroupChatStart, ctx: MessageContext):
    # 1. 解析用户请求
    user_request = self._parse_user_request(message.messages)
    
    # 2. 智能需求分析
    requirements = self._analyze_requirements(user_request)
    
    # 3. 确定输出格式需求
    output_format = self._determine_output_format(user_request)
```

**需求分析增强**:
- ✅ 检测是否需要网络搜索 (`需要读取 te720.com`)
- ✅ 检测是否需要图像生成 (`360全景相机图`)
- ✅ 检测文档格式链 (`md → html → pdf`)
- ✅ 理解最终交付要求 (`产品介绍配图`)

### 2️⃣ **智能任务规划阶段 (Task Planning)**

**核心**: `ORCHESTRATOR_PLAN_PROMPT_JSON` 
**文件**: `/src/magentic_ui/teams/orchestrator/_prompts.py:150`

**规划原则 (已优化)**:
```
1. 信息收集 FIRST → web_surfer 研究
2. 内容生成 SECOND → image_generator 创建视觉内容
3. 文档编译 THIRD → coder_agent 创建 markdown
4. 格式转换 LAST → coder_agent 执行 md→html→pdf
```

### 3️⃣ **智能搜索信息阶段 (Information Gathering)**

**执行器**: `WebSurfer Agent`
**文件**: `/src/magentic_ui/agents/web_surfer/_web_surfer.py`

**搜索策略 (已优化)**:
```python
# 自主搜索原则
AUTONOMOUS_SEARCH_PRINCIPLES = {
    "目标导向": "明确搜索目标，避免无目的浏览",
    "效率优先": "最大3-4个操作完成信息收集", 
    "循环预防": "绝不重复相同操作超过一次",
    "智能完成": "收集到足够信息立即停止"
}
```

**搜索完成信号 (已修复)**:
- ✅ 任务已完成 / ✅ TASK COMPLETED
- ⚠️ 任务因错误完成 / ⚠️ TASK COMPLETED WITH ERRORS  
- 🔄 任务通过替代方案完成 / 🔄 TASK COMPLETED VIA ALTERNATIVE

### 4️⃣ **AI智能画图阶段 (Image Generation)**

**执行器**: `ImageGenerator Agent`
**文件**: `/src/magentic_ui/agents/_image_generator.py`

**生成策略**:
```python
# 基于搜索结果的智能图像生成
class ImageGenerationWorkflow:
    def generate_with_context(self, research_data, requirements):
        # 1. 分析研究数据中的视觉元素
        visual_elements = self.extract_visual_references(research_data)
        
        # 2. 构建增强的提示词
        enhanced_prompt = self.build_context_aware_prompt(
            base_requirement=requirements,
            research_context=visual_elements
        )
        
        # 3. 调用DALL-E生成
        return self.generate_image(enhanced_prompt)
```

### 5️⃣ **Markdown整理资料阶段 (Content Compilation)**

**执行器**: `Coder Agent`
**文件**: `/src/magentic_ui/agents/_coder.py`

**整理策略 (已修复模板错误)**:
```python
# Markdown 文档创建工作流
def create_markdown_document(self, research_data, image_info):
    # 1. 收集所有代理的输出
    web_content = self.extract_web_research_findings()
    image_references = self.get_generated_image_paths()
    
    # 2. 智能内容结构化
    structured_content = self.organize_content_structure({
        "产品概述": research_data.get("product_overview"),
        "技术规格": research_data.get("specifications"), 
        "产品特点": research_data.get("features"),
        "应用场景": research_data.get("use_cases"),
        "产品图片": image_references
    })
    
    # 3. 生成markdown文件
    markdown_file = self.generate_markdown(structured_content)
    return markdown_file
```

### 6️⃣ **HTML排版阶段 (Layout Design)**

**执行器**: `Coder Agent` (继续)
**模板**: 已修复的HTML模板 (避免 KeyError)

**排版策略**:
```python
# HTML 转换工作流 (已修复模板变量问题)
def convert_to_html(self, markdown_file):
    # 1. 读取markdown内容
    md_content = Path(markdown_file).read_text(encoding='utf-8')
    
    # 2. 使用修复后的HTML模板
    html_template = self.get_styled_html_template()  # 已修复 {{title}}, {{content}}
    
    # 3. 转换并嵌入样式
    html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])
    final_html = html_template.format(title="360全景相机产品介绍", content=html_content)
    
    # 4. 保存HTML文件
    html_file = 'product_introduction.html'
    Path(html_file).write_text(final_html, encoding='utf-8')
    return html_file
```

### 7️⃣ **最终格式输出阶段 (Final Output)**

**执行器**: `Coder Agent` (最终步骤)
**输出**: 根据用户需求的最终格式

**输出策略**:
```python
# PDF 生成工作流 (已修复模板变量)
def generate_final_output(self, html_file, output_format="pdf"):
    if output_format.lower() == "pdf":
        # 使用weasyprint转换为PDF
        import weasyprint
        pdf_file = 'product_introduction.pdf'
        weasyprint.HTML(filename=html_file).write_pdf(pdf_file)
        
        # 提供完成确认
        completion_message = f"✅ 文档创建任务已完成: {pdf_file}"
        file_size = Path(pdf_file).stat().st_size / 1024
        
        return {
            "output_file": pdf_file,
            "format": "PDF",
            "size_kb": round(file_size, 1),
            "completion_status": completion_message
        }
```

## 🔧 **关键修复点总结**

### ✅ **已修复问题**:
1. **KeyError: 'title', 'pdf_file'** → 模板变量正确转义
2. **Agent分配错误** → 强化分配规则和提示词
3. **循环操作问题** → 智能循环检测和预防
4. **任务序列混乱** → 逻辑依赖关系明确化

### 🎯 **Munas风格特色**:
1. **智能理解**: 深度解析用户意图和需求
2. **自主决策**: 各Agent自主完成任务，最小化用户干预
3. **协作协调**: Agent间智能信息传递和依赖管理
4. **质量导向**: 基于质量评分的任务完成判断
5. **适应性强**: 根据任务复杂度动态调整策略

## 📈 **预期工作流程**

对于用户请求: "生成360全景相机产品介绍，从te720.com获取信息，最终输出PDF"

```
用户请求 → Orchestrator分析
    ↓
规划5个步骤:
    1. web_surfer: 访问te720.com收集产品信息
    2. image_generator: 生成360相机CG图像  
    3. coder_agent: 创建markdown产品介绍
    4. coder_agent: 转换markdown为HTML
    5. coder_agent: 生成最终PDF文件
    ↓
按序执行 → 智能监控 → 质量验证 → 最终交付
```

这样设计的系统具备了类似Munas的智能协作能力，能够理解复杂需求、自主规划任务、智能分配资源，并高质量完成多模态任务。