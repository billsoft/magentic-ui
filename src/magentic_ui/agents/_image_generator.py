"""
AI图像生成代理 - 简化版，直接调用DALL-E API
"""

import logging
import asyncio
from typing import Any, AsyncGenerator, List, Sequence, Optional, Dict
import json
import base64
from datetime import datetime

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    BaseTextChatMessage,
    MultiModalMessage,
    TextMessage,
    ToolCallRequestEvent,
    ToolCallExecutionEvent,
)
from autogen_core import CancellationToken
from autogen_core.model_context import TokenLimitedChatCompletionContext
from autogen_core.models import ChatCompletionClient

from ..tools.image_generation import ImageGenerationClient, ImageGenerationConfig, ImageGenerationResult
from .visual_prompt_builder import visual_prompt_builder, VisualRequest

logger = logging.getLogger(__name__)

class ImageGeneratorAgent(BaseChatAgent):
    """专用AI图像生成代理 - 完全绕过聊天模型，直接调用DALL-E API"""
    
    def __init__(self, name: str, model_client: ChatCompletionClient, image_client: ImageGenerationClient):
        # 🔧 直接继承BaseChatAgent，完全控制逻辑
        super().__init__(name, "AI图像生成代理 - 专门负责调用DALL-E API生成图像")
        self.image_client = image_client
        # model_client参数保留以满足接口要求，但不使用
        
        logger.info(f"🎨 ImageGeneratorAgent初始化完成: {name}")
        logger.info(f"📡 图像客户端类型: {type(image_client)}")
        logger.info(f"🚀 完全绕过聊天模型，直接调用DALL-E API")
    
    @property
    def produced_message_types(self):
        """返回此代理产生的消息类型"""
        return (TextMessage, MultiModalMessage)
        
    async def on_messages(self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken) -> Response:
        """处理消息并生成图像 - 完全绕过AssistantAgent的默认行为"""
        try:
            logger.info(f"🎯 ImageGeneratorAgent.on_messages被调用 - 消息数量: {len(messages)}")
            
            # 提取用户需求
            user_request = self._extract_user_request(messages)
            if not user_request:
                logger.warning("未找到有效的用户请求")
                return self._create_text_response("请提供您的图像生成需求。")
            
            logger.info(f"🎨 收到图像生成请求: {user_request}")
            logger.info(f"🔧 强制使用DALL-E API，绕过聊天模型！")
            
            # 🔧 关键修复：始终调用图像生成，不管内容是什么
            # 因为到达这里就说明orchestrator已经确定需要图像生成
            logger.info(f"✅ 开始调用DALL-E API生成图像...")
            return await self._generate_image_directly(user_request)
                
        except Exception as e:
            logger.error(f"❌ 图像生成代理错误: {str(e)}")
            import traceback
            logger.error(f"错误追踪: {traceback.format_exc()}")
            return self._create_text_response(f"处理请求时出现错误: {str(e)}")
    
    def _extract_user_request(self, messages: Sequence[BaseChatMessage]) -> str:
        """提取用户请求"""
        for msg in reversed(messages):
            if hasattr(msg, 'source') and msg.source != self.name:
                if hasattr(msg, 'content'):
                    content = msg.content
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, list) and content:
                        # 如果是列表，提取文本部分
                        text_parts = [item for item in content if isinstance(item, str)]
                        return " ".join(text_parts) if text_parts else ""
        return ""
    
    def _is_image_request(self, request: str) -> bool:
        """简单判断是否是图像生成请求"""
        image_keywords = [
            "画", "绘", "生成", "创建", "制作", "设计", "图", "图像", "图片", 
            "照片", "相机", "产品", "概念", "插画", "logo", "draw", "generate", 
            "create", "image", "picture", "camera", "product"
        ]
        return any(keyword in request.lower() for keyword in image_keywords)
    
    async def _generate_image_directly(self, request: str) -> Response:
        """直接生成图像，不依赖复杂的分析"""
        try:
            # 🔧 简化：直接使用用户请求作为基础，进行简单优化
            optimized_prompt = self._optimize_prompt(request)
            
            logger.info(f"🚀 开始生成图像...")
            logger.info(f"📝 优化后提示词: {optimized_prompt}")
            
            # 配置图像生成参数
            config = ImageGenerationConfig(
                model="dall-e-3",
                size="1024x1024",
                quality="standard",
                style="vivid"
            )
            
            # 🔧 关键：直接调用图像生成API
            result = await self.image_client.generate_image(optimized_prompt, config)
            
            if result.success and (result.image_data or result.image_url):
                if result.image_data:
                    logger.info(f"✅ 图像生成成功 (base64)! 大小: {len(result.image_data)} 字符")
                elif result.image_url:
                    logger.info(f"✅ 图像生成成功 (URL): {result.image_url[:80]}...")
                    # 🔧 关键修复：如果是URL格式，下载并转换为base64
                    try:
                        result.image_data = await self._download_and_encode_image(result.image_url)
                        logger.info(f"✅ 图像下载转换成功! 大小: {len(result.image_data)} 字符")
                    except Exception as e:
                        logger.error(f"❌ 图像下载失败: {str(e)}")
                        return self._create_text_response(f"图像下载失败: {str(e)}")
                
                # 🔧 核心修复：直接返回前端能理解的格式
                return self._create_multimodal_response(request, result, optimized_prompt)
            else:
                error_msg = result.error_message or "图像生成失败"
                logger.error(f"❌ 图像生成失败: {error_msg}")
                return self._create_text_response(f"图像生成失败: {error_msg}")
                
        except Exception as e:
            logger.error(f"图像生成过程出错: {str(e)}")
            return self._create_text_response(f"图像生成过程出错: {str(e)}")
    
    def _optimize_prompt(self, request: str) -> str:
        """智能优化提示词，基于成功测试经验"""
        enhanced_parts = []
        
        # 🎯 核心需求（保持用户原意）
        enhanced_parts.append(request)
        
        # 🔧 基础质量增强（基于DALL-E最佳实践）
        quality_base = [
            "high quality", "detailed", "professional grade", 
            "sharp focus", "well-lit", "ultra-detailed"
        ]
        enhanced_parts.extend(quality_base)
        
        # 🎨 根据内容类型添加专业描述
        request_lower = request.lower()
        
        # 产品摄影风格
        if any(word in request_lower for word in ["相机", "camera", "产品", "product", "设备", "device"]):
            product_style = [
                "product photography", "studio lighting", "clean background",
                "commercial photography", "perfect lighting", "professional product shot"
            ]
            enhanced_parts.extend(product_style)
        
        # 全景相机特殊优化
        if any(word in request_lower for word in ["全景", "panoramic", "360", "镜头", "lens"]):
            panoramic_style = [
                "modern camera design", "sleek technology", "multiple lens system",
                "premium electronics", "cutting-edge technology"
            ]
            enhanced_parts.extend(panoramic_style)
        
        # 艺术创作风格
        elif any(word in request_lower for word in ["艺术", "art", "创意", "creative", "概念", "concept"]):
            artistic_style = [
                "artistic composition", "creative design", "conceptual art",
                "masterpiece quality", "award-winning design"
            ]
            enhanced_parts.extend(artistic_style)
        
        # 摄影技术增强
        photo_tech = [
            "8k resolution", "photorealistic", "cinematic lighting",
            "perfect composition", "professional photography"
        ]
        enhanced_parts.extend(photo_tech)
        
        # 🎭 最终优化：去重并构建
        final_prompt = ", ".join(dict.fromkeys(enhanced_parts))  # 去重
        
        logger.info(f"📝 提示词优化: {request} → {final_prompt[:100]}...")
        return final_prompt
    
    async def _download_and_encode_image(self, image_url: str) -> str:
        """下载图像并编码为base64"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    return base64.b64encode(image_bytes).decode('utf-8')
                else:
                    raise Exception(f"下载图像失败: HTTP {response.status}")
    
    def _create_multimodal_response(self, original_request: str, result: ImageGenerationResult, prompt: str) -> Response:
        """创建包含图像的多模态响应"""
        # 🔧 关键修复：构建前端能理解的格式
        text_content = f"""✅ **图像生成完成**

**原始需求**: {original_request}
**优化提示词**: {prompt}
**生成模型**: {result.model_used}
**生成时间**: {result.generation_time:.2f}秒"""
        
        # 🔧 核心：直接创建前端期望的ImageContent格式
        image_content = {
            "data": result.image_data,  # 直接传递base64数据
            "alt": f"4镜头全景相机" if "全景相机" in original_request else f"Generated: {original_request[:30]}..."
        }
        
        # 🔧 构建MultiModalMessage，content为[string, dict]格式
        content = [text_content, image_content]
        
        logger.info(f"📤 返回多模态消息 - 文本长度: {len(text_content)}, 图像数据长度: {len(result.image_data)}")
        
        return Response(chat_message=MultiModalMessage(
            content=content,
            source=self.name,
            metadata={"type": "image_generation", "internal": "no"}
        ))
    
    def _create_text_response(self, text: str) -> Response:
        """创建文本响应"""
        return Response(chat_message=TextMessage(
            content=text,
            source=self.name
        ))
    
    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """重置ImageGeneratorAgent状态 - BaseChatAgent要求的抽象方法"""
        # 对于图像生成代理，我们不需要保存状态，所以这个方法为空
        logger.info(f"🔄 {self.name} 已重置")
        pass 