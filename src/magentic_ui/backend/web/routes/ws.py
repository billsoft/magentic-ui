# api/ws.py
import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from ...datamodel import Run
from ..deps import get_db, get_websocket_manager
from ..managers import WebSocketManager
from ...utils.utils import construct_task

router = APIRouter()


@router.websocket("/runs/{run_id}")
async def run_websocket(
    websocket: WebSocket,
    run_id: int,
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    db=Depends(get_db),
):
    """WebSocket endpoint for run communication with reconnection support"""
    # Verify run exists and is in valid state
    run_response = db.get(Run, filters={"id": run_id}, return_json=False)
    if not run_response.status or not run_response.data:
        logger.warning(f"Run not found: {run_id}")
        await websocket.close(code=4004, reason="Run not found")
        return

    run = run_response.data[0]
    
    # Check if this is a reconnection to an existing background task
    if run.status in ["active", "awaiting_input", "paused"] and hasattr(ws_manager, '_team_managers') and run_id in ws_manager._team_managers:
        logger.info(f"Attempting to reconnect to background task {run_id}")
        reconnected = await ws_manager.reconnect(websocket, run_id)
        if not reconnected:
            await websocket.close(code=4003, reason="Failed to reconnect to background task")
            return
    else:
        # New connection
        connected = await ws_manager.connect(websocket, run_id)
        if not connected:
            await websocket.close(code=4002, reason="Failed to establish connection")
            return

    try:
        logger.info(f"WebSocket connection established for run {run_id}")

        while True:
            try:
                raw_message = await websocket.receive_text()
                message = json.loads(raw_message)

                if message.get("type") == "start":
                    # Handle start message
                    logger.info(f"Received start request for run {run_id}")
                    task = construct_task(
                        query=message.get("task"), files=message.get("files")
                    )
                    team_config = message.get("team_config")
                    settings_config = message.get("settings_config")
                    if task and team_config:
                        # await ws_manager.start_stream(run_id, task, team_config)
                        asyncio.create_task(
                            ws_manager.start_stream(
                                run_id, task, team_config, settings_config
                            )
                        )
                    else:
                        logger.warning(f"Invalid start message format for run {run_id}")
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error": "Invalid start message format",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )

                elif message.get("type") == "stop":
                    logger.info(f"Received stop request for run {run_id}")
                    reason = message.get("reason") or "User requested stop/cancellation"
                    await ws_manager.stop_run(run_id, reason=reason)
                    break

                elif message.get("type") == "input_response":
                    logger.info(f"Received input response for run {run_id}")
                    response = message.get("response", "")
                    await ws_manager.handle_input_response(run_id, response)

                elif message.get("type") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
                    )

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for run {run_id}")
                await ws_manager.disconnect(run_id)
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message handling for run {run_id}: {e}")
                await websocket.send_json(
                    {
                        "type": "error", 
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

    except Exception as e:
        logger.error(f"WebSocket error for run {run_id}: {e}")
        await ws_manager.disconnect(run_id)
