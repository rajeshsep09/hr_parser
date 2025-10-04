from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from app.scoring.pipeline import score_candidate_against_open_jobs, score_job_against_all_candidates
from .repository import canon_col, jobs_col

router = APIRouter(prefix="/scoring", tags=["scoring"])

@router.post("/candidate/{candidate_id}")
def score_candidate(candidate_id: str):
    """
    Score a candidate against all open jobs.
    
    Response:
      {
        "ok": true,
        "pairs_scored": 15
      }
    """
    try:
        n = score_candidate_against_open_jobs(candidate_id)
        return {"ok": True, "pairs_scored": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {e}") from e

@router.post("/job/{job_id}")
def score_job(job_id: str):
    """
    Score a job against all candidates.
    
    Response:
      {
        "ok": true,
        "pairs_scored": 25
      }
    """
    try:
        print(f"Scoring job endpoint called with job_id: {job_id}")
        n = score_job_against_all_candidates(job_id)
        print(f"Scoring completed: {n} pairs scored")
        return {"ok": True, "pairs_scored": n}
    except Exception as e:
        print(f"ERROR in score_job endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}") from e

@router.get("/candidate/{candidate_id}/job/{job_id}")
def score_single_match(candidate_id: str, job_id: str):
    """
    Score a specific candidate against a specific job.
    
    Returns detailed scoring results.
    """
    try:
        from app.scoring.score import compute_base_and_semantic
        from bson import ObjectId
        
        # Get candidate and job from database
        try:
            cand_id = ObjectId(candidate_id)
        except:
            cand_id = candidate_id
            
        try:
            j_id = ObjectId(job_id)
        except:
            j_id = job_id
        
        candidate = canon_col.find_one({"_id": cand_id})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        job = jobs_col.find_one({"_id": j_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Score single match
        result = compute_base_and_semantic(candidate, job)
        
        return {
            "candidate_id": candidate_id,
            "job_id": job_id,
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {e}") from e

@router.get("/candidate/{candidate_id}/scores")
def get_scores_for_candidate(candidate_id: str, limit: int = Query(10, ge=1, le=100)):
    """
    Get all scores for a candidate (top matches).
    
    Returns list of job matches sorted by score.
    """
    db = jobs_col.database  # same DB used elsewhere
    cur = db.scores.find({"candidate_id": candidate_id}).sort("final_score", -1).limit(limit)
    
    # Convert ObjectIds to strings for JSON serialization
    scores = []
    for doc in cur:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        scores.append(doc)
    
    return {"ok": True, "scores": scores}

@router.get("/job/{job_id}/scores")
def get_scores_for_job(job_id: str, limit: int = Query(10, ge=1, le=100)):
    """
    Get all scores for a job (top candidates).
    
    Returns list of candidate matches sorted by score.
    """
    db = jobs_col.database
    cur = db.scores.find({"job_id": job_id}).sort("final_score", -1).limit(limit)
    
    # Convert ObjectIds to strings for JSON serialization
    scores = []
    for doc in cur:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        scores.append(doc)
    
    return {"ok": True, "scores": scores}
