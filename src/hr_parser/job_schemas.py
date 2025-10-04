from pydantic import BaseModel, EmailStr, conint, confloat, constr
from typing import List, Optional, Dict, Literal, Union

class JobMeta(BaseModel):
    canonical_version: str = "1.0"
    parser_version: str = "hrx-0.1.0"
    ingested_at: Optional[str] = None
    source_file: Optional[str] = None
    source_mime: Optional[str] = None
    parsing_confidence: confloat(ge=0, le=1) = 0.0
    language: Optional[str] = "en"
    hash_sha256: Optional[str] = None

class JobLocation(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[constr(min_length=2, max_length=2)] = None
    remote: Optional[bool] = None
    hybrid: Optional[bool] = None

class JobCompany(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None  # e.g., "1-10", "11-50", "51-200", "201-1000", "1000+"
    website: Optional[str] = None
    description: Optional[str] = None

class JobRequirements(BaseModel):
    experience_years: Optional[conint(ge=0, le=50)] = None
    education_level: Optional[Literal["high_school", "associate", "bachelor", "master", "phd", "none"]] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    certifications: List[str] = []
    languages: List[str] = []

class JobCompensation(BaseModel):
    salary_min: Optional[confloat(ge=0)] = None
    salary_max: Optional[confloat(ge=0)] = None
    currency: Optional[str] = None
    equity: Optional[bool] = None
    benefits: List[str] = []

class JobDetails(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    employment_type: Optional[Literal["full_time", "part_time", "contract", "internship", "temporary"]] = None
    work_schedule: Optional[str] = None
    travel_required: Optional[bool] = None
    visa_sponsorship: Optional[bool] = None

class JobApplication(BaseModel):
    contact_email: Optional[EmailStr] = None
    application_url: Optional[str] = None
    application_deadline: Optional[constr(pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$")] = None
    application_method: Optional[str] = None  # e.g., "email", "website", "linkedin"

class CanonicalJobDescription(BaseModel):
    meta: JobMeta
    company: JobCompany
    details: JobDetails
    location: JobLocation
    requirements: JobRequirements
    compensation: JobCompensation
    application: JobApplication
    description: Optional[str] = None
    responsibilities: List[str] = []
    qualifications: List[str] = []
    benefits: List[str] = []
    culture: Optional[str] = None
    growth_opportunities: List[str] = []
    dedupe: Dict[str, List[str]] = {"keys": []}
