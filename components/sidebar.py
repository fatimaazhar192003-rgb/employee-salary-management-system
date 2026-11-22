"""
sidebar.py - Navigation Sidebar for PayrollPro AI
"""
import streamlit as st

ADMIN_MENU = [
    ("📊", "Dashboard",         "dashboard"),
    ("👥", "Employees",         "employees"),
    ("🏢", "Departments",       "departments"),
    ("💰", "Salary Structures", "salary_structures"),
    ("📅", "Attendance",        "attendance"),
    ("🌴", "Leaves",            "leaves"),
    ("💳", "Payroll",           "payroll"),
    ("🤖", "AI Assistant",      "ai_assistant"),
    ("📈", "Analytics",         "analytics"),
    ("📄", "Reports",           "reports"),
    ("⚙️", "Settings",          "settings"),
]

HR_MENU = [
    ("📊", "Dashboard",    "dashboard"),
    ("👥", "Employees",    "employees"),
    ("📅", "Attendance",   "attendance"),
    ("🌴", "Leaves",       "leaves"),
    ("💳", "Payroll",      "payroll"),
    ("🤖", "AI Assistant", "ai_assistant"),
    ("📄", "Reports",      "reports"),
]


def render_sidebar(user_role: str) -> str:
    """Render dark sidebar with navigation. Returns selected page key."""
    with st.sidebar:
        # Logo
        st.markdown(
            """<div class="sidebar-logo">
            <h2>💼 PayrollPro AI</h2>
            <p>Agentic Salary Management</p>
            </div>""",
            unsafe_allow_html=True,
        )

        # User card
        full_name = st.session_state.get("user_full_name") or \
                    st.session_state.get("user", {}).get("full_name", "User")
        role_label = (user_role or "user").upper()
        st.markdown(
            f"""<div class="sidebar-user">
            <div class="user-name">👤 {full_name}</div>
            <div class="user-role">{role_label}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Navigation
        menu = ADMIN_MENU if user_role == "admin" else HR_MENU
        if "current_page" not in st.session_state:
            st.session_state.current_page = "dashboard"

        for icon, label, key in menu:
            is_active = st.session_state.current_page == key
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.current_page = key
                st.rerun()

        st.markdown("---")
        if st.button("🚪  Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    return st.session_state.get("current_page", "dashboard")


def render_page_header(title: str, subtitle: str = None, icon: str = None):
    icon_html = f"{icon} " if icon else ""
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""<div class="page-header"><h1>{icon_html}{title}</h1>{sub_html}</div>""",
        unsafe_allow_html=True,
    )


def render_kpi_card(title: str, value, delta=None, icon: str = None, color: str = "primary"):
    label = f"{icon} {title}" if icon else title
    delta_str = None
    if delta is not None:
        try:
            delta_str = f"{'▲' if float(str(delta).replace('%','')) >= 0 else '▼'} {delta}"
        except (ValueError, TypeError):
            delta_str = str(delta)
    st.metric(label=label, value=value, delta=delta_str)
