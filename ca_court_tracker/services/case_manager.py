"""
Case Manager Service

Central service that integrates all tracking components for
California court case management.
"""

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from ..models.case import Case, CaseType, CaseStatus
from ..models.party import Party, PartyType, Attorney
from ..models.document import Document, DocumentType, ServiceMethod
from ..models.event import CourtEvent, EventType, EventStatus, EventResult
from ..models.deadline import Deadline, DeadlineType, DeadlineStatus, DeadlinePriority

from .deadline_calculator import DeadlineCalculator
from .roa_tracker import ROATracker, ROAEntry
from .cmo_tracker import CMOTracker, CaseManagementOrder
from .filing_tracker import FilingTracker
from .calendar_tracker import CalendarTracker
from .onelegal_tracker import OneLegalTracker, OneLegalTransaction, OneLegalServiceType


@dataclass
class CaseSummary:
    """Summary of a case's current status."""
    case: Case
    upcoming_deadlines: List[Deadline]
    upcoming_events: List[CourtEvent]
    pending_responses: List[Document]
    recent_filings: List[Document]
    current_cmo: Optional[CaseManagementOrder]

    def to_dict(self) -> dict:
        return {
            'case': self.case.to_dict(),
            'upcoming_deadlines': [d.to_dict() for d in self.upcoming_deadlines],
            'upcoming_events': [e.to_dict() for e in self.upcoming_events],
            'pending_responses': [d.to_dict() for d in self.pending_responses],
            'recent_filings': [d.to_dict() for d in self.recent_filings],
            'current_cmo': self.current_cmo.to_dict() if self.current_cmo else None,
        }


class CaseManager:
    """
    Central manager for California court cases.

    Integrates:
    - Case and party management
    - Register of Actions tracking
    - Case Management Order tracking
    - Court filings and service tracking
    - Court calendar management
    - OneLegal e-service tracking
    - Deadline calculation and monitoring
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the Case Manager.

        Args:
            data_dir: Optional directory for data persistence
        """
        self.data_dir = Path(data_dir) if data_dir else None

        # Core data stores
        self.cases: Dict[str, Case] = {}
        self.parties: Dict[str, Party] = {}
        self.deadlines: Dict[str, Deadline] = {}

        # Service trackers
        self.deadline_calculator = DeadlineCalculator()
        self.roa_tracker = ROATracker()
        self.cmo_tracker = CMOTracker()
        self.filing_tracker = FilingTracker()
        self.calendar_tracker = CalendarTracker()
        self.onelegal_tracker = OneLegalTracker()

        # Index mappings
        self.case_parties: Dict[str, List[str]] = {}  # case_id -> [party_ids]
        self.case_deadlines: Dict[str, List[str]] = {}  # case_id -> [deadline_ids]

    # =========================================================================
    # Case Management
    # =========================================================================

    def create_case(self, case_number: str, case_name: str, case_type: CaseType,
                    court_name: str, county: str, **kwargs) -> Case:
        """Create a new case."""
        case = Case(
            case_number=case_number,
            case_name=case_name,
            case_type=case_type,
            court_name=court_name,
            county=county,
            **kwargs
        )
        self.cases[case.id] = case
        self.case_parties[case.id] = []
        self.case_deadlines[case.id] = []
        return case

    def get_case(self, case_id: str) -> Optional[Case]:
        """Get a case by ID."""
        return self.cases.get(case_id)

    def get_case_by_number(self, case_number: str) -> Optional[Case]:
        """Get a case by case number."""
        for case in self.cases.values():
            if case.case_number == case_number:
                return case
        return None

    def update_case(self, case_id: str, **kwargs) -> Optional[Case]:
        """Update case attributes."""
        case = self.cases.get(case_id)
        if case:
            for key, value in kwargs.items():
                if hasattr(case, key):
                    setattr(case, key, value)
            case.updated_at = datetime.now()
        return case

    def list_cases(self, status: Optional[CaseStatus] = None) -> List[Case]:
        """List all cases, optionally filtered by status."""
        cases = list(self.cases.values())
        if status:
            cases = [c for c in cases if c.status == status]
        return sorted(cases, key=lambda c: c.updated_at, reverse=True)

    # =========================================================================
    # Party Management
    # =========================================================================

    def add_party(self, case_id: str, name: str, party_type: PartyType,
                  **kwargs) -> Optional[Party]:
        """Add a party to a case."""
        case = self.cases.get(case_id)
        if not case:
            return None

        party = Party(name=name, party_type=party_type, case_id=case_id, **kwargs)
        self.parties[party.id] = party
        self.case_parties[case_id].append(party.id)
        case.add_party(party.id)
        return party

    def get_party(self, party_id: str) -> Optional[Party]:
        """Get a party by ID."""
        return self.parties.get(party_id)

    def get_case_parties(self, case_id: str, party_type: Optional[PartyType] = None,
                         active_only: bool = True) -> List[Party]:
        """Get all parties for a case."""
        party_ids = self.case_parties.get(case_id, [])
        parties = [self.parties[pid] for pid in party_ids if pid in self.parties]

        if party_type:
            parties = [p for p in parties if p.party_type == party_type]
        if active_only:
            parties = [p for p in parties if p.is_active]

        return parties

    def add_attorney_to_party(self, party_id: str, attorney_name: str,
                               **kwargs) -> Optional[Attorney]:
        """Add an attorney to a party."""
        party = self.parties.get(party_id)
        if party:
            attorney = Attorney(name=attorney_name, **kwargs)
            party.add_attorney(attorney)
            return attorney
        return None

    # =========================================================================
    # Document Management (via FilingTracker)
    # =========================================================================

    def file_document(self, case_id: str, title: str, document_type: DocumentType,
                      filing_date: date, filed_by_party_id: Optional[str] = None,
                      **kwargs) -> Optional[Document]:
        """File a document in a case."""
        case = self.cases.get(case_id)
        if not case:
            return None

        filed_by_name = None
        if filed_by_party_id:
            party = self.parties.get(filed_by_party_id)
            if party:
                filed_by_name = party.name

        document = self.filing_tracker.create_document(
            title=title,
            document_type=document_type,
            case_id=case_id,
            filed_by_party_id=filed_by_party_id,
            filed_by_party_name=filed_by_name,
            **kwargs
        )
        document.mark_filed(filing_date)
        case.add_document(document.id)

        return document

    def serve_document(self, document_id: str, party_id: str,
                       service_method: ServiceMethod, service_date: date,
                       **kwargs) -> bool:
        """Record service of a document on a party."""
        party = self.parties.get(party_id)
        if not party:
            return False

        record = self.filing_tracker.serve_document(
            document_id=document_id,
            party_id=party_id,
            party_name=party.name,
            service_method=service_method,
            service_date=service_date,
            **kwargs
        )
        return record is not None

    def create_response_deadline(self, document_id: str, responsible_party_id: str) -> Optional[Deadline]:
        """Create a response deadline for a document."""
        document = self.filing_tracker.get_document(document_id)
        party = self.parties.get(responsible_party_id)

        if not document or not party:
            return None

        deadline = self.filing_tracker.create_response_deadline(
            document=document,
            responsible_party_id=responsible_party_id,
            responsible_party_name=party.name
        )

        if deadline:
            self.deadlines[deadline.id] = deadline
            if document.case_id not in self.case_deadlines:
                self.case_deadlines[document.case_id] = []
            self.case_deadlines[document.case_id].append(deadline.id)

            case = self.cases.get(document.case_id)
            if case:
                case.add_deadline(deadline.id)

        return deadline

    # =========================================================================
    # Calendar Management (via CalendarTracker)
    # =========================================================================

    def schedule_hearing(self, case_id: str, title: str, hearing_date: date,
                         event_type: EventType = EventType.MOTION_HEARING,
                         create_deadlines: bool = True,
                         responding_party_id: Optional[str] = None,
                         **kwargs) -> Tuple[Optional[CourtEvent], List[Deadline]]:
        """Schedule a hearing and optionally create associated deadlines."""
        case = self.cases.get(case_id)
        if not case:
            return None, []

        if create_deadlines:
            event, deadlines = self.calendar_tracker.schedule_hearing(
                case_id=case_id,
                title=title,
                hearing_date=hearing_date,
                event_type=event_type,
                **kwargs
            )

            # Store deadlines
            for deadline in deadlines:
                if responding_party_id:
                    deadline.responsible_party_id = responding_party_id
                    party = self.parties.get(responding_party_id)
                    if party:
                        deadline.responsible_party_name = party.name

                self.deadlines[deadline.id] = deadline
                self.case_deadlines[case_id].append(deadline.id)
                case.add_deadline(deadline.id)
        else:
            event = self.calendar_tracker.create_event(
                title=title,
                event_type=event_type,
                event_date=hearing_date,
                case_id=case_id,
                **kwargs
            )
            deadlines = []

        case.add_event(event.id)
        return event, deadlines

    def complete_hearing(self, event_id: str, result: EventResult,
                         ruling_summary: Optional[str] = None) -> bool:
        """Record the result of a hearing."""
        return self.calendar_tracker.complete_event(event_id, result, ruling_summary)

    def continue_hearing(self, event_id: str, new_date: date,
                         reason: Optional[str] = None) -> Optional[CourtEvent]:
        """Continue a hearing to a new date."""
        return self.calendar_tracker.continue_event(event_id, new_date, reason)

    # =========================================================================
    # CMO Management (via CMOTracker)
    # =========================================================================

    def add_cmo(self, case_id: str, order_date: date, trial_date: Optional[date] = None,
                **kwargs) -> Optional[CaseManagementOrder]:
        """Add a Case Management Order to a case."""
        case = self.cases.get(case_id)
        if not case:
            return None

        cmo = self.cmo_tracker.create_cmo(
            case_id=case_id,
            order_date=order_date,
            trial_date=trial_date,
            **kwargs
        )

        # Update case with CMO dates
        if trial_date:
            case.trial_date = trial_date

        return cmo

    def generate_cmo_deadlines(self, cmo_id: str) -> List[Deadline]:
        """Generate deadline objects from a CMO."""
        cmo = self.cmo_tracker.get_cmo(cmo_id)
        if not cmo:
            return []

        deadlines = self.cmo_tracker.generate_deadlines_from_cmo(cmo)

        # Store deadlines
        for deadline in deadlines:
            self.deadlines[deadline.id] = deadline
            if cmo.case_id not in self.case_deadlines:
                self.case_deadlines[cmo.case_id] = []
            self.case_deadlines[cmo.case_id].append(deadline.id)

            case = self.cases.get(cmo.case_id)
            if case:
                case.add_deadline(deadline.id)

        return deadlines

    # =========================================================================
    # ROA Management (via ROATracker)
    # =========================================================================

    def add_roa_entry(self, case_id: str, entry_number: str, entry_date: date,
                      description: str, **kwargs) -> Optional[ROAEntry]:
        """Add a Register of Actions entry."""
        case = self.cases.get(case_id)
        if not case:
            return None

        return self.roa_tracker.create_entry(
            entry_number=entry_number,
            entry_date=entry_date,
            description=description,
            case_id=case_id,
            **kwargs
        )

    def import_roa(self, case_id: str, roa_text: str) -> List[ROAEntry]:
        """Import ROA entries from text."""
        case = self.cases.get(case_id)
        if not case:
            return []

        return self.roa_tracker.parse_roa_text(case_id, roa_text)

    # =========================================================================
    # OneLegal Management (via OneLegalTracker)
    # =========================================================================

    def record_onelegal_service(self, document_id: str, transaction_id: str,
                                 recipients: List[str],
                                 recipient_party_ids: List[str],
                                 **kwargs) -> Optional[OneLegalTransaction]:
        """Record a OneLegal service transaction."""
        document = self.filing_tracker.get_document(document_id)
        if not document:
            return None

        transaction = self.onelegal_tracker.create_transaction(
            transaction_id=transaction_id,
            document_id=document_id,
            case_id=document.case_id,
            recipients=recipients,
            recipient_party_ids=recipient_party_ids,
            document_title=document.title,
            **kwargs
        )

        return transaction

    def complete_onelegal_service(self, transaction_id: str,
                                   confirmation_number: str) -> bool:
        """Mark a OneLegal transaction as complete and update document."""
        txn = self.onelegal_tracker.get_transaction_by_onelegal_id(transaction_id)
        if not txn:
            return False

        self.onelegal_tracker.update_transaction_status(
            txn.id,
            status=self.onelegal_tracker.OneLegalStatus.DELIVERED,
            confirmation_number=confirmation_number
        )

        # Update document service records
        document = self.filing_tracker.get_document(txn.document_id)
        if document:
            parties = [self.parties[pid] for pid in txn.recipient_party_ids
                       if pid in self.parties]
            self.onelegal_tracker.record_service_on_document(document, txn, parties)

        return True

    # =========================================================================
    # Deadline Management
    # =========================================================================

    def get_deadline(self, deadline_id: str) -> Optional[Deadline]:
        """Get a deadline by ID."""
        return self.deadlines.get(deadline_id)

    def get_case_deadlines(self, case_id: str, status: Optional[DeadlineStatus] = None,
                           include_completed: bool = False) -> List[Deadline]:
        """Get deadlines for a case."""
        deadline_ids = self.case_deadlines.get(case_id, [])
        deadlines = [self.deadlines[did] for did in deadline_ids if did in self.deadlines]

        if status:
            deadlines = [d for d in deadlines if d.status == status]
        if not include_completed:
            deadlines = [d for d in deadlines
                         if d.status not in [DeadlineStatus.COMPLETED, DeadlineStatus.WAIVED]]

        return sorted(deadlines, key=lambda d: d.due_date)

    def get_urgent_deadlines(self, case_id: str, days_threshold: int = 7) -> List[Deadline]:
        """Get urgent deadlines for a case."""
        deadlines = self.get_case_deadlines(case_id)
        return [d for d in deadlines if d.days_remaining() <= days_threshold and d.days_remaining() >= 0]

    def get_overdue_deadlines(self, case_id: str) -> List[Deadline]:
        """Get overdue deadlines for a case."""
        deadlines = self.get_case_deadlines(case_id)
        return [d for d in deadlines if d.is_past_due()]

    def complete_deadline(self, deadline_id: str, document_id: Optional[str] = None) -> bool:
        """Mark a deadline as completed."""
        deadline = self.deadlines.get(deadline_id)
        if deadline:
            deadline.complete(document_id=document_id)
            return True
        return False

    def extend_deadline(self, deadline_id: str, new_date: date, reason: str,
                        stipulated: bool = False, court_ordered: bool = False) -> bool:
        """Extend a deadline."""
        deadline = self.deadlines.get(deadline_id)
        if deadline:
            deadline.extend(new_date, reason, stipulated, court_ordered)
            return True
        return False

    def calculate_deadline(self, trigger_date: date, base_days: int,
                            service_method: ServiceMethod = ServiceMethod.ELECTRONIC_SERVICE,
                            court_days: bool = False) -> date:
        """Calculate a deadline from a trigger date."""
        service_extension = self.deadline_calculator.get_service_extension(service_method)
        total_days = base_days + service_extension

        if court_days:
            return self.deadline_calculator.add_court_days(trigger_date, total_days)
        else:
            return self.deadline_calculator.add_calendar_days(trigger_date, total_days)

    # =========================================================================
    # Case Summary and Reporting
    # =========================================================================

    def get_case_summary(self, case_id: str) -> Optional[CaseSummary]:
        """Get a comprehensive summary of a case."""
        case = self.cases.get(case_id)
        if not case:
            return None

        return CaseSummary(
            case=case,
            upcoming_deadlines=self.get_urgent_deadlines(case_id, 30),
            upcoming_events=self.calendar_tracker.get_upcoming_events(case_id, 30),
            pending_responses=self.filing_tracker.get_documents_requiring_response(case_id),
            recent_filings=self.filing_tracker.get_recent_filings(case_id, 5),
            current_cmo=self.cmo_tracker.get_current_cmo(case_id)
        )

    def generate_case_report(self, case_id: str) -> str:
        """Generate a comprehensive case report."""
        case = self.cases.get(case_id)
        if not case:
            return f"Case not found: {case_id}"

        lines = [
            "=" * 80,
            "CALIFORNIA COURT CASE REPORT",
            "=" * 80,
            "",
            f"Case Number: {case.case_number}",
            f"Case Name: {case.case_name}",
            f"Case Type: {case.case_type.value}",
            f"Status: {case.status.value}",
            f"Court: {case.court_name}",
            f"County: {case.county}",
        ]

        if case.department:
            lines.append(f"Department: {case.department}")
        if case.judge_name:
            lines.append(f"Judge: {case.judge_name}")
        if case.filing_date:
            lines.append(f"Filed: {case.filing_date.strftime('%m/%d/%Y')}")
        if case.trial_date:
            days = (case.trial_date - date.today()).days
            lines.append(f"Trial Date: {case.trial_date.strftime('%m/%d/%Y')} ({days} days)")

        # Parties
        parties = self.get_case_parties(case_id)
        if parties:
            lines.extend(["", "PARTIES:", "-" * 40])
            for party in parties:
                lines.append(f"  {party.party_type.value.upper()}: {party.name}")
                if party.attorneys:
                    for atty in party.attorneys:
                        lines.append(f"    Attorney: {atty.name}")

        # Upcoming Deadlines
        urgent = self.get_urgent_deadlines(case_id, 14)
        if urgent:
            lines.extend(["", "UPCOMING DEADLINES:", "-" * 40])
            for deadline in urgent:
                status = deadline.get_status_display()
                lines.append(f"  {deadline.due_date.strftime('%m/%d/%Y')} - {deadline.title}")
                lines.append(f"      Status: {status}")

        # Upcoming Events
        events = self.calendar_tracker.get_upcoming_events(case_id, 30)
        if events:
            lines.extend(["", "UPCOMING EVENTS:", "-" * 40])
            for event in events:
                lines.append(f"  {event.event_date.strftime('%m/%d/%Y')} {event.get_display_time()}")
                lines.append(f"      {event.title}")
                lines.append(f"      {event.get_display_location()}")

        # Recent Filings
        recent = self.filing_tracker.get_recent_filings(case_id, 5)
        if recent:
            lines.extend(["", "RECENT FILINGS:", "-" * 40])
            for doc in recent:
                date_str = doc.filing_date.strftime('%m/%d/%Y') if doc.filing_date else 'N/A'
                lines.append(f"  {date_str} - {doc.title}")

        lines.extend(["", "=" * 80])

        return '\n'.join(lines)

    def get_all_upcoming_deadlines(self, days_ahead: int = 14) -> List[Tuple[Case, Deadline]]:
        """Get all upcoming deadlines across all cases."""
        result = []
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)

        for case_id, deadline_ids in self.case_deadlines.items():
            case = self.cases.get(case_id)
            if not case:
                continue

            for did in deadline_ids:
                deadline = self.deadlines.get(did)
                if deadline and deadline.status not in [DeadlineStatus.COMPLETED, DeadlineStatus.WAIVED]:
                    if today <= deadline.due_date <= cutoff:
                        result.append((case, deadline))

        return sorted(result, key=lambda x: x[1].due_date)

    # =========================================================================
    # Data Persistence
    # =========================================================================

    def save(self, filepath: Optional[str] = None) -> bool:
        """Save all data to a JSON file."""
        if filepath:
            save_path = Path(filepath)
        elif self.data_dir:
            save_path = self.data_dir / "case_data.json"
        else:
            return False

        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'cases': {cid: c.to_dict() for cid, c in self.cases.items()},
            'parties': {pid: p.to_dict() for pid, p in self.parties.items()},
            'deadlines': {did: d.to_dict() for did, d in self.deadlines.items()},
            'case_parties': self.case_parties,
            'case_deadlines': self.case_deadlines,
            'roa_entries': {eid: e.to_dict() for eid, e in self.roa_tracker.entries.items()},
            'roa_case_entries': self.roa_tracker.case_entries,
            'cmos': {cid: c.to_dict() for cid, c in self.cmo_tracker.cmos.items()},
            'cmo_case_cmos': self.cmo_tracker.case_cmos,
            'documents': {did: d.to_dict() for did, d in self.filing_tracker.documents.items()},
            'document_case_docs': self.filing_tracker.case_documents,
            'events': {eid: e.to_dict() for eid, e in self.calendar_tracker.events.items()},
            'event_case_events': self.calendar_tracker.case_events,
            'onelegal_transactions': {tid: t.to_dict() for tid, t in self.onelegal_tracker.transactions.items()},
            'onelegal_case_txns': self.onelegal_tracker.case_transactions,
            'onelegal_doc_txns': self.onelegal_tracker.document_transactions,
            'saved_at': datetime.now().isoformat(),
        }

        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)

        return True

    def load(self, filepath: Optional[str] = None) -> bool:
        """Load data from a JSON file."""
        if filepath:
            load_path = Path(filepath)
        elif self.data_dir:
            load_path = self.data_dir / "case_data.json"
        else:
            return False

        if not load_path.exists():
            return False

        with open(load_path, 'r') as f:
            data = json.load(f)

        # Load cases
        self.cases = {cid: Case.from_dict(c) for cid, c in data.get('cases', {}).items()}
        self.parties = {pid: Party.from_dict(p) for pid, p in data.get('parties', {}).items()}
        self.deadlines = {did: Deadline.from_dict(d) for did, d in data.get('deadlines', {}).items()}
        self.case_parties = data.get('case_parties', {})
        self.case_deadlines = data.get('case_deadlines', {})

        # Load ROA entries
        self.roa_tracker.entries = {eid: ROAEntry.from_dict(e)
                                     for eid, e in data.get('roa_entries', {}).items()}
        self.roa_tracker.case_entries = data.get('roa_case_entries', {})

        # Load CMOs
        self.cmo_tracker.cmos = {cid: CaseManagementOrder.from_dict(c)
                                  for cid, c in data.get('cmos', {}).items()}
        self.cmo_tracker.case_cmos = data.get('cmo_case_cmos', {})

        # Load documents
        self.filing_tracker.documents = {did: Document.from_dict(d)
                                          for did, d in data.get('documents', {}).items()}
        self.filing_tracker.case_documents = data.get('document_case_docs', {})

        # Load events
        self.calendar_tracker.events = {eid: CourtEvent.from_dict(e)
                                         for eid, e in data.get('events', {}).items()}
        self.calendar_tracker.case_events = data.get('event_case_events', {})

        # Load OneLegal transactions
        self.onelegal_tracker.transactions = {tid: OneLegalTransaction.from_dict(t)
                                               for tid, t in data.get('onelegal_transactions', {}).items()}
        self.onelegal_tracker.case_transactions = data.get('onelegal_case_txns', {})
        self.onelegal_tracker.document_transactions = data.get('onelegal_doc_txns', {})

        return True
