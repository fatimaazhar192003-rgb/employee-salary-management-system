"""
analytics_agent.py - Analytics & Insights Agent for PayrollPro AI
Generates management insights and anomaly detection without requiring an LLM.
"""
from datetime import date, timedelta


class AnalyticsAgent:
    """Rule-based analytics agent that generates management insights."""

    def generate_management_insights(self) -> dict:
        """
        Return structured insights. Called without db context — uses
        self._db if set, otherwise returns template insights.
        """
        return {
            "💡 Key Recommendations": [
                "Review salary structures for employees hired over 12 months ago.",
                "Ensure all active employees have attendance marked for today.",
                "Process payroll before the last working day of the month.",
                "Review pending leave requests to avoid approval backlogs.",
            ],
            "📈 Growth Indicators": [
                "Track month-over-month payroll growth to manage budget.",
                "Monitor department headcount changes quarterly.",
                "Compare average salaries across departments for equity.",
            ],
            "⚠️ Risk Alerts": [
                "Employees without salary structures cannot be included in payroll.",
                "High absenteeism in a department may signal engagement issues.",
                "Unprocessed payroll for the current month requires immediate action.",
            ],
            "🎯 Best Practices": [
                "Run payroll on a fixed date each month for consistency.",
                "Keep employee records updated after any changes.",
                "Download monthly backups from Settings → Database.",
            ],
        }

    def detect_anomalies(self, db=None) -> list:
        """
        Detect payroll/attendance anomalies.
        Returns a list of anomaly strings (empty = all clear).
        """
        anomalies = []
        if db is None:
            return anomalies

        try:
            today = date.today()

            # 1. Employees without salary structure
            employees = db.get_all_employees() or []
            for emp in employees:
                ss = db.get_salary_structure(emp["id"])
                if not ss:
                    anomalies.append(
                        f"Employee **{emp['full_name']}** ({emp['employee_id']}) has no salary structure."
                    )

            # 2. Unusually high salary (> 3× average)
            if employees:
                avg = sum(e.get("basic_salary", 0) for e in employees) / len(employees)
                for emp in employees:
                    if emp.get("basic_salary", 0) > avg * 3:
                        anomalies.append(
                            f"**{emp['full_name']}** salary (${emp['basic_salary']:,.0f}) is "
                            f"3× above average (${avg:,.0f})."
                        )

            # 3. No payroll this month
            records = db.get_payroll_by_month(month=today.month, year=today.year) or []
            if employees and not records:
                anomalies.append(
                    f"Payroll has not been processed for {today.strftime('%B %Y')}."
                )

            # 4. High pending leaves
            pending = db.get_leaves_by_status("pending") or []
            if len(pending) > 5:
                anomalies.append(f"{len(pending)} leave requests are pending approval.")

        except Exception as e:
            anomalies.append(f"Anomaly detection error: {e}")

        return anomalies

    def get_payroll_growth(self, db, months: int = 6) -> list:
        """Return month-over-month payroll growth data."""
        today = date.today()
        results = []
        for i in range(months - 1, -1, -1):
            target = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
            records = db.get_payroll_by_month(month=target.month, year=target.year) or []
            total = sum(r.get("net_salary", 0) for r in records)
            results.append({
                "month_label": target.strftime("%b %Y"),
                "total_net": total,
                "headcount": len(records),
            })
        return results
