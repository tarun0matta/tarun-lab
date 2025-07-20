from PyPDF2 import PdfReader
from typing import Optional

def pdf_to_text(file_path: str) -> Optional[str]:
    """
    Extract text from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        Optional[str]: Extracted text or None if extraction fails
    """
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None 