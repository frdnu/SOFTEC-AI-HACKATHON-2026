"""Test script for the Opportunity Scanner API"""
import json
from sample_data import SAMPLE_EMAILS, SAMPLE_PROFILE

# Simulate API calls (for testing without server)
from parser import EmailParser
from ranker import RankingEngine
from models import StudentProfile

print("=" * 60)
print("SOFTEC AI HACKATHON 2026 - Opportunity Scanner Test")
print("=" * 60)

# Parse emails
print("\n[1] Parsing emails...")
parser = EmailParser()
opportunities = parser.parse_emails(SAMPLE_EMAILS)

print(f"    Total emails processed: {len(SAMPLE_EMAILS)}")
print(f"    Opportunities detected: {len(opportunities)}")

for opp in opportunities:
    print(f"\n    - {opp.title}")
    print(f"      Type: {opp.opportunity_type.value}")
    print(f"      Deadline: {opp.deadline or 'Not specified'}")
    print(f"      Confidence: {opp.confidence:.1%}")

# Create student profile
print("\n[2] Loading student profile...")
profile = StudentProfile(**SAMPLE_PROFILE)
print(f"    Student: {profile.name}")
print(f"    Degree: {profile.degree} (Semester {profile.semester})")
print(f"    CGPA: {profile.cgpa}")
print(f"    Skills: {', '.join(profile.skills)}")

# Rank opportunities
print("\n[3] Ranking opportunities...")
engine = RankingEngine(profile)
ranked = engine.rank(opportunities)
summary = engine.generate_summary(ranked)

print(f"\n    {summary}")

print("\n" + "=" * 60)
print("RANKED RESULTS (Highest to Lowest Priority)")
print("=" * 60)

for opp in ranked:
    print(f"\n#{opp.rank}: {opp.title}")
    print(f"    Score: {opp.score:.2f} | Urgency: {opp.urgency.upper()}")
    print(f"    Type: {opp.opportunity_type.value}")
    print(f"    Deadline: {opp.deadline or 'Not specified'}")

    print(f"    ✓ Why it matches:")
    for reason in opp.profile_match_reasons[:3]:
        print(f"      - {reason}")

    if opp.missing_requirements:
        print(f"    ⚠ Missing:")
        for req in opp.missing_requirements[:2]:
            print(f"      - {req}")

    print(f"    📋 Action items:")
    for action in opp.action_items[:2]:
        print(f"      - {action}")

print("\n" + "=" * 60)
print("Test complete! API is ready to run.")
print("\nTo start the server: python main.py")
print("=" * 60)
