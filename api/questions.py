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
        # Lazy import and init - ONLY when endpoint called
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not configured"}

        client = Anthropic(api_key=api_key)
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
