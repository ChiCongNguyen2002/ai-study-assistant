"""Chat service with RAG integration."""
import requests
import json
from typing import List, Dict, Tuple
from src.config.settings import settings
from src.config.rag_settings import rag_settings
from src.rag.vector_store import VectorStore
from src.security.pii_detector import PIIDetector, AuditLogger
from src.chat.schemas import ChatResponse, SourceCitation


class ChatService:
    """RAG-powered chat service."""

    def __init__(self):
        """Initialize chat service."""
        self.vector_store = VectorStore()
        self.api_key = settings.ANTHROPIC_API_KEY
        self.pii_detector = PIIDetector()
        self.audit_logger = AuditLogger()

    def process_query(self, query: str, user_id: str = "user_default",
                     session_id: str = "sess_default") -> ChatResponse:
        """
        Process user query with RAG.

        Args:
            query: User question
            user_id: User identifier
            session_id: Chat session ID

        Returns:
            Chat response with answer and sources
        """
        # 1. Detect PII in query
        pii_findings = self.pii_detector.detect_pii(query)
        has_pii = pii_findings["has_sensitive_data"]

        if has_pii:
            self.audit_logger.log_query(user_id, query, has_pii, "HIGH")
            return ChatResponse(
                session_id=session_id,
                message_id="",
                query=query,
                answer=None,
                confidence=0.0,
                error="Query contains sensitive personal information. Please rephrase without PII."
            )

        # 2. Retrieve relevant documents
        retrieval_results = self.vector_store.search(query, top_k=rag_settings.TOP_K_RESULTS)

        if not retrieval_results:
            return ChatResponse(
                session_id=session_id,
                message_id="",
                query=query,
                answer=None,
                confidence=0.0,
                error="No relevant documents found in knowledge base."
            )

        # 3. Calculate retrieval confidence
        retrieval_confidence = sum(r["similarity"] for r in retrieval_results) / len(retrieval_results) / 100

        # 4. Build context from retrieved documents
        context = self._build_context(retrieval_results)

        # 5. Call Claude with context
        answer, response_confidence = self._call_claude(query, context)

        if answer is None:
            return ChatResponse(
                session_id=session_id,
                message_id="",
                query=query,
                answer=None,
                confidence=0.0,
                error="Failed to generate response from Claude API."
            )

        # 6. Check response for PII
        response_pii = self.pii_detector.detect_pii(answer)
        if response_pii["has_sensitive_data"]:
            answer = self.pii_detector.mask_pii(answer)
            self.audit_logger.log_response(user_id, session_id, True, response_confidence)

        # 7. Format sources
        sources = [
            SourceCitation(
                source=r["source"],
                page=r["page"],
                similarity=r["similarity"]
            )
            for r in retrieval_results
        ]

        # 8. Generate follow-up questions
        follow_ups = self._generate_follow_ups(query, answer)

        # 9. Combine confidences
        final_confidence = min(retrieval_confidence * 0.4 + response_confidence * 0.6, 1.0)

        return ChatResponse(
            session_id=session_id,
            message_id=f"msg_{hash(query) % 1000000}",
            query=query,
            answer=answer,
            confidence=round(final_confidence, 2),
            sources=sources,
            follow_up_questions=follow_ups,
            error=None
        )

    def _build_context(self, retrieval_results: List[Dict]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []

        for i, result in enumerate(retrieval_results, 1):
            source = result.get("source", "Unknown")
            page = result.get("page", 0)
            content = result.get("content", "")
            similarity = result.get("similarity", 0)

            context_parts.append(
                f"[Document {i}] Source: {source} (Page {page}, Relevance: {similarity}%)\n"
                f"Content: {content}\n"
            )

        return "\n".join(context_parts)

    def _call_claude(self, query: str, context: str) -> Tuple[str, float]:
        """
        Call Claude API with context.

        Returns:
            (answer, confidence) tuple
        """
        try:
            system_prompt = """You are an expert assistant helping users understand Anfin company documents and market data.

RULES:
1. Use ONLY the provided context to answer questions
2. If the context doesn't contain the answer, say "I couldn't find this information in the provided documents"
3. Always cite your sources: [Source: Document Name, Page X]
4. Be concise but comprehensive
5. If you're uncertain about something, express it: "Based on the available documents, I'm ~60% confident that..."
6. Suggest 2-3 follow-up questions that would deepen understanding
7. Never make up information or hallucinate
8. Keep responses under 500 words"""

            user_message = f"""Context from documents:
{context}

---

User question: {query}

Please answer based ONLY on the context provided above."""

            response = requests.post(
                settings.ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": settings.ANTHROPIC_API_VERSION,
                    "content-type": "application/json"
                },
                json={
                    "model": rag_settings.CLAUDE_MODEL,
                    "max_tokens": rag_settings.CLAUDE_MAX_TOKENS,
                    "temperature": rag_settings.CLAUDE_TEMPERATURE,
                    "system": system_prompt,
                    "messages": [{
                        "role": "user",
                        "content": user_message
                    }]
                },
                timeout=settings.ANTHROPIC_TIMEOUT
            )

            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                print(f"Claude API error: {error_msg}")
                return None, 0.0

            data = response.json()
            answer = data.get("content", [{}])[0].get("text", "")

            # Estimate confidence from response
            # More specific answers = higher confidence
            confidence = 0.85 if len(answer) > 100 else 0.6

            return answer, confidence

        except Exception as e:
            print(f"Error calling Claude: {e}")
            return None, 0.0

    def _generate_follow_ups(self, query: str, answer: str) -> List[str]:
        """Generate follow-up questions."""
        # Simple heuristic - can be improved with ML
        follow_ups = [
            f"Can you explain more about the sources mentioned?",
            f"How does this relate to other market concepts?",
            f"What are the practical implications?"
        ]
        return follow_ups[:2]

    def get_vector_db_stats(self) -> Dict:
        """Get vector database statistics."""
        return self.vector_store.get_stats()
