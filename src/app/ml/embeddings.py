import os, hashlib
from typing import List, Optional, Dict, Any
import numpy as np
from pymongo import MongoClient
from openai import OpenAI

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
USE_EMBEDDINGS = os.getenv("USE_EMBEDDINGS", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
_db = MongoClient(os.getenv("MONGODB_URI","mongodb://localhost:27017"))[os.getenv("DB_NAME","hyperrecruit")]
_cache = _db["_emb_cache"]  # { model, text_sha, vec }

def _sha(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def get_embedding_cached(text: Optional[str]) -> Optional[List[float]]:
    if not text or not USE_EMBEDDINGS or not _client:
        return None
    key = {"model": EMBED_MODEL, "text_sha": _sha(text)}
    hit = _cache.find_one(key)
    if hit: return hit["vec"]
    resp = _client.embeddings.create(model=EMBED_MODEL, input=text[:7000])
    vec = resp.data[0].embedding
    _cache.insert_one({**key, "vec": vec})
    return vec

def cosine(a: List[float], b: List[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb)) or 1.0
    return float(np.dot(va, vb) / denom)

class EmbeddingService:
    """Service for generating and managing embeddings for resumes and job descriptions."""
    
    def __init__(self):
        self.embedding_dim = 1536  # OpenAI text-embedding-3-small dimension
        self.skill_weights = {
            'required': 1.0,
            'preferred': 0.7,
            'candidate': 0.8
        }
    
    def generate_skill_embedding(self, skills: List[Dict[str, Any]]) -> Optional[List[float]]:
        """Generate embedding for skills list."""
        if not skills:
            return None
        
        # Weight skills by proficiency and importance
        weighted_skills = []
        for skill in skills:
            weight = self.skill_weights.get('candidate', 0.8)
            if skill.get('proficiency') == 'expert':
                weight *= 1.2
            elif skill.get('proficiency') == 'advanced':
                weight *= 1.1
            elif skill.get('proficiency') == 'beginner':
                weight *= 0.8
            
            # Add skill name multiple times based on weight
            skill_name = skill.get('name', '').lower()
            for _ in range(int(weight * 10)):
                weighted_skills.append(skill_name)
        
        # Create text for embedding
        skill_text = ' '.join(weighted_skills)
        return get_embedding_cached(skill_text)
    
    def generate_summary_embedding(self, summary: Optional[str]) -> Optional[List[float]]:
        """Generate embedding for summary text."""
        if not summary:
            return None
        
        return get_embedding_cached(summary)
    
    def generate_jd_embedding(self, job_data: Dict[str, Any]) -> Optional[List[float]]:
        """Generate embedding for job description."""
        # Combine key job elements
        jd_text_parts = []
        
        # Job title and company
        title = job_data.get('details', {}).get('title', '')
        company = job_data.get('company', {}).get('name', '')
        if title:
            jd_text_parts.append(title)
        if company:
            jd_text_parts.append(company)
        
        # Description
        description = job_data.get('description', '')
        if description:
            jd_text_parts.append(description)
        
        # Requirements
        requirements = job_data.get('requirements', {})
        required_skills = requirements.get('required_skills', [])
        preferred_skills = requirements.get('preferred_skills', [])
        
        # Add required skills with higher weight
        for skill in required_skills:
            for _ in range(int(self.skill_weights['required'] * 10)):
                jd_text_parts.append(skill.lower())
        
        # Add preferred skills with lower weight
        for skill in preferred_skills:
            for _ in range(int(self.skill_weights['preferred'] * 10)):
                jd_text_parts.append(skill.lower())
        
        # Responsibilities
        responsibilities = job_data.get('responsibilities', [])
        for resp in responsibilities:
            jd_text_parts.append(resp.lower())
        
        # Qualifications
        qualifications = job_data.get('qualifications', [])
        for qual in qualifications:
            jd_text_parts.append(qual.lower())
        
        jd_text = ' '.join(jd_text_parts)
        return get_embedding_cached(jd_text)
    
    def _text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text to embedding vector."""
        if not text:
            return np.zeros(self.embedding_dim)
        
        # Simple hash-based embedding for demonstration
        # In production, use sentence-transformers or OpenAI embeddings
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to embedding vector
        embedding = np.zeros(self.embedding_dim)
        for i in range(0, len(text_hash), 2):
            if i // 2 < self.embedding_dim:
                hex_pair = text_hash[i:i+2]
                embedding[i // 2] = int(hex_pair, 16) / 255.0 - 0.5
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def store_embeddings(self, doc: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
        """Store embeddings in document."""
        doc = doc.copy()
        
        if doc_type == 'resume':
            # Generate embeddings for resume using the specified format
            skills_text = " ".join([s.get("name", "") for s in doc.get("skills", []) if s.get("name")])
            summary_text = (doc.get("summary") or "")
            doc.setdefault("emb", {})
            doc["emb"]["skills_vec"] = get_embedding_cached(skills_text) if skills_text else None
            doc["emb"]["summary_vec"] = get_embedding_cached(summary_text)
        
        elif doc_type == 'job':
            # Generate embeddings for job description using the specified format
            required_skills = doc.get("requirements", {}).get("required_skills", [])
            preferred_skills = doc.get("requirements", {}).get("preferred_skills", [])
            title_norm = doc.get("details", {}).get("title_norm", "")
            description = doc.get("description", "")
            
            doc["emb"] = {
                "skills_vec": get_embedding_cached(" ".join(required_skills + preferred_skills)),
                "jd_vec": get_embedding_cached(f'{title_norm} {description}')
            }
        
        return doc
