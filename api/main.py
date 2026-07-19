from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from . import documents, search, questions
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

app = FastAPI(title="AI Study Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(questions.router, prefix="/api", tags=["questions"])

@app.get("/")
async def root():
    return {"message": "AI Study Assistant API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-study-assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
