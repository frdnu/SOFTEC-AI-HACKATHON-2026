"""Data models for opportunity scanner"""
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class OpportunityType(str, Enum):
    SCHOLARSHIP = "scholarship"
    INTERNSHIP = "internship"
    COMPETITION = "competition"
    FELLOWSHIP = "fellowship"
    ADMISSION = "admission"
    WORKSHOP = "workshop"
    CONFERENCE = "conference"
    OTHER = "other"


class StudentProfile(BaseModel):
    name: str = ""
    degree: str = ""
    semester: int = 0
    cgpa: float = 0.0
    skills: List[str] = []
    interests: List[str] = []
    preferred_types: List[OpportunityType] = []
    financial_need: bool = False
    location_preference: List[str] = []
    past_experience: List[str] = []
    graduation_year: int = 0


class ExtractedOpportunity(BaseModel):
    id: str
    source_email_subject: str
    opportunity_type: OpportunityType
    title: str
    organization: str
    deadline: Optional[str] = None
    eligibility: List[str] = []
    required_documents: List[str] = []
    benefits: List[str] = []
    application_link: Optional[str] = None
    contact_info: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool = False
    confidence: float = 0.0
    raw_content: str


class RankedOpportunity(ExtractedOpportunity):
    rank: int = 0
    score: float = 0.0
    urgency: str = "low"
    profile_match_reasons: List[str] = []
    missing_requirements: List[str] = []
    action_items: List[str] = []


class ParseRequest(BaseModel):
    emails: List[dict]


class RankRequest(BaseModel):
    opportunities: List[ExtractedOpportunity]
    student_profile: StudentProfile


# FIX: New unified request body for /api/scan
# FastAPI cannot handle two separate body params — this wraps both into one model
class ScanRequest(BaseModel):
    emails: List[dict]
    student_profile: StudentProfile


class ParseResponse(BaseModel):
    opportunities: List[ExtractedOpportunity]
    total_emails: int
    detected_opportunities: int


class RankResponse(BaseModel):
    ranked_opportunities: List[RankedOpportunity]
    summary: str
