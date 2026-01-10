"""
OneLegal Service Tracker

Tracks documents served via OneLegal electronic service platform
in California civil cases.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Optional, List, Dict
from uuid import uuid4
from enum import Enum

from ..models.document import Document, ServiceMethod, ServiceRecord
from ..models.party import Party


class OneLegalStatus(Enum):
    """Status of OneLegal service transaction."""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class OneLegalServiceType(Enum):
    """Types of OneLegal service."""
    E_SERVICE = "e_service"  # Electronic service
    E_FILE = "e_file"  # Electronic filing
    E_FILE_AND_SERVE = "e_file_and_serve"
    COURTESY_COPY = "courtesy_copy"


@dataclass
class OneLegalTransaction:
    """
    Represents a OneLegal service transaction.

    Tracks electronic service of documents through OneLegal platform.
    """
    transaction_id: str
    document_id: str
    case_id: str
    service_type: OneLegalServiceType

    id: str = field(default_factory=lambda: str(uuid4()))
    status: OneLegalStatus = OneLegalStatus.PENDING

    # Timing
    submitted_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None

    # Service details
    service_date: Optional[date] = None
    service_time: Optional[time] = None

    # Recipients
    recipients: List[str] = field(default_factory=list)  # Email addresses
    recipient_party_ids: List[str] = field(default_factory=list)

    # Document details
    document_title: str = ""
    document_pages: Optional[int] = None
    file_size_bytes: Optional[int] = None

    # Confirmation
    confirmation_number: Optional[str] = None
    proof_of_service_url: Optional[str] = None

    # Cost
    service_fee: Optional[float] = None
    filing_fee: Optional[float] = None
    total_cost: Optional[float] = None

    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0

    # Metadata
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def mark_sent(self) -> None:
        """Mark transaction as sent."""
        self.status = OneLegalStatus.SENT
        self.sent_at = datetime.now()
        if self.service_date is None:
            self.service_date = date.today()
        self.updated_at = datetime.now()

    def mark_delivered(self) -> None:
        """Mark transaction as delivered."""
        self.status = OneLegalStatus.DELIVERED
        self.delivered_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_opened(self) -> None:
        """Mark transaction as opened by recipient."""
        self.status = OneLegalStatus.OPENED
        self.opened_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_failed(self, error_message: str) -> None:
        """Mark transaction as failed."""
        self.status = OneLegalStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now()

    def get_service_date(self) -> Optional[date]:
        """Get the effective service date."""
        if self.service_date:
            return self.service_date
        if self.sent_at:
            return self.sent_at.date()
        return None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'document_id': self.document_id,
            'case_id': self.case_id,
            'service_type': self.service_type.value,
            'status': self.status.value,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'service_date': self.service_date.isoformat() if self.service_date else None,
            'service_time': self.service_time.isoformat() if self.service_time else None,
            'recipients': self.recipients,
            'recipient_party_ids': self.recipient_party_ids,
            'document_title': self.document_title,
            'document_pages': self.document_pages,
            'file_size_bytes': self.file_size_bytes,
            'confirmation_number': self.confirmation_number,
            'proof_of_service_url': self.proof_of_service_url,
            'service_fee': self.service_fee,
            'filing_fee': self.filing_fee,
            'total_cost': self.total_cost,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'OneLegalTransaction':
        return cls(
            id=data.get('id', str(uuid4())),
            transaction_id=data['transaction_id'],
            document_id=data['document_id'],
            case_id=data['case_id'],
            service_type=OneLegalServiceType(data['service_type']),
            status=OneLegalStatus(data.get('status', 'pending')),
            submitted_at=datetime.fromisoformat(data['submitted_at']) if data.get('submitted_at') else None,
            sent_at=datetime.fromisoformat(data['sent_at']) if data.get('sent_at') else None,
            delivered_at=datetime.fromisoformat(data['delivered_at']) if data.get('delivered_at') else None,
            opened_at=datetime.fromisoformat(data['opened_at']) if data.get('opened_at') else None,
            service_date=date.fromisoformat(data['service_date']) if data.get('service_date') else None,
            service_time=time.fromisoformat(data['service_time']) if data.get('service_time') else None,
            recipients=data.get('recipients', []),
            recipient_party_ids=data.get('recipient_party_ids', []),
            document_title=data.get('document_title', ''),
            document_pages=data.get('document_pages'),
            file_size_bytes=data.get('file_size_bytes'),
            confirmation_number=data.get('confirmation_number'),
            proof_of_service_url=data.get('proof_of_service_url'),
            service_fee=data.get('service_fee'),
            filing_fee=data.get('filing_fee'),
            total_cost=data.get('total_cost'),
            error_message=data.get('error_message'),
            retry_count=data.get('retry_count', 0),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
        )


class OneLegalTracker:
    """
    Manages OneLegal service transactions for California court cases.

    Provides functionality to:
    - Track e-service transactions
    - Record service dates for deadline calculations
    - Generate proof of service records
    - Track service costs
    - Monitor delivery status
    """

    # OneLegal electronic service adds 2 court days per CCP 1010.6
    SERVICE_EXTENSION_DAYS = 2

    def __init__(self):
        """Initialize the OneLegal tracker."""
        self.transactions: Dict[str, OneLegalTransaction] = {}  # id -> Transaction
        self.case_transactions: Dict[str, List[str]] = {}  # case_id -> [transaction_ids]
        self.document_transactions: Dict[str, List[str]] = {}  # document_id -> [transaction_ids]

    def add_transaction(self, transaction: OneLegalTransaction) -> OneLegalTransaction:
        """Add a transaction to the tracker."""
        self.transactions[transaction.id] = transaction

        # Index by case
        if transaction.case_id not in self.case_transactions:
            self.case_transactions[transaction.case_id] = []
        self.case_transactions[transaction.case_id].append(transaction.id)

        # Index by document
        if transaction.document_id not in self.document_transactions:
            self.document_transactions[transaction.document_id] = []
        self.document_transactions[transaction.document_id].append(transaction.id)

        return transaction

    def create_transaction(self, transaction_id: str, document_id: str, case_id: str,
                           service_type: OneLegalServiceType = OneLegalServiceType.E_SERVICE,
                           **kwargs) -> OneLegalTransaction:
        """Create and add a new OneLegal transaction."""
        transaction = OneLegalTransaction(
            transaction_id=transaction_id,
            document_id=document_id,
            case_id=case_id,
            service_type=service_type,
            submitted_at=datetime.now(),
            **kwargs
        )
        return self.add_transaction(transaction)

    def get_transaction(self, transaction_id: str) -> Optional[OneLegalTransaction]:
        """Get a transaction by ID."""
        return self.transactions.get(transaction_id)

    def get_transaction_by_onelegal_id(self, onelegal_transaction_id: str) -> Optional[OneLegalTransaction]:
        """Get a transaction by OneLegal transaction ID."""
        for txn in self.transactions.values():
            if txn.transaction_id == onelegal_transaction_id:
                return txn
        return None

    def get_case_transactions(self, case_id: str) -> List[OneLegalTransaction]:
        """Get all transactions for a case."""
        txn_ids = self.case_transactions.get(case_id, [])
        return [self.transactions[tid] for tid in txn_ids if tid in self.transactions]

    def get_document_transactions(self, document_id: str) -> List[OneLegalTransaction]:
        """Get all transactions for a document."""
        txn_ids = self.document_transactions.get(document_id, [])
        return [self.transactions[tid] for tid in txn_ids if tid in self.transactions]

    def get_pending_transactions(self, case_id: str) -> List[OneLegalTransaction]:
        """Get pending transactions for a case."""
        transactions = self.get_case_transactions(case_id)
        return [t for t in transactions if t.status in [OneLegalStatus.PENDING, OneLegalStatus.PROCESSING]]

    def get_failed_transactions(self, case_id: str) -> List[OneLegalTransaction]:
        """Get failed transactions for a case."""
        transactions = self.get_case_transactions(case_id)
        return [t for t in transactions if t.status == OneLegalStatus.FAILED]

    def update_transaction_status(self, transaction_id: str, status: OneLegalStatus,
                                   confirmation_number: Optional[str] = None,
                                   error_message: Optional[str] = None) -> bool:
        """Update the status of a transaction."""
        txn = self.transactions.get(transaction_id)
        if not txn:
            return False

        txn.status = status
        txn.updated_at = datetime.now()

        if confirmation_number:
            txn.confirmation_number = confirmation_number

        if status == OneLegalStatus.SENT:
            txn.mark_sent()
        elif status == OneLegalStatus.DELIVERED:
            txn.mark_delivered()
        elif status == OneLegalStatus.OPENED:
            txn.mark_opened()
        elif status == OneLegalStatus.FAILED:
            txn.mark_failed(error_message or "Unknown error")

        return True

    def create_service_record_from_transaction(self, transaction: OneLegalTransaction,
                                                party_id: str,
                                                party_name: str) -> Optional[ServiceRecord]:
        """Create a ServiceRecord from a completed OneLegal transaction."""
        if transaction.status not in [OneLegalStatus.SENT, OneLegalStatus.DELIVERED, OneLegalStatus.OPENED]:
            return None

        service_date = transaction.get_service_date()
        if not service_date:
            return None

        return ServiceRecord(
            party_id=party_id,
            party_name=party_name,
            service_method=ServiceMethod.ONELEGAL,
            service_date=service_date,
            service_email=transaction.recipients[0] if transaction.recipients else None,
            onelegal_confirmation=transaction.confirmation_number,
            proof_of_service_filed=transaction.proof_of_service_url is not None
        )

    def record_service_on_document(self, document: Document, transaction: OneLegalTransaction,
                                    parties: List[Party]) -> List[ServiceRecord]:
        """
        Record service on a document based on OneLegal transaction.

        Returns list of created service records.
        """
        service_records = []

        for party in parties:
            if party.id in transaction.recipient_party_ids or \
               (party.service_email and party.service_email in transaction.recipients):
                record = self.create_service_record_from_transaction(
                    transaction, party.id, party.name
                )
                if record:
                    document.add_service_record(record)
                    service_records.append(record)

        # Update document with OneLegal info
        document.onelegal_transaction_id = transaction.transaction_id
        document.onelegal_status = transaction.status.value

        return service_records

    def get_service_statistics(self, case_id: str) -> dict:
        """Get service statistics for a case."""
        transactions = self.get_case_transactions(case_id)

        stats = {
            'total_transactions': len(transactions),
            'successful': 0,
            'pending': 0,
            'failed': 0,
            'total_cost': 0.0,
            'by_type': {},
            'by_status': {},
            'documents_served': set(),
        }

        for txn in transactions:
            # Count by status category
            if txn.status in [OneLegalStatus.SENT, OneLegalStatus.DELIVERED, OneLegalStatus.OPENED]:
                stats['successful'] += 1
            elif txn.status in [OneLegalStatus.PENDING, OneLegalStatus.PROCESSING]:
                stats['pending'] += 1
            elif txn.status in [OneLegalStatus.FAILED, OneLegalStatus.REJECTED]:
                stats['failed'] += 1

            # Sum costs
            if txn.total_cost:
                stats['total_cost'] += txn.total_cost

            # Count by type
            type_name = txn.service_type.value
            stats['by_type'][type_name] = stats['by_type'].get(type_name, 0) + 1

            # Count by status
            status_name = txn.status.value
            stats['by_status'][status_name] = stats['by_status'].get(status_name, 0) + 1

            # Track documents
            stats['documents_served'].add(txn.document_id)

        stats['documents_served'] = len(stats['documents_served'])

        return stats

    def generate_service_report(self, case_id: str) -> str:
        """Generate a OneLegal service report for a case."""
        transactions = self.get_case_transactions(case_id)

        if not transactions:
            return f"No OneLegal transactions for case {case_id}"

        lines = [
            "ONELEGAL SERVICE REPORT",
            "=" * 70,
            f"Case ID: {case_id}",
            f"Generated: {datetime.now().strftime('%m/%d/%Y %H:%M')}",
            "",
        ]

        # Statistics
        stats = self.get_service_statistics(case_id)
        lines.extend([
            "SUMMARY:",
            f"  Total Transactions: {stats['total_transactions']}",
            f"  Successful: {stats['successful']}",
            f"  Pending: {stats['pending']}",
            f"  Failed: {stats['failed']}",
            f"  Total Cost: ${stats['total_cost']:.2f}",
            "",
        ])

        # Recent transactions
        recent = sorted(transactions, key=lambda t: t.created_at, reverse=True)[:10]

        lines.extend([
            "RECENT TRANSACTIONS:",
            "-" * 70,
        ])

        for txn in recent:
            date_str = txn.created_at.strftime('%m/%d/%Y %H:%M')
            status = txn.status.value.upper()
            lines.append(f"  {date_str}  [{status}]")
            lines.append(f"      Transaction: {txn.transaction_id}")
            lines.append(f"      Document: {txn.document_title}")
            lines.append(f"      Recipients: {len(txn.recipients)}")
            if txn.confirmation_number:
                lines.append(f"      Confirmation: {txn.confirmation_number}")
            if txn.error_message:
                lines.append(f"      Error: {txn.error_message}")
            lines.append("")

        # Failed transactions needing attention
        failed = self.get_failed_transactions(case_id)
        if failed:
            lines.extend([
                "FAILED TRANSACTIONS (NEED ATTENTION):",
                "-" * 70,
            ])
            for txn in failed:
                lines.append(f"  {txn.transaction_id}: {txn.error_message}")

        lines.append("=" * 70)

        return '\n'.join(lines)

    def export_transactions(self, case_id: str) -> List[dict]:
        """Export all transactions for a case."""
        transactions = self.get_case_transactions(case_id)
        return [t.to_dict() for t in transactions]

    def import_transaction(self, txn_data: dict) -> OneLegalTransaction:
        """Import a transaction from dict."""
        transaction = OneLegalTransaction.from_dict(txn_data)
        return self.add_transaction(transaction)

    def get_proof_of_service_urls(self, document_id: str) -> List[str]:
        """Get all proof of service URLs for a document."""
        transactions = self.get_document_transactions(document_id)
        return [t.proof_of_service_url for t in transactions if t.proof_of_service_url]

    def calculate_service_date(self, transaction: OneLegalTransaction) -> Optional[date]:
        """
        Calculate the effective service date for deadline purposes.

        Per CCP 1010.6(a)(3)(B), electronic service after 11:59 PM
        is deemed served the next day.
        """
        if transaction.sent_at:
            # If sent before midnight, service date is that day
            # If sent at/after midnight (which shouldn't happen), next day
            service_date = transaction.sent_at.date()

            # Check if service time is after court business hours (typically 5 PM)
            # Some courts consider service after 5 PM as next day service
            if transaction.service_time and transaction.service_time >= time(17, 0):
                # Optional: some practices treat late service as next day
                pass

            return service_date
        return transaction.service_date

    def get_service_extension_days(self) -> int:
        """Get the deadline extension days for OneLegal service."""
        return self.SERVICE_EXTENSION_DAYS
