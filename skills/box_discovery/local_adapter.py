"""
Local File Adapter

Allows the Box Discovery Skill to work with local files
for testing or when Box.com is not available.
"""

import os
from typing import Optional, List, Tuple
from dataclasses import dataclass

from .case_parser import CaseFileParser, CaseProfile
from .discovery_generator import DiscoveryGenerator, PartyRole


@dataclass
class LocalFile:
    """Represents a local file"""
    path: str
    name: str
    size: int

    @property
    def id(self) -> str:
        return self.path


class LocalFileAdapter:
    """
    Adapter for using the discovery skill with local files.

    Use this when:
    - Testing the skill without Box.com access
    - Working with files already downloaded
    - Integrating with other file sources
    """

    SUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}

    def __init__(self, client_role: str = "plaintiff"):
        """
        Initialize the local file adapter.

        Args:
            client_role: Client's role ("plaintiff" or "defendant")
        """
        self.client_role = client_role
        self.parser = CaseFileParser()
        self.case_profile: Optional[CaseProfile] = None
        self.generator: Optional[DiscoveryGenerator] = None

    def load_case_from_directory(self, directory: str) -> CaseProfile:
        """
        Load and parse all supported files from a directory.

        Args:
            directory: Path to directory containing case files

        Returns:
            Parsed CaseProfile
        """
        if not os.path.isdir(directory):
            raise ValueError(f"Directory not found: {directory}")

        documents = []

        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)

            if not os.path.isfile(filepath):
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                continue

            print(f"Processing: {filename}")
            try:
                content = self._read_file_content(filepath)
                documents.append((content, filename, filepath))
            except Exception as e:
                print(f"Warning: Could not read {filename}: {e}")

        if not documents:
            raise ValueError(f"No supported documents found in {directory}")

        # Parse all documents
        self.case_profile = self.parser.parse_case_file(documents)

        # Initialize generator
        role = PartyRole.PLAINTIFF if self.client_role.lower() == "plaintiff" else PartyRole.DEFENDANT
        self.generator = DiscoveryGenerator(self.case_profile, role)

        return self.case_profile

    def load_case_from_file(self, filepath: str) -> CaseProfile:
        """
        Load and parse a single file.

        Args:
            filepath: Path to the case file

        Returns:
            Parsed CaseProfile
        """
        if not os.path.isfile(filepath):
            raise ValueError(f"File not found: {filepath}")

        content = self._read_file_content(filepath)
        filename = os.path.basename(filepath)

        documents = [(content, filename, filepath)]
        self.case_profile = self.parser.parse_case_file(documents)

        role = PartyRole.PLAINTIFF if self.client_role.lower() == "plaintiff" else PartyRole.DEFENDANT
        self.generator = DiscoveryGenerator(self.case_profile, role)

        return self.case_profile

    def load_case_from_files(self, filepaths: List[str]) -> CaseProfile:
        """
        Load and parse multiple specific files.

        Args:
            filepaths: List of file paths

        Returns:
            Parsed CaseProfile
        """
        documents = []

        for filepath in filepaths:
            if not os.path.isfile(filepath):
                print(f"Warning: File not found: {filepath}")
                continue

            filename = os.path.basename(filepath)
            try:
                content = self._read_file_content(filepath)
                documents.append((content, filename, filepath))
            except Exception as e:
                print(f"Warning: Could not read {filename}: {e}")

        if not documents:
            raise ValueError("No files could be loaded")

        self.case_profile = self.parser.parse_case_file(documents)

        role = PartyRole.PLAINTIFF if self.client_role.lower() == "plaintiff" else PartyRole.DEFENDANT
        self.generator = DiscoveryGenerator(self.case_profile, role)

        return self.case_profile

    def load_case_from_text(self, text: str, filename: str = "case_document.txt") -> CaseProfile:
        """
        Load and parse case from raw text content.

        Args:
            text: Text content of the case file
            filename: Filename to use for the document

        Returns:
            Parsed CaseProfile
        """
        documents = [(text, filename, "text_input")]
        self.case_profile = self.parser.parse_case_file(documents)

        role = PartyRole.PLAINTIFF if self.client_role.lower() == "plaintiff" else PartyRole.DEFENDANT
        self.generator = DiscoveryGenerator(self.case_profile, role)

        return self.case_profile

    def _read_file_content(self, filepath: str) -> str:
        """Read text content from a file"""
        ext = os.path.splitext(filepath)[1].lower()

        # For now, just handle text files directly
        # PDF and DOCX would require additional libraries
        if ext in ['.txt', '.rtf']:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

        # Try to read as text anyway
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            with open(filepath, 'rb') as f:
                content = f.read()
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        return content.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                return content.decode('latin-1', errors='replace')

    @property
    def discovery_generator(self) -> Optional[DiscoveryGenerator]:
        """Get the discovery generator (after loading case)"""
        return self.generator


def create_local_skill(directory: Optional[str] = None, role: str = "plaintiff"):
    """
    Create a local discovery skill for testing.

    Args:
        directory: Optional directory with case files
        role: Client role

    Returns:
        Configured LocalFileAdapter
    """
    adapter = LocalFileAdapter(client_role=role)

    if directory:
        adapter.load_case_from_directory(directory)

    return adapter


# Demo/test function
def demo_with_sample_text():
    """
    Demo the skill with sample text (no files needed).
    """
    sample_complaint = """
    IN THE UNITED STATES DISTRICT COURT
    FOR THE NORTHERN DISTRICT OF CALIFORNIA

    Case No. 2024-CV-12345

    JOHN DOE,
        Plaintiff,

    v.

    ACME CORPORATION,
        Defendant.

    COMPLAINT FOR DAMAGES

    Plaintiff John Doe, by and through his attorneys, complains against Defendant
    ACME Corporation as follows:

    PARTIES

    1. Plaintiff John Doe is an individual residing in San Francisco, California.

    2. Defendant ACME Corporation is a Delaware corporation with its principal
    place of business in San Jose, California.

    FACTUAL ALLEGATIONS

    3. On or about January 15, 2024, Plaintiff entered into a contract with
    Defendant for the provision of software development services.

    4. The contract required Defendant to deliver a functioning software
    application by March 1, 2024.

    5. Defendant failed to deliver the software by the agreed upon date.

    6. As a result of Defendant's breach, Plaintiff has suffered damages in
    excess of $500,000.

    FIRST CAUSE OF ACTION
    (Breach of Contract)

    7. Plaintiff incorporates by reference all preceding paragraphs.

    8. Defendant breached the contract by failing to deliver the software
    as promised.

    9. Plaintiff has performed all obligations under the contract.

    10. As a direct result of Defendant's breach, Plaintiff has been damaged.

    WHEREFORE, Plaintiff prays for judgment against Defendant as follows:
    1. Compensatory damages in an amount to be proven at trial;
    2. Costs of suit;
    3. Such other relief as the Court deems just and proper.

    Dated: February 1, 2024

    Respectfully submitted,

    ___________________________
    Attorney for Plaintiff
    """

    print("=" * 60)
    print("DEMO: Box Discovery Skill with Sample Text")
    print("=" * 60)
    print()

    # Create adapter and load sample text
    adapter = LocalFileAdapter(client_role="plaintiff")
    adapter.load_case_from_text(sample_complaint, "complaint.txt")

    # Show case summary
    print("CASE PROFILE:")
    print("-" * 40)
    profile = adapter.case_profile
    print(f"Case Number: {profile.case_number}")
    print(f"Court: {profile.court}")
    print(f"Plaintiffs: {[p.name for p in profile.plaintiffs]}")
    print(f"Defendants: {[d.name for d in profile.defendants]}")
    print(f"Claims: {[c.claim_type for c in profile.legal_claims]}")
    print()

    # Generate interrogatories
    print("SAMPLE INTERROGATORIES:")
    print("-" * 40)
    gen = adapter.discovery_generator
    interrogatories = gen.generate_interrogatories(
        categories=["identity", "incident"],
        max_count=5
    )
    print(interrogatories.to_document())

    return adapter


if __name__ == "__main__":
    demo_with_sample_text()
