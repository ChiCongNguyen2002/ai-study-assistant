"""Document loaders for RAG system."""
import os
from pathlib import Path
from typing import List, Dict
import PyPDF2
from datetime import datetime


class PDFLoader:
    """Load and parse PDF documents."""

    @staticmethod
    def load_pdf(file_path: str) -> List[Dict]:
        """
        Load PDF and extract text with metadata.

        Args:
            file_path: Path to PDF file

        Returns:
            List of chunks with metadata
        """
        chunks = []
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                filename = Path(file_path).name

                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        chunks.append({
                            "content": text,
                            "source": filename,
                            "page": page_num,
                            "type": "pdf",
                            "loaded_at": datetime.now().isoformat(),
                            "sensitivity": "MEDIUM"  # Default, will be updated by security scan
                        })
        except Exception as e:
            print(f"Error loading PDF {file_path}: {e}")

        return chunks

    @staticmethod
    def load_all_pdfs(pdf_directory: str) -> List[Dict]:
        """Load all PDFs from directory."""
        all_chunks = []
        pdf_dir = Path(pdf_directory)

        if not pdf_dir.exists():
            print(f"PDF directory not found: {pdf_directory}")
            return all_chunks

        for pdf_file in pdf_dir.glob("**/*.pdf"):
            print(f"Loading: {pdf_file.name}")
            chunks = PDFLoader.load_pdf(str(pdf_file))
            all_chunks.extend(chunks)

        print(f"✓ Loaded {len(all_chunks)} chunks from PDFs")
        return all_chunks


class ConfluenceLoader:
    """Load documents from Confluence wiki."""

    def __init__(self, base_url: str, username: str, api_token: str):
        """Initialize Confluence loader."""
        self.base_url = base_url
        self.username = username
        self.api_token = api_token

    def load_confluence_pages(self, space_key: str = "TECH") -> List[Dict]:
        """
        Load pages from Confluence space.

        Args:
            space_key: Confluence space key (e.g., "TECH")

        Returns:
            List of document chunks
        """
        chunks = []
        try:
            # Import here to avoid dependency if not used
            from requests.auth import HTTPBasicAuth
            import requests

            # Get pages from space
            url = f"{self.base_url}/rest/api/content?spaceKey={space_key}&limit=100&expand=body.storage"
            auth = HTTPBasicAuth(self.username, self.api_token)

            response = requests.get(url, auth=auth, timeout=10)
            response.raise_for_status()

            pages = response.json().get("results", [])

            for page in pages:
                title = page.get("title", "Unknown")
                content = page.get("body", {}).get("storage", {}).get("value", "")
                page_id = page.get("id")

                if content.strip():
                    chunks.append({
                        "content": content,
                        "source": f"Confluence: {title}",
                        "page_id": page_id,
                        "type": "confluence",
                        "loaded_at": datetime.now().isoformat(),
                        "sensitivity": "HIGH"  # Confluence docs often sensitive
                    })

            print(f"✓ Loaded {len(chunks)} pages from Confluence")

        except Exception as e:
            print(f"Error loading Confluence: {e}")

        return chunks
