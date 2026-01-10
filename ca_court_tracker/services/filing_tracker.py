"""
Court Filing Tracker

Tracks court filings for California civil cases including
documents filed, service records, and response deadlines.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Tuple
from uuid import uuid4

from ..models.document import Document, DocumentType, DocumentStatus, ServiceMethod, ServiceRecord
from ..models.deadline import Deadline, DeadlineType, DeadlinePriority
from .deadline_calculator import DeadlineCalculator


class FilingTracker:
    """
    Manages court filings for California civil cases.

    Provides functionality to:
    - Track all documents filed in a case
    - Record service of documents
    - Calculate response deadlines
    - Track pending responses
    - Generate filing reports
    """

    def __init__(self):
        """Initialize the filing tracker."""
        self.documents: Dict[str, Document] = {}  # doc_id -> Document
        self.case_documents: Dict[str, List[str]] = {}  # case_id -> [doc_ids]
        self.deadline_calculator = DeadlineCalculator()

    def add_document(self, document: Document) -> Document:
        """Add a document to the tracker."""
        self.documents[document.id] = document

        if document.case_id not in self.case_documents:
            self.case_documents[document.case_id] = []
        self.case_documents[document.case_id].append(document.id)

        return document

    def create_document(self, title: str, document_type: DocumentType,
                        case_id: str, **kwargs) -> Document:
        """Create and add a new document."""
        document = Document(
            title=title,
            document_type=document_type,
            case_id=case_id,
            **kwargs
        )
        return self.add_document(document)

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self.documents.get(document_id)

    def get_case_documents(self, case_id: str) -> List[Document]:
        """Get all documents for a case, sorted by filing date."""
        doc_ids = self.case_documents.get(case_id, [])
        docs = [self.documents[did] for did in doc_ids if did in self.documents]
        return sorted(docs, key=lambda d: d.filing_date or date.min, reverse=True)

    def get_documents_by_type(self, case_id: str, doc_type: DocumentType) -> List[Document]:
        """Get documents of a specific type for a case."""
        docs = self.get_case_documents(case_id)
        return [d for d in docs if d.document_type == doc_type]

    def get_documents_by_party(self, case_id: str, party_id: str) -> List[Document]:
        """Get documents filed by a specific party."""
        docs = self.get_case_documents(case_id)
        return [d for d in docs if d.filed_by_party_id == party_id]

    def get_recent_filings(self, case_id: str, limit: int = 10) -> List[Document]:
        """Get the most recent filings for a case."""
        docs = self.get_case_documents(case_id)
        filed = [d for d in docs if d.filing_date is not None]
        return sorted(filed, key=lambda d: d.filing_date, reverse=True)[:limit]

    def file_document(self, document_id: str, filing_date: date,
                      filing_number: Optional[str] = None) -> bool:
        """Mark a document as filed with the court."""
        document = self.documents.get(document_id)
        if document:
            document.mark_filed(filing_date, filing_number)
            return True
        return False

    def serve_document(self, document_id: str, party_id: str, party_name: str,
                       service_method: ServiceMethod, service_date: date,
                       service_address: Optional[str] = None,
                       service_email: Optional[str] = None,
                       onelegal_confirmation: Optional[str] = None) -> Optional[ServiceRecord]:
        """Record service of a document on a party."""
        document = self.documents.get(document_id)
        if not document:
            return None

        record = ServiceRecord(
            party_id=party_id,
            party_name=party_name,
            service_method=service_method,
            service_date=service_date,
            service_address=service_address,
            service_email=service_email,
            onelegal_confirmation=onelegal_confirmation
        )

        document.add_service_record(record)
        return record

    def get_pending_service(self, case_id: str) -> List[Document]:
        """Get documents that are filed but not yet served."""
        docs = self.get_case_documents(case_id)
        return [d for d in docs
                if d.status == DocumentStatus.FILED and not d.service_records]

    def get_documents_requiring_response(self, case_id: str,
                                          responding_party_id: Optional[str] = None) -> List[Document]:
        """Get documents that require a response."""
        docs = self.get_case_documents(case_id)
        requiring_response = []

        for doc in docs:
            if doc.requires_response or doc.is_discovery() or \
               doc.document_type in [DocumentType.COMPLAINT, DocumentType.CROSS_COMPLAINT,
                                     DocumentType.AMENDED_COMPLAINT, DocumentType.DEMURRER]:
                # Check if already responded
                if doc.response_document_id is None:
                    requiring_response.append(doc)

        return requiring_response

    def calculate_response_deadline(self, document: Document,
                                     service_method: Optional[ServiceMethod] = None,
                                     service_date: Optional[date] = None) -> Optional[date]:
        """Calculate the response deadline for a document."""
        # Use provided values or get from document service records
        if service_method is None or service_date is None:
            if document.service_records:
                record = document.service_records[0]
                service_method = service_method or record.service_method
                service_date = service_date or record.service_date
            else:
                return None

        return self.deadline_calculator.calculate_response_deadline(
            document, service_method, service_date
        )

    def create_response_deadline(self, document: Document,
                                  responsible_party_id: str,
                                  responsible_party_name: str,
                                  service_method: Optional[ServiceMethod] = None,
                                  service_date: Optional[date] = None) -> Optional[Deadline]:
        """Create a deadline object for responding to a document."""
        # Get service info
        if service_method is None or service_date is None:
            if document.service_records:
                record = document.service_records[0]
                service_method = service_method or record.service_method
                service_date = service_date or record.service_date
            else:
                return None

        deadline = self.deadline_calculator.create_deadline_from_document(
            document=document,
            service_date=service_date,
            service_method=service_method,
            responsible_party_id=responsible_party_id,
            responsible_party_name=responsible_party_name
        )

        if deadline:
            document.requires_response = True
            document.response_deadline = deadline.due_date

        return deadline

    def link_response(self, original_doc_id: str, response_doc_id: str) -> bool:
        """Link a response document to the original document."""
        original = self.documents.get(original_doc_id)
        response = self.documents.get(response_doc_id)

        if original and response:
            original.response_document_id = response_doc_id
            response.response_to_document_id = original_doc_id
            return True
        return False

    def get_motion_documents(self, case_id: str, include_responses: bool = True) -> List[Document]:
        """Get all motion-related documents for a case."""
        docs = self.get_case_documents(case_id)
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

        if include_responses:
            motion_types.update({DocumentType.OPPOSITION, DocumentType.REPLY})

        return [d for d in docs if d.document_type in motion_types]

    def get_discovery_documents(self, case_id: str) -> List[Document]:
        """Get all discovery documents for a case."""
        docs = self.get_case_documents(case_id)
        return [d for d in docs if d.is_discovery()]

    def get_filing_statistics(self, case_id: str) -> dict:
        """Get filing statistics for a case."""
        docs = self.get_case_documents(case_id)

        stats = {
            'total_documents': len(docs),
            'filed': 0,
            'served': 0,
            'pending_response': 0,
            'motions': 0,
            'discovery': 0,
            'by_type': {},
            'by_party': {},
            'by_month': {},
        }

        for doc in docs:
            # Count by status
            if doc.status in [DocumentStatus.FILED, DocumentStatus.FILED_AND_SERVED]:
                stats['filed'] += 1
            if doc.status in [DocumentStatus.SERVED, DocumentStatus.FILED_AND_SERVED]:
                stats['served'] += 1

            # Count pending responses
            if doc.requires_response and doc.response_document_id is None:
                stats['pending_response'] += 1

            # Count by category
            if doc.is_motion():
                stats['motions'] += 1
            if doc.is_discovery():
                stats['discovery'] += 1

            # Count by type
            type_name = doc.document_type.value
            stats['by_type'][type_name] = stats['by_type'].get(type_name, 0) + 1

            # Count by party
            if doc.filed_by_party_name:
                stats['by_party'][doc.filed_by_party_name] = \
                    stats['by_party'].get(doc.filed_by_party_name, 0) + 1

            # Count by month
            if doc.filing_date:
                month_key = doc.filing_date.strftime('%Y-%m')
                stats['by_month'][month_key] = stats['by_month'].get(month_key, 0) + 1

        return stats

    def generate_filing_report(self, case_id: str) -> str:
        """Generate a filing report for a case."""
        docs = self.get_case_documents(case_id)

        if not docs:
            return f"No documents found for case {case_id}"

        lines = [
            "COURT FILINGS REPORT",
            "=" * 70,
            f"Case ID: {case_id}",
            f"Generated: {datetime.now().strftime('%m/%d/%Y %H:%M')}",
            f"Total Documents: {len(docs)}",
            "",
            "RECENT FILINGS:",
            "-" * 70,
        ]

        # Recent filings
        recent = self.get_recent_filings(case_id, 10)
        for doc in recent:
            date_str = doc.filing_date.strftime('%m/%d/%Y') if doc.filing_date else 'Not filed'
            status = doc.status.value.upper()
            lines.append(f"  {date_str}  [{status}] {doc.title}")
            if doc.filed_by_party_name:
                lines.append(f"              Filed by: {doc.filed_by_party_name}")

        # Pending responses
        pending = self.get_documents_requiring_response(case_id)
        if pending:
            lines.extend([
                "",
                "PENDING RESPONSES:",
                "-" * 70,
            ])
            for doc in pending:
                deadline = "Unknown"
                if doc.response_deadline:
                    days = (doc.response_deadline - date.today()).days
                    deadline = f"{doc.response_deadline.strftime('%m/%d/%Y')} ({days} days)"
                lines.append(f"  {doc.title}")
                lines.append(f"      Response Due: {deadline}")

        lines.extend(["", "=" * 70])

        return '\n'.join(lines)

    def search_documents(self, case_id: str, search_term: str) -> List[Document]:
        """Search documents by title."""
        docs = self.get_case_documents(case_id)
        search_lower = search_term.lower()
        return [d for d in docs if search_lower in d.title.lower()]

    def export_documents(self, case_id: str) -> List[dict]:
        """Export all documents for a case."""
        docs = self.get_case_documents(case_id)
        return [d.to_dict() for d in docs]

    def import_document(self, doc_data: dict) -> Document:
        """Import a document from dict."""
        document = Document.from_dict(doc_data)
        return self.add_document(document)

    def get_documents_by_date_range(self, case_id: str, start_date: date,
                                     end_date: date) -> List[Document]:
        """Get documents filed within a date range."""
        docs = self.get_case_documents(case_id)
        return [d for d in docs
                if d.filing_date and start_date <= d.filing_date <= end_date]

    def get_hearing_documents(self, case_id: str, hearing_date: date) -> List[Document]:
        """Get documents associated with a specific hearing date."""
        docs = self.get_case_documents(case_id)
        return [d for d in docs if d.hearing_date == hearing_date]
