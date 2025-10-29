"""
Parallel citation checker and validator.
Ensures proper parallel reporter citations per Bluebook rules and local practice.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum


class ParallelCiteRequirement(Enum):
    """Requirement level for parallel citations."""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"
    FORBIDDEN = "forbidden"


@dataclass
class ParallelCitationRule:
    """Rule for parallel citations in a jurisdiction."""
    jurisdiction: str  # e.g., "CA", "9th Cir", "S.D. Cal."
    court_type: str  # e.g., "supreme", "appellate", "district"
    official_reporter: str  # e.g., "Cal.", "Cal. App."
    parallel_reporters: List[str]  # e.g., ["P.2d", "P.3d", "Cal. Rptr."]
    requirement: ParallelCiteRequirement
    notes: str


@dataclass
class ParallelCitationCheck:
    """Result of checking parallel citations."""
    citation: str
    jurisdiction: str
    has_official: bool
    has_parallel: bool
    missing_reporters: List[str]
    found_reporters: List[str]
    requirement: ParallelCiteRequirement
    compliant: bool
    suggestions: List[str]
    warnings: List[str]


class ParallelCitationChecker:
    """Checks and suggests parallel citations per jurisdiction rules."""

    def __init__(self, court_profiles: Optional[Dict] = None):
        """
        Initialize parallel citation checker.

        Args:
            court_profiles: Optional court-specific configuration
        """
        self.court_profiles = court_profiles or {}
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default parallel citation rules."""

        self.rules = {
            # California Supreme Court
            "CA-supreme": ParallelCitationRule(
                jurisdiction="California",
                court_type="supreme",
                official_reporter="Cal.",
                parallel_reporters=["P.", "P.2d", "P.3d", "Cal. Rptr.", "Cal. Rptr. 2d", "Cal. Rptr. 3d"],
                requirement=ParallelCiteRequirement.REQUIRED,
                notes="Bluebook Rule 10.3.1(b); Cal. Rules of Court require parallel cites"
            ),

            # California Courts of Appeal
            "CA-appellate": ParallelCitationRule(
                jurisdiction="California",
                court_type="appellate",
                official_reporter="Cal. App.",
                parallel_reporters=["Cal. Rptr.", "Cal. Rptr. 2d", "Cal. Rptr. 3d", "P.2d", "P.3d"],
                requirement=ParallelCiteRequirement.REQUIRED,
                notes="Cal. Rules of Court require parallel cites for Courts of Appeal"
            ),

            # U.S. Supreme Court
            "US-supreme": ParallelCitationRule(
                jurisdiction="United States",
                court_type="supreme",
                official_reporter="U.S.",
                parallel_reporters=["S. Ct.", "L. Ed.", "L. Ed. 2d"],
                requirement=ParallelCiteRequirement.OPTIONAL,
                notes="Bluebook Rule 10.3.1(a); parallel cites optional for U.S. Supreme Court"
            ),

            # Ninth Circuit
            "9th-circuit": ParallelCitationRule(
                jurisdiction="Ninth Circuit",
                court_type="circuit",
                official_reporter="F.",
                parallel_reporters=["F.2d", "F.3d", "F.4th", "F. Supp.", "F. Supp. 2d", "F. Supp. 3d"],
                requirement=ParallelCiteRequirement.OPTIONAL,
                notes="Federal reporters; parallel cites not typically required"
            ),

            # Southern District of California
            "SD-Cal": ParallelCitationRule(
                jurisdiction="S.D. Cal.",
                court_type="district",
                official_reporter="F. Supp.",
                parallel_reporters=["F. Supp. 2d", "F. Supp. 3d"],
                requirement=ParallelCiteRequirement.OPTIONAL,
                notes="Local rules may vary; check S.D. Cal. local rules"
            ),

            # New York
            "NY-appellate": ParallelCitationRule(
                jurisdiction="New York",
                court_type="appellate",
                official_reporter="N.Y.",
                parallel_reporters=["N.E.", "N.E.2d", "N.E.3d", "N.Y.S.", "N.Y.S.2d", "N.Y.S.3d"],
                requirement=ParallelCiteRequirement.REQUIRED,
                notes="N.Y. Rules of Court require parallel citations"
            ),

            # Texas
            "TX-supreme": ParallelCitationRule(
                jurisdiction="Texas",
                court_type="supreme",
                official_reporter="Tex.",
                parallel_reporters=["S.W.", "S.W.2d", "S.W.3d"],
                requirement=ParallelCiteRequirement.RECOMMENDED,
                notes="Texas practice varies; parallel cites recommended"
            ),
        }

        # Reporter to jurisdiction mapping
        self.reporter_map = {
            "Cal.": "CA-supreme",
            "Cal. 2d": "CA-supreme",
            "Cal. 3d": "CA-supreme",
            "Cal. 4th": "CA-supreme",
            "Cal. 5th": "CA-supreme",
            "Cal. App.": "CA-appellate",
            "Cal. App. 2d": "CA-appellate",
            "Cal. App. 3d": "CA-appellate",
            "Cal. App. 4th": "CA-appellate",
            "Cal. App. 5th": "CA-appellate",
            "U.S.": "US-supreme",
            "F.": "9th-circuit",
            "F.2d": "9th-circuit",
            "F.3d": "9th-circuit",
            "F.4th": "9th-circuit",
            "F. Supp.": "SD-Cal",
            "F. Supp. 2d": "SD-Cal",
            "F. Supp. 3d": "SD-Cal",
            "N.Y.": "NY-appellate",
            "N.Y.2d": "NY-appellate",
            "N.Y.3d": "NY-appellate",
            "Tex.": "TX-supreme",
            "S.W.": "TX-supreme",
            "S.W.2d": "TX-supreme",
            "S.W.3d": "TX-supreme",
        }

    def check_citation(
        self,
        citation_str: str,
        reporter: str,
        parallel_citations: List[str]
    ) -> ParallelCitationCheck:
        """
        Check if citation has proper parallel citations.

        Args:
            citation_str: Main citation string
            reporter: Reporter abbreviation
            parallel_citations: List of parallel citation reporters

        Returns:
            ParallelCitationCheck result
        """
        # Identify jurisdiction
        jurisdiction_key = self.reporter_map.get(reporter, "unknown")

        if jurisdiction_key == "unknown":
            return self._create_unknown_check(citation_str, reporter)

        # Get applicable rule
        rule = self.rules.get(jurisdiction_key)
        if not rule:
            return self._create_unknown_check(citation_str, reporter)

        # Check for official reporter
        has_official = reporter == rule.official_reporter or reporter in [rule.official_reporter]

        # Check for parallel reporters
        found_reporters = []
        for parallel in parallel_citations:
            # Extract reporter from citation string
            for known_reporter in rule.parallel_reporters:
                if known_reporter in parallel:
                    found_reporters.append(known_reporter)

        has_parallel = len(found_reporters) > 0

        # Determine missing reporters
        missing = []
        if rule.requirement == ParallelCiteRequirement.REQUIRED:
            # At least one parallel cite should be present
            if not has_parallel:
                missing = rule.parallel_reporters[:2]  # Suggest top 2

        # Check compliance
        compliant = True
        warnings = []
        suggestions = []

        if rule.requirement == ParallelCiteRequirement.REQUIRED:
            if not has_parallel:
                compliant = False
                warnings.append(f"Missing required parallel citation for {rule.jurisdiction}")
                suggestions.append(f"Add parallel citation from: {', '.join(rule.parallel_reporters[:2])}")

        elif rule.requirement == ParallelCiteRequirement.RECOMMENDED:
            if not has_parallel:
                warnings.append(f"Parallel citation recommended for {rule.jurisdiction}")
                suggestions.append(f"Consider adding: {', '.join(rule.parallel_reporters[:2])}")

        elif rule.requirement == ParallelCiteRequirement.FORBIDDEN:
            if has_parallel:
                compliant = False
                warnings.append("Parallel citations not permitted for this citation")

        return ParallelCitationCheck(
            citation=citation_str,
            jurisdiction=rule.jurisdiction,
            has_official=has_official,
            has_parallel=has_parallel,
            missing_reporters=missing,
            found_reporters=found_reporters,
            requirement=rule.requirement,
            compliant=compliant,
            suggestions=suggestions,
            warnings=warnings
        )

    def suggest_parallel_citations(
        self,
        reporter: str,
        volume: str,
        page: str,
        available_parallels: List[Dict[str, str]]
    ) -> List[str]:
        """
        Suggest parallel citations based on available data.

        Args:
            reporter: Primary reporter
            volume: Volume number
            page: Page number
            available_parallels: List of parallel citation dicts with
                                volume, reporter, page

        Returns:
            List of formatted parallel citation suggestions
        """
        suggestions = []

        # Get jurisdiction
        jurisdiction_key = self.reporter_map.get(reporter)
        if not jurisdiction_key:
            return suggestions

        rule = self.rules.get(jurisdiction_key)
        if not rule:
            return suggestions

        # Match available parallels to preferred reporters
        for parallel in available_parallels:
            p_reporter = parallel.get('reporter', '')
            p_volume = parallel.get('volume', '')
            p_page = parallel.get('page', '')

            if p_reporter in rule.parallel_reporters:
                cite = f"{p_volume} {p_reporter} {p_page}"
                suggestions.append(cite)

        return suggestions

    def format_full_citation(
        self,
        primary_cite: str,
        parallel_cites: List[str],
        case_name: Optional[str] = None,
        court: Optional[str] = None,
        year: Optional[str] = None
    ) -> str:
        """
        Format a full citation with parallel cites per Bluebook format.

        Args:
            primary_cite: Primary citation (e.g., "410 U.S. 113")
            parallel_cites: List of parallel citations
            case_name: Case name
            court: Court abbreviation
            year: Year

        Returns:
            Fully formatted citation string
        """
        parts = []

        if case_name:
            parts.append(case_name)

        # Add primary citation
        parts.append(primary_cite)

        # Add parallel citations
        if parallel_cites:
            parts.extend(parallel_cites)

        # Add court and year in parenthetical
        parenthetical = []
        if court:
            parenthetical.append(court)
        if year:
            parenthetical.append(year)

        if parenthetical:
            parts.append(f"({' '.join(parenthetical)})")

        return ', '.join(parts)

    def _create_unknown_check(
        self,
        citation: str,
        reporter: str
    ) -> ParallelCitationCheck:
        """Create a check result for unknown jurisdiction."""
        return ParallelCitationCheck(
            citation=citation,
            jurisdiction="Unknown",
            has_official=True,  # Assume it's OK
            has_parallel=False,
            missing_reporters=[],
            found_reporters=[],
            requirement=ParallelCiteRequirement.OPTIONAL,
            compliant=True,
            suggestions=[],
            warnings=[f"Unknown reporter: {reporter}. Cannot verify parallel citation requirements."]
        )

    def get_jurisdiction_rules(self, jurisdiction: str) -> Optional[ParallelCitationRule]:
        """Get rules for a specific jurisdiction."""
        return self.rules.get(jurisdiction)

    def list_supported_jurisdictions(self) -> List[str]:
        """List all supported jurisdictions."""
        return list(self.rules.keys())

    def to_dict(self, check: ParallelCitationCheck) -> Dict:
        """Convert ParallelCitationCheck to dictionary."""
        data = asdict(check)
        # Convert enum to string
        data['requirement'] = check.requirement.value
        return data
