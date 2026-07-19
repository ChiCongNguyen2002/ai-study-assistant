"""Schema models for questions endpoints."""
from pydantic import BaseModel, Field
from typing import Optional, List


class QuestionRequest(BaseModel):
    """Request model for asking a question."""

    query: str = Field(..., min_length=1, description="The question to ask")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is a futures contract?"
            }
        }


class QuestionResponse(BaseModel):
    """Response model for question answers."""

    answer: Optional[str] = Field(None, description="The answer from Claude")
    sources: List[dict] = Field(default_factory=list, description="Source documents")
    model: str = Field(default="claude-opus-4-8", description="Model used")
    error: Optional[str] = Field(None, description="Error message if any")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "A futures contract is...",
                "sources": [],
                "model": "claude-opus-4-8",
                "error": None
            }
        }
