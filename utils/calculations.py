# utils/calculations.py - Salary Calculation Utilities
"""Pure functions for salary computation — no I/O, fully testable."""
from decimal import Decimal, ROUND_HALF_UP


def _d(value) -> Decimal:
    return Decimal(str(value))


def _round2(value) -> float:
    return float(_d(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_hra(basic: float, percent: float) -> float:
    """HRA = basic * percent / 100"""
    return _round2(_d(basic) * _d(percent) / _d(100))


def calculate_pf(basic: float, percent: float) -> float:
    """PF = basic * percent / 100"""
    return _round2(_d(basic) * _d(percent) / _d(100))


def calculate_tax(gross: float, percent: float) -> float:
    """Tax = gross * percent / 100"""
    return _round2(_d(gross) * _d(percent) / _d(100))


def calculate_gross_salary(basic: float, hra: float, medical: float,
                            transport: float, bonus: float, overtime: float) -> float:
    """Gross = Basic + HRA + Medical + Transport + Bonus + Overtime"""
    return _round2(_d(basic) + _d(hra) + _d(medical) + _d(transport) + _d(bonus) + _d(overtime))


def calculate_total_deductions(pf: float, tax: float, other_deductions: float) -> float:
    """Total deductions = PF + Tax + Other"""
    return _round2(_d(pf) + _d(tax) + _d(other_deductions))


def calculate_net_salary(gross: float, total_deductions: float) -> float:
    """Net = Gross - Total Deductions"""
    net = _d(gross) - _d(total_deductions)
    return _round2(max(net, Decimal("0")))


def calculate_attendance_percentage(present_days: int, total_working_days: int) -> float:
    """Return attendance percentage (0-100)."""
    if total_working_days <= 0:
        return 0.0
    return _round2(_d(present_days) / _d(total_working_days) * _d(100))


def calculate_salary_from_attendance(net_salary: float, present_days: int,
                                     total_working_days: int) -> float:
    """Pro-rate salary based on attendance."""
    if total_working_days <= 0:
        return 0.0
    return _round2(_d(net_salary) * _d(present_days) / _d(total_working_days))


def calculate_full_salary(basic: float, hra_pct: float, medical_pct: float,
                           transport_pct: float, pf_pct: float, tax_pct: float,
                           other_ded_pct: float = 0.0, bonus: float = 0.0,
                           overtime: float = 0.0) -> dict:
    """
    One-shot salary calculation returning all components as a dict.
    """
    hra = calculate_hra(basic, hra_pct)
    medical = _round2(_d(basic) * _d(medical_pct) / 100)
    transport = _round2(_d(basic) * _d(transport_pct) / 100)
    gross = calculate_gross_salary(basic, hra, medical, transport, bonus, overtime)
    pf = calculate_pf(basic, pf_pct)
    tax = calculate_tax(gross, tax_pct)
    other = _round2(_d(gross) * _d(other_ded_pct) / 100)
    total_ded = calculate_total_deductions(pf, tax, other)
    net = calculate_net_salary(gross, total_ded)
    return {
        "basic_salary": basic,
        "hra": hra,
        "medical": medical,
        "transport": transport,
        "bonus": bonus,
        "overtime": overtime,
        "gross_salary": gross,
        "pf": pf,
        "tax": tax,
        "other_deductions": other,
        "total_deductions": total_ded,
        "net_salary": net,
    }
