"""
Citation extraction module using eyecite.
Extracts and normalizes legal citations from text.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import re
import eyecite
from eyecite import get_citations, clean_text
from eyecite.models import (
    FullCaseCitation,
    ShortCaseCitation,
    SupraCitation,
    IdCitation,
    Resource,
    CitationBase
)


@dataclass
class ExtractedCitation:
    """Represents an extracted citation with metadata."""
    raw_text: str
    normalized: str
    reporter: Optional[str]
    volume: Optional[str]
    page: Optional[str]
    year: Optional[int]
    court: Optional[str]
    citation_type: str  # full, short, supra, id
    span_start: int
    span_end: int
    groups: Dict[str, str]
    metadata: Dict


@dataclass
class QuoteContext:
    """Represents a quoted passage with surrounding context."""
    quote_text: str
    span_start: int
    span_end: int
    preceding_text: str  # Text before quote (for citation context)
    following_text: str  # Text after quote
    nearby_citations: List[ExtractedCitation]
    has_ellipsis: bool
    has_brackets: bool
    has_alterations: bool


class CitationExtractor:
    """Extracts and processes legal citations from documents."""

    def __init__(self):
        self.quote_pattern = re.compile(
            r'["\u201c]([^"\u201d]+?)["\u201d]',  # Smart quotes
            re.DOTALL
        )
        self.ellipsis_pattern = re.compile(r'\.\.\.|…')
        self.bracket_pattern = re.compile(r'\[.*?\]')

    def extract_citations(self, text: str) -> List[ExtractedCitation]:
        """
        Extract all citations from the given text.

        Args:
            text: Document text to extract citations from

        Returns:
            List of ExtractedCitation objects
        """
        # Clean the text for better citation extraction
        cleaned = clean_text(text, ['all_whitespace', 'inline_whitespace'])

        # Extract citations using eyecite
        citations = get_citations(cleaned)

        extracted = []
        for cite in citations:
            extracted_cite = self._convert_citation(cite, text)
            if extracted_cite:
                extracted.append(extracted_cite)

        return extracted

    def _convert_citation(
        self,
        cite: CitationBase,
        original_text: str
    ) -> Optional[ExtractedCitation]:
        """Convert eyecite citation object to ExtractedCitation."""

        # Determine citation type
        if isinstance(cite, FullCaseCitation):
            cite_type = "full"
        elif isinstance(cite, ShortCaseCitation):
            cite_type = "short"
        elif isinstance(cite, SupraCitation):
            cite_type = "supra"
        elif isinstance(cite, IdCitation):
            cite_type = "id"
        else:
            cite_type = "unknown"

        # Extract components
        groups = cite.groups if hasattr(cite, 'groups') else {}

        # Get normalized citation string
        normalized = str(cite)

        # Extract metadata
        metadata = {
            'pin_cite': getattr(cite, 'pin_cite', None),
            'defendant': getattr(cite, 'defendant', None),
            'plaintiff': getattr(cite, 'plaintiff', None),
            'court': getattr(cite, 'court', None),
            'year': getattr(cite, 'year', None),
        }

        return ExtractedCitation(
            raw_text=cite.matched_text() if hasattr(cite, 'matched_text') else str(cite),
            normalized=normalized,
            reporter=groups.get('reporter'),
            volume=groups.get('volume'),
            page=groups.get('page'),
            year=metadata.get('year'),
            court=metadata.get('court'),
            citation_type=cite_type,
            span_start=cite.span()[0] if hasattr(cite, 'span') else 0,
            span_end=cite.span()[1] if hasattr(cite, 'span') else 0,
            groups=groups,
            metadata=metadata
        )

    def extract_quotes(
        self,
        text: str,
        context_chars: int = 200
    ) -> List[QuoteContext]:
        """
        Extract quoted passages from the document.

        Args:
            text: Document text
            context_chars: Number of characters before/after quote for context

        Returns:
            List of QuoteContext objects
        """
        quotes = []

        for match in self.quote_pattern.finditer(text):
            quote_text = match.group(1).strip()
            start, end = match.span()

            # Get surrounding context
            context_start = max(0, start - context_chars)
            context_end = min(len(text), end + context_chars)

            preceding = text[context_start:start]
            following = text[end:context_end]

            # Check for alterations
            has_ellipsis = bool(self.ellipsis_pattern.search(quote_text))
            has_brackets = bool(self.bracket_pattern.search(quote_text))
            has_alterations = has_ellipsis or has_brackets

            # Find nearby citations (within context)
            nearby_text = text[context_start:context_end]
            nearby_cites = self.extract_citations(nearby_text)

            quotes.append(QuoteContext(
                quote_text=quote_text,
                span_start=start,
                span_end=end,
                preceding_text=preceding,
                following_text=following,
                nearby_citations=nearby_cites,
                has_ellipsis=has_ellipsis,
                has_brackets=has_brackets,
                has_alterations=has_alterations
            ))

        return quotes

    def match_quotes_to_citations(
        self,
        quotes: List[QuoteContext],
        citations: List[ExtractedCitation],
        max_distance: int = 500
    ) -> Dict[int, List[ExtractedCitation]]:
        """
        Match quotes to their likely source citations.

        Args:
            quotes: List of extracted quotes
            citations: List of extracted citations
            max_distance: Maximum character distance for matching

        Returns:
            Dict mapping quote index to list of candidate citations
        """
        matches = {}

        for i, quote in enumerate(quotes):
            candidates = []

            for cite in citations:
                # Calculate distance from quote to citation
                if cite.span_end <= quote.span_start:
                    # Citation before quote
                    distance = quote.span_start - cite.span_end
                elif cite.span_start >= quote.span_end:
                    # Citation after quote
                    distance = cite.span_start - quote.span_end
                else:
                    # Citation overlaps quote (in context)
                    distance = 0

                if distance <= max_distance:
                    candidates.append(cite)

            # Sort by proximity
            candidates.sort(key=lambda c: abs(c.span_start - quote.span_end))
            matches[i] = candidates

        return matches

    def get_pinpoint_citations(
        self,
        citations: List[ExtractedCitation]
    ) -> List[Tuple[ExtractedCitation, str]]:
        """
        Extract citations with pinpoint references.

        Returns:
            List of (citation, pinpoint) tuples
        """
        pinpoints = []

        for cite in citations:
            pin = cite.metadata.get('pin_cite')
            if pin:
                pinpoints.append((cite, pin))

        return pinpoints

    def to_dict(self, citation: ExtractedCitation) -> Dict:
        """Convert ExtractedCitation to dictionary for JSON serialization."""
        return asdict(citation)

    def quote_to_dict(self, quote: QuoteContext) -> Dict:
        """Convert QuoteContext to dictionary for JSON serialization."""
        data = asdict(quote)
        # Convert nested citations
        data['nearby_citations'] = [
            self.to_dict(c) for c in quote.nearby_citations
        ]
        return data
