"""
PayrollPro AI - Agentic AI-Powered Salary Management System
Main entry point for the Streamlit application.
"""
import streamlit as st
import os
import sys

# ── Page config MUST be the very first Streamlit call ─────────────────────────
st.set_page_config(
    page_title="PayrollPro AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Add project root to Python path ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── CSS loader ────────────────────────────────────────────────────────────────
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

# ── Database initialisation ───────────────────────────────────────────────────
from database import DatabaseManager  # noqa: E402

db = DatabaseManager()
db.initialize_database()


# ── Cached agent instances ────────────────────────────────────────────────────
@st.cache_resource
def get_orchestrator():
    from agents.orchestrator import AgentOrchestrator
    return AgentOrchestrator()


@st.cache_resource
def get_analytics_agent():
    from agents.analytics_agent import AnalyticsAgent
    return AnalyticsAgent()


@st.cache_resource
def get_report_agent():
    from agents.report_agent import ReportAgent
    return ReportAgent()


# ── Session-state bootstrap ───────────────────────────────────────────────────
_DEFAULTS = {
    "authenticated": False,
    "username": None,
    "user_role": None,
    "user_full_name": None,
    "current_page": "dashboard",
    "force_password_change": False,
    "user": {},
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────

def render_login():
    st.markdown(
        """<style>
        [data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#0f172a,#1e1b4b);}
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown(
            """<div style="background:#1e293b;padding:2.5rem;border-radius:1.25rem;
            border:1px solid #334155;box-shadow:0 25px 50px rgba(0,0,0,.5);text-align:center;">
            <div style="font-size:3rem">💰</div>
            <h2 style="margin:.4rem 0;background:linear-gradient(135deg,#6366f1,#06b6d4);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">PayrollPro AI</h2>
            <p style="color:#94a3b8;font-size:.88rem;">Agentic AI-Powered Salary Management</p>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            if st.form_submit_button("🔐  Login", use_container_width=True):
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    _authenticate(username, password)
        st.caption("Default: **admin** / **admin123**")


def _authenticate(username: str, password: str):
    from utils.security import verify_password
    user = db.get_user(username)
    if user and verify_password(password, user["password_hash"]):
        st.session_state.update({
            "authenticated": True,
            "username": username,
            "user_role": user["role"],
            "user_full_name": user.get("full_name", username),
            "force_password_change": bool(user.get("force_password_change", False)),
            "user": {"username": username, "full_name": user.get("full_name", username), "role": user["role"]},
        })
        try:
            db.update_last_login(username)
        except Exception:
            pass
        st.rerun()
    else:
        st.error("❌ Invalid username or password.")


# ─────────────────────────────────────────────────────────────────────────────
# FORCE PASSWORD CHANGE
# ─────────────────────────────────────────────────────────────────────────────

def render_force_password_change():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.warning("🔑 **Password change required** before you can continue.")
        with st.form("force_pw_form"):
            new_pw = st.text_input("New Password", type="password", help="Min 8 characters")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("✅  Set Password", use_container_width=True):
                if not new_pw or not confirm_pw:
                    st.error("Both fields are required.")
                elif len(new_pw) < 8:
                    st.error("Password must be at least 8 characters.")
                elif new_pw != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    from utils.security import hash_password
                    try:
                        db.update_password(st.session_state.username, hash_password(new_pw), force_change=False)
                        st.session_state.force_password_change = False
                        st.success("✅ Password updated! Redirecting…")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE ROUTER
# ─────────────────────────────────────────────────────────────────────────────

_KEY_TO_PAGE = {
    "dashboard":         "Dashboard",
    "employees":         "Employees",
    "departments":       "Departments",
    "salary_structures": "Salary Structures",
    "attendance":        "Attendance",
    "leaves":            "Leaves",
    "payroll":           "Payroll",
    "ai_assistant":      "AI Assistant",
    "analytics":         "Analytics",
    "reports":           "Reports",
    "settings":          "Settings",
    "backup":            "Settings",
}


def _route(page_key: str, orchestrator, analytics_agent, report_agent):
    page = _KEY_TO_PAGE.get(page_key, page_key)
    role = st.session_state.user_role

    if page == "Dashboard":
        from components.dashboard import render_dashboard
        render_dashboard(db)
    elif page == "Employees":
        from components.employee_ui import render_employee_management
        render_employee_management(db, role)
    elif page == "Departments":
        from components.settings_ui import render_department_management
        render_department_management(db, role)
    elif page == "Salary Structures":
        from components.payroll_ui import render_salary_structures
        render_salary_structures(db, role)
    elif page == "Attendance":
        from components.attendance_ui import render_attendance_management
        render_attendance_management(db, role)
    elif page == "Leaves":
        from components.attendance_ui import render_leave_management
        render_leave_management(db, role)
    elif page == "Payroll":
        from components.payroll_ui import render_payroll_management
        render_payroll_management(db, role)
    elif page == "AI Assistant":
        from components.ai_chat import render_ai_chat
        render_ai_chat(db, orchestrator, role)
    elif page == "Analytics":
        from components.analytics_ui import render_analytics
        render_analytics(db, analytics_agent)
    elif page == "Reports":
        from components.reports_ui import render_reports
        render_reports(db, report_agent)
    elif page == "Settings":
        from components.settings_ui import render_settings
        render_settings(db, role)
    else:
        st.error(f"Unknown page: '{page}'")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if not st.session_state.authenticated:
        render_login()
        return

    if st.session_state.force_password_change:
        render_force_password_change()
        return

    orchestrator = get_orchestrator()
    analytics_agent = get_analytics_agent()
    report_agent = get_report_agent()

    from components.sidebar import render_sidebar
    page_key = render_sidebar(st.session_state.user_role)
    _route(page_key, orchestrator, analytics_agent, report_agent)


if __name__ == "__main__":
    main()
