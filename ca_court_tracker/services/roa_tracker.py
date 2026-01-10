"""
Register of Actions (ROA) Tracker

Tracks and manages court Register of Actions entries for California cases.
The ROA is the official record of all filings and court actions in a case.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict
from uuid import uuid4

from ..models.case import Case
from ..models.document import Document, DocumentType, DocumentStatus
from ..models.event import CourtEvent, EventType, EventStatus


@dataclass
class ROAEntry:
    """
    Represents a single entry in the Register of Actions.

    Each ROA entry documents a filing, court action, or other
    significant event in a case.
    """
    entry_number: str
    entry_date: date
    description: str
    case_id: str

    id: str = field(default_factory=lambda: str(uuid4()))
    entry_type: str = "general"  # filing, minute_order, court_action, service, etc.

    # Filing information
    filed_by: Optional[str] = None
    party_type: Optional[str] = None  # plaintiff, defendant, court

    # Associated items
    document_id: Optional[str] = None
    event_id: Optional[str] = None

    # Court clerk information
    clerk_initials: Optional[str] = None
    department: Optional[str] = None

    # Fee information
    filing_fee: Optional[float] = None
    fee_paid: bool = True

    # Status
    is_sealed: bool = False
    is_confidential: bool = False

    # Metadata
    raw_text: Optional[str] = None  # Original text from court system
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'entry_number': self.entry_number,
            'entry_date': self.entry_date.isoformat(),
            'description': self.description,
            'case_id': self.case_id,
            'entry_type': self.entry_type,
            'filed_by': self.filed_by,
            'party_type': self.party_type,
            'document_id': self.document_id,
            'event_id': self.event_id,
            'clerk_initials': self.clerk_initials,
            'department': self.department,
            'filing_fee': self.filing_fee,
            'fee_paid': self.fee_paid,
            'is_sealed': self.is_sealed,
            'is_confidential': self.is_confidential,
            'raw_text': self.raw_text,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ROAEntry':
        return cls(
            id=data.get('id', str(uuid4())),
            entry_number=data['entry_number'],
            entry_date=date.fromisoformat(data['entry_date']),
            description=data['description'],
            case_id=data['case_id'],
            entry_type=data.get('entry_type', 'general'),
            filed_by=data.get('filed_by'),
            party_type=data.get('party_type'),
            document_id=data.get('document_id'),
            event_id=data.get('event_id'),
            clerk_initials=data.get('clerk_initials'),
            department=data.get('department'),
            filing_fee=data.get('filing_fee'),
            fee_paid=data.get('fee_paid', True),
            is_sealed=data.get('is_sealed', False),
            is_confidential=data.get('is_confidential', False),
            raw_text=data.get('raw_text'),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
        )


class ROATracker:
    """
    Manages Register of Actions entries for California court cases.

    Provides functionality to:
    - Add and track ROA entries
    - Parse ROA text from court systems
    - Link entries to documents and events
    - Search and filter entries
    - Generate ROA reports
    """

    # Common ROA entry type patterns
    ENTRY_TYPE_PATTERNS = {
        'filing': ['filed', 'complaint', 'answer', 'motion', 'declaration',
                   'memorandum', 'opposition', 'reply', 'demurrer'],
        'minute_order': ['minute order', 'minutes'],
        'court_order': ['order', 'ruling', 'judgment', 'decree'],
        'hearing': ['hearing', 'conference', 'trial', 'oral argument'],
        'service': ['proof of service', 'served', 'service'],
        'notice': ['notice of', 'notification'],
        'continuance': ['continued', 'continuance', 'reset'],
        'dismissal': ['dismissed', 'dismissal'],
        'default': ['default', 'default entered'],
    }

    # Document type inference from ROA descriptions
    DOCUMENT_TYPE_KEYWORDS = {
        DocumentType.COMPLAINT: ['complaint', 'complaint for'],
        DocumentType.ANSWER: ['answer to complaint', 'answer'],
        DocumentType.DEMURRER: ['demurrer'],
        DocumentType.MOTION: ['motion for', 'motion to'],
        DocumentType.MOTION_FOR_SUMMARY_JUDGMENT: ['motion for summary judgment', 'msj'],
        DocumentType.MOTION_TO_COMPEL: ['motion to compel'],
        DocumentType.OPPOSITION: ['opposition to', 'opposition'],
        DocumentType.REPLY: ['reply to', 'reply in support'],
        DocumentType.DECLARATION: ['declaration of', 'declaration'],
        DocumentType.NOTICE: ['notice of'],
        DocumentType.PROOF_OF_SERVICE: ['proof of service'],
        DocumentType.COURT_ORDER: ['order on', 'order granting', 'order denying', 'order re'],
        DocumentType.MINUTE_ORDER: ['minute order', 'minutes'],
        DocumentType.CASE_MANAGEMENT_ORDER: ['case management order', 'cmo'],
        DocumentType.JUDGMENT: ['judgment', 'judgment entered'],
        DocumentType.DISMISSAL: ['dismissal', 'request for dismissal'],
        DocumentType.STIPULATION: ['stipulation'],
        DocumentType.INTERROGATORIES: ['interrogatories', 'form interrogatories', 'special interrogatories'],
        DocumentType.REQUESTS_FOR_PRODUCTION: ['request for production', 'demand for production'],
        DocumentType.REQUESTS_FOR_ADMISSION: ['request for admission', 'requests for admission'],
    }

    def __init__(self):
        """Initialize the ROA tracker."""
        self.entries: Dict[str, ROAEntry] = {}  # entry_id -> ROAEntry
        self.case_entries: Dict[str, List[str]] = {}  # case_id -> [entry_ids]

    def add_entry(self, entry: ROAEntry) -> ROAEntry:
        """Add a new ROA entry."""
        self.entries[entry.id] = entry

        if entry.case_id not in self.case_entries:
            self.case_entries[entry.case_id] = []
        self.case_entries[entry.case_id].append(entry.id)

        return entry

    def create_entry(self, entry_number: str, entry_date: date,
                     description: str, case_id: str, **kwargs) -> ROAEntry:
        """Create and add a new ROA entry."""
        entry_type = self._infer_entry_type(description)
        entry = ROAEntry(
            entry_number=entry_number,
            entry_date=entry_date,
            description=description,
            case_id=case_id,
            entry_type=entry_type,
            **kwargs
        )
        return self.add_entry(entry)

    def get_entry(self, entry_id: str) -> Optional[ROAEntry]:
        """Get an ROA entry by ID."""
        return self.entries.get(entry_id)

    def get_entry_by_number(self, case_id: str, entry_number: str) -> Optional[ROAEntry]:
        """Get an ROA entry by case ID and entry number."""
        for entry_id in self.case_entries.get(case_id, []):
            entry = self.entries.get(entry_id)
            if entry and entry.entry_number == entry_number:
                return entry
        return None

    def get_case_entries(self, case_id: str) -> List[ROAEntry]:
        """Get all ROA entries for a case, sorted by date."""
        entry_ids = self.case_entries.get(case_id, [])
        entries = [self.entries[eid] for eid in entry_ids if eid in self.entries]
        return sorted(entries, key=lambda e: (e.entry_date, e.entry_number))

    def get_entries_by_type(self, case_id: str, entry_type: str) -> List[ROAEntry]:
        """Get ROA entries of a specific type for a case."""
        entries = self.get_case_entries(case_id)
        return [e for e in entries if e.entry_type == entry_type]

    def get_entries_by_date_range(self, case_id: str, start_date: date,
                                   end_date: date) -> List[ROAEntry]:
        """Get ROA entries within a date range."""
        entries = self.get_case_entries(case_id)
        return [e for e in entries if start_date <= e.entry_date <= end_date]

    def get_recent_entries(self, case_id: str, limit: int = 10) -> List[ROAEntry]:
        """Get the most recent ROA entries for a case."""
        entries = self.get_case_entries(case_id)
        return sorted(entries, key=lambda e: e.entry_date, reverse=True)[:limit]

    def search_entries(self, case_id: str, search_term: str) -> List[ROAEntry]:
        """Search ROA entries by description."""
        entries = self.get_case_entries(case_id)
        search_lower = search_term.lower()
        return [e for e in entries if search_lower in e.description.lower()]

    def _infer_entry_type(self, description: str) -> str:
        """Infer entry type from description text."""
        desc_lower = description.lower()

        for entry_type, keywords in self.ENTRY_TYPE_PATTERNS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return entry_type

        return 'general'

    def infer_document_type(self, description: str) -> Optional[DocumentType]:
        """Infer document type from ROA description."""
        desc_lower = description.lower()

        for doc_type, keywords in self.DOCUMENT_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return doc_type

        return None

    def parse_roa_text(self, case_id: str, roa_text: str) -> List[ROAEntry]:
        """
        Parse raw ROA text from court system.

        Expects format like:
        01/15/2024 001 Complaint filed by Plaintiff John Doe
        01/20/2024 002 Proof of Service filed
        ...

        Returns list of created ROA entries.
        """
        entries = []
        lines = roa_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to parse date and entry number
            parts = line.split(None, 2)  # Split into max 3 parts
            if len(parts) < 3:
                continue

            try:
                # Try common date formats
                date_str = parts[0]
                entry_number = parts[1]
                description = parts[2]

                # Parse date (try multiple formats)
                entry_date = None
                for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                    try:
                        entry_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue

                if entry_date is None:
                    continue

                entry = self.create_entry(
                    entry_number=entry_number,
                    entry_date=entry_date,
                    description=description,
                    case_id=case_id,
                    raw_text=line
                )
                entries.append(entry)

            except (ValueError, IndexError):
                continue

        return entries

    def create_document_from_entry(self, entry: ROAEntry,
                                    filed_by_party_id: Optional[str] = None,
                                    filed_by_party_name: Optional[str] = None) -> Optional[Document]:
        """
        Create a Document object from an ROA entry.

        Useful for populating documents from ROA data.
        """
        doc_type = self.infer_document_type(entry.description)
        if doc_type is None:
            doc_type = DocumentType.OTHER

        document = Document(
            title=entry.description,
            document_type=doc_type,
            case_id=entry.case_id,
            status=DocumentStatus.FILED,
            filing_date=entry.entry_date,
            filed_by_party_id=filed_by_party_id or entry.filed_by,
            filed_by_party_name=filed_by_party_name,
            roa_entry_number=entry.entry_number,
        )

        # Update entry with document reference
        entry.document_id = document.id

        return document

    def create_event_from_entry(self, entry: ROAEntry) -> Optional[CourtEvent]:
        """
        Create a CourtEvent from an ROA entry if it represents a hearing or conference.
        """
        if entry.entry_type not in ['hearing', 'minute_order']:
            return None

        # Determine event type
        desc_lower = entry.description.lower()
        event_type = EventType.OTHER

        if 'case management conference' in desc_lower or 'cmc' in desc_lower:
            event_type = EventType.CASE_MANAGEMENT_CONFERENCE
        elif 'final status conference' in desc_lower or 'fsc' in desc_lower:
            event_type = EventType.FINAL_STATUS_CONFERENCE
        elif 'trial' in desc_lower:
            event_type = EventType.TRIAL
        elif 'motion' in desc_lower:
            event_type = EventType.MOTION_HEARING
        elif 'hearing' in desc_lower:
            event_type = EventType.MOTION_HEARING

        event = CourtEvent(
            title=entry.description,
            event_type=event_type,
            event_date=entry.entry_date,
            case_id=entry.case_id,
            status=EventStatus.COMPLETED,
            department=entry.department,
            roa_entry_number=entry.entry_number,
            roa_description=entry.description,
        )

        # Update entry with event reference
        entry.event_id = event.id

        return event

    def link_entry_to_document(self, entry_id: str, document_id: str) -> bool:
        """Link an ROA entry to a document."""
        entry = self.entries.get(entry_id)
        if entry:
            entry.document_id = document_id
            return True
        return False

    def link_entry_to_event(self, entry_id: str, event_id: str) -> bool:
        """Link an ROA entry to an event."""
        entry = self.entries.get(entry_id)
        if entry:
            entry.event_id = event_id
            return True
        return False

    def generate_roa_report(self, case_id: str) -> str:
        """Generate a formatted ROA report for a case."""
        entries = self.get_case_entries(case_id)

        if not entries:
            return f"No ROA entries found for case {case_id}"

        lines = [
            f"REGISTER OF ACTIONS",
            f"Case ID: {case_id}",
            f"Generated: {datetime.now().strftime('%m/%d/%Y %H:%M')}",
            "=" * 80,
            ""
        ]

        for entry in entries:
            date_str = entry.entry_date.strftime('%m/%d/%Y')
            lines.append(f"{date_str}  {entry.entry_number:>4}  {entry.description}")
            if entry.filed_by:
                lines.append(f"              Filed by: {entry.filed_by}")
            if entry.filing_fee:
                lines.append(f"              Fee: ${entry.filing_fee:.2f}")
            lines.append("")

        lines.append("=" * 80)
        lines.append(f"Total entries: {len(entries)}")

        return '\n'.join(lines)

    def get_filing_statistics(self, case_id: str) -> dict:
        """Get filing statistics for a case."""
        entries = self.get_case_entries(case_id)

        stats = {
            'total_entries': len(entries),
            'filings': 0,
            'court_orders': 0,
            'minute_orders': 0,
            'hearings': 0,
            'by_party_type': {},
            'by_month': {},
            'total_fees': 0.0,
        }

        for entry in entries:
            # Count by type
            if entry.entry_type == 'filing':
                stats['filings'] += 1
            elif entry.entry_type == 'court_order':
                stats['court_orders'] += 1
            elif entry.entry_type == 'minute_order':
                stats['minute_orders'] += 1
            elif entry.entry_type == 'hearing':
                stats['hearings'] += 1

            # Count by party type
            if entry.party_type:
                stats['by_party_type'][entry.party_type] = \
                    stats['by_party_type'].get(entry.party_type, 0) + 1

            # Count by month
            month_key = entry.entry_date.strftime('%Y-%m')
            stats['by_month'][month_key] = stats['by_month'].get(month_key, 0) + 1

            # Sum fees
            if entry.filing_fee:
                stats['total_fees'] += entry.filing_fee

        return stats

    def export_entries(self, case_id: str) -> List[dict]:
        """Export all entries for a case as list of dicts."""
        entries = self.get_case_entries(case_id)
        return [e.to_dict() for e in entries]

    def import_entries(self, entries_data: List[dict]) -> int:
        """Import entries from list of dicts."""
        count = 0
        for data in entries_data:
            entry = ROAEntry.from_dict(data)
            self.add_entry(entry)
            count += 1
        return count
