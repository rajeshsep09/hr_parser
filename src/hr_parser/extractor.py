import mimetypes
from pathlib import Path
import fitz
from docx import Document

def pdf_to_text(path: str) -> str:
    try:
        import fitz
        text = []
        
        with fitz.open(path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Try multiple extraction methods
                page_text = ""
                
                # Method 1: Standard text extraction
                page_text = page.get_text("text")
                
                # Method 2: If no text, try blocks
                if not page_text.strip():
                    blocks = page.get_text("blocks")
                    page_text = "\n".join([block[4] for block in blocks if len(block) > 4 and isinstance(block[4], str)])
                
                # Method 3: If still no text, try words
                if not page_text.strip():
                    words = page.get_text("words")
                    page_text = " ".join([word[4] for word in words if isinstance(word[4], str)])
                
                # Method 4: If still no text, try OCR (if available)
                if not page_text.strip():
                    try:
                        # Convert page to image and use OCR
                        pix = page.get_pixmap()
                        img_data = pix.tobytes("png")
                        
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(img_data))
                        
                        import pytesseract
                        page_text = pytesseract.image_to_string(img)
                    except Exception as ocr_error:
                        print(f"OCR failed for page {page_num}: {ocr_error}")
                        page_text = ""
                
                if page_text.strip():
                    text.append(page_text)
        
        result = "\n".join(text)
        
        # Clean up the result
        if result:
            # Remove excessive whitespace
            result = "\n".join([line.strip() for line in result.split("\n") if line.strip()])
            
            # Check if we got meaningful text
            if len(result) > 50 and not result.startswith('%PDF') and not result.startswith('xœ'):
                return result
            else:
                print(f"Warning: PDF extraction may have failed for {path} - got binary or minimal content")
                return result
        else:
            print(f"Warning: No text extracted from {path}")
            return ""
            
    except Exception as e:
        print(f"Error extracting PDF text from {path}: {e}")
        return ""

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
    
    # Check if it's a PDF by extension or MIME type
    if mime == "application/pdf" or ext == ".pdf":
        return pdf_to_text(path), "application/pdf"
    
    # Check if it's a PDF by content (for temporary files without extension)
    if not ext or ext not in [".docx", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        try:
            with open(path, "rb") as f:
                header = f.read(4)
                if header == b'%PDF':
                    return pdf_to_text(path), "application/pdf"
        except Exception:
            pass
    
    if ext == ".docx":
        return docx_to_text(path), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if ext in [".png",".jpg",".jpeg",".tiff",".bmp"]:
        return image_to_text(path), f"image/{ext.strip('.')}"
    with open(path, "r", errors="ignore") as f:
        return f.read(), "text/plain"
