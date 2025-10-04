from typing import List, Optional

def _norm(s: str) -> str: return s.strip().lower()

def skill_overlap(required: List[str], preferred: List[str], candidate: List[str]) -> float:
    req = {_norm(x) for x in required}
    pref = {_norm(x) for x in preferred}
    cand = {_norm(x) for x in candidate}
    if not req: return 0.0
    req_hits = len(req & cand) / max(1, len(req))
    pref_hits = len(pref & cand) / max(1, len(pref)) if pref else 0.0
    denom = 2.0 + (1.0 if pref else 0.0)
    return (2.0*req_hits + 1.0*pref_hits) / denom

def experience_fit(cand_years: Optional[float], min_years: Optional[float]) -> float:
    if min_years is None: return 1.0
    if cand_years is None: return 0.0
    if cand_years >= min_years:
        return min(1.0, 0.7 + 0.3*min(1.0, (cand_years-min_years)/max(1e-9,min_years)))
    return max(0.0, cand_years / max(1e-9,min_years))

def education_fit(cand_highest: Optional[str], required: Optional[str]) -> float:
    if not required: return 1.0
    if not cand_highest: return 0.0
    return 1.0 if required.lower() in cand_highest.lower() else 0.0

def location_fit(cand_loc: Optional[str], job_loc: Optional[str]) -> float:
    if not job_loc: return 1.0
    if not cand_loc: return 0.5
    return 1.0 if job_loc.lower() in cand_loc.lower() else 0.7
