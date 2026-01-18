# Box Discovery Skill

You are helping a user read case files from Box.com and draft legal discovery. This skill enables Claude to:

1. **Connect to Box.com** - Read files from Box folders, individual files, or shared links
2. **Parse Legal Documents** - Extract parties, claims, facts, dates, and key information
3. **Generate Discovery** - Create interrogatories, requests for production, and requests for admission
4. **Draft Responses** - Respond to incoming discovery based on case file analysis

## Usage

When the user wants to work with Box.com case files for discovery, use the BoxDiscoverySkill.

### Environment Setup

The user must have one of these environment variables set:
- `BOX_ACCESS_TOKEN` - OAuth 2.0 access token
- `BOX_DEVELOPER_TOKEN` - Developer token (for testing, expires in 1 hour)

### Available Actions

1. **Analyze Case** - Parse files and show case summary
2. **Generate Interrogatories** - Create questions for the opposing party
3. **Generate Requests for Production** - Request documents
4. **Generate Requests for Admission** - Request fact admissions
5. **Respond to Discovery** - Draft responses to incoming discovery

### Example Workflows

**Analyze a case folder:**
```python
from skills.box_discovery import BoxDiscoverySkill, SkillConfig

config = SkillConfig(
    box_folder_id="123456789",
    action="analyze"
)
skill = BoxDiscoverySkill(config)
print(skill.run())
```

**Generate interrogatories:**
```python
config = SkillConfig(
    box_folder_id="123456789",
    client_role="plaintiff",
    action="generate_interrogatories"
)
skill = BoxDiscoverySkill(config)
print(skill.run())
```

**Respond to discovery:**
```python
skill = BoxDiscoverySkill()
skill.load_case_from_folder("123456789")

# Incoming interrogatories
interrogatories = [
    (1, "State your full name and address."),
    (2, "Describe all damages you claim."),
]

responses = skill.respond_to_interrogatories(interrogatories)
print(responses.to_document())
```

## Document Types Supported

- PDF (.pdf)
- Word Documents (.doc, .docx)
- Text Files (.txt)
- Rich Text (.rtf)
- OpenDocument (.odt)

## Discovery Types

### Interrogatories
Written questions that must be answered under oath. Categories include:
- Identity (personal information, witnesses)
- Incident (facts of the case)
- Documents (evidence and records)
- Damages (injuries, losses)
- Expert (expert witnesses)
- Communications (correspondence)

### Requests for Production
Demands for documents and tangible evidence. Categories include:
- Documents, Communications, Financial records
- Photographs, Medical records
- Expert materials, Insurance information

### Requests for Admission
Requests to admit or deny specific facts or document authenticity.

## Response Drafting

The skill can draft responses including:
- Substantive answers based on case file content
- Standard legal objections (vague, overbroad, privilege, etc.)
- References to responsive documents
- Appropriate qualifications and reservations

## Important Notes

- Always review generated discovery before filing
- Generated responses are drafts requiring attorney review
- Some jurisdictions have limits on discovery (e.g., 25 interrogatories)
- Attorney-client privilege considerations apply
