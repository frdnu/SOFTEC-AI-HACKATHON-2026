import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True) # hamesha new key jo bhi doon vou use kro bhai

print("🔑 GROQ_API_KEY loaded:", "YES" if os.environ.get("GROQ_API_KEY") else "NO - .env not loading!")
print("Key starts with:", os.environ.get("GROQ_API_KEY")[:10] + "..." if os.environ.get("GROQ_API_KEY") else "None")

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def extract_opportunity_data(email_text):
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
            model="llama-3.1-8b-instant", # removed deprecated model to new and improved model
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

    score = 50  # Base baseline score for being a valid opportunity
    
    # 1. CGPA Hard Check
    req_cgpa = opportunity_json.get('required_cgpa', 0.0)
    if student_profile.get('cgpa', 0.0) >= req_cgpa:
        score += 15
    else:
        score -= 30
        
    # 2. Opportunity Type Fit
    if opportunity_json.get('type') in student_profile.get('opp_types', []):
        score += 15
        
    # 3. Skills Match
    profile_skills = {s.strip().lower() for s in student_profile.get('skills', '').split(',')}
    target_skills = {s.lower() for s in opportunity_json.get('required_skills', [])}
    overlap = profile_skills.intersection(target_skills)
    if overlap:
        score += min(10, len(overlap) * 5)
        
    # 4. Urgency Calculation
    days = opportunity_json.get('days_until_deadline', 999)
    if days <= 7:
        score += 10
        urgency = "HIGH"
    elif days <= 21:
        score += 5
        urgency = "MEDIUM"
    else:
        urgency = "LOW"
        
    final_score = min(100, max(0, score))
    return final_score, urgency


# ==================== MAIN TEST ====================
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
    
    print("Extracting...")
    extracted_data = extract_opportunity_data(test_email)
    print(json.dumps(extracted_data, indent=2))
    
    if extracted_data.get("is_opportunity"):
        print("\nScoring...")
        score, urgency = calculate_match_score(extracted_data, test_profile)
        print(f"Match Score: {score}% | Urgency: {urgency}")