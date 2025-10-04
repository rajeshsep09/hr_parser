from typing import Dict, Any
from app.ml.embeddings import cosine

def compute_base_and_semantic(c: Dict[str,Any], j: Dict[str,Any]) -> Dict[str,Any]:
    from app.scoring.rules import skill_overlap, experience_fit, education_fit, location_fit

    # --- Candidate fields ---
    skills_data = c.get("skills") or []
    # Ensure skills is a list of dicts
    if not isinstance(skills_data, list):
        skills_data = []
    cand_skills = [s.get("name","") for s in skills_data if isinstance(s, dict)]
    
    cand_years  = c.get("total_experience_years")
    cand_edu    = c.get("highest_education")
    
    identity = c.get("identity") or {}
    if not isinstance(identity, dict):
        identity = {}
    location = identity.get("location") or {}
    if not isinstance(location, dict):
        location = {}
    cand_loc = location.get("city")

    # --- Job fields (support both flat and nested CanonicalJobDescription) ---
    requirements = j.get("requirements") or {}
    if not isinstance(requirements, dict):
        requirements = {}
    
    req  = j.get("skills_required") or requirements.get("required_skills") or []
    pref = j.get("skills_preferred") or requirements.get("preferred_skills") or []
    
    # Ensure req and pref are lists
    if not isinstance(req, list):
        req = []
    if not isinstance(pref, list):
        pref = []

    job_min = j.get("experience_min")
    if job_min is None:
        details = j.get("details") or {}
        if isinstance(details, dict):
            job_min = details.get("min_experience_years")
    if job_min is None:
        job_min = requirements.get("experience_years")

    job_edu = j.get("education_required")
    if not job_edu:
        qualifications = j.get("qualifications") or {}
        if isinstance(qualifications, dict):
            job_edu = qualifications.get("education_required")
    if not job_edu:
        job_edu = requirements.get("education_level")

    job_loc = j.get("location")
    if isinstance(job_loc, dict):
        job_loc = job_loc.get("city") or job_loc.get("region") or job_loc.get("country")

    # --- Component scores ---
    s_skills = skill_overlap(req, pref, cand_skills)
    s_sem    = 0.0

    # semantic: resume summary_vec/skills_vec vs JD jd_vec/skills_vec
    cvec = ((c.get("emb") or {}).get("summary_vec")) or ((c.get("emb") or {}).get("skills_vec"))
    jvec = ((j.get("emb") or {}).get("jd_vec")) or ((j.get("emb") or {}).get("skills_vec"))
    if cvec and jvec:
        s_sem = (cosine(cvec, jvec) + 1) / 2.0  # -1..1 → 0..1

    # Weights: 90% skills, 10% AI similarity
    final = (0.9*s_skills + 0.1*s_sem) * 100.0
    return {
        "final_score": round(final, 2),
        "components": {
            "skill": round(100*s_skills, 1),
            "semantic": round(100*s_sem, 1)
        }
    }