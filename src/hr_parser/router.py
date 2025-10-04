# hr_parser/router.py
"""
FastAPI router for the hr_parser module.

Exposes:
  - POST /parser/single : parse a single uploaded resume
  - POST /parser/bulk   : parse multiple uploaded resumes

Returns JSON suitable for wiring directly into your UI or other services.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from .service import HRResumeParserService
from .job_service import HRJobParserService

router = APIRouter(prefix="/parser", tags=["hr_parser"])

# Create service instances for the process
_service = HRResumeParserService()
_job_service = HRJobParserService()


@router.post("/single")
async def parse_single(file: UploadFile = File(...)):
    """
    Parse ONE resume and store canonical result in MongoDB.

    Body (multipart/form-data):
      - file: UploadFile (pdf/docx/image/txt)

    Response:
      {
        "ok": true,
        "candidate_id": "<mongo_id>",
        "parsing_confidence": 0.87
      }
    """
    try:
        return _service.parse_fileobj(file.file, filename=file.filename)
    except Exception as e:
        # Surface a clean error to clients while logging remains in app logs
        raise HTTPException(status_code=500, detail=f"Parse failed for {file.filename}: {e}") from e


@router.post("/bulk")
async def parse_bulk(files: List[UploadFile] = File(...)):
    """
    Parse MANY resumes and store canonical results in MongoDB.

    Body (multipart/form-data):
      - files: List[UploadFile]

    Response:
      {
        "ok": true,
        "count": 3,
        "results": [
          {"ok": true,  "candidate_id": "...", "parsing_confidence": 0.9},
          {"ok": false, "file": "bad.pdf", "error": "reason"},
          {"ok": true,  "candidate_id": "...", "parsing_confidence": 0.78}
        ]
      }
    """
    try:
        items = [(f.file, f.filename) for f in files]
        results = _service.parse_bulk_fileobjs(items)
        return {"ok": True, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk parse failed: {e}") from e


@router.post("/job/single")
async def parse_job_single(file: UploadFile = File(...)):
    """
    Parse ONE job description and store canonical result in MongoDB.

    Body (multipart/form-data):
      - file: UploadFile (pdf/docx/image/txt)

    Response:
      {
        "ok": true,
        "job_id": "<mongo_id>",
        "parsing_confidence": 0.87
      }
    """
    try:
        return _job_service.parse_fileobj(file.file, filename=file.filename)
    except Exception as e:
        # Surface a clean error to clients while logging remains in app logs
        raise HTTPException(status_code=500, detail=f"Job parse failed for {file.filename}: {e}") from e


@router.post("/job/bulk")
async def parse_job_bulk(files: List[UploadFile] = File(...)):
    """
    Parse MANY job descriptions and store canonical results in MongoDB.

    Body (multipart/form-data):
      - files: List[UploadFile]

    Response:
      {
        "ok": true,
        "count": 3,
        "results": [
          {"ok": true,  "job_id": "...", "parsing_confidence": 0.9},
          {"ok": false, "file": "bad.pdf", "error": "reason"},
          {"ok": true,  "job_id": "...", "parsing_confidence": 0.78}
        ]
      }
    """
    try:
        items = [(f.file, f.filename) for f in files]
        results = _job_service.parse_bulk_fileobjs(items)
        return {"ok": True, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk job parse failed: {e}") from e