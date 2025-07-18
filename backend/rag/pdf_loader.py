from PyPDF2 import PdfReader

def pdf_to_text(pdf_path):
    reader = PdfReader(pdf_path)
    return '\n'.join(page.extract_text() for page in reader.pages) 