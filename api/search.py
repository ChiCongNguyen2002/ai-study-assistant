from fastapi import APIRouter
from . import firebase_init

router = APIRouter()

@router.post("/search")
async def search(query: str):
    try:
        if firebase_init.db is None:
            return {"results": [], "count": 0, "message": "Database not configured"}

        docs = firebase_init.db.collection("documents").stream()
        results = []

        for doc in docs:
            filename = doc.get("filename", "")
            if any(word.lower() in query.lower() for word in query.split()):
                results.append({
                    "id": doc.id,
                    "filename": filename,
                    "score": 0.75
                })

        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e), "results": [], "count": 0}
