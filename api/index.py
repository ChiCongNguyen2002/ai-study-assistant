from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import sys

load_dotenv('.env.local')

# Import routers
try:
    from . import documents, search, questions
    routers_loaded = True
except ImportError as e:
    print(f"Warning: Could not load routers: {e}", file=sys.stderr)
    routers_loaded = False

app = FastAPI(
    title="AI Study Assistant",
    version="1.0.0",
    description="AI-powered study assistant with PDF/DOCX support"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
if routers_loaded:
    app.include_router(documents.router, prefix="/api", tags=["documents"])
    app.include_router(search.router, prefix="/api", tags=["search"])
    app.include_router(questions.router, prefix="/api", tags=["questions"])

# Root endpoints
@app.get("/")
async def root():
    return {
        "message": "AI Study Assistant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ai-study-assistant"
    }

# Export for Vercel
handler = app
