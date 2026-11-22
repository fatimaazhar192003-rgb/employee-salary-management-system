# utils/validators.py - Input Validation Utilities
"""
Validation helpers for the PayrollPro AI Salary Management System.
All validators raise :class:`ValueError` on failure unless noted otherwise.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


def validate_email(email: str) -> str:
    """
    Validate an e-mail address.

    Args:
        email: Candidate e-mail string.

    Returns:
        Lower-cased, stripped e-mail if valid.

    Raises:
        ValueError: If *email* is empty or malformed.
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email address is required.")
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError(f"'{email}' is not a valid e-mail address.")
    return email


# ---------------------------------------------------------------------------
# Phone
# ---------------------------------------------------------------------------

_PHONE_RE = re.compile(r"^\+?[\d\s\-().]{7,20}$")


def validate_phone(phone: str) -> str:
    """
    Validate a phone number (international or local).

    Accepts digits, spaces, hyphens, parentheses, dots, and an optional
    leading ``+``.  Must be between 7 and 20 characters of actual digits.

    Args:
        phone: Candidate phone string.

    Returns:
        Stripped phone string if valid.

    Raises:
        ValueError: If *phone* is empty or malformed.
    """
    if not phone or not isinstance(phone, str):
        raise ValueError("Phone number is required.")
    phone = phone.strip()
    if not _PHONE_RE.match(phone):
        raise ValueError(f"'{phone}' is not a valid phone number.")
    digits_only = re.sub(r"\D", "", phone)
    if len(digits_only) < 7:
        raise ValueError("Phone number must contain at least 7 digits.")
    return phone


# ---------------------------------------------------------------------------
# Salary
# ---------------------------------------------------------------------------

def validate_salary(amount) -> Decimal:
    """
    Validate that *amount* represents a positive monetary value.

    Args:
        amount: Numeric value or string representation.

    Returns:
        :class:`~decimal.Decimal` representation of *amount*.

    Raises:
        ValueError: If *amount* is not a positive number.
    """
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        raise ValueError(f"'{amount}' is not a valid numeric salary amount.")
    if value <= 0:
        raise ValueError("Salary amount must be greater than zero.")
    return value


# ---------------------------------------------------------------------------
# Date
# ---------------------------------------------------------------------------

def validate_date(date_str: str) -> str:
    """
    Validate a date string in ``YYYY-MM-DD`` format.

    Args:
        date_str: Date string to validate.

    Returns:
        The original string if it is a valid ``YYYY-MM-DD`` date.

    Raises:
        ValueError: If *date_str* is empty or not a valid date.
    """
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date is required.")
    date_str = date_str.strip()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"'{date_str}' is not a valid date. Expected format: YYYY-MM-DD."
        )
    return date_str


# ---------------------------------------------------------------------------
# Required field
# ---------------------------------------------------------------------------

def validate_required(value, field_name: str = "Field"):
    """
    Ensure *value* is not empty / None.

    Args:
        value:      The value to check.
        field_name: Human-readable name used in the error message.

    Returns:
        *value* unchanged if it is not empty.

    Raises:
        ValueError: If *value* is ``None``, an empty string, or whitespace.
    """
    if value is None:
        raise ValueError(f"{field_name} is required.")
    if isinstance(value, str) and not value.strip():
        raise ValueError(f"{field_name} is required and cannot be blank.")
    return value
