import tempfile, shutil, time, hashlib
from typing import Iterable, List, Dict, Any
from .extractor import file_to_text
from .job_gpt_client import parse_job_with_gpt
from .job_schemas import CanonicalJobDescription
from .repository import upsert_job
from app.ml.embeddings import EmbeddingService

# Force reload of extractor module
import importlib
import hr_parser.extractor
importlib.reload(hr_parser.extractor)
from .extractor import file_to_text

class HRJobParserService:
    """Drop-in service for single/bulk job description parsing."""

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def parse_fileobj(self, fileobj, filename: str) -> Dict[str, Any]:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(fileobj, tmp)
            tmp_path = tmp.name

        text, mime = file_to_text(tmp_path)

        canonical = parse_job_with_gpt(text, source_file=filename)
        # fill meta if missing
        canonical.setdefault("meta", {})
        canonical["meta"].setdefault("source_file", filename)
        canonical["meta"].setdefault("source_mime", mime)
        canonical["meta"].setdefault("parsing_confidence", 0.7)

        # validate schema
        CanonicalJobDescription.model_validate(canonical)

        # Add embeddings
        canonical = self.embedding_service.store_embeddings(canonical, 'job')

        job_id = upsert_job(canonical)
        return {"ok": True, "job_id": job_id,
                "parsing_confidence": canonical["meta"]["parsing_confidence"]}

    def parse_bulk_fileobjs(self, items: Iterable[tuple]) -> List[Dict[str, Any]]:
        out = []
        for fileobj, filename in items:
            try:
                out.append(self.parse_fileobj(fileobj, filename))
            except Exception as e:
                out.append({"ok": False, "file": filename, "error": str(e)})
        return out
