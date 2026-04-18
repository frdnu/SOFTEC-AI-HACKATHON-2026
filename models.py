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
    """Structured student profile"""
    name: str = ""
    degree: str = ""  # e.g., "BS Computer Science"
    semester: int = 0
    cgpa: float = 0.0
    skills: List[str] = []
    interests: List[str] = []
    preferred_types: List[OpportunityType] = []
    financial_need: bool = False
    location_preference: List[str] = []  # e.g., ["remote", "Lahore", "USA"]
    past_experience: List[str] = []
    graduation_year: int = 0


class ExtractedOpportunity(BaseModel):
    """Opportunity extracted from email"""
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
    confidence: float = 0.0  # How confident we are this is a real opportunity
    raw_content: str


class RankedOpportunity(ExtractedOpportunity):
    """Opportunity with ranking info"""
    rank: int = 0
    score: float = 0.0
    urgency: str = "low"  # low, medium, high, critical
    profile_match_reasons: List[str] = []
    missing_requirements: List[str] = []
    action_items: List[str] = []


class ParseRequest(BaseModel):
    """Request to parse emails"""
    emails: List[dict]  # [{subject, body}]


class RankRequest(BaseModel):
    """Request to rank opportunities"""
    opportunities: List[ExtractedOpportunity]
    student_profile: StudentProfile


class ParseResponse(BaseModel):
    """Response from parsing emails"""
    opportunities: List[ExtractedOpportunity]
    total_emails: int
    detected_opportunities: int


class RankResponse(BaseModel):
    """Response from ranking"""
    ranked_opportunities: List[RankedOpportunity]
    summary: str
