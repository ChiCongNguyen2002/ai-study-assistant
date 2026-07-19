"""Route handlers for document management endpoints."""
from fastapi import APIRouter, UploadFile, File, status
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["documents"])


class DocumentItem(BaseModel):
    """Model for a document item."""
    id: str
    filename: str


class UploadResponse(BaseModel):
    """Response model for upload."""
    status: str
    filename: str
    message: Optional[str] = None


class ListResponse(BaseModel):
    """Response model for list documents."""
    documents: List[DocumentItem] = []
    message: Optional[str] = None


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload document",
    description="Upload a PDF or DOCX file"
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a document (PDF or DOCX).

    - **file**: Document file (required)

    Returns upload status and filename.
    """
    return UploadResponse(
        status="warning",
        filename=file.filename,
        message="Database not configured, file received but not persisted"
    )


@router.get(
    "/list",
    response_model=ListResponse,
    status_code=status.HTTP_200_OK,
    summary="List documents",
    description="Get list of uploaded documents"
)
async def list_documents() -> ListResponse:
    """
    Get list of all uploaded documents.

    Returns list of documents and a message.
    """
    return ListResponse(
        documents=[],
        message="Database not configured"
    )
