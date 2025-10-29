#!/usr/bin/env python3
"""
Example usage of the Legal Citation QA System.

This script demonstrates how to use the system programmatically
without Box or webhook integration.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from worker import CitationQAWorker


def example_basic_usage():
    """Basic example: Process a single document."""

    print("="*80)
    print("Legal Citation QA System - Example Usage")
    print("="*80)

    # Initialize worker (using mock services if no credentials)
    use_mock = not os.getenv('COURTLISTENER_TOKEN')

    if use_mock:
        print("\n⚠️  No CourtListener token found - using mock services")
        print("Set COURTLISTENER_TOKEN environment variable for real API calls\n")

    worker = CitationQAWorker(
        courtlistener_token=os.getenv('COURTLISTENER_TOKEN'),
        output_dir='./example_output',
        git_audit_path='./example_audit',
        use_mock_services=use_mock
    )

    # Example: Process a document
    # Replace with your actual document path
    document_path = sys.argv[1] if len(sys.argv) > 1 else None

    if not document_path:
        print("Usage: python example_usage.py <path_to_document.docx>")
        print("\nExample:")
        print("  python example_usage.py /path/to/brief.docx")
        return

    if not Path(document_path).exists():
        print(f"Error: File not found: {document_path}")
        return

    print(f"\n📄 Processing document: {document_path}")
    print("-"*80)

    try:
        # Run the pipeline
        report = worker.process_document(document_path)

        # Display summary
        print("\n✅ Processing complete!")
        print("\n" + "="*80)
        print("REPORT SUMMARY")
        print("="*80)

        summary = report['summary']

        # Overall status
        status_emoji = {
            'green': '🟢',
            'yellow': '🟡',
            'red': '🔴'
        }
        emoji = status_emoji.get(summary['overall_status'], '⚪')

        print(f"\n{emoji} Overall Status: {summary['overall_status'].upper()}")

        # Statistics
        print(f"\n📊 Statistics:")
        print(f"  • Total Citations: {summary['total_citations']}")
        print(f"  • Total Quotes: {summary['total_quotes']}")

        print(f"\n✓ Quote Matches:")
        print(f"  • Exact matches: {summary['quotes_exact_match']}")
        print(f"  • Partial matches: {summary['quotes_partial_match']}")
        print(f"  • No match: {summary['quotes_no_match']}")

        print(f"\n⚖️  Parallel Citations:")
        print(f"  • Compliant: {summary['parallel_citations_compliant']}")
        print(f"  • Issues: {summary['parallel_citations_issues']}")

        # Flags
        flags = report.get('flags', [])
        if flags:
            print(f"\n⚠️  Flags & Warnings ({len(flags)}):")
            for i, flag in enumerate(flags[:10], 1):  # Show first 10
                severity_icon = '🔴' if flag['severity'] == 'error' else '🟡'
                print(f"  {i}. {severity_icon} {flag['message']}")

            if len(flags) > 10:
                print(f"  ... and {len(flags) - 10} more")

        # Output location
        print(f"\n📁 Reports saved to: ./example_output/")
        print(f"   • JSON report (signed)")
        print(f"   • HTML report (visual)")

        print("\n" + "="*80)
        print("\nNext steps:")
        print("  1. Review the HTML report in your browser")
        print("  2. Check flagged citations and quotes")
        print("  3. Make corrections in your brief")
        print("  4. Re-run QA before filing")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def example_citation_extraction():
    """Example: Extract citations from text."""

    from citation_extractor import CitationExtractor

    text = """
    In Roe v. Wade, 410 U.S. 113, 153 (1973), the Court held that...
    The California Supreme Court in People v. Anderson, 6 Cal. 3d 628,
    493 P.2d 880, 100 Cal. Rptr. 152 (1972) established...
    """

    extractor = CitationExtractor()
    citations = extractor.extract_citations(text)

    print("\n📝 Extracted Citations:")
    for cite in citations:
        print(f"  • {cite.normalized}")
        print(f"    Volume: {cite.volume}, Reporter: {cite.reporter}, Page: {cite.page}")


def example_quote_matching():
    """Example: Match a quote to source text."""

    from quote_matcher import QuoteMatcher

    quote = "The right to privacy is broad enough to encompass a woman's decision."

    source = """
    The Constitution does not explicitly mention any right of privacy.
    However, the right to privacy is broad enough to encompass a woman's
    decision whether or not to terminate her pregnancy. The detriment that
    the State would impose upon the pregnant woman by denying this choice
    altogether is apparent.
    """

    matcher = QuoteMatcher()
    best_match = matcher.find_best_match(quote, source)

    if best_match:
        print(f"\n✓ Match found!")
        print(f"  Similarity: {best_match.similarity_score:.1f}%")
        print(f"  Type: {best_match.match_type}")


if __name__ == '__main__':
    example_basic_usage()

    # Uncomment to run other examples:
    # example_citation_extraction()
    # example_quote_matching()
