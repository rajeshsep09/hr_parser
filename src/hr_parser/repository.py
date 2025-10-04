from pymongo import MongoClient
from .config import MONGODB_URI, DB_NAME

_client = MongoClient(MONGODB_URI)
_db = _client[DB_NAME]

canon_col = _db["resumes_canonical"]
jobs_col = _db["jobs_canonical"]

def upsert_canonical(doc: dict) -> str:
    """
    Upsert canonical resume with phone number as primary deduplication key.
    Priority: phone > email > hash
    """
    emails = [e.lower() for e in (doc.get("identity", {}).get("emails") or [])]
    phones = doc.get("identity", {}).get("phones") or []
    
    # Create deduplication keys with phone as primary
    keys = []
    
    # 1. Phone numbers (primary key)
    for phone in phones:
        # Normalize phone number (remove spaces, dashes, parentheses)
        normalized_phone = ''.join(filter(str.isdigit, phone))
        if normalized_phone:
            keys.append(f"phone:{normalized_phone}")
    
    # 2. Email addresses (secondary)
    for email in emails:
        keys.append(f"email:{email}")
    
    # 3. Hash as fallback
    if not keys:
        keys = [f"hash:{doc['meta'].get('hash_sha256','')}"]
    
    # Set dedupe keys in the document
    doc.setdefault("dedupe", {})
    doc["dedupe"]["keys"] = list(set(keys))
    
    # Try to find existing record by phone first, then email, then hash
    existing_doc = None
    
    # Search by phone numbers first (primary deduplication)
    if phones:
        for phone in phones:
            normalized_phone = ''.join(filter(str.isdigit, phone))
            if normalized_phone:
                existing_doc = canon_col.find_one({"dedupe.keys": f"phone:{normalized_phone}"})
                if existing_doc:
                    break
    
    # If no phone match, search by email
    if not existing_doc and emails:
        for email in emails:
            existing_doc = canon_col.find_one({"dedupe.keys": f"email:{email}"})
            if existing_doc:
                break
    
    # If still no match, search by hash
    if not existing_doc:
        hash_key = f"hash:{doc['meta'].get('hash_sha256','')}"
        existing_doc = canon_col.find_one({"dedupe.keys": hash_key})
    
    if existing_doc:
        # Update existing document
        result = canon_col.find_one_and_update(
            {"_id": existing_doc["_id"]},
            {"$set": doc},
            return_document=True
        )
        return str(result["_id"])
    else:
        # Insert new document
        result = canon_col.insert_one(doc)
        return str(result.inserted_id)

def upsert_job(doc: dict) -> str:
    """
    Upsert canonical job description with company name and job title as primary deduplication key.
    Priority: company+title > company+hash > hash
    """
    company_name = doc.get("company", {}).get("name", "").lower().strip()
    job_title = doc.get("details", {}).get("title", "").lower().strip()
    
    # Create deduplication keys
    keys = []
    
    # 1. Company + Job Title (primary key)
    if company_name and job_title:
        keys.append(f"company_title:{company_name}_{job_title}")
    
    # 2. Company name (secondary)
    if company_name:
        keys.append(f"company:{company_name}")
    
    # 3. Hash as fallback
    if not keys:
        keys = [f"hash:{doc['meta'].get('hash_sha256','')}"]
    
    # Set dedupe keys in the document
    doc.setdefault("dedupe", {})
    doc["dedupe"]["keys"] = list(set(keys))
    
    # Try to find existing record by company+title first, then company, then hash
    existing_doc = None
    
    # Search by company + title first (primary deduplication)
    if company_name and job_title:
        existing_doc = jobs_col.find_one({"dedupe.keys": f"company_title:{company_name}_{job_title}"})
    
    # If no company+title match, search by company
    if not existing_doc and company_name:
        existing_doc = jobs_col.find_one({"dedupe.keys": f"company:{company_name}"})
    
    # If still no match, search by hash
    if not existing_doc:
        hash_key = f"hash:{doc['meta'].get('hash_sha256','')}"
        existing_doc = jobs_col.find_one({"dedupe.keys": hash_key})
    
    if existing_doc:
        # Update existing document
        result = jobs_col.find_one_and_update(
            {"_id": existing_doc["_id"]},
            {"$set": doc},
            return_document=True
        )
        return str(result["_id"])
    else:
        # Insert new document
        result = jobs_col.insert_one(doc)
        return str(result.inserted_id)