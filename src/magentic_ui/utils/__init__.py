"""
Magentic-UI实用工具模块
"""

import json
import logging
import os
import psutil
from typing import List, Union, Dict
from autogen_core.models import (
    LLMMessage,
    UserMessage,
    AssistantMessage,
)
from autogen_agentchat.utils import remove_images
from autogen_agentchat.messages import (
    BaseChatMessage,
    BaseTextChatMessage,
    HandoffMessage,
    MultiModalMessage,
    StopMessage,
    TextMessage,
    ToolCallRequestEvent,
    ToolCallExecutionEvent,
    BaseAgentEvent,
)

from .conversation_storage_manager import (
    get_conversation_storage_manager,
    add_conversation_file,
    add_conversation_text_file,
    get_conversation_files,
    mark_file_as_deliverable,
    ConversationFile,
    FileType
)

from .intelligent_deliverable_analyzer import (
    get_deliverable_analyzer,
    analyze_conversation_deliverables,
    DeliverableRecommendation,
    DeliverableAnalysis
)

# Define recursive types for JSON structures
JsonPrimitive = Union[str, int, float, bool, None]
JsonList = List[Union[JsonPrimitive, "JsonDict", "JsonList"]]
JsonDict = Dict[str, Union[JsonPrimitive, JsonList, "JsonDict"]]

def dict_to_str(data: Union[JsonDict, str]) -> str:
    """
    Convert a dictionary or JSON string to a JSON string.

    Args:
        data (JsonDict | str): The dictionary or JSON string to convert.

    Returns:
        str: The input dictionary in JSON format.
    """
    if isinstance(data, dict):
        return json.dumps(data)
    elif isinstance(data, str):
        return data
    else:
        raise ValueError("Unexpected input type")

def thread_to_context(
    messages: List[BaseAgentEvent | BaseChatMessage],
    agent_name: str,
    is_multimodal: bool = False,
) -> List[LLMMessage]:
    """Convert the message thread to a context for the model."""
    from ..types import HumanInputFormat
    
    context: List[LLMMessage] = []
    for m in messages:
        if isinstance(m, ToolCallRequestEvent | ToolCallExecutionEvent):
            # Ignore tool call messages.
            continue
        elif isinstance(m, StopMessage | HandoffMessage):
            context.append(UserMessage(content=m.content, source=m.source))
        elif m.source == agent_name:
            assert isinstance(m, TextMessage | MultiModalMessage), f"{type(m)}"
            if isinstance(m, MultiModalMessage):
                # 对于MultiModalMessage，只使用文本内容
                if isinstance(m.content, list) and len(m.content) > 0:
                    # 提取第一个文本内容
                    text_content = next((item for item in m.content if isinstance(item, str)), str(m.content))
                    context.append(AssistantMessage(content=text_content, source=m.source))
                else:
                    context.append(AssistantMessage(content=str(m.content), source=m.source))
            else:
                context.append(AssistantMessage(content=m.content, source=m.source))
        elif m.source == "user_proxy" or m.source == "user":
            assert isinstance(m, TextMessage | MultiModalMessage), f"{type(m)}"
            if isinstance(m.content, str):
                human_input = HumanInputFormat.from_str(m.content)
                content = f"{human_input.content}"
                if human_input.plan is not None:
                    content += f"\n\nI created the following plan: {human_input.plan}"
                context.append(UserMessage(content=content, source=m.source))
            else:
                # If content is a list, transform only the string part
                content_list = list(m.content)  # Create a copy of the list
                for i, item in enumerate(content_list):
                    if isinstance(item, str):
                        human_input = HumanInputFormat.from_str(item)
                        content_list[i] = f"{human_input.content}"
                        if human_input.plan is not None and isinstance(
                            content_list[i], str
                        ):
                            content_list[i] = (
                                f"{content_list[i]}\n\nI created the following plan: {human_input.plan}"
                            )
                context.append(UserMessage(content=content_list, source=m.source))  # type: ignore
        else:
            assert isinstance(m, BaseTextChatMessage) or isinstance(
                m, MultiModalMessage
            ), f"{type(m)}"
            context.append(UserMessage(content=m.content, source=m.source))
    if is_multimodal:
        return context
    else:
        return remove_images(context)

class LLMCallFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = json.loads(record.getMessage())
            return message.get("type") == "LLMCall"
        except (json.JSONDecodeError, AttributeError):
            return False

def get_internal_urls(inside_docker: bool, paths) -> List[str] | None:
    if not inside_docker:
        return None
    urls: List[str] = []
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name == "AF_INET":
                urls.append(addr.address)

    hostname = os.getenv("HOSTNAME")
    if hostname is not None:
        urls.append(hostname)
    container_name = os.getenv("CONTAINER_NAME")
    if container_name is not None:
        urls.append(container_name)
    return urls

__all__ = [
    'get_conversation_storage_manager',
    'add_conversation_file', 
    'add_conversation_text_file',
    'get_conversation_files',
    'mark_file_as_deliverable',
    'ConversationFile',
    'FileType',
    'get_deliverable_analyzer',
    'analyze_conversation_deliverables',
    'DeliverableRecommendation',
    'DeliverableAnalysis',
    'dict_to_str',
    'thread_to_context',
    'LLMCallFilter',
    'get_internal_urls'
]