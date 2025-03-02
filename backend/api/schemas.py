from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


# Base schemas
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class ToolCall(BaseModel):
    tool: str
    input: str
    output: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ResearchStep(BaseModel):
    step_type: str  # "search", "analysis", "summary", etc.
    description: str
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)


# Response schemas
class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    last_active: datetime
    status: str  # "active", "idle", "error", etc.
    query_count: int = 0


class SessionDetails(SessionInfo):
    current_query: Optional[str] = None
    messages: List[ChatMessage] = []
    research_steps: List[ResearchStep] = []


class ErrorResponse(BaseModel):
    error: str
    details: Optional[Dict[str, Any]] = None
