# config.py - Application Configuration for PayrollPro AI
import os

APP_NAME = "PayrollPro AI"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Agentic AI-Powered Salary Management System"
APP_AUTHOR = "PayrollPro Team"

# Database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "salary_management.db")

# Security
SECRET_KEY = "payrollpro_secret_key_2024_secure_v2"
PASSWORD_SALT = "payrollpro_salt_v2_secure"
SESSION_TIMEOUT = 3600  # seconds

# Company defaults
DEFAULT_COMPANY = {
    "name": "PayrollPro Corp",
    "address": "123 Business Avenue, Tech City, TC 10001",
    "phone": "+1-555-0100",
    "email": "hr@payrollpro.com",
    "website": "www.payrollpro.com",
    "currency": "USD",
    "currency_symbol": "$",
    "tax_year": "2024",
    "fiscal_month_start": 1,
}

# Default salary component percentages (of basic salary)
DEFAULT_SALARY_COMPONENTS = {
    "hra_percent": 40.0,            # House Rent Allowance
    "medical_percent": 10.0,        # Medical Allowance
    "transport_percent": 5.0,       # Transport Allowance
    "pf_percent": 12.0,             # Provident Fund deduction
    "tax_percent": 10.0,            # Income Tax deduction
    "other_deduction_percent": 0.0, # Other deductions
}

# Pagination
RECORDS_PER_PAGE = 15

# AI Configuration
AI_MODE = "deterministic"  # "deterministic" or "llm"
LLM_API_KEY = ""           # Optional: OpenAI/Groq API key
LLM_MODEL = "gpt-3.5-turbo"
AI_LOG_ENABLED = True

# Leave types
LEAVE_TYPES = ["Annual Leave", "Sick Leave", "Casual Leave", "Maternity Leave", 
               "Paternity Leave", "Emergency Leave", "Unpaid Leave"]

# Employment statuses
EMPLOYMENT_STATUSES = ["Active", "Inactive", "On Leave", "Terminated", "Probation"]

# Attendance statuses
ATTENDANCE_STATUSES = ["Present", "Absent", "Half Day", "Late", "On Leave"]

# Payroll statuses
PAYROLL_STATUSES = ["Pending", "Paid", "On Hold"]

# Chart colors
CHART_COLORS = {
    "primary": "#6366f1",
    "secondary": "#8b5cf6",
    "accent": "#06b6d4",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "gradient": ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"],
}
