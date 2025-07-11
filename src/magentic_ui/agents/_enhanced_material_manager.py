"""
增强的素材管理系统 - 支持多步骤工作流程中的素材传递和存储
"""

import json
import os
import base64
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import aiofiles
from loguru import logger

@dataclass
class MaterialItem:
    """素材项数据结构"""
    id: str
    type: str  # 'image', 'markdown', 'html', 'pdf', 'text', 'data'
    content: str  # 文件路径或base64内容
    metadata: Dict[str, Any]
    created_at: str
    step_index: int
    agent_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialItem':
        return cls(**data)

class EnhancedMaterialManager:
    """增强的素材管理器"""
    
    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)
        self.materials_dir = self.work_dir / "materials"
        self.metadata_file = self.materials_dir / "metadata.json"
        self.materials: Dict[str, MaterialItem] = {}
        
        # 创建必要的目录
        self.materials_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载已有素材
        asyncio.create_task(self._load_materials())
    
    async def _load_materials(self) -> None:
        """加载已有素材元数据"""
        if self.metadata_file.exists():
            try:
                async with aiofiles.open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.loads(await f.read())
                    self.materials = {
                        k: MaterialItem.from_dict(v) 
                        for k, v in data.items()
                    }
                logger.info(f"📂 加载了 {len(self.materials)} 个素材")
            except Exception as e:
                logger.error(f"❌ 加载素材元数据失败: {e}")
    
    async def _save_materials(self) -> None:
        """保存素材元数据"""
        try:
            data = {k: v.to_dict() for k, v in self.materials.items()}
            async with aiofiles.open(self.metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            logger.error(f"❌ 保存素材元数据失败: {e}")
    
    def _generate_id(self, content: str, type: str) -> str:
        """生成素材ID"""
        hash_content = f"{content}_{type}_{datetime.now().isoformat()}"
        return hashlib.md5(hash_content.encode()).hexdigest()[:12]
    
    async def store_image(self, 
                         image_data: str, 
                         step_index: int, 
                         agent_name: str,
                         format: str = 'png',
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        存储图像素材
        
        Args:
            image_data: base64编码的图像数据
            step_index: 步骤索引
            agent_name: 代理名称
            format: 图像格式
            metadata: 额外元数据
            
        Returns:
            素材ID
        """
        material_id = self._generate_id(image_data[:100], 'image')
        file_path = self.materials_dir / f"{material_id}.{format}"
        
        try:
            # 保存图像文件
            image_bytes = base64.b64decode(image_data)
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(image_bytes)
            
            # 创建素材项
            material = MaterialItem(
                id=material_id,
                type='image',
                content=str(file_path),
                metadata={
                    'format': format,
                    'size': len(image_bytes),
                    'width': metadata.get('width') if metadata else None,
                    'height': metadata.get('height') if metadata else None,
                    **(metadata or {})
                },
                created_at=datetime.now().isoformat(),
                step_index=step_index,
                agent_name=agent_name
            )
            
            self.materials[material_id] = material
            await self._save_materials()
            
            logger.info(f"🖼️ 图像素材已保存: {material_id} ({len(image_bytes)} bytes)")
            return material_id
            
        except Exception as e:
            logger.error(f"❌ 保存图像素材失败: {e}")
            raise
    
    async def store_text(self, 
                        content: str, 
                        step_index: int, 
                        agent_name: str,
                        type: str = 'text',
                        filename: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        存储文本素材（markdown, html, text等）
        
        Args:
            content: 文本内容
            step_index: 步骤索引
            agent_name: 代理名称
            type: 素材类型
            filename: 文件名（可选）
            metadata: 额外元数据
            
        Returns:
            素材ID
        """
        material_id = self._generate_id(content[:100], type)
        
        # 确定文件扩展名
        ext_map = {
            'markdown': 'md',
            'html': 'html',
            'text': 'txt',
            'json': 'json',
            'yaml': 'yaml'
        }
        ext = ext_map.get(type, 'txt')
        
        file_path = self.materials_dir / f"{filename or material_id}.{ext}"
        
        try:
            # 保存文本文件
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # 创建素材项
            material = MaterialItem(
                id=material_id,
                type=type,
                content=str(file_path),
                metadata={
                    'size': len(content.encode('utf-8')),
                    'filename': filename,
                    'encoding': 'utf-8',
                    **(metadata or {})
                },
                created_at=datetime.now().isoformat(),
                step_index=step_index,
                agent_name=agent_name
            )
            
            self.materials[material_id] = material
            await self._save_materials()
            
            logger.info(f"📝 文本素材已保存: {material_id} ({type})")
            return material_id
            
        except Exception as e:
            logger.error(f"❌ 保存文本素材失败: {e}")
            raise
    
    async def get_material(self, material_id: str) -> Optional[MaterialItem]:
        """获取素材项"""
        return self.materials.get(material_id)
    
    async def get_material_content(self, material_id: str) -> Optional[str]:
        """获取素材内容"""
        material = self.materials.get(material_id)
        if not material:
            return None
        
        try:
            if material.type == 'image':
                # 返回base64编码的图像
                async with aiofiles.open(material.content, 'rb') as f:
                    image_bytes = await f.read()
                    return base64.b64encode(image_bytes).decode('utf-8')
            else:
                # 返回文本内容
                async with aiofiles.open(material.content, 'r', encoding='utf-8') as f:
                    return await f.read()
                    
        except Exception as e:
            logger.error(f"❌ 读取素材内容失败 {material_id}: {e}")
            return None
    
    def get_materials_by_step(self, step_index: int) -> List[MaterialItem]:
        """获取指定步骤的所有素材"""
        return [m for m in self.materials.values() if m.step_index == step_index]
    
    def get_materials_by_agent(self, agent_name: str) -> List[MaterialItem]:
        """获取指定代理的所有素材"""
        return [m for m in self.materials.values() if m.agent_name == agent_name]
    
    def get_materials_by_type(self, type: str) -> List[MaterialItem]:
        """获取指定类型的所有素材"""
        return [m for m in self.materials.values() if m.type == type]
    
    def get_recent_materials(self, limit: int = 10) -> List[MaterialItem]:
        """获取最近的素材"""
        sorted_materials = sorted(
            self.materials.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return sorted_materials[:limit]
    
    def get_materials_context(self, step_index: int) -> str:
        """获取当前步骤可用的素材上下文"""
        available_materials = [
            m for m in self.materials.values() 
            if m.step_index <= step_index
        ]
        
        if not available_materials:
            return "暂无可用素材"
        
        context_parts = ["可用素材:"]
        for material in available_materials:
            context_parts.append(
                f"- {material.type} ({material.id}): {material.agent_name} 在步骤 {material.step_index} 创建"
            )
        
        return "\n".join(context_parts)
    
    async def cleanup_old_materials(self, days: int = 7) -> None:
        """清理过期素材"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        
        materials_to_remove = []
        for material_id, material in self.materials.items():
            material_time = datetime.fromisoformat(material.created_at).timestamp()
            if material_time < cutoff_time:
                materials_to_remove.append(material_id)
                
                # 删除文件
                try:
                    os.remove(material.content)
                except OSError:
                    pass
        
        for material_id in materials_to_remove:
            del self.materials[material_id]
        
        await self._save_materials()
        logger.info(f"🗑️ 清理了 {len(materials_to_remove)} 个过期素材")