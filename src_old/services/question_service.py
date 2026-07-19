"""Service for handling question answering via Anthropic API."""
import requests
from typing import Dict, Optional
from src.config.settings import settings
from src.constants.errors import ErrorCode, ErrorMessage


class QuestionService:
    """Service for processing questions with Claude AI."""

    @staticmethod
    def ask_question(query: str) -> Dict:
        """
        Ask a question and get an answer from Claude.

        Args:
            query: The question to ask

        Returns:
            Dictionary with answer, sources, model, and error (if any)

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            return {
                "error": ErrorMessage.API_KEY_MISSING,
                "answer": None
            }

        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return {
                "error": ErrorMessage.API_KEY_MISSING,
                "answer": None
            }

        try:
            response = requests.post(
                settings.ANTHROPIC_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": settings.ANTHROPIC_API_VERSION,
                    "content-type": "application/json"
                },
                json={
                    "model": settings.ANTHROPIC_MODEL,
                    "max_tokens": settings.ANTHROPIC_MAX_TOKENS,
                    "messages": [{
                        "role": "user",
                        "content": query
                    }]
                },
                timeout=settings.ANTHROPIC_TIMEOUT
            )

            if response.status_code != 200:
                error_msg = QuestionService._extract_error_message(response)
                return {
                    "error": f"API request failed: {error_msg}",
                    "answer": None
                }

            data = response.json()
            answer = data.get("content", [{}])[0].get("text", "No response")

            return {
                "answer": answer,
                "sources": [],
                "model": settings.ANTHROPIC_MODEL,
                "error": None
            }

        except requests.exceptions.Timeout:
            return {
                "error": ErrorMessage.API_TIMEOUT,
                "answer": None
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to process question: {str(e)}",
                "answer": None
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "answer": None
            }

    @staticmethod
    def _extract_error_message(response: requests.Response) -> str:
        """Extract error message from API response."""
        try:
            error_data = response.json().get("error", {})
            if isinstance(error_data, dict):
                return error_data.get("message", f"HTTP {response.status_code}")
            return str(error_data)
        except Exception:
            return f"HTTP {response.status_code}"
