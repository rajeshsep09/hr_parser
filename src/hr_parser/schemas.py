from pydantic import BaseModel, EmailStr, conint, confloat, constr
from typing import List, Optional, Dict, Literal, Union

class Meta(BaseModel):
    canonical_version: str = "1.0"
    parser_version: str = "hrx-0.1.0"
    ingested_at: Optional[str] = None
    source_file: Optional[str] = None
    source_mime: Optional[str] = None
    parsing_confidence: confloat(ge=0, le=1) = 0.0
    language: Optional[str] = "en"
    hash_sha256: Optional[str] = None

class Links(BaseModel):
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = []

class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[constr(min_length=2, max_length=2)] = None

class Identity(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    emails: List[EmailStr] = []
    phones: List[str] = []
    links: Links = Links()
    location: Location = Location()

class Skill(BaseModel):
    name: str
    group: Optional[str] = None
    proficiency: Optional[Literal["beginner","intermediate","advanced","expert"]] = None
    years: Optional[confloat(ge=0, le=50)] = None

class Experience(BaseModel):
    title_raw: Optional[str] = None
    title_norm: Optional[str] = None
    company: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[constr(pattern=r"^\d{4}(-\d{2})?$")] = None
    end_date: Optional[constr(pattern=r"^\d{4}(-\d{2})?$")] = None
    current: Optional[bool] = None
    achievements: List[str] = []
    tech: List[str] = []

class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[conint(ge=1950, le=2100)] = None
    end_year: Optional[conint(ge=1950, le=2100)] = None
    score: Optional[Dict[str, float]] = None

class Preferences(BaseModel):
    remote: Optional[bool] = None
    relocation: Optional[Union[str, bool]] = None  # Allow both string and boolean
    notice_period_days: Optional[conint(ge=0, le=365)] = None
    salary: Optional[Dict[str, Union[str, float]]] = None  # Allow both string and float values

class WorkAuth(BaseModel):
    country: Optional[str] = None
    status: Optional[str] = None

class CanonicalResume(BaseModel):
    meta: Meta
    identity: Identity
    summary: Optional[str] = None
    skills: List[Skill] = []
    experience: List[Experience] = []
    education: List[Education] = []
    projects: List[Dict] = []
    certifications: List[Dict] = []
    preferences: Preferences = Preferences()
    work_auth: WorkAuth = WorkAuth()
    dedupe: Dict[str, List[str]] = {"keys": []}