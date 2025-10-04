import tempfile, shutil, time, hashlib
from typing import Iterable, List, Dict, Any
from .extractor import file_to_text
from .gpt_client import parse_with_gpt
from .schemas import CanonicalResume
from .repository import upsert_canonical
from app.ml.embeddings import EmbeddingService

# Force reload of extractor module
import importlib
import hr_parser.extractor
importlib.reload(hr_parser.extractor)
from .extractor import file_to_text

class HRResumeParserService:
    """Drop-in service for single/bulk resume parsing."""

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def parse_fileobj(self, fileobj, filename: str) -> Dict[str, Any]:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(fileobj, tmp)
            tmp_path = tmp.name

        text, mime = file_to_text(tmp_path)

        canonical = parse_with_gpt(text, source_file=filename)
        # fill meta if missing
        canonical.setdefault("meta", {})
        canonical["meta"].setdefault("source_file", filename)
        canonical["meta"].setdefault("source_mime", mime)
        canonical["meta"].setdefault("parsing_confidence", 0.7)

        # validate schema
        CanonicalResume.model_validate(canonical)

        # Add embeddings
        canonical = self.embedding_service.store_embeddings(canonical, 'resume')

        candidate_id = upsert_canonical(canonical)
        return {"ok": True, "candidate_id": candidate_id,
                "parsing_confidence": canonical["meta"]["parsing_confidence"]}

    def parse_bulk_fileobjs(self, items: Iterable[tuple]) -> List[Dict[str, Any]]:
        out = []
        for fileobj, filename in items:
            try:
                out.append(self.parse_fileobj(fileobj, filename))
            except Exception as e:
                out.append({"ok": False, "file": filename, "error": str(e)})
        return out