"""Validation utilities for California court case tracking."""

import re
from typing import Optional, Tuple


def validate_case_number(case_number: str, county: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate a California court case number.

    California case numbers vary by county but generally follow patterns like:
    - Los Angeles: 24STCV01234, BC123456
    - San Francisco: CGC-24-612345
    - San Diego: 37-2024-00012345-CU-BC-CTL

    Returns:
        Tuple of (is_valid, message)
    """
    if not case_number:
        return False, "Case number is required"

    case_number = case_number.strip().upper()

    # General validation - must have letters and numbers
    if not re.search(r'[A-Z]', case_number):
        return False, "Case number must contain letters"

    if not re.search(r'\d', case_number):
        return False, "Case number must contain numbers"

    # Check minimum length
    if len(case_number) < 6:
        return False, "Case number appears too short"

    # Check maximum length
    if len(case_number) > 30:
        return False, "Case number appears too long"

    # County-specific validation
    if county:
        county_lower = county.lower()

        # Los Angeles Superior Court patterns
        if county_lower in ['los angeles', 'la']:
            # Pattern: YY + Court Code + Case Type + Number (e.g., 24STCV01234)
            if re.match(r'^\d{2}[A-Z]{2,4}[A-Z]{2}\d{5,6}$', case_number):
                return True, "Valid Los Angeles case number"
            # Legacy pattern: BC/BD/etc + numbers
            if re.match(r'^[A-Z]{2}\d{6}$', case_number):
                return True, "Valid Los Angeles legacy case number"

        # San Francisco Superior Court patterns
        elif county_lower in ['san francisco', 'sf']:
            # Pattern: CGC-YY-NNNNNN
            if re.match(r'^[A-Z]{2,3}-\d{2}-\d{6}$', case_number):
                return True, "Valid San Francisco case number"

        # San Diego Superior Court patterns
        elif county_lower in ['san diego', 'sd']:
            # Pattern: 37-YYYY-NNNNNNNNN-XX-XX-XXX
            if re.match(r'^\d{2}-\d{4}-\d{8,9}-[A-Z]{2}-[A-Z]{2}-[A-Z]{3}$', case_number):
                return True, "Valid San Diego case number"

    # General California case number patterns
    # Most are alphanumeric with optional hyphens
    if re.match(r'^[A-Z0-9\-]{6,25}$', case_number):
        return True, "Valid case number format"

    return False, "Case number format not recognized"


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate an email address.

    Returns:
        Tuple of (is_valid, message)
    """
    if not email:
        return False, "Email address is required"

    email = email.strip().lower()

    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(pattern, email):
        return True, "Valid email address"

    return False, "Invalid email address format"


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate a US phone number.

    Accepts various formats:
    - (555) 123-4567
    - 555-123-4567
    - 5551234567
    - +1 555 123 4567

    Returns:
        Tuple of (is_valid, message)
    """
    if not phone:
        return False, "Phone number is required"

    # Remove common formatting characters
    digits = re.sub(r'[\s\-\.\(\)\+]', '', phone)

    # Check if we have the right number of digits
    if len(digits) == 10:
        return True, "Valid US phone number"
    elif len(digits) == 11 and digits.startswith('1'):
        return True, "Valid US phone number with country code"

    return False, "Invalid phone number format"


def format_phone(phone: str) -> str:
    """Format a phone number as (XXX) XXX-XXXX."""
    digits = re.sub(r'[\s\-\.\(\)\+]', '', phone)

    # Remove leading 1 if present
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]

    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    return phone  # Return original if can't format


def validate_bar_number(bar_number: str) -> Tuple[bool, str]:
    """
    Validate a California State Bar number.

    California bar numbers are typically 6 digits.

    Returns:
        Tuple of (is_valid, message)
    """
    if not bar_number:
        return False, "Bar number is required"

    bar_number = bar_number.strip()

    # Remove any non-digit characters
    digits = re.sub(r'\D', '', bar_number)

    # California bar numbers are 6 digits (or up to 7 for newer members)
    if 5 <= len(digits) <= 7:
        return True, "Valid California bar number format"

    return False, "California bar numbers are typically 6 digits"


def validate_zip_code(zip_code: str) -> Tuple[bool, str]:
    """
    Validate a US ZIP code.

    Accepts:
    - 5-digit ZIP: 90210
    - ZIP+4: 90210-1234

    Returns:
        Tuple of (is_valid, message)
    """
    if not zip_code:
        return False, "ZIP code is required"

    zip_code = zip_code.strip()

    # 5-digit ZIP
    if re.match(r'^\d{5}$', zip_code):
        return True, "Valid 5-digit ZIP code"

    # ZIP+4
    if re.match(r'^\d{5}-\d{4}$', zip_code):
        return True, "Valid ZIP+4 code"

    return False, "Invalid ZIP code format"


def validate_california_zip(zip_code: str) -> Tuple[bool, str]:
    """
    Validate that a ZIP code is in California.

    California ZIP codes range from 90001-96162.

    Returns:
        Tuple of (is_valid, message)
    """
    is_valid, msg = validate_zip_code(zip_code)
    if not is_valid:
        return False, msg

    # Extract 5-digit ZIP
    digits = zip_code[:5]
    zip_num = int(digits)

    # California ZIP code ranges
    ca_ranges = [
        (90001, 96162),
    ]

    for start, end in ca_ranges:
        if start <= zip_num <= end:
            return True, "Valid California ZIP code"

    return False, "ZIP code is not in California"


def sanitize_input(text: str, max_length: int = 1000,
                   allow_newlines: bool = False) -> str:
    """
    Sanitize user input text.

    - Strips leading/trailing whitespace
    - Removes control characters
    - Limits length
    - Optionally removes newlines
    """
    if not text:
        return ""

    # Remove control characters except newlines/tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    if not allow_newlines:
        text = text.replace('\n', ' ').replace('\r', '')

    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text)

    # Strip and limit length
    text = text.strip()[:max_length]

    return text


def is_valid_name(name: str, min_length: int = 2, max_length: int = 100) -> Tuple[bool, str]:
    """
    Validate a person or entity name.

    Returns:
        Tuple of (is_valid, message)
    """
    if not name:
        return False, "Name is required"

    name = name.strip()

    if len(name) < min_length:
        return False, f"Name must be at least {min_length} characters"

    if len(name) > max_length:
        return False, f"Name must not exceed {max_length} characters"

    # Check for obviously invalid patterns
    if re.match(r'^[\d\W]+$', name):
        return False, "Name must contain letters"

    return True, "Valid name"
