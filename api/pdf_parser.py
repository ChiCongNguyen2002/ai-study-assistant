from .base import DocumentParser
import pdfplumber

class PDFParser(DocumentParser):
    def parse(self, file_path: str) -> dict:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        return {
            'title': file_path.split('/')[-1],
            'content': text,
            'pages': len(pdf.pages),
            'metadata': {'format': 'pdf', 'type': 'document'}
        }
