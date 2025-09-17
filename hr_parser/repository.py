from pymongo import MongoClient
from .config import MONGODB_URI, DB_NAME

_client = MongoClient(MONGODB_URI)
_db = _client[DB_NAME]

raw_col = _db["resumes_raw"]
canon_col = _db["resumes_canonical"]

def insert_raw(path: str, text: str, meta: dict) -> str:
    res = raw_col.insert_one({"path": path, "text": text, "meta": meta})
    return str(res.inserted_id)

def upsert_canonical(doc: dict) -> str:
    emails = [e.lower() for e in (doc.get("identity", {}).get("emails") or [])]
    phones = doc.get("identity", {}).get("phones") or []
    keys = [f"email:{e}" for e in emails] + [f"phone:{p}" for p in phones]
    if not keys:
        keys = [f"hash:{doc['meta'].get('hash_sha256','')}"]
    doc.setdefault("dedupe", {}).setdefault("keys", list(set(keys)))

    res = canon_col.find_one_and_update(
        {"dedupe.keys": {"$in": doc["dedupe"]["keys"]}},
        {"$set": doc},
        upsert=True,
        return_document=True
    )
    return str(res["_id"]) if res else "upserted"