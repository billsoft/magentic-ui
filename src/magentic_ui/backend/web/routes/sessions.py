# api/routes/sessions.py
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from ...datamodel import Message, Run, Session, RunStatus
from ..deps import get_db

router = APIRouter()


@router.get("/")
async def list_sessions(user_id: str, db=Depends(get_db)) -> Dict:
    """List all sessions for a user"""
    response = db.get(Session, filters={"user_id": user_id})
    return {"status": True, "data": response.data}


@router.get("/{session_id}")
async def get_session(session_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Get a specific session"""
    response = db.get(Session, filters={"id": session_id, "user_id": user_id})
    if not response.status or not response.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": True, "data": response.data[0]}


@router.post("/")
async def create_session(session: Session, db=Depends(get_db)) -> Dict:
    """Create a new session with an associated run"""
    # Create session
    session_response = db.upsert(session)
    if not session_response.status:
        raise HTTPException(status_code=400, detail=session_response.message)

    # Get the actual session ID from the response (session_response.data is a dict when return_json=True)
    created_session = session_response.data
    if not created_session or 'id' not in created_session:
        raise HTTPException(status_code=500, detail="Failed to get session ID from created session")
    
    session_id = created_session['id']
    if not session_id:
        raise HTTPException(status_code=500, detail="Session ID is None")
    
    # Create associated run
    try:
        run = db.upsert(
            Run(
                session_id=session_id,  # 使用从数据库返回的实际session ID
                status=RunStatus.CREATED,
                user_id=session.user_id,
                task=None,
                team_result=None,
            ),
            return_json=False,
        )
        if not run.status:
            # Clean up session if run creation failed
            raise HTTPException(status_code=400, detail=run.message)
        return {"status": True, "data": session_response.data}
    except Exception as e:
        # Clean up session if run creation failed
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{session_id}")
async def update_session(
    session_id: int, user_id: str, session: Session, db=Depends(get_db)
) -> Dict:
    """Update an existing session"""
    # First verify the session belongs to user
    existing = db.get(Session, filters={"id": session_id, "user_id": user_id})
    if not existing.status or not existing.data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update the session
    response = db.upsert(session)
    if not response.status:
        raise HTTPException(status_code=400, detail=response.message)

    return {
        "status": True,
        "data": response.data,
        "message": "Session updated successfully",
    }


@router.delete("/{session_id}")
async def delete_session(session_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Delete a session and all its associated runs and messages"""
    # Delete the session
    db.delete(filters={"id": session_id, "user_id": user_id}, model_class=Session)

    return {"status": True, "message": "Session deleted successfully"}


@router.get("/{session_id}/runs")
async def list_session_runs(session_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Get complete session history organized by runs"""

    try:
        # 1. Verify session exists and belongs to user
        session = db.get(
            Session, filters={"id": session_id, "user_id": user_id}, return_json=False
        )
        if not session.status:
            raise HTTPException(
                status_code=500, detail="Database error while fetching session"
            )
        if not session.data:
            raise HTTPException(
                status_code=404, detail="Session not found or access denied"
            )

        # 2. Get ordered runs for session
        runs = db.get(
            Run, filters={"session_id": session_id}, order="asc", return_json=False
        )
        if not runs.status:
            raise HTTPException(
                status_code=500, detail="Database error while fetching runs"
            )

        # 3. Build response with messages per run
        run_data = []
        if runs.data:  # It's ok to have no runs
            for run in runs.data:
                try:
                    # Get messages for this specific run
                    messages = db.get(
                        Message,
                        filters={"run_id": run.id},
                        order="asc",
                        return_json=False,
                    )
                    if not messages.status:
                        logger.error(f"Failed to fetch messages for run {run.id}")
                        # Continue processing other runs even if one fails
                        messages.data = []

                    run_data.append(
                        {
                            "id": str(run.id),
                            "created_at": run.created_at,
                            "status": run.status,
                            "task": run.task,
                            "team_result": run.team_result,
                            "messages": messages.data or [],
                            "input_request": getattr(run, "input_request", None),
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing run {run.id}: {str(e)}")
                    # Include run with error state instead of failing entirely
                    run_data.append(
                        {
                            "id": str(run.id),
                            "created_at": run.created_at,
                            "status": "ERROR",
                            "task": run.task,
                            "team_result": None,
                            "messages": [],
                            "error": f"Failed to process run: {str(e)}",
                            "input_request": getattr(run, "input_request", None),
                        }
                    )

        return {"status": True, "data": {"runs": run_data}}

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error in list_messages: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching session data"
        ) from e
