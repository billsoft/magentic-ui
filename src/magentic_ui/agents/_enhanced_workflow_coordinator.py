"""
增强的工作流程协调器 - 专门处理多步骤复杂任务
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from loguru import logger

from ._enhanced_material_manager import EnhancedMaterialManager, MaterialItem
from ..types import Plan, PlanStep

@dataclass
class WorkflowStep:
    """工作流程步骤"""
    index: int
    plan_step: PlanStep
    status: str  # 'pending', 'in_progress', 'completed', 'failed', 'skipped'
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    materials: List[str] = None  # 素材ID列表
    
    def __post_init__(self):
        if self.materials is None:
            self.materials = []

@dataclass
class WorkflowContext:
    """工作流程上下文"""
    task_description: str
    steps: List[WorkflowStep]
    current_step_index: int = 0
    global_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.global_context is None:
            self.global_context = {}

class EnhancedWorkflowCoordinator:
    """增强的工作流程协调器"""
    
    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)
        self.material_manager = EnhancedMaterialManager(work_dir)
        self.context: Optional[WorkflowContext] = None
        self.completion_signals = {
            'step_completed': [
                "步骤已完成", "当前步骤已完成", "step completed", 
                "任务完成", "已完成", "完成了", "成功"
            ],
            'task_completed': [
                "整个任务已完成", "所有步骤已完成", "task completed",
                "全部完成", "工作流程完成"
            ],
            'step_failed': [
                "步骤失败", "执行失败", "step failed", 
                "错误", "失败", "无法完成"
            ]
        }
    
    def initialize_workflow(self, plan: Plan) -> None:
        """初始化工作流程"""
        steps = []
        for i, plan_step in enumerate(plan.steps):
            workflow_step = WorkflowStep(
                index=i,
                plan_step=plan_step,
                status='pending'
            )
            steps.append(workflow_step)
        
        self.context = WorkflowContext(
            task_description=plan.task or "未指定任务",
            steps=steps,
            current_step_index=0
        )
        
        logger.info(f"🚀 工作流程初始化: {len(steps)} 个步骤")
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """获取当前步骤"""
        if not self.context or self.context.current_step_index >= len(self.context.steps):
            return None
        return self.context.steps[self.context.current_step_index]
    
    def get_step_context(self, step_index: Optional[int] = None) -> str:
        """获取步骤上下文信息"""
        if not self.context:
            return "工作流程未初始化"
        
        if step_index is None:
            step_index = self.context.current_step_index
        
        context_parts = [
            f"📋 任务: {self.context.task_description}",
            f"📊 进度: {step_index + 1}/{len(self.context.steps)}",
            "",
            "🔄 当前步骤:"
        ]
        
        current_step = self.context.steps[step_index]
        context_parts.append(f"  {current_step.plan_step.agent_name}: {current_step.plan_step.title}")
        context_parts.append(f"  详情: {current_step.plan_step.details}")
        
        # 添加已完成步骤的总结
        completed_steps = [s for s in self.context.steps[:step_index] if s.status == 'completed']
        if completed_steps:
            context_parts.append("")
            context_parts.append("✅ 已完成步骤:")
            for step in completed_steps:
                context_parts.append(f"  - {step.plan_step.agent_name}: {step.plan_step.title}")
                if step.materials:
                    context_parts.append(f"    生成素材: {len(step.materials)} 个")
        
        # 添加素材上下文
        materials_context = self.material_manager.get_materials_context(step_index)
        if materials_context != "暂无可用素材":
            context_parts.append("")
            context_parts.append(materials_context)
        
        return "\n".join(context_parts)
    
    def start_step(self, step_index: Optional[int] = None) -> None:
        """开始步骤"""
        if not self.context:
            return
        
        if step_index is None:
            step_index = self.context.current_step_index
        
        if step_index < len(self.context.steps):
            step = self.context.steps[step_index]
            step.status = 'in_progress'
            step.start_time = datetime.now().isoformat()
            
            logger.info(f"🏁 开始步骤 {step_index + 1}: {step.plan_step.title}")
    
    def complete_step(self, 
                     step_index: Optional[int] = None, 
                     result: Optional[str] = None,
                     materials: Optional[List[str]] = None) -> bool:
        """完成步骤"""
        if not self.context:
            return False
        
        if step_index is None:
            step_index = self.context.current_step_index
        
        if step_index < len(self.context.steps):
            step = self.context.steps[step_index]
            step.status = 'completed'
            step.end_time = datetime.now().isoformat()
            step.result = result
            if materials:
                step.materials.extend(materials)
            
            logger.info(f"✅ 完成步骤 {step_index + 1}: {step.plan_step.title}")
            
            # 如果是当前步骤，移动到下一步
            if step_index == self.context.current_step_index:
                self.context.current_step_index += 1
                return True
        
        return False
    
    def fail_step(self, 
                  step_index: Optional[int] = None, 
                  error: Optional[str] = None) -> None:
        """标记步骤失败"""
        if not self.context:
            return
        
        if step_index is None:
            step_index = self.context.current_step_index
        
        if step_index < len(self.context.steps):
            step = self.context.steps[step_index]
            step.status = 'failed'
            step.end_time = datetime.now().isoformat()
            step.error = error
            
            logger.error(f"❌ 步骤 {step_index + 1} 失败: {step.plan_step.title}")
            if error:
                logger.error(f"    错误: {error}")
    
    def analyze_agent_message(self, message: str, agent_name: str) -> Dict[str, Any]:
        """分析代理消息，判断步骤状态"""
        message_lower = message.lower()
        
        # 检查完成信号
        step_completed = any(signal in message_lower for signal in self.completion_signals['step_completed'])
        task_completed = any(signal in message_lower for signal in self.completion_signals['task_completed'])
        step_failed = any(signal in message_lower for signal in self.completion_signals['step_failed'])
        
        # 检查是否包含素材信息
        has_image = any(keyword in message_lower for keyword in ['图', '图像', '图片', 'image', 'png', 'jpg'])
        has_markdown = any(keyword in message_lower for keyword in ['markdown', 'md', '文档'])
        has_html = any(keyword in message_lower for keyword in ['html', '网页', '排版'])
        has_pdf = any(keyword in message_lower for keyword in ['pdf', '文档'])
        
        return {
            'step_completed': step_completed,
            'task_completed': task_completed,
            'step_failed': step_failed,
            'has_materials': has_image or has_markdown or has_html or has_pdf,
            'material_types': {
                'image': has_image,
                'markdown': has_markdown,
                'html': has_html,
                'pdf': has_pdf
            },
            'agent_name': agent_name
        }
    
    def should_continue_workflow(self) -> bool:
        """判断是否应该继续工作流程"""
        if not self.context:
            return False
        
        # 检查是否还有未完成的步骤
        return self.context.current_step_index < len(self.context.steps)
    
    def get_workflow_summary(self) -> str:
        """获取工作流程总结"""
        if not self.context:
            return "工作流程未初始化"
        
        completed_count = sum(1 for s in self.context.steps if s.status == 'completed')
        failed_count = sum(1 for s in self.context.steps if s.status == 'failed')
        total_count = len(self.context.steps)
        
        summary_parts = [
            f"📊 工作流程总结",
            f"任务: {self.context.task_description}",
            f"进度: {completed_count}/{total_count} 已完成",
            f"失败: {failed_count} 个步骤",
            ""
        ]
        
        # 添加各步骤状态
        for i, step in enumerate(self.context.steps):
            status_emoji = {
                'completed': '✅',
                'failed': '❌',
                'in_progress': '⏳',
                'pending': '⏸️',
                'skipped': '⏭️'
            }
            
            emoji = status_emoji.get(step.status, '❓')
            summary_parts.append(f"{emoji} 步骤 {i + 1}: {step.plan_step.title}")
            
            if step.materials:
                summary_parts.append(f"    生成素材: {len(step.materials)} 个")
        
        return "\n".join(summary_parts)
    
    async def store_step_result(self, 
                              content: str, 
                              content_type: str,
                              step_index: Optional[int] = None,
                              filename: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """存储步骤结果"""
        if step_index is None:
            step_index = self.context.current_step_index if self.context else 0
        
        current_step = self.get_current_step()
        agent_name = current_step.plan_step.agent_name if current_step else "unknown"
        
        if content_type == 'image':
            material_id = await self.material_manager.store_image(
                content, step_index, agent_name, metadata=metadata
            )
        else:
            material_id = await self.material_manager.store_text(
                content, step_index, agent_name, content_type, filename, metadata
            )
        
        # 将素材ID添加到步骤
        if self.context and step_index < len(self.context.steps):
            self.context.steps[step_index].materials.append(material_id)
        
        return material_id
    
    def get_step_materials(self, step_index: Optional[int] = None) -> List[MaterialItem]:
        """获取步骤的素材"""
        if step_index is None:
            step_index = self.context.current_step_index if self.context else 0
        
        return self.material_manager.get_materials_by_step(step_index)
    
    def update_global_context(self, key: str, value: Any) -> None:
        """更新全局上下文"""
        if self.context:
            self.context.global_context[key] = value
    
    def get_global_context(self, key: str) -> Any:
        """获取全局上下文"""
        if self.context:
            return self.context.global_context.get(key)
        return None