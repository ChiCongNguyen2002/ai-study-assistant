"""Text chunking and preprocessing."""
from typing import List, Dict
from src.config.rag_settings import rag_settings


class TextChunker:
    """Smart text chunking with overlap."""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (tokens, ~4 chars per token)
            overlap: Overlap between chunks

        Returns:
            List of chunks
        """
        chunk_size = chunk_size or rag_settings.CHUNK_SIZE
        overlap = overlap or rag_settings.CHUNK_OVERLAP

        # Approximate token to character conversion (1 token ≈ 4 chars)
        char_size = chunk_size * 4
        char_overlap = overlap * 4

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + char_size, len(text))
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            # Move start position for next chunk (with overlap)
            start += (char_size - char_overlap)

        return chunks

    @staticmethod
    def process_documents(documents: List[Dict]) -> List[Dict]:
        """
        Process documents: chunk, clean, add metadata.

        Args:
            documents: List of document objects

        Returns:
            List of processed chunks with metadata
        """
        all_chunks = []

        for doc in documents:
            content = doc.get("content", "")
            source = doc.get("source", "unknown")
            page = doc.get("page", 0)
            sensitivity = doc.get("sensitivity", "MEDIUM")

            # Clean text
            content = TextChunker._clean_text(content)

            if not content:
                continue

            # Chunk
            text_chunks = TextChunker.chunk_text(content)

            # Create chunk objects
            for i, chunk_text in enumerate(text_chunks):
                chunk_obj = {
                    "id": f"{source}_{page}_{i}",
                    "content": chunk_text,
                    "source": source,
                    "page": page,
                    "chunk_index": i,
                    "sensitivity": sensitivity,
                    "metadata": {
                        "source": source,
                        "page": page,
                        "chunk_index": i,
                        "sensitivity": sensitivity
                    }
                }
                all_chunks.append(chunk_obj)

        return all_chunks

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text for processing."""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Remove common artifacts
        text = text.replace("\x00", "")
        return text
