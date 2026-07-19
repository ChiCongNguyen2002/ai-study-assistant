"""Route handlers for question answering endpoints."""
from fastapi import APIRouter, status
from src.api.schemas.questions import QuestionRequest, QuestionResponse
from src.services.question_service import QuestionService

router = APIRouter(prefix="/api", tags=["questions"])


@router.post(
    "/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question",
    description="Submit a question and get an answer from Claude AI"
)
async def ask_question(request: QuestionRequest) -> QuestionResponse:
    """
    Ask a question and get an answer from Claude AI.

    - **query**: The question to ask (required)

    Returns the answer, sources, model used, and any error message.
    """
    try:
        result = QuestionService.ask_question(request.query)

        return QuestionResponse(
            answer=result.get("answer"),
            sources=result.get("sources", []),
            model=result.get("model", "claude-opus-4-8"),
            error=result.get("error")
        )
    except Exception as e:
        return QuestionResponse(error=f"Request failed: {str(e)}")
