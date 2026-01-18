# Box Discovery Skill

A Claude Code skill for reading legal case files from Box.com and drafting discovery requests and responses.

## Features

- **Box.com Integration**: Securely access case files stored in Box.com
- **Document Parsing**: Extract key information from legal documents (complaints, answers, motions, depositions, etc.)
- **Discovery Generation**: Automatically generate interrogatories, requests for production, and requests for admission
- **Response Drafting**: Draft responses to incoming discovery with appropriate objections
- **Case Analysis**: Build comprehensive case profiles from multiple documents

## Installation

### Prerequisites

- Python 3.7+
- Box.com account with API access

### Setup

1. Clone this repository
2. Install dependencies (if using pip):
   ```bash
   pip install requests
   ```

3. Set up Box.com authentication:
   - Go to [Box Developer Console](https://developer.box.com/)
   - Create a new app or use existing credentials
   - Get your access token

4. Set environment variable:
   ```bash
   export BOX_ACCESS_TOKEN="your_access_token_here"
   # OR for testing:
   export BOX_DEVELOPER_TOKEN="your_developer_token_here"
   ```

## Usage

### Command Line

```bash
# Analyze a case folder
python -m skills.box_discovery.skill --folder-id 123456789 --action analyze

# Generate interrogatories as plaintiff
python -m skills.box_discovery.skill --folder-id 123456789 --action generate_interrogatories --role plaintiff

# Generate all discovery types
python -m skills.box_discovery.skill --folder-id 123456789 --action generate_all --output discovery.txt

# Use a shared link
python -m skills.box_discovery.skill --shared-link "https://app.box.com/s/abc123" --action analyze
```

### Python API

```python
from skills.box_discovery import BoxDiscoverySkill, SkillConfig

# Initialize skill
skill = BoxDiscoverySkill()

# Load case from Box folder
case = skill.load_case_from_folder("123456789")

# Get case summary
print(skill.get_case_summary())

# Generate interrogatories
interrogatories = skill.generate_interrogatories(
    categories=["identity", "incident", "damages"],
    max_count=25
)
print(interrogatories.to_document())

# Generate requests for production
rfps = skill.generate_requests_for_production(
    categories=["documents", "communications", "financial"]
)
print(rfps.to_document())

# Generate requests for admission
rfas = skill.generate_requests_for_admission(
    facts=["Defendant breached the contract on January 15, 2024."],
    documents=["Contract dated June 1, 2023"]
)
print(rfas.to_document())

# Respond to incoming discovery
incoming_interrogatories = [
    (1, "State your full legal name and address."),
    (2, "Identify all witnesses to the incident."),
    (3, "Describe the damages you claim to have suffered."),
]

responses = skill.respond_to_interrogatories(incoming_interrogatories)
print(responses.to_document())
```

### With Configuration

```python
from skills.box_discovery import BoxDiscoverySkill, SkillConfig

config = SkillConfig(
    box_folder_id="123456789",
    client_role="defendant",
    action="generate_all",
    output_format="text",
    output_path="discovery_output.txt"
)

skill = BoxDiscoverySkill(config)
result = skill.run()
```

## Supported Document Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | .pdf | Uses Box text extraction |
| Word | .doc, .docx | Modern and legacy formats |
| Text | .txt | Plain text |
| RTF | .rtf | Rich text format |
| OpenDocument | .odt | LibreOffice/OpenOffice |

## Document Type Recognition

The skill automatically identifies legal document types:

- **Complaints** - Initial pleadings with causes of action
- **Answers** - Responses with affirmative defenses
- **Motions** - Procedural requests to the court
- **Depositions** - Sworn testimony transcripts
- **Interrogatories** - Written questions
- **Requests for Production** - Document demands
- **Requests for Admission** - Fact verification requests
- **Contracts** - Agreements between parties
- **Correspondence** - Letters and communications
- **Court Orders** - Judicial rulings
- **Affidavits** - Sworn statements

## Discovery Generation

### Interrogatory Categories

| Category | Description |
|----------|-------------|
| identity | Personal info, witness identification |
| incident | Facts and circumstances |
| documents | Document identification |
| damages | Injury and loss details |
| expert | Expert witness information |
| communications | Correspondence and statements |

### Request for Production Categories

| Category | Description |
|----------|-------------|
| documents | General documents |
| communications | Emails, letters, messages |
| financial | Invoices, payments, records |
| photographs | Photos, videos, recordings |
| medical | Medical records and bills |
| expert | Expert reports and materials |
| insurance | Policies and correspondence |

## Response Features

When drafting responses, the skill includes:

- **Substantive Responses**: Based on case file analysis
- **Standard Objections**:
  - Vague/Ambiguous
  - Overbroad
  - Unduly burdensome
  - Attorney-client privilege
  - Work product doctrine
  - Proprietary information
  - Not relevant
- **Document References**: Links to responsive documents
- **Qualifications**: Investigation ongoing, will supplement

## Box.com Authentication

### Developer Token (Testing)
1. Go to your Box app in the Developer Console
2. Generate a Developer Token
3. Set `BOX_DEVELOPER_TOKEN` environment variable
4. Note: Token expires in 1 hour

### OAuth 2.0 (Production)
1. Implement OAuth flow to get access token
2. Set `BOX_ACCESS_TOKEN` environment variable
3. Implement token refresh as needed

### Environment Variables

| Variable | Description |
|----------|-------------|
| `BOX_ACCESS_TOKEN` | OAuth 2.0 access token |
| `BOX_DEVELOPER_TOKEN` | Developer token for testing |
| `BOX_CLIENT_ID` | OAuth client ID (optional) |
| `BOX_CLIENT_SECRET` | OAuth client secret (optional) |

## API Reference

### BoxDiscoverySkill

Main skill class.

**Methods:**
- `load_case_from_folder(folder_id)` - Load case from Box folder
- `load_case_from_file(file_id)` - Load single file
- `load_case_from_shared_link(url)` - Load from shared link
- `analyze_case()` - Get structured case analysis
- `get_case_summary()` - Get human-readable summary
- `generate_interrogatories(...)` - Generate interrogatories
- `generate_requests_for_production(...)` - Generate RFPs
- `generate_requests_for_admission(...)` - Generate RFAs
- `respond_to_interrogatories(...)` - Draft interrogatory responses
- `respond_to_rfp(...)` - Draft RFP responses
- `respond_to_rfa(...)` - Draft RFA responses

### SkillConfig

Configuration options.

**Fields:**
- `box_folder_id` - Box folder ID
- `box_file_id` - Box file ID
- `box_shared_link` - Box shared link URL
- `client_role` - "plaintiff" or "defendant"
- `action` - Action to perform
- `output_format` - "text", "json", or "markdown"
- `output_path` - Output file path

## Limitations

- Jurisdictional variations not fully covered
- Complex formatting may require manual adjustment
- OCR for scanned documents not included (relies on Box)
- Attorney review required before filing

## License

MIT License

## Disclaimer

This tool generates draft discovery documents for attorney review. It is not a substitute for legal advice. All generated documents should be reviewed and approved by a licensed attorney before filing with any court.
