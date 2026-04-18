"""SOFTEC AI Hackathon 2026 - Opportunity Scanner Backend"""
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional  # FIX: use Optional from typing (not X | Y which needs Python 3.10+)

from models import (
    StudentProfile,
    ExtractedOpportunity,
    RankedOpportunity,
    ParseRequest,
    RankRequest,
    ParseResponse,
    RankResponse,
    ScanRequest,      # FIX: import the new unified ScanRequest
    OpportunityType,
)
from parser import EmailParser
from ranker import RankingEngine

app = FastAPI(
    title="SOFTEC AI Hackathon 2026",
    description="Opportunity Scanner - Backend API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

opportunities_store: List[ExtractedOpportunity] = []
student_profile: Optional[StudentProfile] = None  # FIX: was StudentProfile | None (Python 3.10+ only)


@app.get("/")
async def root():
    return {
        "service": "SOFTEC AI Hackathon 2026 - Opportunity Scanner",
        "status": "running",
        "endpoints": ["/api/parse-emails", "/api/rank", "/api/opportunities", "/api/scan", "/api/profile"],
    }


@app.post("/api/parse-emails", response_model=ParseResponse)
async def parse_emails(request: ParseRequest):
    """Parse opportunity emails and extract structured data."""
    global opportunities_store
    if not request.emails:
        raise HTTPException(status_code=400, detail="No emails provided")
    parser = EmailParser()
    opportunities = parser.parse_emails(request.emails)
    opportunities_store = opportunities
    return ParseResponse(
        opportunities=opportunities,
        total_emails=len(request.emails),
        detected_opportunities=len(opportunities),
    )


@app.post("/api/rank", response_model=RankResponse)
async def rank_opportunities(request: RankRequest):
    """Rank opportunities based on student profile."""
    if not request.opportunities:
        raise HTTPException(status_code=400, detail="No opportunities to rank")
    engine = RankingEngine(request.student_profile)
    ranked = engine.rank(request.opportunities)
    summary = engine.generate_summary(ranked)
    return RankResponse(ranked_opportunities=ranked, summary=summary)


@app.get("/api/opportunities", response_model=List[ExtractedOpportunity])
async def get_opportunities():
    """Get all parsed opportunities from last parse request."""
    if not opportunities_store:
        raise HTTPException(status_code=404, detail="No opportunities parsed yet")
    return opportunities_store


@app.post("/api/profile")
async def set_profile(profile: StudentProfile):
    """Set the student profile for ranking."""
    global student_profile
    student_profile = profile
    return {"status": "Profile saved", "profile": profile}


@app.get("/api/profile")
async def get_profile():
    """Get current student profile."""
    if not student_profile:
        raise HTTPException(status_code=404, detail="No profile set")
    return student_profile


# FIX: /api/scan previously took two separate body params (ParseRequest + StudentProfile)
# which FastAPI cannot handle — it caused 422 Unprocessable Entity on every call.
# Now uses a single ScanRequest model that wraps both.
@app.post("/api/scan", response_model=RankResponse)
async def scan_emails(request: ScanRequest):
    """
    Full pipeline: parse emails + rank in one request. Main demo endpoint.

    Body:
    {
        "emails": [{"subject": "...", "body": "..."}],
        "student_profile": { "cgpa": 3.5, "skills": ["Python"], ... }
    }
    """
    if not request.emails:
        raise HTTPException(status_code=400, detail="No emails provided")

    parser = EmailParser()
    opportunities = parser.parse_emails(request.emails)

    if not opportunities:
        raise HTTPException(status_code=404, detail="No real opportunities detected in provided emails")

    engine = RankingEngine(request.student_profile)
    ranked = engine.rank(opportunities)
    summary = engine.generate_summary(ranked)

    return RankResponse(ranked_opportunities=ranked, summary=summary)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
