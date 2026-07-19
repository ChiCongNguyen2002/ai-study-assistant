from fastapi import APIRouter
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from . import firebase_init

load_dotenv('.env.local')

router = APIRouter()

class QuestionRequest(BaseModel):
    query: str

# Lazy load client only when needed
_client = None

def get_client():
    global _client
    if _client is None:
        try:
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                _client = Anthropic(api_key=api_key)
        except Exception as e:
            print(f"Warning: Could not initialize Anthropic client: {e}")
    return _client

@router.post("/questions")
async def ask_question(request: QuestionRequest):
    try:
        client = get_client()
        if not client:
            return {"error": "ANTHROPIC_API_KEY not configured or client unavailable"}

        query = request.query
        results = []

        if firebase_init.db:
            try:
                docs = firebase_init.db.collection("documents").stream()
                for doc in docs:
                    filename = doc.get("filename", "")
                    if any(word.lower() in query.lower() for word in query.split()):
                        results.append({"filename": filename})
            except Exception as e:
                print(f"Database query warning: {e}")

        context = "Study materials available."
        if results:
            context += f" Found {len(results)} relevant documents: " + ", ".join([r['filename'] for r in results])

        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Context: {context}

Question: {query}

Answer based on the study materials available."""
            }]
        )

        return {
            "answer": response.content[0].text,
            "sources": results,
            "model": "claude-opus-4-8"
        }
    except Exception as e:
        return {"error": str(e)}
