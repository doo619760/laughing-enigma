# Citation Checker and Verification Tool

A comprehensive OSINT tool for verifying citations, checking link validity, archiving sources, and generating verification reports for intelligence investigations.

## Features

- **URL Verification**: Check if URLs are accessible and valid
- **Metadata Extraction**: Extract Open Graph, Twitter Cards, and other metadata
- **Archive Checking**: Verify if archived versions exist on Wayback Machine
- **Social Media Support**: Platform-specific verification for Twitter, Facebook, LinkedIn, Instagram, YouTube
- **Database Storage**: SQLite database for tracking citation verification history
- **Batch Processing**: Check multiple citations from a file
- **Report Generation**: Create detailed verification reports
- **Content Hashing**: Track content changes over time

## Installation

### Prerequisites

This tool is designed for Python 2.7 (compatible with the existing OSINT tools in this repository).

### Required Dependencies

```bash
pip install termcolor BeautifulSoup httplib2
```

### Already Installed (if using fbstalker/geostalker)

The following dependencies are already available if you've set up fbstalker or geostalker:
- urllib2 (built-in)
- sqlite3 (built-in)
- BeautifulSoup
- termcolor
- httplib2

## Usage

### Command Line Interface

#### Check a Single Citation

```bash
python citation_checker.py check <url>
```

Example:
```bash
python citation_checker.py check https://www.bbc.com/news/technology
```

#### Batch Check Multiple Citations

Create a text file with one URL per line:

```bash
python citation_checker.py batch <urls_file>
```

Example:
```bash
python citation_checker.py batch example_citations.txt
```

The tool will:
- Check each URL sequentially
- Extract metadata
- Check for archived versions
- Save results to database
- Generate a report file (`citation_report.txt`)

#### List Citations from Database

```bash
# List all citations
python citation_checker.py list

# List only verified citations
python citation_checker.py list verified

# List only failed citations
python citation_checker.py list failed
```

### Python API Usage

```python
from citation_checker import CitationChecker

# Initialize checker
checker = CitationChecker(db_path="my_citations.db")

# Check a single URL
report = checker.check_citation("https://example.com")

# Verify URL only (no metadata or archive check)
result = checker.verify_url("https://example.com")

# Extract metadata
metadata = checker.extract_metadata("https://example.com")

# Check Wayback Machine
archive = checker.check_wayback_machine("https://example.com")

# Batch check multiple URLs
urls = ["https://example1.com", "https://example2.com"]
reports = checker.batch_check_citations(urls, delay=2)

# Generate report
report_text = checker.generate_report(reports, output_file="report.txt")
```

## Output Examples

### Single Citation Check

```
[*] Checking citation: https://www.bbc.com/news
  [+] Verifying URL accessibility...
  [+] URL verified (HTTP 200)
  [+] Extracting metadata...
  [+] Checking Wayback Machine...
  [+] Archived version available: http://web.archive.org/web/...
  [+] Citation saved to database (ID: 1)
```

### Batch Report

```
================================================================================
CITATION VERIFICATION REPORT
Generated: 2025-10-24 15:30:45
================================================================================

SUMMARY
--------------------------------------------------------------------------------
Total Citations: 10
Verified: 8 (80.0%)
Failed: 2 (20.0%)
Archived: 7 (70.0%)

DETAILED RESULTS
--------------------------------------------------------------------------------

1. https://www.bbc.com/news
   Status: VERIFIED
   HTTP Status: 200
   Title: BBC News - Home
   Archive: http://web.archive.org/web/20251024123045/https://www.bbc.com/news
```

## Database Schema

### Citations Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| url | TEXT | Original URL |
| url_hash | TEXT | SHA-256 hash of URL (unique) |
| title | TEXT | Page title |
| author | TEXT | Author metadata |
| date_published | TEXT | Publication date |
| date_verified | TIMESTAMP | Last verification date |
| status | TEXT | Verification status |
| http_status | INTEGER | HTTP status code |
| content_hash | TEXT | MD5 hash of content |
| archived_url | TEXT | Wayback Machine URL |
| metadata | TEXT | JSON metadata |
| notes | TEXT | User notes |

### Verification History Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| citation_id | INTEGER | Foreign key to citations |
| verification_date | TIMESTAMP | Check timestamp |
| status | TEXT | Status at time of check |
| http_status | INTEGER | HTTP status code |
| changes_detected | BOOLEAN | Content changed flag |

## Verification Statuses

- **verified**: URL is accessible and returns HTTP 200
- **accessible**: URL is accessible but returns non-200 status
- **error**: HTTP error (404, 403, etc.)
- **unreachable**: Network/DNS error
- **failed**: Other error occurred
- **unknown**: Not yet verified

## OSINT Use Cases

### Intelligence Gathering

1. **Source Verification**: Verify the authenticity and accessibility of intelligence sources
2. **Evidence Preservation**: Archive snapshots of web sources before they disappear
3. **Citation Trail**: Track citation history for investigations
4. **Social Media OSINT**: Verify social media profiles and posts
5. **Content Monitoring**: Detect when cited sources change or go offline

### Integration with Existing Tools

This tool complements the existing OSINT tools in this repository:

- **fbstalker**: Verify Facebook URLs extracted during stalking operations
- **geostalker**: Verify geolocation-based sources and social media links
- **Maltego**: Generate citation verification data for Maltego graphs

### Example Workflow

```bash
# 1. Use fbstalker to gather Facebook data
python fbstalker1.py ...

# 2. Extract URLs from the collected data

# 3. Verify all citations
python citation_checker.py batch facebook_urls.txt

# 4. Review verification report
cat citation_report.txt

# 5. Archive important sources
# URLs are automatically checked against Wayback Machine
```

## Advanced Features

### Content Change Detection

The tool generates MD5 hashes of page content. Re-checking a URL will detect if content has changed:

```python
# First check
report1 = checker.check_citation("https://example.com")

# Later check (content may have changed)
report2 = checker.check_citation("https://example.com")

# Compare content_hash values
if report1['verification']['content_hash'] != report2['verification']['content_hash']:
    print "Content has changed!"
```

### Custom Database Queries

```python
import sqlite3

conn = sqlite3.connect("citation_checker.db")
cursor = conn.cursor()

# Find all citations that failed
cursor.execute("SELECT url, error FROM citations WHERE status = 'failed'")

# Find citations verified in last 24 hours
cursor.execute("""
    SELECT url, status, date_verified
    FROM citations
    WHERE date_verified > datetime('now', '-1 day')
""")
```

## Options

- `--no-archive`: Skip Wayback Machine checking (faster)
- `--no-db`: Don't save to database
- `--delay <seconds>`: Set delay between batch requests (default: 1)

Example:
```bash
python citation_checker.py batch urls.txt --delay 2 --no-archive
```

## Troubleshooting

### SSL Certificate Errors

If you encounter SSL errors, you can modify the code to disable SSL verification (not recommended for production):

```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

### Timeout Errors

Increase timeout for slow websites:

```python
checker = CitationChecker()
result = checker.verify_url("https://slow-site.com", timeout=30)
```

### Rate Limiting

If checking many URLs, increase delay to avoid rate limiting:

```bash
python citation_checker.py batch urls.txt --delay 5
```

## Privacy and Ethics

- This tool is designed for OSINT and defensive security research
- Respect robots.txt and website terms of service
- Be mindful of rate limiting and server load
- Only use for legitimate intelligence gathering and verification
- Do not use for harassment or unauthorized access

## Future Enhancements

- [ ] Screenshot capture for visual archiving
- [ ] Integration with archive.is and other archive services
- [ ] PDF generation for reports
- [ ] Citation format export (BibTeX, APA, MLA)
- [ ] Browser automation for JavaScript-heavy sites
- [ ] Bulk download and local archiving
- [ ] Change monitoring with notifications
- [ ] Integration with Maltego
- [ ] GraphML output for network analysis

## Contributing

This tool is part of the OSINT tool suite. Contributions are welcome!

## License

This tool follows the same license as the parent OSINT project.

## Author

Created as part of the OSINT Citation Verification Project.

## Support

For issues or questions, please refer to the main repository documentation.
