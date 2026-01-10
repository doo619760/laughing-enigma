"""Deadline model for California court case deadlines."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class DeadlineType(Enum):
    """Types of legal deadlines."""
    # Response deadlines
    ANSWER_DUE = "answer_due"
    OPPOSITION_DUE = "opposition_due"
    REPLY_DUE = "reply_due"
    DISCOVERY_RESPONSE_DUE = "discovery_response"
    OBJECTION_DUE = "objection_due"

    # Filing deadlines
    MOTION_FILING = "motion_filing"
    MSJ_FILING = "msj_filing"  # 75 days before trial (CCP 437c)
    MOTION_IN_LIMINE_FILING = "mil_filing"
    JURY_INSTRUCTIONS_DUE = "jury_instructions"
    EXHIBIT_LIST_DUE = "exhibit_list"
    WITNESS_LIST_DUE = "witness_list"
    EXPERT_DESIGNATION_DUE = "expert_designation"

    # Discovery deadlines
    FACT_DISCOVERY_CUTOFF = "fact_discovery_cutoff"
    EXPERT_DISCOVERY_CUTOFF = "expert_discovery_cutoff"
    DEPOSITION_DEADLINE = "deposition_deadline"

    # Court-ordered deadlines
    CMO_DEADLINE = "cmo_deadline"
    COURT_ORDERED = "court_ordered"

    # Hearing-related
    HEARING_PAPERS_DUE = "hearing_papers"
    NOTICE_OF_HEARING = "notice_of_hearing"
    MEET_AND_CONFER = "meet_and_confer"

    # Service deadlines
    SERVICE_DEADLINE = "service_deadline"
    PROOF_OF_SERVICE_DUE = "proof_of_service"

    # Statute-based
    STATUTE_OF_LIMITATIONS = "sol"
    CLAIM_FILING_DEADLINE = "claim_deadline"

    # Other
    CMC_STATEMENT_DUE = "cmc_statement"
    FSC_DOCUMENTS_DUE = "fsc_documents"
    SETTLEMENT_DEMAND = "settlement_demand"
    CUSTOM = "custom"


class DeadlineStatus(Enum):
    """Status of a deadline."""
    PENDING = "pending"
    UPCOMING = "upcoming"  # Within warning threshold
    URGENT = "urgent"  # Within urgent threshold
    COMPLETED = "completed"
    MISSED = "missed"
    EXTENDED = "extended"
    WAIVED = "waived"
    NOT_APPLICABLE = "not_applicable"


class DeadlinePriority(Enum):
    """Priority level of a deadline."""
    CRITICAL = "critical"  # Court-imposed, cannot miss
    HIGH = "high"  # Important but may have remedy
    MEDIUM = "medium"  # Standard deadline
    LOW = "low"  # Internal/soft deadline


@dataclass
class DeadlineExtension:
    """Record of a deadline extension."""
    original_date: date
    new_date: date
    extension_date: date
    reason: str
    stipulated: bool = False
    court_ordered: bool = False
    order_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'original_date': self.original_date.isoformat(),
            'new_date': self.new_date.isoformat(),
            'extension_date': self.extension_date.isoformat(),
            'reason': self.reason,
            'stipulated': self.stipulated,
            'court_ordered': self.court_ordered,
            'order_id': self.order_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DeadlineExtension':
        return cls(
            original_date=date.fromisoformat(data['original_date']),
            new_date=date.fromisoformat(data['new_date']),
            extension_date=date.fromisoformat(data['extension_date']),
            reason=data['reason'],
            stipulated=data.get('stipulated', False),
            court_ordered=data.get('court_ordered', False),
            order_id=data.get('order_id'),
        )


@dataclass
class Deadline:
    """
    Represents a deadline in a California court case.

    Tracks due dates, calculates deadlines based on California
    Code of Civil Procedure, and manages extensions.
    """
    title: str
    deadline_type: DeadlineType
    due_date: date
    case_id: str

    # Optional fields
    id: str = field(default_factory=lambda: str(uuid4()))
    status: DeadlineStatus = DeadlineStatus.PENDING
    priority: DeadlinePriority = DeadlinePriority.MEDIUM

    # Calculation basis
    trigger_date: Optional[date] = None  # Date that triggered this deadline
    trigger_document_id: Optional[str] = None
    trigger_event_id: Optional[str] = None
    base_days: Optional[int] = None  # Base number of days
    service_extension_days: int = 0  # Additional days for service method
    court_days: bool = False  # If True, count only court days

    # Related items
    related_event_id: Optional[str] = None  # Hearing this deadline relates to
    response_to_document_id: Optional[str] = None
    resulting_document_id: Optional[str] = None  # Document filed to meet deadline

    # Party information
    responsible_party_id: Optional[str] = None
    responsible_party_name: Optional[str] = None

    # Extensions
    extensions: List[DeadlineExtension] = field(default_factory=list)
    original_due_date: Optional[date] = None

    # Completion tracking
    completed_date: Optional[date] = None
    completed_document_id: Optional[str] = None

    # Notifications
    warning_days: int = 7  # Days before to show warning
    urgent_days: int = 3  # Days before to show urgent
    reminder_days: List[int] = field(default_factory=lambda: [14, 7, 3, 1])
    reminders_sent: List[date] = field(default_factory=list)

    # Legal basis
    ccp_section: Optional[str] = None  # California Code of Civil Procedure section
    crc_rule: Optional[str] = None  # California Rules of Court rule
    local_rule: Optional[str] = None  # Local court rule

    # Metadata
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.original_due_date is None:
            self.original_due_date = self.due_date
        self._update_status()

    def _update_status(self) -> None:
        """Update status based on current date."""
        if self.status in (DeadlineStatus.COMPLETED, DeadlineStatus.WAIVED,
                           DeadlineStatus.NOT_APPLICABLE, DeadlineStatus.MISSED):
            return

        days_remaining = self.days_remaining()

        if days_remaining < 0:
            self.status = DeadlineStatus.MISSED
        elif days_remaining <= self.urgent_days:
            self.status = DeadlineStatus.URGENT
        elif days_remaining <= self.warning_days:
            self.status = DeadlineStatus.UPCOMING
        else:
            self.status = DeadlineStatus.PENDING

    def days_remaining(self) -> int:
        """Get number of days until deadline."""
        return (self.due_date - date.today()).days

    def is_past_due(self) -> bool:
        """Check if deadline has passed."""
        return self.due_date < date.today()

    def is_due_today(self) -> bool:
        """Check if deadline is today."""
        return self.due_date == date.today()

    def is_urgent(self) -> bool:
        """Check if deadline is within urgent threshold."""
        return 0 <= self.days_remaining() <= self.urgent_days

    def is_warning(self) -> bool:
        """Check if deadline is within warning threshold."""
        return self.urgent_days < self.days_remaining() <= self.warning_days

    def extend(self, new_date: date, reason: str,
               stipulated: bool = False, court_ordered: bool = False,
               order_id: Optional[str] = None) -> None:
        """Extend the deadline to a new date."""
        extension = DeadlineExtension(
            original_date=self.due_date,
            new_date=new_date,
            extension_date=date.today(),
            reason=reason,
            stipulated=stipulated,
            court_ordered=court_ordered,
            order_id=order_id
        )
        self.extensions.append(extension)
        self.due_date = new_date
        self.status = DeadlineStatus.EXTENDED
        self.updated_at = datetime.now()
        self._update_status()

    def complete(self, completed_date: Optional[date] = None,
                 document_id: Optional[str] = None) -> None:
        """Mark deadline as completed."""
        self.status = DeadlineStatus.COMPLETED
        self.completed_date = completed_date or date.today()
        self.completed_document_id = document_id
        self.updated_at = datetime.now()

    def waive(self, reason: str = "") -> None:
        """Waive this deadline."""
        self.status = DeadlineStatus.WAIVED
        if reason:
            self.notes += f"\nWaived: {reason}"
        self.updated_at = datetime.now()

    def mark_not_applicable(self, reason: str = "") -> None:
        """Mark deadline as not applicable."""
        self.status = DeadlineStatus.NOT_APPLICABLE
        if reason:
            self.notes += f"\nN/A: {reason}"
        self.updated_at = datetime.now()

    def get_total_extension_days(self) -> int:
        """Get total days extended from original due date."""
        if self.original_due_date:
            return (self.due_date - self.original_due_date).days
        return 0

    def get_status_display(self) -> str:
        """Get human-readable status string."""
        days = self.days_remaining()
        if self.status == DeadlineStatus.COMPLETED:
            return "Completed"
        elif self.status == DeadlineStatus.MISSED:
            return f"MISSED by {abs(days)} days"
        elif self.status == DeadlineStatus.WAIVED:
            return "Waived"
        elif self.status == DeadlineStatus.URGENT:
            return f"URGENT - Due in {days} days"
        elif self.status == DeadlineStatus.UPCOMING:
            return f"Upcoming - Due in {days} days"
        elif days == 0:
            return "DUE TODAY"
        elif days == 1:
            return "Due tomorrow"
        else:
            return f"Due in {days} days"

    def to_dict(self) -> dict:
        """Convert deadline to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'deadline_type': self.deadline_type.value,
            'due_date': self.due_date.isoformat(),
            'case_id': self.case_id,
            'status': self.status.value,
            'priority': self.priority.value,
            'trigger_date': self.trigger_date.isoformat() if self.trigger_date else None,
            'trigger_document_id': self.trigger_document_id,
            'trigger_event_id': self.trigger_event_id,
            'base_days': self.base_days,
            'service_extension_days': self.service_extension_days,
            'court_days': self.court_days,
            'related_event_id': self.related_event_id,
            'response_to_document_id': self.response_to_document_id,
            'resulting_document_id': self.resulting_document_id,
            'responsible_party_id': self.responsible_party_id,
            'responsible_party_name': self.responsible_party_name,
            'extensions': [e.to_dict() for e in self.extensions],
            'original_due_date': self.original_due_date.isoformat() if self.original_due_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'completed_document_id': self.completed_document_id,
            'warning_days': self.warning_days,
            'urgent_days': self.urgent_days,
            'reminder_days': self.reminder_days,
            'reminders_sent': [d.isoformat() for d in self.reminders_sent],
            'ccp_section': self.ccp_section,
            'crc_rule': self.crc_rule,
            'local_rule': self.local_rule,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Deadline':
        """Create Deadline from dictionary."""
        extensions = [DeadlineExtension.from_dict(e) for e in data.get('extensions', [])]
        deadline = cls(
            id=data.get('id', str(uuid4())),
            title=data['title'],
            deadline_type=DeadlineType(data['deadline_type']),
            due_date=date.fromisoformat(data['due_date']),
            case_id=data['case_id'],
            status=DeadlineStatus(data.get('status', 'pending')),
            priority=DeadlinePriority(data.get('priority', 'medium')),
            trigger_date=date.fromisoformat(data['trigger_date']) if data.get('trigger_date') else None,
            trigger_document_id=data.get('trigger_document_id'),
            trigger_event_id=data.get('trigger_event_id'),
            base_days=data.get('base_days'),
            service_extension_days=data.get('service_extension_days', 0),
            court_days=data.get('court_days', False),
            related_event_id=data.get('related_event_id'),
            response_to_document_id=data.get('response_to_document_id'),
            resulting_document_id=data.get('resulting_document_id'),
            responsible_party_id=data.get('responsible_party_id'),
            responsible_party_name=data.get('responsible_party_name'),
            extensions=extensions,
            original_due_date=date.fromisoformat(data['original_due_date']) if data.get('original_due_date') else None,
            completed_date=date.fromisoformat(data['completed_date']) if data.get('completed_date') else None,
            completed_document_id=data.get('completed_document_id'),
            warning_days=data.get('warning_days', 7),
            urgent_days=data.get('urgent_days', 3),
            reminder_days=data.get('reminder_days', [14, 7, 3, 1]),
            reminders_sent=[date.fromisoformat(d) for d in data.get('reminders_sent', [])],
            ccp_section=data.get('ccp_section'),
            crc_rule=data.get('crc_rule'),
            local_rule=data.get('local_rule'),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
        )
        return deadline

    def __repr__(self) -> str:
        return f"Deadline({self.title}, {self.due_date.isoformat()})"
