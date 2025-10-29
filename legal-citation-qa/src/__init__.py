"""
Legal Citation QA System

Automated citation and quote validation for legal briefs.
"""

__version__ = "1.0.0"
__author__ = "Legal Citation QA Project"

from .citation_extractor import CitationExtractor, ExtractedCitation, QuoteContext
from .courtlistener_client import CourtListenerClient, OpinionMetadata, OpinionText
from .quote_matcher import QuoteMatcher, QuoteMatch, MatchResult
from .parallel_checker import ParallelCitationChecker, ParallelCitationCheck
from .text_extractor import TextExtractor
from .report_generator import ReportGenerator
from .box_handler import BoxHandler
from .git_audit import GitAuditTrail
from .worker import CitationQAWorker

__all__ = [
    # Main worker
    "CitationQAWorker",

    # Citation extraction
    "CitationExtractor",
    "ExtractedCitation",
    "QuoteContext",

    # CourtListener
    "CourtListenerClient",
    "OpinionMetadata",
    "OpinionText",

    # Quote matching
    "QuoteMatcher",
    "QuoteMatch",
    "MatchResult",

    # Parallel citations
    "ParallelCitationChecker",
    "ParallelCitationCheck",

    # Text extraction
    "TextExtractor",

    # Reports
    "ReportGenerator",

    # Integrations
    "BoxHandler",
    "GitAuditTrail",
]
