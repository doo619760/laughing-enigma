"""
California Court Case Tracker

A comprehensive application for tracking court cases in California through:
- Register of Actions (ROA)
- Case Management Orders
- Court Filings
- Court Calendar
- Documents served via OneLegal

Includes deadline calculation based on California Code of Civil Procedure.
"""

__version__ = "1.0.0"
__author__ = "CA Court Tracker"

from .models.case import Case, CaseType, CaseStatus
from .models.party import Party, PartyType
from .models.document import Document, DocumentType, ServiceMethod
from .models.event import CourtEvent, EventType
from .models.deadline import Deadline, DeadlineType, DeadlineStatus

from .services.deadline_calculator import DeadlineCalculator
from .services.roa_tracker import ROATracker
from .services.cmo_tracker import CMOTracker
from .services.filing_tracker import FilingTracker
from .services.calendar_tracker import CalendarTracker
from .services.onelegal_tracker import OneLegalTracker
from .services.case_manager import CaseManager

__all__ = [
    'Case', 'CaseType', 'CaseStatus',
    'Party', 'PartyType',
    'Document', 'DocumentType', 'ServiceMethod',
    'CourtEvent', 'EventType',
    'Deadline', 'DeadlineType', 'DeadlineStatus',
    'DeadlineCalculator',
    'ROATracker',
    'CMOTracker',
    'FilingTracker',
    'CalendarTracker',
    'OneLegalTracker',
    'CaseManager',
]
