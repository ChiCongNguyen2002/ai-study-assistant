"""Vector database management."""
import chromadb
from typing import List, Dict, Optional
from src.config.rag_settings import rag_settings


class VectorStore:
    """ChromaDB vector store for embeddings."""

    def __init__(self, persist_directory: str = None):
        """Initialize vector store."""
        self.persist_dir = persist_directory or rag_settings.CHROMA_PATH
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="anfin_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: List[Dict]) -> int:
        """
        Add documents to vector store.

        Args:
            documents: List of document chunks with content and metadata

        Returns:
            Number of documents added
        """
        ids = []
        documents_text = []
        metadatas = []

        for doc in documents:
            ids.append(doc.get("id", f"doc_{len(ids)}"))
            documents_text.append(doc.get("content", ""))
            metadatas.append({
                "source": doc.get("source", "unknown"),
                "page": int(doc.get("page", 0)),
                "sensitivity": doc.get("sensitivity", "MEDIUM"),
                "chunk_index": int(doc.get("chunk_index", 0))
            })

        # upsert (not add) so re-running ingestion is idempotent and safe
        # for daily batch reloads without failing on duplicate chunk IDs
        self.collection.upsert(
            ids=ids,
            documents=documents_text,
            metadatas=metadatas
        )

        return len(ids)

    def search(self, query: str, top_k: int = None,
               min_similarity: Optional[float] = None) -> List[Dict]:
        """
        Search for relevant documents above a similarity threshold.

        Args:
            query: Search query
            top_k: Number of candidates to fetch before filtering
            min_similarity: Minimum similarity (0-1 scale) to keep a
                result; defaults to rag_settings.SIMILARITY_THRESHOLD.
                Pass 0 to disable filtering (e.g. for a broad
                candidate pool that will be reranked downstream).

        Returns:
            List of result dicts sorted by similarity descending
        """
        top_k = top_k or rag_settings.TOP_K_RESULTS
        threshold = rag_settings.SIMILARITY_THRESHOLD if min_similarity is None else min_similarity

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        formatted_results = []
        if results["documents"] and len(results["documents"]) > 0:
            docs = results["documents"][0]
            distances = results["distances"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else []

            for doc, distance, metadata in zip(docs, distances, metadatas):
                # Convert distance to similarity (cosine distance to similarity)
                similarity = 1 - distance

                if similarity < threshold:
                    continue

                formatted_results.append({
                    "content": doc,
                    "similarity": round(similarity * 100, 1),  # 0-100%
                    "source": metadata.get("source", "unknown"),
                    "page": int(metadata.get("page", 0)),
                    "chunk_index": int(metadata.get("chunk_index", 0)),
                    "sensitivity": metadata.get("sensitivity", "MEDIUM"),
                    "metadata": metadata
                })

        return formatted_results

    def get_neighbor_chunks(self, source: str, chunk_index: int, window: int = 2) -> List[Dict]:
        """
        Fetch the chunks immediately before/after a given chunk in the
        same source document, to reconstruct a multi-step procedure
        that a single top-k similarity match would only capture part of.

        Args:
            source: Document filename the chunk belongs to
            chunk_index: Index of the anchor chunk
            window: How many chunks to include on each side

        Returns:
            List of neighboring chunk dicts (excluding the anchor),
            ordered by chunk_index
        """
        target_indices = [
            i for i in range(chunk_index - window, chunk_index + window + 1)
            if i != chunk_index and i >= 0
        ]
        if not target_indices:
            return []

        results = self.collection.get(
            where={
                "$and": [
                    {"source": {"$eq": source}},
                    {"chunk_index": {"$in": target_indices}}
                ]
            }
        )

        neighbors = []
        for doc, metadata in zip(results.get("documents", []), results.get("metadatas", [])):
            neighbors.append({
                "content": doc,
                "source": metadata.get("source", "unknown"),
                "page": int(metadata.get("page", 0)),
                "chunk_index": int(metadata.get("chunk_index", 0)),
                "sensitivity": metadata.get("sensitivity", "MEDIUM"),
                "metadata": metadata
            })

        neighbors.sort(key=lambda c: c["chunk_index"])
        return neighbors

    def clear(self):
        """Clear all documents from vector store."""
        self.client.delete_collection(name="anfin_documents")
        self.collection = self.client.get_or_create_collection(
            name="anfin_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def get_stats(self) -> Dict:
        """Get vector store statistics."""
        count = self.collection.count()
        return {
            "total_documents": count,
            "collection_name": "anfin_documents",
            "database_type": "chromadb",
            "path": self.persist_dir
        }
