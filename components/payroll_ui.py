"""
payroll_ui.py - Salary Structures & Payroll Processing for PayrollPro AI
"""
import streamlit as st
import pandas as pd
from datetime import date
from utils.calculations import calculate_full_salary


def render_salary_structures(db, user_role):
    """Salary structure management."""
    st.markdown("## 💰 Salary Structures")

    tab1, tab2 = st.tabs(["📋 All Structures", "⚙️ Assign / Edit Structure"])

    with tab1:
        try:
            structures = db.get_all_salary_structures()
            if structures:
                df = pd.DataFrame(structures)
                display = [c for c in ["emp_code", "full_name", "basic_salary", "hra_percent",
                                        "pf_percent", "tax_percent", "bonus", "effective_date"] if c in df.columns]
                st.dataframe(df[display], use_container_width=True, hide_index=True)
            else:
                st.info("No salary structures defined yet.")
        except Exception as e:
            st.warning(f"Could not load structures: {e}")

    with tab2:
        _render_assign_salary_structure(db)


def _render_assign_salary_structure(db):
    st.subheader("⚙️ Assign Salary Structure")

    employees = db.get_all_employees()
    if not employees:
        st.info("No employees found.")
        return

    emp_df = pd.DataFrame(employees)
    emp_opts = {f"{r['full_name']} ({r['employee_id']})": r['id'] for _, r in emp_df.iterrows()}

    selected_label = st.selectbox("Select Employee", list(emp_opts.keys()))
    selected_id = emp_opts[selected_label]

    # Prefill from existing structure or DB defaults
    existing = db.get_salary_structure(selected_id)
    defaults = {}
    try:
        defaults = db.get_salary_defaults() or {}
    except Exception:
        pass
    emp = db.get_employee(selected_id)
    prefill_basic = existing.get("basic_salary", emp.get("basic_salary", 0)) if existing else emp.get("basic_salary", 0)

    with st.form("salary_structure_form"):
        col1, col2 = st.columns(2)
        with col1:
            basic = st.number_input("Basic Salary ($)", value=float(prefill_basic), min_value=0.0, step=100.0)
            hra_pct = st.number_input("HRA %", value=float(existing.get("hra_percent", defaults.get("hra_percent", 40)) if existing else defaults.get("hra_percent", 40)), min_value=0.0, max_value=100.0, step=0.5)
            medical_pct = st.number_input("Medical %", value=float(existing.get("medical_percent", defaults.get("medical_percent", 10)) if existing else defaults.get("medical_percent", 10)), min_value=0.0, max_value=100.0, step=0.5)
            transport_pct = st.number_input("Transport %", value=float(existing.get("transport_percent", defaults.get("transport_percent", 5)) if existing else defaults.get("transport_percent", 5)), min_value=0.0, max_value=100.0, step=0.5)
        with col2:
            pf_pct = st.number_input("PF % (deduction)", value=float(existing.get("pf_percent", defaults.get("pf_percent", 12)) if existing else defaults.get("pf_percent", 12)), min_value=0.0, max_value=100.0, step=0.5)
            tax_pct = st.number_input("Tax % (deduction)", value=float(existing.get("tax_percent", defaults.get("tax_percent", 10)) if existing else defaults.get("tax_percent", 10)), min_value=0.0, max_value=100.0, step=0.5)
            other_pct = st.number_input("Other Deductions %", value=float(existing.get("other_deduction_percent", defaults.get("other_deduction_percent", 0)) if existing else defaults.get("other_deduction_percent", 0)), min_value=0.0, max_value=100.0, step=0.5)
            bonus = st.number_input("Monthly Bonus ($)", value=float(existing.get("bonus", 0) if existing else 0), min_value=0.0, step=50.0)

        effective_date = st.date_input("Effective Date", value=date.today())

        # Live preview
        calc = calculate_full_salary(basic, hra_pct, medical_pct, transport_pct, pf_pct, tax_pct, other_pct, bonus)
        st.markdown("**📊 Live Salary Breakdown Preview**")
        p1, p2, p3 = st.columns(3)
        with p1:
            st.metric("Gross Salary", f"${calc['gross_salary']:,.0f}")
        with p2:
            st.metric("Total Deductions", f"${calc['total_deductions']:,.0f}")
        with p3:
            st.metric("Net Salary", f"${calc['net_salary']:,.0f}")

        submitted = st.form_submit_button("💾 Save Structure", use_container_width=True)
        if submitted:
            try:
                db.save_salary_structure(
                    employee_id=selected_id,
                    basic_salary=basic,
                    hra_percent=hra_pct,
                    medical_percent=medical_pct,
                    transport_percent=transport_pct,
                    pf_percent=pf_pct,
                    tax_percent=tax_pct,
                    other_deduction_percent=other_pct,
                    bonus=bonus,
                    effective_date=effective_date.isoformat(),
                )
                st.success(f"✅ Salary structure saved for {selected_label}.")
            except Exception as e:
                st.error(f"Error saving: {e}")


def render_payroll_management(db, user_role):
    """Full payroll processing page."""
    st.markdown("## 💳 Payroll Management")

    tab1, tab2, tab3 = st.tabs(["🔄 Process Payroll", "📊 Payroll Register", "📜 History"])

    with tab1:
        _render_process_payroll(db)
    with tab2:
        _render_payroll_register(db)
    with tab3:
        _render_payroll_history(db)


def _render_process_payroll(db):
    st.subheader("🔄 Process Monthly Payroll")

    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Month", list(range(1, 13)), index=date.today().month - 1,
                             format_func=lambda m: date(2000, m, 1).strftime("%B"))
    with col2:
        year = st.selectbox("Year", list(range(date.today().year - 2, date.today().year + 1)), index=2)

    working_days = st.number_input("Working Days in Month", min_value=1, max_value=31, value=26)

    employees = db.get_all_employees()
    if not employees:
        st.info("No active employees.")
        return

    st.markdown(f"**{len(employees)} employee(s) will be processed.**")

    if st.button("⚡ Process Payroll for All Employees", type="primary", use_container_width=True):
        progress = st.progress(0)
        processed, skipped, errors = 0, 0, []

        for i, emp in enumerate(employees):
            emp_id = emp["id"]
            try:
                ss = db.get_salary_structure(emp_id)
                if not ss:
                    skipped += 1
                    continue

                att = db.get_attendance_history(employee_id=emp_id, month=month, year=year)
                present_days = sum(1 for a in att if a["status"] in ("present", "late", "half_day")) if att else working_days

                calc = calculate_full_salary(
                    basic=ss["basic_salary"],
                    hra_pct=ss["hra_percent"],
                    medical_pct=ss["medical_percent"],
                    transport_pct=ss["transport_percent"],
                    pf_pct=ss["pf_percent"],
                    tax_pct=ss["tax_percent"],
                    other_ded_pct=ss["other_deduction_percent"],
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
                    processed_by=st.session_state.get("username", "admin"),
                )
                processed += 1
            except Exception as e:
                errors.append(f"{emp.get('full_name', emp_id)}: {e}")

            progress.progress((i + 1) / len(employees))

        progress.empty()
        st.success(f"✅ Processed: {processed} | Skipped (no structure): {skipped}")
        if errors:
            with st.expander(f"⚠️ {len(errors)} error(s)"):
                for e in errors:
                    st.error(e)


def _render_payroll_register(db):
    st.subheader("📊 Payroll Register")

    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Month", list(range(1, 13)), index=date.today().month - 1,
                             format_func=lambda m: date(2000, m, 1).strftime("%B"), key="reg_month")
    with col2:
        year = st.selectbox("Year", list(range(date.today().year - 2, date.today().year + 1)), index=2, key="reg_year")

    records = db.get_payroll_by_month(month=month, year=year)
    if not records:
        st.info(f"No payroll records for {date(year, month, 1).strftime('%B %Y')}.")
        return

    df = pd.DataFrame(records)
    total_net = df["net_salary"].sum() if "net_salary" in df.columns else 0
    total_gross = df["gross_salary"].sum() if "gross_salary" in df.columns else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Employees Processed", len(records))
    with c2:
        st.metric("Total Gross", f"${total_gross:,.0f}")
    with c3:
        st.metric("Total Net Payroll", f"${total_net:,.0f}")

    display = [c for c in ["emp_code", "full_name", "department", "gross_salary",
                             "total_deductions", "net_salary", "present_days", "working_days", "status"] if c in df.columns]
    st.dataframe(df[display], use_container_width=True, hide_index=True)

    from io import BytesIO
    buf = BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    st.download_button("📥 Export to Excel", data=buf,
                       file_name=f"payroll_{year}_{month:02d}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _render_payroll_history(db):
    st.subheader("📜 Payroll History")
    employees = db.get_all_employees()
    if not employees:
        st.info("No employees.")
        return

    emp_df = pd.DataFrame(employees)
    emp_opts = {"All Employees": None}
    emp_opts.update({f"{r['full_name']} ({r['employee_id']})": r['id'] for _, r in emp_df.iterrows()})
    selected = st.selectbox("Employee", list(emp_opts.keys()))
    selected_id = emp_opts[selected]

    all_records = []
    for yr in range(date.today().year - 2, date.today().year + 1):
        for mo in range(1, 13):
            if yr == date.today().year and mo > date.today().month:
                break
            recs = db.get_payroll_by_month(month=mo, year=yr)
            if recs:
                all_records.extend(recs)

    if not all_records:
        st.info("No payroll history found.")
        return

    df = pd.DataFrame(all_records)
    if selected_id and "employee_id" in df.columns:
        df = df[df["employee_id"] == selected_id]

    if df.empty:
        st.info("No records for selected employee.")
        return

    display = [c for c in ["full_name", "month", "year", "gross_salary", "net_salary", "status"] if c in df.columns]
    st.dataframe(df[display], use_container_width=True, hide_index=True)
