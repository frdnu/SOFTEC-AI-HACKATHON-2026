"""Ranking engine for opportunities based on student profile"""
from typing import List, Dict
from models import StudentProfile, ExtractedOpportunity, RankedOpportunity, OpportunityType


class RankingEngine:
    """Scores and ranks opportunities against student profile"""

    # Weights for scoring
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
        """Rank opportunities based on student profile"""
        ranked = []

        for opp in opportunities:
            ranked_opp = self._evaluate(opp)
            ranked.append(ranked_opp)

        # Sort by score descending
        ranked.sort(key=lambda x: x.score, reverse=True)

        # Assign ranks
        for i, opp in enumerate(ranked):
            opp.rank = i + 1

        return ranked

    def _evaluate(self, opp: ExtractedOpportunity) -> RankedOpportunity:
        """Evaluate a single opportunity"""
        ranked = RankedOpportunity(**opp.dict())

        # Calculate component scores
        type_score = self._score_type_match(opp)
        eligibility_score = self._score_eligibility(opp)
        skill_score = self._score_skills(opp)
        interest_score = self._score_interests(opp)
        urgency_score = self._score_urgency(opp)
        completeness_score = self._score_completeness(opp)

        # Weighted total
        ranked.score = round(
            type_score * self.WEIGHTS["type_match"] +
            eligibility_score * self.WEIGHTS["eligibility_match"] +
            skill_score * self.WEIGHTS["skill_match"] +
            interest_score * self.WEIGHTS["interest_match"] +
            urgency_score * self.WEIGHTS["urgency"] +
            completeness_score * self.WEIGHTS["completeness"],
            2
        )

        # Determine urgency level
        ranked.urgency = self._determine_urgency(opp)

        # Generate reasons
        ranked.profile_match_reasons = self._generate_match_reasons(
            opp, type_score, eligibility_score, skill_score, interest_score
        )

        # Identify missing requirements
        ranked.missing_requirements = self._find_missing_requirements(opp)

        # Generate action items
        ranked.action_items = self._generate_action_items(opp)

        return ranked

    def _score_type_match(self, opp: ExtractedOpportunity) -> float:
        """Score based on preferred opportunity types"""
        if not self.profile.preferred_types:
            return 0.7  # Neutral if no preference stated

        if opp.opportunity_type in self.profile.preferred_types:
            # Higher rank for earlier preferences
            idx = self.profile.preferred_types.index(opp.opportunity_type)
            return 1.0 - (idx * 0.15)

        return 0.3  # Not preferred but still relevant

    def _score_eligibility(self, opp: ExtractedOpportunity) -> float:
        """Score based on eligibility match"""
        if not opp.eligibility:
            return 0.5  # Unknown eligibility

        score = 1.0
        eligibility_text = " ".join(opp.eligibility).lower()

        # Check CGPA requirement
        import re
        cgpa_match = re.search(r"(?:cgpa|gpa)[:\s>=]*([\d.]+)", eligibility_text)
        if cgpa_match:
            required_cgpa = float(cgpa_match.group(1))
            if self.profile.cgpa < required_cgpa:
                score -= 0.4
            elif self.profile.cgpa >= required_cgpa + 0.5:
                score += 0.1

        # Check semester/year requirement
        semester_match = re.search(r"(?:semester|year|level)[:\s]*(\d+)", eligibility_text)
        if semester_match:
            required_semester = int(semester_match.group(1))
            if abs(self.profile.semester - required_semester) > 2:
                score -= 0.3

        # Check degree match
        if self.profile.degree and any(
            deg.lower() in eligibility_text for deg in [self.profile.degree.lower(), "student", "undergraduate", "graduate"]
        ):
            score += 0.1

        return max(0.0, min(1.0, score))

    def _score_skills(self, opp: ExtractedOpportunity) -> float:
        """Score based on skills match"""
        if not self.profile.skills:
            return 0.5  # Neutral if no skills listed

        content_lower = opp.raw_content.lower()
        matched_skills = []

        for skill in self.profile.skills:
            if skill.lower() in content_lower:
                matched_skills.append(skill)

        if not matched_skills:
            return 0.4  # No skill match found

        return min(1.0, 0.5 + (len(matched_skills) * 0.15))

    def _score_interests(self, opp: ExtractedOpportunity) -> float:
        """Score based on interest match"""
        if not self.profile.interests:
            return 0.5

        content_lower = opp.raw_content.lower()
        matched_interests = []

        for interest in self.profile.interests:
            if interest.lower() in content_lower:
                matched_interests.append(interest)

        if not matched_interests:
            return 0.4

        return min(1.0, 0.5 + (len(matched_interests) * 0.15))

    def _score_urgency(self, opp: ExtractedOpportunity) -> float:
        """Score based on deadline urgency"""
        if not opp.deadline:
            return 0.5  # Unknown deadline

        # Try to parse deadline
        from datetime import datetime, timedelta

        deadline_str = opp.deadline.lower()

        # Check for relative deadlines
        if "today" in deadline_str:
            return 1.0
        if "tomorrow" in deadline_str:
            return 0.95
        if "week" in deadline_str:
            return 0.8
        if "month" in deadline_str:
            return 0.5

        # Try to parse date
        try:
            for fmt in ["%B %d, %Y", "%b %d, %Y", "%d/%m/%Y", "%m/%d/%Y"]:
                try:
                    deadline_date = datetime.strptime(opp.deadline, fmt)
                    days_left = (deadline_date - datetime.now()).days

                    if days_left < 0:
                        return 0.0  # Already passed
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
        except Exception:
            pass

        return 0.5

    def _score_completeness(self, opp: ExtractedOpportunity) -> float:
        """Score based on how complete the opportunity info is"""
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
        """Determine urgency level"""
        urgency_score = self._score_urgency(opp)

        if urgency_score >= 0.9:
            return "critical"
        elif urgency_score >= 0.7:
            return "high"
        elif urgency_score >= 0.5:
            return "medium"
        else:
            return "low"

    def _generate_match_reasons(self, opp: ExtractedOpportunity,
                                type_score: float, eligibility_score: float,
                                skill_score: float, interest_score: float) -> List[str]:
        """Generate reasons why this opportunity matches the student"""
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
            reasons.append("Remote opportunity - flexible location")

        if self.profile.location_preference:
            for loc in self.profile.location_preference:
                if loc.lower() in (opp.location or "").lower():
                    reasons.append(f"Located in your preferred area: {opp.location}")

        if opp.confidence >= 0.8:
            reasons.append("High confidence - well-structured opportunity")

        return reasons if reasons else ["General opportunity match"]

    def _find_missing_requirements(self, opp: ExtractedOpportunity) -> List[str]:
        """Find requirements the student may be missing"""
        missing = []

        # Check documents
        if opp.required_documents:
            if "Resume" in opp.required_documents or "CV" in opp.required_documents:
                missing.append("Prepare/update your resume")
            if "Transcript" in opp.required_documents:
                missing.append("Request academic transcript")
            if "Letter of recommendation" in opp.required_documents:
                missing.append("Arrange recommendation letters")

        # Check CGPA
        eligibility_text = " ".join(opp.eligibility).lower()
        import re
        cgpa_match = re.search(r"(?:cgpa|gpa)[:\s>=]*([\d.]+)", eligibility_text)
        if cgpa_match:
            required = float(cgpa_match.group(1))
            if self.profile.cgpa < required:
                missing.append(f"CGPA requirement ({required}) exceeds yours ({self.profile.cgpa})")

        return missing

    def _generate_action_items(self, opp: ExtractedOpportunity) -> List[str]:
        """Generate actionable next steps"""
        actions = []

        if opp.application_link:
            actions.append(f"Visit application portal: {opp.application_link[:50]}...")
        elif opp.contact_info:
            actions.append(f"Contact for details: {opp.contact_info}")

        if opp.deadline:
            actions.append(f"Note deadline: {opp.deadline}")

        if opp.required_documents:
            actions.append(f"Gather required documents: {len(opp.required_documents)} items")

        if opp.eligibility:
            actions.append("Review eligibility criteria carefully")

        actions.append("Prepare application materials")

        return actions[:5]

    def generate_summary(self, ranked: List[RankedOpportunity]) -> str:
        """Generate a summary of the ranking results"""
        if not ranked:
            return "No opportunities found to rank."

        critical = sum(1 for r in ranked if r.urgency == "critical")
        high = sum(1 for r in ranked if r.urgency == "high")

        top_score = ranked[0].score if ranked else 0

        summary = f"Found {len(ranked)} opportunities. "
        summary += f"Top match: '{ranked[0].title}' (Score: {top_score}). "

        if critical > 0:
            summary += f"⚠️ {critical} opportunity(s) require immediate action. "
        if high > 0:
            summary += f"📌 {high} high-priority opportunity(s) this week."

        return summary
