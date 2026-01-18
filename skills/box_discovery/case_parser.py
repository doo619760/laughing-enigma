"""
Case File Parser

Parses legal case files and extracts structured information for discovery.
Supports PDF, DOCX, TXT, and RTF formats.
"""

import os
import re
import json
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    """Types of legal documents"""
    COMPLAINT = "complaint"
    ANSWER = "answer"
    MOTION = "motion"
    BRIEF = "brief"
    DEPOSITION = "deposition"
    INTERROGATORY = "interrogatory"
    REQUEST_FOR_PRODUCTION = "request_for_production"
    REQUEST_FOR_ADMISSION = "request_for_admission"
    CORRESPONDENCE = "correspondence"
    CONTRACT = "contract"
    EXHIBIT = "exhibit"
    DISCOVERY_RESPONSE = "discovery_response"
    COURT_ORDER = "court_order"
    SUBPOENA = "subpoena"
    AFFIDAVIT = "affidavit"
    UNKNOWN = "unknown"


@dataclass
class Party:
    """Represents a party in the case"""
    name: str
    role: str  # plaintiff, defendant, witness, etc.
    description: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    contact_info: Optional[Dict[str, str]] = None


@dataclass
class KeyDate:
    """Represents a significant date in the case"""
    date: str
    description: str
    source_document: Optional[str] = None
    significance: Optional[str] = None


@dataclass
class KeyFact:
    """Represents a key fact from the case"""
    fact: str
    source: str
    disputed: bool = False
    supporting_evidence: List[str] = field(default_factory=list)
    category: Optional[str] = None  # damages, liability, causation, etc.


@dataclass
class LegalClaim:
    """Represents a legal claim or cause of action"""
    claim_type: str
    description: str
    elements: List[str] = field(default_factory=list)
    supporting_facts: List[str] = field(default_factory=list)
    damages_sought: Optional[str] = None


@dataclass
class Document:
    """Represents a parsed document"""
    filename: str
    file_id: str
    document_type: DocumentType
    title: Optional[str] = None
    date: Optional[str] = None
    content: str = ""
    summary: Optional[str] = None
    key_excerpts: List[str] = field(default_factory=list)
    mentioned_parties: List[str] = field(default_factory=list)
    mentioned_dates: List[str] = field(default_factory=list)


@dataclass
class CaseProfile:
    """Complete profile of a legal case"""
    case_number: Optional[str] = None
    case_title: Optional[str] = None
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    case_type: Optional[str] = None  # civil, criminal, family, etc.

    # Parties
    plaintiffs: List[Party] = field(default_factory=list)
    defendants: List[Party] = field(default_factory=list)
    other_parties: List[Party] = field(default_factory=list)

    # Timeline
    key_dates: List[KeyDate] = field(default_factory=list)
    filing_date: Optional[str] = None
    incident_date: Optional[str] = None

    # Substance
    key_facts: List[KeyFact] = field(default_factory=list)
    disputed_facts: List[KeyFact] = field(default_factory=list)
    legal_claims: List[LegalClaim] = field(default_factory=list)
    defenses: List[str] = field(default_factory=list)

    # Documents
    documents: List[Document] = field(default_factory=list)

    # Discovery Status
    discovery_requests_received: List[Dict] = field(default_factory=list)
    discovery_requests_sent: List[Dict] = field(default_factory=list)

    # Analysis
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    key_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CaseProfile':
        """Create CaseProfile from dictionary"""
        # Handle nested dataclasses
        if 'plaintiffs' in data:
            data['plaintiffs'] = [Party(**p) if isinstance(p, dict) else p for p in data['plaintiffs']]
        if 'defendants' in data:
            data['defendants'] = [Party(**p) if isinstance(p, dict) else p for p in data['defendants']]
        if 'other_parties' in data:
            data['other_parties'] = [Party(**p) if isinstance(p, dict) else p for p in data['other_parties']]
        if 'key_dates' in data:
            data['key_dates'] = [KeyDate(**d) if isinstance(d, dict) else d for d in data['key_dates']]
        if 'key_facts' in data:
            data['key_facts'] = [KeyFact(**f) if isinstance(f, dict) else f for f in data['key_facts']]
        if 'disputed_facts' in data:
            data['disputed_facts'] = [KeyFact(**f) if isinstance(f, dict) else f for f in data['disputed_facts']]
        if 'legal_claims' in data:
            data['legal_claims'] = [LegalClaim(**c) if isinstance(c, dict) else c for c in data['legal_claims']]
        if 'documents' in data:
            docs = []
            for d in data['documents']:
                if isinstance(d, dict):
                    d['document_type'] = DocumentType(d['document_type']) if isinstance(d['document_type'], str) else d['document_type']
                    docs.append(Document(**d))
                else:
                    docs.append(d)
            data['documents'] = docs
        return cls(**data)


class CaseFileParser:
    """
    Parser for legal case files.

    Extracts structured information from various document formats
    to build a comprehensive case profile for discovery purposes.
    """

    # Patterns for identifying document types
    DOCUMENT_TYPE_PATTERNS = {
        DocumentType.COMPLAINT: [
            r'complaint\s+for', r'plaintiff.*complains', r'causes?\s+of\s+action',
            r'comes\s+now.*plaintiff', r'wherefore.*plaintiff.*prays'
        ],
        DocumentType.ANSWER: [
            r'answer\s+to\s+complaint', r'defendant.*answers', r'affirmative\s+defense',
            r'comes\s+now.*defendant'
        ],
        DocumentType.MOTION: [
            r'motion\s+(to|for)', r'moves?\s+this\s+court', r'memorandum\s+in\s+support'
        ],
        DocumentType.DEPOSITION: [
            r'deposition\s+of', r'examination\s+of', r'direct\s+examination',
            r'cross[-\s]examination', r'q\.\s+.*\n\s*a\.'
        ],
        DocumentType.INTERROGATORY: [
            r'interrogator(y|ies)', r'answers?\s+to\s+interrogator',
            r'propounded\s+by'
        ],
        DocumentType.REQUEST_FOR_PRODUCTION: [
            r'request(s)?\s+for\s+production', r'document\s+request',
            r'produce.*document'
        ],
        DocumentType.REQUEST_FOR_ADMISSION: [
            r'request(s)?\s+for\s+admission', r'admit\s+or\s+deny'
        ],
        DocumentType.CONTRACT: [
            r'agreement\s+between', r'terms\s+and\s+conditions',
            r'whereas.*now\s+therefore', r'in\s+witness\s+whereof'
        ],
        DocumentType.COURT_ORDER: [
            r'order\s+of\s+the\s+court', r'it\s+is\s+(so\s+)?ordered',
            r'the\s+court.*orders'
        ],
        DocumentType.SUBPOENA: [
            r'subpoena', r'you\s+are\s+commanded', r'witness\s+fee'
        ],
        DocumentType.AFFIDAVIT: [
            r'affidavit\s+of', r'sworn\s+statement', r'under\s+penalty\s+of\s+perjury',
            r'subscribed\s+and\s+sworn'
        ]
    }

    # Patterns for extracting case information
    CASE_NUMBER_PATTERNS = [
        r'case\s*(?:no\.?|number)[:\s]*([A-Z0-9\-:]+)',
        r'civil\s*(?:action\s*)?(?:no\.?|number)[:\s]*([A-Z0-9\-:]+)',
        r'docket\s*(?:no\.?|number)[:\s]*([A-Z0-9\-:]+)',
        r'(?:cv|ca|civ)[:\-\s]*(\d+[\-:]\d+[\-:]?\w*)',
    ]

    COURT_PATTERNS = [
        r'(?:in\s+the\s+)?((?:united\s+states\s+)?(?:district|circuit|superior|supreme|county)\s+court[^,\n]+)',
        r'(?:in\s+the\s+)?(court\s+of\s+(?:common\s+pleas|appeals?)[^,\n]+)',
    ]

    PARTY_PATTERNS = {
        'plaintiff': [
            r'([A-Z][A-Za-z\s,\.]+),?\s*(?:plaintiff|petitioner)',
            r'plaintiff[:\s]+([A-Z][A-Za-z\s,\.]+)',
        ],
        'defendant': [
            r'([A-Z][A-Za-z\s,\.]+),?\s*(?:defendant|respondent)',
            r'defendant[:\s]+([A-Z][A-Za-z\s,\.]+)',
        ]
    }

    DATE_PATTERNS = [
        r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',
        r'\b(\d{1,2}-\d{1,2}-\d{2,4})\b',
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
        r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
    ]

    MONEY_PATTERNS = [
        r'\$[\d,]+(?:\.\d{2})?',
        r'[\d,]+\s+dollars?',
        r'damages?\s+(?:of|in\s+the\s+amount\s+of)\s+\$?[\d,]+',
    ]

    def __init__(self):
        """Initialize the parser"""
        self.case_profile = CaseProfile()

    def parse_document(self, content: str, filename: str, file_id: str) -> Document:
        """
        Parse a single document and extract relevant information.

        Args:
            content: Text content of the document
            filename: Name of the file
            file_id: Box file ID

        Returns:
            Parsed Document object
        """
        doc_type = self._identify_document_type(content, filename)

        # Extract basic information
        title = self._extract_title(content, filename)
        date = self._extract_document_date(content)
        mentioned_parties = self._extract_mentioned_names(content)
        mentioned_dates = self._extract_dates(content)

        # Extract key excerpts based on document type
        key_excerpts = self._extract_key_excerpts(content, doc_type)

        # Generate summary
        summary = self._generate_document_summary(content, doc_type)

        return Document(
            filename=filename,
            file_id=file_id,
            document_type=doc_type,
            title=title,
            date=date,
            content=content,
            summary=summary,
            key_excerpts=key_excerpts,
            mentioned_parties=mentioned_parties,
            mentioned_dates=mentioned_dates
        )

    def _identify_document_type(self, content: str, filename: str) -> DocumentType:
        """Identify the type of legal document"""
        content_lower = content.lower()
        filename_lower = filename.lower()

        # Check filename first
        filename_hints = {
            'complaint': DocumentType.COMPLAINT,
            'answer': DocumentType.ANSWER,
            'motion': DocumentType.MOTION,
            'deposition': DocumentType.DEPOSITION,
            'interrogator': DocumentType.INTERROGATORY,
            'rfa': DocumentType.REQUEST_FOR_ADMISSION,
            'rfp': DocumentType.REQUEST_FOR_PRODUCTION,
            'contract': DocumentType.CONTRACT,
            'agreement': DocumentType.CONTRACT,
            'order': DocumentType.COURT_ORDER,
            'subpoena': DocumentType.SUBPOENA,
            'affidavit': DocumentType.AFFIDAVIT,
            'exhibit': DocumentType.EXHIBIT,
        }

        for hint, doc_type in filename_hints.items():
            if hint in filename_lower:
                return doc_type

        # Check content patterns
        for doc_type, patterns in self.DOCUMENT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return doc_type

        return DocumentType.UNKNOWN

    def _extract_title(self, content: str, filename: str) -> str:
        """Extract document title from content or filename"""
        # Try to find title in first few lines
        lines = content.strip().split('\n')[:10]

        for line in lines:
            line = line.strip()
            # Skip blank lines and very short lines
            if len(line) < 5:
                continue
            # Title is often in caps or has specific format
            if line.isupper() and len(line) > 10:
                return line
            if re.match(r'^(MOTION|COMPLAINT|ANSWER|ORDER|BRIEF|MEMORANDUM)', line, re.I):
                return line

        # Fall back to filename without extension
        return os.path.splitext(filename)[0]

    def _extract_document_date(self, content: str) -> Optional[str]:
        """Extract the primary date from a document"""
        # Look for dated patterns at the start of document
        date_intro_patterns = [
            r'dated[:\s]+(' + self.DATE_PATTERNS[2][2:-2] + ')',
            r'date[:\s]+(' + self.DATE_PATTERNS[0][2:-2] + ')',
        ]

        for pattern in date_intro_patterns:
            match = re.search(pattern, content[:2000], re.I)
            if match:
                return match.group(1)

        # Find any date near the beginning
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, content[:2000], re.I)
            if match:
                return match.group(1)

        return None

    def _extract_dates(self, content: str) -> List[str]:
        """Extract all dates mentioned in content"""
        dates = []
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, content, re.I)
            dates.extend(matches)
        return list(set(dates))[:20]  # Limit to 20 unique dates

    def _extract_mentioned_names(self, content: str) -> List[str]:
        """Extract proper names mentioned in the document"""
        # Pattern for names (basic heuristic)
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        matches = re.findall(name_pattern, content)

        # Filter out common phrases
        common_phrases = {
            'United States', 'State of', 'County of', 'City of',
            'District Court', 'Superior Court', 'Supreme Court'
        }

        names = []
        for match in matches:
            if not any(phrase in match for phrase in common_phrases):
                names.append(match)

        return list(set(names))[:30]  # Limit to 30 unique names

    def _extract_key_excerpts(self, content: str, doc_type: DocumentType) -> List[str]:
        """Extract key excerpts based on document type"""
        excerpts = []

        if doc_type == DocumentType.COMPLAINT:
            # Extract causes of action
            coa_pattern = r'(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)\s+(?:CAUSE\s+OF\s+ACTION|CLAIM)[:\s]*([^\n]+(?:\n[^\n]+){0,5})'
            matches = re.findall(coa_pattern, content, re.I)
            excerpts.extend(matches[:5])

            # Extract prayer for relief
            prayer_pattern = r'(?:WHEREFORE|PRAYER\s+FOR\s+RELIEF)[,:\s]*([^\n]+(?:\n[^\n]+){0,10})'
            match = re.search(prayer_pattern, content, re.I)
            if match:
                excerpts.append(match.group(1))

        elif doc_type == DocumentType.ANSWER:
            # Extract affirmative defenses
            defense_pattern = r'(?:FIRST|SECOND|THIRD|FOURTH|FIFTH)\s+(?:AFFIRMATIVE\s+)?DEFENSE[:\s]*([^\n]+(?:\n[^\n]+){0,3})'
            matches = re.findall(defense_pattern, content, re.I)
            excerpts.extend(matches[:5])

        elif doc_type == DocumentType.DEPOSITION:
            # Extract Q&A exchanges
            qa_pattern = r'Q\.\s+([^\n]+)\n\s*A\.\s+([^\n]+)'
            matches = re.findall(qa_pattern, content)
            for q, a in matches[:10]:
                excerpts.append(f"Q: {q}\nA: {a}")

        elif doc_type in [DocumentType.INTERROGATORY, DocumentType.REQUEST_FOR_PRODUCTION]:
            # Extract numbered requests
            request_pattern = r'(?:INTERROGATORY|REQUEST)\s+(?:NO\.?\s*)?(\d+)[:\s]*([^\n]+(?:\n[^\n]+){0,5})'
            matches = re.findall(request_pattern, content, re.I)
            for num, text in matches[:10]:
                excerpts.append(f"{num}. {text.strip()}")

        # Extract any section with damages or amounts
        money_context_pattern = r'[^\n]*(?:\$[\d,]+|\d+\s+dollars?)[^\n]*'
        money_matches = re.findall(money_context_pattern, content, re.I)
        excerpts.extend(money_matches[:5])

        return excerpts[:15]  # Limit total excerpts

    def _generate_document_summary(self, content: str, doc_type: DocumentType) -> str:
        """Generate a brief summary of the document"""
        # Extract first substantive paragraph
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 100]

        if paragraphs:
            first_para = paragraphs[0][:500]
            return f"[{doc_type.value.upper()}] {first_para}..."

        return f"[{doc_type.value.upper()}] Document with {len(content)} characters"

    def parse_case_file(self, documents: List[Tuple[str, str, str]]) -> CaseProfile:
        """
        Parse multiple documents to build a complete case profile.

        Args:
            documents: List of (content, filename, file_id) tuples

        Returns:
            Comprehensive CaseProfile
        """
        self.case_profile = CaseProfile()

        # Parse each document
        for content, filename, file_id in documents:
            doc = self.parse_document(content, filename, file_id)
            self.case_profile.documents.append(doc)

            # Extract case-level information from complaint
            if doc.document_type == DocumentType.COMPLAINT:
                self._extract_case_info_from_complaint(content)

            # Extract parties from all documents
            self._update_parties(content)

            # Extract key dates
            for date in doc.mentioned_dates:
                self.case_profile.key_dates.append(KeyDate(
                    date=date,
                    description=f"Date mentioned in {filename}",
                    source_document=filename
                ))

        # Deduplicate and organize
        self._deduplicate_case_profile()

        return self.case_profile

    def _extract_case_info_from_complaint(self, content: str):
        """Extract case information from complaint document"""
        # Case number
        for pattern in self.CASE_NUMBER_PATTERNS:
            match = re.search(pattern, content, re.I)
            if match:
                self.case_profile.case_number = match.group(1)
                break

        # Court
        for pattern in self.COURT_PATTERNS:
            match = re.search(pattern, content, re.I)
            if match:
                self.case_profile.court = match.group(1).strip()
                break

        # Extract claims
        claim_patterns = [
            r'(?:FIRST|SECOND|THIRD|FOURTH|FIFTH)\s+(?:CAUSE\s+OF\s+ACTION|CLAIM)\s*[:\-]?\s*\n?\s*([^\n]+)',
            r'(?:Count|Claim)\s+(?:I|II|III|IV|V|VI|VII|VIII|IX|X)[:\s]+([^\n]+)',
        ]

        for pattern in claim_patterns:
            matches = re.findall(pattern, content, re.I)
            for claim_text in matches:
                self.case_profile.legal_claims.append(LegalClaim(
                    claim_type=claim_text.strip(),
                    description=claim_text.strip()
                ))

    def _update_parties(self, content: str):
        """Extract and update party information"""
        for role, patterns in self.PARTY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.I)
                for name in matches:
                    name = name.strip().rstrip(',.')
                    if len(name) < 100:  # Sanity check
                        party = Party(name=name, role=role)
                        if role == 'plaintiff' and party not in self.case_profile.plaintiffs:
                            self.case_profile.plaintiffs.append(party)
                        elif role == 'defendant' and party not in self.case_profile.defendants:
                            self.case_profile.defendants.append(party)

    def _deduplicate_case_profile(self):
        """Remove duplicates from case profile"""
        # Deduplicate dates
        seen_dates = set()
        unique_dates = []
        for kd in self.case_profile.key_dates:
            if kd.date not in seen_dates:
                seen_dates.add(kd.date)
                unique_dates.append(kd)
        self.case_profile.key_dates = unique_dates[:20]

        # Deduplicate parties by name
        seen_plaintiffs = set()
        unique_plaintiffs = []
        for p in self.case_profile.plaintiffs:
            if p.name.lower() not in seen_plaintiffs:
                seen_plaintiffs.add(p.name.lower())
                unique_plaintiffs.append(p)
        self.case_profile.plaintiffs = unique_plaintiffs

        seen_defendants = set()
        unique_defendants = []
        for d in self.case_profile.defendants:
            if d.name.lower() not in seen_defendants:
                seen_defendants.add(d.name.lower())
                unique_defendants.append(d)
        self.case_profile.defendants = unique_defendants

    def extract_key_facts(self, content: str, source: str) -> List[KeyFact]:
        """
        Extract key facts from document content.

        Args:
            content: Document text
            source: Source document name

        Returns:
            List of KeyFact objects
        """
        facts = []

        # Look for factual allegations
        allegation_patterns = [
            r'(?:plaintiff|defendant)\s+(?:alleges?|states?|contends?|asserts?)\s+(?:that\s+)?([^.]+\.)',
            r'on\s+(?:or\s+about\s+)?(?:' + self.DATE_PATTERNS[2][2:-2] + r')[,\s]+([^.]+\.)',
            r'(?:the\s+)?(?:evidence|facts?|record)\s+(?:shows?|demonstrates?|establishes?)\s+(?:that\s+)?([^.]+\.)',
        ]

        for pattern in allegation_patterns:
            matches = re.findall(pattern, content, re.I)
            for match in matches[:10]:
                if isinstance(match, tuple):
                    fact_text = match[-1]
                else:
                    fact_text = match
                if len(fact_text) > 20:
                    facts.append(KeyFact(
                        fact=fact_text.strip(),
                        source=source,
                        disputed=False
                    ))

        return facts

    def get_discovery_context(self) -> Dict[str, Any]:
        """
        Get case context formatted for discovery drafting.

        Returns:
            Dictionary with organized case information for discovery
        """
        return {
            "case_info": {
                "case_number": self.case_profile.case_number,
                "case_title": self.case_profile.case_title,
                "court": self.case_profile.court,
                "case_type": self.case_profile.case_type,
            },
            "parties": {
                "plaintiffs": [p.name for p in self.case_profile.plaintiffs],
                "defendants": [d.name for d in self.case_profile.defendants],
            },
            "claims": [
                {"type": c.claim_type, "description": c.description}
                for c in self.case_profile.legal_claims
            ],
            "key_dates": [
                {"date": d.date, "description": d.description}
                for d in self.case_profile.key_dates
            ],
            "key_facts": [
                {"fact": f.fact, "source": f.source, "disputed": f.disputed}
                for f in self.case_profile.key_facts
            ],
            "documents": [
                {
                    "filename": d.filename,
                    "type": d.document_type.value,
                    "summary": d.summary,
                    "key_excerpts": d.key_excerpts[:5]
                }
                for d in self.case_profile.documents
            ]
        }
