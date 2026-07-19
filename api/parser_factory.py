from .base import DocumentParser
from .pdf_parser import PDFParser
from .docx_parser import DocxParser

class ParserFactory:
    @staticmethod
    def get_parser(file_path: str) -> DocumentParser:
        if file_path.endswith('.pdf'):
            return PDFParser()
        elif file_path.endswith('.docx'):
            return DocxParser()
        else:
            raise ValueError(f"Format not supported: {file_path}")
