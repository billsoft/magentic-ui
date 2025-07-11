from typing import Any, ClassVar, Dict, List, Literal, Optional, Union

from autogen_core import ComponentModel
from pydantic import BaseModel, Field

from .agents.mcp import McpAgentConfig
from .types import Plan


class ModelClientConfigs(BaseModel):
    """Configurations for the model clients.
    Attributes:
        default_client_config (dict): Default configuration for the model clients.
        orchestrator (Optional[Union[ComponentModel, Dict[str, Any]]]): Configuration for the orchestrator component. Default: None.
        web_surfer (Optional[Union[ComponentModel, Dict[str, Any]]]): Configuration for the web surfer component. Default: None.
        coder (Optional[Union[ComponentModel, Dict[str, Any]]]): Configuration for the coder component. Default: None.
        file_surfer (Optional[Union[ComponentModel, Dict[str, Any]]]): Configuration for the file surfer component. Default: None.
        action_guard (Optional[Union[ComponentModel, Dict[str, Any]]]): Configuration for the action guard component. Default: None.
        image_generator (Optional[Union[ComponentModel, Dict[str, Any]]]): Configuration for the image generator component. Default: None.
    """

    orchestrator: Optional[Union[ComponentModel, Dict[str, Any]]] = None
    web_surfer: Optional[Union[ComponentModel, Dict[str, Any]]] = None
    coder: Optional[Union[ComponentModel, Dict[str, Any]]] = None
    file_surfer: Optional[Union[ComponentModel, Dict[str, Any]]] = None
    action_guard: Optional[Union[ComponentModel, Dict[str, Any]]] = None
    image_generator: Optional[Union[ComponentModel, Dict[str, Any]]] = None

    # 🔧 默认配置现在使用配置文件中的模型，而不是硬编码
    default_client_config: ClassVar[Dict[str, Any]] = {
        "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
        "config": {
            "model": "anthropic/claude-3-5-sonnet-20241022",  # 🔧 更改为配置文件中的模型
            "api_key": "$OPENROUTER_API_KEY",  # 🔧 使用配置文件中的API密钥
            "base_url": "https://openrouter.ai/api/v1",  # 🔧 使用配置文件中的base_url
            "timeout": 180.0,  # 🔧 增加超时时间到3分钟
            "max_retries": 8,  # 🔧 增加重试次数
            # 🔧 增强网络连接稳定性配置
            "http_client_config": {
                "connect": 60.0,  # 🔧 连接超时60秒
                "read": 180.0,    # 🔧 读取超时3分钟
                "write": 60.0,    # 🔧 写入超时60秒
                "pool": 120.0,    # 🔧 连接池超时2分钟
            },
            "retry_config": {
                "max_retries": 8,  # 🔧 增加重试次数
                "exponential_base": 2,
                "jitter": True,
                "max_delay": 120.0,  # 🔧 最大延迟2分钟
                "retry_on_timeout": True,
                "retry_on_connection_error": True,
                "retry_on_rate_limit": True,  # 🔧 添加速率限制重试
            }
        }
    }
    default_action_guard_config: ClassVar[Dict[str, Any]] = {
        "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient", 
        "config": {
            "model": "anthropic/claude-3-5-sonnet-20241022",  # 🔧 更改为配置文件中的模型
            "api_key": "$OPENROUTER_API_KEY",  # 🔧 使用配置文件中的API密钥
            "base_url": "https://openrouter.ai/api/v1",  # 🔧 使用配置文件中的base_url
            "timeout": 180.0,  # 🔧 增加超时时间到3分钟
            "max_retries": 8,  # 🔧 增加重试次数
            # 🔧 增强网络连接稳定性配置
            "http_client_config": {
                "connect": 60.0,  # 🔧 连接超时60秒
                "read": 180.0,    # 🔧 读取超时3分钟
                "write": 60.0,    # 🔧 写入超时60秒
                "pool": 120.0,    # 🔧 连接池超时2分钟
            },
            "retry_config": {
                "max_retries": 8,  # 🔧 增加重试次数
                "exponential_base": 2,
                "jitter": True,
                "max_delay": 120.0,  # 🔧 最大延迟2分钟
                "retry_on_timeout": True,
                "retry_on_connection_error": True,
                "retry_on_rate_limit": True,  # 🔧 添加速率限制重试
            }
        }
    }

    @classmethod
    def get_default_client_config(cls) -> Dict[str, Any]:
        return cls.default_client_config

    @classmethod
    def get_default_action_guard_config(cls) -> Dict[str, Any]:
        return cls.default_action_guard_config


class MagenticUIConfig(BaseModel):
    """
    A simplified set of configuration options for Magentic-UI.

    Attributes:
        model_client_configs (ModelClientConfigs): Configurations for the model client.
        mcp_agent_configs (List[McpAgentConfig], optional): Configs for AssistantAgents with access to MCP Servers.
        cooperative_planning (bool): Enable co-planning mode (default: enabled), user will be involved in the planning process. Default: True.
        autonomous_execution (bool): Enable autonomous execution mode (default: disabled), user will not be involved in the execution. Default: False.
        allowed_websites (List[str], optional): List of websites that are permitted.
        max_actions_per_step (int): Maximum number of actions allowed per step. Default: 5.
        multiple_tools_per_call (bool): Allow multiple tools to be called in a single step. Default: False.
        max_turns (int): Maximum number of operational turns allowed. Default: 20.
        plan (Plan, optional): A pre-defined plan. In cooperative planning mode, the plan will be enhanced with user feedback.
        approval_policy (str, optional): Policy for action approval. Default: "auto-conservative".
        allow_for_replans (bool): Whether to allow the orchestrator to create a new plan when needed. Default: True.
        do_bing_search (bool): Flag to determine if Bing search should be used to come up with information for the plan. Default: False.
        websurfer_loop (bool): Flag to determine if the websurfer should loop through the plan. Default: False.
        retrieve_relevant_plans (Literal["never", "hint", "reuse"]): Determines if the orchestrator should retrieve relevant plans from memory. Default: `never`.
        memory_controller_key (str, optional): The key to retrieve the memory_controller for a particular user. Default: None.
        model_context_token_limit (int, optional): The maximum number of tokens the model can use. Default: 110000.
        allow_follow_up_input (bool): Flag to determine if new input should be requested after a final answer is given. Default: True.
        final_answer_prompt (str, optional): Prompt for the final answer. Should be a string that can be formatted with the {task} variable. Default: None.
        playwright_port (int, optional): Port for the Playwright browser. Default: -1 (auto-assign).
        novnc_port (int, optional): Port for the noVNC server. Default: -1 (auto-assign).
        user_proxy_type (str, optional): Type of user proxy agent to use ("dummy", "metadata", or None for default). Default: None.
        task (str, optional): Task to be performed by the agents. Default: None.
        hints (str, optional): Helpful hints for the task. Default: None.
        answer (str, optional): Answer to the task. Default: None.
        inside_docker (bool, optional): Whether to run inside a docker container. Default: True.
        browser_headless (bool, optional): Whether to run a headless browser or not. Default: False.
        browser_local (bool, optional): Whether to run a local browser (as opposed to dockerized browser). Default: False.
        sentinel_tasks (bool, optional): Whether to enable SentinelPlanStep functionality. Default: False.
        run_without_docker (bool, optional): If docker is not available, run without docker for browser, remove coder and filesurfer agents. Default: False.
    """

    model_client_configs: ModelClientConfigs = Field(default_factory=ModelClientConfigs)
    mcp_agent_configs: List[McpAgentConfig] = Field(default_factory=lambda: [])
    cooperative_planning: bool = True
    autonomous_execution: bool = False
    allowed_websites: Optional[List[str]] = None
    max_actions_per_step: int = 5
    multiple_tools_per_call: bool = False
    max_turns: int = 20
    plan: Optional[Plan] = None
    approval_policy: Literal[
        "always", "never", "auto-conservative", "auto-permissive"
    ] = "auto-conservative"
    allow_for_replans: bool = True
    do_bing_search: bool = False
    websurfer_loop: bool = False
    retrieve_relevant_plans: Literal["never", "hint", "reuse"] = "never"
    memory_controller_key: Optional[str] = None
    model_context_token_limit: int = 110000
    allow_follow_up_input: bool = True
    final_answer_prompt: str | None = None
    playwright_port: int = -1
    novnc_port: int = -1
    user_proxy_type: Optional[str] = None
    task: Optional[str] = None
    hints: Optional[str] = None
    answer: Optional[str] = None
    inside_docker: bool = True
    browser_local: bool = False
    sentinel_tasks: bool = False
    run_without_docker: bool = False
    browser_headless: bool = False
