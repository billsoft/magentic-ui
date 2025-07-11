"""
增强的图像生成器 - 改进存储和传递机制
"""

import base64
import json
from typing import Any, Dict, List, Optional, Sequence
from loguru import logger
from pathlib import Path
from datetime import datetime

from ._image_generator import ImageGeneratorAgent
from .._enhanced_workflow_coordinator import EnhancedWorkflowCoordinator
from ..tools.image_generation import ImageGenerationClient, ImageGenerationConfig

class EnhancedImageGeneratorAgent(ImageGeneratorAgent):
    """增强的图像生成器"""
    
    def __init__(self, name: str, model_client, image_client: ImageGenerationClient, 
                 workflow_coordinator: Optional[EnhancedWorkflowCoordinator] = None):
        super().__init__(name, model_client, image_client)
        self.workflow_coordinator = workflow_coordinator
        
        # 图像生成配置
        self.generation_config = {
            'auto_store': True,  # 自动存储生成的图像
            'include_metadata': True,  # 包含元数据
            'generate_variations': False,  # 生成变体
            'quality_check': True,  # 质量检查
        }
        
        logger.info(f"🎨 增强图像生成器初始化: {name}")
    
    def _extract_enhanced_image_request(self, messages: Sequence) -> Dict[str, Any]:
        """提取增强的图像请求信息"""
        request_info = {
            'prompt': '',
            'style_hints': [],
            'technical_requirements': {},
            'context_info': {}
        }
        
        # 提取用户请求
        for msg in reversed(messages):
            if hasattr(msg, 'source') and msg.source != self.name:
                if hasattr(msg, 'content'):
                    content = msg.content
                    if isinstance(content, str):
                        request_info['prompt'] = content
                        break
        
        # 分析请求内容
        prompt = request_info['prompt'].lower()
        
        # 提取风格提示
        style_keywords = {
            'cg': ['cg', 'computer graphics', '电脑图形'],
            'realistic': ['realistic', '真实', '写实'],
            'cartoon': ['cartoon', '卡通', '动画'],
            'technical': ['technical', '技术', '工程'],
            'product': ['product', '产品', '商品'],
            'professional': ['professional', '专业', '商业']
        }
        
        for style, keywords in style_keywords.items():
            if any(keyword in prompt for keyword in keywords):
                request_info['style_hints'].append(style)
        
        # 提取技术要求
        if any(keyword in prompt for keyword in ['高清', 'hd', 'high quality', '4k']):
            request_info['technical_requirements']['quality'] = 'hd'
        
        if any(keyword in prompt for keyword in ['360', '全景', 'panoramic']):
            request_info['technical_requirements']['type'] = 'panoramic'
        
        # 提取产品信息
        if any(keyword in prompt for keyword in ['相机', 'camera', '镜头', 'lens']):
            request_info['context_info']['product_type'] = 'camera'
        
        return request_info
    
    def _build_enhanced_prompt(self, request_info: Dict[str, Any]) -> str:
        """构建增强的提示词"""
        base_prompt = request_info['prompt']
        
        # 添加风格增强
        style_enhancements = {
            'cg': ", high-quality CG render, 3D computer graphics, professional lighting",
            'realistic': ", photorealistic, high detail, professional photography",
            'product': ", product photography, clean background, professional lighting, commercial quality",
            'technical': ", technical illustration, precise details, engineering drawing style"
        }
        
        enhanced_prompt = base_prompt
        for style in request_info['style_hints']:
            if style in style_enhancements:
                enhanced_prompt += style_enhancements[style]
        
        # 添加质量增强
        if request_info['technical_requirements'].get('quality') == 'hd':
            enhanced_prompt += ", 4K resolution, ultra-high definition, crisp details"
        
        # 添加通用质量提升
        enhanced_prompt += ", professional quality, detailed, well-composed"
        
        logger.info(f"🎯 增强提示词: {enhanced_prompt}")
        return enhanced_prompt
    
    def _generate_image_metadata(self, request_info: Dict[str, Any], generation_result: Any) -> Dict[str, Any]:
        """生成图像元数据"""
        metadata = {
            'generation_time': datetime.now().isoformat(),
            'original_prompt': request_info['prompt'],
            'style_hints': request_info['style_hints'],
            'technical_requirements': request_info['technical_requirements'],
            'context_info': request_info['context_info'],
            'generation_config': {
                'model': 'dall-e-3',
                'quality': 'standard',
                'style': 'vivid',
                'size': '1024x1024'
            }
        }
        
        # 添加生成结果信息
        if hasattr(generation_result, 'model_used'):
            metadata['generation_config']['model'] = generation_result.model_used
        
        return metadata
    
    async def _store_generated_image(self, image_data: str, metadata: Dict[str, Any]) -> Optional[str]:
        """存储生成的图像"""
        if not self.workflow_coordinator:
            logger.warning("⚠️ 未配置工作流程协调器，无法存储图像")
            return None
        
        try:
            # 获取当前步骤信息
            current_step = self.workflow_coordinator.get_current_step()
            step_index = current_step.index if current_step else 0
            
            # 存储图像
            material_id = await self.workflow_coordinator.store_step_result(
                content=image_data,
                content_type='image',
                step_index=step_index,
                filename=f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                metadata=metadata
            )
            
            logger.info(f"🖼️ 图像已存储: {material_id}")
            return material_id
            
        except Exception as e:
            logger.error(f"❌ 存储图像失败: {e}")
            return None
    
    def _create_enhanced_response(self, image_data: str, material_id: Optional[str], metadata: Dict[str, Any]) -> Any:
        """创建增强的响应"""
        # 基础响应信息
        response_content = "🎨 图像生成完成！\n\n"
        
        # 添加技术信息
        if metadata.get('style_hints'):
            response_content += f"🎭 风格: {', '.join(metadata['style_hints'])}\n"
        
        if metadata.get('technical_requirements'):
            response_content += f"⚙️ 技术要求: {metadata['technical_requirements']}\n"
        
        # 添加存储信息
        if material_id:
            response_content += f"📁 素材ID: {material_id}\n"
            response_content += "✅ 图像已自动保存到工作流程中\n"
        
        response_content += "\n🔄 图像已准备就绪，可以继续下一步骤"
        
        # 创建多模态响应（包含图像）
        try:
            from autogen_agentchat.messages import MultiModalMessage
            from autogen_core import Image as AGImage
            import io
            import PIL.Image
            
            # 解码图像
            image_bytes = base64.b64decode(image_data)
            image = PIL.Image.open(io.BytesIO(image_bytes))
            
            # 创建AutoGen图像对象
            ag_image = AGImage(image)
            
            # 创建多模态消息
            response = MultiModalMessage(
                content=[response_content, ag_image],
                source=self.name
            )
            
            logger.info("🖼️ 创建多模态响应成功")
            return self._create_text_response(response_content)
            
        except Exception as e:
            logger.error(f"❌ 创建多模态响应失败: {e}")
            return self._create_text_response(response_content)
    
    async def _generate_image_directly(self, request: str) -> Any:
        """重写的直接图像生成方法"""
        try:
            logger.info(f"🎨 开始图像生成: {request}")
            
            # 提取请求信息
            request_info = self._extract_enhanced_image_request([type('Message', (), {'content': request, 'source': 'user'})()])
            
            # 构建增强提示词
            enhanced_prompt = self._build_enhanced_prompt(request_info)
            
            # 生成图像
            config = ImageGenerationConfig(
                model="dall-e-3",
                size="1024x1024",
                quality="standard",
                style="vivid",
                response_format="b64_json"
            )
            
            generation_result = await self.image_client.generate_image(enhanced_prompt, config)
            
            if not generation_result.success:
                error_msg = f"❌ 图像生成失败: {generation_result.error_message}"
                logger.error(error_msg)
                return self._create_text_response(error_msg)
            
            # 生成元数据
            metadata = self._generate_image_metadata(request_info, generation_result)
            
            # 存储图像
            material_id = None
            if self.generation_config['auto_store']:
                material_id = await self._store_generated_image(generation_result.image_data, metadata)
            
            # 创建响应
            response = self._create_enhanced_response(generation_result.image_data, material_id, metadata)
            
            # 更新工作流程状态
            if self.workflow_coordinator:
                current_step = self.workflow_coordinator.get_current_step()
                if current_step:
                    materials = [material_id] if material_id else []
                    self.workflow_coordinator.complete_step(
                        result=f"图像生成任务已完成 - {enhanced_prompt}",
                        materials=materials
                    )
            
            logger.info("✅ 图像生成和处理完成")
            return response
            
        except Exception as e:
            logger.error(f"❌ 图像生成过程错误: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            
            # 标记步骤失败
            if self.workflow_coordinator:
                self.workflow_coordinator.fail_step(error=str(e))
            
            return self._create_text_response(f"图像生成失败: {str(e)}")
    
    def get_generation_summary(self) -> str:
        """获取生成总结"""
        if not self.workflow_coordinator:
            return "无工作流程信息"
        
        # 获取图像类型的素材
        image_materials = self.workflow_coordinator.material_manager.get_materials_by_type('image')
        
        if not image_materials:
            return "暂无生成的图像"
        
        summary = f"🎨 图像生成总结:\n"
        summary += f"  生成数量: {len(image_materials)}\n"
        
        for material in image_materials[-3:]:  # 显示最近3个
            summary += f"  - {material.id}: {material.metadata.get('style_hints', '未知风格')}\n"
        
        return summary