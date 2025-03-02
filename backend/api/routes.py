import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel

from utils.session_manager import SessionManager, get_session_manager
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Request and response models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    session_id: str
    status: str
    message: str


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    last_active: str
    status: str


# API endpoints
@router.post("/query", response_model=QueryResponse)
async def submit_query(
        request: QueryRequest,
        background_tasks: BackgroundTasks,
        session_manager: SessionManager = Depends(get_session_manager)
):
    """Submit a research query to be processed asynchronously"""

    # Create or get a session
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Ensure session exists
        if not await session_manager.session_exists(session_id):
            await session_manager.create_session(session_id)

        # Queue the query for processing
        background_tasks.add_task(
            session_manager.process_query,
            session_id,
            request.query
        )

        return {
            "session_id": session_id,
            "status": "processing",
            "message": "Query accepted and processing started. Connect to WebSocket for real-time updates."
        }

    except Exception as e:
        logger.error(f"Error submitting query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(
        session_manager: SessionManager = Depends(get_session_manager)
):
    """List all active research sessions"""
    try:
        sessions = await session_manager.list_sessions()
        return sessions

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(
        session_id: str,
        session_manager: SessionManager = Depends(get_session_manager)
):
    """Get details for a specific research session"""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(
        session_id: str,
        session_manager: SessionManager = Depends(get_session_manager)
):
    """Delete a specific research session"""
    try:
        success = await session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return {"status": "success", "message": f"Session {session_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")
