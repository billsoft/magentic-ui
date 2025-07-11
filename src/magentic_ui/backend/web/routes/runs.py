# /api/runs routes
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...datamodel import Message, Run, RunStatus, Session
from ..deps import get_db, get_websocket_manager

router = APIRouter()


class CreateRunRequest(BaseModel):
    session_id: int
    user_id: str


@router.post("/")
async def create_run(
    request: CreateRunRequest,
    db=Depends(get_db),
) -> Dict[str, Any]:
    """Return the existing run for a session or create a new one"""
    # First check if session exists and belongs to user
    session_response = db.get(
        Session,
        filters={"id": request.session_id, "user_id": request.user_id},
        return_json=False,
    )
    if not session_response.status or not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the latest run for this session
    run_response = db.get(
        Run,
        filters={"session_id": request.session_id},
        return_json=False,
    )

    if not run_response.status or not run_response.data:
        # Create a new run if one doesn't exist
        try:
            run_response = db.upsert(
                Run(
                    session_id=request.session_id,
                    status=RunStatus.CREATED,
                    user_id=request.user_id,
                    task=None,
                    team_result=None,
                ),
                return_json=False,
            )
            if not run_response.status:
                raise HTTPException(status_code=400, detail=run_response.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    # Return the run (either existing or newly created)
    run = None
    if isinstance(run_response.data, list) and run_response.data:
        # get the run with the latest created_at
        run = max(run_response.data, key=lambda x: x.created_at)
    else:
        run = run_response.data
    return {"status": run_response.status, "data": {"run_id": str(run.id)}}


# We might want to add these endpoints:


@router.get("/{run_id}")
async def get_run(run_id: int, db=Depends(get_db)) -> Dict[str, Any]:
    """Get run details including task and result"""
    run = db.get(Run, filters={"id": run_id}, return_json=False)
    if not run.status or not run.data:
        raise HTTPException(status_code=404, detail="Run not found")

    return {"status": True, "data": run.data[0]}


@router.get("/{run_id}/messages")
async def get_run_messages(run_id: int, db=Depends(get_db)) -> Dict[str, Any]:
    """Get all messages for a run"""
    messages = db.get(
        Message, filters={"run_id": run_id}, order="created_at asc", return_json=False
    )

    return {"status": True, "data": messages.data}


@router.get("/{run_id}/health")
async def check_run_health(
    run_id: int, 
    db=Depends(get_db),
    ws_manager=Depends(get_websocket_manager)
) -> Dict[str, Any]:
    """Check if a run is still active in the background and available for reconnection"""
    # Get run from database
    run_response = db.get(Run, filters={"id": run_id}, return_json=False)
    if not run_response.status or not run_response.data:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = run_response.data[0]
    
    # Check if run is in a reconnectable state
    is_reconnectable = run.status in [RunStatus.ACTIVE, RunStatus.AWAITING_INPUT, RunStatus.PAUSED]
    
    # Check if there's an active team manager for this run
    has_active_manager = False
    if hasattr(ws_manager, '_team_managers') and run_id in ws_manager._team_managers:
        has_active_manager = True
    
    # Check WebSocket connection status
    has_websocket_connection = (
        hasattr(ws_manager, '_connections') and run_id in ws_manager._connections and
        hasattr(ws_manager, '_closed_connections') and run_id not in ws_manager._closed_connections
    )
    
    return {
        "status": True,
        "data": {
            "run_id": run_id,
            "run_status": run.status,
            "is_reconnectable": is_reconnectable,
            "has_active_manager": has_active_manager,
            "has_websocket_connection": has_websocket_connection,
            "background_task_active": is_reconnectable and has_active_manager,
            "can_reconnect": is_reconnectable and has_active_manager and not has_websocket_connection,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        }
    }


@router.post("/{run_id}/stop")
async def stop_run(
    run_id: int,
    db=Depends(get_db),
    ws_manager=Depends(get_websocket_manager)
) -> Dict[str, Any]:
    """Stop a background run"""
    # Verify run exists
    run_response = db.get(Run, filters={"id": run_id}, return_json=False)
    if not run_response.status or not run_response.data:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = run_response.data[0]
    
    # Stop the run through WebSocket manager
    if hasattr(ws_manager, '_cancellation_tokens') and run_id in ws_manager._cancellation_tokens:
        cancellation_token = ws_manager._cancellation_tokens[run_id]
        cancellation_token.cancel()
        
        # Update run status in database
        run.status = RunStatus.STOPPED
        db.upsert(run)
        
        return {"status": True, "message": f"Run {run_id} stopped successfully"}
    else:
        # Update status in database even if no active manager
        if run.status in [RunStatus.ACTIVE, RunStatus.AWAITING_INPUT, RunStatus.PAUSED]:
            run.status = RunStatus.STOPPED
            db.upsert(run)
        
        return {"status": True, "message": f"Run {run_id} was not actively running, status updated to stopped"}


@router.get("/")
async def list_active_runs(
    user_id: str,
    db=Depends(get_db),
    ws_manager=Depends(get_websocket_manager)
) -> Dict[str, Any]:
    """List all active background runs for a user"""
    # Get all runs for user, then filter by status
    run_response = db.get(
        Run, 
        filters={"user_id": user_id}, 
        return_json=False
    )
    
    # Filter active runs manually since status__in is not supported
    active_runs = []
    if run_response.status and run_response.data:
        active_runs = [
            run for run in run_response.data 
            if run.status in [RunStatus.ACTIVE, RunStatus.AWAITING_INPUT, RunStatus.PAUSED]
        ]
    
    if not run_response.status:
        raise HTTPException(status_code=500, detail="Failed to query runs")
    
    # Enhance with real-time status
    enhanced_runs = []
    for run in active_runs:
        has_active_manager = hasattr(ws_manager, '_team_managers') and run.id in ws_manager._team_managers
        has_websocket_connection = (
            hasattr(ws_manager, '_connections') and run.id in ws_manager._connections and
            hasattr(ws_manager, '_closed_connections') and run.id not in ws_manager._closed_connections
        )
        
        enhanced_runs.append({
            "id": run.id,
            "session_id": run.session_id,
            "status": run.status,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
            "task": run.task,
            "has_active_manager": has_active_manager,
            "has_websocket_connection": has_websocket_connection,
            "background_task_active": has_active_manager,
            "can_reconnect": has_active_manager and not has_websocket_connection,
        })
    
    return {
        "status": True,
        "data": {
            "active_runs": enhanced_runs,
            "total_count": len(enhanced_runs)
        }
    }
