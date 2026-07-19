"""FastAPI application factory for RAG chatbot."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.chat.routes import router as chat_router
from src.config.settings import settings


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="AI Study Assistant - RAG Chatbot",
        version="2.0.0",
        description="AI-powered study assistant with RAG (Retrieval Augmented Generation)"
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(chat_router)

    # Health check
    @app.get("/health", tags=["health"])
    async def health():
        """Health check endpoint."""
        return {
            "status": "ok",
            "service": "ai-study-assistant",
            "version": "2.0.0",
            "mode": "RAG_CHATBOT"
        }

    # Root endpoint
    @app.get("/", tags=["info"])
    async def root():
        """Root endpoint."""
        return {
            "message": "AI Study Assistant - RAG Chatbot API",
            "version": "2.0.0",
            "docs": "/docs",
            "status": "running"
        }

    return app


# Create app instance
app = create_app()
