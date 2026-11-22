"""
employee_ui.py - Employee Management UI for PayrollPro AI
"""
import streamlit as st
import pandas as pd
from datetime import date
from components.sidebar import render_page_header
from utils.security import generate_employee_id, sanitize_input
from utils.validators import validate_email, validate_phone, validate_salary

EMPLOYMENT_STATUSES = ["Full-time", "Part-time", "Contract", "Intern", "Probation", "Terminated"]


def _get_departments(db):
    try:
        depts = db.get_all_departments()
        return {d["name"]: d["id"] for d in depts} if depts else {}
    except Exception:
        return {}


def render_employee_management(db, user_role):
    render_page_header("Employee Management", "Add, view, edit and manage employees", "👥")

    sub = st.session_state.get("employee_subpage", "list")

    tab1, tab2 = st.tabs(["👤 Employee List", "➕ Add Employee"])

    with tab1:
        if sub == "edit" and st.session_state.get("edit_employee_id"):
            _render_edit_employee(db, st.session_state.edit_employee_id)
        elif sub == "profile" and st.session_state.get("view_employee_id"):
            _render_employee_profile(db, st.session_state.view_employee_id)
        else:
            render_employee_list(db)

    with tab2:
        _render_add_employee(db)


def render_employee_list(db):
    col_s, col_d, col_st = st.columns([3, 2, 2])
    with col_s:
        search = st.text_input("🔍 Search", placeholder="Name, email, ID…")
    with col_d:
        dept_map = _get_departments(db)
        dept_opts = ["All Departments"] + list(dept_map.keys())
        dept_filter = st.selectbox("Department", dept_opts)
    with col_st:
        status_filter = st.selectbox("Status", ["All", "Active", "Inactive"])

    try:
        employees = db.get_all_employees()
    except Exception as e:
        st.error(f"Failed to load employees: {e}")
        return

    if not employees:
        st.info("No employees found. Add your first employee above.")
        return

    df = pd.DataFrame(employees)

    if search:
        mask = (
            df.get("full_name", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
            df.get("email", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
            df.get("employee_id", pd.Series(dtype=str)).str.contains(search, case=False, na=False)
        )
        df = df[mask]
    if dept_filter != "All Departments" and "department_name" in df.columns:
        df = df[df["department_name"] == dept_filter]
    if status_filter == "Active" and "is_active" in df.columns:
        df = df[df["is_active"] == 1]
    elif status_filter == "Inactive" and "is_active" in df.columns:
        df = df[df["is_active"] == 0]

    if df.empty:
        st.warning("No employees match your filters.")
        return

    display_cols = [c for c in ["employee_id", "full_name", "department_name", "designation",
                                 "employment_status", "basic_salary", "is_active"] if c in df.columns]
    df_display = df[display_cols].copy()
    if "is_active" in df_display.columns:
        df_display["is_active"] = df_display["is_active"].apply(lambda x: "✅ Active" if x else "❌ Inactive")
    if "basic_salary" in df_display.columns:
        df_display["basic_salary"] = df_display["basic_salary"].apply(lambda x: f"${x:,.0f}")
    df_display.columns = [c.replace("_", " ").title() for c in df_display.columns]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**🛠 Actions**")
    a1, a2, a3 = st.columns([3, 1, 1])
    with a1:
        emp_options = {f"{r.get('employee_id','')}) – {r.get('full_name','')}": r.get("id")
                       for _, r in df.iterrows()}
        selected_label = st.selectbox("Select Employee", list(emp_options.keys()))
        selected_id = emp_options.get(selected_label)
    with a2:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.edit_employee_id = selected_id
            st.session_state.employee_subpage = "edit"
            st.rerun()
    with a3:
        if st.button("👁 Profile", use_container_width=True):
            st.session_state.view_employee_id = selected_id
            st.session_state.employee_subpage = "profile"
            st.rerun()

    with st.expander("🗑️ Delete Employee (irreversible)"):
        st.warning("⚠️ This permanently deactivates the employee.")
        confirm = st.text_input("Type employee's full name to confirm")
        if st.button("Delete", type="primary"):
            matched = next((r for _, r in df.iterrows() if r.get("id") == selected_id), None)
            if matched and confirm.strip() == matched.get("full_name", ""):
                try:
                    db.delete_employee(selected_id)
                    st.success("Employee deactivated.")
                    st.session_state.employee_subpage = "list"
                    st.rerun()
                except Exception as e:
                    st.error(f"Delete failed: {e}")
            else:
                st.error("Name does not match.")


def _render_add_employee(db):
    st.subheader("➕ Add New Employee")
    dept_map = _get_departments(db)

    with st.form("add_employee_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            designation = st.text_input("Designation / Job Title")
        with col2:
            department = st.selectbox("Department", list(dept_map.keys()) if dept_map else ["—"])
            employment_status = st.selectbox("Employment Type", EMPLOYMENT_STATUSES)
            joining_date = st.date_input("Joining Date", value=date.today())
            basic_salary = st.number_input("Basic Salary ($)", min_value=0.0, step=100.0)

        address = st.text_area("Address")
        submitted = st.form_submit_button("💾 Add Employee", use_container_width=True)

        if submitted:
            errors = []
            if not full_name.strip():
                errors.append("Full name is required.")
            if email and not validate_email(email):
                errors.append("Invalid email format.")
            if phone and not validate_phone(phone):
                errors.append("Invalid phone number.")
            if basic_salary < 0:
                errors.append("Salary cannot be negative.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                try:
                    seq = db.get_next_employee_sequence()
                    emp_id = generate_employee_id("EMP", seq)
                    dept_id = dept_map.get(department)
                    db.add_employee(
                        employee_id=emp_id,
                        full_name=sanitize_input(full_name),
                        email=email.strip(),
                        phone=phone.strip(),
                        address=sanitize_input(address),
                        department_id=dept_id,
                        designation=sanitize_input(designation),
                        joining_date=joining_date.isoformat(),
                        employment_status=employment_status,
                        basic_salary=basic_salary,
                    )
                    st.success(f"✅ Employee **{full_name}** added with ID **{emp_id}**.")
                except Exception as e:
                    st.error(f"Error adding employee: {e}")


def _render_edit_employee(db, emp_id):
    emp = db.get_employee(emp_id)
    if not emp:
        st.error("Employee not found.")
        return

    st.subheader(f"✏️ Edit — {emp['full_name']}")
    dept_map = _get_departments(db)

    with st.form("edit_employee_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name", value=emp.get("full_name", ""))
            email = st.text_input("Email", value=emp.get("email", ""))
            phone = st.text_input("Phone", value=emp.get("phone", ""))
            designation = st.text_input("Designation", value=emp.get("designation", ""))
        with col2:
            dept_names = list(dept_map.keys())
            current_dept = emp.get("department_name", "")
            dept_idx = dept_names.index(current_dept) if current_dept in dept_names else 0
            department = st.selectbox("Department", dept_names, index=dept_idx)
            status_idx = EMPLOYMENT_STATUSES.index(emp.get("employment_status", "Full-time")) if emp.get("employment_status") in EMPLOYMENT_STATUSES else 0
            employment_status = st.selectbox("Employment Type", EMPLOYMENT_STATUSES, index=status_idx)
            basic_salary = st.number_input("Basic Salary ($)", value=float(emp.get("basic_salary", 0)), min_value=0.0, step=100.0)
            is_active = st.checkbox("Active", value=bool(emp.get("is_active", 1)))

        address = st.text_area("Address", value=emp.get("address", ""))

        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col_cancel:
            cancel = st.form_submit_button("✖ Cancel", use_container_width=True)

        if cancel:
            st.session_state.employee_subpage = "list"
            st.rerun()

        if submitted:
            try:
                db.update_employee(
                    emp_id=emp_id,
                    full_name=sanitize_input(full_name),
                    email=email.strip(),
                    phone=phone.strip(),
                    address=sanitize_input(address),
                    department_id=dept_map.get(department),
                    designation=sanitize_input(designation),
                    employment_status=employment_status,
                    basic_salary=basic_salary,
                    is_active=is_active,
                )
                st.success("✅ Employee updated successfully.")
                st.session_state.employee_subpage = "list"
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")


def _render_employee_profile(db, emp_id):
    emp = db.get_employee(emp_id)
    if not emp:
        st.error("Employee not found.")
        return

    st.subheader(f"👤 Profile — {emp['full_name']}")
    if st.button("← Back to List"):
        st.session_state.employee_subpage = "list"
        st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Employee ID", emp.get("employee_id", "—"))
        st.metric("Department", emp.get("department_name", "—"))
        st.metric("Designation", emp.get("designation", "—"))
    with col2:
        st.metric("Basic Salary", f"${emp.get('basic_salary', 0):,.0f}")
        st.metric("Employment Type", emp.get("employment_status", "—"))
        st.metric("Joining Date", emp.get("joining_date", "—"))
    with col3:
        st.metric("Status", "✅ Active" if emp.get("is_active") else "❌ Inactive")
        st.metric("Email", emp.get("email", "—"))
        st.metric("Phone", emp.get("phone", "—"))

    st.markdown("---")
    st.markdown(f"**📍 Address:** {emp.get('address', 'N/A')}")

    # Salary structure
    try:
        ss = db.get_salary_structure(emp_id)
        if ss:
            st.markdown("### 💰 Salary Structure")
            cols = st.columns(4)
            fields = [("HRA %", "hra_percent"), ("Medical %", "medical_percent"),
                      ("Transport %", "transport_percent"), ("PF %", "pf_percent"),
                      ("Tax %", "tax_percent"), ("Bonus", "bonus")]
            for i, (label, key) in enumerate(fields):
                with cols[i % 4]:
                    st.metric(label, ss.get(key, 0))
    except Exception:
        pass

    # Attendance summary
    try:
        today = __import__("datetime").date.today()
        att = db.get_attendance_history(employee_id=emp_id, month=today.month, year=today.year)
        if att:
            df = pd.DataFrame(att)
            st.markdown("### 📅 This Month's Attendance")
            st.dataframe(df[["date", "status", "check_in", "check_out"]].head(31),
                         use_container_width=True, hide_index=True)
    except Exception:
        pass
