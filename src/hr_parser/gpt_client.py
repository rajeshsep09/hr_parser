# hr_parser/gpt_client.py  (fallback for older SDKs)
import os, time, hashlib, json, re
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI
from .config import OPENAI_API_KEY, MAX_INPUT_CHARS, MAX_OUTPUT_TOKENS, USE_MOCK
from .schemas import CanonicalResume

SYSTEM_PROMPT = (
    "You are a resume parser. Extract key fields into JSON: "
    "name, first_name, phones, emails, education, experience, skills. "
    "Keep responses concise. Use null for missing data. "
    "Dates: YYYY or YYYY-MM format. "
    "Skills: normalize aliases (JS->JavaScript). "
    "Experience: include title_norm, company, dates, achievements."
)

# A compact schema description to guide JSON mode (since json_schema isn't available here)
SCHEMA_HINT = """
JSON keys:
- meta: {canonical_version, parser_version, ingested_at, source_file, source_mime, parsing_confidence, language, hash_sha256}
- identity: {full_name, first_name, last_name, emails[], phones[], links{linkedin,github,portfolio,other[]}, location{city,state,country}}
- summary: string or null
- skills: [{name, group, proficiency, years}]
- experience: [{title_raw,title_norm,company,employment_type,location,start_date,end_date,current,achievements[],tech[]}]
- education: [{institution,degree,field_of_study,start_year,end_year,score{value,scale}}]
- projects: [object]
- certifications: [object]
- preferences: {remote, relocation, notice_period_days, salary{currency, expectation_lpa}}
- work_auth: {country, status}
- dedupe: {keys[]}
"""

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _mock_response(plain_text: str, source_file: str) -> dict:
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "meta": {
            "canonical_version": "1.0",
            "parser_version": "hrx-0.1.0",
            "ingested_at": now_iso,
            "source_file": source_file,
            "source_mime": "text/plain",
            "parsing_confidence": 0.9,
            "language": "en",
            "hash_sha256": _sha256(plain_text[:5000]),
        },
        "identity": {
            "full_name": (source_file.rsplit(".", 1)[0]).replace("_", " ").title(),
            "first_name": None, "last_name": None,
            "emails": [], "phones": [],
            "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
            "location": {"city": None, "state": None, "country": None},
        },
        "summary": "Mock mode resume parsed successfully.",
        "skills": [{"name": "Python"}, {"name": "FastAPI"}],
        "experience": [], "education": [], "projects": [], "certifications": [],
        "preferences": {}, "work_auth": {}, "dedupe": {"keys": []},
    }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def parse_with_gpt(plain_text: str, source_file: str) -> dict:
    clipped = plain_text[:MAX_INPUT_CHARS]

    if USE_MOCK or not OPENAI_API_KEY:
        return _mock_response(clipped, source_file)

    client = OpenAI(api_key=OPENAI_API_KEY)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Extract and normalize this resume into the Canonical JSON described below. "
                "Pay special attention to: FIRST NAME, PHONE NUMBERS, EDUCATION (degree/institution/years), "
                "JOB TITLES/DESIGNATIONS, WORK EXPERIENCE (company/role/dates/achievements), and SKILLS. "
                "Return only valid JSON (no code fence, no prose). "
                f"\n\nSchema hint:\n{SCHEMA_HINT}\n\nResume text:\n{clipped}"
            ),
        },
    ]

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=MAX_OUTPUT_TOKENS,
    )

    raw = resp.choices[0].message.content
    
    # Clean up the response
    if raw:
        # Remove any markdown code blocks
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response (first 1000 chars): {raw[:1000]}")
        print(f"Raw response (last 500 chars): {raw[-500:]}")
        raise

    # Inject standard meta if missing
    obj.setdefault("meta", {})
    obj["meta"].setdefault("canonical_version", "1.0")
    obj["meta"].setdefault("parser_version", "hrx-0.1.0")
    obj["meta"].setdefault("ingested_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    obj["meta"].setdefault("source_file", source_file)
    obj["meta"].setdefault("hash_sha256", _sha256(clipped))
    # Ensure parsing_confidence is always a valid number
    confidence = obj["meta"].get("parsing_confidence")
    if confidence is None or not isinstance(confidence, (int, float)):
        confidence = 0.75
    obj["meta"]["parsing_confidence"] = float(confidence)

    # Fix validation issues
    # Fix country code (should be 2 characters)
    if obj.get("identity", {}).get("location", {}).get("country"):
        country = obj["identity"]["location"]["country"]
        if country == "India":
            obj["identity"]["location"]["country"] = "IN"
        elif country == "United States":
            obj["identity"]["location"]["country"] = "US"
        elif country == "United Kingdom":
            obj["identity"]["location"]["country"] = "GB"
        elif len(country) > 2:
            obj["identity"]["location"]["country"] = country[:2].upper()
    
    # Fix education score fields (remove null values)
    for edu in obj.get("education", []):
        if edu.get("score"):
            if edu["score"].get("value") is None:
                del edu["score"]["value"]
            if edu["score"].get("scale") is None:
                del edu["score"]["scale"]
            if not edu["score"]:
                del edu["score"]
    
    # Fix preferences salary fields (remove null values and handle type issues)
    if obj.get("preferences", {}).get("salary"):
        salary = obj["preferences"]["salary"]
        if salary.get("currency") is None:
            del salary["currency"]
        elif isinstance(salary.get("currency"), str) and salary["currency"].upper() in ["USD", "INR", "EUR", "GBP"]:
            # Keep currency as string if it's a valid currency code
            pass
        elif isinstance(salary.get("currency"), (int, float)):
            # Keep numeric currency values
            pass
        else:
            # Remove invalid currency values
            del salary["currency"]
            
        if salary.get("expectation_lpa") is None:
            del salary["expectation_lpa"]
        elif isinstance(salary.get("expectation_lpa"), str):
            # Try to convert string to float
            try:
                salary["expectation_lpa"] = float(salary["expectation_lpa"])
            except (ValueError, TypeError):
                del salary["expectation_lpa"]
                
        if not salary:
            del obj["preferences"]["salary"]
    
    # Fix relocation field (convert boolean to string if needed)
    if obj.get("preferences", {}).get("relocation") is not None:
        relocation = obj["preferences"]["relocation"]
        if isinstance(relocation, bool):
            obj["preferences"]["relocation"] = "Yes" if relocation else "No"
    
    # Fix experience date fields (handle "Current", "Present", etc.)
    for exp in obj.get("experience", []):
        # Handle end_date
        if exp.get("end_date"):
            end_date = exp["end_date"]
            if isinstance(end_date, str):
                end_date_lower = end_date.lower().strip()
                if end_date_lower in ["current", "present", "ongoing", "now"]:
                    exp["end_date"] = None
                    exp["current"] = True
                elif not re.match(r'^\d{4}(-\d{2})?$', end_date_lower):
                    # Try to extract year from the string
                    year_match = re.search(r'\b(19|20)\d{2}\b', end_date)
                    if year_match:
                        exp["end_date"] = year_match.group()
                    else:
                        exp["end_date"] = None
        
        # Handle start_date
        if exp.get("start_date"):
            start_date = exp["start_date"]
            if isinstance(start_date, str):
                if not re.match(r'^\d{4}(-\d{2})?$', start_date):
                    # Try to extract year from the string
                    year_match = re.search(r'\b(19|20)\d{2}\b', start_date)
                    if year_match:
                        exp["start_date"] = year_match.group()
                    else:
                        exp["start_date"] = None
    
    # Fix skills proficiency - normalize to lowercase
    for skill in obj.get("skills", []):
        if skill.get("proficiency"):
            proficiency = skill["proficiency"]
            if isinstance(proficiency, str):
                proficiency_lower = proficiency.lower().strip()
                if proficiency_lower in ["beginner", "intermediate", "advanced", "expert"]:
                    skill["proficiency"] = proficiency_lower
                else:
                    # Remove invalid proficiency
                    skill["proficiency"] = None

    return obj