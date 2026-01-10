"""Party model for California court cases."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class PartyType(Enum):
    """Types of parties in a case."""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    CROSS_COMPLAINANT = "cross_complainant"
    CROSS_DEFENDANT = "cross_defendant"
    INTERVENOR = "intervenor"
    REAL_PARTY_IN_INTEREST = "real_party_in_interest"
    CLAIMANT = "claimant"
    JUDGMENT_CREDITOR = "judgment_creditor"
    JUDGMENT_DEBTOR = "judgment_debtor"
    THIRD_PARTY = "third_party"
    OTHER = "other"


class PartyRole(Enum):
    """Role of party in case (for service purposes)."""
    MOVING_PARTY = "moving_party"
    RESPONDING_PARTY = "responding_party"
    OPPOSING_PARTY = "opposing_party"
    JOINED_PARTY = "joined_party"


@dataclass
class Attorney:
    """Attorney representing a party."""
    name: str
    bar_number: Optional[str] = None
    firm_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: str = "CA"
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    is_lead_counsel: bool = False

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'bar_number': self.bar_number,
            'firm_name': self.firm_name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone': self.phone,
            'fax': self.fax,
            'email': self.email,
            'is_lead_counsel': self.is_lead_counsel,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Attorney':
        return cls(**data)


@dataclass
class Party:
    """
    Represents a party in a California court case.

    Tracks party information, attorneys, and service details.
    """
    name: str
    party_type: PartyType

    # Optional fields
    id: str = field(default_factory=lambda: str(uuid4()))
    case_id: Optional[str] = None
    is_entity: bool = False  # True for corporations, LLCs, etc.
    entity_type: Optional[str] = None  # Corporation, LLC, Partnership, etc.

    # Contact information
    address: Optional[str] = None
    city: Optional[str] = None
    state: str = "CA"
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    # Representation
    is_self_represented: bool = False
    attorneys: List[Attorney] = field(default_factory=list)

    # Service information
    service_address: Optional[str] = None
    service_email: Optional[str] = None
    accepts_electronic_service: bool = False
    onelegal_id: Optional[str] = None  # For OneLegal service tracking

    # Status
    is_active: bool = True
    date_added: Optional[datetime] = None
    date_dismissed: Optional[datetime] = None

    # Metadata
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.date_added is None:
            self.date_added = datetime.now()

    def add_attorney(self, attorney: Attorney) -> None:
        """Add an attorney to represent this party."""
        self.attorneys.append(attorney)
        self.is_self_represented = False
        self.updated_at = datetime.now()

    def remove_attorney(self, attorney_name: str) -> bool:
        """Remove an attorney by name."""
        for i, atty in enumerate(self.attorneys):
            if atty.name == attorney_name:
                self.attorneys.pop(i)
                if not self.attorneys:
                    self.is_self_represented = True
                self.updated_at = datetime.now()
                return True
        return False

    def get_lead_counsel(self) -> Optional[Attorney]:
        """Get the lead counsel for this party."""
        for atty in self.attorneys:
            if atty.is_lead_counsel:
                return atty
        return self.attorneys[0] if self.attorneys else None

    def get_service_address(self) -> Optional[str]:
        """Get the address for service of process."""
        if self.service_address:
            return self.service_address
        lead_counsel = self.get_lead_counsel()
        if lead_counsel and lead_counsel.address:
            return f"{lead_counsel.address}, {lead_counsel.city}, {lead_counsel.state} {lead_counsel.zip_code}"
        if self.address:
            return f"{self.address}, {self.city}, {self.state} {self.zip_code}"
        return None

    def get_service_email(self) -> Optional[str]:
        """Get email for electronic service."""
        if self.service_email:
            return self.service_email
        lead_counsel = self.get_lead_counsel()
        if lead_counsel and lead_counsel.email:
            return lead_counsel.email
        return self.email

    def dismiss(self) -> None:
        """Mark party as dismissed from case."""
        self.is_active = False
        self.date_dismissed = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert party to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'party_type': self.party_type.value,
            'case_id': self.case_id,
            'is_entity': self.is_entity,
            'entity_type': self.entity_type,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone': self.phone,
            'email': self.email,
            'is_self_represented': self.is_self_represented,
            'attorneys': [a.to_dict() for a in self.attorneys],
            'service_address': self.service_address,
            'service_email': self.service_email,
            'accepts_electronic_service': self.accepts_electronic_service,
            'onelegal_id': self.onelegal_id,
            'is_active': self.is_active,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'date_dismissed': self.date_dismissed.isoformat() if self.date_dismissed else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Party':
        """Create Party from dictionary."""
        attorneys = [Attorney.from_dict(a) for a in data.get('attorneys', [])]
        return cls(
            id=data.get('id', str(uuid4())),
            name=data['name'],
            party_type=PartyType(data['party_type']),
            case_id=data.get('case_id'),
            is_entity=data.get('is_entity', False),
            entity_type=data.get('entity_type'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state', 'CA'),
            zip_code=data.get('zip_code'),
            phone=data.get('phone'),
            email=data.get('email'),
            is_self_represented=data.get('is_self_represented', False),
            attorneys=attorneys,
            service_address=data.get('service_address'),
            service_email=data.get('service_email'),
            accepts_electronic_service=data.get('accepts_electronic_service', False),
            onelegal_id=data.get('onelegal_id'),
            is_active=data.get('is_active', True),
            date_added=datetime.fromisoformat(data['date_added']) if data.get('date_added') else None,
            date_dismissed=datetime.fromisoformat(data['date_dismissed']) if data.get('date_dismissed') else None,
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
        )

    def __repr__(self) -> str:
        return f"Party({self.name}, {self.party_type.value})"
