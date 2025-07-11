#!/usr/bin/env python3
"""
🧪 Agent间协作流程测试
测试多Agent之间的工作流衔接和数据传递
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, List, Any, Optional

class MockAgent:
    def __init__(self, name: str, response_template: str):
        self.name = name
        self.response_template = response_template
        self.received_instructions = []
        self.execution_count = 0
    
    async def execute(self, instruction: str) -> str:
        self.received_instructions.append(instruction)
        self.execution_count += 1
        return self.response_template.format(
            step=self.execution_count,
            instruction=instruction[:50]
        )

class MockOrchestrator:
    def __init__(self):
        self.current_step = 0
        self.steps = []
        self.execution_log = []
        self.context = {}
    
    async def execute_step(self, agent: MockAgent, instruction: str) -> tuple[bool, str]:
        """执行单个步骤并返回(成功状态, 响应)"""
        response = await agent.execute(instruction)
        self.execution_log.append({
            'step': self.current_step,
            'agent': agent.name,
            'instruction': instruction,
            'response': response
        })
        
        # 模拟完成检查
        is_complete = "完成" in response or "completed" in response
        if is_complete:
            self.current_step += 1
        
        return is_complete, response

class TestAgentCollaboration:
    """测试Agent协作流程"""
    
    @pytest.mark.asyncio
    async def test_websurfer_to_image_generator_flow(self):
        """测试WebSurfer到ImageGenerator的数据传递"""
        
        # 创建模拟Agent
        websurfer = MockAgent(
            "web_surfer",
            "✅ 当前步骤已完成：已访问te720.com，发现TECHE 360度全景相机产品信息"
        )
        
        image_generator = MockAgent(
            "image_generator", 
            "图像生成任务已完成：已生成360度4镜头全景相机的CG风格图像"
        )
        
        orchestrator = MockOrchestrator()
        
        # 执行步骤1：WebSurfer研究
        step1_instruction = "访问te720.com收集360度全景相机信息"
        success1, response1 = await orchestrator.execute_step(websurfer, step1_instruction)
        
        assert success1, "WebSurfer步骤应该成功完成"
        assert "te720.com" in response1, "WebSurfer响应应包含网站信息"
        assert orchestrator.current_step == 1, "步骤应该推进到1"
        
        # 提取上下文信息（模拟信息传递）
        orchestrator.context['research_info'] = "TECHE 360度全景相机产品信息"
        
        # 执行步骤2：ImageGenerator生成
        step2_instruction = f"基于研究信息生成360度相机图像：{orchestrator.context['research_info']}"
        success2, response2 = await orchestrator.execute_step(image_generator, step2_instruction)
        
        assert success2, "ImageGenerator步骤应该成功完成"
        assert "图像生成" in response2, "ImageGenerator响应应包含生成确认"
        assert orchestrator.current_step == 2, "步骤应该推进到2"

    @pytest.mark.asyncio 
    async def test_complete_workflow_integration(self):
        """测试完整工作流程的集成"""
        
        # 创建完整的Agent链
        agents = {
            'web_surfer': MockAgent("web_surfer", "✅ 当前步骤已完成：收集了360相机信息"),
            'image_generator': MockAgent("image_generator", "图像生成任务已完成：创建了CG风格图像"),
            'coder_agent_md': MockAgent("coder_agent", "文档创建任务已完成：生成了markdown文件"),
            'coder_agent_html': MockAgent("coder_agent", "HTML转换完成：创建了styled HTML"),
            'coder_agent_pdf': MockAgent("coder_agent", "PDF生成完成：输出了最终PDF文件")
        }
        
        # 定义工作流步骤
        workflow = [
            ('web_surfer', "访问te720.com研究360度全景相机"),
            ('image_generator', "生成360度4镜头相机的CG图像"),
            ('coder_agent_md', "创建包含图像的产品介绍markdown"),
            ('coder_agent_html', "转换markdown为styled HTML"),
            ('coder_agent_pdf', "将HTML转换为最终PDF")
        ]
        
        orchestrator = MockOrchestrator()
        context = {}
        
        # 执行完整工作流
        for step_idx, (agent_name, instruction) in enumerate(workflow):
            agent = agents[agent_name]
            
            # 添加上下文信息到指令
            if step_idx > 0:
                instruction += f" [基于前面步骤的结果: {len(context)}项信息]"
            
            success, response = await orchestrator.execute_step(agent, instruction)
            
            assert success, f"步骤{step_idx + 1}应该成功完成"
            
            # 模拟上下文累积
            context[f'step_{step_idx}'] = response
            
            # 验证步骤推进
            assert orchestrator.current_step == step_idx + 1
        
        # 验证完整流程执行
        assert len(orchestrator.execution_log) == 5, "应该执行了5个步骤"
        assert orchestrator.current_step == 5, "最终应该完成所有步骤"
        
        # 验证每个Agent都被调用
        for agent_name, agent in agents.items():
            assert agent.execution_count > 0, f"{agent_name}应该被执行"

    def test_context_data_propagation(self):
        """测试上下文数据在步骤间的传播"""
        
        class ContextManager:
            def __init__(self):
                self.global_context = {}
                self.step_outputs = {}
            
            def update_context(self, step: int, agent: str, output: str):
                """更新步骤上下文"""
                self.step_outputs[step] = {
                    'agent': agent,
                    'output': output,
                    'timestamp': f"time_{step}"
                }
                
                # 提取关键信息到全局上下文
                if "image" in output.lower() and "生成" in output:
                    self.global_context['image_generated'] = True
                    self.global_context['image_info'] = output
                elif "图像" in output and "生成" in output:
                    self.global_context['image_generated'] = True
                    self.global_context['image_info'] = output
                
                if "te720" in output.lower():
                    self.global_context['research_completed'] = True
                    self.global_context['research_info'] = output
            
            def get_context_for_step(self, step: int) -> Dict[str, Any]:
                """获取特定步骤的可用上下文"""
                available_context = {}
                
                # 包含所有之前步骤的输出
                for prev_step in range(step):
                    if prev_step in self.step_outputs:
                        available_context[f'prev_step_{prev_step}'] = self.step_outputs[prev_step]
                
                # 包含全局上下文
                available_context.update(self.global_context)
                
                return available_context
        
        # 测试上下文管理
        ctx_mgr = ContextManager()
        
        # 模拟步骤执行和上下文更新
        ctx_mgr.update_context(0, "web_surfer", "✅ 已访问te720.com收集产品信息")
        ctx_mgr.update_context(1, "image_generator", "图像生成任务已完成")
        
        # 验证上下文传播
        step2_context = ctx_mgr.get_context_for_step(2)
        
        assert step2_context['research_completed'] == True
        assert step2_context['image_generated'] == True
        assert 'prev_step_0' in step2_context
        assert 'prev_step_1' in step2_context
        
        # 验证上下文用于后续步骤指令生成
        def generate_instruction_with_context(base_instruction: str, context: Dict[str, Any]) -> str:
            enhanced_instruction = base_instruction
            
            if context.get('research_completed'):
                enhanced_instruction += " [基于te720.com研究结果]"
            
            if context.get('image_generated'):
                enhanced_instruction += " [包含已生成的360度相机图像]"
            
            return enhanced_instruction
        
        instruction = generate_instruction_with_context(
            "创建产品介绍markdown文档", 
            step2_context
        )
        
        assert "[基于te720.com研究结果]" in instruction
        assert "[包含已生成的360度相机图像]" in instruction

if __name__ == "__main__":
    pytest.main([__file__, "-v"])