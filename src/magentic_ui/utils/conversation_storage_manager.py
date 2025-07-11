"""
对话级存储管理器 - 每个对话独立文件管理
支持每个session独立的文件存储和智能文件提交分析
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import hashlib
import mimetypes
from enum import Enum

class FileType(Enum):
    """文件类型枚举"""
    IMAGE = "image"
    DOCUMENT = "document"  
    CODE = "code"
    DATA = "data"
    MEDIA = "media"
    OTHER = "other"

@dataclass
class ConversationFile:
    """对话文件信息"""
    file_path: Path
    relative_path: str
    file_type: FileType
    size: int
    created_at: datetime
    created_by: str  # agent名称
    description: Optional[str] = None
    tags: List[str] = None
    is_intermediate: bool = True  # 是否为中间产物
    is_deliverable: bool = False  # 是否为最终交付物

@dataclass 
class ConversationStorage:
    """对话存储信息"""
    session_id: int
    conversation_dir: Path
    files: Dict[str, ConversationFile] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.files is None:
            self.files = {}
        if self.metadata is None:
            self.metadata = {}

class ConversationStorageManager:
    """
    对话存储管理器
    
    设计理念：
    - 每个对话(session)有独立的文件存储目录
    - 支持多种文件类型的分类存储
    - 智能识别中间产物和最终交付物
    - 提供文件元数据管理和检索功能
    """
    
    def __init__(self, base_storage_dir: str = "conversation_storage"):
        self.base_storage_dir = Path(base_storage_dir)
        self.base_storage_dir.mkdir(exist_ok=True)
        
        # 存储结构：conversation_storage/session_{id}/
        #   ├── inputs/          # 输入文件
        #   ├── documents/       # 文档类文件(md, pdf, html等)
        #   ├── images/          # 图片文件 
        #   ├── code/           # 代码文件
        #   ├── data/           # 数据文件(json, csv等)
        #   ├── media/          # 媒体文件(视频、音频等)
        #   ├── outputs/        # 最终输出文件
        #   ├── logs/           # 日志文件
        #   └── metadata.json   # 文件元数据
        
        self.conversations: Dict[int, ConversationStorage] = {}
        self._load_existing_conversations()
    
    def get_or_create_conversation_storage(self, session_id: int) -> ConversationStorage:
        """获取或创建对话存储"""
        if session_id not in self.conversations:
            conversation_dir = self.base_storage_dir / f"session_{session_id}"
            conversation_dir.mkdir(exist_ok=True)
            
            # 创建子目录
            subdirs = ["inputs", "documents", "images", "code", "data", "media", "outputs", "logs"]
            for subdir in subdirs:
                (conversation_dir / subdir).mkdir(exist_ok=True)
            
            storage = ConversationStorage(
                session_id=session_id,
                conversation_dir=conversation_dir,
                files={},
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "session_id": session_id,
                    "total_files": 0,
                    "file_types": {}
                }
            )
            
            self.conversations[session_id] = storage
            self._save_conversation_metadata(session_id)
        
        return self.conversations[session_id]
    
    def add_file(self, session_id: int, file_content: bytes, filename: str, 
                 agent_name: str, description: str = None, 
                 is_intermediate: bool = True, tags: List[str] = None) -> ConversationFile:
        """添加文件到对话存储"""
        storage = self.get_or_create_conversation_storage(session_id)
        
        # 确定文件类型和存储目录
        file_type = self._detect_file_type(filename)
        subdir = self._get_storage_subdir(file_type, is_intermediate)
        
        # 创建唯一文件名（避免冲突）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{timestamp}_{name}{ext}"
        
        file_path = storage.conversation_dir / subdir / unique_filename
        relative_path = str(Path(subdir) / unique_filename)
        
        # 保存文件
        file_path.write_bytes(file_content)
        
        # 创建文件信息
        conversation_file = ConversationFile(
            file_path=file_path,
            relative_path=relative_path,
            file_type=file_type,
            size=len(file_content),
            created_at=datetime.now(),
            created_by=agent_name,
            description=description,
            tags=tags or [],
            is_intermediate=is_intermediate,
            is_deliverable=not is_intermediate
        )
        
        # 添加到存储记录
        file_id = f"{agent_name}_{timestamp}_{name}"
        storage.files[file_id] = conversation_file
        
        # 更新元数据
        storage.metadata["total_files"] = len(storage.files)
        if file_type.value not in storage.metadata["file_types"]:
            storage.metadata["file_types"][file_type.value] = 0
        storage.metadata["file_types"][file_type.value] += 1
        storage.metadata["last_updated"] = datetime.now().isoformat()
        
        self._save_conversation_metadata(session_id)
        
        return conversation_file
    
    def add_text_file(self, session_id: int, content: str, filename: str,
                     agent_name: str, description: str = None,
                     is_intermediate: bool = True, tags: List[str] = None) -> ConversationFile:
        """添加文本文件到对话存储"""
        return self.add_file(
            session_id=session_id,
            file_content=content.encode('utf-8'),
            filename=filename,
            agent_name=agent_name,
            description=description,
            is_intermediate=is_intermediate,
            tags=tags
        )
    
    def get_conversation_files(self, session_id: int, 
                             file_type: Optional[FileType] = None,
                             agent_name: Optional[str] = None,
                             is_deliverable_only: bool = False) -> List[ConversationFile]:
        """获取对话的文件列表"""
        if session_id not in self.conversations:
            return []
        
        storage = self.conversations[session_id]
        files = list(storage.files.values())
        
        # 过滤条件
        if file_type:
            files = [f for f in files if f.file_type == file_type]
        
        if agent_name:
            files = [f for f in files if f.created_by == agent_name]
        
        if is_deliverable_only:
            files = [f for f in files if f.is_deliverable]
        
        # 按创建时间排序
        files.sort(key=lambda x: x.created_at, reverse=True)
        
        return files
    
    def get_file_content(self, session_id: int, file_id: str) -> Optional[bytes]:
        """获取文件内容"""
        if session_id not in self.conversations:
            return None
        
        storage = self.conversations[session_id]
        if file_id not in storage.files:
            return None
        
        file_info = storage.files[file_id]
        if file_info.file_path.exists():
            return file_info.file_path.read_bytes()
        
        return None
    
    def mark_as_deliverable(self, session_id: int, file_id: str, 
                           description: str = None):
        """标记文件为最终交付物"""
        if session_id not in self.conversations:
            return
        
        storage = self.conversations[session_id]
        if file_id in storage.files:
            file_info = storage.files[file_id]
            file_info.is_deliverable = True
            file_info.is_intermediate = False
            if description:
                file_info.description = description
            
            self._save_conversation_metadata(session_id)
    
    def get_conversation_summary(self, session_id: int) -> Dict[str, Any]:
        """获取对话存储摘要"""
        if session_id not in self.conversations:
            return {}
        
        storage = self.conversations[session_id]
        files = list(storage.files.values())
        
        deliverable_files = [f for f in files if f.is_deliverable]
        intermediate_files = [f for f in files if f.is_intermediate]
        
        # 按agent分组统计
        agent_stats = {}
        for file in files:
            agent = file.created_by
            if agent not in agent_stats:
                agent_stats[agent] = {"total": 0, "deliverable": 0, "file_types": {}}
            
            agent_stats[agent]["total"] += 1
            if file.is_deliverable:
                agent_stats[agent]["deliverable"] += 1
            
            file_type = file.file_type.value
            if file_type not in agent_stats[agent]["file_types"]:
                agent_stats[agent]["file_types"][file_type] = 0
            agent_stats[agent]["file_types"][file_type] += 1
        
        return {
            "session_id": session_id,
            "total_files": len(files),
            "deliverable_files": len(deliverable_files),
            "intermediate_files": len(intermediate_files),
            "file_types": storage.metadata.get("file_types", {}),
            "agent_statistics": agent_stats,
            "storage_path": str(storage.conversation_dir),
            "created_at": storage.metadata.get("created_at"),
            "last_updated": storage.metadata.get("last_updated")
        }
    
    def _detect_file_type(self, filename: str) -> FileType:
        """检测文件类型"""
        ext = Path(filename).suffix.lower()
        
        # 图片文件
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp']:
            return FileType.IMAGE
        
        # 文档文件
        elif ext in ['.md', '.pdf', '.html', '.htm', '.txt', '.doc', '.docx']:
            return FileType.DOCUMENT
        
        # 代码文件
        elif ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go']:
            return FileType.CODE
        
        # 数据文件
        elif ext in ['.json', '.csv', '.xml', '.yaml', '.yml', '.sql']:
            return FileType.DATA
        
        # 媒体文件
        elif ext in ['.mp4', '.avi', '.mov', '.mp3', '.wav', '.flac']:
            return FileType.MEDIA
        
        else:
            return FileType.OTHER
    
    def _get_storage_subdir(self, file_type: FileType, is_intermediate: bool) -> str:
        """获取存储子目录"""
        if not is_intermediate:
            return "outputs"
        
        return {
            FileType.IMAGE: "images",
            FileType.DOCUMENT: "documents", 
            FileType.CODE: "code",
            FileType.DATA: "data",
            FileType.MEDIA: "media",
            FileType.OTHER: "data"
        }.get(file_type, "data")
    
    def _save_conversation_metadata(self, session_id: int):
        """保存对话元数据"""
        if session_id not in self.conversations:
            return
        
        storage = self.conversations[session_id]
        metadata_file = storage.conversation_dir / "metadata.json"
        
        # 构建文件列表（用于保存）
        files_data = {}
        for file_id, file_info in storage.files.items():
            files_data[file_id] = {
                "relative_path": file_info.relative_path,
                "file_type": file_info.file_type.value,
                "size": file_info.size,
                "created_at": file_info.created_at.isoformat(),
                "created_by": file_info.created_by,
                "description": file_info.description,
                "tags": file_info.tags,
                "is_intermediate": file_info.is_intermediate,
                "is_deliverable": file_info.is_deliverable
            }
        
        metadata = {
            **storage.metadata,
            "files": files_data
        }
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _load_existing_conversations(self):
        """加载已存在的对话存储"""
        if not self.base_storage_dir.exists():
            return
        
        for session_dir in self.base_storage_dir.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith("session_"):
                try:
                    session_id = int(session_dir.name.replace("session_", ""))
                    metadata_file = session_dir / "metadata.json"
                    
                    if metadata_file.exists():
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        
                        # 重建文件信息
                        files = {}
                        files_data = metadata.get("files", {})
                        
                        for file_id, file_data in files_data.items():
                            file_path = session_dir / file_data["relative_path"]
                            if file_path.exists():
                                files[file_id] = ConversationFile(
                                    file_path=file_path,
                                    relative_path=file_data["relative_path"],
                                    file_type=FileType(file_data["file_type"]),
                                    size=file_data["size"],
                                    created_at=datetime.fromisoformat(file_data["created_at"]),
                                    created_by=file_data["created_by"],
                                    description=file_data.get("description"),
                                    tags=file_data.get("tags", []),
                                    is_intermediate=file_data.get("is_intermediate", True),
                                    is_deliverable=file_data.get("is_deliverable", False)
                                )
                        
                        storage = ConversationStorage(
                            session_id=session_id,
                            conversation_dir=session_dir,
                            files=files,
                            metadata=metadata
                        )
                        
                        self.conversations[session_id] = storage
                        
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    print(f"Error loading conversation {session_dir.name}: {e}")
                    continue

# 全局实例
_conversation_storage_manager = None

def get_conversation_storage_manager() -> ConversationStorageManager:
    """获取全局对话存储管理器实例"""
    global _conversation_storage_manager
    if _conversation_storage_manager is None:
        _conversation_storage_manager = ConversationStorageManager()
    return _conversation_storage_manager

# 便捷函数
def add_conversation_file(session_id: int, file_content: bytes, filename: str,
                         agent_name: str, description: str = None,
                         is_intermediate: bool = True, tags: List[str] = None) -> ConversationFile:
    """添加文件到对话存储的便捷函数"""
    return get_conversation_storage_manager().add_file(
        session_id=session_id,
        file_content=file_content,
        filename=filename,
        agent_name=agent_name,
        description=description,
        is_intermediate=is_intermediate,
        tags=tags
    )

def add_conversation_text_file(session_id: int, content: str, filename: str,
                              agent_name: str, description: str = None,
                              is_intermediate: bool = True, tags: List[str] = None) -> ConversationFile:
    """添加文本文件到对话存储的便捷函数"""
    return get_conversation_storage_manager().add_text_file(
        session_id=session_id,
        content=content,
        filename=filename,
        agent_name=agent_name,
        description=description,
        is_intermediate=is_intermediate,
        tags=tags
    )

def get_conversation_files(session_id: int, **kwargs) -> List[ConversationFile]:
    """获取对话文件列表的便捷函数"""
    return get_conversation_storage_manager().get_conversation_files(session_id, **kwargs)

def mark_file_as_deliverable(session_id: int, file_id: str, description: str = None):
    """标记文件为交付物的便捷函数"""
    return get_conversation_storage_manager().mark_as_deliverable(session_id, file_id, description)