"""
payroll_agent.py - Payroll Processing Agent for PayrollPro AI
Handles automated payroll computation and batch processing.
"""
from datetime import date
from utils.calculations import calculate_full_salary


class PayrollAgent:
    """Automates payroll computation for all employees."""

    def process_all(self, db, month: int, year: int,
                    working_days: int = 26, processed_by: str = "agent") -> dict:
        """
        Process payroll for all active employees for the given month/year.
        Returns a summary dict.
        """
        employees = db.get_all_employees() or []
        results = {"processed": 0, "skipped": 0, "errors": [], "total_net": 0.0}

        for emp in employees:
            emp_id = emp["id"]
            ss = db.get_salary_structure(emp_id)
            if not ss:
                results["skipped"] += 1
                continue

            try:
                att = db.get_attendance_history(employee_id=emp_id, month=month, year=year) or []
                present_days = sum(1 for a in att if a["status"] in ("present", "late", "half_day")) or working_days

                calc = calculate_full_salary(
                    basic=ss["basic_salary"],
                    hra_pct=ss["hra_percent"],
                    medical_pct=ss["medical_percent"],
                    transport_pct=ss["transport_percent"],
                    pf_pct=ss["pf_percent"],
                    tax_pct=ss["tax_percent"],
                    other_ded_pct=ss.get("other_deduction_percent", 0),
                    bonus=ss.get("bonus", 0),
                )

                db.save_payroll(
                    employee_id=emp_id,
                    month=month,
                    year=year,
                    basic_salary=calc["basic_salary"],
                    hra=calc["hra"],
                    medical=calc["medical"],
                    transport=calc["transport"],
                    bonus=calc["bonus"],
                    overtime=calc["overtime"],
                    gross_salary=calc["gross_salary"],
                    pf=calc["pf"],
                    tax=calc["tax"],
                    other_deductions=calc["other_deductions"],
                    total_deductions=calc["total_deductions"],
                    net_salary=calc["net_salary"],
                    working_days=working_days,
                    present_days=present_days,
                    processed_by=processed_by,
                )
                results["processed"] += 1
                results["total_net"] += calc["net_salary"]

            except Exception as e:
                results["errors"].append(f"{emp.get('full_name', emp_id)}: {e}")

        return results

    def get_payroll_summary(self, db, month: int, year: int) -> dict:
        """Return high-level payroll summary for a given month."""
        records = db.get_payroll_by_month(month=month, year=year) or []
        return {
            "month": date(year, month, 1).strftime("%B %Y"),
            "employee_count": len(records),
            "total_gross": sum(r.get("gross_salary", 0) for r in records),
            "total_deductions": sum(r.get("total_deductions", 0) for r in records),
            "total_net": sum(r.get("net_salary", 0) for r in records),
        }
