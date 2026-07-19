"""Chat API routes."""
from fastapi import APIRouter, status
from src.chat.schemas import ChatRequest, ChatResponse
from src.chat.service import ChatService
from src.rag.ingest import ingest_documents

router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_service = ChatService()


@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
    description="Send a message to RAG-powered chatbot"
)
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the chatbot.

    - **query**: Your question (required)
    - **session_id**: Chat session ID (optional)
    - **include_history**: Include chat history (optional, default True)

    Returns the chatbot response with:
    - answer: The AI-generated response
    - confidence: Confidence score (0-1)
    - sources: Referenced documents
    - follow_up_questions: Suggested follow-ups
    """
    try:
        response = chat_service.process_query(
            query=request.query,
            user_id="user_default",
            session_id=request.session_id or "sess_default"
        )
        return response
    except Exception as e:
        return ChatResponse(
            session_id=request.session_id or "sess_default",
            message_id="",
            query=request.query,
            answer=None,
            confidence=0.0,
            error=f"Error processing query: {str(e)}"
        )


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Get chatbot stats",
    description="Get vector database and system statistics"
)
async def get_stats():
    """Get chatbot statistics."""
    return {
        "status": "ok",
        "vector_db": chat_service.get_vector_db_stats()
    }


@router.post(
    "/ingest",
    status_code=status.HTTP_200_OK,
    summary="Reload knowledge base",
    description="Load documents from configured sources (PDF, Confluence), "
                 "chunk them, and upsert into the vector store"
)
async def trigger_ingest():
    """Trigger a batch (re)ingestion of documents into the vector store."""
    summary = ingest_documents(chat_service.vector_store)
    return {"status": "ok", "result": summary}
