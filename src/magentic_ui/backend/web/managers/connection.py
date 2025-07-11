import asyncio
import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence, Union
import json

from autogen_agentchat.base._task import TaskResult
from autogen_agentchat.messages import (
    AgentEvent,
    BaseTextChatMessage,
    ChatMessage,
    HandoffMessage,
    ModelClientStreamingChunkEvent,
    MultiModalMessage,
    StopMessage,
    TextMessage,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
)
from ....input_func import InputFuncType, InputRequestType
from autogen_core import CancellationToken
from fastapi import WebSocket, WebSocketDisconnect
from pathlib import Path
from ....types import CheckpointEvent
from ...database import DatabaseManager
from ...datamodel import (
    LLMCallEventMessage,
    Message,
    MessageConfig,
    Run,
    RunStatus,
    Settings,
    SettingsConfig,
    TeamResult,
)
from ...teammanager import TeamManager
from ...utils.utils import compress_state

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and message streaming for team task execution

    Args:
        db_manager (DatabaseManager): Database manager instance for database operations
        internal_workspace_root (Path): Path to the internal root directory
        external_workspace_root (Path): Path to the external root directory
        inside_docker (bool): Flag indicating if the application is running inside Docker
        run_without_docker (bool): Flag indicating if the application is running without docker
        config (dict): Configuration for Magentic-UI
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        internal_workspace_root: Path,
        external_workspace_root: Path,
        inside_docker: bool,
        config: Dict[str, Any],
        run_without_docker: bool,
    ):
        self.db_manager = db_manager
        self.internal_workspace_root = internal_workspace_root
        self.external_workspace_root = external_workspace_root
        self.inside_docker = inside_docker
        self.config = config
        self.run_without_docker = run_without_docker
        self._connections: Dict[int, WebSocket] = {}
        self._cancellation_tokens: Dict[int, CancellationToken] = {}
        # Track explicitly closed connections
        self._closed_connections: set[int] = set()
        self._input_responses: Dict[int, asyncio.Queue[str]] = {}
        self._team_managers: Dict[int, TeamManager] = {}
        self._cancel_message = TeamResult(
            task_result=TaskResult(
                messages=[TextMessage(source="user", content="Run cancelled by user")],
                stop_reason="cancelled by user",
            ),
            usage="",
            duration=0,
        ).model_dump()

    def _get_stop_message(self, reason: str) -> dict[str, Any]:
        return TeamResult(
            task_result=TaskResult(
                messages=[TextMessage(source="user", content=reason)],
                stop_reason=reason,
            ),
            usage="",
            duration=0,
        ).model_dump()

    async def connect(self, websocket: WebSocket, run_id: int) -> bool:
        try:
            await websocket.accept()
            self._connections[run_id] = websocket
            self._closed_connections.discard(run_id)
            # Initialize input queue for this connection
            self._input_responses[run_id] = asyncio.Queue()

            await self._send_message(
                run_id,
                {
                    "type": "system",
                    "status": "connected",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            return True
        except Exception as e:
            logger.error(f"Connection error for run {run_id}: {e}")
            return False

    async def start_stream(
        self,
        run_id: int,
        task: str | ChatMessage | Sequence[ChatMessage] | None,
        team_config: Dict[str, Any],
        settings_config: Dict[str, Any],
        user_settings: Settings | None = None,
    ) -> None:
        """
        Start streaming task execution with proper run management

        Args:
            run_id (int): ID of the run
            task (str | ChatMessage | Sequence[ChatMessage] | None): Task to execute
            team_config (Dict[str, Any]): Configuration for the team
            settings_config (Dict[str, Any]): Configuration for settings
            user_settings (Settings, optional): User settings for the run
        """
        if run_id not in self._connections or run_id in self._closed_connections:
            raise ValueError(f"No active connection for run {run_id}")

        # do not create a new team manager if one already exists
        if run_id not in self._team_managers:
            team_manager = TeamManager(
                internal_workspace_root=self.internal_workspace_root,
                external_workspace_root=self.external_workspace_root,
                inside_docker=self.inside_docker,
                config=self.config,
                run_without_docker=self.run_without_docker,
            )
            self._team_managers[run_id] = team_manager

        else:
            team_manager = self._team_managers[run_id]
        cancellation_token = CancellationToken()
        self._cancellation_tokens[run_id] = cancellation_token
        final_result = None

        try:
            # Update run with task and status
            run = await self._get_run(run_id)
            assert run is not None, f"Run {run_id} not found in database"
            assert run.user_id is not None, f"Run {run_id} has no user ID"

            # Get user Settings
            user_settings = await self._get_settings(run.user_id)
            env_vars = (
                SettingsConfig(**user_settings.config).environment  # type: ignore
                if user_settings
                else None
            )

            settings_config["memory_controller_key"] = run.user_id

            state = None
            if run:
                run.task = MessageConfig(content=task, source="user").model_dump()
                run.status = RunStatus.ACTIVE
                state = run.state
                self.db_manager.upsert(run)
                await self._update_run_status(run_id, RunStatus.ACTIVE)

            # add task as message
            if isinstance(task, str):
                await self._send_message(
                    run_id,
                    self._format_message(TextMessage(source="user_proxy", content=task))
                    or {},
                )
                await self._save_message(
                    run_id, TextMessage(source="user_proxy", content=task)
                )

            elif isinstance(task, Sequence):
                for task_message in task:
                    if isinstance(task_message, TextMessage) or isinstance(
                        task_message, MultiModalMessage
                    ):
                        if (
                            hasattr(task_message, "metadata")
                            and task_message.metadata.get("internal") == "yes"
                        ):
                            continue

                        await self._send_message(
                            run_id, self._format_message(task_message) or {}
                        )
                        await self._save_message(run_id, task_message)

            input_func: InputFuncType = self.create_input_func(run_id)

            message: ChatMessage | AgentEvent | TeamResult | LLMCallEventMessage
            async for message in team_manager.run_stream(
                task=task,
                team_config=team_config,
                state=state,
                input_func=input_func,
                cancellation_token=cancellation_token,
                env_vars=env_vars,
                settings_config=settings_config,
                run=run,
            ):
                # Only stop if explicitly cancelled, NOT just because connection closed
                if cancellation_token.is_cancelled():
                    logger.info(f"Stream cancelled for run {run_id}")
                    break
                    
                # For closed connections, just skip message sending but keep processing
                if run_id in self._closed_connections:
                    # Task continues in background, just don't send messages to client
                    logger.debug(f"Processing message in background for run {run_id}")

                if isinstance(message, CheckpointEvent):
                    # Save state to run
                    run = await self._get_run(run_id)
                    if run:
                        # Use compress_state utility to compress the state
                        state_dict = json.loads(message.state)
                        run.state = compress_state(state_dict)
                        self.db_manager.upsert(run)
                    continue

                # do not show internal messages
                if (
                    hasattr(message, "metadata")
                    and message.metadata.get("internal") == "yes"  # type: ignore
                ):
                    continue

                formatted_message = self._format_message(message)
                if formatted_message:
                    # Only send message if connection is active, otherwise just process silently
                    if run_id not in self._closed_connections:
                        await self._send_message(run_id, formatted_message)
                    else:
                        # Background processing - save but don't send
                        logger.debug(f"Background processing message for run {run_id}: {message.__class__.__name__}")

                    # Save messages by concrete type
                    if isinstance(
                        message,
                        (
                            TextMessage,
                            MultiModalMessage,
                            StopMessage,
                            HandoffMessage,
                            ToolCallRequestEvent,
                            ToolCallExecutionEvent,
                            LLMCallEventMessage,
                        ),
                    ):
                        await self._save_message(run_id, message)
                    # Capture final result if it's a TeamResult
                    elif isinstance(message, TeamResult):
                        final_result = message.model_dump()
                    self._team_managers[run_id] = team_manager  # Track the team manager
            if (
                not cancellation_token.is_cancelled()
                and run_id not in self._closed_connections
            ):
                if final_result:
                    await self._update_run(
                        run_id, RunStatus.COMPLETE, team_result=final_result
                    )
                else:
                    logger.warning(
                        f"No final result captured for completed run {run_id}"
                    )
                    await self._update_run_status(run_id, RunStatus.COMPLETE)
            else:
                await self._send_message(
                    run_id,
                    {
                        "type": "completion",
                        "status": "cancelled",
                        "data": self._cancel_message,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                # Update run with cancellation result
                await self._update_run(
                    run_id, RunStatus.STOPPED, team_result=self._cancel_message
                )

        except Exception as e:
            logger.error(f"Stream error for run {run_id}: {e}")
            traceback.print_exc()
            
            # 🔧 增强网络错误处理 - 区分网络错误和其他错误
            import openai
            import httpx
            
            error_message = str(e)
            is_network_error = (
                isinstance(e, (openai.APIConnectionError, httpx.ConnectError)) or
                "Connection error" in error_message or
                "All connection attempts failed" in error_message or
                "ConnectTimeout" in error_message or
                "ReadTimeout" in error_message
            )
            
            # 🔧 修复：减少过度的网络错误容忍，恢复直接错误处理
            if is_network_error:
                # 网络错误：发送明确的错误信息，不再默认保持任务活跃
                logger.error(f"Network error for run {run_id}: {e}")
                
                await self._send_message(
                    run_id,
                    {
                        "type": "error",
                        "status": "network_error",
                        "error": f"网络连接错误：{str(e)}",
                        "data": {"error": str(e), "error_type": "network_error"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                
                # 标记为错误状态，让用户知道出了问题
                await self._handle_stream_error(run_id, e)
                
            else:
                # 其他错误：按原有逻辑处理
                await self._handle_stream_error(run_id, e)
        finally:
            self._cancellation_tokens.pop(run_id, None)
            # Only remove team manager if task was actually completed or cancelled
            # Keep team manager for background processing if connection closed but task not done
            should_remove_team_manager = (
                cancellation_token.is_cancelled() or  # Explicitly cancelled
                final_result is not None  # Task completed successfully
            )
            
            if should_remove_team_manager:
                self._team_managers.pop(run_id, None)
                logger.info(f"Team manager removed for run {run_id} (task completed or cancelled)")
            else:
                logger.info(f"Team manager preserved for run {run_id} (background processing or connection closed)")

    async def _save_message(
        self, run_id: int, message: Union[AgentEvent | ChatMessage, LLMCallEventMessage]
    ) -> None:
        """
        Save a message to the database

        Args:
            run_id (int): ID of the run
            message (Union[AgentEvent | ChatMessage, LLMCallEventMessage]): Message to save
        """

        run = await self._get_run(run_id)
        if run:
            db_message = Message(
                created_at=datetime.now(),
                session_id=run.session_id,
                run_id=run_id,
                config=message.model_dump(),
                user_id=run.user_id,  # Pass the user_id from the run object
            )
            self.db_manager.upsert(db_message)

    async def _update_run(
        self,
        run_id: int,
        status: RunStatus,
        team_result: Optional[TeamResult | Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Update run status and result

        Args:
            run_id (int): ID of the run
            status (RunStatus): New status to set
            team_result (TeamResult | dict[str, Any], optional): Optional team result to set
            error (str, optional): Optional error message
        """
        run = await self._get_run(run_id)
        if run:
            run.status = status
            if team_result:
                run.team_result = team_result
            if error:
                run.error_message = error
            self.db_manager.upsert(run)

    def create_input_func(self, run_id: int, timeout: int = 3600) -> InputFuncType:
        """
        Creates an input function for a specific run

        Args:
            run_id (int): ID of the run
            timeout (int, optional): Timeout for input response in seconds. Default: 3600 (1 hour)
        Returns:
            InputFuncType: Input function for the run
        """

        async def input_handler(
            prompt: str = "",
            cancellation_token: Optional[CancellationToken] = None,
            input_type: InputRequestType = "text_input",
        ) -> str:
            try:
                # resume run if it is paused
                await self.resume_run(run_id)

                # update run status to awaiting_input
                await self._update_run_status(run_id, RunStatus.AWAITING_INPUT)
                
                # Store input_request in the Run object for persistence
                run = await self._get_run(run_id)
                if run:
                    run.input_request = {"prompt": prompt, "input_type": input_type}
                    self.db_manager.upsert(run)
                
                # Send input request to client only if connection exists
                if run_id in self._connections and run_id not in self._closed_connections:
                    logger.info(
                        f"Sending input request for run {run_id}: ({input_type}) {prompt}"
                    )
                    await self._send_message(
                        run_id,
                        {
                            "type": "input_request",
                            "input_type": input_type,
                            "prompt": prompt,
                            "data": {"source": "system", "content": prompt},
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                else:
                    # Connection lost - save state and provide default response for autonomous tasks
                    logger.warning(f"No WebSocket connection for run {run_id}, providing default response")
                    if "continue" in prompt.lower() or "proceed" in prompt.lower():
                        await self._update_run_status(run_id, RunStatus.ACTIVE)
                        return "continue"
                    else:
                        # For other inputs, try to provide a reasonable default
                        await self._update_run_status(run_id, RunStatus.ACTIVE)
                        return "yes"  # Default approval for most actions

                # Wait for response with timeout
                if run_id in self._input_responses:
                    try:

                        async def poll_for_response():
                            while True:
                                # Check if run was closed/cancelled
                                if run_id in self._closed_connections:
                                    logger.warning(f"Run {run_id} was closed during input wait")
                                    # Don't raise error, try to continue with default response
                                    return "continue"

                                # Try to get response with short timeout
                                try:
                                    response = await asyncio.wait_for(
                                        self._input_responses[run_id].get(),
                                        timeout=min(timeout, 30),  # Check every 30 seconds
                                    )
                                    await self._update_run_status(
                                        run_id, RunStatus.ACTIVE
                                    )
                                    return response
                                except asyncio.TimeoutError:
                                    # Check if we should continue with automatic response
                                    if run_id in self._closed_connections:
                                        logger.info(f"Connection lost for run {run_id}, providing automatic response")
                                        return "continue"
                                    continue  # Keep checking for closed status

                        response = await asyncio.wait_for(
                            poll_for_response(), timeout=timeout
                        )
                        return response

                    except asyncio.TimeoutError:
                        # Enhanced timeout handling - don't immediately stop the run
                        logger.warning(f"Input response timeout for run {run_id}, but keeping run alive")
                        
                        # Update run with timeout info but don't stop it
                        await self._send_message(
                            run_id,
                            {
                                "type": "system",
                                "status": "timeout_warning", 
                                "message": "Input timeout occurred, but task will continue automatically",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )
                        
                        # Provide default response to continue execution
                        await self._update_run_status(run_id, RunStatus.ACTIVE)
                        return "continue"  # Allow task to proceed
                else:
                    logger.warning(f"No input queue for run {run_id}, providing default response")
                    await self._update_run_status(run_id, RunStatus.ACTIVE)
                    return "continue"

            except Exception as e:
                logger.error(f"Error handling input for run {run_id}: {e}")
                # Don't re-raise - provide default response to continue
                try:
                    await self._update_run_status(run_id, RunStatus.ACTIVE)
                except:
                    pass  # Ignore secondary errors
                return "continue"

        return input_handler

    async def handle_input_response(self, run_id: int, response: str) -> None:
        """Handle input response from client"""
        if run_id in self._input_responses:
            await self._input_responses[run_id].put(response)
        else:
            logger.warning(f"Received input response for inactive run {run_id}")

    async def stop_run(self, run_id: int, reason: str) -> None:
        if run_id in self._cancellation_tokens:
            logger.info(f"Stopping run {run_id}")

            stop_message = self._get_stop_message(reason)

            try:
                # Update run record first
                await self._update_run(
                    run_id, status=RunStatus.STOPPED, team_result=stop_message
                )

                # Then handle websocket communication if connection is active
                if (
                    run_id in self._connections
                    and run_id not in self._closed_connections
                ):
                    await self._send_message(
                        run_id,
                        {
                            "type": "completion",
                            "status": "cancelled",
                            "data": stop_message,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                # Finally cancel the token and clean up team manager
                self._cancellation_tokens[run_id].cancel()
                # Remove team manager since task is explicitly stopped
                team_manager = self._team_managers.pop(run_id, None)
                if team_manager:
                    await team_manager.close()
                logger.info(f"Run {run_id} explicitly stopped and team manager cleaned up")
            except Exception as e:
                logger.error(f"Error stopping run {run_id}: {e}")
                # We might want to force disconnect here if db update failed
                # await self.disconnect(run_id)  # Optional

    async def disconnect(self, run_id: int) -> None:
        """
        Clean up connection but allow background task continuation

        Args:
            run_id (int): ID of the run to disconnect
        """
        logger.info(f"Disconnecting WebSocket for run {run_id}, but keeping task alive")

        # Mark as closed to prevent new messages
        self._closed_connections.add(run_id)

        # Save current state to database for later recovery
        run = await self._get_run(run_id)
        if run and run.status in [RunStatus.ACTIVE, RunStatus.AWAITING_INPUT]:
            # Update status to indicate background execution
            run.status = RunStatus.ACTIVE  # Keep active for background processing
            self.db_manager.upsert(run)
            logger.info(f"Run {run_id} will continue in background mode")

        # Clean up WebSocket resources but keep task running
        self._connections.pop(run_id, None)
        self._input_responses.pop(run_id, None)
        
        # DO NOT cancel the cancellation token or stop the team manager
        # This allows the task to continue running in the background
        logger.info(f"WebSocket disconnected for run {run_id}, task continues in background")

    async def _send_message(self, run_id: int, message: Dict[str, Any]) -> None:
        """Send a message through the WebSocket with connection state checking

        Args:
            run_id (int): int of the run
            message (Dict[str, Any]): Message dictionary to send
        """
        if run_id in self._closed_connections:
            logger.warning(
                f"Attempted to send message to closed connection for run {run_id}"
            )
            return

        try:
            if run_id in self._connections:
                websocket = self._connections[run_id]
                await websocket.send_json(message)
        except WebSocketDisconnect:
            logger.warning(
                f"WebSocket disconnected while sending message for run {run_id}"
            )
            await self.disconnect(run_id)
        except Exception as e:
            logger.error(f"Error sending message for run {run_id}: {e}, {message}")
            # Don't try to send error message here to avoid potential recursive loop
            await self._update_run_status(run_id, RunStatus.ERROR, str(e))
            await self.disconnect(run_id)

    async def _handle_stream_error(self, run_id: int, error: Exception) -> None:
        """
        Handle stream errors with proper run updates

        Args:
            run_id (int): ID of the run
            error (Exception): Exception that occurred
        """
        if run_id not in self._closed_connections:
            error_result = TeamResult(
                task_result=TaskResult(
                    messages=[TextMessage(source="system", content=str(error))],
                    stop_reason="An error occurred while processing this run",
                ),
                usage="",
                duration=0,
            ).model_dump()

            await self._send_message(
                run_id,
                {
                    "type": "completion",
                    "status": "error",
                    "data": error_result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            await self._update_run(
                run_id, RunStatus.ERROR, team_result=error_result, error=str(error)
            )

    def _format_message(self, message: Any) -> Optional[Dict[str, Any]]:
        """Format message for WebSocket transmission

        Args:
            message (Any): Message to format

        Returns:
            Optional[Dict[str, Any]]: Formatted message or None if formatting fails
        """

        try:
            if isinstance(message, MultiModalMessage):
                message_dump = message.model_dump()

                message_content: list[dict[str, Any]] = []
                for row in message_dump["content"]:
                    if "data" in row:
                        # 🔧 根据消息类型智能设置alt文本
                        alt_text = "WebSurfer Screenshot"  # 默认值
                        if "metadata" in message_dump and message_dump["metadata"]:
                            msg_type = message_dump["metadata"].get('type', '')
                            logger.debug(f"🖼️ 处理图像消息，类型: {msg_type}")
                            if msg_type == 'image_generation':
                                alt_text = row.get('alt', f"Generated image")
                                logger.info(f"✅ 图像生成消息，alt设置为: {alt_text}")
                            elif msg_type == 'browser_screenshot':
                                alt_text = "WebSurfer Screenshot"
                            elif msg_type == 'file_surfer_response':
                                alt_text = "File content"
                        else:
                            logger.debug(f"🖼️ 图像消息无metadata，使用默认alt: {alt_text}")
                        
                        message_content.append(
                            {
                                "url": f"data:image/png;base64,{row['data']}",
                                "data": row['data'],  # 🔧 保留原始base64数据
                                "alt": alt_text,
                            }
                        )
                    else:
                        message_content.append(row)
                message_dump["content"] = message_content

                return {"type": "message", "data": message_dump}

            elif isinstance(message, TeamResult):
                return {
                    "type": "result",
                    "data": message.model_dump(),
                    "status": "complete",
                }
            elif isinstance(message, ModelClientStreamingChunkEvent):
                return {"type": "message_chunk", "data": message.model_dump()}

            elif isinstance(
                message,
                (
                    BaseTextChatMessage,
                    ToolCallRequestEvent,
                    ToolCallExecutionEvent,
                ),
            ):
                return {"type": "message", "data": message.model_dump()}
            elif isinstance(message, str):
                return {
                    "type": "message",
                    "data": {"source": "user", "content": message},
                }
            else:
                logger.warning(
                    f"Cannot format unrecognized message type: {type(message)}"
                )

            return None

        except Exception as e:
            logger.error(f"Message formatting error: {e}")
            return None

    async def _get_run(self, run_id: int) -> Optional[Run]:
        """Get run from database

        Args:
            run_id (int): int of the run to retrieve

        Returns:
            Optional[Run]: Run object if found, None otherwise
        """
        response = self.db_manager.get(Run, filters={"id": run_id}, return_json=False)
        return response.data[0] if response.status and response.data else None

    async def _get_settings(self, user_id: str) -> Optional[Settings]:
        """Get user settings from database
        Args:
            user_id (str): User ID to retrieve settings for
        Returns:
            Optional[Settings]: User settings if found, None otherwise
        """
        response = self.db_manager.get(
            filters={"user_id": user_id}, model_class=Settings, return_json=False
        )
        return response.data[0] if response.status and response.data else None

    async def _update_run_status(
        self, run_id: int, status: RunStatus, error: Optional[str] = None
    ) -> None:
        """Update run status in database

        Args:
            run_id (int): int of the run to update
            status (RunStatus): New status to set
            error (str, optional): Optional error message
        """
        run = await self._get_run(run_id)
        if run:
            run.status = status
            run.error_message = error
            self.db_manager.upsert(run)
        # send system message to client with status
        await self._send_message(
            run_id,
            {
                "type": "system",
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def cleanup(self) -> None:
        """Clean up all active connections and resources when server is shutting down"""
        logger.info(f"Cleaning up {len(self.active_connections)} active connections")

        try:
            # First cancel all running tasks
            for run_id in self.active_connections.copy():
                if run_id in self._cancellation_tokens:
                    self._cancellation_tokens[run_id].cancel()
                run = await self._get_run(run_id)
                if run and run.status == RunStatus.ACTIVE:
                    interrupted_result = TeamResult(
                        task_result=TaskResult(
                            messages=[
                                TextMessage(
                                    source="system",
                                    content="Run interrupted by server shutdown",
                                )
                            ],
                            stop_reason="server_shutdown",
                        ),
                        usage="",
                        duration=0,
                    ).model_dump()

                    run.status = RunStatus.STOPPED
                    run.team_result = interrupted_result
                    self.db_manager.upsert(run)

            # Then disconnect all websockets with timeout
            # 10 second timeout for entire cleanup
            async def disconnect_all():
                for run_id in self.active_connections.copy():
                    try:
                        await asyncio.wait_for(self.disconnect(run_id), timeout=2)
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout disconnecting run {run_id}")
                    except Exception as e:
                        logger.error(f"Error disconnecting run {run_id}: {e}")

            await asyncio.wait_for(disconnect_all(), timeout=10)

        except asyncio.TimeoutError:
            logger.warning("WebSocketManager cleanup timed out")
        except Exception as e:
            logger.error(f"Error during WebSocketManager cleanup: {e}")
        finally:
            # Always clear internal state, even if cleanup had errors
            self._connections.clear()
            self._cancellation_tokens.clear()
            self._closed_connections.clear()
            self._input_responses.clear()

    @property
    def active_connections(self) -> set[int]:
        """Get set of active run IDs"""
        return set(self._connections.keys()) - self._closed_connections

    @property
    def active_runs(self) -> set[int]:
        """Get set of runs with active cancellation tokens"""
        return set(self._cancellation_tokens.keys())

    async def pause_run(self, run_id: int) -> None:
        """Pause the run"""
        if (
            run_id in self._connections
            and run_id not in self._closed_connections
            and run_id in self._team_managers
        ):
            team_manager = self._team_managers.get(run_id)
            if team_manager:
                await team_manager.pause_run()
                # await self._send_message(
                #     run_id,
                #     {
                #         "type": "system",
                #         "status": "paused",
                #         "timestamp": datetime.now(timezone.utc).isoformat(),
                #     },
                # )
                # await self._update_run_status(run_id, RunStatus.PAUSED)

    async def resume_run(self, run_id: int) -> None:
        """Resume the run"""
        if (
            run_id in self._connections
            and run_id not in self._closed_connections
            and run_id in self._team_managers
        ):
            team_manager = self._team_managers.get(run_id)
            if team_manager:
                await team_manager.resume_run()
                await self._update_run_status(run_id, RunStatus.ACTIVE)

    async def reconnect(self, websocket: WebSocket, run_id: int) -> bool:
        """
        Reconnect to an existing background run

        Args:
            websocket (WebSocket): New WebSocket connection
            run_id (int): ID of the existing run

        Returns:
            bool: True if reconnection successful
        """
        try:
            # Check if run exists and is still active
            run = await self._get_run(run_id)
            if not run:
                logger.warning(f"Run {run_id} not found for reconnection")
                return False

            if run.status not in [RunStatus.ACTIVE, RunStatus.AWAITING_INPUT, RunStatus.PAUSED]:
                logger.warning(f"Run {run_id} is not in a reconnectable state: {run.status}")
                return False

            # Accept the new connection
            await websocket.accept()
            
            # Remove from closed connections and update connection tracking
            self._closed_connections.discard(run_id)
            self._connections[run_id] = websocket
            self._input_responses[run_id] = asyncio.Queue()

            # Send reconnection confirmation
            await self._send_message(
                run_id,
                {
                    "type": "system",
                    "status": "reconnected",
                    "message": f"Reconnected to background task. Status: {run.status}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            # If run was awaiting input, resend the input request
            if run.input_request:
                await self._send_message(
                    run_id,
                    {
                        "type": "input_request",
                        "input_type": run.input_request.get("input_type", "text_input"),
                        "prompt": run.input_request.get("prompt", ""),
                        "data": {"source": "system", "content": run.input_request.get("prompt", "")},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

            logger.info(f"Successfully reconnected to run {run_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reconnect to run {run_id}: {e}")
            return False
