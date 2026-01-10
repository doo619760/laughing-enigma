# California Court Case Tracker

A comprehensive Python application for tracking court cases in California through the Register of Actions, Case Management Orders, Court Filings, Court Calendar, and documents served via OneLegal. The application calculates deadlines and other controlling dates based on the California Code of Civil Procedure.

## Features

### Case Management
- Track unlimited civil, limited civil, small claims, unlawful detainer, and other California case types
- Store case information including court, county, department, and judge
- Track case status through the litigation lifecycle

### Register of Actions (ROA) Tracking
- Import and track ROA entries from court systems
- Automatic document type inference from ROA descriptions
- Link ROA entries to documents and events
- Generate ROA reports

### Case Management Order (CMO) Tracking
- Track all dates from Case Management Orders
- Automatic deadline generation from CMO dates
- Support for superseded CMOs
- Track discovery cutoffs, motion deadlines, and trial dates

### Court Filings Tracker
- Track all documents filed in a case
- Record service of documents on parties
- Track service methods and calculate service extensions
- Link documents to hearings and responses

### Court Calendar Integration
- Track hearings, conferences, and trial dates
- Automatic deadline creation for hearings (opposition/reply deadlines)
- Track hearing results and rulings
- Continue or vacate scheduled events

### OneLegal Service Tracking
- Track electronic service transactions
- Record service dates for deadline calculations
- Monitor delivery status
- Generate proof of service records

### Deadline Calculator
Based on California Code of Civil Procedure:
- **Discovery Deadlines** (CCP 2030.260, 2031.260, 2033.250)
  - Interrogatories: 30 days + service extension
  - Requests for Production: 30 days + service extension
  - Requests for Admission: 30 days + service extension
- **Motion Deadlines** (CCP 1005(b))
  - Notice: 16 calendar days + 2 court days before hearing
  - Opposition: 9 court days before hearing
  - Reply: 5 court days before hearing
- **Summary Judgment Deadlines** (CCP 437c)
  - Notice/Moving Papers: 75 calendar days before hearing
  - Opposition: 14 calendar days before hearing
  - Reply: 5 calendar days before hearing
- **Service Extensions** (CCP 1013, 1010.6)
  - Personal Service: 0 days
  - Electronic Service: +2 court days
  - Mail Service (in CA): +5 calendar days
  - Mail Service (out of CA): +10 calendar days
  - Overnight Delivery: +2 court days

## Installation

```bash
# Clone the repository
cd /path/to/laughing-enigma

# Install in development mode
pip install -e .

# Or run directly
python -m ca_court_tracker
```

## Quick Start

### Create a Case

```bash
ca-court-tracker case create \
  --number 24STCV01234 \
  --name "Smith v. Jones" \
  --type unlimited_civil \
  --court "Los Angeles Superior Court" \
  --county "Los Angeles" \
  --department 31 \
  --judge "Hon. Jane Smith" \
  --filed 01/15/2024
```

### Add Parties

```bash
ca-court-tracker party add \
  --case 24STCV01234 \
  --name "John Smith" \
  --type plaintiff \
  --attorney "Jane Attorney" \
  --email "jattorney@lawfirm.com"

ca-court-tracker party add \
  --case 24STCV01234 \
  --name "ABC Corporation" \
  --type defendant
```

### File Documents

```bash
ca-court-tracker document file \
  --case 24STCV01234 \
  --title "Complaint for Damages" \
  --type complaint \
  --date 01/15/2024 \
  --party "John Smith"
```

### Schedule Hearings

```bash
ca-court-tracker event add \
  --case 24STCV01234 \
  --title "Motion to Compel Discovery" \
  --type motion_hearing \
  --date 03/15/2024 \
  --time 09:00 \
  --department 31 \
  --create-deadlines
```

### Calculate Deadlines

```bash
# Calculate discovery response deadline
ca-court-tracker calculate discovery \
  --served 01/20/2024 \
  --type interrogatories \
  --method electronic

# Calculate motion deadlines
ca-court-tracker calculate motion \
  --hearing 03/15/2024

# Calculate summary judgment deadlines
ca-court-tracker calculate motion \
  --hearing 06/01/2024 \
  --msj
```

### View Upcoming Deadlines

```bash
# Show all upcoming deadlines
ca-court-tracker deadline upcoming --days 14

# List deadlines for a specific case
ca-court-tracker deadline list --case 24STCV01234
```

### Generate Reports

```bash
# Full case report
ca-court-tracker report case 24STCV01234

# Calendar report
ca-court-tracker report calendar --case 24STCV01234 --days 60

# Deadline report
ca-court-tracker report deadlines --days 30
```

## Python API Usage

```python
from ca_court_tracker import CaseManager, CaseType, PartyType, DocumentType, ServiceMethod
from datetime import date

# Initialize the case manager
manager = CaseManager(data_dir='./case_data')

# Create a case
case = manager.create_case(
    case_number='24STCV01234',
    case_name='Smith v. Jones',
    case_type=CaseType.UNLIMITED_CIVIL,
    court_name='Los Angeles Superior Court',
    county='Los Angeles',
    filing_date=date(2024, 1, 15)
)

# Add parties
plaintiff = manager.add_party(
    case_id=case.id,
    name='John Smith',
    party_type=PartyType.PLAINTIFF
)

defendant = manager.add_party(
    case_id=case.id,
    name='ABC Corporation',
    party_type=PartyType.DEFENDANT
)

# File a document
complaint = manager.file_document(
    case_id=case.id,
    title='Complaint for Damages',
    document_type=DocumentType.COMPLAINT,
    filing_date=date(2024, 1, 15),
    filed_by_party_id=plaintiff.id
)

# Record service
manager.serve_document(
    document_id=complaint.id,
    party_id=defendant.id,
    service_method=ServiceMethod.ELECTRONIC_SERVICE,
    service_date=date(2024, 1, 20)
)

# Create response deadline
deadline = manager.create_response_deadline(
    document_id=complaint.id,
    responsible_party_id=defendant.id
)

print(f"Answer due: {deadline.due_date}")  # 30 days + 2 court days for e-service

# Save data
manager.save()
```

## Deadline Calculation Examples

```python
from ca_court_tracker.services import DeadlineCalculator
from datetime import date

calc = DeadlineCalculator()

# Calculate motion deadlines for a hearing on March 15, 2024
motion_deadlines = calc.calculate_motion_deadlines(date(2024, 3, 15))
print(f"Opposition due: {motion_deadlines['opposition_deadline']}")
print(f"Reply due: {motion_deadlines['reply_deadline']}")

# Calculate MSJ deadlines
msj_deadlines = calc.calculate_msj_deadlines(date(2024, 6, 1))
print(f"MSJ filing deadline: {msj_deadlines['moving_papers_deadline']}")

# Add court days (excluding weekends and holidays)
deadline = calc.add_court_days(date(2024, 1, 15), 9)

# Check if a date is a court day
is_open = calc.is_court_day(date(2024, 7, 4))  # False - Independence Day
```

## Project Structure

```
ca_court_tracker/
├── __init__.py           # Package initialization
├── __main__.py           # Entry point for module execution
├── cli.py                # Command-line interface
├── models/
│   ├── __init__.py
│   ├── case.py           # Case model
│   ├── party.py          # Party and Attorney models
│   ├── document.py       # Document and Service models
│   ├── event.py          # Court event model
│   └── deadline.py       # Deadline model
├── services/
│   ├── __init__.py
│   ├── case_manager.py   # Central case management service
│   ├── deadline_calculator.py  # CA deadline calculations
│   ├── roa_tracker.py    # Register of Actions tracker
│   ├── cmo_tracker.py    # Case Management Order tracker
│   ├── filing_tracker.py # Court filings tracker
│   ├── calendar_tracker.py # Court calendar tracker
│   └── onelegal_tracker.py # OneLegal service tracker
└── utils/
    ├── __init__.py
    ├── date_utils.py     # Date utility functions
    └── validators.py     # Input validation
```

## California Court Holidays

The deadline calculator accounts for California court holidays:
- New Year's Day
- Martin Luther King Jr. Day
- Presidents' Day
- Cesar Chavez Day
- Memorial Day
- Independence Day
- Labor Day
- Indigenous Peoples' Day
- Veterans Day
- Thanksgiving Day and day after
- Christmas Day

## Legal References

- **CCP 12a**: Court day calculation rules
- **CCP 1005(b)**: Motion notice and response deadlines
- **CCP 437c**: Summary judgment motion deadlines
- **CCP 1010.6**: Electronic service rules
- **CCP 1013**: Service extension rules
- **CCP 2030.260**: Interrogatory response deadline
- **CCP 2031.260**: Request for production response deadline
- **CCP 2033.250**: Request for admission response deadline
- **CRC 3.720**: Case Management rules
- **CRC 3.725**: Case Management Statement requirements

## Contributing

Contributions are welcome! Please ensure any changes:
1. Follow PEP 8 style guidelines
2. Include appropriate documentation
3. Add tests for new functionality
4. Update the README if adding features

## License

MIT License - See LICENSE file for details.

## Disclaimer

This software is provided for informational purposes only and does not constitute legal advice. Always verify deadline calculations with applicable California statutes, court rules, and local rules. Consult with a licensed California attorney for legal matters.
