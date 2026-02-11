import fitz  # PyMuPDF
import chardet
from pathlib import Path

def extract_text(file_path: str) -> str:
    """
    Extract clean text from PDF or text file.
    Returns empty string on failure (never crashes the pipeline).
    """
    path = Path(file_path)
    
    try:
        if path.suffix.lower() == '.pdf':
            return _extract_pdf(file_path)
        elif path.suffix.lower() == '.txt':
            return _extract_txt(file_path)
    except Exception as e:
        print(f"[EXTRACTOR] Failed to extract {file_path}: {e}")
        return ""
    
    return ""


def _extract_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    doc = fitz.open(file_path)
    text_parts = []
    
    for page_num in range(min(doc.page_count, 10)):  # limit to first 10 pages
        page = doc[page_num]
        text_parts.append(page.get_text())
    
    doc.close()
    full_text = "\n".join(text_parts)
    
    # Clean up whitespace
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    return " ".join(lines)


def _extract_txt(file_path: str) -> str:
    """Extract text from .txt file with auto-encoding detection."""
    with open(file_path, 'rb') as f:
        raw = f.read()
    
    # Auto-detect encoding (handles UTF-8, Latin-1, etc.)
    detected = chardet.detect(raw)
    encoding = detected.get('encoding', 'utf-8') or 'utf-8'
    
    return raw.decode(encoding, errors='replace')


def get_snippet(text: str, length: int = 200) -> str:
    """Return a short preview snippet of text."""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + "..."
