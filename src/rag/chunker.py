"""Text chunking and preprocessing."""
from typing import List, Dict, Tuple
from src.config.rag_settings import rag_settings


class TextChunker:
    """
    Structure-aware chunking.

    Instead of cutting each page independently at a fixed character
    count (which can slice a procedure/sentence in half right at a
    page boundary), all pages of the same source document are merged
    in order, split into paragraph units, then greedily packed into
    chunks up to CHUNK_SIZE with the trailing paragraphs of one chunk
    carried forward as the overlap for the next — so overlap never
    cuts mid-paragraph either.
    """

    @staticmethod
    def process_documents(documents: List[Dict]) -> List[Dict]:
        """
        Process documents: merge per-source, chunk, add metadata.

        Args:
            documents: List of document/page entries (each with
                content/source/page/sensitivity)

        Returns:
            List of processed chunks with metadata
        """
        grouped: Dict[str, List[Dict]] = {}
        source_order: List[str] = []

        for doc in documents:
            source = doc.get("source", "unknown")
            if source not in grouped:
                grouped[source] = []
                source_order.append(source)
            grouped[source].append(doc)

        all_chunks = []
        for source in source_order:
            entries = grouped[source]
            sensitivity = entries[0].get("sensitivity", "MEDIUM")

            paragraphs_with_page: List[Tuple[str, int]] = []
            for entry in entries:
                content = TextChunker._clean_text(entry.get("content", ""))
                page = entry.get("page", 0)
                paragraphs_with_page.extend(
                    (para, page) for para in TextChunker._split_paragraphs(content)
                )

            if not paragraphs_with_page:
                continue

            packed = TextChunker._pack_paragraphs(
                paragraphs_with_page,
                rag_settings.CHUNK_SIZE,
                rag_settings.CHUNK_OVERLAP
            )

            for i, chunk in enumerate(packed):
                all_chunks.append({
                    "id": f"{source}_{i}",
                    "content": chunk["content"],
                    "source": source,
                    "page": chunk["page"],
                    "chunk_index": i,
                    "sensitivity": sensitivity,
                    "metadata": {
                        "source": source,
                        "page": chunk["page"],
                        "chunk_index": i,
                        "sensitivity": sensitivity
                    }
                })

        return all_chunks

    @staticmethod
    def _pack_paragraphs(paragraphs_with_page: List[Tuple[str, int]],
                          chunk_size: int, overlap: int) -> List[Dict]:
        """Greedily pack (paragraph, page) units into chunks with paragraph-level overlap."""
        # Approximate token to character conversion (1 token ≈ 4 chars)
        char_size = chunk_size * 4
        char_overlap = overlap * 4

        chunks = []
        current: List[Tuple[str, int]] = []
        current_len = 0

        def flush():
            if current:
                chunks.append({
                    "content": "\n".join(p for p, _ in current),
                    "page": current[0][1]
                })

        for para, page in paragraphs_with_page:
            para_len = len(para)

            if current and current_len + para_len > char_size:
                flush()

                # Carry trailing paragraphs forward as overlap, without
                # exceeding char_overlap, so the split never breaks a
                # paragraph in the middle.
                overlap_parts: List[Tuple[str, int]] = []
                overlap_len = 0
                for p, pg in reversed(current):
                    if overlap_len + len(p) > char_overlap:
                        break
                    overlap_parts.insert(0, (p, pg))
                    overlap_len += len(p)

                current = overlap_parts
                current_len = overlap_len

            current.append((para, page))
            current_len += para_len

        flush()
        return chunks

    @staticmethod
    def _split_paragraphs(text: str) -> List[str]:
        """Split cleaned text into paragraph units (one per non-empty line)."""
        return [line for line in text.split("\n") if line.strip()]

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text for processing while preserving paragraph breaks."""
        text = text.replace("\x00", "")
        lines = (" ".join(line.split()) for line in text.split("\n"))
        return "\n".join(line for line in lines if line)
