#!/usr/bin/env python3
"""
Simple deduplication test.
"""

import os
import sys
sys.path.insert(0, '.')

from pymongo import MongoClient
from bson import ObjectId

def simple_test():
    """Simple test of deduplication."""
    
    # Set environment variables
    os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
    os.environ["DB_NAME"] = "hyperrecruit"
    
    print("🧪 Simple Deduplication Test")
    print("=" * 40)
    
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017")
    db = client["hyperrecruit"]
    canon_col = db["resumes_canonical"]
    
    # Check current documents
    total = canon_col.count_documents({})
    print(f"📊 Total documents: {total}")
    
    # Show latest few documents
    docs = list(canon_col.find({}, {"identity": 1, "dedupe": 1, "_id": 1}).sort("_id", -1).limit(3))
    
    for i, doc in enumerate(docs, 1):
        name = doc.get("identity", {}).get("full_name", "Unknown")
        phones = doc.get("identity", {}).get("phones", [])
        dedupe_keys = doc.get("dedupe", {}).get("keys", [])
        doc_id = str(doc["_id"])
        print(f"  {i}. {name}")
        print(f"     ID: {doc_id}")
        print(f"     Phones: {phones}")
        print(f"     Dedupe keys: {dedupe_keys}")
        print()
    
    # Test the repository function directly
    print("🔧 Testing repository function directly...")
    from hr_parser.repository import upsert_canonical
    
    # Create a test document
    test_doc = {
        "meta": {
            "canonical_version": "1.0",
            "parser_version": "hrx-0.1.0",
            "ingested_at": "2024-01-01T00:00:00Z",
            "source_file": "test.pdf",
            "parsing_confidence": 0.9,
            "hash_sha256": "test123"
        },
        "identity": {
            "full_name": "Test User",
            "first_name": "Test",
            "phones": ["555-999-8888"],
            "emails": ["test@example.com"]
        }
    }
    
    print(f"  Test document phones: {test_doc['identity']['phones']}")
    print(f"  Test document emails: {test_doc['identity']['emails']}")
    
    candidate_id = upsert_canonical(test_doc)
    print(f"  Candidate ID returned: {candidate_id}")
    
    # Check what was stored
    try:
        stored_doc = canon_col.find_one({"_id": ObjectId(candidate_id)})
        if stored_doc:
            print(f"  Stored dedupe keys: {stored_doc.get('dedupe', {}).get('keys', [])}")
        else:
            print(f"  No document found with ID: {candidate_id}")
    except Exception as e:
        print(f"  Error: {e}")
    
    client.close()

if __name__ == "__main__":
    simple_test()

