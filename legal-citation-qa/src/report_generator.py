"""
Report generator for citation QA results.
Generates both JSON and HTML reports.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging
from pathlib import Path
from jinja2 import Template
import hashlib

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate QA reports in JSON and HTML formats."""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize report generator.

        Args:
            template_dir: Directory containing HTML templates
        """
        self.template_dir = Path(template_dir) if template_dir else None

    def generate_report(
        self,
        document_path: str,
        citations: List[Dict],
        quotes: List[Dict],
        match_results: List[Dict],
        parallel_checks: List[Dict],
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate complete QA report data.

        Args:
            document_path: Path to analyzed document
            citations: List of extracted citations
            quotes: List of extracted quotes
            match_results: List of quote match results
            parallel_checks: List of parallel citation checks
            metadata: Optional document metadata

        Returns:
            Complete report dictionary
        """
        # Calculate statistics
        stats = self._calculate_statistics(
            citations,
            quotes,
            match_results,
            parallel_checks
        )

        # Determine overall status
        overall_status = self._determine_overall_status(match_results, parallel_checks)

        # Build report
        report = {
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'document_path': document_path,
                'document_name': Path(document_path).name,
                'version': '1.0',
                'generator': 'Legal Citation QA System'
            },
            'summary': {
                'overall_status': overall_status,
                'total_citations': len(citations),
                'total_quotes': len(quotes),
                'citations_matched': stats['citations_matched'],
                'citations_ambiguous': stats['citations_ambiguous'],
                'citations_invalid': stats['citations_invalid'],
                'quotes_exact_match': stats['quotes_exact_match'],
                'quotes_partial_match': stats['quotes_partial_match'],
                'quotes_no_match': stats['quotes_no_match'],
                'parallel_citations_compliant': stats['parallel_compliant'],
                'parallel_citations_issues': stats['parallel_issues']
            },
            'citations': citations,
            'quotes': quotes,
            'match_results': match_results,
            'parallel_checks': parallel_checks,
            'statistics': stats,
            'flags': self._collect_flags(match_results, parallel_checks),
            'document_metadata': metadata or {}
        }

        return report

    def _calculate_statistics(
        self,
        citations: List[Dict],
        quotes: List[Dict],
        match_results: List[Dict],
        parallel_checks: List[Dict]
    ) -> Dict[str, int]:
        """Calculate report statistics."""

        stats = {
            'citations_matched': 0,
            'citations_ambiguous': 0,
            'citations_invalid': 0,
            'quotes_exact_match': 0,
            'quotes_partial_match': 0,
            'quotes_no_match': 0,
            'parallel_compliant': 0,
            'parallel_issues': 0,
            'total_flags': 0
        }

        # Count match results
        for result in match_results:
            confidence = result.get('confidence', 'red')
            if confidence == 'green':
                stats['quotes_exact_match'] += 1
            elif confidence == 'yellow':
                stats['quotes_partial_match'] += 1
            else:
                stats['quotes_no_match'] += 1

        # Count parallel citation compliance
        for check in parallel_checks:
            if check.get('compliant', True):
                stats['parallel_compliant'] += 1
            else:
                stats['parallel_issues'] += 1

        # Estimate citation validity (based on match results)
        stats['citations_matched'] = stats['quotes_exact_match'] + stats['quotes_partial_match']
        stats['citations_invalid'] = stats['quotes_no_match']

        return stats

    def _determine_overall_status(
        self,
        match_results: List[Dict],
        parallel_checks: List[Dict]
    ) -> str:
        """Determine overall report status (green/yellow/red)."""

        # Count issues
        red_matches = sum(1 for r in match_results if r.get('confidence') == 'red')
        yellow_matches = sum(1 for r in match_results if r.get('confidence') == 'yellow')
        parallel_issues = sum(1 for c in parallel_checks if not c.get('compliant', True))

        # Determine status
        if red_matches > 0 or parallel_issues > 0:
            return 'red'
        elif yellow_matches > 0:
            return 'yellow'
        else:
            return 'green'

    def _collect_flags(
        self,
        match_results: List[Dict],
        parallel_checks: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Collect all flags and warnings from results."""

        flags = []

        # Collect from match results
        for i, result in enumerate(match_results):
            warnings = result.get('warnings', [])
            for warning in warnings:
                flags.append({
                    'type': 'quote_match',
                    'severity': 'warning' if result.get('confidence') == 'yellow' else 'error',
                    'message': warning,
                    'quote_index': i,
                    'citation': result.get('citation', '')
                })

        # Collect from parallel checks
        for i, check in enumerate(parallel_checks):
            warnings = check.get('warnings', [])
            for warning in warnings:
                flags.append({
                    'type': 'parallel_citation',
                    'severity': 'error' if not check.get('compliant') else 'warning',
                    'message': warning,
                    'citation_index': i,
                    'citation': check.get('citation', '')
                })

        return flags

    def save_json_report(
        self,
        report: Dict[str, Any],
        output_path: str,
        pretty: bool = True
    ) -> bool:
        """
        Save report as JSON file.

        Args:
            report: Report dictionary
            output_path: Output file path
            pretty: Whether to pretty-print JSON

        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(report, f, ensure_ascii=False)

            logger.info(f"JSON report saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save JSON report: {e}")
            return False

    def generate_html_report(
        self,
        report: Dict[str, Any],
        template_name: str = 'report_template.html'
    ) -> str:
        """
        Generate HTML report.

        Args:
            report: Report dictionary
            template_name: Template filename

        Returns:
            HTML string
        """
        # Use embedded template if no template dir specified
        if self.template_dir and (self.template_dir / template_name).exists():
            with open(self.template_dir / template_name, 'r') as f:
                template_str = f.read()
        else:
            template_str = self._get_default_template()

        template = Template(template_str)

        # Render template
        html = template.render(
            report=report,
            summary=report.get('summary', {}),
            citations=report.get('citations', []),
            quotes=report.get('quotes', []),
            match_results=report.get('match_results', []),
            parallel_checks=report.get('parallel_checks', []),
            flags=report.get('flags', []),
            metadata=report.get('metadata', {}),
            generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        )

        return html

    def save_html_report(
        self,
        report: Dict[str, Any],
        output_path: str
    ) -> bool:
        """
        Save HTML report to file.

        Args:
            report: Report dictionary
            output_path: Output file path

        Returns:
            True if successful
        """
        try:
            html = self.generate_html_report(report)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info(f"HTML report saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save HTML report: {e}")
            return False

    def sign_report(self, report: Dict[str, Any]) -> str:
        """
        Generate a cryptographic signature for the report.

        Args:
            report: Report dictionary

        Returns:
            SHA-256 hash of report
        """
        # Convert to canonical JSON
        canonical = json.dumps(report, sort_keys=True, ensure_ascii=False)

        # Hash
        signature = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

        return signature

    def add_signature(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add signature to report.

        Args:
            report: Report dictionary

        Returns:
            Report with signature added
        """
        # Create a copy
        signed_report = report.copy()

        # Generate signature (excluding existing signature if any)
        if 'signature' in signed_report:
            del signed_report['signature']

        signature = self.sign_report(signed_report)

        # Add signature
        signed_report['signature'] = {
            'algorithm': 'SHA-256',
            'value': signature,
            'signed_at': datetime.utcnow().isoformat()
        }

        return signed_report

    def _get_default_template(self) -> str:
        """Get default HTML template."""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Citation QA Report - {{ metadata.document_name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #1a1a1a; margin-bottom: 10px; font-size: 2em; }
        h2 { color: #2c3e50; margin: 30px 0 15px; border-bottom: 2px solid #3498db; padding-bottom: 8px; }
        h3 { color: #34495e; margin: 20px 0 10px; }

        .header { margin-bottom: 40px; }
        .metadata { color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }

        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 1.1em;
            margin: 10px 0;
        }
        .status-green { background: #2ecc71; color: white; }
        .status-yellow { background: #f39c12; color: white; }
        .status-red { background: #e74c3c; color: white; }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .summary-card {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }
        .summary-card .number { font-size: 2.5em; font-weight: bold; color: #2c3e50; }
        .summary-card .label { color: #7f8c8d; font-size: 0.9em; margin-top: 5px; }

        .flag {
            padding: 12px;
            margin: 10px 0;
            border-left: 4px solid;
            background: #f8f9fa;
        }
        .flag-error { border-color: #e74c3c; background: #fadbd8; }
        .flag-warning { border-color: #f39c12; background: #fef5e7; }
        .flag-type { font-weight: bold; text-transform: uppercase; font-size: 0.85em; }

        .citation-item, .quote-item {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 4px solid #3498db;
        }
        .citation-text { font-family: "Georgia", serif; font-style: italic; margin: 10px 0; }
        .match-score {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .score-green { background: #d5f4e6; color: #27ae60; }
        .score-yellow { background: #fef9e7; color: #f39c12; }
        .score-red { background: #fadbd8; color: #e74c3c; }

        .quote-text {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #95a5a6;
            font-family: "Georgia", serif;
        }

        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #34495e; color: white; font-weight: bold; }
        tr:hover { background: #f8f9fa; }

        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 0.9em;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Legal Citation QA Report</h1>
            <div class="metadata">
                <strong>Document:</strong> {{ metadata.document_name }}<br>
                <strong>Generated:</strong> {{ generated_at }}<br>
                <strong>Version:</strong> {{ metadata.version }}
            </div>
            <div class="status-badge status-{{ summary.overall_status }}">
                Overall Status: {{ summary.overall_status|upper }}
            </div>
        </div>

        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="number">{{ summary.total_citations }}</div>
                <div class="label">Total Citations</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ summary.total_quotes }}</div>
                <div class="label">Total Quotes</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ summary.quotes_exact_match }}</div>
                <div class="label">Exact Matches</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ summary.quotes_partial_match }}</div>
                <div class="label">Partial Matches</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ summary.quotes_no_match }}</div>
                <div class="label">No Match</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ summary.parallel_citations_issues }}</div>
                <div class="label">Parallel Citation Issues</div>
            </div>
        </div>

        {% if flags %}
        <h2>Flags & Warnings ({{ flags|length }})</h2>
        {% for flag in flags %}
        <div class="flag flag-{{ flag.severity }}">
            <div class="flag-type">{{ flag.type }} - {{ flag.severity }}</div>
            <div>{{ flag.message }}</div>
            <div style="margin-top: 5px; font-size: 0.9em; color: #7f8c8d;">
                {{ flag.citation }}
            </div>
        </div>
        {% endfor %}
        {% endif %}

        <h2>Quote Match Results</h2>
        {% for result in match_results %}
        <div class="quote-item">
            <div>
                <strong>Quote #{{ loop.index }}:</strong>
                <span class="match-score score-{{ result.confidence }}">
                    {{ result.confidence|upper }}
                    {% if result.best_match %}
                    - {{ "%.1f"|format(result.best_match.similarity_score) }}% match
                    {% endif %}
                </span>
            </div>
            <div class="quote-text">"{{ result.quote_text }}"</div>
            <div><strong>Citation:</strong> {{ result.citation }}</div>
            {% if result.warnings %}
            <div style="margin-top: 10px;">
                <strong>Warnings:</strong>
                <ul style="margin-left: 20px;">
                {% for warning in result.warnings %}
                    <li>{{ warning }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        {% endfor %}

        <h2>Parallel Citation Checks</h2>
        {% for check in parallel_checks %}
        <div class="citation-item">
            <div class="citation-text">{{ check.citation }}</div>
            <div><strong>Jurisdiction:</strong> {{ check.jurisdiction }}</div>
            <div><strong>Requirement:</strong> {{ check.requirement }}</div>
            <div><strong>Compliant:</strong>
                {% if check.compliant %}
                <span style="color: #27ae60;">✓ Yes</span>
                {% else %}
                <span style="color: #e74c3c;">✗ No</span>
                {% endif %}
            </div>
            {% if check.suggestions %}
            <div style="margin-top: 10px;">
                <strong>Suggestions:</strong>
                <ul style="margin-left: 20px;">
                {% for suggestion in check.suggestions %}
                    <li>{{ suggestion }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        {% endfor %}

        <div class="footer">
            🤖 Generated with Legal Citation QA System<br>
            This report provides automated citation validation. Please review manually before filing.
        </div>
    </div>
</body>
</html>
'''
