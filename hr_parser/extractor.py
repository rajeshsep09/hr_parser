import mimetypes
from pathlib import Path
import fitz
from docx import Document

def pdf_to_text(path: str) -> str:
    text = []
    with fitz.open(path) as doc:
        for p in doc:
            text.append(p.get_text("text"))
    return "\n".join(text)

def docx_to_text(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def image_to_text(path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(path))
    except Exception:
        return ""

def file_to_text(path: str) -> tuple[str, str]:
    mime, _ = mimetypes.guess_type(path)
    ext = Path(path).suffix.lower()
    if mime == "application/pdf" or ext == ".pdf":
        return pdf_to_text(path), "application/pdf"
    if ext == ".docx":
        return docx_to_text(path), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if ext in [".png",".jpg",".jpeg",".tiff",".bmp"]:
        return image_to_text(path), f"image/{ext.strip('.')}"
    with open(path, "r", errors="ignore") as f:
        return f.read(), "text/plain"
