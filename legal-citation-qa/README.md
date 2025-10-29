# Legal Citation QA System

> **Automated, local-first citation and quote validation for legal briefs.**

A comprehensive system that automatically extracts, validates, and audits every citation and quote in your legal briefs before filing. Fully automated, local-first, and auditable.

---

## What It Does

This system provides pre-filing QA for legal documents by:

- **Citation Extraction & Validation**: Automatically parses every citation, matches to the correct opinion/cluster in CourtListener, and confirms reporter + pinpoint accuracy
- **Quote Verification**: Compares quoted passages in your brief to source opinion text using fuzzy string matching (RapidFuzz), flagging mismatches or altered quotes
- **Parallel Citation Checking**: Identifies missing or incorrect parallel reporter citations per Bluebook Rule 10.3.1 and local court rules
- **Audit Trail**: Generates signed JSON/HTML reports, stored in Box and committed to a git repository for immutability

---

## Key Features

### 🔍 **Citation Analysis**
- Extracts citations using [eyecite](https://github.com/freelawproject/eyecite)
- Validates against [CourtListener](https://www.courtlistener.com/) API
- Supports full, short, id., and supra citations
- Pinpoint verification

### 📝 **Quote Matching**
- Fuzzy matching with [RapidFuzz](https://github.com/maxbachmann/RapidFuzz)
- 98%+ similarity threshold for exact matches
- Flags alterations (brackets, ellipses)
- Context-aware matching

### ⚖️ **Parallel Citations**
- Pre-configured rules for CA, 9th Cir., S.D. Cal., NY, TX, and more
- Bluebook Rule 10.3.1 compliance
- Auto-suggests missing parallel cites
- Customizable per jurisdiction

### 📊 **Reports**
- **JSON**: Signed, structured data for API integration
- **HTML**: Human-readable report with color-coded status (green/yellow/red)
- Per-citation breakdown with confidence scores
- Flagged issues with actionable warnings

### 🔐 **Audit Trail**
- Append-only git repository
- Cryptographic signatures (SHA-256)
- Automatic push to remote backup
- Full history tracking

---

## Architecture

```
┌─────────────────┐
│  Box Webhook    │  ← Document uploaded to /drafts
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Citation QA Pipeline                │
│                                             │
│  1. Text Extraction (DOCX/PDF)             │
│  2. Citation Parsing (eyecite)             │
│  3. Quote Extraction                        │
│  4. CourtListener Lookup                    │
│  5. Quote Matching (RapidFuzz)             │
│  6. Parallel Citation Check                 │
│  7. Report Generation                       │
│  8. Sign & Audit                            │
└────────┬────────────────────────────────────┘
         │
         ├─────► Box (/qa-checks/)
         └─────► Git Audit Repo
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- CourtListener API token (free: [courtlistener.com/api](https://www.courtlistener.com/api/rest-info/))
- Box Developer account (optional, for webhook integration)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone repository
cd legal-citation-qa

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env

# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f
```

The webhook server will be available at `http://localhost:8000`.

#### Option 2: Local Development

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export COURTLISTENER_TOKEN="your_token_here"
export OUTPUT_DIR="./output"
export GIT_AUDIT_PATH="./audit"

# Run worker directly
python src/worker.py /path/to/brief.docx

# Or run webhook server
python src/webhook_server.py
```

---

## Usage

### 1. Command-Line (Standalone)

Process a single document:

```bash
python src/worker.py /path/to/brief.docx \
  --courtlistener-token YOUR_TOKEN \
  --output-dir ./reports \
  --git-audit-path ./audit
```

### 2. Webhook Mode (Box Integration)

1. **Configure Box Webhook**:
   - Go to Box Developer Console → Webhooks
   - Create webhook for your `/drafts` folder
   - Target URL: `https://your-server.com/webhook/box`
   - Events: `FILE.UPLOADED`, `FILE.COPIED`

2. **Drop a .docx or .pdf in Box**:
   - System auto-processes on upload
   - Report appears in `/qa-checks/` folder
   - Committed to git audit trail

3. **Check Reports**:
   - HTML report: Visual summary with color-coded flags
   - JSON report: Structured data for integrations

### 3. API Endpoints

The webhook server exposes:

- `GET /health` - Health check
- `POST /webhook/box` - Box webhook receiver
- `POST /process?file_id=123` - Manual processing trigger
- `GET /audit/status` - Audit trail status
- `GET /audit/history?limit=50` - Audit history

---

## Configuration

### Court Profiles

Edit `config/court_profiles.json` to customize:

- Parallel citation requirements per jurisdiction
- Quote matching thresholds
- Allowed alterations (brackets, ellipses)
- Bluebook rules

**Example**:

```json
{
  "california_supreme": {
    "parallel_requirement": "required",
    "quote_match_threshold": 98.0,
    "parallel_reporters": ["P.3d", "Cal. Rptr. 3d"]
  }
}
```

### Application Settings

Edit `config/config.yaml` for:

- Processing thresholds
- Rate limits
- Storage paths
- Feature flags
- Logging

---

## Report Interpretation

### Status Colors

- 🟢 **Green**: All citations valid, quotes match exactly (≥98% similarity)
- 🟡 **Yellow**: Citations valid, quotes partially match (90-97%)
- 🔴 **Red**: Invalid citations, missing parallels, or quotes don't match (<90%)

### Common Flags

| Flag | Meaning | Action |
|------|---------|--------|
| `Missing required parallel citation` | State court cite lacks parallel reporter | Add Cal. Rptr. / P.3d cite |
| `Quote does not match source exactly` | Text differs from opinion | Verify quotation accuracy |
| `Contains bracketed alterations` | Quote has `[...]` edits | Ensure alterations are accurate |
| `Citation not found in CourtListener` | Reporter/page mismatch | Double-check citation |
| `No citation found near this quote` | Quote missing citation | Add citation |

---

## Development

### Project Structure

```
legal-citation-qa/
├── src/
│   ├── citation_extractor.py    # eyecite wrapper
│   ├── courtlistener_client.py  # CourtListener API client
│   ├── quote_matcher.py         # RapidFuzz matching engine
│   ├── parallel_checker.py      # Parallel citation validator
│   ├── text_extractor.py        # DOCX/PDF extraction
│   ├── report_generator.py      # JSON/HTML reports
│   ├── box_handler.py           # Box SDK integration
│   ├── git_audit.py             # Git audit trail
│   ├── worker.py                # Main pipeline orchestrator
│   └── webhook_server.py        # FastAPI webhook server
├── config/
│   ├── court_profiles.json      # Jurisdiction rules
│   └── config.yaml              # App configuration
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

### Mock Mode (No Credentials)

For testing without CourtListener/Box/Git credentials:

```bash
python src/worker.py /path/to/brief.docx --mock
```

This uses mock services that simulate API responses.

---

## CourtListener API

This system relies on the [Free Law Project's CourtListener API](https://www.courtlistener.com/api/rest-info/).

**Getting a Token**:
1. Create free account: [courtlistener.com/sign-up](https://www.courtlistener.com/sign-up/)
2. Generate token: Profile → API → Create Token
3. Set in `.env`: `COURTLISTENER_TOKEN=your_token`

**Rate Limits**:
- Free tier: ~1 request/second
- Paid tiers: Higher limits available
- System auto-throttles to comply

---

## Security & Privacy

### Local-First

- All processing happens on your infrastructure
- No third-party analytics or tracking
- Documents never sent to external services (except CourtListener for public opinions)

### Credentials

- Store `.env` securely (never commit to git)
- Use Box JWT auth for production (not developer tokens)
- Git audit repo should be private
- Consider encrypting git remote

### Audit Trail

- SHA-256 signatures on all reports
- Append-only git log prevents tampering
- Timestamps in UTC
- Full attribution in commit messages

---

## Troubleshooting

### "No text could be extracted"

**Cause**: Scanned PDF or corrupted document
**Fix**: Use OCR tool first, or re-save as native PDF/DOCX

### "Citation not found in CourtListener"

**Cause**: Typo in citation, or case not in database
**Fix**: Verify reporter abbreviation, check [courtlistener.com/c/](https://www.courtlistener.com/c/)

### "Box webhook signature verification failed"

**Cause**: Incorrect signing key or payload tampering
**Fix**: Copy exact key from Box Developer Console, check firewalls

### "Git push failed"

**Cause**: No remote configured or auth failure
**Fix**: Set `GIT_REMOTE_URL` and ensure SSH keys or HTTPS credentials

---

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use strong, unique credentials
- [ ] Enable HTTPS with reverse proxy (nginx, Caddy)
- [ ] Set up automated backups of git audit repo
- [ ] Configure log rotation
- [ ] Set resource limits in docker-compose.yml
- [ ] Enable monitoring (Prometheus, Datadog, etc.)
- [ ] Set up alerts for failed jobs

### Scaling

For high-volume processing:

1. **Horizontal Scaling**: Run multiple worker containers behind load balancer
2. **Queue System**: Add Redis + RQ for job queue
3. **Database**: Store reports in PostgreSQL instead of files
4. **Cache**: Use Redis to cache CourtListener responses

---

## Roadmap

- [ ] Support for additional citation formats (ALWD, Canadian, UK)
- [ ] ML-based quote matching for paraphrases
- [ ] Integration with Westlaw/Lexis APIs
- [ ] Browser extension for Google Docs
- [ ] Bulk processing API
- [ ] Citation network analysis
- [ ] Shepardize/KeyCite integration

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

**MIT License**

Copyright (c) 2025 Legal Citation QA Project

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Acknowledgments

- [Free Law Project](https://free.law/) for CourtListener API
- [eyecite](https://github.com/freelawproject/eyecite) for citation extraction
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) for fuzzy matching
- Inspired by the need for better legal tech tooling

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/legal-citation-qa/issues)
- **Documentation**: [Wiki](https://github.com/your-org/legal-citation-qa/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/legal-citation-qa/discussions)

---

**Built with ❤️ for lawyers, by lawyers (and developers who work with them).**
