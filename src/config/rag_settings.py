"""RAG system configuration."""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class RAGSettings(BaseSettings):
    """RAG configuration."""

    # Embedding
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536

    # Vector DB
    VECTOR_DB_TYPE: str = "chroma"  # chroma, weaviate, pinecone
    CHROMA_PATH: str = "./data/chroma"

    # Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Retrieval
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.3

    # Data sources
    PDF_PATH: str = "./documents"
    CONFLUENCE_URL: Optional[str] = os.getenv("CONFLUENCE_URL")
    CONFLUENCE_USERNAME: Optional[str] = os.getenv("CONFLUENCE_USERNAME")
    CONFLUENCE_API_TOKEN: Optional[str] = os.getenv("CONFLUENCE_API_TOKEN")

    # Update schedule
    UPDATE_SCHEDULE: str = "0 5 * * *"  # 5 AM daily

    # Claude
    CLAUDE_MODEL: str = "claude-opus-4-8"
    CLAUDE_MAX_TOKENS: int = 2048
    CLAUDE_TEMPERATURE: float = 0.3

    # Security
    ENABLE_PII_DETECTION: bool = True
    ENABLE_FINANCIAL_MASKING: bool = True
    ENABLE_AUDIT_LOG: bool = True

    class Config:
        env_file = ".env.local"
        extra = "ignore"


rag_settings = RAGSettings()
