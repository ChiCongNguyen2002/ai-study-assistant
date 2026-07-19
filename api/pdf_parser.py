from .base import DocumentParser
from PyPDF2 import PdfReader

class PDFParser(DocumentParser):
    def parse(self, file_path: str) -> dict:
        text = ""
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)

            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            text = f"Error parsing PDF: {str(e)}"
            num_pages = 0

        return {
            'title': file_path.split('/')[-1],
            'content': text,
            'pages': num_pages,
            'metadata': {'format': 'pdf', 'type': 'document'}
        }
