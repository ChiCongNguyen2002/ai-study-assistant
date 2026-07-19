"""Vector database management."""
import chromadb
from typing import List, Dict, Tuple
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
                "page": str(doc.get("page", 0)),
                "sensitivity": doc.get("sensitivity", "MEDIUM"),
                "chunk_index": str(doc.get("chunk_index", 0))
            })

        self.collection.add(
            ids=ids,
            documents=documents_text,
            metadatas=metadatas
        )

        return len(ids)

    def search(self, query: str, top_k: int = None) -> List[Tuple[str, float, Dict]]:
        """
        Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (content, score, metadata) tuples
        """
        top_k = top_k or rag_settings.TOP_K_RESULTS

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        # Format results
        formatted_results = []
        if results["documents"] and len(results["documents"]) > 0:
            docs = results["documents"][0]
            distances = results["distances"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else []

            for doc, distance, metadata in zip(docs, distances, metadatas):
                # Convert distance to similarity (cosine distance to similarity)
                similarity = 1 - distance

                formatted_results.append({
                    "content": doc,
                    "similarity": round(similarity * 100, 1),  # 0-100%
                    "source": metadata.get("source", "unknown"),
                    "page": int(metadata.get("page", 0)),
                    "sensitivity": metadata.get("sensitivity", "MEDIUM"),
                    "metadata": metadata
                })

        return formatted_results

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
