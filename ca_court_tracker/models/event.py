"""Court event model for California court cases."""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class EventType(Enum):
    """Types of court events."""
    # Conferences
    CASE_MANAGEMENT_CONFERENCE = "cmc"
    FINAL_STATUS_CONFERENCE = "fsc"
    SETTLEMENT_CONFERENCE = "settlement_conference"
    STATUS_CONFERENCE = "status_conference"
    TRIAL_SETTING_CONFERENCE = "trial_setting"
    OSC_HEARING = "osc"  # Order to Show Cause

    # Hearings
    MOTION_HEARING = "motion_hearing"
    DEMURRER_HEARING = "demurrer_hearing"
    MSJ_HEARING = "msj_hearing"
    MSA_HEARING = "msa_hearing"
    EX_PARTE_HEARING = "ex_parte_hearing"
    DISCOVERY_MOTION_HEARING = "discovery_motion"

    # Trial
    TRIAL = "trial"
    JURY_TRIAL = "jury_trial"
    BENCH_TRIAL = "bench_trial"
    TRIAL_CONTINUED = "trial_continued"

    # Other proceedings
    DEPOSITION = "deposition"
    MEDIATION = "mediation"
    ARBITRATION = "arbitration"
    EXPERT_DISCOVERY_CUTOFF = "expert_cutoff"
    FACT_DISCOVERY_CUTOFF = "fact_cutoff"

    # Administrative
    FILING_DEADLINE = "filing_deadline"
    SERVICE_DEADLINE = "service_deadline"
    APPEARANCE = "appearance"
    JUDGMENT_HEARING = "judgment_hearing"

    # ROA Events
    ROA_ENTRY = "roa_entry"
    MINUTE_ORDER = "minute_order"
    COURT_ORDER = "court_order"

    OTHER = "other"


class EventStatus(Enum):
    """Status of a court event."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CONTINUED = "continued"
    VACATED = "vacated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OFF_CALENDAR = "off_calendar"


class EventResult(Enum):
    """Result of a completed court event."""
    GRANTED = "granted"
    DENIED = "denied"
    GRANTED_IN_PART = "granted_in_part"
    TAKEN_UNDER_SUBMISSION = "under_submission"
    CONTINUED = "continued"
    SETTLED = "settled"
    DISMISSED = "dismissed"
    DEFAULT_ENTERED = "default_entered"
    JUDGMENT_ENTERED = "judgment_entered"
    OFF_CALENDAR = "off_calendar"
    NO_APPEARANCE = "no_appearance"
    HELD = "held"
    OTHER = "other"


@dataclass
class CourtEvent:
    """
    Represents a court event or calendar entry in a California case.

    Tracks hearings, conferences, deadlines, and other court proceedings
    from the court calendar and Register of Actions.
    """
    title: str
    event_type: EventType
    event_date: date
    case_id: str

    # Optional fields
    id: str = field(default_factory=lambda: str(uuid4()))
    status: EventStatus = EventStatus.SCHEDULED

    # Time and location
    event_time: Optional[time] = None
    end_time: Optional[time] = None
    department: Optional[str] = None
    courtroom: Optional[str] = None
    court_address: Optional[str] = None

    # Court details
    judge_name: Optional[str] = None
    clerk_name: Optional[str] = None

    # Associated documents
    related_document_ids: List[str] = field(default_factory=list)
    minute_order_id: Optional[str] = None

    # Parties required
    parties_required: List[str] = field(default_factory=list)

    # Deadlines associated with this event
    associated_deadline_ids: List[str] = field(default_factory=list)

    # Result tracking
    result: Optional[EventResult] = None
    ruling_summary: Optional[str] = None
    next_event_id: Optional[str] = None  # If continued

    # Register of Actions
    roa_entry_number: Optional[str] = None
    roa_description: Optional[str] = None

    # Reminders
    reminder_days_before: List[int] = field(default_factory=lambda: [7, 3, 1])
    reminders_sent: List[date] = field(default_factory=list)

    # Metadata
    notes: str = ""
    is_mandatory: bool = False
    requires_appearance: bool = True
    allow_telephonic: bool = False
    allow_remote: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_past(self) -> bool:
        """Check if the event date has passed."""
        return self.event_date < date.today()

    def is_today(self) -> bool:
        """Check if the event is today."""
        return self.event_date == date.today()

    def days_until(self) -> int:
        """Get days until the event (negative if past)."""
        return (self.event_date - date.today()).days

    def is_hearing(self) -> bool:
        """Check if this event is a hearing type."""
        hearing_types = {
            EventType.MOTION_HEARING,
            EventType.DEMURRER_HEARING,
            EventType.MSJ_HEARING,
            EventType.MSA_HEARING,
            EventType.EX_PARTE_HEARING,
            EventType.DISCOVERY_MOTION_HEARING,
            EventType.OSC_HEARING,
        }
        return self.event_type in hearing_types

    def is_conference(self) -> bool:
        """Check if this event is a conference type."""
        conference_types = {
            EventType.CASE_MANAGEMENT_CONFERENCE,
            EventType.FINAL_STATUS_CONFERENCE,
            EventType.SETTLEMENT_CONFERENCE,
            EventType.STATUS_CONFERENCE,
            EventType.TRIAL_SETTING_CONFERENCE,
        }
        return self.event_type in conference_types

    def is_trial(self) -> bool:
        """Check if this event is a trial type."""
        trial_types = {
            EventType.TRIAL,
            EventType.JURY_TRIAL,
            EventType.BENCH_TRIAL,
        }
        return self.event_type in trial_types

    def continue_to(self, new_date: date, reason: Optional[str] = None) -> None:
        """Continue this event to a new date."""
        self.status = EventStatus.CONTINUED
        self.result = EventResult.CONTINUED
        if reason:
            self.notes += f"\nContinued to {new_date.isoformat()}: {reason}"
        self.updated_at = datetime.now()

    def complete(self, result: EventResult, ruling_summary: Optional[str] = None) -> None:
        """Mark event as completed with result."""
        self.status = EventStatus.COMPLETED
        self.result = result
        self.ruling_summary = ruling_summary
        self.updated_at = datetime.now()

    def vacate(self, reason: Optional[str] = None) -> None:
        """Vacate this event."""
        self.status = EventStatus.VACATED
        if reason:
            self.notes += f"\nVacated: {reason}"
        self.updated_at = datetime.now()

    def add_related_document(self, document_id: str) -> None:
        """Add a related document to this event."""
        if document_id not in self.related_document_ids:
            self.related_document_ids.append(document_id)
            self.updated_at = datetime.now()

    def add_deadline(self, deadline_id: str) -> None:
        """Add an associated deadline to this event."""
        if deadline_id not in self.associated_deadline_ids:
            self.associated_deadline_ids.append(deadline_id)
            self.updated_at = datetime.now()

    def get_display_time(self) -> str:
        """Get formatted display time."""
        if self.event_time:
            return self.event_time.strftime("%I:%M %p")
        return "Time TBD"

    def get_display_location(self) -> str:
        """Get formatted display location."""
        parts = []
        if self.department:
            parts.append(f"Dept. {self.department}")
        if self.courtroom:
            parts.append(f"Courtroom {self.courtroom}")
        return ", ".join(parts) if parts else "Location TBD"

    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'event_type': self.event_type.value,
            'event_date': self.event_date.isoformat(),
            'case_id': self.case_id,
            'status': self.status.value,
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'department': self.department,
            'courtroom': self.courtroom,
            'court_address': self.court_address,
            'judge_name': self.judge_name,
            'clerk_name': self.clerk_name,
            'related_document_ids': self.related_document_ids,
            'minute_order_id': self.minute_order_id,
            'parties_required': self.parties_required,
            'associated_deadline_ids': self.associated_deadline_ids,
            'result': self.result.value if self.result else None,
            'ruling_summary': self.ruling_summary,
            'next_event_id': self.next_event_id,
            'roa_entry_number': self.roa_entry_number,
            'roa_description': self.roa_description,
            'reminder_days_before': self.reminder_days_before,
            'reminders_sent': [d.isoformat() for d in self.reminders_sent],
            'notes': self.notes,
            'is_mandatory': self.is_mandatory,
            'requires_appearance': self.requires_appearance,
            'allow_telephonic': self.allow_telephonic,
            'allow_remote': self.allow_remote,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CourtEvent':
        """Create CourtEvent from dictionary."""
        return cls(
            id=data.get('id', str(uuid4())),
            title=data['title'],
            event_type=EventType(data['event_type']),
            event_date=date.fromisoformat(data['event_date']),
            case_id=data['case_id'],
            status=EventStatus(data.get('status', 'scheduled')),
            event_time=time.fromisoformat(data['event_time']) if data.get('event_time') else None,
            end_time=time.fromisoformat(data['end_time']) if data.get('end_time') else None,
            department=data.get('department'),
            courtroom=data.get('courtroom'),
            court_address=data.get('court_address'),
            judge_name=data.get('judge_name'),
            clerk_name=data.get('clerk_name'),
            related_document_ids=data.get('related_document_ids', []),
            minute_order_id=data.get('minute_order_id'),
            parties_required=data.get('parties_required', []),
            associated_deadline_ids=data.get('associated_deadline_ids', []),
            result=EventResult(data['result']) if data.get('result') else None,
            ruling_summary=data.get('ruling_summary'),
            next_event_id=data.get('next_event_id'),
            roa_entry_number=data.get('roa_entry_number'),
            roa_description=data.get('roa_description'),
            reminder_days_before=data.get('reminder_days_before', [7, 3, 1]),
            reminders_sent=[date.fromisoformat(d) for d in data.get('reminders_sent', [])],
            notes=data.get('notes', ''),
            is_mandatory=data.get('is_mandatory', False),
            requires_appearance=data.get('requires_appearance', True),
            allow_telephonic=data.get('allow_telephonic', False),
            allow_remote=data.get('allow_remote', False),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
        )

    def __repr__(self) -> str:
        return f"CourtEvent({self.title}, {self.event_date.isoformat()})"
