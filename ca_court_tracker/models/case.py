"""Case model for California court cases."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class CaseType(Enum):
    """Types of California civil cases."""
    UNLIMITED_CIVIL = "unlimited_civil"  # Over $35,000
    LIMITED_CIVIL = "limited_civil"  # $35,000 or less
    SMALL_CLAIMS = "small_claims"  # $12,500 or less
    UNLAWFUL_DETAINER = "unlawful_detainer"
    FAMILY_LAW = "family_law"
    PROBATE = "probate"
    PERSONAL_INJURY = "personal_injury"
    EMPLOYMENT = "employment"
    CONTRACT = "contract"
    REAL_PROPERTY = "real_property"
    CONSTRUCTION_DEFECT = "construction_defect"
    COMPLEX_CIVIL = "complex_civil"
    OTHER = "other"


class CaseStatus(Enum):
    """Status of a court case."""
    PENDING = "pending"
    ACTIVE = "active"
    AT_ISSUE = "at_issue"
    TRIAL_SET = "trial_set"
    STAYED = "stayed"
    DISMISSED = "dismissed"
    SETTLED = "settled"
    JUDGMENT_ENTERED = "judgment_entered"
    APPEAL_PENDING = "appeal_pending"
    CLOSED = "closed"


@dataclass
class Case:
    """
    Represents a California court case.

    Tracks all essential information for case management including
    parties, case type, court information, and key dates.
    """
    case_number: str
    case_name: str
    case_type: CaseType
    court_name: str
    county: str

    # Optional fields
    id: str = field(default_factory=lambda: str(uuid4()))
    status: CaseStatus = CaseStatus.PENDING
    department: Optional[str] = None
    judge_name: Optional[str] = None

    # Key dates
    filing_date: Optional[date] = None
    trial_date: Optional[date] = None
    cmc_date: Optional[date] = None  # Case Management Conference
    fsc_date: Optional[date] = None  # Final Status Conference
    msj_hearing_date: Optional[date] = None  # Motion for Summary Judgment

    # Classification
    is_complex: bool = False
    is_expedited: bool = False

    # Tracking
    parties: List[str] = field(default_factory=list)  # Party IDs
    documents: List[str] = field(default_factory=list)  # Document IDs
    events: List[str] = field(default_factory=list)  # Event IDs
    deadlines: List[str] = field(default_factory=list)  # Deadline IDs

    # Metadata
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate case data after initialization."""
        if not self.case_number:
            raise ValueError("Case number is required")
        if not self.case_name:
            raise ValueError("Case name is required")

    def update_status(self, new_status: CaseStatus) -> None:
        """Update case status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.now()

    def add_party(self, party_id: str) -> None:
        """Add a party to the case."""
        if party_id not in self.parties:
            self.parties.append(party_id)
            self.updated_at = datetime.now()

    def add_document(self, document_id: str) -> None:
        """Add a document to the case."""
        if document_id not in self.documents:
            self.documents.append(document_id)
            self.updated_at = datetime.now()

    def add_event(self, event_id: str) -> None:
        """Add an event to the case."""
        if event_id not in self.events:
            self.events.append(event_id)
            self.updated_at = datetime.now()

    def add_deadline(self, deadline_id: str) -> None:
        """Add a deadline to the case."""
        if deadline_id not in self.deadlines:
            self.deadlines.append(deadline_id)
            self.updated_at = datetime.now()

    def get_days_since_filing(self) -> Optional[int]:
        """Calculate days since case was filed."""
        if self.filing_date:
            return (date.today() - self.filing_date).days
        return None

    def get_days_until_trial(self) -> Optional[int]:
        """Calculate days until trial date."""
        if self.trial_date:
            return (self.trial_date - date.today()).days
        return None

    def to_dict(self) -> dict:
        """Convert case to dictionary for serialization."""
        return {
            'id': self.id,
            'case_number': self.case_number,
            'case_name': self.case_name,
            'case_type': self.case_type.value,
            'court_name': self.court_name,
            'county': self.county,
            'status': self.status.value,
            'department': self.department,
            'judge_name': self.judge_name,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'trial_date': self.trial_date.isoformat() if self.trial_date else None,
            'cmc_date': self.cmc_date.isoformat() if self.cmc_date else None,
            'fsc_date': self.fsc_date.isoformat() if self.fsc_date else None,
            'msj_hearing_date': self.msj_hearing_date.isoformat() if self.msj_hearing_date else None,
            'is_complex': self.is_complex,
            'is_expedited': self.is_expedited,
            'parties': self.parties,
            'documents': self.documents,
            'events': self.events,
            'deadlines': self.deadlines,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Case':
        """Create Case from dictionary."""
        return cls(
            id=data.get('id', str(uuid4())),
            case_number=data['case_number'],
            case_name=data['case_name'],
            case_type=CaseType(data['case_type']),
            court_name=data['court_name'],
            county=data['county'],
            status=CaseStatus(data.get('status', 'pending')),
            department=data.get('department'),
            judge_name=data.get('judge_name'),
            filing_date=date.fromisoformat(data['filing_date']) if data.get('filing_date') else None,
            trial_date=date.fromisoformat(data['trial_date']) if data.get('trial_date') else None,
            cmc_date=date.fromisoformat(data['cmc_date']) if data.get('cmc_date') else None,
            fsc_date=date.fromisoformat(data['fsc_date']) if data.get('fsc_date') else None,
            msj_hearing_date=date.fromisoformat(data['msj_hearing_date']) if data.get('msj_hearing_date') else None,
            is_complex=data.get('is_complex', False),
            is_expedited=data.get('is_expedited', False),
            parties=data.get('parties', []),
            documents=data.get('documents', []),
            events=data.get('events', []),
            deadlines=data.get('deadlines', []),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
        )

    def __repr__(self) -> str:
        return f"Case({self.case_number}: {self.case_name})"
