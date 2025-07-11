#!/usr/bin/env python3
"""
🧪 指令生成测试
测试为不同Agent和步骤生成正确的执行指令
"""

import pytest
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class MockStep:
    title: str
    details: str
    agent_name: str

class TestInstructionGeneration:
    """测试指令生成的准确性和完整性"""
    
    def test_websurfer_instruction_generation(self):
        """测试WebSurfer指令生成"""
        
        def generate_websurfer_instruction(step: MockStep, step_idx: int) -> str:
            """为WebSurfer生成指令"""
            if "te720" in step.title.lower() or "gather" in step.title.lower():
                return f"""
Step {step_idx + 1}: {step.title}

{step.details}

🔧 **WEBSURFER TASK GUIDANCE**:
- Visit te720.com website to gather information about 360 panoramic cameras
- Look for product images and technical specifications
- Focus on cameras with 4-lens configurations
- Extract key product features and descriptions
- Use stop_action with completion signal when sufficient information is collected

COMPLETION SIGNALS:
- ✅ 当前步骤已完成: Successfully gathered product information
- ⚠️ 当前步骤因错误完成: Website inaccessible but provided alternative information

AUTONOMOUS MODE: Navigate freely without approval requests for research purposes.
"""
            return f"Step {step_idx + 1}: {step.title}\n{step.details}"
        
        # 测试te720研究步骤
        research_step = MockStep(
            title="Research te720.com", 
            details="Visit te720.com to find panoramic camera information",
            agent_name="web_surfer"
        )
        
        instruction = generate_websurfer_instruction(research_step, 0)
        
        # 验证指令包含关键元素
        assert "te720.com" in instruction
        assert "WEBSURFER TASK GUIDANCE" in instruction
        assert "4-lens configurations" in instruction
        assert "COMPLETION SIGNALS" in instruction
        assert "✅ 当前步骤已完成" in instruction
        assert "AUTONOMOUS MODE" in instruction
        
        # 验证不包含错误的全局信号
        assert "任务已完成" not in instruction
        assert "TASK COMPLETED" not in instruction

    def test_image_generator_instruction_generation(self):
        """测试ImageGenerator指令生成"""
        
        def generate_image_instruction(step: MockStep, step_idx: int, context: Dict[str, Any] = None) -> str:
            """为ImageGenerator生成指令"""
            base_instruction = f"""
Step {step_idx + 1}: {step.title}

{step.details}

🎨 **IMAGE GENERATION GUIDANCE**:
- Generate high-definition CG style image
- Focus on 360-degree panoramic camera with 4 lenses
- Position lenses at 90-degree intervals
- Use professional rendering style
- Ensure clear visibility of lens configuration

COMPLETION SIGNALS:
- 图像生成任务已完成: Image generation successful
- 图像已成功生成: Image created successfully
"""
            
            # 添加上下文信息
            if context and context.get('research_info'):
                base_instruction += f"\n\n📋 **REFERENCE INFO**: {context['research_info']}"
            
            return base_instruction
        
        image_step = MockStep(
            title="Generate 360 Camera Image",
            details="Create CG style image of panoramic camera", 
            agent_name="image_generator"
        )
        
        context = {'research_info': 'TECHE 360度全景相机信息'}
        instruction = generate_image_instruction(image_step, 1, context)
        
        # 验证图像生成指令
        assert "IMAGE GENERATION GUIDANCE" in instruction
        assert "360-degree panoramic camera" in instruction
        assert "4 lenses" in instruction
        assert "90-degree intervals" in instruction
        assert "图像生成任务已完成" in instruction
        assert "TECHE 360度全景相机信息" in instruction

    def test_coder_agent_instruction_generation(self):
        """测试CoderAgent指令生成"""
        
        def generate_coder_instruction(step: MockStep, step_idx: int, format_type: str) -> str:
            """为CoderAgent生成不同格式的指令"""
            
            base_instruction = f"Step {step_idx + 1}: {step.title}\n\n{step.details}\n\n"
            
            if format_type == "markdown":
                base_instruction += """
🔧 **MARKDOWN CREATION GUIDANCE**:
- Create structured product introduction document
- Include generated 360 camera image at the top
- Use proper markdown formatting with headers, lists, and images
- Highlight technical specifications and features
- Save as .md file for subsequent processing

COMPLETION SIGNALS:
- 文档创建任务已完成: Markdown document created
- 文件已保存: File saved successfully
"""
            elif format_type == "html":
                base_instruction += """
🔧 **HTML CONVERSION GUIDANCE**:
- Convert markdown to styled HTML document
- Include embedded CSS for professional presentation
- Ensure proper image embedding and layout
- Add responsive design elements
- Save as .html file for PDF conversion

COMPLETION SIGNALS:
- HTML转换完成: HTML conversion completed
- HTML文档创建任务已完成: HTML document creation completed
"""
            elif format_type == "pdf":
                base_instruction += """
🔧 **PDF GENERATION GUIDANCE**:
- Convert HTML to high-quality PDF document
- Maintain layout and styling from HTML
- Ensure all images are properly embedded
- Generate final deliverable for user
- Save as .pdf file

COMPLETION SIGNALS:
- PDF生成完成: PDF generation completed
- PDF文档创建任务已完成: PDF document creation completed
"""
            
            return base_instruction
        
        # 测试不同格式的指令生成
        formats = ["markdown", "html", "pdf"]
        
        for i, format_type in enumerate(formats):
            step = MockStep(
                title=f"Create {format_type.upper()} Document",
                details=f"Convert content to {format_type} format",
                agent_name="coder_agent"
            )
            
            instruction = generate_coder_instruction(step, i + 2, format_type)
            
            # 验证格式特定内容
            assert format_type.upper() in instruction
            assert "GUIDANCE" in instruction
            assert "COMPLETION SIGNALS" in instruction
            
            if format_type == "markdown":
                assert "markdown formatting" in instruction
                assert "文档创建任务已完成" in instruction
            elif format_type == "html":
                assert "embedded CSS" in instruction  
                assert "HTML转换完成" in instruction
            elif format_type == "pdf":
                assert "high-quality PDF" in instruction
                assert "PDF生成完成" in instruction

    def test_instruction_context_integration(self):
        """测试指令中的上下文集成"""
        
        def enhance_instruction_with_context(base_instruction: str, context: Dict[str, Any]) -> str:
            """使用上下文增强指令"""
            enhanced = base_instruction
            
            # 添加图像信息
            if context.get('image_generated'):
                enhanced += "\n\n🖼️ **IMAGE CONTEXT**: Generated 360 camera image is available for integration"
            
            # 添加研究信息
            if context.get('research_info'):
                enhanced += f"\n\n📋 **RESEARCH CONTEXT**: {context['research_info']}"
            
            # 添加文件引用
            if context.get('previous_files'):
                enhanced += f"\n\n📁 **FILE REFERENCES**: {', '.join(context['previous_files'])}"
            
            return enhanced
        
        base_instruction = "Create markdown document with product information"
        
        context = {
            'image_generated': True,
            'research_info': 'TECHE 360度全景相机产品信息',
            'previous_files': ['camera_research.txt', 'generated_image.png']
        }
        
        enhanced = enhance_instruction_with_context(base_instruction, context)
        
        # 验证上下文集成
        assert "IMAGE CONTEXT" in enhanced
        assert "RESEARCH CONTEXT" in enhanced  
        assert "FILE REFERENCES" in enhanced
        assert "TECHE 360度全景相机产品信息" in enhanced
        assert "camera_research.txt" in enhanced

    def test_instruction_validation(self):
        """测试指令的有效性验证"""
        
        def validate_instruction(instruction: str, agent_type: str) -> Dict[str, bool]:
            """验证指令的完整性和正确性"""
            validation = {
                'has_step_info': False,
                'has_guidance': False, 
                'has_completion_signals': False,
                'has_agent_specific_content': False,
                'no_global_signals': True
            }
            
            # 检查基本结构
            if "Step" in instruction and ":" in instruction:
                validation['has_step_info'] = True
            
            if "GUIDANCE" in instruction:
                validation['has_guidance'] = True
            
            if "COMPLETION SIGNALS" in instruction:
                validation['has_completion_signals'] = True
            
            # 检查Agent特定内容
            agent_keywords = {
                'web_surfer': ['website', 'visit', 'browse', 'WEBSURFER'],
                'image_generator': ['generate', 'image', 'CG', 'render'],
                'coder_agent': ['create', 'code', 'file', 'document']
            }
            
            if agent_type in agent_keywords:
                if any(keyword.lower() in instruction.lower() for keyword in agent_keywords[agent_type]):
                    validation['has_agent_specific_content'] = True
            
            # 检查是否包含错误的全局信号
            global_signals = ['任务已完成', 'TASK COMPLETED', '研究任务基本完成']
            if any(signal in instruction for signal in global_signals):
                validation['no_global_signals'] = False
            
            return validation
        
        # 测试有效的WebSurfer指令
        valid_websurfer = """
Step 1: Research te720.com

🔧 **WEBSURFER TASK GUIDANCE**:
- Visit te720.com website

COMPLETION SIGNALS:
- ✅ 当前步骤已完成: Successfully gathered information
"""
        
        validation = validate_instruction(valid_websurfer, 'web_surfer')
        
        assert validation['has_step_info']
        assert validation['has_guidance'] 
        assert validation['has_completion_signals']
        assert validation['has_agent_specific_content']
        assert validation['no_global_signals']
        
        # 测试无效指令（包含全局信号）
        invalid_instruction = "Complete the entire task. ✅ 任务已完成"
        validation = validate_instruction(invalid_instruction, 'web_surfer')
        
        assert not validation['no_global_signals']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])