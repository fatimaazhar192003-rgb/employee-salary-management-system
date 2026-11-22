"""
reports_ui.py - Reports & Downloads for PayrollPro AI
"""
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date


def render_reports(db, report_agent):
    """Reports page with tabs."""
    st.markdown("## 📄 Reports")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Payroll Reports",
        "📅 Attendance Reports",
        "👤 Employee Reports",
        "🏢 Department Reports",
        "🤖 AI Execution History",
    ])

    with tab1:
        render_payroll_report_download(db, report_agent)
    with tab2:
        _render_attendance_report_download(db)
    with tab3:
        _render_employee_report_download(db)
    with tab4:
        _render_department_report(db)
    with tab5:
        render_ai_execution_history(db)


# ─────────────────────────── PAYROLL REPORTS ────────────────────────

def render_payroll_report_download(db, report_agent):
    """Month/year selector + Download PDF + Download Excel buttons."""
    st.subheader("💰 Payroll Reports")

    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox(
            "Month",
            list(range(1, 13)),
            index=date.today().month - 1,
            format_func=lambda m: date(2000, m, 1).strftime("%B"),
            key="pay_rpt_month",
        )
    with col2:
        year = st.selectbox(
            "Year",
            list(range(date.today().year - 3, date.today().year + 1)),
            index=3,
            key="pay_rpt_year",
        )

    payroll_records = db.get_payroll_by_month(month=month, year=year)

    if not payroll_records:
        st.info(f"No payroll records found for {date(year, month, 1).strftime('%B %Y')}.")
        return

    df = pd.DataFrame(payroll_records)
    st.dataframe(df, use_container_width=True, hide_index=True)

    col_pdf, col_excel = st.columns(2)

    with col_excel:
        buf = BytesIO()
        df.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        st.download_button(
            label="📥 Download Excel",
            data=buf,
            file_name=f"payroll_{year}_{month:02d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_pdf:
        if st.button("📥 Generate & Download PDF", use_container_width=True, key="payroll_pdf_btn"):
            with st.spinner("Generating PDF..."):
                try:
                    pdf_bytes = report_agent.generate_payroll_pdf(month=month, year=year, records=payroll_records)
                    st.download_button(
                        label="📄 Download PDF Now",
                        data=pdf_bytes,
                        file_name=f"payroll_{year}_{month:02d}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="payroll_pdf_download",
                    )
                except Exception as e:
                    st.error(f"Could not generate PDF: {e}")


# ─────────────────────────── ATTENDANCE REPORTS ─────────────────────

def _render_attendance_report_download(db):
    """Attendance report with Excel download."""
    st.subheader("📅 Attendance Reports")

    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox(
            "Month",
            list(range(1, 13)),
            index=date.today().month - 1,
            format_func=lambda m: date(2000, m, 1).strftime("%B"),
            key="att_dl_month",
        )
    with col2:
        year = st.selectbox(
            "Year",
            list(range(date.today().year - 3, date.today().year + 1)),
            index=3,
            key="att_dl_year",
        )

    records = db.get_attendance_history(employee_id=None, month=month, year=year)
    if not records:
        st.info("No attendance records found.")
        return

    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True, hide_index=True)

    buf = BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    st.download_button(
        label="📥 Download Attendance Report (Excel)",
        data=buf,
        file_name=f"attendance_{year}_{month:02d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ─────────────────────────── EMPLOYEE REPORTS ───────────────────────

def _render_employee_report_download(db):
    """Employee report CSV download."""
    st.subheader("👤 Employee Reports")

    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Employment Status", ["All", "active", "inactive", "terminated"], key="emp_rpt_status")
    with col2:
        departments = db.get_all_departments()
        dept_options = {"All Departments": None}
        if departments:
            dept_options.update({d["name"]: d["id"] for d in departments})
        selected_dept_name = st.selectbox("Department", list(dept_options.keys()), key="emp_rpt_dept")
        selected_dept_id = dept_options[selected_dept_name]

    employees = db.get_all_employees(
        status=None if status_filter == "All" else status_filter,
        department_id=selected_dept_id,
    )

    if not employees:
        st.info("No employees found.")
        return

    df = pd.DataFrame(employees)
    # Hide sensitive columns
    for col in ["password_hash", "password"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    st.dataframe(df, use_container_width=True, hide_index=True)

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Employee List (CSV)",
        data=csv_data,
        file_name="employees.csv",
        mime="text/csv",
    )


# ─────────────────────────── DEPARTMENT REPORTS ─────────────────────

def _render_department_report(db):
    """Department expense/headcount summary."""
    st.subheader("🏢 Department Reports")

    departments = db.get_all_departments()
    if not departments:
        st.info("No departments found.")
        return

    df = pd.DataFrame(departments)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Department expense summary (last payroll)
    today = date.today()
    expense_data = db.get_department_expenses(
        f"{today.year}-01-01",
        today.isoformat(),
    )
    if expense_data:
        st.markdown("### Department Expense Summary")
        exp_df = pd.DataFrame(expense_data)
        st.dataframe(exp_df, use_container_width=True, hide_index=True)

        buf = BytesIO()
        exp_df.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        st.download_button(
            label="📥 Download Department Report (Excel)",
            data=buf,
            file_name="department_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ─────────────────────────── AI EXECUTION HISTORY ───────────────────

def render_ai_execution_history(db):
    """Show AI execution logs table with expandable rows."""
    st.subheader("🤖 AI Execution History")

    try:
        logs = db.get_ai_logs()
    except Exception as e:
        st.warning(f"Could not load AI logs: {e}")
        return

    if not logs:
        st.info("No AI execution history found.")
        return

    df = pd.DataFrame(logs)

    # Summary table (compact)
    summary_cols = ["timestamp", "username", "agent_used", "task_type", "status"]
    available = [c for c in summary_cols if c in df.columns]
    if available:
        st.dataframe(df[available], use_container_width=True, hide_index=True)

    st.markdown("### Execution Details")
    for i, row in df.iterrows():
        label = f"#{i+1} | {row.get('timestamp', '')} | {row.get('agent_used', 'Agent')} | {row.get('task_type', '')} | {row.get('status', '')}"
        with st.expander(label):
            st.markdown(f"**User Query:** {row.get('user_query', 'N/A')}")
            st.markdown(f"**Agent:** {row.get('agent_used', 'N/A')}")
            st.markdown(f"**Task:** {row.get('task_type', 'N/A')}")
            st.markdown(f"**Status:** {row.get('status', 'N/A')}")
            result = row.get("result", "")
            if result:
                st.markdown("**Result:**")
                st.code(str(result), language="json")
            st.markdown(f"**Timestamp:** {row.get('timestamp', 'N/A')}")
