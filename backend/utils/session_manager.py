import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

from fastapi import WebSocket, Depends
from pydantic import BaseModel

from agent.research_agent import ResearchAgent
from config import settings

logger = logging.getLogger(__name__)


class Session:
    """Class representing a research session"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.status = "idle"
        self.current_query: Optional[str] = None
        self.messages = []
        self.research_steps = []
        self.connected_websockets = set()
        self.agent = None
        self.lock = asyncio.Lock()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "status": self.status,
            "current_query": self.current_query,
            "messages": self.messages,
            "research_steps": self.research_steps,
            "query_count": len([m for m in self.messages if m["role"] == "user"]),
        }

    def update_last_active(self):
        """Update the last active timestamp"""
        self.last_active = datetime.now()

    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast a message to all connected WebSockets"""
        if not self.connected_websockets:
            return

        dead_websockets = set()

        for websocket in self.connected_websockets:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {str(e)}")
                dead_websockets.add(websocket)

        # Remove dead WebSockets
        self.connected_websockets -= dead_websockets


class SessionManager:
    """Manager for research sessions"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.cleanup_task = None

    async def start_cleanup_task(self):
        """Start the session cleanup task"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_sessions())

    async def _cleanup_sessions(self):
        """Periodically clean up inactive sessions"""
        try:
            while True:
                # Sleep first to avoid immediate cleanup
                await asyncio.sleep(300)  # Check every 5 minutes

                now = datetime.now()
                timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)

                sessions_to_remove = []

                for session_id, session in self.sessions.items():
                    if now - session.last_active > timeout:
                        sessions_to_remove.append(session_id)

                for session_id in sessions_to_remove:
                    logger.info(f"Cleaning up inactive session {session_id}")
                    await self.delete_session(session_id)

        except asyncio.CancelledError:
            logger.info("Session cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in session cleanup task: {str(e)}")

    async def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new research session"""
        if session_id is None:
            session_id = str(uuid.uuid4())

        if session_id in self.sessions:
            raise ValueError(f"Session {session_id} already exists")

        self.sessions[session_id] = Session(session_id)

        # Start cleanup task if not running
        await self.start_cleanup_task()

        logger.info(f"Created new session {session_id}")
        return session_id

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        return session_id in self.sessions

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        session.update_last_active()
        return session.to_dict()

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        return [session.to_dict() for session in self.sessions.values()]

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session = self.sessions.pop(session_id, None)
        if not session:
            return False

        # Close all WebSocket connections
        for websocket in session.connected_websockets:
            try:
                await websocket.close()
            except Exception:
                pass

        return True

    async def register_websocket(self, session_id: str, websocket: WebSocket):
        """Register a WebSocket with a session"""
        if session_id not in self.sessions:
            await self.create_session(session_id)

        session = self.sessions[session_id]
        session.connected_websockets.add(websocket)
        session.update_last_active()

        # Send current session state to the client
        await websocket.send_json({
            "event": "session_state",
            "data": session.to_dict()
        })

    async def unregister_websocket(self, session_id: str, websocket: Optional[WebSocket] = None):
        """Unregister a WebSocket from a session"""
        session = self.sessions.get(session_id)
        if not session:
            return

        if websocket:
            session.connected_websockets.discard(websocket)
        else:
            # Unregister all WebSockets
            for ws in list(session.connected_websockets):
                session.connected_websockets.discard(ws)

    async def handle_websocket_message(self, session_id: str, data: Dict[str, Any]):
        """Handle a message from a WebSocket"""
        session = self.sessions.get(session_id)
        if not session:
            return

        session.update_last_active()

        if data.get("type") == "query":
            query = data.get("query")
            if query:
                await self.process_query(session_id, query)

    async def stream_callback(self, session_id: str, token: str, info: Dict[str, Any]):
        """Callback for streaming agent output"""
        session = self.sessions.get(session_id)
        if not session:
            return

        if info.get("event"):
            # Event information
            await session.broadcast({
                "event": info["event"],
                "data": info
            })
        elif token:
            # Token from streaming
            await session.broadcast({
                "event": "token",
                "data": {"token": token}
            })

    async def process_query(self, session_id: str, query: str):
        """Process a query in a session"""
        session = self.sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return

        async with session.lock:
            try:
                session.status = "processing"
                session.current_query = query
                session.update_last_active()

                # Add user message to history
                timestamp = datetime.now().isoformat()
                session.messages.append({
                    "role": "user",
                    "content": query,
                    "timestamp": timestamp
                })

                # Initialize agent if not already done
                if session.agent is None:
                    session.agent = ResearchAgent(
                        session_id=session_id,
                        streaming_callback=lambda token, info: asyncio.create_task(
                            self.stream_callback(session_id, token, info)
                        )
                    )

                # Process query with agent
                result = await session.agent.process_query(query)

                # Add assistant message to history
                timestamp = datetime.now().isoformat()
                session.messages.append({
                    "role": "assistant",
                    "content": result["result"],
                    "timestamp": timestamp
                })

                session.status = "idle"
                session.current_query = None

                # Broadcast completion
                await session.broadcast({
                    "event": "query_complete",
                    "data": {
                        "query": query,
                        "result": result,
                        "session_id": session_id
                    }
                })

            except Exception as e:
                logger.error(f"Error processing query in session {session_id}: {str(e)}")
                session.status = "error"

                await session.broadcast({
                    "event": "query_error",
                    "data": {
                        "query": query,
                        "error": str(e),
                        "session_id": session_id
                    }
                })

    async def close_all_sessions(self):
        """Close all sessions"""
        if self.cleanup_task:
            self.cleanup_task.cancel()

        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.delete_session(session_id)


# FastAPI dependency
async def get_session_manager():
    """Dependency to get the session manager instance"""
    manager = SessionManager()
    try:
        yield manager
    finally:
        await manager.close_all_sessions()
