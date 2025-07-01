import os
import copy
from typing import Any, Dict, List, Optional, Union

from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.base import ChatAgent
from autogen_core import ComponentModel
from autogen_core.models import ChatCompletionClient

from .agents import USER_PROXY_DESCRIPTION, CoderAgent, FileSurfer, WebSurfer
from .agents._image_generator import ImageGeneratorAgent
from .agents.mcp import McpAgent
from .agents.users import DummyUserProxy, MetadataUserProxy
from .agents.web_surfer import WebSurferConfig
from .tools.image_generation import ImageGenerationClient
from .approval_guard import (
    ApprovalConfig,
    ApprovalGuard,
    ApprovalGuardContext,
    BaseApprovalGuard,
)
from .input_func import InputFuncType, make_agentchat_input_func
from .learning.memory_provider import MemoryControllerProvider
from .magentic_ui_config import MagenticUIConfig, ModelClientConfigs
from .teams import GroupChat, RoundRobinGroupChat
from .teams.orchestrator.orchestrator_config import OrchestratorConfig
from .tools.playwright.browser import get_browser_resource_config
from .types import RunPaths
from .utils import get_internal_urls


def resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """递归解析配置中的环境变量"""
    resolved_config = copy.deepcopy(config)
    
    def _resolve_dict(obj: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in obj.items():
            if isinstance(value, str) and value.startswith('$'):
                # 解析环境变量
                env_var = value[1:]  # 移除 $ 前缀
                env_value = os.getenv(env_var)
                if env_value:
                    obj[key] = env_value
                else:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"⚠️ 环境变量 {env_var} 未设置，保留原值: {value}")
            elif isinstance(value, dict):
                obj[key] = _resolve_dict(value)
            elif isinstance(value, list):
                obj[key] = _resolve_list(value)
        return obj
    
    def _resolve_list(obj: List[Any]) -> List[Any]:
        for i, item in enumerate(obj):
            if isinstance(item, str) and item.startswith('$'):
                env_var = item[1:]
                env_value = os.getenv(env_var)
                if env_value:
                    obj[i] = env_value
            elif isinstance(item, dict):
                obj[i] = _resolve_dict(item)
            elif isinstance(item, list):
                obj[i] = _resolve_list(item)
        return obj
    
    if isinstance(resolved_config, dict):
        return _resolve_dict(resolved_config)
    return resolved_config


async def get_task_team(
    magentic_ui_config: Optional[MagenticUIConfig] = None,
    input_func: Optional[InputFuncType] = None,
    *,
    paths: RunPaths,
) -> GroupChat | RoundRobinGroupChat:
    """
    Creates and returns a GroupChat team with specified configuration.

    Args:
        magentic_ui_config (MagenticUIConfig, optional): Magentic UI configuration for team. Default: None.
        paths (RunPaths): Paths for internal and external run directories.

    Returns:
        GroupChat | RoundRobinGroupChat: An instance of GroupChat or RoundRobinGroupChat with the specified agents and configuration.
    """
    if magentic_ui_config is None:
        magentic_ui_config = MagenticUIConfig()

    def get_model_client(
        model_client_config: Union[ComponentModel, Dict[str, Any], None],
        is_action_guard: bool = False,
    ) -> ChatCompletionClient:
        if model_client_config is None:
            return ChatCompletionClient.load_component(
                ModelClientConfigs.get_default_client_config()
                if not is_action_guard
                else ModelClientConfigs.get_default_action_guard_config()
            )
        
        # 处理配置格式
        if isinstance(model_client_config, ComponentModel):
            config_dict = model_client_config.model_dump()
        elif isinstance(model_client_config, dict):
            config_dict = model_client_config
        else:
            config_dict = dict(model_client_config) if hasattr(model_client_config, 'items') else {}
        
        # 解析环境变量
        resolved_config = resolve_env_vars(config_dict)
        
        # 添加调试日志
        import logging
        logger = logging.getLogger(__name__)
        api_key = resolved_config.get('config', {}).get('api_key', '')
        if api_key:
            logger.info(f"🔑 API密钥已解析: {api_key[:10]}...")
        else:
            logger.warning("⚠️ API密钥未找到或为空")
        
        return ChatCompletionClient.load_component(resolved_config)

    if not magentic_ui_config.inside_docker:
        assert (
            paths.external_run_dir == paths.internal_run_dir
        ), "External and internal run dirs must be the same in non-docker mode"

    model_client_orch = get_model_client(
        magentic_ui_config.model_client_configs.orchestrator
    )
    approval_guard: BaseApprovalGuard | None = None

    approval_policy = (
        magentic_ui_config.approval_policy
        if magentic_ui_config.approval_policy
        else "never"
    )

    websurfer_loop_team: bool = (
        magentic_ui_config.websurfer_loop if magentic_ui_config else False
    )

    model_client_coder = get_model_client(magentic_ui_config.model_client_configs.coder)
    model_client_file_surfer = get_model_client(
        magentic_ui_config.model_client_configs.file_surfer
    )
    # 图像生成客户端配置将在后面专门处理
    browser_resource_config, _novnc_port, _playwright_port = (
        get_browser_resource_config(
            paths.external_run_dir,
            magentic_ui_config.novnc_port,
            magentic_ui_config.playwright_port,
            magentic_ui_config.inside_docker,
            headless=magentic_ui_config.browser_headless,
            local=magentic_ui_config.browser_local
            or magentic_ui_config.run_without_docker,
        )
    )

    orchestrator_config = OrchestratorConfig(
        cooperative_planning=magentic_ui_config.cooperative_planning,
        autonomous_execution=magentic_ui_config.autonomous_execution,
        allowed_websites=magentic_ui_config.allowed_websites,
        plan=magentic_ui_config.plan,
        model_context_token_limit=magentic_ui_config.model_context_token_limit,
        do_bing_search=magentic_ui_config.do_bing_search,
        retrieve_relevant_plans=magentic_ui_config.retrieve_relevant_plans,
        memory_controller_key=magentic_ui_config.memory_controller_key,
        allow_follow_up_input=magentic_ui_config.allow_follow_up_input,
        final_answer_prompt=magentic_ui_config.final_answer_prompt,
    )
    websurfer_model_client = magentic_ui_config.model_client_configs.web_surfer
    if websurfer_model_client is None:
        websurfer_model_client = ModelClientConfigs.get_default_client_config()
    websurfer_config = WebSurferConfig(
        name="web_surfer",
        model_client=websurfer_model_client,
        browser=browser_resource_config,
        single_tab_mode=False,
        max_actions_per_step=magentic_ui_config.max_actions_per_step,
        url_statuses={key: "allowed" for key in orchestrator_config.allowed_websites}
        if orchestrator_config.allowed_websites
        else None,
        url_block_list=get_internal_urls(magentic_ui_config.inside_docker, paths),
        multiple_tools_per_call=magentic_ui_config.multiple_tools_per_call,
        downloads_folder=str(paths.internal_run_dir),
        debug_dir=str(paths.internal_run_dir),
        animate_actions=True,
        start_page=None,
        use_action_guard=True,
        to_save_screenshots=False,
    )

    user_proxy: DummyUserProxy | MetadataUserProxy | UserProxyAgent

    if magentic_ui_config.user_proxy_type == "dummy":
        user_proxy = DummyUserProxy(name="user_proxy")
    elif magentic_ui_config.user_proxy_type == "metadata":
        assert (
            magentic_ui_config.task is not None
        ), "Task must be provided for metadata user proxy"
        assert (
            magentic_ui_config.hints is not None
        ), "Hints must be provided for metadata user proxy"
        assert (
            magentic_ui_config.answer is not None
        ), "Answer must be provided for metadata user proxy"
        user_proxy = MetadataUserProxy(
            name="user_proxy",
            description="Metadata User Proxy Agent",
            task=magentic_ui_config.task,
            helpful_task_hints=magentic_ui_config.hints,
            task_answer=magentic_ui_config.answer,
            model_client=model_client_orch,
        )
    else:
        user_proxy_input_func = make_agentchat_input_func(input_func)
        user_proxy = UserProxyAgent(
            description=USER_PROXY_DESCRIPTION,
            name="user_proxy",
            input_func=user_proxy_input_func,
        )

    if magentic_ui_config.user_proxy_type in ["dummy", "metadata"]:
        model_client_action_guard = get_model_client(
            magentic_ui_config.model_client_configs.action_guard,
            is_action_guard=True,
        )

        # Simple approval function that always returns yes
        def always_yes_input(prompt: str, input_type: str = "text_input") -> str:
            return "yes"

        approval_guard = ApprovalGuard(
            input_func=always_yes_input,
            default_approval=False,
            model_client=model_client_action_guard,
            config=ApprovalConfig(
                approval_policy=approval_policy,
            ),
        )
    elif input_func is not None:
        model_client_action_guard = get_model_client(
            magentic_ui_config.model_client_configs.action_guard
        )
        approval_guard = ApprovalGuard(
            input_func=input_func,
            default_approval=False,
            model_client=model_client_action_guard,
            config=ApprovalConfig(
                approval_policy=approval_policy,
            ),
        )
    with ApprovalGuardContext.populate_context(approval_guard):
        web_surfer = WebSurfer.from_config(websurfer_config)
    if websurfer_loop_team:
        # simplified team of only the web surfer
        team = RoundRobinGroupChat(
            participants=[web_surfer, user_proxy],
            max_turns=10000,
        )
        await team.lazy_init()
        return team
    coder_agent: CoderAgent | None = None
    file_surfer: FileSurfer | None = None
    if not magentic_ui_config.run_without_docker:
        coder_agent = CoderAgent(
            name="coder_agent",
            model_client=model_client_coder,
            work_dir=paths.internal_run_dir,
            bind_dir=paths.external_run_dir,
            model_context_token_limit=magentic_ui_config.model_context_token_limit,
            approval_guard=approval_guard,
        )

        file_surfer = FileSurfer(
            name="file_surfer",
            model_client=model_client_file_surfer,
            work_dir=paths.internal_run_dir,
            bind_dir=paths.external_run_dir,
            model_context_token_limit=magentic_ui_config.model_context_token_limit,
            approval_guard=approval_guard,
        )

    # Setup any mcp_agents
    mcp_agents: List[McpAgent] = [
        # TODO: Init from constructor?
        McpAgent._from_config(config)  # type: ignore
        for config in magentic_ui_config.mcp_agent_configs
    ]

    # 创建图像生成代理 (总是可用，无需Docker)
    image_generator_agent: ImageGeneratorAgent | None = None
    try:
        # 获取图像生成客户端配置
        image_client_config = (
            magentic_ui_config.model_client_configs.image_generator or 
            magentic_ui_config.model_client_configs.orchestrator
        )
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🎨 初始化图像生成代理 - 配置类型: {type(image_client_config)}")
        
        # 创建专用的图像生成客户端
        if image_client_config is not None:
            # 处理配置转换
            if isinstance(image_client_config, ComponentModel):
                config_dict = image_client_config.model_dump()
            elif isinstance(image_client_config, dict):
                config_dict = image_client_config
            else:
                config_dict = dict(image_client_config) if hasattr(image_client_config, 'items') else {}
            
            # ✅ 关键修复：解析环境变量
            resolved_config = resolve_env_vars(config_dict)
            
            # 检查是否是专用图像生成配置
            provider = resolved_config.get('provider', '')
            client_config = resolved_config.get('config', {})
            
            logger.info(f"🔧 图像生成配置 - 提供者: {provider}")
            logger.info(f"🔑 API密钥检查: {'已设置' if client_config.get('api_key') else '未设置'}")
            
            if provider == 'direct_openai_image_client':
                # 专用图像生成客户端：直接创建ImageGenerationClient
                image_client = ImageGenerationClient(
                    api_key=client_config.get('api_key', ''),
                    base_url=client_config.get('base_url', 'https://api.openai.com/v1'),
                    default_model=client_config.get('model', 'dall-e-3'),
                    timeout=client_config.get('timeout', 60)
                )
                logger.info(f"✅ 创建专用图像生成客户端成功")
            else:
                # 降级：从聊天客户端配置创建（已解析环境变量）
                image_client = ImageGenerationClient.from_chat_client_config(resolved_config)
                logger.info(f"✅ 从聊天客户端配置创建图像生成客户端")
        else:
            # 使用默认OpenAI配置
            logger.warning("⚠️ 未找到图像生成配置，使用默认OpenAI配置")
            openai_key = os.getenv("OPENAI_API_KEY", "")
            if openai_key:
                image_client = ImageGenerationClient(
                    api_key=openai_key,
                    base_url="https://api.openai.com/v1",
                    default_model="dall-e-3"
                )
                logger.info("✅ 使用环境变量OPENAI_API_KEY创建默认图像客户端")
            else:
                logger.error("❌ 未找到OPENAI_API_KEY环境变量")
                raise ValueError("图像生成需要OPENAI_API_KEY环境变量")
        
        # 🔧 关键修复：图像生成代理不需要聊天模型客户端
        # 我们的ImageGeneratorAgent有自定义的on_messages方法，不应该调用聊天模型
        # 为了满足AssistantAgent的要求，我们仍然需要传递一个model_client，
        # 但确保我们的自定义逻辑完全绕过它
        model_client_image_generator = get_model_client(
            magentic_ui_config.model_client_configs.orchestrator
        )
        
        image_generator_agent = ImageGeneratorAgent(
            name="image_generator",
            model_client=model_client_image_generator,
            image_client=image_client,
        )
        logger.info(f"🎯 图像生成代理创建成功")
        
    except Exception as e:
        # 如果图像生成客户端创建失败，记录错误但继续运行
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ 无法创建图像生成代理: {e}")
        logger.error(f"🔍 错误详情: {type(e).__name__}: {str(e)}")
        logger.warning("🔄 AI绘图功能将不可用，但不影响其他功能")
        image_generator_agent = None

    if (
        orchestrator_config.memory_controller_key is not None
        and orchestrator_config.retrieve_relevant_plans in ["reuse", "hint"]
    ):
        memory_provider = MemoryControllerProvider(
            internal_workspace_root=paths.internal_root_dir,
            external_workspace_root=paths.external_root_dir,
            inside_docker=magentic_ui_config.inside_docker,
        )
    else:
        memory_provider = None

    team_participants: List[ChatAgent] = [
        web_surfer,
        user_proxy,
    ]
    if not magentic_ui_config.run_without_docker:
        assert coder_agent is not None
        assert file_surfer is not None
        team_participants.extend([coder_agent, file_surfer])
    team_participants.extend(mcp_agents)
    
    # 添加图像生成代理 (如果可用)
    if image_generator_agent is not None:
        team_participants.append(image_generator_agent)

    team = GroupChat(
        participants=team_participants,
        orchestrator_config=orchestrator_config,
        model_client=model_client_orch,
        memory_provider=memory_provider,
    )

    await team.lazy_init()
    return team
