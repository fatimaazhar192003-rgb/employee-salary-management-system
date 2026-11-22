"""
orchestrator.py - Master Agent Orchestrator for PayrollPro AI
Routes queries to specialist agents and returns structured responses.
"""
from datetime import date


class AgentOrchestrator:
    """Routes natural language queries to the correct specialist agent."""

    def __init__(self):
        self._analytics = None
        self._payroll = None
        self._report = None

    def _get_analytics(self):
        if not self._analytics:
            from agents.analytics_agent import AnalyticsAgent
            self._analytics = AnalyticsAgent()
        return self._analytics

    def _get_payroll(self):
        if not self._payroll:
            from agents.payroll_agent import PayrollAgent
            self._payroll = PayrollAgent()
        return self._payroll

    def _get_report(self):
        if not self._report:
            from agents.report_agent import ReportAgent
            self._report = ReportAgent()
        return self._report

    def process_query(self, query: str, db, user_role: str = "admin", username: str = "user") -> dict:
        """
        Classify the query and dispatch to the appropriate handler.
        Returns a dict: {answer, agent_used, task_type, status}
        """
        q = query.lower().strip()

        # ── Classification ─────────────────────────────────────────
        if any(k in q for k in ["payroll", "salary", "process", "net pay", "gross", "deduction"]):
            return self._handle_payroll(q, db, query)
        elif any(k in q for k in ["attendance", "present", "absent", "leave", "absent"]):
            return self._handle_attendance(q, db, query)
        elif any(k in q for k in ["analytic", "trend", "chart", "insight", "anomaly"]):
            return self._handle_analytics(q, db, query)
        elif any(k in q for k in ["report", "export", "download", "pdf", "excel"]):
            return self._handle_report(q, db, query)
        elif any(k in q for k in ["employee", "staff", "headcount", "department", "who"]):
            return self._handle_employee(q, db, query)
        elif any(k in q for k in ["dashboard", "summary", "overview", "stats"]):
            return self._handle_dashboard(q, db, query)
        else:
            return self._handle_general(query, db)

    # ── Handlers ───────────────────────────────────────────────────

    def _handle_payroll(self, q: str, db, original: str) -> dict:
        try:
            today = date.today()
            records = db.get_payroll_by_month(month=today.month, year=today.year)
            if records:
                total = sum(r.get("net_salary", 0) for r in records)
                gross = sum(r.get("gross_salary", 0) for r in records)
                answer = (
                    f"**💳 Payroll Summary — {today.strftime('%B %Y')}**\n\n"
                    f"- Employees processed: **{len(records)}**\n"
                    f"- Total Gross Salary: **${gross:,.2f}**\n"
                    f"- Total Net Payroll: **${total:,.2f}**\n"
                    f"- Average Net Salary: **${total/len(records):,.2f}**\n\n"
                    "Go to **Payroll** in the sidebar to process or view detailed records."
                )
            else:
                answer = (
                    f"No payroll records found for **{today.strftime('%B %Y')}**. "
                    "Go to **Payroll → Process Payroll** to run this month's payroll."
                )
            return {"answer": answer, "agent_used": "PayrollAgent", "task_type": "payroll_query", "status": "success"}
        except Exception as e:
            return {"answer": f"⚠️ Payroll query failed: {e}", "agent_used": "PayrollAgent", "task_type": "payroll_query", "status": "error"}

    def _handle_attendance(self, q: str, db, original: str) -> dict:
        try:
            today = date.today()
            att = db.get_attendance_history(month=today.month, year=today.year)
            if att:
                from collections import Counter
                statuses = Counter(a["status"] for a in att)
                answer = (
                    f"**📅 Attendance Summary — {today.strftime('%B %Y')}**\n\n"
                    + "\n".join(f"- {k.replace('_',' ').title()}: **{v}**" for k, v in statuses.items())
                    + f"\n\n*Total records: {len(att)}*"
                )
            else:
                pending = db.get_leaves_by_status("pending")
                answer = (
                    f"No attendance records for {today.strftime('%B %Y')} yet.\n\n"
                    f"**Pending leave requests:** {len(pending)}"
                )
            return {"answer": answer, "agent_used": "OrchestratorAttendance", "task_type": "attendance_query", "status": "success"}
        except Exception as e:
            return {"answer": f"⚠️ Attendance query failed: {e}", "agent_used": "OrchestratorAttendance", "task_type": "attendance_query", "status": "error"}

    def _handle_analytics(self, q: str, db, original: str) -> dict:
        try:
            agent = self._get_analytics()
            insights = agent.generate_management_insights()
            if isinstance(insights, dict):
                lines = []
                for cat, items in insights.items():
                    lines.append(f"**{cat}**")
                    if isinstance(items, list):
                        lines.extend(f"  - {i}" for i in items)
                    else:
                        lines.append(f"  {items}")
                answer = "**📊 AI Management Insights**\n\n" + "\n".join(lines)
            else:
                answer = str(insights)
            return {"answer": answer, "agent_used": "AnalyticsAgent", "task_type": "analytics_query", "status": "success"}
        except Exception as e:
            return {"answer": f"⚠️ Analytics query failed: {e}", "agent_used": "AnalyticsAgent", "task_type": "analytics_query", "status": "error"}

    def _handle_report(self, q: str, db, original: str) -> dict:
        answer = (
            "**📄 Reports**\n\n"
            "I can generate the following reports:\n"
            "- 💰 **Payroll Report** — PDF + Excel\n"
            "- 📅 **Attendance Report** — Excel\n"
            "- 👤 **Employee List** — CSV\n"
            "- 🏢 **Department Summary** — Excel\n\n"
            "Go to the **Reports** page in the sidebar to download them."
        )
        return {"answer": answer, "agent_used": "ReportAgent", "task_type": "report_info", "status": "success"}

    def _handle_employee(self, q: str, db, original: str) -> dict:
        try:
            employees = db.get_all_employees()
            active = [e for e in employees if e.get("is_active")]
            depts = db.get_all_departments()

            answer = (
                f"**👥 Workforce Summary**\n\n"
                f"- Total Employees: **{len(employees)}**\n"
                f"- Active: **{len(active)}**\n"
                f"- Departments: **{len(depts)}**\n\n"
                "**Departments:**\n"
                + "\n".join(f"  - {d['name']}" for d in depts)
            )
            if "top" in q or "highest" in q or "earner" in q:
                top = db.get_top_earners(5)
                answer += "\n\n**🏆 Top 5 Earners:**\n" + "\n".join(
                    f"  {i+1}. {e['full_name']} — ${e['basic_salary']:,.0f}" for i, e in enumerate(top)
                )
            return {"answer": answer, "agent_used": "OrchestratorEmployee", "task_type": "employee_query", "status": "success"}
        except Exception as e:
            return {"answer": f"⚠️ Employee query failed: {e}", "agent_used": "OrchestratorEmployee", "task_type": "employee_query", "status": "error"}

    def _handle_dashboard(self, q: str, db, original: str) -> dict:
        try:
            stats = db.get_dashboard_stats()
            answer = (
                "**📊 Dashboard Summary**\n\n"
                f"- 👥 Total Employees: **{stats.get('total_employees', 0)}**\n"
                f"- ✅ Active: **{stats.get('active_employees', 0)}**\n"
                f"- 🏢 Present Today: **{stats.get('present_today', 0)}**\n"
                f"- 🏠 Absent Today: **{stats.get('absent_today', 0)}**\n"
                f"- 🌴 Pending Leaves: **{stats.get('pending_leaves', 0)}**\n"
                f"- 💳 Monthly Payroll: **${stats.get('total_payroll_month', 0):,.2f}**\n"
                f"- 📈 Average Salary: **${stats.get('avg_salary', 0):,.2f}**"
            )
            return {"answer": answer, "agent_used": "OrchestratorDashboard", "task_type": "dashboard_query", "status": "success"}
        except Exception as e:
            return {"answer": f"⚠️ Dashboard query failed: {e}", "agent_used": "OrchestratorDashboard", "task_type": "dashboard_query", "status": "error"}

    def _handle_general(self, query: str, db) -> dict:
        answer = (
            f"I'm not sure I understand: *\"{query}\"*\n\n"
            "Here are things I can help with:\n"
            "- **Payroll** — summaries, processing status\n"
            "- **Attendance** — monthly stats, leave requests\n"
            "- **Employees** — headcount, department breakdown, top earners\n"
            "- **Analytics** — insights and anomaly detection\n"
            "- **Reports** — how to download reports\n"
            "- **Dashboard** — overall system summary\n\n"
            "Try asking: *\"Show payroll summary\"* or *\"How many employees are active?\"*"
        )
        return {"answer": answer, "agent_used": "Orchestrator", "task_type": "general", "status": "success"}
