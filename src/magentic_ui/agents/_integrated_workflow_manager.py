"""
集成的工作流程管理器 - 整合所有增强组件
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from loguru import logger
from datetime import datetime

from ._enhanced_workflow_coordinator import EnhancedWorkflowCoordinator
from ._enhanced_material_manager import EnhancedMaterialManager
from ._enhanced_web_surfer import EnhancedWebSurferAgent
from ._enhanced_image_generator import EnhancedImageGeneratorAgent
from ._enhanced_coder import EnhancedCoderAgent
from ..types import Plan, PlanStep

class IntegratedWorkflowManager:
    """集成的工作流程管理器"""
    
    def __init__(self, work_dir: Path, team_config: Dict[str, Any]):
        self.work_dir = Path(work_dir)
        self.team_config = team_config
        
        # 初始化核心组件
        self.coordinator = EnhancedWorkflowCoordinator(work_dir)
        self.material_manager = self.coordinator.material_manager
        
        # 增强的代理实例
        self.enhanced_agents: Dict[str, Any] = {}
        
        logger.info(f"🚀 集成工作流程管理器初始化: {work_dir}")
    
    def initialize_enhanced_agents(self, original_agents: Dict[str, Any]) -> None:
        """初始化增强的代理"""
        try:
            # 增强WebSurfer
            if 'web_surfer' in original_agents:
                web_surfer = original_agents['web_surfer']
                enhanced_web_surfer = EnhancedWebSurferAgent(
                    name=web_surfer.name,
                    model_client=web_surfer._model_client,
                    workflow_coordinator=self.coordinator,
                    **self._extract_web_surfer_config(web_surfer)
                )
                self.enhanced_agents['web_surfer'] = enhanced_web_surfer
                logger.info("🌐 增强WebSurfer已初始化")
            
            # 增强ImageGenerator
            if 'image_generator' in original_agents:
                image_gen = original_agents['image_generator']
                enhanced_image_gen = EnhancedImageGeneratorAgent(
                    name=image_gen.name,
                    model_client=image_gen._model_client,
                    image_client=image_gen.image_client,
                    workflow_coordinator=self.coordinator
                )
                self.enhanced_agents['image_generator'] = enhanced_image_gen
                logger.info("🎨 增强ImageGenerator已初始化")
            
            # 增强Coder
            if 'coder' in original_agents:
                coder = original_agents['coder']
                enhanced_coder = EnhancedCoderAgent(
                    name=coder.name,
                    model_client=coder._model_client,
                    workflow_coordinator=self.coordinator,
                    **self._extract_coder_config(coder)
                )
                self.enhanced_agents['coder'] = enhanced_coder
                logger.info("💻 增强Coder已初始化")
            
        except Exception as e:
            logger.error(f"❌ 初始化增强代理失败: {e}")
            raise
    
    def _extract_web_surfer_config(self, web_surfer) -> Dict[str, Any]:
        """提取WebSurfer配置"""
        return {
            'description': getattr(web_surfer, 'description', ''),
            'browser_config': getattr(web_surfer, 'browser_config', {}),
            'single_tab_mode': getattr(web_surfer, 'single_tab_mode', True),
            'start_page': getattr(web_surfer, 'start_page', 'about:blank'),
            'downloads_folder': getattr(web_surfer, 'downloads_folder', None),
            'viewport': getattr(web_surfer, 'viewport', {'width': 1440, 'height': 900}),
            'playwright_controller': getattr(web_surfer, '_playwright_controller', None)
        }
    
    def _extract_coder_config(self, coder) -> Dict[str, Any]:
        """提取Coder配置"""
        return {
            'description': getattr(coder, 'description', ''),
            'max_debug_rounds': getattr(coder, '_max_debug_rounds', 3),
            'summarize_output': getattr(coder, '_summarize_output', False),
            'work_dir': getattr(coder, '_work_dir', None),
            'code_executor': getattr(coder, '_code_executor', None),
            'approval_guard': getattr(coder, '_approval_guard', None)
        }
    
    def start_workflow(self, plan: Plan) -> None:
        """启动工作流程"""
        try:
            self.coordinator.initialize_workflow(plan)
            logger.info(f"🎯 工作流程已启动: {plan.task}")
            
            # 为每个步骤重置代理状态
            for agent in self.enhanced_agents.values():
                if hasattr(agent, 'reset_loop_detection'):
                    agent.reset_loop_detection()
            
        except Exception as e:
            logger.error(f"❌ 启动工作流程失败: {e}")
            raise
    
    def get_next_agent(self) -> Optional[Any]:
        """获取下一个要执行的代理"""
        current_step = self.coordinator.get_current_step()
        if not current_step:
            return None
        
        agent_name = current_step.plan_step.agent_name.lower()
        
        # 映射代理名称
        agent_mapping = {
            'websurfer': 'web_surfer',
            'web_surfer': 'web_surfer',
            'image_generator': 'image_generator',
            'imagegenerator': 'image_generator',
            'coder': 'coder',
            'coderAgent': 'coder',
            'file_surfer': 'file_surfer'
        }
        
        mapped_name = agent_mapping.get(agent_name, agent_name)
        
        # 优先返回增强的代理
        if mapped_name in self.enhanced_agents:
            agent = self.enhanced_agents[mapped_name]
            logger.info(f"🔄 使用增强代理: {mapped_name}")
            return agent
        
        logger.warning(f"⚠️ 未找到增强代理: {mapped_name}")
        return None
    
    def process_agent_response(self, agent_name: str, response: Any) -> Dict[str, Any]:
        """处理代理响应"""
        try:
            # 分析响应内容
            response_content = ""
            if hasattr(response, 'content'):
                response_content = response.content
            elif hasattr(response, 'messages') and response.messages:
                response_content = response.messages[-1].content if response.messages[-1].content else ""
            
            # 使用协调器分析消息
            analysis = self.coordinator.analyze_agent_message(response_content, agent_name)
            
            # 处理步骤完成
            if analysis['step_completed']:
                logger.info(f"✅ 步骤完成信号: {agent_name}")
                self.coordinator.complete_step(result=response_content)
            
            # 处理步骤失败
            elif analysis['step_failed']:
                logger.error(f"❌ 步骤失败信号: {agent_name}")
                self.coordinator.fail_step(error=response_content)
            
            # 处理任务完成
            elif analysis['task_completed']:
                logger.info(f"🎉 任务完成信号: {agent_name}")
                self.coordinator.complete_step(result=response_content)
                # 这里可以添加额外的任务完成处理
            
            return {
                'success': True,
                'analysis': analysis,
                'should_continue': self.coordinator.should_continue_workflow()
            }
            
        except Exception as e:
            logger.error(f"❌ 处理代理响应失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'should_continue': False
            }
    
    def get_current_context(self) -> str:
        """获取当前上下文"""
        return self.coordinator.get_step_context()
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流程状态"""
        current_step = self.coordinator.get_current_step()
        
        status = {
            'current_step': current_step.index if current_step else None,
            'current_step_title': current_step.plan_step.title if current_step else None,
            'current_agent': current_step.plan_step.agent_name if current_step else None,
            'total_steps': len(self.coordinator.context.steps) if self.coordinator.context else 0,
            'completed_steps': 0,
            'failed_steps': 0,
            'materials_count': len(self.material_manager.materials),
            'should_continue': self.coordinator.should_continue_workflow()
        }
        
        if self.coordinator.context:
            status['completed_steps'] = sum(1 for s in self.coordinator.context.steps if s.status == 'completed')
            status['failed_steps'] = sum(1 for s in self.coordinator.context.steps if s.status == 'failed')
        
        return status
    
    def get_generated_materials(self) -> List[Dict[str, Any]]:
        """获取生成的素材列表"""
        materials = []
        
        for material_id, material in self.material_manager.materials.items():
            materials.append({
                'id': material_id,
                'type': material.type,
                'step_index': material.step_index,
                'agent_name': material.agent_name,
                'created_at': material.created_at,
                'metadata': material.metadata
            })
        
        return sorted(materials, key=lambda x: x['created_at'], reverse=True)
    
    def get_final_outputs(self) -> Dict[str, Any]:
        """获取最终输出"""
        final_outputs = {
            'summary': self.coordinator.get_workflow_summary(),
            'materials': self.get_generated_materials(),
            'status': self.get_workflow_status(),
            'generated_files': []
        }
        
        # 检查生成的文件
        output_dir = self.work_dir / "generated_documents"
        if output_dir.exists():
            for file_path in output_dir.glob("*"):
                if file_path.is_file():
                    final_outputs['generated_files'].append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'type': file_path.suffix.lstrip('.')
                    })
        
        return final_outputs
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 清理代理资源
            for agent in self.enhanced_agents.values():
                if hasattr(agent, 'cleanup'):
                    agent.cleanup()
            
            # 清理过期素材
            asyncio.run(self.material_manager.cleanup_old_materials())
            
            logger.info("🧹 工作流程管理器清理完成")
            
        except Exception as e:
            logger.error(f"❌ 清理失败: {e}")
    
    def force_complete_current_step(self, reason: str = "手动完成") -> bool:
        """强制完成当前步骤"""
        try:
            current_step = self.coordinator.get_current_step()
            if current_step:
                self.coordinator.complete_step(result=f"强制完成: {reason}")
                logger.info(f"🔧 强制完成步骤: {current_step.plan_step.title}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 强制完成步骤失败: {e}")
            return False
    
    def skip_current_step(self, reason: str = "跳过步骤") -> bool:
        """跳过当前步骤"""
        try:
            current_step = self.coordinator.get_current_step()
            if current_step:
                current_step.status = 'skipped'
                current_step.result = f"跳过: {reason}"
                current_step.end_time = datetime.now().isoformat()
                
                if self.coordinator.context:
                    self.coordinator.context.current_step_index += 1
                
                logger.info(f"⏭️ 跳过步骤: {current_step.plan_step.title}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 跳过步骤失败: {e}")
            return False