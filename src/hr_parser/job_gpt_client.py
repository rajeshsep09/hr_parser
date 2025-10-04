# hr_parser/job_gpt_client.py
import os, time, hashlib, json, re
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI
from .config import OPENAI_API_KEY, MAX_INPUT_CHARS, MAX_OUTPUT_TOKENS, USE_MOCK
from .job_schemas import CanonicalJobDescription

SYSTEM_PROMPT = (
    "You are an expert job description parser. Analyze the ENTIRE document carefully to extract ALL information accurately. "
    "Read through the complete text to understand context before extracting fields.\n\n"
    "EXTRACTION GUIDELINES:\n"
    "1. Job Title: Look for any mention of job title, role, position. It may appear as 'Job Title:', 'Position:', 'Role:', or in headings. "
    "Common patterns: 'Data Scientist', 'Software Engineer III', 'Senior DevOps Engineer', etc.\n"
    "2. Company: Extract company name from document header, footer, or mentions like 'Company:', '[CompanyName] is looking for...'\n"
    "3. Location: Look for city names, states, countries. May appear as 'Location:', 'Based in:', or within text.\n"
    "4. Work Model: Identify if Remote, Hybrid, or On-site. Look for phrases like 'remote', 'hybrid', 'office', 'WFH', 'work from home'.\n"
    "5. Responsibilities: Extract ALL bullet points or paragraphs under sections like 'Responsibilities', 'What you'll do', 'Role', 'Duties'.\n"
    "6. Qualifications/Requirements: Extract from sections like 'Requirements', 'Qualifications', 'Must have', 'Minimum Qualifications'.\n"
    "7. Skills: Identify required vs preferred skills. Look for technical skills, tools, technologies mentioned.\n"
    "8. Experience: Extract years of experience required (e.g., '6-8 years', '5+ years').\n"
    "9. Education: Look for degree requirements (Bachelor's, Master's, PhD, etc.).\n\n"
    "OUTPUT FORMATTING (CRITICAL):\n"
    "- employment_type: MUST be exactly one of: 'full_time', 'part_time', 'contract', 'internship', 'temporary' (lowercase with underscore)\n"
    "- travel_required: MUST be boolean true/false or null (NOT string)\n"
    "- education_level: MUST be exactly one of: 'high_school', 'associate', 'bachelor', 'master', 'phd', 'none'\n"
    "- country: MUST be 2-letter ISO code (US, IN, GB, CA, etc.)\n"
    "- remote, hybrid, visa_sponsorship: MUST be boolean true/false or null\n"
    "- Extract experience as NUMBER (e.g., 6 for '6-8 years', use minimum of range)\n"
    "- Use null for truly missing data, infer from context when possible"
)

# A compact schema description to guide JSON mode
SCHEMA_HINT = """
JSON keys:
- meta: {canonical_version, parser_version, ingested_at, source_file, source_mime, parsing_confidence, language, hash_sha256}
- company: {name, industry, size, website, description}
- details: {title, department, employment_type, work_schedule, travel_required, visa_sponsorship}
- location: {city, state, country, remote, hybrid}
- requirements: {experience_years, education_level, required_skills[], preferred_skills[], certifications[], languages[]}
- compensation: {salary_min, salary_max, currency, equity, benefits[]}
- application: {contact_email, application_url, application_deadline, application_method}
- description: string or null
- responsibilities: [string]
- qualifications: [string]
- benefits: [string]
- culture: string or null
- growth_opportunities: [string]
- dedupe: {keys[]}
"""

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _mock_job_response(plain_text: str, source_file: str) -> dict:
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
        "company": {
            "name": "Tech Corp",
            "industry": "Technology",
            "size": "201-1000",
            "website": None,
            "description": "Leading technology company"
        },
        "details": {
            "title": "Software Engineer",
            "department": "Engineering",
            "employment_type": "full_time",
            "work_schedule": None,
            "travel_required": False,
            "visa_sponsorship": True
        },
        "location": {
            "city": "San Francisco",
            "state": "CA",
            "country": "US",
            "remote": True,
            "hybrid": True
        },
        "requirements": {
            "experience_years": 3,
            "education_level": "bachelor",
            "required_skills": ["Python", "JavaScript", "React"],
            "preferred_skills": ["AWS", "Docker"],
            "certifications": [],
            "languages": ["English"]
        },
        "compensation": {
            "salary_min": 80000,
            "salary_max": 120000,
            "currency": "USD",
            "equity": True,
            "benefits": ["Health Insurance", "401k", "PTO"]
        },
        "application": {
            "contact_email": "jobs@techcorp.com",
            "application_url": None,
            "application_deadline": None,
            "application_method": "email"
        },
        "description": "Mock job description parsed successfully.",
        "responsibilities": ["Develop software applications", "Collaborate with team"],
        "qualifications": ["3+ years experience", "Bachelor's degree"],
        "benefits": ["Health Insurance", "401k", "PTO"],
        "culture": "Innovative and collaborative",
        "growth_opportunities": ["Career advancement", "Learning opportunities"],
        "dedupe": {"keys": []},
    }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def parse_job_with_gpt(plain_text: str, source_file: str) -> dict:
    clipped = plain_text[:MAX_INPUT_CHARS]

    if USE_MOCK or not OPENAI_API_KEY:
        return _mock_job_response(clipped, source_file)

    client = OpenAI(api_key=OPENAI_API_KEY)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Parse this job description and extract ALL information EXACTLY as written.\n\n"
                "EXTRACTION RULES:\n"
                "1. If you see 'Job Title: Senior Data Scientist – Retail Analytics', extract the COMPLETE title after 'Job Title:'\n"
                "2. If you see 'Location: Chennai, India', extract city='Chennai', country='IN'\n"
                "3. If you see 'Employment Type: Full-time', convert to employment_type='full_time'\n"
                "4. If you see 'Work Model: Hybrid', set location.hybrid=true, location.remote=false\n"
                "5. If you see 'Experience Required: 6+ years', extract the NUMBER (6) into requirements.experience_years\n"
                "6. If you see 'Education: Master's degree', set requirements.education_level='master'\n"
                "7. Extract ALL bullet points under 'Responsibilities' into the responsibilities array\n"
                "8. Skills under 'Required Skills' go into requirements.required_skills array\n"
                "9. Skills under 'Preferred Skills' go into requirements.preferred_skills array\n"
                "10. Extract company info from 'About the Company' section\n\n"
                "CRITICAL FORMATTING:\n"
                "- details.title must be the EXACT complete job title as written\n"
                "- requirements.required_skills: extract each skill mentioned (Python, SQL, Spark, etc.)\n"
                "- requirements.preferred_skills: extract each preferred skill\n"
                "- responsibilities: extract EVERY bullet point as separate array item\n"
                "- qualifications: extract from 'Required Skills' or 'Qualifications' section\n\n"
                "Return ONLY valid JSON (no markdown, no code fence). "
                f"\n\nSchema:\n{SCHEMA_HINT}\n\nJob description:\n{clipped}"
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
    if obj.get("location", {}).get("country"):
        country = obj["location"]["country"]
        if country == "United States":
            obj["location"]["country"] = "US"
        elif country == "United Kingdom":
            obj["location"]["country"] = "GB"
        elif country == "India":
            obj["location"]["country"] = "IN"
        elif len(country) > 2:
            obj["location"]["country"] = country[:2].upper()

    # Fix compensation fields (remove null values and handle type issues)
    if obj.get("compensation", {}).get("salary_min") is None:
        del obj["compensation"]["salary_min"]
    if obj.get("compensation", {}).get("salary_max") is None:
        del obj["compensation"]["salary_max"]
    if obj.get("compensation", {}).get("currency") is None:
        del obj["compensation"]["currency"]
    if obj.get("compensation", {}).get("equity") is None:
        del obj["compensation"]["equity"]

    # Fix application deadline format
    if obj.get("application", {}).get("application_deadline"):
        deadline = obj["application"]["application_deadline"]
        if isinstance(deadline, str):
            # Try to extract year from the string
            year_match = re.search(r'\b(19|20)\d{2}\b', deadline)
            if year_match:
                obj["application"]["application_deadline"] = year_match.group()
            else:
                obj["application"]["application_deadline"] = None

    # Fix employment type
    if obj.get("details", {}).get("employment_type"):
        emp_type = obj["details"]["employment_type"]
        if isinstance(emp_type, str):
            emp_type_lower = emp_type.lower().strip()
            valid_type = None
            if emp_type_lower in ["full-time", "full time", "fulltime"]:
                valid_type = "full_time"
            elif emp_type_lower in ["part-time", "part time", "parttime"]:
                valid_type = "part_time"
            elif emp_type_lower in ["contractor", "contract"]:
                valid_type = "contract"
            elif emp_type_lower in ["intern", "internship"]:
                valid_type = "internship"
            elif emp_type_lower in ["temp", "temporary"]:
                valid_type = "temporary"
            
            if valid_type:
                obj["details"]["employment_type"] = valid_type
            else:
                # If invalid value, set to None
                obj["details"]["employment_type"] = None
    
    # Fix travel_required to be boolean or None
    if "details" in obj:
        if "travel_required" in obj["details"]:
            travel = obj["details"]["travel_required"]
            if travel is None:
                pass  # Keep as None
            elif isinstance(travel, bool):
                pass  # Already boolean
            elif isinstance(travel, str):
                travel_lower = travel.lower().strip()
                if travel_lower in ["yes", "true", "required", "1"]:
                    obj["details"]["travel_required"] = True
                elif travel_lower in ["no", "false", "not required", "0"]:
                    obj["details"]["travel_required"] = False
                else:
                    obj["details"]["travel_required"] = None
            else:
                obj["details"]["travel_required"] = None
    
    # Fix visa_sponsorship to be boolean or None
    if "details" in obj and "visa_sponsorship" in obj["details"]:
        visa = obj["details"]["visa_sponsorship"]
        if not isinstance(visa, (bool, type(None))):
            if isinstance(visa, str):
                visa_lower = visa.lower().strip()
                if visa_lower in ["yes", "true", "available", "1"]:
                    obj["details"]["visa_sponsorship"] = True
                elif visa_lower in ["no", "false", "not available", "0"]:
                    obj["details"]["visa_sponsorship"] = False
                else:
                    obj["details"]["visa_sponsorship"] = None
            else:
                obj["details"]["visa_sponsorship"] = None
    
    # Fix remote and hybrid to be boolean or None
    if "location" in obj:
        for field in ["remote", "hybrid"]:
            if field in obj["location"]:
                value = obj["location"][field]
                if not isinstance(value, (bool, type(None))):
                    if isinstance(value, str):
                        value_lower = value.lower().strip()
                        if value_lower in ["yes", "true", "1"]:
                            obj["location"][field] = True
                        elif value_lower in ["no", "false", "0"]:
                            obj["location"][field] = False
                        else:
                            obj["location"][field] = None
                    else:
                        obj["location"][field] = None

    # Ensure all required nested objects exist with defaults
    obj.setdefault("company", {})
    obj.setdefault("details", {})
    obj.setdefault("location", {})
    obj.setdefault("requirements", {})
    obj.setdefault("compensation", {})
    obj.setdefault("application", {})
    obj.setdefault("responsibilities", [])
    obj.setdefault("qualifications", [])
    obj.setdefault("benefits", [])
    obj.setdefault("growth_opportunities", [])
    obj.setdefault("dedupe", {"keys": []})

    # Fix education level
    if obj.get("requirements", {}).get("education_level"):
        edu_level = obj["requirements"]["education_level"]
        if isinstance(edu_level, str):
            edu_level_lower = edu_level.lower().strip()
            if edu_level_lower in ["high school", "highschool"]:
                obj["requirements"]["education_level"] = "high_school"
            elif edu_level_lower in ["associate", "associates"]:
                obj["requirements"]["education_level"] = "associate"
            elif edu_level_lower in ["bachelor", "bachelors", "bachelor's", "bs", "ba"]:
                obj["requirements"]["education_level"] = "bachelor"
            elif edu_level_lower in ["master", "masters", "master's", "ms", "ma"]:
                obj["requirements"]["education_level"] = "master"
            elif edu_level_lower in ["phd", "ph.d", "doctorate"]:
                obj["requirements"]["education_level"] = "phd"
            elif edu_level_lower in ["none", "no degree"]:
                obj["requirements"]["education_level"] = "none"

    return obj
