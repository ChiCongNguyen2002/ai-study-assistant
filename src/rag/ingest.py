"""Document ingestion pipeline: load -> chunk -> embed into vector store."""
from typing import Dict
from src.config.rag_settings import rag_settings
from src.rag.loaders import PDFLoader, ConfluenceLoader
from src.rag.chunker import TextChunker
from src.rag.vector_store import VectorStore


def ingest_documents(vector_store: VectorStore = None) -> Dict:
    """
    Load documents from all configured sources, chunk them, and
    upsert them into the vector store.

    Returns:
        Summary of the ingestion run.
    """
    vector_store = vector_store or VectorStore()

    raw_documents = PDFLoader.load_all_pdfs(rag_settings.PDF_PATH)

    if rag_settings.CONFLUENCE_URL and rag_settings.CONFLUENCE_USERNAME and rag_settings.CONFLUENCE_API_TOKEN:
        confluence_loader = ConfluenceLoader(
            base_url=rag_settings.CONFLUENCE_URL,
            username=rag_settings.CONFLUENCE_USERNAME,
            api_token=rag_settings.CONFLUENCE_API_TOKEN
        )
        raw_documents.extend(confluence_loader.load_confluence_pages())

    chunks = TextChunker.process_documents(raw_documents)
    added = vector_store.add_documents(chunks) if chunks else 0

    summary = {
        "source_documents": len(raw_documents),
        "chunks_created": len(chunks),
        "chunks_added": added,
        "vector_db": vector_store.get_stats()
    }
    print(f"✓ Ingestion complete: {summary}")
    return summary


if __name__ == "__main__":
    ingest_documents()
