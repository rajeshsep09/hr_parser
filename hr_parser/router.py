"""
FastAPI router for HR Resume Parser application.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from .service import hr_resume_parser_service
from .schemas import HealthCheck, ErrorResponse
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parser", tags=["resume-parser"])


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    try:
        # Check MongoDB connection
        stats = await hr_resume_parser_service.get_resume_stats()
        database_status = "healthy" if stats["success"] else "unhealthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = "unhealthy"
    
    try:
        # Check OpenAI connection (simple test)
        if settings.use_mock:
            openai_status = "healthy (mock)"
        else:
            # You could add a simple OpenAI API test here
            openai_status = "healthy"
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        openai_status = "unhealthy"
    
    return HealthCheck(
        status="healthy" if database_status == "healthy" else "unhealthy",
        version=settings.app_version,
        database_status=database_status,
        openai_status=openai_status,
        mock_mode=settings.use_mock
    )


@router.post("/single")
async def parse_single_resume(file: UploadFile = File(...)):
    """Parse a single resume file."""
    try:
        # Validate file size
        if file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        
        # Validate file extension
        file_extension = "." + file.filename.split(".")[-1].lower()
        if file_extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File extension {file_extension} not allowed. Allowed extensions: {settings.allowed_extensions}"
            )
        
        # Read file content
        content = await file.read()
        file_obj = BytesIO(content)
        
        # Parse resume
        result = await hr_resume_parser_service.parse_fileobj(file_obj, file.filename)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing single resume: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bulk")
async def parse_bulk_resumes(files: List[UploadFile] = File(...)):
    """Parse multiple resume files."""
    try:
        if len(files) > 50:  # Limit bulk processing
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 files allowed for bulk processing"
            )
        
        # Validate all files
        for file in files:
            if file.size > settings.max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {file.filename} exceeds maximum allowed size of {settings.max_file_size} bytes"
                )
            
            file_extension = "." + file.filename.split(".")[-1].lower()
            if file_extension not in settings.allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} has unsupported extension {file_extension}"
                )
        
        # Read all files
        file_items = []
        for file in files:
            content = await file.read()
            file_obj = BytesIO(content)
            file_items.append((file_obj, file.filename))
        
        # Parse all resumes
        results = await hr_resume_parser_service.parse_bulk_fileobjs(file_items)
        
        # Calculate summary
        successful_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - successful_count
        
        return {
            "success": True,
            "results": results,
            "total_processed": len(results),
            "successful_count": successful_count,
            "failed_count": failed_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing bulk resumes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/resumes/{resume_id}")
async def get_resume(resume_id: str):
    """Get resume by ID."""
    try:
        result = await hr_resume_parser_service.get_resume_by_id(resume_id)
        
        if not result["success"]:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/resumes")
async def search_resumes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):
    """Search resumes by text query."""
    try:
        result = await hr_resume_parser_service.search_resumes(
            query=q,
            limit=limit,
            skip=skip
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching resumes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_resume_stats():
    """Get resume statistics."""
    try:
        result = await hr_resume_parser_service.get_resume_stats()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: str):
    """Delete resume by ID."""
    try:
        result = await hr_resume_parser_service.delete_resume(resume_id)
        
        if not result["success"]:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=f"Request to {request.url} failed"
        ).dict()
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail="An unexpected error occurred"
        ).dict()
    )