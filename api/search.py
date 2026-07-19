from fastapi import APIRouter
from pydantic import BaseModel
from . import firebase_init

router = APIRouter()

class SearchRequest(BaseModel):
    query: str

@router.post("/search")
async def search(request: SearchRequest):
    try:
        if firebase_init.db is None:
            return {"results": [], "count": 0, "message": "Database not configured"}

        docs = firebase_init.db.collection("documents").stream()
        results = []

        for doc in docs:
            filename = doc.get("filename", "")
            if any(word.lower() in request.query.lower() for word in request.query.split()):
                results.append({
                    "id": doc.id,
                    "filename": filename,
                    "score": 0.75
                })

        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e), "results": [], "count": 0}
