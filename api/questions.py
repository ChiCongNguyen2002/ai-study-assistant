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
            return {"error": "API key not configured", "answer": None}

        import requests

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-12-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1024,
                "system": "Bạn là một trợ lý AI hữu ích. Hãy trả lời ngắn gọn và chính xác.",
                "messages": [{
                    "role": "user",
                    "content": request.query
                }]
            },
            timeout=8
        )

        if response.status_code != 200:
            error_detail = response.json().get("error", {}).get("message", f"HTTP {response.status_code}") if response.text else f"HTTP {response.status_code}"
            return {"error": f"API request failed: {error_detail}", "answer": None}

        data = response.json()
        answer = data.get("content", [{}])[0].get("text", "No response")

        return {
            "answer": answer,
            "sources": [],
            "model": "claude-3-5-sonnet-20241022"
        }
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            error_msg = "Request timed out - API is taking too long to respond"
        return {"error": f"Failed to process question: {error_msg}", "answer": None}
