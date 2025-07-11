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
from ..utils.conversation_storage_manager import add_conversation_file

logger = logging.getLogger(__name__)

class ImageGeneratorAgent(BaseChatAgent):
    """专用AI图像生成代理 - 完全绕过聊天模型，直接调用DALL-E API"""
    
    def __init__(self, name: str, model_client: ChatCompletionClient, image_client: ImageGenerationClient, session_id: int = None):
        # 🔧 直接继承BaseChatAgent，完全控制逻辑
        super().__init__(name, "AI图像生成代理 - 专门负责调用DALL-E API生成图像")
        self.image_client = image_client
        self.session_id = session_id  # 🔧 新增：对话会话ID
        # model_client参数保留以满足接口要求，但不使用
        
        logger.info(f"🎨 ImageGeneratorAgent初始化完成: {name}")
        logger.info(f"📡 图像客户端类型: {type(image_client)}")
        logger.info(f"📁 对话会话ID: {session_id}")
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
            
            # 🚀 2025最新DALL-E 3最佳配置
            config = ImageGenerationConfig(
                model="dall-e-3",  # ✅ 确认使用最新版本
                size="1792x1024",  # 🔧 横向格式，更适合产品展示
                quality="hd",      # 🔧 高清模式，更佳细节
                style="vivid"      # 🔧 戏剧化风格，更生动
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
                
                # 🔧 新增：保存图像到对话级存储
                await self._save_to_conversation_storage(result, optimized_prompt)
                
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
        """🎨 智能提示词优化系统 - 根据用户需求自动选择最佳绘图风格"""
        enhanced_parts = []
        request_lower = request.lower()
        
        # 🎯 风格识别矩阵
        style_keywords = {
            "简图": ["简图", "简单", "简洁", "线条图", "示意图", "草图", "概念图"],
            "线条图": ["线条", "线稿", "轮廓", "素描", "手绘", "铅笔画"],
            "3D渲染": ["3d", "三维", "立体", "渲染", "建模", "cg", "三d"],
            "照片级": ["照片", "真实", "高清", "写实", "逼真", "实物", "产品图"],
            "科技风": ["科技", "未来", "科幻", "电子", "数字", "智能", "现代"],
            "工业设计": ["工业", "产品设计", "设计图", "专业", "产品"],
            "概念艺术": ["概念", "艺术", "创意", "想象", "幻想"]
        }
        
        # 🔍 识别用户偏好的绘图风格
        detected_styles = []
        for style, keywords in style_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                detected_styles.append(style)
        
        # 🖼️ 特殊主题优化（全景相机、折叠手机等）
        if any(word in request_lower for word in ["全景相机", "全景", "panoramic camera", "360相机", "4镜头", "四镜头", "多镜头"]):
            panoramic_desc = [
                "A professional 360-degree panoramic camera with exactly 4 visible camera lenses",
                "spherical or cylindrical body design specifically for panoramic photography", 
                "four distinct ultra-wide-angle lenses positioned strategically around the device",
                "modern VR camera technology for immersive content creation",
                "compact multi-lens system with visible lens details and professional grade build quality"
            ]
            enhanced_parts.extend(panoramic_desc)
            
        elif any(word in request_lower for word in ["折叠屏", "折叠手机", "foldable", "fold", "flip", "多屏", "4屏"]):
            foldable_desc = [
                "Advanced foldable smartphone with multiple flexible OLED screens",
                "innovative hinge mechanism and seamless folding design",
                "multiple screen panels that unfold into larger display surface",
                "premium materials with sophisticated engineering details",
                "next-generation mobile device technology showcase"
            ]
            enhanced_parts.extend(foldable_desc)
        
        # 🎨 根据检测到的风格应用相应的提示词增强
        style_enhancements = {
            "简图": [
                "simple line drawing", "clean minimal design", "schematic style",
                "basic shapes and lines", "technical diagram aesthetic",
                "clear and uncluttered composition"
            ],
            "线条图": [
                "detailed line art", "precise linework", "technical drawing style", 
                "engineering blueprint aesthetic", "clean vector graphics",
                "professional technical illustration"
            ],
            "3D渲染": [
                "high-quality 3D render", "advanced 3D modeling", "realistic materials and textures",
                "professional 3D visualization", "cinema 4d style rendering",
                "volumetric lighting and ray tracing effects"
            ],
            "照片级": [
                "photorealistic rendering", "studio photography lighting", "commercial product photography",
                "ultra-high definition details", "professional camera setup",
                "perfect focus and depth of field"
            ],
            "科技风": [
                "futuristic technology design", "sleek modern aesthetics", "digital interface elements",
                "holographic effects", "neon accent lighting", "advanced sci-fi styling"
            ],
            "工业设计": [
                "professional industrial design", "premium materials showcase", "ergonomic form factor",
                "manufacturing precision details", "contemporary product design language",
                "design excellence and innovation"
            ],
            "概念艺术": [
                "concept art style", "creative artistic interpretation", "imaginative design exploration",
                "artistic vision and creativity", "unique aesthetic approach",
                "visionary design concepts"
            ]
        }
        
        # ✨ 应用检测到的风格增强
        for style in detected_styles:
            if style in style_enhancements:
                enhanced_parts.extend(style_enhancements[style])
        
        # 🏆 默认高质量基础增强（如果没有特定风格）
        if not detected_styles:
            default_enhancements = [
                "high quality", "detailed", "professional grade", "sharp focus", 
                "well-lit", "ultra-detailed", "8k resolution", "photorealistic",
                "cinematic lighting", "perfect composition", "professional photography"
            ]
            enhanced_parts.extend(default_enhancements)
        
        # 🌈 通用质量增强词汇
        quality_boost = [
            "crisp details", "vibrant colors", "excellent craftsmanship",
            "premium quality", "cutting-edge design", "innovative technology",
            "state-of-the-art engineering", "world-class aesthetics"
        ]
        enhanced_parts.extend(quality_boost)
        
        # 🔧 组合最终提示词
        final_prompt = f"{request.strip()}, {', '.join(enhanced_parts)}"
        
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
        # 🔧 关键修复：构建前端能理解的格式，并明确标识任务完成
        text_content = f"""✅ **图像生成任务已完成**

🎯 **任务状态**: COMPLETED
📋 **原始需求**: {original_request}
🚀 **生成结果**: 成功生成高质量图像
📝 **优化提示词**: {prompt[:100]}{"..." if len(prompt) > 100 else ""}
🤖 **生成模型**: {result.model_used}
⏱️ **生成时间**: {result.generation_time:.2f}秒

图像已成功生成并准备显示。"""
        
        # 🔧 核心修复：同时设置url和data字段，确保前端兼容性
        image_content = {
            "url": f"data:image/png;base64,{result.image_data}",  # 🔧 设置完整的data URL
            "data": result.image_data,  # 🔧 保留原始base64数据
            "alt": f"Generated image: {original_request[:50]}..." if len(original_request) > 50 else f"Generated: {original_request}"
        }
        
        # 🔧 构建MultiModalMessage，content为[string, dict]格式
        content = [text_content, image_content]
        
        logger.info(f"📤 返回多模态消息 - 文本长度: {len(text_content)}, 图像数据长度: {len(result.image_data)}")
        logger.info(f"🖼️ 图像格式: data URL长度={len(image_content['url'])}, base64长度={len(result.image_data)}")
        logger.info(f"🎯 任务完成信号已发送: COMPLETED")
        
        return Response(chat_message=MultiModalMessage(
            content=content,
            source=self.name,
            metadata={
                "type": "image_generation", 
                "status": "completed",  # 🔧 明确的完成状态
                "task_complete": "true",  # 🔧 修复：使用字符串而非布尔值
                "internal": "no"
            }
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
    
    async def _save_to_conversation_storage(self, result: ImageGenerationResult, prompt: str):
        """保存生成的图像到对话级存储"""
        try:
            if not self.session_id:
                logger.warning("⚠️ 未设置session_id，跳过对话级存储")
                return
            
            if not result.image_data:
                logger.warning("⚠️ 没有图像数据，跳过存储")
                return
            
            # 将base64转换为字节数据
            image_bytes = base64.b64decode(result.image_data)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_image_{timestamp}.png"
            
            # 保存到对话存储
            saved_file = add_conversation_file(
                session_id=self.session_id,
                file_content=image_bytes,
                filename=filename,
                agent_name=self.name,
                description=f"AI生成的图像 - 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}",
                is_intermediate=False,  # 图像是最终交付物
                tags=["ai_generated", "image", "dall-e", "deliverable"]
            )
            
            logger.info(f"📁 图像已保存到对话存储: {saved_file.file_path}")
            logger.info(f"📊 文件大小: {saved_file.size} bytes")
            
        except Exception as e:
            logger.error(f"❌ 保存图像到对话存储失败: {str(e)}")
            # 不抛出异常，因为这不应该影响主要的图像生成流程