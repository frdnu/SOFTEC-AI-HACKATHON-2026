import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

print("🔑 GROQ_API_KEY loaded:", "YES" if os.environ.get("GROQ_API_KEY") else "NO - .env not loading!")

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def extract_opportunity_data(email_text):
    # Reject obvious jibberish/short inputs immediately
    if len(email_text.strip()) < 50:
        return {"is_opportunity": False}

    system_prompt = """
You are a strict AI classifier for student opportunity emails.

FIRST: Decide if this is a REAL opportunity. It must have ALL of these:
- A clear opportunity type (internship, scholarship, fellowship, competition, workshop, admission)
- Some eligibility or target audience mentioned
- At least one of: deadline, application link, contact info, or benefits

If ANY of these are missing, return EXACTLY: {"is_opportunity": false}
Also return {"is_opportunity": false} for: spam, jibberish, random text, promotions, newsletters, rejection emails, general announcements.

ONLY if it passes all checks, return this exact JSON:
{
    "is_opportunity": true,
    "title": "Clear Name of Opportunity",
    "type": "Internship|Scholarship|Fellowship|Competition|Workshop|Admission",
    "deadline": "Month DD, YYYY or null",
    "days_until_deadline": integer (days from April 18 2026, or 999 if no deadline),
    "requirements": ["req1", "req2", "req3"],
    "next_steps": "Short actionable step with URL or contact if available",
    "why_matters": "One punchy sentence on why this is highly valuable",
    "required_cgpa": float (or 0.0 if not mentioned),
    "required_skills": ["skill1", "skill2"]
}

Return ONLY valid JSON. No markdown, no explanation.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Email text:\n{email_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {"is_opportunity": False}


def calculate_match_score(opportunity_json, student_profile):
    if not opportunity_json.get("is_opportunity"):
        return 0, "LOW"

    score = 40  # Lower base score — must EARN the rest

    # 1. CGPA Check
    req_cgpa = opportunity_json.get('required_cgpa', 0.0)
    if req_cgpa > 0:
        if student_profile.get('cgpa', 0.0) >= req_cgpa:
            score += 20
        else:
            score -= 25  # Hard penalty for not meeting requirement
    else:
        score += 10  # No CGPA requirement = small bonus

    # 2. Opportunity Type Fit
    opp_type = opportunity_json.get('type', '').lower()
    preferred = [t.lower() for t in student_profile.get('opp_types', [])]
    if opp_type in preferred:
        # Higher bonus if it's their TOP preference
        idx = preferred.index(opp_type) if opp_type in preferred else 99
        score += max(5, 20 - idx * 5)

    # 3. Skills Match
    profile_skills = {s.strip().lower() for s in student_profile.get('skills', '').split(',')}
    target_skills = {s.lower() for s in opportunity_json.get('required_skills', [])}
    overlap = profile_skills.intersection(target_skills)
    if overlap:
        score += min(15, len(overlap) * 5)

    # 4. Urgency bonus
    days = opportunity_json.get('days_until_deadline', 999)
    if days <= 7:
        score += 10
        urgency = "HIGH"
    elif days <= 21:
        score += 5
        urgency = "MEDIUM"
    else:
        urgency = "LOW"

    # 5. Completeness bonus — well-structured emails score higher
    has_deadline = opportunity_json.get('deadline') not in [None, "null", ""]
    has_link = "http" in opportunity_json.get('next_steps', '')
    if has_deadline:
        score += 5
    if has_link:
        score += 5

    return min(100, max(0, score)), urgency


def analyze_emails(emails_input, student_profile):
    raw_emails = [e.strip() for e in emails_input.split('---') if e.strip()]
    results = []

    for idx, email_text in enumerate(raw_emails):
        opp_data = extract_opportunity_data(email_text)
        if not opp_data.get("is_opportunity", False):
            continue

        match_score, urgency = calculate_match_score(opp_data, student_profile)

        results.append({
            "rank": 0,
            "title": opp_data.get("title", "Untitled Opportunity"),
            "type": opp_data.get("type", "Unknown"),
            "deadline": opp_data.get("deadline", "No deadline"),
            "urgency": urgency,
            "match_score": match_score,
            "why_matters": opp_data.get("why_matters", "Valuable opportunity for your profile."),
            "requirements": opp_data.get("requirements", []),
            "next_steps": opp_data.get("next_steps", "Check original email for details."),
            "is_opportunity": True,
            "days_until_deadline": opp_data.get("days_until_deadline", 999)
        })

    urgency_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    results.sort(key=lambda x: (-x["match_score"], urgency_order.get(x["urgency"], 2)))

    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results


if __name__ == "__main__":
    test_profile = {
        "cgpa": 3.2,
        "opp_types": ["Internship", "Scholarship"],
        "skills": "Python, Web Dev, C++"
    }
    test_email = """
    We are excited to announce the GDG Summer Internship for 2026. 
    We are looking for students with a CGPA of 3.0 or higher who know Python and Web Dev.
    Deadline is April 25, 2026. Apply at gdg.umt/apply.
    """
    extracted_data = extract_opportunity_data(test_email)
    print(json.dumps(extracted_data, indent=2))
    if extracted_data.get("is_opportunity"):
        score, urgency = calculate_match_score(extracted_data, test_profile)
        print(f"Match Score: {score}% | Urgency: {urgency}")
