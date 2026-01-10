"""Document model for California court filings and served documents."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class DocumentType(Enum):
    """Types of court documents."""
    # Pleadings
    COMPLAINT = "complaint"
    CROSS_COMPLAINT = "cross_complaint"
    ANSWER = "answer"
    DEMURRER = "demurrer"
    AMENDED_COMPLAINT = "amended_complaint"
    AMENDED_ANSWER = "amended_answer"

    # Motions
    MOTION = "motion"
    MOTION_TO_COMPEL = "motion_to_compel"
    MOTION_FOR_SUMMARY_JUDGMENT = "msj"
    MOTION_FOR_SUMMARY_ADJUDICATION = "msa"
    MOTION_TO_DISMISS = "motion_to_dismiss"
    MOTION_IN_LIMINE = "motion_in_limine"
    EX_PARTE_APPLICATION = "ex_parte"

    # Discovery
    INTERROGATORIES = "interrogatories"
    REQUESTS_FOR_PRODUCTION = "rfp"
    REQUESTS_FOR_ADMISSION = "rfa"
    DEPOSITION_NOTICE = "deposition_notice"
    SUBPOENA = "subpoena"

    # Responses
    OPPOSITION = "opposition"
    REPLY = "reply"
    RESPONSE = "response"
    OBJECTION = "objection"

    # Court Orders
    COURT_ORDER = "court_order"
    CASE_MANAGEMENT_ORDER = "cmo"
    SCHEDULING_ORDER = "scheduling_order"
    TENTATIVE_RULING = "tentative_ruling"
    MINUTE_ORDER = "minute_order"

    # Declarations and Evidence
    DECLARATION = "declaration"
    EXHIBIT = "exhibit"
    EVIDENCE = "evidence"

    # Notices
    NOTICE = "notice"
    NOTICE_OF_MOTION = "notice_of_motion"
    NOTICE_OF_HEARING = "notice_of_hearing"
    NOTICE_OF_RULING = "notice_of_ruling"

    # Settlement and Judgment
    SETTLEMENT_AGREEMENT = "settlement"
    STIPULATION = "stipulation"
    JUDGMENT = "judgment"
    DISMISSAL = "dismissal"

    # Other
    PROOF_OF_SERVICE = "proof_of_service"
    MEMORANDUM = "memorandum"
    BRIEF = "brief"
    OTHER = "other"


class ServiceMethod(Enum):
    """Methods of service under California law."""
    PERSONAL_SERVICE = "personal"  # CCP 415.10
    SUBSTITUTED_SERVICE = "substituted"  # CCP 415.20
    MAIL_SERVICE = "mail"  # CCP 415.30
    ELECTRONIC_SERVICE = "electronic"  # CCP 1010.6
    ONELEGAL = "onelegal"  # Via OneLegal e-service
    FAX_SERVICE = "fax"
    OVERNIGHT_DELIVERY = "overnight"
    POSTING = "posting"  # CCP 415.45
    PUBLICATION = "publication"  # CCP 415.50
    NOT_SERVED = "not_served"


class DocumentStatus(Enum):
    """Status of a document."""
    DRAFT = "draft"
    FILED = "filed"
    SERVED = "served"
    FILED_AND_SERVED = "filed_and_served"
    REJECTED = "rejected"
    LODGED = "lodged"
    RECEIVED = "received"


@dataclass
class ServiceRecord:
    """Record of service for a document."""
    party_id: str
    party_name: str
    service_method: ServiceMethod
    service_date: date
    service_address: Optional[str] = None
    service_email: Optional[str] = None
    onelegal_confirmation: Optional[str] = None
    proof_of_service_filed: bool = False
    notes: Optional[str] = None

    def get_service_extension_days(self) -> int:
        """
        Get deadline extension days based on service method.
        Based on CCP 1013 and 1010.6.
        """
        extensions = {
            ServiceMethod.PERSONAL_SERVICE: 0,
            ServiceMethod.ELECTRONIC_SERVICE: 2,  # CCP 1010.6(a)(3)(B)
            ServiceMethod.ONELEGAL: 2,  # Electronic service via OneLegal
            ServiceMethod.MAIL_SERVICE: 5,  # CCP 1013(a) - within CA
            ServiceMethod.FAX_SERVICE: 2,
            ServiceMethod.OVERNIGHT_DELIVERY: 2,
        }
        return extensions.get(self.service_method, 0)

    def to_dict(self) -> dict:
        return {
            'party_id': self.party_id,
            'party_name': self.party_name,
            'service_method': self.service_method.value,
            'service_date': self.service_date.isoformat(),
            'service_address': self.service_address,
            'service_email': self.service_email,
            'onelegal_confirmation': self.onelegal_confirmation,
            'proof_of_service_filed': self.proof_of_service_filed,
            'notes': self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ServiceRecord':
        return cls(
            party_id=data['party_id'],
            party_name=data['party_name'],
            service_method=ServiceMethod(data['service_method']),
            service_date=date.fromisoformat(data['service_date']),
            service_address=data.get('service_address'),
            service_email=data.get('service_email'),
            onelegal_confirmation=data.get('onelegal_confirmation'),
            proof_of_service_filed=data.get('proof_of_service_filed', False),
            notes=data.get('notes'),
        )


@dataclass
class Document:
    """
    Represents a court document in a California case.

    Tracks filing information, service records, and generates
    related deadlines based on document type.
    """
    title: str
    document_type: DocumentType
    case_id: str

    # Optional fields
    id: str = field(default_factory=lambda: str(uuid4()))
    status: DocumentStatus = DocumentStatus.DRAFT

    # Filing information
    filing_date: Optional[date] = None
    filed_by_party_id: Optional[str] = None
    filed_by_party_name: Optional[str] = None
    court_filing_number: Optional[str] = None
    roa_entry_number: Optional[str] = None  # Register of Actions entry

    # Content details
    page_count: Optional[int] = None
    exhibits: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)

    # Hearing association
    hearing_date: Optional[date] = None
    hearing_time: Optional[str] = None
    department: Optional[str] = None

    # Service records
    service_records: List[ServiceRecord] = field(default_factory=list)

    # Response tracking
    requires_response: bool = False
    response_deadline: Optional[date] = None
    response_document_id: Optional[str] = None

    # OneLegal specific
    onelegal_transaction_id: Optional[str] = None
    onelegal_status: Optional[str] = None

    # File reference
    file_path: Optional[str] = None
    url: Optional[str] = None

    # Metadata
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def mark_filed(self, filing_date: date, filing_number: Optional[str] = None) -> None:
        """Mark document as filed with the court."""
        self.filing_date = filing_date
        self.court_filing_number = filing_number
        if self.status == DocumentStatus.SERVED:
            self.status = DocumentStatus.FILED_AND_SERVED
        else:
            self.status = DocumentStatus.FILED
        self.updated_at = datetime.now()

    def add_service_record(self, record: ServiceRecord) -> None:
        """Add a service record for this document."""
        self.service_records.append(record)
        if self.status == DocumentStatus.FILED:
            self.status = DocumentStatus.FILED_AND_SERVED
        elif self.status == DocumentStatus.DRAFT:
            self.status = DocumentStatus.SERVED
        self.updated_at = datetime.now()

    def get_service_date(self) -> Optional[date]:
        """Get the earliest service date."""
        if self.service_records:
            return min(r.service_date for r in self.service_records)
        return None

    def get_max_service_extension(self) -> int:
        """Get the maximum service extension days from all service records."""
        if self.service_records:
            return max(r.get_service_extension_days() for r in self.service_records)
        return 0

    def is_motion(self) -> bool:
        """Check if this document is a motion type."""
        motion_types = {
            DocumentType.MOTION,
            DocumentType.MOTION_TO_COMPEL,
            DocumentType.MOTION_FOR_SUMMARY_JUDGMENT,
            DocumentType.MOTION_FOR_SUMMARY_ADJUDICATION,
            DocumentType.MOTION_TO_DISMISS,
            DocumentType.MOTION_IN_LIMINE,
            DocumentType.EX_PARTE_APPLICATION,
            DocumentType.DEMURRER,
        }
        return self.document_type in motion_types

    def is_discovery(self) -> bool:
        """Check if this document is a discovery request."""
        discovery_types = {
            DocumentType.INTERROGATORIES,
            DocumentType.REQUESTS_FOR_PRODUCTION,
            DocumentType.REQUESTS_FOR_ADMISSION,
            DocumentType.DEPOSITION_NOTICE,
            DocumentType.SUBPOENA,
        }
        return self.document_type in discovery_types

    def get_response_deadline_days(self) -> Optional[int]:
        """
        Get the number of days to respond based on document type.
        Based on California Code of Civil Procedure.
        """
        # Discovery response deadlines (CCP 2030.260, 2031.260, 2033.250)
        discovery_deadlines = {
            DocumentType.INTERROGATORIES: 30,
            DocumentType.REQUESTS_FOR_PRODUCTION: 30,
            DocumentType.REQUESTS_FOR_ADMISSION: 30,
            DocumentType.DEPOSITION_NOTICE: 20,  # Objection deadline
        }

        # Motion response deadlines
        motion_deadlines = {
            DocumentType.MOTION: 9,  # Opposition due 9 court days before hearing
            DocumentType.MOTION_TO_COMPEL: 9,
            DocumentType.MOTION_FOR_SUMMARY_JUDGMENT: 14,  # Opposition due 14 days before hearing
            DocumentType.MOTION_FOR_SUMMARY_ADJUDICATION: 14,
            DocumentType.DEMURRER: 9,
            DocumentType.EX_PARTE_APPLICATION: 1,  # Notice requirement
        }

        # Pleading deadlines
        pleading_deadlines = {
            DocumentType.COMPLAINT: 30,  # Answer due 30 days after service
            DocumentType.CROSS_COMPLAINT: 30,
            DocumentType.AMENDED_COMPLAINT: 30,
        }

        if self.document_type in discovery_deadlines:
            return discovery_deadlines[self.document_type]
        elif self.document_type in motion_deadlines:
            return motion_deadlines[self.document_type]
        elif self.document_type in pleading_deadlines:
            return pleading_deadlines[self.document_type]

        return None

    def to_dict(self) -> dict:
        """Convert document to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'document_type': self.document_type.value,
            'case_id': self.case_id,
            'status': self.status.value,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'filed_by_party_id': self.filed_by_party_id,
            'filed_by_party_name': self.filed_by_party_name,
            'court_filing_number': self.court_filing_number,
            'roa_entry_number': self.roa_entry_number,
            'page_count': self.page_count,
            'exhibits': self.exhibits,
            'attachments': self.attachments,
            'hearing_date': self.hearing_date.isoformat() if self.hearing_date else None,
            'hearing_time': self.hearing_time,
            'department': self.department,
            'service_records': [r.to_dict() for r in self.service_records],
            'requires_response': self.requires_response,
            'response_deadline': self.response_deadline.isoformat() if self.response_deadline else None,
            'response_document_id': self.response_document_id,
            'onelegal_transaction_id': self.onelegal_transaction_id,
            'onelegal_status': self.onelegal_status,
            'file_path': self.file_path,
            'url': self.url,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Document':
        """Create Document from dictionary."""
        service_records = [ServiceRecord.from_dict(r) for r in data.get('service_records', [])]
        return cls(
            id=data.get('id', str(uuid4())),
            title=data['title'],
            document_type=DocumentType(data['document_type']),
            case_id=data['case_id'],
            status=DocumentStatus(data.get('status', 'draft')),
            filing_date=date.fromisoformat(data['filing_date']) if data.get('filing_date') else None,
            filed_by_party_id=data.get('filed_by_party_id'),
            filed_by_party_name=data.get('filed_by_party_name'),
            court_filing_number=data.get('court_filing_number'),
            roa_entry_number=data.get('roa_entry_number'),
            page_count=data.get('page_count'),
            exhibits=data.get('exhibits', []),
            attachments=data.get('attachments', []),
            hearing_date=date.fromisoformat(data['hearing_date']) if data.get('hearing_date') else None,
            hearing_time=data.get('hearing_time'),
            department=data.get('department'),
            service_records=service_records,
            requires_response=data.get('requires_response', False),
            response_deadline=date.fromisoformat(data['response_deadline']) if data.get('response_deadline') else None,
            response_document_id=data.get('response_document_id'),
            onelegal_transaction_id=data.get('onelegal_transaction_id'),
            onelegal_status=data.get('onelegal_status'),
            file_path=data.get('file_path'),
            url=data.get('url'),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
        )

    def __repr__(self) -> str:
        return f"Document({self.title}, {self.document_type.value})"
