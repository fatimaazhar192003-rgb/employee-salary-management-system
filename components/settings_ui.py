"""
settings_ui.py - Settings & Administration for PayrollPro AI
"""
import streamlit as st
import pandas as pd
from datetime import date


def render_settings(db, user_role):
    """Settings page — Admin-only with 5 tabs."""
    st.markdown("## ⚙️ Settings")

    if user_role not in ("admin", "hr"):
        st.error("🚫 You do not have permission to access Settings.")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Company Info",
        "💲 Salary Components",
        "👥 User Management",
        "🗄️ Database",
        "🔑 Change Password",
    ])

    with tab1:
        render_company_settings(db)
    with tab2:
        render_salary_config(db)
    with tab3:
        if user_role == "admin":
            render_user_management(db)
        else:
            st.info("Only admins can manage users.")
    with tab4:
        render_database_settings(db)
    with tab5:
        render_change_password(db)


# ─────────────────────────── COMPANY SETTINGS ───────────────────────

def render_company_settings(db):
    """Company info form with save."""
    st.subheader("🏢 Company Information")

    try:
        config = db.get_company_settings() or {}
    except Exception:
        config = {}

    with st.form("company_settings_form"):
        company_name = st.text_input("Company Name", value=config.get("name", "PayrollPro Corp"))
        address = st.text_area("Address", value=config.get("address", "123 Business Avenue, Tech City"))
        phone = st.text_input("Phone", value=config.get("phone", "+1-555-0100"))
        email = st.text_input("Email", value=config.get("email", "hr@payrollpro.com"))

        col1, col2 = st.columns(2)
        with col1:
            currency = st.selectbox(
                "Currency",
                ["USD", "EUR", "GBP", "INR", "AED", "SGD", "CAD", "AUD"],
                index=["USD", "EUR", "GBP", "INR", "AED", "SGD", "CAD", "AUD"].index(config.get("currency", "USD")),
            )
        with col2:
            currency_symbol = st.text_input("Currency Symbol", value=config.get("currency_symbol", "$"), max_chars=4)

        tax_year = st.text_input("Tax Year", value=config.get("tax_year", str(date.today().year)))

        st.markdown("**Company Logo** *(placeholder — upload coming soon)*")
        st.image("https://via.placeholder.com/200x80?text=Your+Logo", width=200)

        saved = st.form_submit_button("💾 Save Company Info", use_container_width=True)
        if saved:
            try:
                db.save_company_settings({
                    "name": company_name,
                    "address": address,
                    "phone": phone,
                    "email": email,
                    "currency": currency,
                    "currency_symbol": currency_symbol,
                    "tax_year": tax_year,
                })
                st.success("✅ Company information saved successfully.")
            except Exception as e:
                st.error(f"Error saving settings: {e}")


# ─────────────────────────── SALARY CONFIG ──────────────────────────

def render_salary_config(db):
    """Global salary component defaults."""
    st.subheader("💲 Default Salary Component Percentages")
    st.markdown("These defaults are applied when creating new salary structures.")

    try:
        defaults = db.get_salary_defaults() or {}
    except Exception:
        defaults = {}

    with st.form("salary_config_form"):
        col1, col2 = st.columns(2)
        with col1:
            hra = st.number_input("HRA % (of Basic)", min_value=0.0, max_value=100.0,
                                  value=float(defaults.get("hra_percent", 40.0)), step=0.5)
            medical = st.number_input("Medical Allowance %", min_value=0.0, max_value=100.0,
                                      value=float(defaults.get("medical_percent", 10.0)), step=0.5)
            transport = st.number_input("Transport Allowance %", min_value=0.0, max_value=100.0,
                                        value=float(defaults.get("transport_percent", 5.0)), step=0.5)
        with col2:
            pf = st.number_input("Provident Fund % (Deduction)", min_value=0.0, max_value=100.0,
                                 value=float(defaults.get("pf_percent", 12.0)), step=0.5)
            tax = st.number_input("Income Tax % (Deduction)", min_value=0.0, max_value=100.0,
                                  value=float(defaults.get("tax_percent", 10.0)), step=0.5)
            other = st.number_input("Other Deductions %", min_value=0.0, max_value=100.0,
                                    value=float(defaults.get("other_deduction_percent", 0.0)), step=0.5)

        saved = st.form_submit_button("💾 Save Salary Defaults", use_container_width=True)
        if saved:
            try:
                db.save_salary_defaults({
                    "hra_percent": hra,
                    "medical_percent": medical,
                    "transport_percent": transport,
                    "pf_percent": pf,
                    "tax_percent": tax,
                    "other_deduction_percent": other,
                })
                st.success("✅ Salary component defaults saved.")
            except Exception as e:
                st.error(f"Error saving salary config: {e}")


# ─────────────────────────── USER MANAGEMENT ────────────────────────

def render_user_management(db):
    """User list + add user form."""
    st.subheader("👥 User Management")

    # List existing users
    try:
        users = db.get_all_users()
    except Exception as e:
        st.warning(f"Could not load users: {e}")
        users = []

    if users:
        df = pd.DataFrame(users)
        display_cols = [c for c in ["username", "full_name", "email", "role", "is_active", "last_login"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No users found.")

    st.markdown("---")
    st.markdown("### ➕ Add New HR User")

    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Username")
            new_full_name = st.text_input("Full Name")
        with col2:
            new_email = st.text_input("Email")
            new_role = st.selectbox("Role", ["hr", "admin"])

        new_password = st.text_input("Initial Password", type="password",
                                     help="User will be forced to change on first login.")
        force_change = st.checkbox("Force password change on first login", value=True)

        submitted = st.form_submit_button("👤 Create User", use_container_width=True)
        if submitted:
            if not new_username or not new_password:
                st.error("Username and password are required.")
            else:
                try:
                    from utils.security import hash_password
                    hashed = hash_password(new_password)
                    db.create_user(
                        username=new_username,
                        password_hash=hashed,
                        role=new_role,
                        full_name=new_full_name,
                        email=new_email,
                        force_password_change=force_change,
                    )
                    st.success(f"✅ User '{new_username}' created with role '{new_role}'.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating user: {e}")

    # Reset password section
    st.markdown("---")
    st.markdown("### 🔑 Reset User Password")
    with st.form("reset_pw_form"):
        reset_username = st.text_input("Username to Reset")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        reset_submitted = st.form_submit_button("🔄 Reset Password", use_container_width=True)
        if reset_submitted:
            if not reset_username or not new_pw:
                st.error("Username and new password are required.")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match.")
            else:
                try:
                    from utils.security import hash_password
                    db.update_password(reset_username, hash_password(new_pw), force_change=True)
                    st.success(f"✅ Password reset for '{reset_username}'. User will be forced to change on next login.")
                except Exception as e:
                    st.error(f"Error resetting password: {e}")


# ─────────────────────────── DATABASE SETTINGS ──────────────────────

def render_database_settings(db):
    """DB backup download."""
    st.subheader("🗄️ Database Management")

    st.markdown("""
    > [!NOTE]
    > This section allows you to download a backup of the SQLite database file.
    > Keep regular backups to prevent data loss.
    """)

    import os
    db_path = db.db_path if hasattr(db, "db_path") else None

    if db_path and os.path.exists(db_path):
        file_size = os.path.getsize(db_path)
        st.metric("Database Size", f"{file_size / 1024:.1f} KB")
        st.caption(f"Database path: `{db_path}`")

        with open(db_path, "rb") as f:
            db_bytes = f.read()

        st.download_button(
            label="📥 Download Database Backup (.db)",
            data=db_bytes,
            file_name=f"salary_management_backup_{date.today().isoformat()}.db",
            mime="application/octet-stream",
        )
    else:
        st.warning("Database file path not accessible.")

    st.markdown("---")
    st.markdown("### ℹ️ Restore Instructions")
    st.markdown("""
    To restore a backup:
    1. Stop the Streamlit application.
    2. Replace `data/salary_management.db` with your backup file.
    3. Restart the application.
    """)


# ─────────────────────────── CHANGE PASSWORD ────────────────────────

def render_change_password(db):
    """Password change form with current password verification."""
    st.subheader("🔑 Change Your Password")

    username = st.session_state.get("username", "")
    if not username:
        st.error("Session expired. Please log in again.")
        return

    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password",
                                     help="Must be at least 8 characters.")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("🔑 Change Password", use_container_width=True)

        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("All fields are required.")
            elif len(new_password) < 8:
                st.error("New password must be at least 8 characters long.")
            elif new_password != confirm_password:
                st.error("New passwords do not match.")
            else:
                try:
                    from utils.security import verify_password, hash_password
                    user = db.get_user(username)
                    if not user or not verify_password(current_password, user["password_hash"]):
                        st.error("Current password is incorrect.")
                    else:
                        db.update_password(username, hash_password(new_password), force_change=False)
                        st.session_state.force_password_change = False
                        st.success("✅ Password changed successfully.")
                except Exception as e:
                    st.error(f"Error changing password: {e}")


# ─────────────────────────── DEPARTMENT MANAGEMENT ──────────────────

def render_department_management(db, user_role):
    """Department CRUD — accessible from main navigation."""
    st.markdown("## 🏢 Department Management")

    if user_role not in ("admin", "hr"):
        st.error("🚫 Access denied.")
        return

    # List departments
    try:
        departments = db.get_all_departments()
    except Exception as e:
        st.warning(f"Could not load departments: {e}")
        departments = []

    if departments:
        df = pd.DataFrame(departments)
        display_cols = [c for c in ["id", "name", "description", "manager_name", "created_at"] if c in df.columns]
        st.dataframe(df[display_cols] if display_cols else df, use_container_width=True, hide_index=True)
    else:
        st.info("No departments created yet.")

    st.markdown("---")
    col_add, col_edit = st.columns(2)

    with col_add:
        st.markdown("### ➕ Add Department")
        with st.form("add_dept_form"):
            dept_name = st.text_input("Department Name")
            dept_desc = st.text_area("Description", max_chars=300)
            submitted = st.form_submit_button("Add Department", use_container_width=True)
            if submitted:
                if not dept_name.strip():
                    st.error("Department name is required.")
                else:
                    try:
                        db.add_department(name=dept_name.strip(), description=dept_desc.strip())
                        st.success(f"✅ Department '{dept_name}' created.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col_edit:
        if departments:
            st.markdown("### ✏️ Edit Department")
            dept_options = {d["name"]: d["id"] for d in departments}
            with st.form("edit_dept_form"):
                selected_name = st.selectbox("Select Department", list(dept_options.keys()))
                selected_id = dept_options[selected_name]
                selected_dept = next((d for d in departments if d["id"] == selected_id), {})

                new_name = st.text_input("New Name", value=selected_dept.get("name", ""))
                new_desc = st.text_area("New Description", value=selected_dept.get("description", ""), max_chars=300)
                update_submitted = st.form_submit_button("💾 Update Department", use_container_width=True)
                if update_submitted:
                    try:
                        db.update_department(dept_id=selected_id, name=new_name.strip(), description=new_desc.strip())
                        st.success(f"✅ Department updated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
