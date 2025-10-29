"""
Document text extraction for DOCX and PDF files.
"""

from typing import Optional
import logging
from pathlib import Path
import re

# DOCX extraction
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# PDF extraction
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    from pdfminer.layout import LAParams
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract text from legal documents (DOCX, PDF)."""

    def __init__(self):
        """Initialize text extractor."""
        self.supported_formats = []

        if DOCX_AVAILABLE:
            self.supported_formats.append('.docx')
        if PDF_AVAILABLE:
            self.supported_formats.append('.pdf')

        if not self.supported_formats:
            logger.warning("No document extraction libraries available")

    def extract(self, file_path: str) -> Optional[str]:
        """
        Extract text from a document.

        Args:
            file_path: Path to document file

        Returns:
            Extracted text, or None if extraction fails

        Raises:
            ValueError: If file format is not supported
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()

        if suffix not in self.supported_formats:
            raise ValueError(
                f"Unsupported format: {suffix}. "
                f"Supported: {', '.join(self.supported_formats)}"
            )

        try:
            if suffix == '.docx':
                return self.extract_docx(file_path)
            elif suffix == '.pdf':
                return self.extract_pdf(file_path)
            else:
                return None

        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            return None

    def extract_docx(self, file_path: str) -> Optional[str]:
        """
        Extract text from DOCX file.

        Args:
            file_path: Path to DOCX file

        Returns:
            Extracted text
        """
        if not DOCX_AVAILABLE:
            raise RuntimeError("python-docx not installed")

        try:
            doc = Document(file_path)

            # Extract paragraphs
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)

            # Extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        paragraphs.append(row_text)

            # Join with double newlines to preserve paragraph structure
            full_text = '\n\n'.join(paragraphs)

            # Clean up the text
            full_text = self._clean_text(full_text)

            return full_text

        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            return None

    def extract_pdf(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text
        """
        if not PDF_AVAILABLE:
            raise RuntimeError("pdfminer.six not installed")

        try:
            # Configure layout analysis parameters
            laparams = LAParams(
                line_margin=0.5,
                word_margin=0.1,
                char_margin=2.0,
                all_texts=True
            )

            # Extract text
            text = pdf_extract_text(
                file_path,
                laparams=laparams,
                maxpages=0  # Process all pages
            )

            # Clean up the text
            if text:
                text = self._clean_text(text)

            return text

        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove excessive whitespace while preserving structure
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace more than 2 newlines with 2
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove spaces at the beginning/end of lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # Remove common PDF artifacts
        # Page numbers at start of line
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

        # Headers/footers (heuristic: single line with less than 60 chars)
        lines = text.split('\n')
        cleaned_lines = []
        for i, line in enumerate(lines):
            # Skip likely headers/footers
            if len(line) < 60 and (i == 0 or i == len(lines) - 1):
                # Check if it looks like a header/footer
                if re.match(r'^(Page \d+|Case \d+|[\d\-]+)$', line.strip()):
                    continue
            cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # Normalize unicode quotation marks
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u2013', '-').replace('\u2014', '--')

        # Trim
        text = text.strip()

        return text

    def extract_metadata(self, file_path: str) -> dict:
        """
        Extract document metadata.

        Args:
            file_path: Path to document

        Returns:
            Dictionary of metadata
        """
        path = Path(file_path)

        metadata = {
            'filename': path.name,
            'size_bytes': path.stat().st_size if path.exists() else 0,
            'format': path.suffix.lower(),
            'modified': path.stat().st_mtime if path.exists() else 0
        }

        suffix = path.suffix.lower()

        if suffix == '.docx' and DOCX_AVAILABLE:
            try:
                doc = Document(file_path)
                core_props = doc.core_properties

                metadata.update({
                    'title': core_props.title or '',
                    'author': core_props.author or '',
                    'subject': core_props.subject or '',
                    'created': str(core_props.created) if core_props.created else '',
                    'modified': str(core_props.modified) if core_props.modified else '',
                    'last_modified_by': core_props.last_modified_by or ''
                })

            except Exception as e:
                logger.warning(f"Could not extract DOCX metadata: {e}")

        return metadata

    def validate_document(self, file_path: str) -> tuple[bool, str]:
        """
        Validate that a document can be processed.

        Args:
            file_path: Path to document

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(file_path)

        if not path.exists():
            return False, "File does not exist"

        if not path.is_file():
            return False, "Path is not a file"

        suffix = path.suffix.lower()
        if suffix not in self.supported_formats:
            return False, f"Unsupported format: {suffix}"

        # Check file size (warn if > 50MB)
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 50:
            return True, f"Warning: Large file ({size_mb:.1f}MB) may take time to process"

        # Try to extract text
        try:
            text = self.extract(file_path)
            if not text:
                return False, "No text could be extracted"

            if len(text) < 100:
                return True, "Warning: Very little text extracted"

            return True, "OK"

        except Exception as e:
            return False, f"Extraction test failed: {e}"

    def get_page_count_estimate(self, text: str) -> int:
        """
        Estimate page count from text.

        Args:
            text: Extracted text

        Returns:
            Estimated number of pages
        """
        # Average ~500 words per page for legal documents
        word_count = len(text.split())
        return max(1, word_count // 500)

    def get_statistics(self, text: str) -> dict:
        """
        Get text statistics.

        Args:
            text: Extracted text

        Returns:
            Dictionary of statistics
        """
        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        return {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': text.count('\n\n') + 1,
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'estimated_pages': self.get_page_count_estimate(text)
        }
