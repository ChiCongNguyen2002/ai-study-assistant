from fastapi import APIRouter
from pydantic import BaseModel
from anthropic import Anthropic
import os
from dotenv import load_dotenv
from firebase_admin import firestore

load_dotenv('.env.local')

router = APIRouter()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
db = firestore.client()

class QuestionRequest(BaseModel):
    query: str

@router.post("/questions")
async def ask_question(request: QuestionRequest):
    try:
        query = request.query
        docs = db.collection("documents").stream()
        results = []

        for doc in docs:
            filename = doc.get("filename", "")
            if any(word.lower() in query.lower() for word in query.split()):
                results.append({"filename": filename})

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
