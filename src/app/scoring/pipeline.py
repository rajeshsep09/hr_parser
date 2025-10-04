import time, os
from typing import Union
from bson import ObjectId
from pymongo import MongoClient
from app.scoring.score import compute_base_and_semantic

client = MongoClient(os.getenv("MONGODB_URI","mongodb://localhost:27017"))
db = client[os.getenv("DB_NAME","hyperrecruit")]

def _oid(x: Union[str, ObjectId]) -> ObjectId:
    return x if isinstance(x, ObjectId) else ObjectId(str(x))

def score_candidate_against_open_jobs(candidate_id):
    c = db.resumes_canonical.find_one({"_id": _oid(candidate_id)})
    if not c: return 0
    cnt = 0
    # Score against all jobs (remove status filter since we don't have that field)
    for j in db.jobs_canonical.find({}):
        res = compute_base_and_semantic(c, j)
        key = {"job_id": str(j["_id"]), "candidate_id": str(c["_id"])}
        db.scores.update_one(key, {"$set": {
            **key, **res, "version":"v1.0", "scored_at": time.time()
        }}, upsert=True)
        cnt += 1
    return cnt

def score_job_against_all_candidates(job_id):
    try:
        j = db.jobs_canonical.find_one({"_id": _oid(job_id)})
        if not j:
            print(f"Job not found: {job_id}")
            return 0
        
        print(f"Scoring job {job_id} against all candidates...")
        cnt = 0
        for c in db.resumes_canonical.find({}):
            try:
                res = compute_base_and_semantic(c, j)
                key = {"job_id": str(j["_id"]), "candidate_id": str(c["_id"])}
                db.scores.update_one(key, {"$set": {
                    **key, **res, "version":"v1.0", "scored_at": time.time()
                }}, upsert=True)
                cnt += 1
            except Exception as e:
                print(f"Error scoring candidate {c.get('_id')}: {e}")
                # Continue with next candidate instead of failing completely
                continue
        
        print(f"Scored {cnt} candidates successfully")
        return cnt
    except Exception as e:
        print(f"Fatal error in score_job_against_all_candidates: {e}")
        import traceback
        traceback.print_exc()
        raise