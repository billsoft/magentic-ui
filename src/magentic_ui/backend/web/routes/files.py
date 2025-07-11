"""
文件管理API路由 - 支持对话级文件管理和下载
"""

import io
import zipfile
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from ..deps import get_db_session, get_user_id
from ...teammanager.conversation_aware_team_manager import ConversationAwareTeamManager
from ....utils.conversation_storage_manager import get_conversation_storage_manager
from ....utils.intelligent_deliverable_analyzer import get_deliverable_analyzer

router = APIRouter(prefix="/api/files", tags=["files"])

# 依赖注入：获取团队管理器（这里需要根据实际情况调整）
def get_team_manager() -> ConversationAwareTeamManager:
    # 这里应该返回实际的团队管理器实例
    # 暂时返回None，实际使用时需要从应用状态中获取
    return None

@router.get("/sessions/{session_id}")
async def get_session_files(
    session_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db_session),
    file_type: Optional[str] = Query(None, description="过滤文件类型"),
    agent_name: Optional[str] = Query(None, description="过滤创建者"),
    is_deliverable_only: bool = Query(False, description="只返回交付物")
):
    """
    获取会话的文件列表
    
    Args:
        session_id: 会话ID
        file_type: 文件类型过滤 (image, document, code, data, media, other)
        agent_name: 创建者过滤
        is_deliverable_only: 是否只返回交付物
    """
    try:
        storage_manager = get_conversation_storage_manager()
        
        # 获取文件列表
        files = storage_manager.get_conversation_files(
            session_id=session_id,
            file_type=file_type,
            agent_name=agent_name, 
            is_deliverable_only=is_deliverable_only
        )
        
        # 转换为API响应格式
        file_list = []
        for i, file_info in enumerate(files):
            # 生成文件ID（基于索引和时间戳）
            file_id = f"{file_info.created_by}_{file_info.created_at.strftime('%Y%m%d_%H%M%S')}_{file_info.file_path.stem}"
            
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
                "relative_path": file_info.relative_path,
                "download_url": f"/api/files/sessions/{session_id}/download/{file_id}"
            }
            file_list.append(file_data)
        
        # 获取会话摘要
        summary = storage_manager.get_conversation_summary(session_id)
        
        return {
            "session_id": session_id,
            "files": file_list,
            "summary": summary,
            "total_files": len(file_list),
            "filters_applied": {
                "file_type": file_type,
                "agent_name": agent_name,
                "is_deliverable_only": is_deliverable_only
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session files: {str(e)}")

@router.get("/sessions/{session_id}/download/{file_id}")
async def download_file(
    session_id: int,
    file_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db_session)
):
    """
    下载单个文件
    
    Args:
        session_id: 会话ID
        file_id: 文件ID
    """
    try:
        storage_manager = get_conversation_storage_manager()
        
        # 获取文件内容
        file_content = storage_manager.get_file_content(session_id, file_id)
        if not file_content:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 获取文件信息
        conversation = storage_manager.conversations.get(session_id)
        if not conversation or file_id not in conversation.files:
            raise HTTPException(status_code=404, detail="File metadata not found")
        
        file_info = conversation.files[file_id]
        
        # 确定内容类型
        import mimetypes
        content_type, _ = mimetypes.guess_type(str(file_info.file_path))
        if not content_type:
            content_type = "application/octet-stream"
        
        # 创建响应
        response = Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_info.file_path.name}",
                "Content-Length": str(len(file_content))
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@router.post("/sessions/{session_id}/analyze-deliverables")
async def analyze_deliverables(
    session_id: int,
    task_description: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db_session),
    conversation_messages: Optional[List[dict]] = None
):
    """
    分析会话的交付物
    
    Args:
        session_id: 会话ID
        task_description: 任务描述
        conversation_messages: 对话消息（可选）
    """
    try:
        analyzer = get_deliverable_analyzer()
        
        analysis = await analyzer.analyze_deliverables(
            session_id=session_id,
            task_description=task_description,
            conversation_messages=conversation_messages
        )
        
        # 转换为API响应格式
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
                "created_at": rec.file_info.created_at.isoformat(),
                "download_url": f"/api/files/sessions/{session_id}/download/{rec.file_id}"
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
        raise HTTPException(status_code=500, detail=f"Error analyzing deliverables: {str(e)}")

@router.get("/sessions/{session_id}/deliverable-package")
async def download_deliverable_package(
    session_id: int,
    task_description: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db_session),
    priority_threshold: int = Query(3, description="优先级阈值（<=该值的文件将被包含）"),
    format: str = Query("zip", description="打包格式 (zip)")
):
    """
    下载交付物打包文件
    
    Args:
        session_id: 会话ID  
        task_description: 任务描述
        priority_threshold: 优先级阈值
        format: 打包格式
    """
    try:
        if format != "zip":
            raise HTTPException(status_code=400, detail="Only zip format is supported")
        
        analyzer = get_deliverable_analyzer()
        storage_manager = get_conversation_storage_manager()
        
        # 分析交付物
        analysis = await analyzer.analyze_deliverables(
            session_id=session_id,
            task_description=task_description
        )
        
        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 添加分析报告
            analysis_report = {
                "task_goal": analysis.task_goal,
                "delivery_summary": analysis.delivery_summary,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
                "included_files": []
            }
            
            # 添加推荐文件
            for rec in analysis.recommended_files:
                if rec.delivery_priority <= priority_threshold:
                    # 获取文件内容
                    file_content = storage_manager.get_file_content(session_id, rec.file_id)
                    if file_content:
                        # 使用建议的文件名
                        filename = rec.suggested_filename or rec.file_info.file_path.name
                        
                        # 添加文件到ZIP
                        zip_file.writestr(filename, file_content)
                        
                        # 记录到分析报告
                        analysis_report["included_files"].append({
                            "filename": filename,
                            "original_filename": rec.file_info.file_path.name,
                            "description": rec.customer_description or rec.recommendation_reason,
                            "priority": rec.delivery_priority,
                            "relevance_score": rec.relevance_score,
                            "created_by": rec.file_info.created_by
                        })
            
            # 添加分析报告
            import json
            report_content = json.dumps(analysis_report, ensure_ascii=False, indent=2)
            zip_file.writestr("交付物分析报告.json", report_content.encode('utf-8'))
        
        zip_buffer.seek(0)
        
        # 生成文件名
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"session_{session_id}_deliverables_{timestamp}.zip"
        
        # 返回ZIP文件
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating deliverable package: {str(e)}")

@router.post("/sessions/{session_id}/mark-deliverable")
async def mark_file_as_deliverable(
    session_id: int,
    file_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db_session),
    description: Optional[str] = None
):
    """
    标记文件为交付物
    
    Args:
        session_id: 会话ID
        file_id: 文件ID
        description: 交付描述
    """
    try:
        storage_manager = get_conversation_storage_manager()
        
        # 检查文件是否存在
        conversation = storage_manager.conversations.get(session_id)
        if not conversation or file_id not in conversation.files:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 标记为交付物
        storage_manager.mark_as_deliverable(session_id, file_id, description)
        
        return {
            "success": True,
            "message": "File marked as deliverable",
            "file_id": file_id,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking file as deliverable: {str(e)}")

@router.get("/sessions/{session_id}/stats")
async def get_session_file_stats(
    session_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db_session)
):
    """
    获取会话文件统计信息
    
    Args:
        session_id: 会话ID
    """
    try:
        storage_manager = get_conversation_storage_manager()
        summary = storage_manager.get_conversation_summary(session_id)
        
        if not summary:
            return {
                "session_id": session_id,
                "total_files": 0,
                "deliverable_files": 0,
                "intermediate_files": 0,
                "file_types": {},
                "agent_statistics": {},
                "storage_path": "",
                "created_at": None,
                "last_updated": None
            }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session stats: {str(e)}")

@router.delete("/sessions/{session_id}/files/{file_id}")
async def delete_file(
    session_id: int,
    file_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db_session)
):
    """
    删除文件
    
    Args:
        session_id: 会话ID
        file_id: 文件ID
    """
    try:
        storage_manager = get_conversation_storage_manager()
        
        # 检查文件是否存在
        conversation = storage_manager.conversations.get(session_id)
        if not conversation or file_id not in conversation.files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = conversation.files[file_id]
        
        # 删除物理文件
        if file_info.file_path.exists():
            file_info.file_path.unlink()
        
        # 从记录中删除
        del conversation.files[file_id]
        
        # 更新元数据
        conversation.metadata["total_files"] = len(conversation.files)
        conversation.metadata["last_updated"] = datetime.now().isoformat()
        
        # 保存更新
        storage_manager._save_conversation_metadata(session_id)
        
        return {
            "success": True,
            "message": "File deleted successfully",
            "file_id": file_id,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")