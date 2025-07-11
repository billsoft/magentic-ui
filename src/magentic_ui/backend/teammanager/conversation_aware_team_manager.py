"""
对话感知的团队管理器 - 集成文件管理功能
"""

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from pathlib import Path

from .teammanager import TeamManager
from ...utils.conversation_storage_manager import get_conversation_storage_manager
from ...utils.intelligent_deliverable_analyzer import get_deliverable_analyzer
from ...agents._conversation_aware_agent import ConversationAwareMixin
from ..datamodel.db import Run

class ConversationAwareTeamManager(TeamManager):
    """
    对话感知的团队管理器
    
    在原有功能基础上增加：
    - 自动设置agent的会话上下文
    - 管理对话级文件存储
    - 智能分析交付物
    - 提供文件下载接口
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage_manager = get_conversation_storage_manager()
        self.deliverable_analyzer = get_deliverable_analyzer()
    
    def _setup_conversation_context_for_agents(self, session_id: int):
        """为所有对话感知的agent设置会话上下文"""
        if not self.team:
            return
        
        # 遍历team中的所有agents
        for agent in self.team.participants:
            if isinstance(agent, ConversationAwareMixin):
                agent.set_session_context(session_id)
    
    async def run_stream(
        self,
        run: Run,
        task: str,
        **kwargs
    ) -> AsyncGenerator[Any, None]:
        """
        增强的运行流，支持对话感知
        """
        # 设置对话上下文
        if run.session_id:
            self._setup_conversation_context_for_agents(run.session_id)
        
        # 调用原始的run_stream方法
        async for item in super().run_stream(run, task, **kwargs):
            yield item
    
    async def get_conversation_files(self, session_id: int) -> Dict[str, Any]:
        """
        获取对话中的文件信息
        
        Returns:
            {
                "files": [文件列表],
                "summary": {统计摘要},
                "deliverable_analysis": {交付物分析}
            }
        """
        try:
            # 获取文件列表
            files = self.storage_manager.get_conversation_files(session_id)
            
            # 获取摘要
            summary = self.storage_manager.get_conversation_summary(session_id)
            
            # 构建文件信息
            file_list = []
            for file_id, file_info in self.storage_manager.conversations.get(session_id, {}).get("files", {}).items():
                file_data = {
                    "id": file_id,
                    "filename": file_info.file_path.name,
                    "file_type": file_info.file_type.value,
                    "size": file_info.size,
                    "created_at": file_info.created_at.isoformat(),
                    "created_by": file_info.created_by,
                    "description": file_info.description,
                    "is_deliverable": file_info.is_deliverable,
                    "is_intermediate": file_info.is_intermediate,
                    "tags": file_info.tags or [],
                    "relative_path": file_info.relative_path
                }
                file_list.append(file_data)
            
            return {
                "files": file_list,
                "summary": summary,
                "total_files": len(file_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation files: {e}")
            return {
                "files": [],
                "summary": {},
                "total_files": 0,
                "error": str(e)
            }
    
    async def analyze_deliverables(self, session_id: int, task_description: str,
                                 conversation_messages: Optional[list] = None) -> Dict[str, Any]:
        """
        分析对话中的交付物
        
        Args:
            session_id: 会话ID
            task_description: 任务描述
            conversation_messages: 对话消息（可选）
        
        Returns:
            交付物分析结果
        """
        try:
            analysis = await self.deliverable_analyzer.analyze_deliverables(
                session_id=session_id,
                task_description=task_description,
                conversation_messages=conversation_messages
            )
            
            # 转换为可序列化的格式
            recommendations = []
            for rec in analysis.recommended_files:
                rec_data = {
                    "file_id": rec.file_id,
                    "filename": rec.file_info.file_path.name,
                    "file_type": rec.file_info.file_type.value,
                    "relevance_score": rec.relevance_score,
                    "delivery_priority": rec.delivery_priority,
                    "recommendation_reason": rec.recommendation_reason,
                    "suggested_filename": rec.suggested_filename,
                    "customer_description": rec.customer_description,
                    "file_size": rec.file_info.size,
                    "created_by": rec.file_info.created_by,
                    "created_at": rec.file_info.created_at.isoformat()
                }
                recommendations.append(rec_data)
            
            return {
                "session_id": analysis.session_id,
                "task_goal": analysis.task_goal,
                "recommended_files": recommendations,
                "delivery_summary": analysis.delivery_summary,
                "total_files_analyzed": analysis.total_files_analyzed,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing deliverables: {e}")
            return {
                "session_id": session_id,
                "task_goal": task_description,
                "recommended_files": [],
                "delivery_summary": f"Error analyzing deliverables: {str(e)}",
                "total_files_analyzed": 0,
                "analysis_timestamp": "",
                "error": str(e)
            }
    
    async def get_file_for_download(self, session_id: int, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件用于下载
        
        Args:
            session_id: 会话ID
            file_id: 文件ID
        
        Returns:
            {
                "filename": str,
                "content": bytes,
                "content_type": str,
                "size": int
            }
        """
        try:
            # 获取文件内容
            file_content = self.storage_manager.get_file_content(session_id, file_id)
            if not file_content:
                return None
            
            # 获取文件信息
            conversation = self.storage_manager.conversations.get(session_id)
            if not conversation or file_id not in conversation.files:
                return None
            
            file_info = conversation.files[file_id]
            
            # 确定内容类型
            import mimetypes
            content_type, _ = mimetypes.guess_type(str(file_info.file_path))
            if not content_type:
                content_type = "application/octet-stream"
            
            return {
                "filename": file_info.file_path.name,
                "content": file_content,
                "content_type": content_type,
                "size": len(file_content),
                "description": file_info.description
            }
            
        except Exception as e:
            logger.error(f"Error getting file for download: {e}")
            return None
    
    async def get_deliverable_package(self, session_id: int, task_description: str,
                                    priority_threshold: int = 3) -> Optional[Dict[str, Any]]:
        """
        获取交付物打包
        
        Args:
            session_id: 会话ID
            task_description: 任务描述
            priority_threshold: 优先级阈值（<=该值的文件将被包含）
        
        Returns:
            {
                "files": [{"filename": str, "content": bytes, "content_type": str}],
                "analysis": {分析结果},
                "package_info": {打包信息}
            }
        """
        try:
            # 分析交付物
            analysis = await self.analyze_deliverables(session_id, task_description)
            
            # 获取推荐文件
            package_files = []
            total_size = 0
            
            for rec in analysis["recommended_files"]:
                if rec["delivery_priority"] <= priority_threshold:
                    file_data = await self.get_file_for_download(session_id, rec["file_id"])
                    if file_data:
                        # 使用建议的文件名
                        if rec["suggested_filename"]:
                            file_data["filename"] = rec["suggested_filename"]
                        
                        package_files.append({
                            "filename": file_data["filename"],
                            "content": file_data["content"],
                            "content_type": file_data["content_type"],
                            "size": file_data["size"],
                            "description": rec["customer_description"] or file_data.get("description", ""),
                            "priority": rec["delivery_priority"]
                        })
                        total_size += file_data["size"]
            
            # 生成打包信息
            package_info = {
                "total_files": len(package_files),
                "total_size": total_size,
                "created_at": analysis["analysis_timestamp"],
                "priority_threshold": priority_threshold,
                "session_id": session_id
            }
            
            return {
                "files": package_files,
                "analysis": analysis,
                "package_info": package_info
            }
            
        except Exception as e:
            logger.error(f"Error creating deliverable package: {e}")
            return None
    
    async def mark_file_as_deliverable(self, session_id: int, file_id: str, 
                                     description: Optional[str] = None) -> bool:
        """
        标记文件为交付物
        
        Args:
            session_id: 会话ID
            file_id: 文件ID
            description: 交付描述
        
        Returns:
            是否成功
        """
        try:
            self.storage_manager.mark_as_deliverable(session_id, file_id, description)
            return True
        except Exception as e:
            logger.error(f"Error marking file as deliverable: {e}")
            return False
    
    def get_conversation_context_for_agents(self, session_id: int) -> str:
        """
        获取agent使用的对话上下文信息
        
        Args:
            session_id: 会话ID
        
        Returns:
            格式化的上下文字符串
        """
        try:
            summary = self.storage_manager.get_conversation_summary(session_id)
            
            if not summary:
                return "No conversation context available."
            
            context_lines = [
                "## 📁 对话文件上下文",
                f"会话ID: {session_id}",
                f"总文件数: {summary.get('total_files', 0)}",
                f"交付物: {summary.get('deliverable_files', 0)}",
                f"中间产物: {summary.get('intermediate_files', 0)}",
                ""
            ]
            
            # 文件类型分布
            file_types = summary.get('file_types', {})
            if file_types:
                context_lines.append("文件类型分布:")
                for file_type, count in file_types.items():
                    context_lines.append(f"  • {file_type}: {count}")
                context_lines.append("")
            
            # Agent统计
            agent_stats = summary.get('agent_statistics', {})
            if agent_stats:
                context_lines.append("按创建者分布:")
                for agent, stats in agent_stats.items():
                    context_lines.append(f"  • {agent}: {stats.get('total', 0)} 文件")
                context_lines.append("")
            
            context_lines.append("💡 提示: 使用文件管理功能查看、创建和管理文件")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return f"Error getting conversation context: {str(e)}"

# 便捷函数用于创建对话感知的团队管理器
def create_conversation_aware_team_manager(*args, **kwargs) -> ConversationAwareTeamManager:
    """创建对话感知的团队管理器"""
    return ConversationAwareTeamManager(*args, **kwargs)