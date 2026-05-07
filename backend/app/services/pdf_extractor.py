import fitz  # PyMuPDF


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file using PyMuPDF."""
    doc = fitz.open(file_path)
    text_parts = []
    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text("text")
        if page_text.strip():
            text_parts.append(f"--- Page {page_num} ---\n{page_text}")
    doc.close()
    return "\n\n".join(text_parts)


def extract_text_by_page(file_path: str) -> list[dict]:
    """Extract text from each page separately, returning page number and text."""
    doc = fitz.open(file_path)
    pages = []
    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text("text")
        if page_text.strip():
            pages.append({"page": page_num, "text": page_text.strip()})
    doc.close()
    return pages
