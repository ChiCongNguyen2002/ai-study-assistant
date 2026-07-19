"""FastAPI application factory."""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.config.settings import settings
from src.api.routes import questions, search, documents


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered study assistant with PDF/DOCX support"
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
    app.include_router(questions.router)
    app.include_router(search.router)
    app.include_router(documents.router)

    # Health check endpoint
    @app.get("/health", status_code=status.HTTP_200_OK, tags=["health"])
    async def health():
        """Health check endpoint."""
        return {
            "status": "ok",
            "service": "ai-study-assistant",
            "version": settings.APP_VERSION
        }

    # Root endpoint
    @app.get("/", status_code=status.HTTP_200_OK, tags=["info"])
    async def root():
        """Root endpoint with API information."""
        return {
            "message": f"{settings.APP_NAME} API",
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs"
        }

    return app


# Create application instance
app = create_app()
