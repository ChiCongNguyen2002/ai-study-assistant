from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

# Import routers
try:
    from . import documents, search, questions
    routers_loaded = True
except Exception as e:
    print(f"Warning: Could not load routers: {e}")
    routers_loaded = False

app = FastAPI(title="AI Study Assistant", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers if they loaded successfully
if routers_loaded:
    try:
        app.include_router(documents.router, prefix="/api", tags=["documents"])
        app.include_router(search.router, prefix="/api", tags=["search"])
        app.include_router(questions.router, prefix="/api", tags=["questions"])
    except Exception as e:
        print(f"Warning: Could not include routers: {e}")

# Health check endpoints
@app.get("/")
async def root():
    return {
        "message": "AI Study Assistant API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-study-assistant"}

# Serve static HTML from public folder
@app.get("/ui")
async def ui():
    return {
        "message": "AI Study Assistant UI",
        "access_at": "/static/index.html"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
