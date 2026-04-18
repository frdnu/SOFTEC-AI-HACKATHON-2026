"""Ranking engine for opportunities based on student profile"""
import re  # FIX: moved imports to top of file
from datetime import datetime  # FIX: moved imports to top of file
from typing import List
from models import StudentProfile, ExtractedOpportunity, RankedOpportunity, OpportunityType


class RankingEngine:
    """Scores and ranks opportunities against student profile"""

    WEIGHTS = {
        "type_match": 0.25,
        "eligibility_match": 0.25,
        "skill_match": 0.15,
        "interest_match": 0.15,
        "urgency": 0.10,
        "completeness": 0.10,
    }

    def __init__(self, student_profile: StudentProfile):
        self.profile = student_profile

    def rank(self, opportunities: List[ExtractedOpportunity]) -> List[RankedOpportunity]:
        ranked = []
        for opp in opportunities:
            ranked_opp = self._evaluate(opp)
            ranked.append(ranked_opp)
        ranked.sort(key=lambda x: x.score, reverse=True)
        for i, opp in enumerate(ranked):
            opp.rank = i + 1
        return ranked

    def _evaluate(self, opp: ExtractedOpportunity) -> RankedOpportunity:
        ranked = RankedOpportunity(**opp.dict())

        type_score = self._score_type_match(opp)
        eligibility_score = self._score_eligibility(opp)
        skill_score = self._score_skills(opp)
        interest_score = self._score_interests(opp)
        urgency_score = self._score_urgency(opp)
        completeness_score = self._score_completeness(opp)

        ranked.score = round(
            type_score * self.WEIGHTS["type_match"] +
            eligibility_score * self.WEIGHTS["eligibility_match"] +
            skill_score * self.WEIGHTS["skill_match"] +
            interest_score * self.WEIGHTS["interest_match"] +
            urgency_score * self.WEIGHTS["urgency"] +
            completeness_score * self.WEIGHTS["completeness"],
            2
        )

        ranked.urgency = self._determine_urgency(opp)
        ranked.profile_match_reasons = self._generate_match_reasons(
            opp, type_score, eligibility_score, skill_score, interest_score
        )
        ranked.missing_requirements = self._find_missing_requirements(opp)
        ranked.action_items = self._generate_action_items(opp)

        return ranked

    def _score_type_match(self, opp: ExtractedOpportunity) -> float:
        if not self.profile.preferred_types:
            return 0.7
        if opp.opportunity_type in self.profile.preferred_types:
            idx = self.profile.preferred_types.index(opp.opportunity_type)
            return max(0.5, 1.0 - (idx * 0.15))
        return 0.3

    def _score_eligibility(self, opp: ExtractedOpportunity) -> float:
        if not opp.eligibility:
            return 0.5

        score = 1.0
        eligibility_text = " ".join(opp.eligibility).lower()

        cgpa_match = re.search(r"(?:cgpa|gpa)[:\s>=]*([\d.]+)", eligibility_text)
        if cgpa_match:
            required_cgpa = float(cgpa_match.group(1))
            if self.profile.cgpa < required_cgpa:
                score -= 0.4
            elif self.profile.cgpa >= required_cgpa + 0.5:
                score += 0.1

        semester_match = re.search(r"(?:semester|year|level)[:\s]*(\d+)", eligibility_text)
        if semester_match:
            required_semester = int(semester_match.group(1))
            if abs(self.profile.semester - required_semester) > 2:
                score -= 0.3

        if self.profile.degree and any(
            deg.lower() in eligibility_text
            for deg in [self.profile.degree.lower(), "student", "undergraduate", "graduate"]
        ):
            score += 0.1

        return max(0.0, min(1.0, score))

    def _score_skills(self, opp: ExtractedOpportunity) -> float:
        if not self.profile.skills:
            return 0.5
        content_lower = opp.raw_content.lower()
        matched = [s for s in self.profile.skills if s.lower() in content_lower]
        if not matched:
            return 0.4
        return min(1.0, 0.5 + len(matched) * 0.15)

    def _score_interests(self, opp: ExtractedOpportunity) -> float:
        if not self.profile.interests:
            return 0.5
        content_lower = opp.raw_content.lower()
        matched = [i for i in self.profile.interests if i.lower() in content_lower]
        if not matched:
            return 0.4
        return min(1.0, 0.5 + len(matched) * 0.15)

    def _score_urgency(self, opp: ExtractedOpportunity) -> float:
        if not opp.deadline:
            return 0.5

        deadline_str = opp.deadline.lower()
        if "today" in deadline_str:
            return 1.0
        if "tomorrow" in deadline_str:
            return 0.95
        if "week" in deadline_str:
            return 0.8
        if "month" in deadline_str:
            return 0.5

        # FIX: Try multiple date formats including both DD/MM and MM/DD
        # Prefer DD/MM (international) over MM/DD to match Pakistani context
        for fmt in ["%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y", "%d/%m/%Y", "%m/%d/%Y"]:
            try:
                deadline_date = datetime.strptime(opp.deadline.strip(), fmt)
                days_left = (deadline_date - datetime.now()).days
                if days_left < 0:
                    return 0.0
                elif days_left <= 3:
                    return 1.0
                elif days_left <= 7:
                    return 0.9
                elif days_left <= 14:
                    return 0.7
                elif days_left <= 30:
                    return 0.5
                else:
                    return 0.3
            except ValueError:
                continue

        return 0.5

    def _score_completeness(self, opp: ExtractedOpportunity) -> float:
        score = 0.0
        if opp.deadline:
            score += 0.2
        if opp.eligibility:
            score += 0.2
        if opp.required_documents:
            score += 0.15
        if opp.application_link:
            score += 0.2
        if opp.benefits:
            score += 0.15
        if opp.organization and opp.organization != "Unknown":
            score += 0.1
        return min(1.0, score)

    def _determine_urgency(self, opp: ExtractedOpportunity) -> str:
        s = self._score_urgency(opp)
        if s >= 0.9:
            return "critical"
        elif s >= 0.7:
            return "high"
        elif s >= 0.5:
            return "medium"
        return "low"

    def _generate_match_reasons(self, opp, type_score, eligibility_score,
                                skill_score, interest_score) -> List[str]:
        reasons = []
        if type_score >= 0.7:
            reasons.append(f"Matches your interest in {opp.opportunity_type.value}")
        if eligibility_score >= 0.7:
            reasons.append("You meet the eligibility criteria")
        if skill_score >= 0.7:
            reasons.append("Aligns with your skills")
        if interest_score >= 0.7:
            reasons.append("Matches your stated interests")
        if opp.is_remote:
            reasons.append("Remote opportunity — flexible location")
        if self.profile.location_preference:
            for loc in self.profile.location_preference:
                if loc.lower() in (opp.location or "").lower():
                    reasons.append(f"Located in your preferred area: {opp.location}")
        if opp.confidence >= 0.8:
            reasons.append("High confidence — well-structured opportunity")
        return reasons if reasons else ["General opportunity match"]

    def _find_missing_requirements(self, opp: ExtractedOpportunity) -> List[str]:
        missing = []
        if opp.required_documents:
            if any(d in opp.required_documents for d in ["Resume", "CV"]):
                missing.append("Prepare/update your resume")
            if "Transcript" in opp.required_documents:
                missing.append("Request academic transcript")
            if "Letter Of Recommendation" in opp.required_documents:
                missing.append("Arrange recommendation letters")

        eligibility_text = " ".join(opp.eligibility).lower()
        cgpa_match = re.search(r"(?:cgpa|gpa)[:\s>=]*([\d.]+)", eligibility_text)
        if cgpa_match:
            required = float(cgpa_match.group(1))
            if self.profile.cgpa < required:
                missing.append(f"CGPA requirement ({required}) exceeds yours ({self.profile.cgpa})")

        return missing

    def _generate_action_items(self, opp: ExtractedOpportunity) -> List[str]:
        actions = []
        if opp.application_link:
            actions.append(f"Visit application portal: {opp.application_link[:60]}")
        elif opp.contact_info:
            actions.append(f"Contact for details: {opp.contact_info}")
        if opp.deadline:
            actions.append(f"Note deadline: {opp.deadline}")
        if opp.required_documents:
            actions.append(f"Gather required documents ({len(opp.required_documents)} items)")
        if opp.eligibility:
            actions.append("Review eligibility criteria carefully")
        actions.append("Prepare application materials")
        return actions[:5]

    def generate_summary(self, ranked: List[RankedOpportunity]) -> str:
        if not ranked:
            return "No opportunities found to rank."

        critical = sum(1 for r in ranked if r.urgency == "critical")
        high = sum(1 for r in ranked if r.urgency == "high")
        top = ranked[0]

        summary = f"Found {len(ranked)} opportunities. "
        summary += f"Top match: '{top.title}' (Score: {top.score}, Urgency: {top.urgency.upper()}). "
        if critical:
            summary += f"⚠️ {critical} opportunity(s) require IMMEDIATE action. "
        if high:
            summary += f"📌 {high} high-priority opportunity(s) this week."
        return summary
