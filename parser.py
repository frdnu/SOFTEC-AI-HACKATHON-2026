"""Email parser for extracting opportunity details"""
import re
from typing import List, Optional
from models import ExtractedOpportunity, OpportunityType


class EmailParser:
    """Parses opportunity emails and extracts structured data"""

    TYPE_KEYWORDS = {
        OpportunityType.SCHOLARSHIP: ["scholarship", "financial aid", "grant", "funding", "tuition"],
        OpportunityType.INTERNSHIP: ["internship", "intern", "industrial training", "summer intern"],
        OpportunityType.COMPETITION: ["competition", "contest", "hackathon", "challenge", "award"],
        OpportunityType.FELLOWSHIP: ["fellowship", "research fellow", "visiting fellow"],
        OpportunityType.WORKSHOP: ["workshop", "seminar", "training", "bootcamp", "course"],
        OpportunityType.CONFERENCE: ["conference", "symposium", "colloquium", "presentation"],
        OpportunityType.ADMISSION: ["admission", "apply now", "enrollment", "intake"],
    }

    TYPE_PRIORITY = [
        OpportunityType.SCHOLARSHIP,
        OpportunityType.INTERNSHIP,
        OpportunityType.FELLOWSHIP,
        OpportunityType.COMPETITION,
        OpportunityType.WORKSHOP,
        OpportunityType.CONFERENCE,
        OpportunityType.ADMISSION,
    ]

    # FIX: More deadline patterns including ordinal dates like "30th June 2026"
    DEADLINE_PATTERNS = [
        r"(?:deadline|due date|apply by|closing date|last date)[:\s]+(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})",
        r"(?:deadline|due date|apply by|closing date|last date)[:\s]+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
        r"(?:deadline|due date|apply by|closing date|last date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(?:before|by|until)\s+(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})",
        r"(?:before|by|until)\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
        r"Deadline[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
    ]

    DOCUMENT_PATTERNS = [
        r"(?:resume|cv|curriculum vitae)",
        r"(?:transcript|academic record|mark sheet)",
        r"(?:letter of recommendation|recommendation letter|reference)",
        r"(?:cover letter|motivation letter|statement of purpose)",
        r"(?:portfolio|github|code sample)",
        r"(?:cnic|passport|id card)",
        r"(?:certificate|certification)",
    ]

    # FIX: Stronger spam signals list
    SPAM_SIGNALS = [
        "lottery winner", "claim now", "urgent business proposal",
        "inheritance", "million dollars", "bank details", "wire transfer",
        "nigerian prince", "you have been selected to receive",
        "send your bank", "not a scam",
    ]

    def __init__(self):
        self.opportunities = []

    def parse_emails(self, emails: List[dict]) -> List[ExtractedOpportunity]:
        self.opportunities = []
        for idx, email in enumerate(emails):
            subject = email.get("subject", "")
            body = email.get("body", "")
            content = f"{subject}\n\n{body}"

            # FIX: Reject spam before any further processing
            if self._is_spam(content):
                continue

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

    # FIX: Dedicated spam checker — keeps spam logic separate and easy to extend
    def _is_spam(self, content: str) -> bool:
        content_lower = content.lower()
        return sum(1 for s in self.SPAM_SIGNALS if s in content_lower) >= 1

    def _detect_type(self, content: str) -> Optional[OpportunityType]:
        content_lower = content.lower()
        found_types = []
        for opp_type, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower:
                    found_types.append(opp_type)
                    break
        for opp_type in self.TYPE_PRIORITY:
            if opp_type in found_types:
                return opp_type
        return None

    def _is_opportunity(self, content: str) -> bool:
        content_lower = content.lower()
        positive_signals = [
            "apply", "application", "register", "opportunity", "invite",
            "welcome", "eligible", "qualified", "deadline", "closing",
            "last date", "submit", "open to"
        ]
        # FIX: Raised threshold from 2 -> 3 to cut false positives
        return sum(1 for s in positive_signals if s in content_lower) >= 3

    def _extract_opportunity(self, id: str, subject: str, content: str,
                             detected_type: Optional[OpportunityType]) -> ExtractedOpportunity:
        deadline = self._extract_deadline(content)
        eligibility = self._extract_eligibility(content)
        documents = self._extract_documents(content)
        benefits = self._extract_benefits(content)
        application_link = self._extract_links(content)
        location, is_remote = self._extract_location(content)
        confidence = self._calculate_confidence(content, deadline, eligibility)
        opp_type = detected_type if detected_type else OpportunityType.OTHER
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
        for pattern in self.DEADLINE_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # FIX: Strip ordinal suffixes so ranker can parse dates downstream
                raw = match.group(1).strip()
                cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", raw)
                return cleaned
        return None

    def _extract_eligibility(self, content: str) -> List[str]:
        eligibility = []

        # FIX: Try block extraction under "Eligibility" heading first
        block_match = re.search(
            r"(?:eligibility[^:\n]*|requirements)[:\s]*\n((?:\s*[-•*]?.+\n?){1,10})",
            content, re.IGNORECASE
        )
        if block_match:
            lines = block_match.group(1).strip().split("\n")
            for line in lines:
                line = re.sub(r"^[\s\-•*]+", "", line).strip()
                if line:
                    eligibility.append(line)

        # Fallback to individual patterns
        if not eligibility:
            patterns = [
                r"(?:cgpa|gpa)\s*[:>=\s]*\s*([\d.]+\s*(?:or above|or higher|minimum)?)",
                r"(?:semester|year)\s*[:\s]*\s*(\d+(?:st|nd|rd|th)?(?:\s*(?:or above|to \d+))?)",
                r"(?:must be enrolled in|open to|for)\s+([^\n.]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    eligibility.append(match.group(0).strip())

        return eligibility[:6]

    def _extract_documents(self, content: str) -> List[str]:
        documents = []
        content_lower = content.lower()
        for pattern in self.DOCUMENT_PATTERNS:
            if re.search(pattern, content_lower):
                doc_name = pattern.strip("()[]").split("|")[0].replace("?:", "")
                documents.append(doc_name.title())
        return list(set(documents))

    def _extract_benefits(self, content: str) -> List[str]:
        benefits = []
        patterns = [
            r"(?:offering|provides|includes|benefits|you will)[:\s]+(.+?)(?:\.|\n)",
            r"(?:stipend|salary|payment|amount|funding)\s*[:\s]*\s*[$\d,PKR\s]+",
            r"(?:certificate|certification|letter of completion)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                benefits.append(match.group(0).strip()[:200])
        return benefits[:5]

    def _extract_links(self, content: str) -> Optional[str]:
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        matches = re.findall(url_pattern, content)
        for url in matches:
            if any(kw in url.lower() for kw in ["apply", "register", "form", "portal"]):
                return url
        return matches[0] if matches else None

    def _extract_location(self, content: str) -> tuple:
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
        return (", ".join(locations[:2]) if locations else None), is_remote

    def _extract_organization(self, content: str, subject: str) -> str:
        patterns = [
            r"(?:organized by|hosted by|presented by|from)\s+([A-Z][A-Za-z\s&]+?)(?:\n|$|\.)",
            r"(?:university|institute|foundation|society|lab)[s]?\s+(?:of\s+)?([A-Z][A-Za-z\s]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        if "[" in subject and "]" in subject:
            return subject[subject.index("[") + 1:subject.index("]")].strip()
        return "Unknown"

    def _extract_title(self, subject: str, content: str) -> str:
        title = re.sub(r"^(?:re:|fw:|fwd:|\[.*?\])\s*", "", subject, flags=re.IGNORECASE)
        return title.strip() or "Opportunity"

    def _extract_contact(self, content: str) -> Optional[str]:
        patterns = [
            r"(?:contact|email|reach)\s*(?:us|at)?[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None

    def _calculate_confidence(self, content: str, deadline, eligibility) -> float:
        confidence = 0.5
        if deadline:
            confidence += 0.15
        if eligibility:
            confidence += 0.1 * min(len(eligibility), 3)
        if len(content) > 200:
            confidence += 0.1
        if "http" in content:
            confidence += 0.1
        return min(confidence, 1.0)
