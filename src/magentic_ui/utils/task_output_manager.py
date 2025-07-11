"""
任务输出管理器 - 通用多任务输出目录管理
支持MUNAS风格的多任务智能体平台
"""

import os
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import hashlib


@dataclass
class TaskSession:
    """任务会话信息"""
    session_id: str
    task_type: str
    task_description: str
    created_at: datetime
    status: str = "active"
    output_dir: Optional[Path] = None
    metadata: Dict[str, Any] = None


class TaskOutputManager:
    """
    任务输出管理器
    
    设计理念：
    - 每个任务会话有唯一的输出目录
    - 支持任务类型分类和管理
    - 自动清理过期的中间文件
    - 保持核心功能的通用性
    """
    
    def __init__(self, base_output_dir: str = "task_outputs"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        
        # 创建子目录结构
        self.active_dir = self.base_output_dir / "active"
        self.completed_dir = self.base_output_dir / "completed"
        self.archived_dir = self.base_output_dir / "archived"
        
        for dir_path in [self.active_dir, self.completed_dir, self.archived_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # 加载或创建会话记录
        self.sessions_file = self.base_output_dir / "sessions.json"
        self.sessions = self._load_sessions()
    
    def create_task_session(self, task_description: str, task_type: str = "general") -> TaskSession:
        """
        创建新的任务会话
        
        Args:
            task_description: 任务描述
            task_type: 任务类型 (如: web_research, image_generation, document_processing)
        
        Returns:
            TaskSession: 新创建的任务会话
        """
        # 生成唯一的会话ID
        timestamp = int(time.time())
        task_hash = hashlib.md5(task_description.encode()).hexdigest()[:8]
        session_id = f"{task_type}_{timestamp}_{task_hash}"
        
        # 创建会话目录
        session_dir = self.active_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        for subdir in ["inputs", "intermediates", "outputs", "logs"]:
            (session_dir / subdir).mkdir(exist_ok=True)
        
        # 创建会话对象
        session = TaskSession(
            session_id=session_id,
            task_type=task_type,
            task_description=task_description,
            created_at=datetime.now(),
            output_dir=session_dir,
            metadata={}
        )
        
        # 保存会话信息
        self.sessions[session_id] = session
        self._save_sessions()
        
        # 创建会话元数据文件
        session_metadata = {
            "session_id": session_id,
            "task_type": task_type,
            "task_description": task_description,
            "created_at": session.created_at.isoformat(),
            "status": "active"
        }
        
        with open(session_dir / "session_metadata.json", "w", encoding="utf-8") as f:
            json.dump(session_metadata, f, ensure_ascii=False, indent=2)
        
        return session
    
    def get_task_session(self, session_id: str) -> Optional[TaskSession]:
        """获取任务会话"""
        return self.sessions.get(session_id)
    
    def get_active_sessions(self) -> List[TaskSession]:
        """获取所有活跃的会话"""
        return [session for session in self.sessions.values() if session.status == "active"]
    
    def complete_task_session(self, session_id: str, final_outputs: Optional[Dict[str, Any]] = None):
        """
        完成任务会话
        
        Args:
            session_id: 会话ID
            final_outputs: 最终输出文件信息
        """
        session = self.sessions.get(session_id)
        if not session:
            return
        
        session.status = "completed"
        
        # 移动到完成目录
        if session.output_dir and session.output_dir.exists():
            completed_dir = self.completed_dir / session_id
            if completed_dir.exists():
                shutil.rmtree(completed_dir)
            shutil.move(str(session.output_dir), str(completed_dir))
            session.output_dir = completed_dir
        
        # 更新元数据
        if final_outputs:
            session.metadata.update(final_outputs)
        
        self._save_sessions()
    
    def archive_old_sessions(self, days_old: int = 7):
        """归档旧的会话"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
        
        sessions_to_archive = []
        for session in self.sessions.values():
            if (session.status == "completed" and 
                session.created_at.timestamp() < cutoff_time):
                sessions_to_archive.append(session)
        
        for session in sessions_to_archive:
            if session.output_dir and session.output_dir.exists():
                archived_dir = self.archived_dir / session.session_id
                if archived_dir.exists():
                    shutil.rmtree(archived_dir)
                shutil.move(str(session.output_dir), str(archived_dir))
                session.output_dir = archived_dir
                session.status = "archived"
        
        self._save_sessions()
    
    def cleanup_failed_sessions(self):
        """清理失败的会话"""
        for session_dir in self.active_dir.iterdir():
            if session_dir.is_dir():
                session_id = session_dir.name
                if session_id not in self.sessions:
                    # 孤立的目录，删除
                    shutil.rmtree(session_dir)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        stats = {
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() if s.status == "active"]),
            "completed_sessions": len([s for s in self.sessions.values() if s.status == "completed"]),
            "archived_sessions": len([s for s in self.sessions.values() if s.status == "archived"]),
            "task_types": {}
        }
        
        # 统计任务类型
        for session in self.sessions.values():
            task_type = session.task_type
            if task_type not in stats["task_types"]:
                stats["task_types"][task_type] = 0
            stats["task_types"][task_type] += 1
        
        return stats
    
    def _load_sessions(self) -> Dict[str, TaskSession]:
        """加载会话记录"""
        if not self.sessions_file.exists():
            return {}
        
        try:
            with open(self.sessions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            sessions = {}
            for session_data in data:
                session = TaskSession(
                    session_id=session_data["session_id"],
                    task_type=session_data["task_type"],
                    task_description=session_data["task_description"],
                    created_at=datetime.fromisoformat(session_data["created_at"]),
                    status=session_data.get("status", "active"),
                    output_dir=Path(session_data["output_dir"]) if session_data.get("output_dir") else None,
                    metadata=session_data.get("metadata", {})
                )
                sessions[session.session_id] = session
            
            return sessions
        except Exception as e:
            print(f"加载会话记录失败: {e}")
            return {}
    
    def _save_sessions(self):
        """保存会话记录"""
        try:
            sessions_data = []
            for session in self.sessions.values():
                session_data = {
                    "session_id": session.session_id,
                    "task_type": session.task_type,
                    "task_description": session.task_description,
                    "created_at": session.created_at.isoformat(),
                    "status": session.status,
                    "output_dir": str(session.output_dir) if session.output_dir else None,
                    "metadata": session.metadata or {}
                }
                sessions_data.append(session_data)
            
            with open(self.sessions_file, "w", encoding="utf-8") as f:
                json.dump(sessions_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存会话记录失败: {e}")


# 全局实例
_task_output_manager = None

def get_task_output_manager() -> TaskOutputManager:
    """获取全局任务输出管理器实例"""
    global _task_output_manager
    if _task_output_manager is None:
        _task_output_manager = TaskOutputManager()
    return _task_output_manager


# 便捷函数
def create_task_session(task_description: str, task_type: str = "general") -> TaskSession:
    """创建任务会话的便捷函数"""
    return get_task_output_manager().create_task_session(task_description, task_type)


def get_task_session(session_id: str) -> Optional[TaskSession]:
    """获取任务会话的便捷函数"""
    return get_task_output_manager().get_task_session(session_id)


def complete_task_session(session_id: str, final_outputs: Optional[Dict[str, Any]] = None):
    """完成任务会话的便捷函数"""
    return get_task_output_manager().complete_task_session(session_id, final_outputs)