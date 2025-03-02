import os
import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel

from api.routes import router as api_router
from config import settings
from utils.session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize session manager
session_manager = SessionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load any resources or initialize services
    logger.info("Starting up the Deep Research Agent backend...")
    yield
    # Shutdown: clean up resources
    logger.info("Shutting down the Deep Research Agent backend...")
    await session_manager.close_all_sessions()


app = FastAPI(
    title="Custom Deep Research Agent API",
    description="API for a custom deep research agent using Groq, Ollama, and Perplexica",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Deep Research Agent is running",
        "version": "1.0.0",
    }


# WebSocket for real-time communication with frontend
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connection opened for session {session_id}")

    try:
        # Register this websocket with the session
        await session_manager.register_websocket(session_id, websocket)

        # Keep the connection open and listen for messages
        while True:
            data = await websocket.receive_json()
            await session_manager.handle_websocket_message(session_id, data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        await session_manager.unregister_websocket(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        await session_manager.unregister_websocket(session_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
