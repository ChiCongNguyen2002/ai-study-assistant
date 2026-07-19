"""Chat service with RAG integration."""
import requests
import json
import re
from typing import List, Dict, Optional
from src.config.settings import settings
from src.config.rag_settings import rag_settings
from src.rag.vector_store import VectorStore
from src.security.pii_detector import PIIDetector, AuditLogger
from src.chat.schemas import ChatResponse, SourceCitation

# Keywords that suggest the user is asking about a multi-step process
# ("how do I place an order", "what's the flow") rather than a single
# fact — these need more/contiguous context than a plain top-k match.
PROCEDURAL_KEYWORDS = [
    "làm sao", "làm thế nào", "cách ", "các bước", "quy trình", "luồng",
    "hướng dẫn", "thao tác", "trình tự",
    "how to", "step by step", "steps", "process", "workflow", "flow", "procedure"
]

BROAD_CANDIDATE_MULTIPLIER = 4
MIN_BROAD_CANDIDATES = 15
MAX_CONTEXT_CHUNKS = 12
NEIGHBOR_WINDOW = 2
NEIGHBOR_SOURCES_TO_EXPAND = 2


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

        # 2. Broad retrieval above the similarity threshold, then rerank
        broad_k = max(rag_settings.TOP_K_RESULTS * BROAD_CANDIDATE_MULTIPLIER, MIN_BROAD_CANDIDATES)
        candidates = self.vector_store.search(query, top_k=broad_k)

        if not candidates:
            return ChatResponse(
                session_id=session_id,
                message_id="",
                query=query,
                answer=None,
                confidence=0.0,
                error="No relevant documents found in knowledge base."
            )

        reranked = self._rerank(query, candidates, top_n=rag_settings.TOP_K_RESULTS)

        # 3. For procedural/"flow" questions, pull in neighboring chunks
        # from the same document so a multi-step procedure isn't left
        # split across chunks that individually scored lower on similarity.
        context_chunks = reranked
        if self._is_procedural_query(query):
            context_chunks = self._expand_with_neighbors(reranked)

        # 4. Calculate retrieval confidence from the chunks actually used
        retrieval_confidence = sum(c["similarity"] for c in context_chunks) / len(context_chunks) / 100

        # 5. Build context from retrieved documents
        context = self._build_context(context_chunks)

        # 6. Call Claude with context
        answer, response_confidence, grounded = self._call_claude(query, context)

        if answer is None:
            return ChatResponse(
                session_id=session_id,
                message_id="",
                query=query,
                answer=None,
                confidence=0.0,
                error="Failed to generate response from Claude API."
            )

        # 7. Check response for PII
        response_pii = self.pii_detector.detect_pii(answer)
        if response_pii["has_sensitive_data"]:
            answer = self.pii_detector.mask_pii(answer)
            self.audit_logger.log_response(user_id, session_id, True, response_confidence)

        # 8. Format sources (dedup by source, keep the highest similarity per source)
        sources = self._format_sources(context_chunks)

        # 9. Generate follow-up questions
        follow_ups = self._generate_follow_ups(query, answer)

        # 10. Combine confidences — the model's own grounded self-assessment
        # carries the most weight since it directly reflects whether the
        # retrieved context actually supported the answer.
        final_confidence = min(retrieval_confidence * 0.3 + response_confidence * 0.7, 1.0)
        if not grounded:
            final_confidence = min(final_confidence, 0.4)

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

    def _is_procedural_query(self, query: str) -> bool:
        """Heuristically detect multi-step "how/flow" questions."""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in PROCEDURAL_KEYWORDS)

    def _rerank(self, query: str, candidates: List[Dict], top_n: int) -> List[Dict]:
        """
        Rerank the broad candidate pool with Claude so the final
        context is chosen by relevance, not just raw vector distance.
        Falls back to the original similarity order if the rerank
        call fails for any reason (e.g. no API key configured).
        """
        if len(candidates) <= top_n:
            return candidates

        numbered = "\n".join(
            f"[{i}] (similarity {c['similarity']}%) {c['content'][:300]}"
            for i, c in enumerate(candidates)
        )
        prompt = f"""Rank the following document excerpts by how relevant and useful they are for answering the user's question. Respond with ONLY a JSON array of the top {top_n} excerpt numbers, most relevant first — no other text. Example: [3, 0, 7]

Question: {query}

Excerpts:
{numbered}"""

        try:
            response = requests.post(
                settings.ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": settings.ANTHROPIC_API_VERSION,
                    "content-type": "application/json"
                },
                json={
                    "model": rag_settings.CLAUDE_MODEL,
                    "max_tokens": 200,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=settings.ANTHROPIC_TIMEOUT
            )
            if response.status_code != 200:
                return candidates[:top_n]

            text = response.json().get("content", [{}])[0].get("text", "")
            match = re.search(r"\[[\d,\s]*\]", text)
            if not match:
                return candidates[:top_n]

            indices = json.loads(match.group())
            ranked = [candidates[i] for i in indices if isinstance(i, int) and 0 <= i < len(candidates)]

            if len(ranked) < top_n:
                already_ranked_ids = {id(c) for c in ranked}
                for c in candidates:
                    if id(c) not in already_ranked_ids:
                        ranked.append(c)
                    if len(ranked) >= top_n:
                        break

            return ranked[:top_n] or candidates[:top_n]

        except Exception as e:
            print(f"Rerank failed, falling back to similarity order: {e}")
            return candidates[:top_n]

    def _expand_with_neighbors(self, chunks: List[Dict]) -> List[Dict]:
        """Pull in neighboring chunks from the top matching source documents."""
        seen = {(c["source"], c["chunk_index"]) for c in chunks}
        expanded = list(chunks)

        expanded_sources = 0
        for chunk in chunks:
            if expanded_sources >= NEIGHBOR_SOURCES_TO_EXPAND:
                break
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
                # Neighbor chunks weren't scored by the query directly;
                # approximate their relevance from the anchor chunk so
                # confidence math and citations stay meaningful.
                neighbor["similarity"] = round(chunk["similarity"] * 0.85, 1)
                expanded.append(neighbor)
            expanded_sources += 1

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

    def _call_claude(self, query: str, context: str) -> tuple[Optional[str], float, bool]:
        """
        Call Claude API with context.

        Returns:
            (answer, confidence, grounded) tuple. confidence and
            grounded come from the model's own structured
            self-assessment of how well the context supports the
            answer, rather than a length-based guess.
        """
        try:
            system_prompt = """You are an expert assistant helping users understand Anfin company documents and market data.

RULES:
1. Use ONLY the provided context to answer questions
2. If the context doesn't contain the answer, say so plainly in the answer field and set grounded to false
3. Always cite your sources: [Source: Document Name, Page X]
4. Be concise but comprehensive
5. Suggest 2-3 follow-up questions that would deepen understanding
6. Never make up information or hallucinate
7. Keep responses under 500 words

Respond with ONLY a JSON object, no other text, in this exact shape:
{"answer": "...", "confidence": 0.0-1.0, "grounded": true or false}
Where confidence reflects how well the provided context actually supports the answer, and grounded is false whenever the answer had to go beyond what the context contains."""

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
                return None, 0.0, False

            data = response.json()
            raw_text = data.get("content", [{}])[0].get("text", "")

            return self._parse_structured_answer(raw_text)

        except Exception as e:
            print(f"Error calling Claude: {e}")
            return None, 0.0, False

    def _parse_structured_answer(self, raw_text: str) -> tuple[Optional[str], float, bool]:
        """Parse the {answer, confidence, grounded} JSON Claude was asked to return."""
        try:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            payload = json.loads(match.group()) if match else json.loads(raw_text)

            answer = payload.get("answer")
            confidence = float(payload.get("confidence", 0.5))
            grounded = bool(payload.get("grounded", True))

            if not answer:
                return None, 0.0, False

            return answer, max(0.0, min(confidence, 1.0)), grounded

        except Exception:
            # Model didn't return valid JSON — fall back to treating the
            # raw text as the answer with a conservative confidence
            # instead of failing the whole request.
            if raw_text.strip():
                return raw_text.strip(), 0.5, True
            return None, 0.0, False

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
