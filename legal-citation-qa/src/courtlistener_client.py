"""
CourtListener API client for opinion lookup and text retrieval.
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import requests
import time
import logging
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)


@dataclass
class OpinionMetadata:
    """Metadata for a CourtListener opinion."""
    cluster_id: Optional[int]
    opinion_id: Optional[int]
    case_name: str
    court: str
    date_filed: str
    citation: str
    parallel_citations: List[str]
    url: str
    docket_number: Optional[str]
    judges: Optional[str]
    nature_of_suit: Optional[str]
    syllabus: Optional[str]
    precedential_status: Optional[str]


@dataclass
class OpinionText:
    """Full text of an opinion."""
    opinion_id: int
    cluster_id: int
    plain_text: str
    html: Optional[str]
    xml_harvard: Optional[str]
    author: Optional[str]
    type: str  # majority, concurring, dissenting, etc.
    page_count: Optional[int]


class CourtListenerClient:
    """Client for interacting with CourtListener REST APIs."""

    BASE_URL = "https://www.courtlistener.com/api/rest/v3/"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize CourtListener client.

        Args:
            api_token: Optional API token for authenticated requests
                      (required for higher rate limits)
        """
        self.api_token = api_token
        self.session = requests.Session()

        if api_token:
            self.session.headers.update({
                'Authorization': f'Token {api_token}'
            })

        self.session.headers.update({
            'User-Agent': 'LegalCitationQA/1.0'
        })

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests

    def _rate_limit(self):
        """Implement rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make a rate-limited request to the API.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.RequestException: On API errors
        """
        self._rate_limit()

        url = urljoin(self.BASE_URL, endpoint)

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def lookup_citation(self, citation: str) -> Optional[OpinionMetadata]:
        """
        Lookup a citation and return metadata.

        Args:
            citation: Citation string (e.g., "410 U.S. 113")

        Returns:
            OpinionMetadata if found, None otherwise
        """
        try:
            # Use the citation lookup endpoint
            data = self._make_request(
                'search/',
                params={
                    'q': citation,
                    'type': 'o',  # opinions
                    'format': 'json'
                }
            )

            results = data.get('results', [])
            if not results:
                logger.warning(f"No results found for citation: {citation}")
                return None

            # Take the first result (most relevant)
            result = results[0]

            return self._parse_opinion_metadata(result)

        except Exception as e:
            logger.error(f"Citation lookup failed for {citation}: {e}")
            return None

    def get_opinion_cluster(self, cluster_id: int) -> Optional[OpinionMetadata]:
        """
        Get opinion cluster by ID.

        Args:
            cluster_id: Cluster ID

        Returns:
            OpinionMetadata if found
        """
        try:
            data = self._make_request(f'clusters/{cluster_id}/')
            return self._parse_opinion_metadata(data)

        except Exception as e:
            logger.error(f"Cluster lookup failed for ID {cluster_id}: {e}")
            return None

    def get_opinion_text(self, opinion_id: int) -> Optional[OpinionText]:
        """
        Get full text of an opinion.

        Args:
            opinion_id: Opinion ID

        Returns:
            OpinionText if found
        """
        try:
            data = self._make_request(f'opinions/{opinion_id}/')
            return self._parse_opinion_text(data)

        except Exception as e:
            logger.error(f"Opinion text lookup failed for ID {opinion_id}: {e}")
            return None

    def get_cluster_opinions(self, cluster_id: int) -> List[OpinionText]:
        """
        Get all opinions in a cluster (majority, concurring, dissenting).

        Args:
            cluster_id: Cluster ID

        Returns:
            List of OpinionText objects
        """
        try:
            # Get cluster to find opinion IDs
            cluster_data = self._make_request(f'clusters/{cluster_id}/')

            sub_opinions = cluster_data.get('sub_opinions', [])

            opinions = []
            for opinion_url in sub_opinions:
                # Extract opinion ID from URL
                opinion_id = int(opinion_url.rstrip('/').split('/')[-1])
                opinion_text = self.get_opinion_text(opinion_id)

                if opinion_text:
                    opinions.append(opinion_text)

            return opinions

        except Exception as e:
            logger.error(f"Failed to get cluster opinions for {cluster_id}: {e}")
            return []

    def search_by_citation_string(
        self,
        citation: str,
        volume: Optional[str] = None,
        reporter: Optional[str] = None,
        page: Optional[str] = None
    ) -> List[OpinionMetadata]:
        """
        Search for opinions by citation components.

        Args:
            citation: Full citation string or case name
            volume: Volume number
            reporter: Reporter abbreviation
            page: Page number

        Returns:
            List of matching OpinionMetadata
        """
        # Build query
        query_parts = []

        if citation:
            query_parts.append(f'"{citation}"')

        if volume and reporter and page:
            query_parts.append(f'citation:({volume} {reporter} {page})')

        query = ' '.join(query_parts)

        try:
            data = self._make_request(
                'search/',
                params={
                    'q': query,
                    'type': 'o',
                    'format': 'json'
                }
            )

            results = data.get('results', [])
            return [self._parse_opinion_metadata(r) for r in results]

        except Exception as e:
            logger.error(f"Citation search failed: {e}")
            return []

    def get_opinion_by_citation(
        self,
        volume: str,
        reporter: str,
        page: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get opinion metadata and text by citation components.

        Args:
            volume: Volume number
            reporter: Reporter abbreviation
            page: Page number

        Returns:
            Dict with metadata and text, or None
        """
        # First, get the metadata
        metadata_list = self.search_by_citation_string(
            citation=None,
            volume=volume,
            reporter=reporter,
            page=page
        )

        if not metadata_list:
            return None

        metadata = metadata_list[0]

        # Get all opinion texts for this cluster
        if metadata.cluster_id:
            opinions = self.get_cluster_opinions(metadata.cluster_id)
        else:
            opinions = []

        return {
            'metadata': metadata,
            'opinions': opinions
        }

    def _parse_opinion_metadata(self, data: Dict) -> OpinionMetadata:
        """Parse API response into OpinionMetadata."""

        # Extract parallel citations
        parallel_cites = []
        if 'citations' in data:
            parallel_cites = [
                f"{c.get('volume')} {c.get('reporter')} {c.get('page')}"
                for c in data['citations']
                if all(k in c for k in ['volume', 'reporter', 'page'])
            ]

        return OpinionMetadata(
            cluster_id=data.get('cluster_id') or data.get('id'),
            opinion_id=data.get('opinion_id'),
            case_name=data.get('caseName') or data.get('case_name', ''),
            court=data.get('court') or data.get('court_id', ''),
            date_filed=data.get('dateFiled') or data.get('date_filed', ''),
            citation=data.get('citation', [''])[0] if isinstance(data.get('citation'), list) else data.get('citation', ''),
            parallel_citations=parallel_cites,
            url=data.get('absolute_url', ''),
            docket_number=data.get('docket_number'),
            judges=data.get('judges'),
            nature_of_suit=data.get('nature_of_suit'),
            syllabus=data.get('syllabus'),
            precedential_status=data.get('precedential_status')
        )

    def _parse_opinion_text(self, data: Dict) -> OpinionText:
        """Parse API response into OpinionText."""

        return OpinionText(
            opinion_id=data.get('id', 0),
            cluster_id=data.get('cluster_id', 0) or data.get('cluster', '').split('/')[-2] if data.get('cluster') else 0,
            plain_text=data.get('plain_text', ''),
            html=data.get('html'),
            xml_harvard=data.get('xml_harvard'),
            author=data.get('author_str'),
            type=data.get('type', 'unknown'),
            page_count=data.get('page_count')
        )

    def extract_text_at_pinpoint(
        self,
        opinion_text: str,
        pinpoint: str,
        context_chars: int = 500
    ) -> Optional[str]:
        """
        Extract text around a pinpoint citation.

        Args:
            opinion_text: Full opinion text
            pinpoint: Pinpoint page/paragraph reference
            context_chars: Characters to extract around pinpoint

        Returns:
            Text excerpt around pinpoint, or None if not found
        """
        # Simple heuristic: look for page markers or paragraph numbers
        # This is approximate as exact page boundaries aren't in plain text

        # Try to find references to the pinpoint page
        patterns = [
            rf'\*{pinpoint}\s',  # *123 format
            rf'\[{pinpoint}\]',  # [123] format
            rf'page {pinpoint}\b',
            rf'at {pinpoint}\b',
        ]

        for pattern in patterns:
            import re
            match = re.search(pattern, opinion_text, re.IGNORECASE)
            if match:
                start = max(0, match.start() - context_chars)
                end = min(len(opinion_text), match.end() + context_chars)
                return opinion_text[start:end]

        # Fallback: return beginning of opinion
        return opinion_text[:context_chars * 2] if opinion_text else None
