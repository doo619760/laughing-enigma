# California Complaint Generator

A Python program that converts legal demand letters into properly formatted California complaints in .docx format.

## Features

- Converts demand letters into California court-compliant complaints
- Proper California pleading paper format:
  - Times New Roman, 13 point font
  - Double-spaced text
  - Line numbering (1-28) on left margin
  - Proper margins for legal pleadings
- Standard complaint sections:
  - Parties
  - Jurisdiction and Venue
  - General Factual Allegations
  - Specific Factual Allegations
  - Causes of Action
  - Prayer for Relief
- Interactive file upload prompts
- Uses exemplar complaints as templates
- Outputs professional .docx format

## Requirements

- Python 3.6 or higher
- python-docx library
- tkinter (usually included with Python)

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install python-docx
```

## Usage

### Running the Program

```bash
python3 demand_to_complaint.py
```

### Step-by-Step Process

1. **Launch the program**
   - Run the command above
   - The program will open file selection dialogs

2. **Select Demand Letter**
   - When prompted, select the demand letter file (.docx format)
   - This file contains the facts and demands from the client

3. **Select Exemplar Complaint**
   - When prompted, select an exemplar complaint file (.docx format)
   - This provides structure and formatting reference
   - Can be a previous complaint or template

4. **Choose Output Location**
   - Select where to save the generated complaint
   - Choose a filename (will be saved as .docx)

5. **Review Output**
   - The program will generate a formatted complaint
   - Review all sections and placeholders
   - Customize as needed

### File Formats

**Input Files:**
- Demand Letter: .docx format
- Exemplar Complaint: .docx format

**Output:**
- Generated Complaint: .docx format
- California pleading paper formatting
- Ready for customization and filing

## Output Format

The generated complaint includes:

### 1. Header Section
- Attorney name and bar number
- Law firm information
- Contact details
- Court designation

### 2. Caption
- Plaintiff name(s)
- Defendant name(s)
- Case number
- List of causes of action

### 3. Parties Section
- Plaintiff identification and residency
- Defendant identification and business location
- Additional party information

### 4. Jurisdiction and Venue
- Court jurisdiction basis
- Venue propriety
- Amount in controversy

### 5. General Factual Allegations
- Background facts
- Context for claims
- Timeline of events

### 6. Causes of Action
- Separate sections for each cause
- Elements of each claim
- Specific factual support
- Damages allegations

### 7. Prayer for Relief
- General damages
- Special damages
- Costs and fees
- Other relief

### 8. Signature Block
- Date line
- Attorney signature space
- Attorney name and designation

## Formatting Specifications

### Font and Spacing
- **Font:** Times New Roman
- **Size:** 13 point
- **Line Spacing:** Double-spaced
- **Paragraph Spacing:** 0 pt before and after

### Margins
- **Left Margin:** 1.5 inches (to accommodate line numbers)
- **Right Margin:** 1.0 inch
- **Top Margin:** 1.0 inch
- **Bottom Margin:** 1.0 inch

### Page Setup
- **Paper Size:** 8.5 x 11 inches (Letter)
- **Line Numbers:** 1-28, continuous
- **Orientation:** Portrait

## Important Notes

### After Generation

1. **Review All Content**
   - This is a TEMPLATE document
   - All bracketed placeholders must be replaced
   - Example: [PLAINTIFF NAME] → John Doe

2. **Customize Information**
   - Attorney information
   - Party names and details
   - Case-specific facts
   - Causes of action
   - Damages amounts

3. **Verify Facts**
   - Cross-reference with demand letter
   - Ensure accuracy of all allegations
   - Verify dates and amounts
   - Check legal theories

4. **Local Court Rules**
   - Review local court formatting requirements
   - Some courts have specific rules
   - Verify caption format
   - Check pagination requirements

5. **Professional Review**
   - Have an attorney review before filing
   - Verify all legal citations
   - Ensure proper service copies
   - Check filing requirements

### Legal Disclaimer

This program generates a template document. It does NOT:
- Provide legal advice
- Ensure legal sufficiency
- Verify facts or claims
- Replace attorney review
- Guarantee court acceptance

**Always have a licensed attorney review legal documents before filing.**

## Troubleshooting

### Common Issues

**Problem:** File dialog doesn't appear
- **Solution:** Ensure tkinter is installed
- Try: `sudo apt-get install python3-tk` (Linux)

**Problem:** Error reading demand letter
- **Solution:** Ensure file is in .docx format (not .doc)
- Check file is not corrupted
- Verify file permissions

**Problem:** Formatting appears incorrect
- **Solution:** Open in Microsoft Word or compatible software
- Line numbers appear in Print Preview
- Some formatting may not display in web viewers

**Problem:** Missing line numbers
- **Solution:** Line numbers appear when:
  - Viewing in Print Layout mode
  - Using Print Preview
  - Printing the document

## Technical Details

### Dependencies

- **python-docx**: Document creation and manipulation
- **tkinter**: File dialog interface (usually pre-installed)

### Python Version

- Tested on Python 3.6+
- Should work on Python 2.7+ (not recommended)

### Platform Support

- **Windows:** Full support
- **macOS:** Full support
- **Linux:** Full support (may need tkinter installation)

## Examples

### Example 1: Personal Injury Case

Input: Demand letter for slip and fall accident
Output: Complaint with:
- Premises liability cause of action
- Negligence allegations
- Medical damages
- Pain and suffering

### Example 2: Contract Dispute

Input: Demand letter for breach of contract
Output: Complaint with:
- Breach of contract cause of action
- Contract terms allegations
- Performance allegations
- Damages calculations

### Example 3: Employment Matter

Input: Demand letter for wrongful termination
Output: Complaint with:
- Wrongful termination cause of action
- Employment relationship facts
- Termination circumstances
- Lost wages and benefits

## Advanced Usage

### Customizing the Template

To modify the default template, edit `demand_to_complaint.py`:

1. **Case Information (Lines ~250-265)**
   ```python
   case_info = {
       'attorney_name': '[ATTORNEY NAME]',
       'law_firm': '[LAW FIRM NAME]',
       # Modify default values here
   }
   ```

2. **Section Content**
   - Modify `parties_content`, `jurisdiction_content`, etc.
   - Add or remove sections as needed

3. **Formatting**
   - Adjust margins in `create_pleading_paper_document()`
   - Modify font/spacing in `set_paragraph_format()`

### Batch Processing

For multiple complaints:
```python
# Modify the script to loop through multiple files
# Or create a wrapper script
```

## Contributing

Contributions welcome:
- Bug fixes
- Feature enhancements
- Documentation improvements
- Format templates

## License

This software is provided as-is for legal document preparation purposes.

## Support

For issues or questions:
1. Check Troubleshooting section
2. Review documentation
3. Consult with IT support for installation issues
4. Consult with legal team for content issues

## Version History

- **v1.0** - Initial release
  - Basic complaint generation
  - California pleading paper format
  - File upload prompts
  - Standard sections

## Future Enhancements

Potential improvements:
- AI-powered fact extraction from demand letters
- Multiple jurisdiction support
- Cause of action templates library
- Auto-population from exemplar complaints
- Batch processing
- Web interface
- Cloud storage integration

## Credits

Developed for legal professionals to streamline complaint drafting while maintaining proper California court formatting standards.

---

**Remember:** This tool assists with document formatting. All legal content must be reviewed and approved by a licensed attorney before filing with any court.
