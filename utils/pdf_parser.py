import pdfplumber
import logging
import os

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file.
    
    Args:
        file_path (str): The absolute path to the PDF file.
        
    Returns:
        str: The extracted text. Returns an empty string if extraction fails.
    """
    if not os.path.exists(file_path):
        logger.error(f"PDF file not found: {file_path}")
        return ""
        
    text = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
                else:
                    logger.warning(f"No text extracted from page {page_num} in {file_path}")
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {str(e)}")
        return ""
