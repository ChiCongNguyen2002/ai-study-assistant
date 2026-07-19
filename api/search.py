from fastapi import APIRouter
from firebase_admin import firestore

router = APIRouter()
db = firestore.client()

@router.post("/search")
async def search(query: str):
    try:
        docs = db.collection("documents").stream()
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
        return {"error": str(e)}
