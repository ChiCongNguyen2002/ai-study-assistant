from fastapi import APIRouter
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from . import firebase_init

load_dotenv('.env.local')

router = APIRouter()

class QuestionRequest(BaseModel):
    query: str

@router.post("/questions")
async def ask_question(request: QuestionRequest):
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not configured", "answer": "Demo mode: No API key"}

        import requests

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-opus-4-8",
                "max_tokens": 500,
                "messages": [{
                    "role": "user",
                    "content": f"Question: {request.query}\n\nAnswer concisely."
                }]
            },
            timeout=30
        )

        if response.status_code != 200:
            return {"error": f"API error {response.status_code}", "answer": "Demo mode: API call failed"}

        data = response.json()
        answer = data.get("content", [{}])[0].get("text", "No response")

        return {
            "answer": answer,
            "sources": [],
            "model": "claude-opus-4-8"
        }
    except Exception as e:
        return {"error": f"API call failed: {str(e)}", "answer": "Demo mode: Could not call Claude API"}
