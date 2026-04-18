import json
import os
from openai import OpenAI

# pip install openai
# Make sure your terminal has the API key exported: 
# export OPENAI_API_KEY="sk-..."
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def extract_opportunity_data(email_text):
    """
    Step 1: The AI Classifier & Extractor.
    Takes raw email text, filters out the BS, and returns clean JSON.
    """
    system_prompt = """
    You are a ruthless AI data extractor. Read the provided email.
    If it is NOT a genuine academic/professional opportunity (e.g., spam, fluff, rejection, newsletter), 
    return EXACTLY: {"is_opportunity": false}
    
    If it IS an opportunity, extract the details and return JSON matching this exact structure:
    {
        "is_opportunity": true,
        "title": "Clear Name of Opportunity",
        "type": "Internship|Scholarship|Fellowship|Competition|Research|Admission",
        "deadline": "Month DD, YYYY",
        "days_until_deadline": integer (estimate based on today being April 18, 2026, or 999 if none),
        "requirements": ["req1", "req2", "req3"],
        "next_steps": "Short actionable step with URL or contact if available",
        "why_matters": "One punchy sentence on why this is highly valuable",
        "required_cgpa": float (or 0.0 if not mentioned),
        "required_skills": ["skill1", "skill2"]
    }
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Fast, cheap, perfect for hackathons
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Email text:\n{email_text}"}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1 # Keep it strictly deterministic, no creative hallucinations
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {"is_opportunity": False}


def calculate_match_score(opportunity_json, student_profile):
    """
    Step 2: The Deterministic Scoring Engine.
    Takes the JSON from Step 1 and the Student Profile, outputs a score out of 100.
    """
    if not opportunity_json.get("is_opportunity"):
        return 0, "LOW"

    score = 50  # Base baseline score for being a valid opportunity
    
    # --- 1. CGPA Hard Check ---
    req_cgpa = opportunity_json.get('required_cgpa', 0.0)
    if student_profile.get('cgpa', 0.0) >= req_cgpa:
        score += 15
    else:
        score -= 30  # Heavy penalty for not meeting hard academic requirements
        
    # --- 2. Opportunity Type Fit ---
    if opportunity_json.get('type') in student_profile.get('opp_types', []):
        score += 15
        
    # --- 3. Skills Match ---
    # Convert both lists to lowercase sets to find the overlap
    profile_skills = {s.strip().lower() for s in student_profile.get('skills', '').split(',')}
    target_skills = {s.lower() for s in opportunity_json.get('required_skills', [])}
    
    overlap = profile_skills.intersection(target_skills)
    if overlap:
        score += min(10, len(overlap) * 5) # +5 points per matching skill (max 10 points)
        
    # --- 4. Urgency Calculation ---
    days = opportunity_json.get('days_until_deadline', 999)
    if days <= 7:
        score += 10
        urgency = "HIGH"
    elif days <= 21:
        score += 5
        urgency = "MEDIUM"
    else:
        urgency = "LOW"
        
    # Cap the score between 0 and 100
    final_score = min(100, max(0, score))
    
    return final_score, urgency


def analyze_emails(emails_input, student_profile):
    """
    Main orchestrator: parses emails, extracts opportunities, scores them,
    and returns ranked results with evidence.
    """
    # Split emails by separator
    raw_emails = [e.strip() for e in emails_input.split('---') if e.strip()]

    results = []

    for idx, email_text in enumerate(raw_emails):
        # Step 1: Extract opportunity data
        opp_data = extract_opportunity_data(email_text)

        if not opp_data.get("is_opportunity", False):
            continue  # Skip non-opportunities

        # Step 2: Calculate match score
        match_score, urgency = calculate_match_score(opp_data, student_profile)

        # Build result entry
        results.append({
            "rank": 0,  # Will be set after sorting
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

    # Sort by match_score descending, then by urgency (HIGH > MEDIUM > LOW)
    urgency_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    results.sort(key=lambda x: (-x["match_score"], urgency_order.get(x["urgency"], 2)))

    # Assign ranks
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results