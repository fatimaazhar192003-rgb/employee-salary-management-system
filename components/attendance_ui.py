"""
attendance_ui.py - Attendance & Leave Management UI for PayrollPro AI
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta


# ─────────────────────────── ATTENDANCE ────────────────────────────

def render_attendance_management(db, user_role):
    """Main attendance page with tabs: Mark Attendance, Attendance History, Leave Management."""
    st.markdown("## 📅 Attendance Management")

    tab1, tab2, tab3 = st.tabs(["✅ Mark Attendance", "📊 Attendance History", "📋 Attendance Reports"])

    with tab1:
        render_mark_attendance(db)
    with tab2:
        render_attendance_history(db)
    with tab3:
        _render_attendance_reports(db)


def render_mark_attendance(db):
    """Daily attendance marking UI."""
    st.subheader("Mark Attendance")

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_date = st.date_input("Date", value=date.today(), max_value=date.today())

    employees = db.get_all_employees()
    if not employees:
        st.info("No active employees found. Please add employees first.")
        return

    emp_df = pd.DataFrame(employees)

    # Bulk or individual
    mode = st.radio("Mode", ["Mark Individual", "Bulk Mark All"], horizontal=True)

    if mode == "Mark Individual":
        emp_options = {f"{r['full_name']} ({r['employee_id']})": r['id'] for _, r in emp_df.iterrows()}
        selected_emp_label = st.selectbox("Select Employee", list(emp_options.keys()))
        selected_emp_id = emp_options[selected_emp_label]

        # Check duplicate
        existing = db.get_attendance_record(selected_emp_id, selected_date.isoformat())
        if existing:
            st.warning(f"⚠️ Attendance already marked for this employee on {selected_date}. Submitting will update it.")

        with st.form("mark_attendance_form"):
            status = st.selectbox("Status", ["Present", "Absent", "Half Day", "Late"])
            col_ci, col_co = st.columns(2)
            with col_ci:
                check_in = st.time_input("Check-In Time (optional)", value=None)
            with col_co:
                check_out = st.time_input("Check-Out Time (optional)", value=None)
            notes = st.text_area("Notes (optional)", max_chars=300)
            submitted = st.form_submit_button("💾 Save Attendance", use_container_width=True)

            if submitted:
                try:
                    db.mark_attendance(
                        employee_id=selected_emp_id,
                        att_date=selected_date.isoformat(),
                        status=status.lower().replace(" ", "_"),
                        check_in=check_in.strftime("%H:%M") if check_in else None,
                        check_out=check_out.strftime("%H:%M") if check_out else None,
                        notes=notes.strip() or None,
                    )
                    st.success(f"✅ Attendance marked as **{status}** for {selected_emp_label} on {selected_date}.")
                except Exception as e:
                    st.error(f"Error saving attendance: {e}")

    else:  # Bulk mark
        with st.form("bulk_attendance_form"):
            status = st.selectbox("Status for ALL employees", ["Present", "Absent", "Half Day", "Late"])
            submitted = st.form_submit_button("💾 Bulk Save", use_container_width=True)

            if submitted:
                success_count = 0
                for _, row in emp_df.iterrows():
                    try:
                        db.mark_attendance(
                            employee_id=row["id"],
                            att_date=selected_date.isoformat(),
                            status=status.lower().replace(" ", "_"),
                            check_in=None,
                            check_out=None,
                            notes="Bulk marked",
                        )
                        success_count += 1
                    except Exception:
                        pass
                st.success(f"✅ Bulk attendance marked for {success_count} employee(s) as **{status}** on {selected_date}.")


def render_attendance_history(db):
    """View attendance records with filters."""
    st.subheader("Attendance History")

    employees = db.get_all_employees()
    if not employees:
        st.info("No employees found.")
        return

    emp_df = pd.DataFrame(employees)
    emp_options = {"All Employees": None}
    emp_options.update({f"{r['full_name']} ({r['employee_id']})": r['id'] for _, r in emp_df.iterrows()})

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_emp_label = st.selectbox("Employee", list(emp_options.keys()))
        selected_emp_id = emp_options[selected_emp_label]
    with col2:
        month = st.selectbox("Month", list(range(1, 13)), index=date.today().month - 1,
                             format_func=lambda m: date(2000, m, 1).strftime("%B"))
    with col3:
        year = st.selectbox("Year", list(range(date.today().year - 3, date.today().year + 1)),
                            index=3)

    records = db.get_attendance_history(employee_id=selected_emp_id, month=month, year=year)

    if not records:
        st.info("No attendance records found for the selected filters.")
        return

    df = pd.DataFrame(records)

    # Status badge colouring via styling
    STATUS_COLORS = {
        "present": "🟢",
        "absent": "🔴",
        "half_day": "🟡",
        "late": "🟠",
    }

    df["Status"] = df["status"].apply(lambda s: f"{STATUS_COLORS.get(s, '⚪')} {s.replace('_', ' ').title()}")
    display_cols = {
        "date": "Date",
        "employee_name": "Employee",
        "Status": "Status",
        "check_in": "Check-In",
        "check_out": "Check-Out",
        "notes": "Notes",
    }
    rename_map = {k: v for k, v in display_cols.items() if k in df.columns}
    df_display = df.rename(columns=rename_map)[[v for v in display_cols.values() if v in df.rename(columns=rename_map).columns]]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Attendance percentage per employee
    st.markdown("### 📈 Attendance Summary")
    summary_data = []
    grouped = df.groupby("employee_id") if "employee_id" in df.columns else []
    if hasattr(grouped, "__iter__"):
        for emp_id, grp in grouped:
            total = len(grp)
            present = grp["status"].isin(["present", "late", "half_day"]).sum()
            pct = round(present / total * 100, 1) if total else 0
            name = grp["employee_name"].iloc[0] if "employee_name" in grp.columns else str(emp_id)
            summary_data.append({"Employee": name, "Total Days": total, "Present": present, "Attendance %": pct})

    if summary_data:
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)


def _render_attendance_reports(db):
    """Monthly attendance summary table with export."""
    st.subheader("Attendance Reports")
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Month", list(range(1, 13)), index=date.today().month - 1,
                             format_func=lambda m: date(2000, m, 1).strftime("%B"), key="att_rpt_month")
    with col2:
        year = st.selectbox("Year", list(range(date.today().year - 3, date.today().year + 1)),
                            index=3, key="att_rpt_year")

    records = db.get_attendance_history(employee_id=None, month=month, year=year)
    if not records:
        st.info("No records found.")
        return

    df = pd.DataFrame(records)
    pivot = df.pivot_table(index="employee_name", columns="date", values="status", aggfunc="first")

    st.dataframe(pivot, use_container_width=True)

    # Excel download
    from io import BytesIO
    buf = BytesIO()
    pivot.to_excel(buf, engine="openpyxl")
    buf.seek(0)
    st.download_button(
        label="📥 Download Attendance Report (Excel)",
        data=buf,
        file_name=f"attendance_{year}_{month:02d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ─────────────────────────── LEAVE ─────────────────────────────────

def render_leave_management(db, user_role):
    """Main leave management page."""
    st.markdown("## 🏖️ Leave Management")

    if user_role in ("admin", "hr"):
        tab1, tab2, tab3 = st.tabs(["📝 Apply Leave", "✅ Approve / Reject", "📜 Leave History"])
        with tab1:
            render_apply_leave(db)
        with tab2:
            render_leave_approval(db, user_role)
        with tab3:
            _render_leave_history(db)
    else:
        tab1, tab2 = st.tabs(["📝 Apply Leave", "📜 My Leave History"])
        with tab1:
            render_apply_leave(db)
        with tab2:
            _render_leave_history(db)


def render_apply_leave(db):
    """Leave application form."""
    st.subheader("Apply for Leave")

    employees = db.get_all_employees()
    if not employees:
        st.info("No employees found.")
        return

    emp_df = pd.DataFrame(employees)
    emp_options = {f"{r['full_name']} ({r['employee_id']})": r['id'] for _, r in emp_df.iterrows()}

    with st.form("apply_leave_form"):
        selected_emp_label = st.selectbox("Employee", list(emp_options.keys()))
        selected_emp_id = emp_options[selected_emp_label]

        leave_type = st.selectbox("Leave Type", ["Casual Leave", "Sick Leave", "Annual Leave", "Maternity Leave", "Paternity Leave", "Unpaid Leave"])

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today())
        with col2:
            end_date = st.date_input("End Date", value=date.today())

        if end_date < start_date:
            st.error("End date cannot be before start date.")

        reason = st.text_area("Reason for Leave", max_chars=500)
        submitted = st.form_submit_button("📤 Submit Leave Application", use_container_width=True)

        if submitted:
            if end_date < start_date:
                st.error("Please fix the date range.")
            elif not reason.strip():
                st.error("Please provide a reason for leave.")
            else:
                days = (end_date - start_date).days + 1
                try:
                    db.apply_leave(
                        employee_id=selected_emp_id,
                        leave_type=leave_type,
                        start_date=start_date.isoformat(),
                        end_date=end_date.isoformat(),
                        days=days,
                        reason=reason.strip(),
                    )
                    st.success(f"✅ Leave application submitted for {days} day(s). Pending approval.")
                except Exception as e:
                    st.error(f"Error submitting leave: {e}")


def render_leave_approval(db, user_role):
    """For HR/Admin: Show pending leaves with Approve/Reject buttons."""
    st.subheader("Pending Leave Approvals")

    pending = db.get_leaves_by_status("pending")
    if not pending:
        st.info("🎉 No pending leave requests.")
        return

    for leave in pending:
        with st.expander(f"🧑 {leave.get('employee_name', 'Unknown')} | {leave.get('leave_type', '')} | {leave.get('start_date', '')} → {leave.get('end_date', '')} ({leave.get('days', '')} days)"):
            st.markdown(f"**Reason:** {leave.get('reason', 'N/A')}")
            st.markdown(f"**Applied on:** {leave.get('created_at', 'N/A')}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Approve", key=f"approve_{leave['id']}"):
                    try:
                        db.update_leave_status(leave["id"], "approved", approved_by=st.session_state.get("username", "admin"))
                        st.success("Leave approved!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            with col2:
                if st.button(f"❌ Reject", key=f"reject_{leave['id']}"):
                    try:
                        db.update_leave_status(leave["id"], "rejected", approved_by=st.session_state.get("username", "admin"))
                        st.warning("Leave rejected.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")


def _render_leave_history(db):
    """Show leave history with filters."""
    st.subheader("Leave History")

    employees = db.get_all_employees()
    if not employees:
        st.info("No employees.")
        return

    emp_df = pd.DataFrame(employees)
    emp_options = {"All Employees": None}
    emp_options.update({f"{r['full_name']} ({r['employee_id']})": r['id'] for _, r in emp_df.iterrows()})

    col1, col2 = st.columns(2)
    with col1:
        selected_emp_label = st.selectbox("Employee", list(emp_options.keys()), key="leave_hist_emp")
        selected_emp_id = emp_options[selected_emp_label]
    with col2:
        status_filter = st.selectbox("Status", ["All", "pending", "approved", "rejected"], key="leave_hist_status")

    leaves = db.get_all_leaves(employee_id=selected_emp_id)
    if not leaves:
        st.info("No leave records found.")
        return

    df = pd.DataFrame(leaves)
    if status_filter != "All":
        df = df[df["status"] == status_filter]

    STATUS_ICONS = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    if "status" in df.columns:
        df["Status"] = df["status"].apply(lambda s: f"{STATUS_ICONS.get(s, '❓')} {s.title()}")

    display_map = {
        "employee_name": "Employee",
        "leave_type": "Leave Type",
        "start_date": "Start Date",
        "end_date": "End Date",
        "days": "Days",
        "Status": "Status",
        "reason": "Reason",
        "approved_by": "Approved By",
    }
    df_renamed = df.rename(columns={k: v for k, v in display_map.items() if k in df.columns})
    show_cols = [v for v in display_map.values() if v in df_renamed.columns]
    st.dataframe(df_renamed[show_cols], use_container_width=True, hide_index=True)
