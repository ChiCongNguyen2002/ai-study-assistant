"""Chat message schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    """A single chat message."""
    id: str = Field(default="", description="Message ID")
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)


class SourceCitation(BaseModel):
    """Source citation in response."""
    source: str = Field(..., description="Document source")
    page: int = Field(default=0, description="Page number")
    similarity: float = Field(..., description="Similarity score 0-100")


class ChatRequest(BaseModel):
    """Chat request from user."""
    query: str = Field(..., min_length=1, max_length=1000, description="User question")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    include_history: bool = Field(default=True, description="Include chat history")


class ChatResponse(BaseModel):
    """Response to chat request."""
    session_id: str
    message_id: str
    query: str
    answer: Optional[str] = Field(None, description="AI response")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    sources: List[SourceCitation] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_123",
                "message_id": "msg_456",
                "query": "Hợp đồng tương lai là gì?",
                "answer": "Hợp đồng tương lai (Futures) là một thỏa thuận...",
                "confidence": 0.92,
                "sources": [
                    {
                        "source": "B1. Tổng quan thị trường",
                        "page": 12,
                        "similarity": 95.2
                    }
                ],
                "follow_up_questions": [
                    "Sự khác nhau giữa Futures và Options?",
                    "Risks của trading derivatives?"
                ],
                "error": None,
                "timestamp": "2026-07-19T10:30:00Z"
            }
        }


class ChatSession(BaseModel):
    """Chat session."""
    id: str
    user_id: str
    title: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sess_123",
                "user_id": "user_456",
                "title": "Derivatives Market Questions",
                "messages": [],
                "created_at": "2026-07-19T10:00:00Z",
                "updated_at": "2026-07-19T10:30:00Z",
                "metadata": {}
            }
        }
