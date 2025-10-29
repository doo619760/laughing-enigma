"""
Quote matching engine using RapidFuzz for fuzzy string matching.
Compares quoted passages in briefs to source opinion text.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import re
from rapidfuzz import fuzz, process
from rapidfuzz.distance import Levenshtein


@dataclass
class QuoteMatch:
    """Result of matching a quote to source text."""
    quote: str
    source_excerpt: str
    similarity_score: float  # 0-100
    match_type: str  # exact, high, medium, low, none
    start_position: int
    end_position: int
    differences: List[str]
    normalized_quote: str
    normalized_source: str
    flags: List[str]  # warnings/issues


@dataclass
class MatchResult:
    """Complete matching result for a quote-citation pair."""
    quote_text: str
    citation: str
    opinion_id: Optional[int]
    matches: List[QuoteMatch]
    best_match: Optional[QuoteMatch]
    confidence: str  # green, yellow, red
    warnings: List[str]


class QuoteMatcher:
    """Matches quoted passages to source opinion text."""

    # Similarity thresholds
    EXACT_THRESHOLD = 98.0
    HIGH_THRESHOLD = 90.0
    MEDIUM_THRESHOLD = 80.0

    def __init__(self):
        """Initialize the quote matcher."""
        # Patterns for text normalization
        self.whitespace_pattern = re.compile(r'\s+')
        self.punctuation_pattern = re.compile(r'[.,;:!?\-\u2013\u2014]')
        self.bracket_pattern = re.compile(r'\[.*?\]')
        self.ellipsis_pattern = re.compile(r'\.\.\.|…')

    def normalize_text(
        self,
        text: str,
        remove_brackets: bool = False,
        remove_ellipses: bool = False
    ) -> str:
        """
        Normalize text for comparison.

        Args:
            text: Text to normalize
            remove_brackets: Remove bracketed alterations
            remove_ellipses: Remove ellipses

        Returns:
            Normalized text
        """
        # Convert to lowercase
        normalized = text.lower()

        # Optionally remove brackets
        if remove_brackets:
            normalized = self.bracket_pattern.sub('', normalized)

        # Optionally remove ellipses
        if remove_ellipses:
            normalized = self.ellipsis_pattern.sub(' ', normalized)

        # Normalize whitespace
        normalized = self.whitespace_pattern.sub(' ', normalized)

        # Remove leading/trailing whitespace
        normalized = normalized.strip()

        return normalized

    def find_best_match(
        self,
        quote: str,
        opinion_text: str,
        context_window: int = 100
    ) -> Optional[QuoteMatch]:
        """
        Find the best match for a quote in the opinion text.

        Args:
            quote: Quoted text from brief
            opinion_text: Full opinion text
            context_window: Characters to search around quote

        Returns:
            Best QuoteMatch or None
        """
        if not quote or not opinion_text:
            return None

        # Normalize for comparison
        norm_quote = self.normalize_text(quote)
        norm_opinion = self.normalize_text(opinion_text)

        # Try exact match first
        if norm_quote in norm_opinion:
            pos = norm_opinion.index(norm_quote)
            return self._create_match(
                quote,
                opinion_text,
                pos,
                pos + len(norm_quote),
                100.0,
                "exact"
            )

        # Try fuzzy matching using sliding window
        matches = self._sliding_window_match(
            norm_quote,
            norm_opinion,
            opinion_text
        )

        if matches:
            best = max(matches, key=lambda m: m.similarity_score)
            return best

        return None

    def _sliding_window_match(
        self,
        norm_quote: str,
        norm_opinion: str,
        original_opinion: str,
        overlap: float = 0.5
    ) -> List[QuoteMatch]:
        """
        Use sliding window to find best fuzzy matches.

        Args:
            norm_quote: Normalized quote
            norm_opinion: Normalized opinion text
            original_opinion: Original opinion text
            overlap: Window overlap factor

        Returns:
            List of QuoteMatch objects
        """
        matches = []
        quote_len = len(norm_quote)
        window_size = int(quote_len * 1.2)  # 20% larger window
        step = int(window_size * overlap)

        if step == 0:
            step = 1

        for i in range(0, len(norm_opinion) - window_size + 1, step):
            window = norm_opinion[i:i + window_size]

            # Calculate similarity
            score = fuzz.ratio(norm_quote, window)

            if score >= self.MEDIUM_THRESHOLD:
                match_type = self._classify_match(score)

                match = self._create_match(
                    norm_quote,
                    original_opinion,
                    i,
                    i + window_size,
                    score,
                    match_type
                )

                matches.append(match)

        # Merge overlapping high-quality matches
        return self._merge_matches(matches)

    def _create_match(
        self,
        quote: str,
        opinion_text: str,
        start: int,
        end: int,
        score: float,
        match_type: str
    ) -> QuoteMatch:
        """Create a QuoteMatch object."""

        # Extract source excerpt
        source_excerpt = opinion_text[start:end]

        # Normalize both for comparison
        norm_quote = self.normalize_text(quote)
        norm_source = self.normalize_text(source_excerpt)

        # Find differences
        differences = self._find_differences(norm_quote, norm_source)

        # Generate flags
        flags = self._generate_flags(quote, source_excerpt, differences, score)

        return QuoteMatch(
            quote=quote,
            source_excerpt=source_excerpt,
            similarity_score=score,
            match_type=match_type,
            start_position=start,
            end_position=end,
            differences=differences,
            normalized_quote=norm_quote,
            normalized_source=norm_source,
            flags=flags
        )

    def _classify_match(self, score: float) -> str:
        """Classify match quality based on score."""
        if score >= self.EXACT_THRESHOLD:
            return "exact"
        elif score >= self.HIGH_THRESHOLD:
            return "high"
        elif score >= self.MEDIUM_THRESHOLD:
            return "medium"
        else:
            return "low"

    def _find_differences(self, text1: str, text2: str) -> List[str]:
        """
        Find specific differences between two texts.

        Returns:
            List of difference descriptions
        """
        differences = []

        # Check length difference
        len_diff = abs(len(text1) - len(text2))
        if len_diff > 10:
            differences.append(f"Length difference: {len_diff} characters")

        # Use Levenshtein to find edit operations
        ops = Levenshtein.editops(text1, text2)

        if len(ops) > 0:
            # Categorize operations
            insertions = sum(1 for op in ops if op[0] == 'insert')
            deletions = sum(1 for op in ops if op[0] == 'delete')
            replacements = sum(1 for op in ops if op[0] == 'replace')

            if insertions > 0:
                differences.append(f"{insertions} insertions")
            if deletions > 0:
                differences.append(f"{deletions} deletions")
            if replacements > 0:
                differences.append(f"{replacements} replacements")

        return differences

    def _generate_flags(
        self,
        quote: str,
        source: str,
        differences: List[str],
        score: float
    ) -> List[str]:
        """Generate warning flags for the match."""
        flags = []

        # Check for alterations in quote
        if self.bracket_pattern.search(quote):
            flags.append("Contains bracketed alterations")

        if self.ellipsis_pattern.search(quote):
            flags.append("Contains ellipses (omissions)")

        # Check score
        if score < self.HIGH_THRESHOLD:
            flags.append(f"Low similarity score: {score:.1f}%")

        # Check for significant differences
        if len(differences) > 5:
            flags.append("Multiple differences detected")

        # Check for quotation marks within quote
        if '"' in quote or '"' in quote or '"' in quote:
            flags.append("Contains nested quotation marks")

        return flags

    def _merge_matches(self, matches: List[QuoteMatch]) -> List[QuoteMatch]:
        """Merge overlapping matches, keeping the best ones."""
        if not matches:
            return []

        # Sort by score (descending) then position
        sorted_matches = sorted(
            matches,
            key=lambda m: (-m.similarity_score, m.start_position)
        )

        merged = []
        for match in sorted_matches:
            # Check if overlaps with existing merged matches
            overlaps = False
            for existing in merged:
                if self._ranges_overlap(
                    match.start_position,
                    match.end_position,
                    existing.start_position,
                    existing.end_position
                ):
                    overlaps = True
                    break

            if not overlaps:
                merged.append(match)

        return merged

    def _ranges_overlap(
        self,
        start1: int,
        end1: int,
        start2: int,
        end2: int
    ) -> bool:
        """Check if two ranges overlap."""
        return not (end1 <= start2 or end2 <= start1)

    def match_quote_to_opinion(
        self,
        quote: str,
        opinion_text: str,
        citation: str,
        opinion_id: Optional[int] = None
    ) -> MatchResult:
        """
        Match a quote to opinion text and generate result.

        Args:
            quote: Quoted text
            opinion_text: Opinion full text
            citation: Citation string
            opinion_id: Optional opinion ID

        Returns:
            MatchResult
        """
        # Find all potential matches
        all_matches = []

        # Try exact match first
        best = self.find_best_match(quote, opinion_text)
        if best:
            all_matches.append(best)

        # Try with alterations removed
        quote_no_brackets = self.bracket_pattern.sub('', quote)
        quote_no_ellipses = self.ellipsis_pattern.sub(' ', quote_no_brackets)

        if quote_no_ellipses != quote:
            alt_match = self.find_best_match(quote_no_ellipses, opinion_text)
            if alt_match and alt_match not in all_matches:
                all_matches.append(alt_match)

        # Determine best match
        best_match = max(all_matches, key=lambda m: m.similarity_score) if all_matches else None

        # Determine confidence level
        confidence = self._determine_confidence(best_match)

        # Generate warnings
        warnings = self._generate_warnings(best_match, quote)

        return MatchResult(
            quote_text=quote,
            citation=citation,
            opinion_id=opinion_id,
            matches=all_matches,
            best_match=best_match,
            confidence=confidence,
            warnings=warnings
        )

    def _determine_confidence(self, match: Optional[QuoteMatch]) -> str:
        """Determine confidence level (green/yellow/red)."""
        if not match:
            return "red"

        score = match.similarity_score

        if score >= self.EXACT_THRESHOLD:
            return "green"
        elif score >= self.HIGH_THRESHOLD:
            return "yellow"
        else:
            return "red"

    def _generate_warnings(
        self,
        match: Optional[QuoteMatch],
        quote: str
    ) -> List[str]:
        """Generate warnings for the match result."""
        warnings = []

        if not match:
            warnings.append("No match found in opinion text")
            return warnings

        if match.similarity_score < self.EXACT_THRESHOLD:
            warnings.append(
                f"Quote does not match source exactly ({match.similarity_score:.1f}% similar)"
            )

        if match.flags:
            warnings.extend(match.flags)

        if len(match.differences) > 3:
            warnings.append("Significant differences between quote and source")

        return warnings

    def to_dict(self, result: MatchResult) -> Dict:
        """Convert MatchResult to dictionary for JSON serialization."""
        data = asdict(result)

        # Convert nested QuoteMatch objects
        if result.best_match:
            data['best_match'] = asdict(result.best_match)

        data['matches'] = [asdict(m) for m in result.matches]

        return data
