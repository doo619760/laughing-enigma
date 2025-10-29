"""
Main worker script for citation QA pipeline.
Orchestrates the complete end-to-end workflow.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from citation_extractor import CitationExtractor
from courtlistener_client import CourtListenerClient
from quote_matcher import QuoteMatcher
from parallel_checker import ParallelCitationChecker
from text_extractor import TextExtractor
from report_generator import ReportGenerator
from box_handler import BoxHandler, MockBoxHandler
from git_audit import GitAuditTrail, MockGitAuditTrail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CitationQAWorker:
    """Main worker for citation QA pipeline."""

    def __init__(
        self,
        courtlistener_token: Optional[str] = None,
        box_client_id: Optional[str] = None,
        box_client_secret: Optional[str] = None,
        box_access_token: Optional[str] = None,
        git_audit_path: Optional[str] = None,
        git_remote_url: Optional[str] = None,
        output_dir: Optional[str] = None,
        use_mock_services: bool = False
    ):
        """
        Initialize the QA worker.

        Args:
            courtlistener_token: CourtListener API token
            box_client_id: Box client ID
            box_client_secret: Box client secret
            box_access_token: Box access token
            git_audit_path: Path to git audit repository
            git_remote_url: Git remote URL
            output_dir: Output directory for reports
            use_mock_services: Use mock services for testing
        """
        # Initialize components
        self.text_extractor = TextExtractor()
        self.citation_extractor = CitationExtractor()
        self.courtlistener_client = CourtListenerClient(courtlistener_token)
        self.quote_matcher = QuoteMatcher()
        self.parallel_checker = ParallelCitationChecker()
        self.report_generator = ReportGenerator()

        # Initialize Box handler
        if use_mock_services or not all([box_client_id, box_access_token]):
            self.box_handler = MockBoxHandler()
        else:
            self.box_handler = BoxHandler(
                box_client_id,
                box_client_secret,
                box_access_token
            )

        # Initialize Git audit
        if use_mock_services or not git_audit_path:
            self.git_audit = MockGitAuditTrail()
        else:
            self.git_audit = GitAuditTrail(
                git_audit_path,
                git_remote_url
            )

        # Output directory
        self.output_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir()) / 'citation-qa'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_document(self, document_path: str) -> Dict[str, Any]:
        """
        Process a document through the complete QA pipeline.

        Args:
            document_path: Path to document file

        Returns:
            Complete QA report
        """
        logger.info(f"Processing document: {document_path}")

        try:
            # Step 1: Extract text
            logger.info("Step 1: Extracting text from document")
            text = self.text_extractor.extract(document_path)

            if not text:
                raise ValueError("Failed to extract text from document")

            logger.info(f"Extracted {len(text)} characters")

            # Step 2: Extract citations
            logger.info("Step 2: Extracting citations")
            citations = self.citation_extractor.extract_citations(text)
            logger.info(f"Found {len(citations)} citations")

            # Step 3: Extract quotes
            logger.info("Step 3: Extracting quoted passages")
            quotes = self.citation_extractor.extract_quotes(text)
            logger.info(f"Found {len(quotes)} quoted passages")

            # Step 4: Match quotes to citations
            logger.info("Step 4: Matching quotes to citations")
            quote_citation_matches = self.citation_extractor.match_quotes_to_citations(
                quotes,
                citations
            )

            # Step 5: Lookup citations and match quotes
            logger.info("Step 5: Looking up citations and matching quotes")
            match_results = []

            for i, quote in enumerate(quotes):
                candidate_cites = quote_citation_matches.get(i, [])

                if not candidate_cites:
                    # Create a "no citation" result
                    match_results.append({
                        'quote_text': quote.quote_text,
                        'citation': 'No citation found',
                        'opinion_id': None,
                        'matches': [],
                        'best_match': None,
                        'confidence': 'red',
                        'warnings': ['No citation found near this quote']
                    })
                    continue

                # Use first (closest) citation
                cite = candidate_cites[0]

                # Lookup citation
                if cite.volume and cite.reporter and cite.page:
                    opinion_data = self.courtlistener_client.get_opinion_by_citation(
                        cite.volume,
                        cite.reporter,
                        cite.page
                    )

                    if opinion_data:
                        metadata = opinion_data['metadata']
                        opinions = opinion_data['opinions']

                        # Get opinion text (use first/majority opinion)
                        opinion_text = opinions[0].plain_text if opinions else ""

                        # Match quote
                        result = self.quote_matcher.match_quote_to_opinion(
                            quote.quote_text,
                            opinion_text,
                            cite.normalized,
                            opinions[0].opinion_id if opinions else None
                        )

                        match_results.append(self.quote_matcher.to_dict(result))
                    else:
                        # Citation not found
                        match_results.append({
                            'quote_text': quote.quote_text,
                            'citation': cite.normalized,
                            'opinion_id': None,
                            'matches': [],
                            'best_match': None,
                            'confidence': 'red',
                            'warnings': ['Citation not found in CourtListener']
                        })
                else:
                    # Invalid citation format
                    match_results.append({
                        'quote_text': quote.quote_text,
                        'citation': cite.normalized,
                        'opinion_id': None,
                        'matches': [],
                        'best_match': None,
                        'confidence': 'red',
                        'warnings': ['Invalid citation format']
                    })

            # Step 6: Check parallel citations
            logger.info("Step 6: Checking parallel citations")
            parallel_checks = []

            for cite in citations:
                if cite.reporter and cite.volume and cite.page:
                    # For simplicity, assume no parallel cites in extracted data
                    # In production, you'd extract these from the citation context
                    check = self.parallel_checker.check_citation(
                        cite.normalized,
                        cite.reporter,
                        []  # parallel citations list
                    )

                    parallel_checks.append(self.parallel_checker.to_dict(check))

            # Step 7: Generate report
            logger.info("Step 7: Generating report")

            # Convert citations and quotes to dicts
            citations_dict = [self.citation_extractor.to_dict(c) for c in citations]
            quotes_dict = [self.citation_extractor.quote_to_dict(q) for q in quotes]

            # Get document metadata
            doc_metadata = self.text_extractor.extract_metadata(document_path)

            # Generate report
            report = self.report_generator.generate_report(
                document_path,
                citations_dict,
                quotes_dict,
                match_results,
                parallel_checks,
                doc_metadata
            )

            # Sign report
            report = self.report_generator.add_signature(report)

            # Step 8: Save reports
            logger.info("Step 8: Saving reports")

            doc_name = Path(document_path).name
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            base_name = f"qa-report_{timestamp}"

            # Save JSON
            json_path = self.output_dir / f"{base_name}.json"
            self.report_generator.save_json_report(report, str(json_path))

            # Save HTML
            html_path = self.output_dir / f"{base_name}.html"
            self.report_generator.save_html_report(report, str(html_path))

            logger.info(f"Reports saved to {self.output_dir}")

            # Step 9: Commit to git audit trail
            logger.info("Step 9: Committing to audit trail")
            self.git_audit.commit_report(
                report,
                doc_name,
                str(json_path),
                str(html_path)
            )

            # Push to remote
            self.git_audit.push_to_remote()

            # Step 10: Upload to Box (if configured)
            logger.info("Step 10: Uploading to Box")
            # This would upload to a specific Box folder
            # For now, we just log
            logger.info("Box upload: Not implemented in this version")

            logger.info("Pipeline completed successfully")

            return report

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise

    def process_box_file(self, file_id: str) -> Dict[str, Any]:
        """
        Process a file from Box.

        Args:
            file_id: Box file ID

        Returns:
            QA report
        """
        logger.info(f"Processing Box file: {file_id}")

        # Download file
        temp_path = self.box_handler.download_file(file_id)

        if not temp_path:
            raise ValueError(f"Failed to download Box file {file_id}")

        try:
            # Process document
            report = self.process_document(temp_path)
            return report

        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Legal Citation QA Worker')
    parser.add_argument('document', help='Path to document to process')
    parser.add_argument('--courtlistener-token', help='CourtListener API token')
    parser.add_argument('--output-dir', help='Output directory for reports')
    parser.add_argument('--git-audit-path', help='Path to git audit repository')
    parser.add_argument('--git-remote-url', help='Git remote URL')
    parser.add_argument('--mock', action='store_true', help='Use mock services')

    args = parser.parse_args()

    # Create worker
    worker = CitationQAWorker(
        courtlistener_token=args.courtlistener_token or os.getenv('COURTLISTENER_TOKEN'),
        output_dir=args.output_dir or os.getenv('OUTPUT_DIR'),
        git_audit_path=args.git_audit_path or os.getenv('GIT_AUDIT_PATH'),
        git_remote_url=args.git_remote_url or os.getenv('GIT_REMOTE_URL'),
        use_mock_services=args.mock
    )

    # Process document
    try:
        report = worker.process_document(args.document)

        print("\n" + "="*80)
        print("QA REPORT SUMMARY")
        print("="*80)

        summary = report['summary']
        print(f"\nOverall Status: {summary['overall_status'].upper()}")
        print(f"\nCitations: {summary['total_citations']}")
        print(f"Quotes: {summary['total_quotes']}")
        print(f"  - Exact matches: {summary['quotes_exact_match']}")
        print(f"  - Partial matches: {summary['quotes_partial_match']}")
        print(f"  - No match: {summary['quotes_no_match']}")
        print(f"\nParallel Citation Issues: {summary['parallel_citations_issues']}")

        if report['flags']:
            print(f"\nFlags: {len(report['flags'])}")
            for flag in report['flags'][:5]:  # Show first 5
                print(f"  - {flag['message']}")

        print("\n" + "="*80)

    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
