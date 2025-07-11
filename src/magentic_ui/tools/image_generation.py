"""
图像生成工具 - 支持多种OpenAI兼容的图像生成模型
"""

import base64
import asyncio
import logging
from typing import Dict, Any, Optional
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ImageGenerationResult:
    """图像生成结果"""
    success: bool
    image_data: Optional[str] = None  # base64编码的图像数据
    image_url: Optional[str] = None   # 图像URL
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    generation_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass 
class ImageGenerationConfig:
    """图像生成配置 - 从配置文件动态获取默认值"""
    model: str = "dall-e-3"  # 🔧 保持作为默认值，实际使用时会从配置文件获取
    size: str = "1024x1024"
    quality: str = "standard"  # "standard" or "hd"
    style: str = "vivid"       # "natural" or "vivid"
    response_format: str = "b64_json"  # "url" or "b64_json"
    n: int = 1

class ImageGenerationClient:
    """统一的图像生成客户端，支持多种OpenAI兼容的模型"""
    
    # 支持的模型映射
    SUPPORTED_MODELS = {
        # OpenAI DALL-E
        "dall-e-3": {
            "provider": "openai",
            "sizes": ["1024x1024", "1792x1024", "1024x1792"],
            "qualities": ["standard", "hd"],
            "styles": ["natural", "vivid"]
        },
        "dall-e-2": {
            "provider": "openai", 
            "sizes": ["256x256", "512x512", "1024x1024"],
            "qualities": ["standard"],
            "styles": []
        },
        # Google Imagen
        "imagen-3.0-generate-002": {
            "provider": "google",
            "sizes": ["1024x1024", "1024x1536", "1536x1024"],
            "qualities": ["low", "medium", "high"],
            "styles": []
        },
        # Stable Diffusion通过OpenRouter
        "stability-ai/stable-diffusion-xl": {
            "provider": "stability",
            "sizes": ["1024x1024", "1152x896", "896x1152"],
            "qualities": ["standard"],
            "styles": []
        }
    }
    
    def __init__(self, 
                 api_key: str,
                 base_url: str = "https://api.openai.com/v1",  # 🔧 保持默认值，实际使用时会从配置文件获取
                 default_model: str = "dall-e-3",  # 🔧 保持默认值，实际使用时会从配置文件获取
                 timeout: int = 60):
        # 如果api_key为空，尝试从环境变量获取
        if not api_key:
            import os
            if base_url.startswith("https://api.openai.com"):
                api_key = os.getenv("OPENAI_API_KEY", "")
            elif "openrouter" in base_url:
                api_key = os.getenv("OPENROUTER_API_KEY", "")
            else:
                api_key = os.getenv("OPENAI_API_KEY", "")  # 默认使用OpenAI
                
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.timeout = timeout
        
        # 验证关键配置
        if not self.api_key:
            logger.warning("⚠️ 图像生成API密钥未设置，请检查环境变量OPENAI_API_KEY")
        
        logger.info(f"🎨 图像生成客户端初始化: {base_url} (模型: {default_model})")
        
    async def generate_image(self, 
                           prompt: str,
                           config: Optional[ImageGenerationConfig] = None) -> ImageGenerationResult:
        """
        生成图像
        
        Args:
            prompt: 图像描述提示词
            config: 生成配置，如果为None则使用默认配置
            
        Returns:
            ImageGenerationResult: 生成结果
        """
        if config is None:
            config = ImageGenerationConfig(model=self.default_model)
            
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 验证模型和参数
            self._validate_config(config)
            
            # 构建请求数据
            request_data = self._build_request_data(prompt, config)
            
            # 发送请求
            result = await self._send_request(request_data)
            
            generation_time = asyncio.get_event_loop().time() - start_time
            
            return ImageGenerationResult(
                success=True,
                image_data=result.get("image_data"),
                image_url=result.get("image_url"),
                model_used=config.model,
                generation_time=generation_time,
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"图像生成失败: {str(e)}")
            generation_time = asyncio.get_event_loop().time() - start_time
            
            return ImageGenerationResult(
                success=False,
                error_message=str(e),
                model_used=config.model,
                generation_time=generation_time
            )
    
    def _validate_config(self, config: ImageGenerationConfig):
        """验证配置参数"""
        if config.model not in self.SUPPORTED_MODELS:
            raise ValueError(f"不支持的模型: {config.model}. 支持的模型: {list(self.SUPPORTED_MODELS.keys())}")
        
        model_info = self.SUPPORTED_MODELS[config.model]
        
        if config.size not in model_info["sizes"]:
            raise ValueError(f"模型 {config.model} 不支持尺寸 {config.size}")
        
        if config.quality not in model_info["qualities"]:
            raise ValueError(f"模型 {config.model} 不支持质量 {config.quality}")
        
        if model_info["styles"] and config.style not in model_info["styles"]:
            raise ValueError(f"模型 {config.model} 不支持风格 {config.style}")
    
    def _build_request_data(self, prompt: str, config: ImageGenerationConfig) -> Dict[str, Any]:
        """构建请求数据"""
        data = {
            "model": config.model,
            "prompt": prompt,
            "n": config.n,
            "size": config.size,
            "response_format": config.response_format
        }
        
        # 添加模型特定参数
        model_info = self.SUPPORTED_MODELS[config.model]
        
        if model_info["provider"] == "openai":
            if config.quality in model_info["qualities"]:
                data["quality"] = config.quality
            if config.style and model_info["styles"]:
                data["style"] = config.style
        elif model_info["provider"] == "google":
            # Imagen特定参数
            data["quality"] = config.quality
        
        return data
    
    async def _send_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送图像生成请求"""
        url = f"{self.base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.post(url, headers=headers, json=request_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API请求失败 (状态码: {response.status}): {error_text}")
                
                result = await response.json()
                
                # 处理响应数据
                if "data" not in result or not result["data"]:
                    raise Exception("API响应中没有图像数据")
                
                image_info = result["data"][0]
                
                processed_result = {
                    "metadata": {
                        "revised_prompt": image_info.get("revised_prompt"),
                        "response": result
                    }
                }
                
                if "b64_json" in image_info:
                    processed_result["image_data"] = image_info["b64_json"]
                elif "url" in image_info:
                    processed_result["image_url"] = image_info["url"]
                    # 如果需要，可以下载图像并转换为base64
                    if request_data.get("response_format") == "b64_json":
                        processed_result["image_data"] = await self._download_and_encode(image_info["url"])
                
                return processed_result
    
    async def _download_and_encode(self, image_url: str) -> str:
        """下载图像并编码为base64"""
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    return base64.b64encode(image_bytes).decode('utf-8')
                else:
                    raise Exception(f"下载图像失败: {response.status}")
    
    @classmethod
    def from_chat_client_config(cls, 
                              chat_client_config: Dict[str, Any],
                              image_model: Optional[str] = None) -> "ImageGenerationClient":
        """
        从现有的聊天客户端配置创建图像生成客户端
        
        Args:
            chat_client_config: 现有的聊天客户端配置
            image_model: 指定的图像生成模型，如果为None则尝试自动选择
            
        Returns:
            ImageGenerationClient实例
        """
        config = chat_client_config.get("config", {})
        
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.openai.com/v1")
        
        if not api_key:
            raise ValueError("未找到API密钥")
        
        # 自动选择图像模型
        if image_model is None:
            current_model = config.get("model", "")
            if "gemini" in current_model.lower():
                image_model = "imagen-3.0-generate-002"
            elif "gpt" in current_model.lower() or "openai" in base_url.lower():
                image_model = "dall-e-3"
            else:
                image_model = "dall-e-3"  # 默认
        
        return cls(
            api_key=api_key,
            base_url=base_url,
            default_model=image_model,
            timeout=config.get("timeout", 60)
        )

# 便利函数
async def quick_generate_image(prompt: str, 
                             api_key: str,
                             base_url: str = "https://api.openai.com/v1",
                             model: str = "dall-e-3") -> ImageGenerationResult:
    """快速生成图像的便利函数"""
    client = ImageGenerationClient(api_key, base_url, model)
    config = ImageGenerationConfig(model=model)
    return await client.generate_image(prompt, config) 