"""
dashboard.py - Main Dashboard for PayrollPro AI
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from components.sidebar import render_page_header, render_kpi_card

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(30,41,59,1)",
    plot_bgcolor="rgba(30,41,59,1)",
    font=dict(color="#94a3b8", family="Inter"),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(gridcolor="rgba(51,65,85,.5)", showgrid=True),
    yaxis=dict(gridcolor="rgba(51,65,85,.5)", showgrid=True),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
COLORS = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"]


def render_dashboard(db):
    render_page_header("Dashboard", "Real-time payroll & workforce overview", "📊")

    stats = {}
    try:
        stats = db.get_dashboard_stats()
    except Exception as e:
        st.warning(f"Could not load dashboard stats: {e}")

    # ── KPI Row 1 ─────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("👥 Total Employees", stats.get("total_employees", 0))
    with c2:
        st.metric("✅ Active Employees", stats.get("active_employees", 0))
    with c3:
        st.metric("💳 Monthly Payroll", f"${stats.get('total_payroll_month', 0):,.0f}")
    with c4:
        st.metric("📈 Avg Salary", f"${stats.get('avg_salary', 0):,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPI Row 2 ─────────────────────────────────────────────────────
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("🏢 Present Today", stats.get("present_today", 0))
    with c6:
        st.metric("🏠 Absent Today", stats.get("absent_today", 0))
    with c7:
        st.metric("⏳ Pending Payroll", stats.get("pending_payroll", 0))
    with c8:
        st.metric("🌴 Pending Leaves", stats.get("pending_leaves", 0))

    st.markdown("---")

    # ── Charts Row ────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📈 Monthly Payroll Trend")
        try:
            trend_data = db.get_monthly_payroll_trend()
            if trend_data:
                df = pd.DataFrame(trend_data)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df.get("month", []),
                    y=df.get("total", []),
                    mode="lines+markers",
                    line=dict(color="#6366f1", width=2.5),
                    marker=dict(size=7, color="#8b5cf6"),
                    fill="tozeroy",
                    fillcolor="rgba(99,102,241,.12)",
                    name="Net Payroll",
                ))
                fig.update_layout(**PLOT_LAYOUT, height=280)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No payroll data yet.")
        except Exception as e:
            st.warning(f"Chart unavailable: {e}")

    with col_right:
        st.markdown("#### 🏢 Department Salary Breakdown")
        try:
            dept_data = db.get_department_salary_expenses()
            if dept_data:
                df_dept = pd.DataFrame(dept_data)
                fig = px.bar(
                    df_dept, x="department", y="total_salary",
                    color_discrete_sequence=COLORS,
                    labels={"total_salary": "Total Salary ($)", "department": ""},
                )
                fig.update_layout(**PLOT_LAYOUT, height=280)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No department data yet.")
        except Exception as e:
            st.warning(f"Chart unavailable: {e}")

    # ── Bottom Row ────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 📋 Recent Employees")
        try:
            emps = db.get_all_employees()
            if emps:
                df_e = pd.DataFrame(emps[:10])
                show = [c for c in ["employee_id", "full_name", "department_name", "designation", "basic_salary"] if c in df_e.columns]
                st.dataframe(df_e[show], use_container_width=True, hide_index=True)
            else:
                st.info("No employees yet.")
        except Exception as e:
            st.warning(f"Could not load employees: {e}")

    with col_b:
        st.markdown("#### 🌴 Pending Leave Requests")
        try:
            leaves = db.get_leaves_by_status("pending")
            if leaves:
                df_l = pd.DataFrame(leaves[:8])
                show = [c for c in ["employee_name", "leave_type", "start_date", "end_date", "days"] if c in df_l.columns]
                st.dataframe(df_l[show], use_container_width=True, hide_index=True)
            else:
                st.success("✅ No pending leaves.")
        except Exception as e:
            st.warning(f"Could not load leaves: {e}")
