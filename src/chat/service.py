"""Chat service with RAG integration."""
import requests
from typing import List, Dict, Optional
from src.config.settings import settings
from src.config.rag_settings import rag_settings
from src.rag.vector_store import VectorStore
from src.security.pii_detector import PIIDetector, AuditLogger
from src.chat.schemas import ChatResponse, SourceCitation

# Keywords that suggest the user is asking about a multi-step process
# ("how do I place an order", "what's the flow") rather than a single
# fact — these need the surrounding steps, not just the single
# best-matching chunk.
PROCEDURAL_KEYWORDS = [
    "làm sao", "làm thế nào", "cách ", "các bước", "quy trình", "luồng",
    "hướng dẫn", "thao tác", "trình tự",
    "how to", "step by step", "steps", "process", "workflow", "flow", "procedure"
]

NEIGHBOR_WINDOW = 2
NEIGHBOR_SOURCES_TO_EXPAND = 2
MAX_CONTEXT_CHUNKS = 12


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
        if pii_findings["has_sensitive_data"]:
            self.audit_logger.log_query(user_id, query, True, "HIGH")
            return ChatResponse(
                session_id=session_id,
                message_id="",
                query=query,
                answer=None,
                confidence=0.0,
                error="Query contains sensitive personal information. Please rephrase without PII."
            )

        # 2. Retrieve relevant documents (already filtered by similarity threshold)
        chunks = self.vector_store.search(query, top_k=rag_settings.TOP_K_RESULTS)

        if not chunks:
            return ChatResponse(
                session_id=session_id,
                message_id="",
                query=query,
                answer=None,
                confidence=0.0,
                error="No relevant documents found in knowledge base."
            )

        # 3. Multi-step "how/flow" questions need the surrounding steps,
        # not just the single best-matching chunk
        if self._is_procedural_query(query):
            chunks = self._expand_with_neighbors(chunks)

        # 4. Confidence is the retrieved chunks' own similarity score —
        # a measurable property of retrieval, not something we ask the
        # model to grade about itself.
        confidence = round(sum(c["similarity"] for c in chunks) / len(chunks) / 100, 2)

        # 5. Build context and call Claude
        context = self._build_context(chunks)
        answer = self._call_claude(query, context)

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
            self.audit_logger.log_response(user_id, session_id, True, confidence)

        return ChatResponse(
            session_id=session_id,
            message_id=f"msg_{hash(query) % 1000000}",
            query=query,
            answer=answer,
            confidence=confidence,
            sources=self._format_sources(chunks),
            follow_up_questions=self._generate_follow_ups(),
            error=None
        )

    def _is_procedural_query(self, query: str) -> bool:
        """Heuristically detect multi-step "how/flow" questions."""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in PROCEDURAL_KEYWORDS)

    def _expand_with_neighbors(self, chunks: List[Dict]) -> List[Dict]:
        """Pull in neighboring chunks from the top matching source documents."""
        seen = {(c["source"], c["chunk_index"]) for c in chunks}
        expanded = list(chunks)

        for chunk in chunks[:NEIGHBOR_SOURCES_TO_EXPAND]:
            if len(expanded) >= MAX_CONTEXT_CHUNKS:
                break

            neighbors = self.vector_store.get_neighbor_chunks(
                chunk["source"], chunk["chunk_index"], window=NEIGHBOR_WINDOW
            )
            for neighbor in neighbors:
                key = (neighbor["source"], neighbor["chunk_index"])
                if key in seen or len(expanded) >= MAX_CONTEXT_CHUNKS:
                    continue
                seen.add(key)
                # Neighbor wasn't scored by the query directly — inherit
                # the anchor chunk's similarity so citations/confidence
                # still reflect why it was pulled in.
                neighbor["similarity"] = chunk["similarity"]
                expanded.append(neighbor)

        expanded.sort(key=lambda c: (c["source"], c["chunk_index"]))
        return expanded

    def _format_sources(self, chunks: List[Dict]) -> List[SourceCitation]:
        """Dedup citations by source, keeping the highest similarity seen."""
        best_by_source: Dict[str, Dict] = {}
        for c in chunks:
            existing = best_by_source.get(c["source"])
            if existing is None or c["similarity"] > existing["similarity"]:
                best_by_source[c["source"]] = c

        return [
            SourceCitation(source=c["source"], page=c["page"], similarity=c["similarity"])
            for c in best_by_source.values()
        ]

    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "Unknown")
            page = chunk.get("page", 0)
            content = chunk.get("content", "")
            similarity = chunk.get("similarity", 0)

            context_parts.append(
                f"[Document {i}] Source: {source} (Page {page}, Relevance: {similarity}%)\n"
                f"Content: {content}\n"
            )

        return "\n".join(context_parts)

    def _call_claude(self, query: str, context: str) -> Optional[str]:
        """Call Claude API with context. Returns the answer text, or None on failure."""
        try:
            system_prompt = """You are an expert assistant helping users understand Anfin company documents and market data.

RULES:
1. Use ONLY the provided context to answer questions
2. If the context doesn't contain the answer, say "I couldn't find this information in the provided documents"
3. Always cite your sources: [Source: Document Name, Page X]
4. Be concise but comprehensive
5. Suggest 2-3 follow-up questions that would deepen understanding
6. Never make up information or hallucinate
7. Keep responses under 500 words"""

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
                return None

            answer = response.json().get("content", [{}])[0].get("text", "").strip()
            return answer or None

        except Exception as e:
            print(f"Error calling Claude: {e}")
            return None

    def _generate_follow_ups(self) -> List[str]:
        """Generate follow-up questions."""
        # Simple heuristic - can be improved with ML
        return [
            "Can you explain more about the sources mentioned?",
            "How does this relate to other market concepts?"
        ]

    def get_vector_db_stats(self) -> Dict:
        """Get vector database statistics."""
        return self.vector_store.get_stats()
