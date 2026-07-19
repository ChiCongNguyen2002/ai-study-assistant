from fastapi import APIRouter, UploadFile, File, HTTPException
from firebase_admin import firestore, storage
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

router = APIRouter()
db = firestore.client()
bucket = storage.bucket()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")

        blob = bucket.blob(f"documents/{file.filename}")
        blob.upload_from_string(content)

        db.collection("documents").add({
            "filename": file.filename,
            "format": file.filename.split('.')[-1],
            "size": len(content),
            "uploaded_at": datetime.now(),
            "user": "default"
        })

        return {
            "status": "success",
            "filename": file.filename,
            "message": "Document uploaded"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/list")
async def list_documents():
    try:
        docs = db.collection("documents").stream()
        result = []
        for doc in docs:
            result.append({
                "id": doc.id,
                "filename": doc.get("filename"),
                "format": doc.get("format"),
                "uploaded_at": doc.get("uploaded_at").isoformat() if doc.get("uploaded_at") else None
            })
        return {"documents": result}
    except Exception as e:
        return {"error": str(e)}
