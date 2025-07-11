"""
对话感知代理混入类 - 让所有agent了解并管理对话中的文件内容
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from ..utils.conversation_storage_manager import (
    get_conversation_storage_manager,
    add_conversation_file,
    add_conversation_text_file,
    get_conversation_files,
    mark_file_as_deliverable,
    ConversationFile,
    FileType
)

class ConversationAwareMixin:
    """
    对话感知混入类
    
    为agent提供对话级文件管理能力：
    - 了解当前对话中存在的文件
    - 创建和保存新文件到对话存储
    - 管理中间产物和最终交付物
    - 提供文件内容检索和引用功能
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage_manager = get_conversation_storage_manager()
        self.current_session_id: Optional[int] = None
        self.agent_name = getattr(self, 'name', self.__class__.__name__)
    
    def set_session_context(self, session_id: int):
        """设置当前会话上下文"""
        self.current_session_id = session_id
    
    def save_text_file(self, content: str, filename: str, description: str = None,
                      is_intermediate: bool = True, tags: List[str] = None) -> ConversationFile:
        """
        保存文本文件到对话存储
        
        Args:
            content: 文件内容
            filename: 文件名
            description: 文件描述
            is_intermediate: 是否为中间产物
            tags: 文件标签
        """
        if not self.current_session_id:
            raise ValueError("Session context not set. Call set_session_context first.")
        
        return add_conversation_text_file(
            session_id=self.current_session_id,
            content=content,
            filename=filename,
            agent_name=self.agent_name,
            description=description,
            is_intermediate=is_intermediate,
            tags=tags
        )
    
    def save_binary_file(self, content: bytes, filename: str, description: str = None,
                        is_intermediate: bool = True, tags: List[str] = None) -> ConversationFile:
        """
        保存二进制文件到对话存储
        
        Args:
            content: 文件内容（字节）
            filename: 文件名
            description: 文件描述
            is_intermediate: 是否为中间产物
            tags: 文件标签
        """
        if not self.current_session_id:
            raise ValueError("Session context not set. Call set_session_context first.")
        
        return add_conversation_file(
            session_id=self.current_session_id,
            file_content=content,
            filename=filename,
            agent_name=self.agent_name,
            description=description,
            is_intermediate=is_intermediate,
            tags=tags
        )
    
    def get_conversation_files(self, file_type: Optional[FileType] = None,
                             agent_name: Optional[str] = None,
                             is_deliverable_only: bool = False) -> List[ConversationFile]:
        """
        获取对话中的文件列表
        
        Args:
            file_type: 过滤文件类型
            agent_name: 过滤创建者
            is_deliverable_only: 只返回交付物
        """
        if not self.current_session_id:
            return []
        
        return get_conversation_files(
            session_id=self.current_session_id,
            file_type=file_type,
            agent_name=agent_name,
            is_deliverable_only=is_deliverable_only
        )
    
    def get_my_files(self, file_type: Optional[FileType] = None) -> List[ConversationFile]:
        """获取本agent创建的文件"""
        return self.get_conversation_files(
            file_type=file_type,
            agent_name=self.agent_name
        )
    
    def get_available_files_summary(self) -> str:
        """获取可用文件摘要（用于agent的上下文理解）"""
        if not self.current_session_id:
            return "No session context available."
        
        all_files = self.get_conversation_files()
        if not all_files:
            return "No files available in current conversation."
        
        # 按agent和文件类型分组
        agents_files = {}
        for file in all_files:
            agent = file.created_by
            if agent not in agents_files:
                agents_files[agent] = {"total": 0, "types": {}}
            
            agents_files[agent]["total"] += 1
            file_type = file.file_type.value
            if file_type not in agents_files[agent]["types"]:
                agents_files[agent]["types"][file_type] = 0
            agents_files[agent]["types"][file_type] += 1
        
        # 构建摘要
        summary_lines = ["Available files in conversation:"]
        
        for agent, info in agents_files.items():
            summary_lines.append(f"• {agent}: {info['total']} files")
            for file_type, count in info["types"].items():
                summary_lines.append(f"  - {file_type}: {count}")
        
        # 添加最新的几个文件
        recent_files = sorted(all_files, key=lambda x: x.created_at, reverse=True)[:5]
        if recent_files:
            summary_lines.append("\nRecent files:")
            for file in recent_files:
                desc = file.description or "No description"
                summary_lines.append(f"• {file.file_path.name} ({file.file_type.value}) - {desc}")
        
        return "\n".join(summary_lines)
    
    def read_file_content(self, file_id: str) -> Optional[str]:
        """
        读取文件内容（文本）
        
        Args:
            file_id: 文件ID
        """
        if not self.current_session_id:
            return None
        
        content = self.storage_manager.get_file_content(self.current_session_id, file_id)
        if content:
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return f"Binary file content (size: {len(content)} bytes)"
        
        return None
    
    def read_file_bytes(self, file_id: str) -> Optional[bytes]:
        """
        读取文件内容（字节）
        
        Args:
            file_id: 文件ID
        """
        if not self.current_session_id:
            return None
        
        return self.storage_manager.get_file_content(self.current_session_id, file_id)
    
    def mark_as_deliverable(self, file_id: str, description: str = None):
        """
        标记文件为最终交付物
        
        Args:
            file_id: 文件ID
            description: 交付描述
        """
        if not self.current_session_id:
            return
        
        mark_file_as_deliverable(self.current_session_id, file_id, description)
    
    def find_files_by_pattern(self, pattern: str, file_type: Optional[FileType] = None) -> List[ConversationFile]:
        """
        根据模式查找文件
        
        Args:
            pattern: 文件名模式（支持通配符）
            file_type: 文件类型过滤
        """
        import fnmatch
        
        all_files = self.get_conversation_files(file_type=file_type)
        matching_files = []
        
        for file in all_files:
            if fnmatch.fnmatch(file.file_path.name.lower(), pattern.lower()):
                matching_files.append(file)
        
        return matching_files
    
    def get_file_reference_context(self, max_files: int = 10) -> str:
        """
        获取文件引用上下文（用于agent回复中引用文件）
        
        Args:
            max_files: 最大文件数量
        """
        recent_files = self.get_conversation_files()
        if not recent_files:
            return ""
        
        # 按创建时间排序，取最新的
        recent_files = sorted(recent_files, key=lambda x: x.created_at, reverse=True)[:max_files]
        
        context_lines = []
        for file in recent_files:
            file_info = f"📁 {file.file_path.name}"
            if file.description:
                file_info += f" - {file.description}"
            
            # 添加文件状态标识
            if file.is_deliverable:
                file_info += " ✅ [交付物]"
            elif file.is_intermediate:
                file_info += " 🔄 [中间产物]"
            
            context_lines.append(file_info)
        
        if context_lines:
            return "\n" + "\n".join(context_lines) + "\n"
        
        return ""
    
    def create_file_summary_report(self) -> str:
        """创建文件摘要报告"""
        if not self.current_session_id:
            return "No session context available for file summary."
        
        all_files = self.get_conversation_files()
        if not all_files:
            return "No files have been created in this conversation."
        
        # 统计信息
        total_files = len(all_files)
        deliverable_files = [f for f in all_files if f.is_deliverable]
        intermediate_files = [f for f in all_files if f.is_intermediate]
        
        # 按类型分组
        type_stats = {}
        for file in all_files:
            file_type = file.file_type.value
            if file_type not in type_stats:
                type_stats[file_type] = 0
            type_stats[file_type] += 1
        
        # 按agent分组
        agent_stats = {}
        for file in all_files:
            agent = file.created_by
            if agent not in agent_stats:
                agent_stats[agent] = 0
            agent_stats[agent] += 1
        
        # 构建报告
        report_lines = [
            f"## 📊 文件摘要报告",
            f"",
            f"**总文件数**: {total_files}",
            f"**交付物**: {len(deliverable_files)}",
            f"**中间产物**: {len(intermediate_files)}",
            f"",
            f"**按类型分布**:"
        ]
        
        for file_type, count in sorted(type_stats.items()):
            report_lines.append(f"- {file_type}: {count}")
        
        report_lines.extend([
            f"",
            f"**按创建者分布**:"
        ])
        
        for agent, count in sorted(agent_stats.items()):
            report_lines.append(f"- {agent}: {count}")
        
        if deliverable_files:
            report_lines.extend([
                f"",
                f"**🎯 交付物列表**:"
            ])
            for file in deliverable_files:
                desc = file.description or "No description"
                report_lines.append(f"- {file.file_path.name} - {desc}")
        
        return "\n".join(report_lines)

class ConversationAwareWebSurfer(ConversationAwareMixin):
    """对话感知的WebSurfer增强"""
    
    def save_webpage_content(self, url: str, content: str, title: str = None) -> ConversationFile:
        """保存网页内容"""
        filename = f"webpage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        description = f"Webpage content from {url}"
        if title:
            description += f" - {title}"
        
        return self.save_text_file(
            content=content,
            filename=filename,
            description=description,
            is_intermediate=True,
            tags=["webpage", "html", url]
        )
    
    def save_screenshot(self, image_data: bytes, url: str) -> ConversationFile:
        """保存截图"""
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        description = f"Screenshot from {url}"
        
        return self.save_binary_file(
            content=image_data,
            filename=filename,
            description=description,
            is_intermediate=True,
            tags=["screenshot", "image", url]
        )
    
    def get_browsing_history_summary(self) -> str:
        """获取浏览历史摘要"""
        webpage_files = self.get_my_files(file_type=FileType.DOCUMENT)
        screenshot_files = self.get_my_files(file_type=FileType.IMAGE)
        
        if not webpage_files and not screenshot_files:
            return "No browsing history available."
        
        summary_lines = ["🌐 Browsing History:"]
        
        if webpage_files:
            summary_lines.append(f"Visited {len(webpage_files)} pages:")
            for file in webpage_files[-5:]:  # 最近5个
                if "webpage" in file.tags:
                    url = next((tag for tag in file.tags if tag.startswith("http")), "Unknown URL")
                    summary_lines.append(f"  • {url}")
        
        if screenshot_files:
            summary_lines.append(f"Captured {len(screenshot_files)} screenshots")
        
        return "\n".join(summary_lines)

class ConversationAwareImageGenerator(ConversationAwareMixin):
    """对话感知的图像生成器增强"""
    
    def save_generated_image(self, image_data: bytes, prompt: str, 
                           model_info: Dict[str, Any] = None) -> ConversationFile:
        """保存生成的图像"""
        filename = f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        description = f"Generated image: {prompt[:100]}..."
        
        tags = ["generated", "image", "ai-created"]
        if model_info:
            if "model" in model_info:
                tags.append(f"model:{model_info['model']}")
        
        return self.save_binary_file(
            content=image_data,
            filename=filename,
            description=description,
            is_intermediate=False,  # 生成的图像通常是交付物
            tags=tags
        )
    
    def get_generation_history(self) -> str:
        """获取图像生成历史"""
        image_files = self.get_my_files(file_type=FileType.IMAGE)
        
        if not image_files:
            return "No images generated yet."
        
        summary_lines = ["🎨 Image Generation History:"]
        for file in image_files[-3:]:  # 最近3个
            summary_lines.append(f"  • {file.file_path.name} - {file.description}")
        
        return "\n".join(summary_lines)

class ConversationAwareCoder(ConversationAwareMixin):
    """对话感知的编码器增强"""
    
    def save_code_file(self, code: str, filename: str, language: str = None,
                      purpose: str = None) -> ConversationFile:
        """保存代码文件"""
        description = f"Generated code file"
        if purpose:
            description += f" - {purpose}"
        if language:
            description += f" ({language})"
        
        tags = ["code", "generated"]
        if language:
            tags.append(f"lang:{language}")
        
        return self.save_text_file(
            content=code,
            filename=filename,
            description=description,
            is_intermediate=True,
            tags=tags
        )
    
    def save_document(self, content: str, filename: str, doc_type: str = None,
                     is_final: bool = False) -> ConversationFile:
        """保存文档文件"""
        description = f"Generated document"
        if doc_type:
            description += f" ({doc_type})"
        
        tags = ["document", "generated"]
        if doc_type:
            tags.append(f"type:{doc_type}")
        
        return self.save_text_file(
            content=content,
            filename=filename,
            description=description,
            is_intermediate=not is_final,
            tags=tags
        )
    
    def get_code_files_summary(self) -> str:
        """获取代码文件摘要"""
        code_files = self.get_my_files(file_type=FileType.CODE)
        doc_files = self.get_my_files(file_type=FileType.DOCUMENT)
        
        summary_lines = ["💻 Generated Files:"]
        
        if code_files:
            summary_lines.append(f"Code files: {len(code_files)}")
            for file in code_files[-3:]:
                summary_lines.append(f"  • {file.file_path.name}")
        
        if doc_files:
            summary_lines.append(f"Documents: {len(doc_files)}")
            for file in doc_files[-3:]:
                summary_lines.append(f"  • {file.file_path.name}")
        
        return "\n".join(summary_lines)