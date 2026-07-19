from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import os
from dotenv import load_dotenv
from . import firebase_init

load_dotenv('.env.local')

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")

        if firebase_init.db is None:
            return {
                "status": "warning",
                "filename": file.filename,
                "message": "Database not configured, file received but not persisted"
            }

        if firebase_init.bucket:
            try:
                blob = firebase_init.bucket.blob(f"documents/{file.filename}")
                blob.upload_from_string(content)
            except Exception as e:
                print(f"Storage upload warning: {e}")

        firebase_init.db.collection("documents").add({
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
        if firebase_init.db is None:
            return {"documents": [], "message": "Database not configured"}

        docs = firebase_init.db.collection("documents").stream()
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
        return {"error": str(e), "documents": []}
