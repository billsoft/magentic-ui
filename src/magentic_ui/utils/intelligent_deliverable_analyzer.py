"""
智能文件提交分析器 - 使用LLM分析应该提交什么给客户
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .conversation_storage_manager import (
    get_conversation_storage_manager, 
    ConversationFile, 
    FileType
)

@dataclass
class DeliverableRecommendation:
    """交付物推荐"""
    file_id: str
    file_info: ConversationFile
    relevance_score: float  # 0-1的相关性评分
    recommendation_reason: str
    delivery_priority: int  # 1-5的优先级
    suggested_filename: Optional[str] = None
    customer_description: Optional[str] = None

@dataclass
class DeliverableAnalysis:
    """交付物分析结果"""
    session_id: int
    task_goal: str
    recommended_files: List[DeliverableRecommendation]
    delivery_summary: str
    total_files_analyzed: int
    analysis_timestamp: datetime

class IntelligentDeliverableAnalyzer:
    """
    智能交付物分析器
    
    使用LLM分析对话中的文件，确定应该提交给客户的最佳文件组合
    """
    
    def __init__(self, llm_client=None):
        self.storage_manager = get_conversation_storage_manager()
        self.llm_client = llm_client  # 这里可以注入LLM客户端
    
    async def analyze_deliverables(self, session_id: int, task_description: str,
                                 conversation_messages: List[Dict[str, Any]] = None) -> DeliverableAnalysis:
        """
        分析对话中的文件，推荐应该交付给客户的文件
        
        Args:
            session_id: 会话ID
            task_description: 任务描述
            conversation_messages: 对话消息（可选，用于更好的分析）
        """
        
        # 获取对话中的所有文件
        all_files = self.storage_manager.get_conversation_files(session_id)
        
        if not all_files:
            return DeliverableAnalysis(
                session_id=session_id,
                task_goal=task_description,
                recommended_files=[],
                delivery_summary="No files found in conversation",
                total_files_analyzed=0,
                analysis_timestamp=datetime.now()
            )
        
        # 使用LLM分析文件相关性
        recommendations = await self._analyze_files_with_llm(
            session_id=session_id,
            task_description=task_description,
            files=all_files,
            conversation_messages=conversation_messages
        )
        
        # 生成交付摘要
        delivery_summary = await self._generate_delivery_summary(
            task_description=task_description,
            recommendations=recommendations
        )
        
        return DeliverableAnalysis(
            session_id=session_id,
            task_goal=task_description,
            recommended_files=recommendations,
            delivery_summary=delivery_summary,
            total_files_analyzed=len(all_files),
            analysis_timestamp=datetime.now()
        )
    
    async def _analyze_files_with_llm(self, session_id: int, task_description: str,
                                    files: List[ConversationFile],
                                    conversation_messages: List[Dict[str, Any]] = None) -> List[DeliverableRecommendation]:
        """使用LLM分析文件相关性"""
        
        # 构建文件信息摘要
        files_summary = []
        for i, file in enumerate(files):
            file_summary = {
                "index": i,
                "filename": file.file_path.name,
                "file_type": file.file_type.value,
                "size": file.size,
                "created_by": file.created_by,
                "description": file.description or "No description",
                "is_intermediate": file.is_intermediate,
                "is_deliverable": file.is_deliverable,
                "tags": file.tags or [],
                "relative_path": file.relative_path
            }
            files_summary.append(file_summary)
        
        # 构建LLM提示词
        prompt = self._build_analysis_prompt(
            task_description=task_description,
            files_summary=files_summary,
            conversation_messages=conversation_messages
        )
        
        if self.llm_client:
            # 使用真实LLM进行分析
            analysis_result = await self._call_llm_for_analysis(prompt)
        else:
            # 使用规则基础的分析作为后备
            analysis_result = self._fallback_rule_based_analysis(task_description, files)
        
        # 解析LLM结果并构建推荐
        recommendations = self._parse_llm_analysis_result(analysis_result, files)
        
        return recommendations
    
    def _build_analysis_prompt(self, task_description: str, files_summary: List[Dict],
                             conversation_messages: List[Dict[str, Any]] = None) -> str:
        """构建LLM分析提示词"""
        
        conversation_context = ""
        if conversation_messages:
            # 提取最近的几条关键消息
            recent_messages = conversation_messages[-10:] if len(conversation_messages) > 10 else conversation_messages
            conversation_context = "\n".join([
                f"- {msg.get('source', 'User')}: {str(msg.get('content', ''))[:200]}..."
                for msg in recent_messages
            ])
        
        prompt = f"""
# 智能文件交付分析任务

## 任务目标
{task_description}

## 对话文件列表
以下是本次对话中生成的所有文件：

{json.dumps(files_summary, ensure_ascii=False, indent=2)}

## 对话上下文（最近消息）
{conversation_context}

## 分析要求
请分析上述文件，确定应该提交给客户的最佳文件组合。对每个文件进行评估：

1. **相关性评分** (0-1): 文件与任务目标的相关程度
2. **交付优先级** (1-5): 1=必须交付，2=强烈建议，3=建议，4=可选，5=不建议
3. **推荐理由**: 为什么推荐或不推荐这个文件
4. **客户友好的文件名**: 如果推荐，建议一个对客户友好的文件名
5. **客户描述**: 向客户解释这个文件的作用和价值

## 分析原则
- 优先推荐最终成果物而非中间产物
- 考虑文件的完整性和实用性
- 关注客户的实际需求和使用场景
- 避免重复或冗余的文件
- 确保推荐的文件组合能完整满足任务目标

## 输出格式
请以JSON格式返回分析结果：

```json
{{
  "analysis_summary": "整体分析总结",
  "file_recommendations": [
    {{
      "file_index": 0,
      "relevance_score": 0.95,
      "delivery_priority": 1,
      "recommendation_reason": "这是最终的产品文档，直接满足客户需求",
      "suggested_filename": "360度全景相机产品介绍.pdf",
      "customer_description": "完整的产品介绍文档，包含技术规格和应用场景"
    }}
  ],
  "delivery_notes": "交付建议和注意事项"
}}
```

请开始分析：
"""
        return prompt
    
    async def _call_llm_for_analysis(self, prompt: str) -> Dict[str, Any]:
        """调用LLM进行分析"""
        # 这里应该调用实际的LLM API
        # 暂时返回模拟结果，实际实现时需要替换为真实的LLM调用
        
        # 模拟LLM响应
        mock_response = {
            "analysis_summary": "基于任务目标和生成的文件，推荐交付最终的产品文档和配图",
            "file_recommendations": [
                {
                    "file_index": 0,
                    "relevance_score": 0.95,
                    "delivery_priority": 1,
                    "recommendation_reason": "主要的任务产出，包含完整的产品信息",
                    "suggested_filename": "产品介绍文档.pdf",
                    "customer_description": "完整的产品介绍，包含规格和特性"
                }
            ],
            "delivery_notes": "建议将文档和图片一起提供给客户以获得最佳体验"
        }
        
        return mock_response
    
    def _fallback_rule_based_analysis(self, task_description: str, 
                                    files: List[ConversationFile]) -> Dict[str, Any]:
        """基于规则的后备分析方法"""
        
        recommendations = []
        
        for i, file in enumerate(files):
            # 基础评分逻辑
            relevance_score = 0.5  # 默认评分
            priority = 3  # 默认优先级
            reason = "Generated file in conversation"
            
            # 已标记为交付物的文件
            if file.is_deliverable:
                relevance_score = 0.9
                priority = 1
                reason = "Marked as deliverable output"
            
            # 最终输出文件
            elif "output" in file.relative_path:
                relevance_score = 0.8
                priority = 2
                reason = "Located in outputs directory"
            
            # 文档类型文件
            elif file.file_type == FileType.DOCUMENT:
                relevance_score = 0.7
                priority = 2
                reason = "Document file likely contains final results"
            
            # 图片文件
            elif file.file_type == FileType.IMAGE:
                relevance_score = 0.6
                priority = 3
                reason = "Image file may be supporting material"
            
            # 中间产物
            elif file.is_intermediate:
                relevance_score = 0.3
                priority = 4
                reason = "Intermediate file, may not be needed by customer"
            
            # 根据文件大小调整（太小的文件可能不重要）
            if file.size < 1024:  # 小于1KB
                relevance_score *= 0.8
                priority = min(priority + 1, 5)
            
            recommendations.append({
                "file_index": i,
                "relevance_score": relevance_score,
                "delivery_priority": priority,
                "recommendation_reason": reason,
                "suggested_filename": file.file_path.name,
                "customer_description": file.description or f"Generated {file.file_type.value} file"
            })
        
        return {
            "analysis_summary": f"Rule-based analysis of {len(files)} files for task: {task_description}",
            "file_recommendations": recommendations,
            "delivery_notes": "Files analyzed using rule-based approach. Consider manual review."
        }
    
    def _parse_llm_analysis_result(self, analysis_result: Dict[str, Any],
                                 files: List[ConversationFile]) -> List[DeliverableRecommendation]:
        """解析LLM分析结果"""
        
        recommendations = []
        file_recommendations = analysis_result.get("file_recommendations", [])
        
        for rec in file_recommendations:
            try:
                file_index = rec.get("file_index", 0)
                if 0 <= file_index < len(files):
                    file_info = files[file_index]
                    
                    # 创建文件ID
                    file_id = f"{file_info.created_by}_{file_info.created_at.strftime('%Y%m%d_%H%M%S')}_{file_info.file_path.stem}"
                    
                    recommendation = DeliverableRecommendation(
                        file_id=file_id,
                        file_info=file_info,
                        relevance_score=rec.get("relevance_score", 0.5),
                        recommendation_reason=rec.get("recommendation_reason", ""),
                        delivery_priority=rec.get("delivery_priority", 3),
                        suggested_filename=rec.get("suggested_filename"),
                        customer_description=rec.get("customer_description")
                    )
                    
                    recommendations.append(recommendation)
                    
            except (KeyError, IndexError, ValueError) as e:
                print(f"Error parsing recommendation: {e}")
                continue
        
        # 按优先级排序
        recommendations.sort(key=lambda x: (x.delivery_priority, -x.relevance_score))
        
        return recommendations
    
    async def _generate_delivery_summary(self, task_description: str,
                                       recommendations: List[DeliverableRecommendation]) -> str:
        """生成交付摘要"""
        
        if not recommendations:
            return "No files recommended for delivery."
        
        high_priority_files = [r for r in recommendations if r.delivery_priority <= 2]
        medium_priority_files = [r for r in recommendations if r.delivery_priority == 3]
        
        summary_parts = []
        
        if high_priority_files:
            summary_parts.append(f"推荐交付 {len(high_priority_files)} 个核心文件：")
            for rec in high_priority_files[:3]:  # 只显示前3个
                filename = rec.suggested_filename or rec.file_info.file_path.name
                summary_parts.append(f"• {filename} - {rec.customer_description or rec.recommendation_reason}")
        
        if medium_priority_files:
            summary_parts.append(f"\n可选交付 {len(medium_priority_files)} 个补充文件")
        
        summary_parts.append(f"\n任务目标: {task_description}")
        
        return "\n".join(summary_parts)
    
    def get_deliverable_files_for_download(self, session_id: int,
                                         analysis: DeliverableAnalysis,
                                         priority_threshold: int = 3) -> List[Tuple[str, bytes, str]]:
        """
        获取可下载的交付文件
        
        Returns:
            List of tuples: (filename, file_content, content_type)
        """
        downloadable_files = []
        
        for rec in analysis.recommended_files:
            if rec.delivery_priority <= priority_threshold:
                file_content = self.storage_manager.get_file_content(session_id, rec.file_id)
                if file_content:
                    filename = rec.suggested_filename or rec.file_info.file_path.name
                    
                    # 确定内容类型
                    content_type = self._get_content_type(rec.file_info.file_path)
                    
                    downloadable_files.append((filename, file_content, content_type))
        
        return downloadable_files
    
    def _get_content_type(self, file_path: Path) -> str:
        """获取文件的MIME类型"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(str(file_path))
        return content_type or "application/octet-stream"

# 全局实例
_deliverable_analyzer = None

def get_deliverable_analyzer() -> IntelligentDeliverableAnalyzer:
    """获取全局交付物分析器实例"""
    global _deliverable_analyzer
    if _deliverable_analyzer is None:
        _deliverable_analyzer = IntelligentDeliverableAnalyzer()
    return _deliverable_analyzer

# 便捷函数
async def analyze_conversation_deliverables(session_id: int, task_description: str,
                                          conversation_messages: List[Dict[str, Any]] = None) -> DeliverableAnalysis:
    """分析对话交付物的便捷函数"""
    analyzer = get_deliverable_analyzer()
    return await analyzer.analyze_deliverables(session_id, task_description, conversation_messages)