# utils/security.py - Security & Authentication Utilities
"""Security helpers for PayrollPro AI."""
import hashlib
import os
from config import PASSWORD_SALT


def hash_password(password: str) -> str:
    """SHA-256 hash with application salt."""
    salted = PASSWORD_SALT + password
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Compare plain password against stored hash."""
    return hash_password(plain) == hashed


def generate_employee_id(prefix: str = "EMP", sequence: int = 1) -> str:
    """Generate employee ID like EMP-00042."""
    return f"{prefix}-{sequence:05d}"


def sanitize_input(text: str) -> str:
    """Strip potentially dangerous characters from user input."""
    if not text:
        return ""
    dangerous = ["<", ">", '"', "'", ";", "--", "/*", "*/", "\\"]
    for ch in dangerous:
        text = text.replace(ch, "")
    return text.strip()
