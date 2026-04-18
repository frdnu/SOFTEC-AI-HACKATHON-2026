"""Email parser for extracting opportunity details"""
import re
from datetime import datetime
from typing import List, Optional
from models import ExtractedOpportunity, OpportunityType


class EmailParser:
    """Parses opportunity emails and extracts structured data"""

    # Keywords to identify opportunity types
    TYPE_KEYWORDS = {
        OpportunityType.SCHOLARSHIP: ["scholarship", "financial aid", "grant", "funding", "tuition"],
        OpportunityType.INTERNSHIP: ["internship", "intern", "industrial training", "summer intern"],
        OpportunityType.COMPETITION: ["competition", "contest", "hackathon", "challenge", "award"],
        OpportunityType.FELLOWSHIP: ["fellowship", "research fellow", "visiting fellow"],
        OpportunityType.ADMISSION: ["admission", "apply now", "enrollment", "intake", "register"],
        OpportunityType.WORKSHOP: ["workshop", "seminar", "training", "bootcamp", "course"],
        OpportunityType.CONFERENCE: ["conference", "symposium", "colloquium", "presentation"],
    }

    # Deadline patterns
    DEADLINE_PATTERNS = [
        r"(?:deadline|due date|apply by|closing date)[:\s]+([A-Za-z0-9,]+)",
        r"(?:before|by|until)\s+([A-Za-z0-9,\s]+?)(?:\.|$|\n)",
        r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ]

    # Document patterns
    DOCUMENT_PATTERNS = [
        r"(?:resume|cv|curriculum vitae)",
        r"(?:transcript|academic record|mark sheet)",
        r"(?:letter of recommendation|recommendation letter|reference)",
        r"(?:cover letter|motivation letter|statement of purpose)",
        r"(?:portfolio|github|code sample)",
        r"(?:cnic|passport|id card)",
        r"(?:certificate|certification)",
    ]

    def __init__(self):
        self.opportunities = []

    def parse_emails(self, emails: List[dict]) -> List[ExtractedOpportunity]:
        """Parse a list of emails and extract opportunities"""
        self.opportunities = []

        for idx, email in enumerate(emails):
            subject = email.get("subject", "")
            body = email.get("body", "")
            content = f"{subject}\n\n{body}"

            opp_type = self._detect_type(content)
            if opp_type or self._is_opportunity(content):
                opportunity = self._extract_opportunity(
                    id=f"opp_{idx}",
                    subject=subject,
                    content=content,
                    detected_type=opp_type
                )
                self.opportunities.append(opportunity)

        return self.opportunities

    def _detect_type(self, content: str) -> Optional[OpportunityType]:
        """Detect the type of opportunity"""
        content_lower = content.lower()

        for opp_type, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return opp_type
        return None

    def _is_opportunity(self, content: str) -> bool:
        """Check if content contains a genuine opportunity"""
        content_lower = content.lower()

        # Positive signals
        positive_signals = [
            "apply", "application", "register", "opportunity", "invite",
            "welcome", "eligible", "qualified", "selected", "winner",
            "deadline", "closing", "last date", "submit"
        ]

        # Negative signals (likely spam or not opportunity)
        negative_signals = [
            "unsubscribe", "spam", "lottery winner", "claim now",
            "urgent business proposal", "inheritance", "million dollars"
        ]

        positive_count = sum(1 for signal in positive_signals if signal in content_lower)
        negative_count = sum(1 for signal in negative_signals if signal in content_lower)

        return positive_count >= 2 and negative_count == 0

    def _extract_opportunity(self, id: str, subject: str, content: str,
                            detected_type: Optional[OpportunityType]) -> ExtractedOpportunity:
        """Extract structured data from email content"""

        # Extract deadline
        deadline = self._extract_deadline(content)

        # Extract eligibility
        eligibility = self._extract_eligibility(content)

        # Extract required documents
        documents = self._extract_documents(content)

        # Extract benefits
        benefits = self._extract_benefits(content)

        # Extract links
        application_link = self._extract_links(content)

        # Extract location
        location, is_remote = self._extract_location(content)

        # Calculate confidence
        confidence = self._calculate_confidence(content, deadline, eligibility)

        # Determine type
        opp_type = detected_type if detected_type else OpportunityType.OTHER

        # Extract organization
        organization = self._extract_organization(content, subject)

        return ExtractedOpportunity(
            id=id,
            source_email_subject=subject,
            opportunity_type=opp_type,
            title=self._extract_title(subject, content),
            organization=organization,
            deadline=deadline,
            eligibility=eligibility,
            required_documents=documents,
            benefits=benefits,
            application_link=application_link,
            contact_info=self._extract_contact(content),
            location=location,
            is_remote=is_remote,
            confidence=confidence,
            raw_content=content
        )

    def _extract_deadline(self, content: str) -> Optional[str]:
        """Extract deadline from content"""
        for pattern in self.DEADLINE_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_eligibility(self, content: str) -> List[str]:
        """Extract eligibility criteria"""
        eligibility = []
        patterns = [
            r"(?:eligible for|eligibility|requirements|must be|candidates must)[:\s]+(.+?)(?:\n\n|\n{2}|$)",
            r"(?:for|open to)\s+(?:students|undergraduates|graduates)[^.\n]+",
            r"(?:cgpa|gpa|grade)\s*[:>=\s]*\s*([\d.]+)",
            r"(?:semester|year|level)\s*[:\s]*\s*(\d+(?:st|nd|rd|th)?|\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                eligibility.append(match.group(0).strip())

        return eligibility[:5]  # Limit to 5 criteria

    def _extract_documents(self, content: str) -> List[str]:
        """Extract required documents"""
        documents = []
        content_lower = content.lower()

        for pattern in self.DOCUMENT_PATTERNS:
            if re.search(pattern, content_lower):
                # Normalize document name
                doc_name = pattern.strip("()[]").split("|")[0].replace("?:", "")
                documents.append(doc_name.title())

        return list(set(documents))

    def _extract_benefits(self, content: str) -> List[str]:
        """Extract benefits/what's offered"""
        benefits = []
        patterns = [
            r"(?:offering|provides|includes|benefits|you will)[:\s]+(.+?)(?:\.|\n)",
            r"(?:stipend|salary|payment|amount|funding)\s*[:\s]*\s*[$\d,]+",
            r"(?:certificate|certification|letter of completion)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                benefits.append(match.group(0).strip()[:200])

        return benefits[:5]

    def _extract_links(self, content: str) -> Optional[str]:
        """Extract application/contact links"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        matches = re.findall(url_pattern, content)

        # Filter for application-related links
        for url in matches:
            if any(kw in url.lower() for kw in ["apply", "register", "form", "portal"]):
                return url

        return matches[0] if matches else None

    def _extract_location(self, content: str) -> tuple:
        """Extract location and remote status"""
        is_remote = bool(re.search(r"\b(remote|virtual|online|zoom)\b", content, re.IGNORECASE))

        locations = []
        city_patterns = [
            r"\b(Lahore|Karachi|Islamabad|Faisalabad|Peshawar|Multan)\b",
            r"\b(New York|London|Boston|San Francisco|Seattle|Remote)\b",
        ]

        for pattern in city_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                locations.append(match.group(1))

        location = ", ".join(locations[:2]) if locations else None
        return location, is_remote

    def _extract_organization(self, content: str, subject: str) -> str:
        """Extract organization name"""
        # Look for common org patterns
        patterns = [
            r"(?:organized by|hosted by|presented by|from)\s+([A-Z][A-Za-z\s&]+?)(?:\n|$|\.)",
            r"(?:university|institute|foundation|society|lab)[s]?\s+(?:of\s+)?([A-Z][A-Za-z\s]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Extract from subject if possible
        if "[" in subject and "]" in subject:
            return subject[subject.index("[")+1:subject.index("]")].strip()

        return "Unknown"

    def _extract_title(self, subject: str, content: str) -> str:
        """Extract opportunity title"""
        # Clean subject line
        title = re.sub(r"^(?:re:|fw:|fwd:|\[.*?\])\s*", "", subject, flags=re.IGNORECASE)
        return title.strip() or "Opportunity"

    def _extract_contact(self, content: str) -> Optional[str]:
        """Extract contact information"""
        patterns = [
            r"(?:contact|email|reach)\s*(?:us|at)?[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _calculate_confidence(self, content: str, deadline: Optional[str],
                             eligibility: List[str]) -> float:
        """Calculate confidence score for this being a real opportunity"""
        confidence = 0.5  # Base confidence

        # Has deadline
        if deadline:
            confidence += 0.15

        # Has eligibility criteria
        if eligibility:
            confidence += 0.1 * len(eligibility)

        # Has structured content
        if len(content) > 200:
            confidence += 0.1

        # Has link
        if "http" in content:
            confidence += 0.1

        return min(confidence, 1.0)
