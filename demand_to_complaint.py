#!/usr/bin/env python3
"""
California Complaint Generator
Converts a legal demand letter into a properly formatted California complaint.

Format specifications:
- Times New Roman, 13 point font
- Double-spaced
- 1-28 pleading paper with line numbers
- Standard sections: parties, jurisdiction/venue, allegations, causes of action, prayer
"""

import os
import sys
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import tkinter as tk
from tkinter import filedialog
import re


class CaliforniaComplaintGenerator:
    """Generator for California-formatted legal complaints."""

    def __init__(self):
        self.demand_letter_path = None
        self.exemplar_complaint_path = None
        self.output_path = None

    def prompt_file_upload(self):
        """Prompt user to upload demand letter and exemplar complaint."""
        root = tk.Tk()
        root.withdraw()  # Hide the main window

        print("\n" + "="*60)
        print("California Complaint Generator")
        print("="*60)

        print("\nPlease select the DEMAND LETTER file:")
        self.demand_letter_path = filedialog.askopenfilename(
            title="Select Demand Letter",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")]
        )

        if not self.demand_letter_path:
            print("Error: No demand letter selected.")
            return False

        print(f"✓ Demand letter selected: {os.path.basename(self.demand_letter_path)}")

        print("\nPlease select the EXEMPLAR COMPLAINT file:")
        self.exemplar_complaint_path = filedialog.askopenfilename(
            title="Select Exemplar Complaint",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")]
        )

        if not self.exemplar_complaint_path:
            print("Error: No exemplar complaint selected.")
            return False

        print(f"✓ Exemplar complaint selected: {os.path.basename(self.exemplar_complaint_path)}")

        print("\nPlease select where to SAVE the output complaint:")
        self.output_path = filedialog.asksaveasfilename(
            title="Save Complaint As",
            defaultextension=".docx",
            filetypes=[("Word Documents", "*.docx")]
        )

        if not self.output_path:
            print("Error: No output path selected.")
            return False

        print(f"✓ Output will be saved to: {os.path.basename(self.output_path)}")

        return True

    def read_demand_letter(self):
        """Read and extract content from demand letter."""
        try:
            doc = Document(self.demand_letter_path)
            content = {
                'full_text': [],
                'parties': [],
                'facts': [],
                'damages': []
            }

            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    content['full_text'].append(text)

            return content
        except Exception as e:
            print(f"Error reading demand letter: {e}")
            return None

    def read_exemplar_complaint(self):
        """Read and analyze exemplar complaint structure."""
        try:
            doc = Document(self.exemplar_complaint_path)
            structure = {
                'sections': [],
                'formatting': {},
                'paragraphs': []
            }

            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    structure['paragraphs'].append({
                        'text': text,
                        'style': para.style.name
                    })

            return structure
        except Exception as e:
            print(f"Error reading exemplar complaint: {e}")
            return None

    def create_pleading_paper_document(self):
        """Create a new document with California pleading paper formatting."""
        doc = Document()

        # Set up page margins for pleading paper
        # Left margin needs space for line numbers (approximately 1.5 inches)
        sections = doc.sections
        for section in sections:
            section.left_margin = Inches(1.5)
            section.right_margin = Inches(1.0)
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.page_height = Inches(11)
            section.page_width = Inches(8.5)

        return doc

    def set_paragraph_format(self, paragraph, bold=False, align='left'):
        """Apply California complaint formatting to a paragraph."""
        # Set font
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        font = run.font
        font.name = 'Times New Roman'
        font.size = Pt(13)
        font.bold = bold

        # Set RTF font for proper rendering
        r = run._element
        rPr = r.get_or_add_rPr()
        rFonts = OxmlElement('w:rFonts')
        rFonts.set(qn('w:ascii'), 'Times New Roman')
        rFonts.set(qn('w:hAnsi'), 'Times New Roman')
        rPr.append(rFonts)

        # Set paragraph spacing
        paragraph_format = paragraph.paragraph_format
        paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
        paragraph_format.space_before = Pt(0)
        paragraph_format.space_after = Pt(0)

        # Set alignment
        if align == 'center':
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == 'right':
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

        return paragraph

    def add_line_numbers(self, doc):
        """Add line numbers 1-28 to the document (California pleading paper)."""
        # Note: Line numbers in Word are typically added through section properties
        # This is a simplified version - full implementation would require
        # more complex OOXML manipulation
        section = doc.sections[0]
        sectPr = section._sectPr

        # Create line numbering element
        lnNumType = OxmlElement('w:lnNumType')
        lnNumType.set(qn('w:countBy'), '1')
        lnNumType.set(qn('w:restart'), 'continuous')
        lnNumType.set(qn('w:distance'), '360')  # Distance from text

        sectPr.append(lnNumType)

    def generate_complaint_header(self, doc, case_info):
        """Generate the complaint header with party information."""
        # Attorney information (top left)
        p = doc.add_paragraph()
        p.add_run(case_info.get('attorney_name', '[ATTORNEY NAME]')).bold = True
        self.set_paragraph_format(p)

        p = doc.add_paragraph(case_info.get('attorney_bar', '[State Bar No. XXXXXX]'))
        self.set_paragraph_format(p)

        p = doc.add_paragraph(case_info.get('law_firm', '[LAW FIRM NAME]'))
        self.set_paragraph_format(p)

        p = doc.add_paragraph(case_info.get('address', '[ADDRESS]'))
        self.set_paragraph_format(p)

        p = doc.add_paragraph(case_info.get('city_state_zip', '[CITY, STATE ZIP]'))
        self.set_paragraph_format(p)

        p = doc.add_paragraph(case_info.get('phone', 'Telephone: [XXX-XXX-XXXX]'))
        self.set_paragraph_format(p)

        p = doc.add_paragraph(case_info.get('email', 'Email: [email@example.com]'))
        self.set_paragraph_format(p)

        doc.add_paragraph()  # Blank line

        p = doc.add_paragraph('Attorney for Plaintiff')
        self.set_paragraph_format(p)

        doc.add_paragraph()  # Blank line
        doc.add_paragraph()  # Blank line

        # Court heading
        p = doc.add_paragraph('SUPERIOR COURT OF THE STATE OF CALIFORNIA')
        self.set_paragraph_format(p, align='center', bold=True)

        p = doc.add_paragraph(case_info.get('county', 'FOR THE COUNTY OF [COUNTY]'))
        self.set_paragraph_format(p, align='center', bold=True)

        doc.add_paragraph()  # Blank line

        return doc

    def generate_caption(self, doc, case_info):
        """Generate the case caption."""
        # This would typically be in a table format
        # Simplified version here

        p = doc.add_paragraph()
        run = p.add_run(case_info.get('plaintiff', '[PLAINTIFF NAME]'))
        run.font.name = 'Times New Roman'
        run.font.size = Pt(13)
        self.set_paragraph_format(p)

        p = doc.add_paragraph()
        p.add_run(' ' * 20).font.name = 'Times New Roman'
        p.add_run('Plaintiff,')
        self.set_paragraph_format(p)

        p = doc.add_paragraph()
        p.add_run(' ' * 10).font.name = 'Times New Roman'
        run = p.add_run('vs.')
        self.set_paragraph_format(p, align='center')

        p = doc.add_paragraph()
        doc.add_paragraph()

        p = doc.add_paragraph(case_info.get('defendant', '[DEFENDANT NAME]'))
        self.set_paragraph_format(p)

        p = doc.add_paragraph()
        p.add_run(' ' * 20).font.name = 'Times New Roman'
        p.add_run('Defendant.')
        self.set_paragraph_format(p)

        # Case number box (right side)
        # This is simplified - would typically be in a text box
        doc.add_paragraph()
        p = doc.add_paragraph(f"Case No.: {case_info.get('case_no', '[TO BE ASSIGNED]')}")
        self.set_paragraph_format(p)

        doc.add_paragraph()
        p = doc.add_paragraph('COMPLAINT FOR:')
        run = p.runs[0]
        run.bold = True
        self.set_paragraph_format(p)

        causes = case_info.get('causes_of_action', ['[CAUSE OF ACTION 1]', '[CAUSE OF ACTION 2]'])
        for i, cause in enumerate(causes, 1):
            p = doc.add_paragraph(f"{i}. {cause}")
            self.set_paragraph_format(p)

        doc.add_paragraph()

        return doc

    def add_section(self, doc, title, content_list):
        """Add a section to the complaint."""
        # Section heading
        p = doc.add_paragraph(title)
        run = p.runs[0]
        run.bold = True
        run.underline = True
        self.set_paragraph_format(p, bold=True, align='center')

        doc.add_paragraph()

        # Section content
        for i, content in enumerate(content_list, 1):
            p = doc.add_paragraph(f"{i}. {content}")
            self.set_paragraph_format(p)

        doc.add_paragraph()

        return doc

    def generate_complaint(self, demand_content, exemplar_structure):
        """Generate the formatted complaint document."""
        print("\nGenerating complaint document...")

        # Create document with pleading paper format
        doc = self.create_pleading_paper_document()

        # Case information (this would be extracted or prompted)
        case_info = {
            'attorney_name': '[ATTORNEY NAME]',
            'attorney_bar': '[State Bar No. XXXXXX]',
            'law_firm': '[LAW FIRM NAME]',
            'address': '[ADDRESS]',
            'city_state_zip': '[CITY, STATE ZIP]',
            'phone': 'Telephone: [XXX-XXX-XXXX]',
            'email': 'Email: [email@example.com]',
            'county': 'FOR THE COUNTY OF [COUNTY]',
            'plaintiff': '[PLAINTIFF NAME]',
            'defendant': '[DEFENDANT NAME]',
            'case_no': '[TO BE ASSIGNED]',
            'causes_of_action': [
                '[CAUSE OF ACTION 1]',
                '[CAUSE OF ACTION 2]'
            ]
        }

        # Generate header
        self.generate_complaint_header(doc, case_info)

        # Generate caption
        self.generate_caption(doc, case_info)

        # PARTIES section
        parties_content = [
            "Plaintiff [PLAINTIFF NAME] is an individual residing in [CITY], California.",
            "Defendant [DEFENDANT NAME] is [DESCRIPTION], doing business in [CITY], California.",
            "[Add additional party allegations as needed]"
        ]
        self.add_section(doc, "PARTIES", parties_content)

        # JURISDICTION AND VENUE section
        jurisdiction_content = [
            "This Court has jurisdiction over this action pursuant to California Constitution, article VI, section 10.",
            "Venue is proper in this Court pursuant to Code of Civil Procedure section 395 because [VENUE REASON].",
            "The amount in controversy exceeds the jurisdictional minimum of this Court."
        ]
        self.add_section(doc, "JURISDICTION AND VENUE", jurisdiction_content)

        # GENERAL ALLEGATIONS section
        general_allegations = [
            "[Insert general factual allegations from demand letter]",
            "[These should provide context and background]",
            "[Continue with additional general facts]"
        ]

        # Extract facts from demand letter if available
        if demand_content and demand_content.get('full_text'):
            general_allegations = [
                "Plaintiff incorporates by reference all allegations contained herein.",
                f"Based on the demand letter, the following facts are alleged: {' '.join(demand_content['full_text'][:3])}",
                "[Continue with specific factual allegations based on the demand letter content]"
            ]

        self.add_section(doc, "GENERAL FACTUAL ALLEGATIONS", general_allegations)

        # FIRST CAUSE OF ACTION
        p = doc.add_paragraph("FIRST CAUSE OF ACTION")
        run = p.runs[0]
        run.bold = True
        run.underline = True
        self.set_paragraph_format(p, bold=True, align='center')

        p = doc.add_paragraph("[Name of Cause of Action]")
        self.set_paragraph_format(p, align='center')

        doc.add_paragraph()

        first_cause_content = [
            "Plaintiff realleges and incorporates by reference paragraphs 1 through [X] as though fully set forth herein.",
            "[State elements of first cause of action]",
            "[Continue with specific allegations]",
            "As a direct and proximate result of Defendant's conduct, Plaintiff has suffered damages in an amount to be proven at trial."
        ]

        for i, content in enumerate(first_cause_content, 1):
            p = doc.add_paragraph(f"{i}. {content}")
            self.set_paragraph_format(p)

        doc.add_paragraph()

        # PRAYER FOR RELIEF
        p = doc.add_paragraph("PRAYER FOR RELIEF")
        run = p.runs[0]
        run.bold = True
        run.underline = True
        self.set_paragraph_format(p, bold=True, align='center')

        doc.add_paragraph()

        p = doc.add_paragraph("WHEREFORE, Plaintiff prays for judgment against Defendant as follows:")
        self.set_paragraph_format(p)

        prayer_items = [
            "For general damages according to proof;",
            "For special damages according to proof;",
            "For costs of suit incurred herein;",
            "For attorney's fees as permitted by law;",
            "For prejudgment interest;",
            "For such other and further relief as the Court deems just and proper."
        ]

        for i, item in enumerate(prayer_items, 1):
            p = doc.add_paragraph(f"{i}. {item}")
            self.set_paragraph_format(p)

        doc.add_paragraph()
        doc.add_paragraph()

        # Signature block
        p = doc.add_paragraph("Dated: _________________")
        self.set_paragraph_format(p)

        doc.add_paragraph()
        doc.add_paragraph()

        p = doc.add_paragraph("Respectfully submitted,")
        self.set_paragraph_format(p)

        doc.add_paragraph()
        doc.add_paragraph()

        p = doc.add_paragraph("_" * 40)
        self.set_paragraph_format(p)

        p = doc.add_paragraph("[ATTORNEY NAME]")
        self.set_paragraph_format(p)

        p = doc.add_paragraph("Attorney for Plaintiff")
        self.set_paragraph_format(p)

        # Add line numbering
        self.add_line_numbers(doc)

        # Save document
        try:
            doc.save(self.output_path)
            print(f"\n✓ Complaint successfully generated!")
            print(f"✓ Saved to: {self.output_path}")
            return True
        except Exception as e:
            print(f"\nError saving document: {e}")
            return False

    def run(self):
        """Main execution method."""
        print("Starting California Complaint Generator...")

        # Step 1: Prompt for files
        if not self.prompt_file_upload():
            print("\nError: File selection incomplete.")
            return False

        # Step 2: Read demand letter
        print("\nReading demand letter...")
        demand_content = self.read_demand_letter()
        if not demand_content:
            print("Warning: Could not read demand letter content.")

        # Step 3: Read exemplar complaint
        print("Reading exemplar complaint...")
        exemplar_structure = self.read_exemplar_complaint()
        if not exemplar_structure:
            print("Warning: Could not read exemplar complaint structure.")

        # Step 4: Generate complaint
        success = self.generate_complaint(demand_content, exemplar_structure)

        if success:
            print("\n" + "="*60)
            print("IMPORTANT NOTES:")
            print("="*60)
            print("1. This is a template - please review and customize all sections")
            print("2. Replace all bracketed placeholders with actual information")
            print("3. Verify all facts and allegations from the demand letter")
            print("4. Ensure causes of action match the facts alleged")
            print("5. Review formatting for compliance with local court rules")
            print("6. Line numbers will appear when printed or in Print Preview")
            print("="*60)

        return success


def main():
    """Main entry point."""
    try:
        generator = CaliforniaComplaintGenerator()
        generator.run()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
