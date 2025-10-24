#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Citation Checker and Verification Tool
OSINT Citation Verification and Validation System

This tool helps verify citations, check link validity, archive sources,
and generate verification reports for OSINT investigations.

Author: Claude AI
Date: 2025-10-24
"""

import sys
import urllib.request
import urllib.parse
import urllib.error
import sqlite3
import json
import time
import re
from datetime import datetime
from termcolor import colored
import hashlib

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: BeautifulSoup4 is required. Install with: pip install beautifulsoup4")
    sys.exit(1)

class CitationChecker:
    """Main citation checker and verification class"""

    def __init__(self, db_path="citation_checker.db"):
        """
        Initialize the citation checker

        Args:
            db_path: Path to SQLite database for storing verification results
        """
        self.db_path = db_path
        self.init_database()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def init_database(self):
        """Initialize SQLite database for citation storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create citations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                url_hash TEXT UNIQUE NOT NULL,
                title TEXT,
                author TEXT,
                date_published TEXT,
                date_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                http_status INTEGER,
                content_hash TEXT,
                archived_url TEXT,
                metadata TEXT,
                notes TEXT
            )
        ''')

        # Create verification history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                citation_id INTEGER,
                verification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                http_status INTEGER,
                changes_detected BOOLEAN,
                FOREIGN KEY (citation_id) REFERENCES citations(id)
            )
        ''')

        conn.commit()
        conn.close()

    def generate_url_hash(self, url):
        """Generate unique hash for URL"""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    def verify_url(self, url, timeout=10):
        """
        Verify if a URL is accessible

        Args:
            url: URL to verify
            timeout: Request timeout in seconds

        Returns:
            dict: Verification results including status, http_code, title, etc.
        """
        result = {
            'url': url,
            'status': 'unknown',
            'http_status': None,
            'title': None,
            'content_type': None,
            'timestamp': datetime.now().isoformat(),
            'error': None
        }

        try:
            # Parse URL to ensure it's valid
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme:
                url = 'http://' + url

            # Make request
            request = urllib.request.Request(url, headers=self.headers)
            response = urllib.request.urlopen(request, timeout=timeout)

            result['http_status'] = response.getcode()
            result['content_type'] = response.info().get('Content-Type', '')

            # Read content
            html_content = response.read()

            # Parse HTML to extract title
            if 'text/html' in result['content_type']:
                try:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    title_tag = soup.find('title')
                    if title_tag:
                        result['title'] = title_tag.text.strip()
                except:
                    pass

            # Generate content hash
            result['content_hash'] = hashlib.md5(html_content).hexdigest()

            if result['http_status'] == 200:
                result['status'] = 'verified'
            else:
                result['status'] = 'accessible'

        except urllib.error.HTTPError as e:
            result['status'] = 'error'
            result['http_status'] = e.code
            result['error'] = str(e)
        except urllib.error.URLError as e:
            result['status'] = 'unreachable'
            result['error'] = str(e.reason)
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)

        return result

    def check_wayback_machine(self, url):
        """
        Check if URL has archived version on Wayback Machine

        Args:
            url: URL to check

        Returns:
            dict: Archive information including latest snapshot
        """
        wayback_api = "http://archive.org/wayback/available?url="
        archive_info = {
            'has_archive': False,
            'latest_snapshot': None,
            'snapshot_url': None,
            'snapshot_timestamp': None
        }

        try:
            request = urllib.request.Request(wayback_api + urllib.parse.quote(url))
            response = urllib.request.urlopen(request, timeout=10)
            data = json.loads(response.read().decode('utf-8'))

            if 'archived_snapshots' in data and 'closest' in data['archived_snapshots']:
                snapshot = data['archived_snapshots']['closest']
                archive_info['has_archive'] = snapshot.get('available', False)
                archive_info['snapshot_url'] = snapshot.get('url', None)
                archive_info['snapshot_timestamp'] = snapshot.get('timestamp', None)
                archive_info['latest_snapshot'] = snapshot

        except Exception as e:
            archive_info['error'] = str(e)

        return archive_info

    def extract_metadata(self, url):
        """
        Extract metadata from URL (Open Graph, Twitter Cards, etc.)

        Args:
            url: URL to extract metadata from

        Returns:
            dict: Extracted metadata
        """
        metadata = {
            'og_title': None,
            'og_description': None,
            'og_image': None,
            'og_type': None,
            'twitter_card': None,
            'author': None,
            'published_date': None,
            'keywords': None
        }

        try:
            request = urllib.request.Request(url, headers=self.headers)
            response = urllib.request.urlopen(request, timeout=10)
            html_content = response.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # Open Graph tags
            og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
            for tag in og_tags:
                prop = tag.get('property', '').replace('og:', '')
                content = tag.get('content', '')
                if prop:
                    metadata['og_' + prop] = content

            # Twitter Card tags
            twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
            for tag in twitter_tags:
                name = tag.get('name', '').replace('twitter:', '')
                content = tag.get('content', '')
                if name == 'card':
                    metadata['twitter_card'] = content

            # Author
            author_tag = soup.find('meta', attrs={'name': 'author'})
            if author_tag:
                metadata['author'] = author_tag.get('content', '')

            # Published date
            date_tags = soup.find_all('meta', property=re.compile(r'published_time|article:published_time'))
            if date_tags:
                metadata['published_date'] = date_tags[0].get('content', '')

            # Keywords
            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_tag:
                metadata['keywords'] = keywords_tag.get('content', '')

        except Exception as e:
            metadata['error'] = str(e)

        return metadata

    def verify_social_media_url(self, url):
        """
        Verify social media URLs (Twitter, Facebook, LinkedIn, Instagram)

        Args:
            url: Social media URL to verify

        Returns:
            dict: Verification results with platform-specific info
        """
        platform = None

        # Detect platform
        if 'twitter.com' in url or 'x.com' in url:
            platform = 'twitter'
        elif 'facebook.com' in url or 'fb.com' in url:
            platform = 'facebook'
        elif 'linkedin.com' in url:
            platform = 'linkedin'
        elif 'instagram.com' in url:
            platform = 'instagram'
        elif 'youtube.com' in url or 'youtu.be' in url:
            platform = 'youtube'

        result = self.verify_url(url)
        result['platform'] = platform

        return result

    def save_citation(self, url, verification_result, metadata=None):
        """
        Save citation to database

        Args:
            url: Citation URL
            verification_result: Result from verify_url()
            metadata: Optional metadata dict

        Returns:
            int: Citation ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        url_hash = self.generate_url_hash(url)

        # Check if citation already exists
        cursor.execute('SELECT id FROM citations WHERE url_hash = ?', (url_hash,))
        existing = cursor.fetchone()

        metadata_json = json.dumps(metadata) if metadata else None

        if existing:
            # Update existing citation
            citation_id = existing[0]
            cursor.execute('''
                UPDATE citations
                SET date_verified = CURRENT_TIMESTAMP,
                    status = ?,
                    http_status = ?,
                    title = ?,
                    content_hash = ?,
                    metadata = ?
                WHERE id = ?
            ''', (
                verification_result['status'],
                verification_result['http_status'],
                verification_result.get('title'),
                verification_result.get('content_hash'),
                metadata_json,
                citation_id
            ))
        else:
            # Insert new citation
            cursor.execute('''
                INSERT INTO citations
                (url, url_hash, title, status, http_status, content_hash, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                url,
                url_hash,
                verification_result.get('title'),
                verification_result['status'],
                verification_result['http_status'],
                verification_result.get('content_hash'),
                metadata_json
            ))
            citation_id = cursor.lastrowid

        # Add verification history
        cursor.execute('''
            INSERT INTO verification_history
            (citation_id, status, http_status)
            VALUES (?, ?, ?)
        ''', (citation_id, verification_result['status'], verification_result['http_status']))

        conn.commit()
        conn.close()

        return citation_id

    def check_citation(self, url, save_to_db=True, check_archive=True):
        """
        Comprehensive citation check

        Args:
            url: URL to check
            save_to_db: Whether to save results to database
            check_archive: Whether to check Wayback Machine

        Returns:
            dict: Complete citation verification report
        """
        print(colored("[*] Checking citation: %s" % url, 'cyan'))

        report = {
            'url': url,
            'timestamp': datetime.now().isoformat()
        }

        # Verify URL
        print(colored("  [+] Verifying URL accessibility...", 'yellow'))
        verification = self.verify_url(url)
        report['verification'] = verification

        if verification['status'] == 'verified':
            print(colored("  [+] URL verified (HTTP %d)" % verification['http_status'], 'green'))
        else:
            print(colored("  [-] URL verification failed: %s" % verification.get('error', 'Unknown'), 'red'))

        # Extract metadata
        if verification['status'] in ['verified', 'accessible']:
            print(colored("  [+] Extracting metadata...", 'yellow'))
            metadata = self.extract_metadata(url)
            report['metadata'] = metadata

        # Check archive
        if check_archive:
            print(colored("  [+] Checking Wayback Machine...", 'yellow'))
            archive = self.check_wayback_machine(url)
            report['archive'] = archive

            if archive['has_archive']:
                print(colored("  [+] Archived version available: %s" % archive['snapshot_url'], 'green'))
            else:
                print(colored("  [-] No archived version found", 'yellow'))

        # Save to database
        if save_to_db:
            citation_id = self.save_citation(url, verification, report.get('metadata'))
            report['citation_id'] = citation_id
            print(colored("  [+] Citation saved to database (ID: %d)" % citation_id, 'green'))

        return report

    def batch_check_citations(self, urls, delay=1):
        """
        Check multiple citations in batch

        Args:
            urls: List of URLs to check
            delay: Delay between requests in seconds

        Returns:
            list: List of citation reports
        """
        reports = []
        total = len(urls)

        print(colored("\n[*] Starting batch citation check (%d URLs)" % total, 'cyan', attrs=['bold']))

        for i, url in enumerate(urls, 1):
            print(colored("\n[%d/%d] Processing: %s" % (i, total, url), 'cyan', attrs=['bold']))

            try:
                report = self.check_citation(url)
                reports.append(report)
            except Exception as e:
                print(colored("  [!] Error: %s" % str(e), 'red'))
                reports.append({
                    'url': url,
                    'error': str(e),
                    'status': 'failed'
                })

            # Delay between requests
            if i < total and delay > 0:
                time.sleep(delay)

        return reports

    def generate_report(self, reports, output_file=None):
        """
        Generate citation verification report

        Args:
            reports: List of citation reports
            output_file: Optional file path to save report

        Returns:
            str: Formatted report
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("CITATION VERIFICATION REPORT")
        report_lines.append("Generated: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        report_lines.append("=" * 80)
        report_lines.append("")

        # Summary statistics
        total = len(reports)
        verified = sum(1 for r in reports if r.get('verification', {}).get('status') == 'verified')
        failed = sum(1 for r in reports if r.get('verification', {}).get('status') in ['error', 'failed', 'unreachable'])
        archived = sum(1 for r in reports if r.get('archive', {}).get('has_archive', False))

        report_lines.append("SUMMARY")
        report_lines.append("-" * 80)
        report_lines.append("Total Citations: %d" % total)
        report_lines.append("Verified: %d (%.1f%%)" % (verified, (verified * 100.0 / total) if total > 0 else 0))
        report_lines.append("Failed: %d (%.1f%%)" % (failed, (failed * 100.0 / total) if total > 0 else 0))
        report_lines.append("Archived: %d (%.1f%%)" % (archived, (archived * 100.0 / total) if total > 0 else 0))
        report_lines.append("")

        # Detailed results
        report_lines.append("DETAILED RESULTS")
        report_lines.append("-" * 80)

        for i, report in enumerate(reports, 1):
            report_lines.append("\n%d. %s" % (i, report['url']))

            verification = report.get('verification', {})
            report_lines.append("   Status: %s" % verification.get('status', 'unknown').upper())

            if verification.get('http_status'):
                report_lines.append("   HTTP Status: %d" % verification['http_status'])

            if verification.get('title'):
                report_lines.append("   Title: %s" % verification['title'])

            metadata = report.get('metadata', {})
            if metadata.get('author'):
                report_lines.append("   Author: %s" % metadata['author'])
            if metadata.get('published_date'):
                report_lines.append("   Published: %s" % metadata['published_date'])

            archive = report.get('archive', {})
            if archive.get('has_archive'):
                report_lines.append("   Archive: %s" % archive['snapshot_url'])

            if verification.get('error'):
                report_lines.append("   Error: %s" % verification['error'])

        report_lines.append("\n" + "=" * 80)

        report_text = "\n".join(report_lines)

        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(colored("\n[+] Report saved to: %s" % output_file, 'green'))

        return report_text

    def list_citations(self, status=None, limit=50):
        """
        List citations from database

        Args:
            status: Filter by status (verified, failed, etc.)
            limit: Maximum number of results

        Returns:
            list: List of citation records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute('''
                SELECT * FROM citations
                WHERE status = ?
                ORDER BY date_verified DESC
                LIMIT ?
            ''', (status, limit))
        else:
            cursor.execute('''
                SELECT * FROM citations
                ORDER BY date_verified DESC
                LIMIT ?
            ''', (limit,))

        citations = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return citations


def print_usage():
    """Print usage information"""
    print("""
Citation Checker and Verification Tool
=======================================

Usage:
    python citation_checker.py [options] <command> [arguments]

Commands:
    check <url>                  Check a single citation
    batch <file>                 Check multiple citations from file (one URL per line)
    list [status]                List citations from database
    report [output_file]         Generate report from last batch check

Options:
    -h, --help                   Show this help message
    --no-archive                 Skip Wayback Machine check
    --no-db                      Don't save to database
    --delay <seconds>            Delay between requests (default: 1)

Examples:
    python citation_checker.py check https://example.com
    python citation_checker.py batch urls.txt
    python citation_checker.py list verified
    python citation_checker.py report citations_report.txt
""")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]

    if command in ['-h', '--help']:
        print_usage()
        return

    checker = CitationChecker()

    if command == 'check':
        if len(sys.argv) < 3:
            print(colored("[!] Error: URL required", 'red'))
            print(colored("Usage: python citation_checker.py check <url>", 'yellow'))
            return

        url = sys.argv[2]
        report = checker.check_citation(url)

        print(colored("\n" + "=" * 80, 'cyan'))
        print(colored("CITATION CHECK COMPLETE", 'cyan', attrs=['bold']))
        print(colored("=" * 80, 'cyan'))
        print(json.dumps(report, indent=2))

    elif command == 'batch':
        if len(sys.argv) < 3:
            print(colored("[!] Error: Input file required", 'red'))
            print(colored("Usage: python citation_checker.py batch <file>", 'yellow'))
            return

        input_file = sys.argv[2]

        try:
            with open(input_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            reports = checker.batch_check_citations(urls)

            # Generate and display report
            report_text = checker.generate_report(reports, output_file='citation_report.txt')
            print(colored("\n" + report_text, 'white'))

        except IOError as e:
            print(colored("[!] Error reading file: %s" % str(e), 'red'))

    elif command == 'list':
        status = sys.argv[2] if len(sys.argv) > 2 else None
        citations = checker.list_citations(status=status)

        print(colored("\nCITATIONS DATABASE", 'cyan', attrs=['bold']))
        print(colored("=" * 80, 'cyan'))

        for citation in citations:
            status_color = 'green' if citation['status'] == 'verified' else 'red'
            print(colored("\n[%d] %s" % (citation['id'], citation['url']), 'white', attrs=['bold']))
            print(colored("    Status: %s" % citation['status'].upper(), status_color))
            if citation['title']:
                print(colored("    Title: %s" % citation['title'], 'white'))
            print(colored("    Verified: %s" % citation['date_verified'], 'yellow'))

    else:
        print(colored("[!] Unknown command: %s" % command, 'red'))
        print_usage()


if __name__ == '__main__':
    main()
