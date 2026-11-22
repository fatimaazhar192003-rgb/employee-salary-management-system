"""
analytics_ui.py - Analytics & Insights Dashboard for PayrollPro AI
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, timedelta


def render_analytics(db, analytics_agent):
    """Full analytics page."""
    st.markdown("## 📊 Analytics & Insights")

    # ── Date range selector ──────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "From",
            value=date.today().replace(day=1) - timedelta(days=365),
            key="analytics_start",
        )
    with col2:
        end_date = st.date_input("To", value=date.today(), key="analytics_end")

    if start_date > end_date:
        st.error("Start date must be before end date.")
        return

    st.markdown("---")

    # Fetch data
    payroll_trends = db.get_payroll_trends(start_date.isoformat(), end_date.isoformat())
    dept_expenses = db.get_department_expenses(start_date.isoformat(), end_date.isoformat())
    salary_dist = db.get_salary_distribution()
    top_earners = db.get_top_earners(limit=5)
    attendance_data = db.get_attendance_heatmap_data(start_date.isoformat(), end_date.isoformat())

    # ── Row 1: Payroll trends + Department chart ──────────────────────
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(create_payroll_trend_chart(payroll_trends), use_container_width=True)
    with col_right:
        st.plotly_chart(create_department_chart(dept_expenses), use_container_width=True)

    # ── Row 2: Salary distribution + Top earners ─────────────────────
    col_left2, col_right2 = st.columns(2)
    with col_left2:
        st.plotly_chart(create_salary_distribution(salary_dist), use_container_width=True)
    with col_right2:
        st.plotly_chart(create_top_earners_chart(top_earners), use_container_width=True)

    # ── Attendance heatmap ────────────────────────────────────────────
    if attendance_data:
        st.markdown("### 📅 Attendance Heatmap")
        st.plotly_chart(create_attendance_heatmap(attendance_data), use_container_width=True)

    st.markdown("---")

    # ── AI Insights ───────────────────────────────────────────────────
    st.markdown("### 🤖 AI-Generated Management Insights")
    with st.spinner("Generating insights..."):
        try:
            insights = analytics_agent.generate_management_insights()
            if isinstance(insights, dict):
                for category, items in insights.items():
                    with st.expander(f"💡 {category}", expanded=True):
                        if isinstance(items, list):
                            for item in items:
                                st.markdown(f"- {item}")
                        else:
                            st.markdown(str(items))
            elif isinstance(insights, str):
                st.markdown(insights)
            else:
                st.info("No insights generated.")
        except Exception as e:
            st.warning(f"Could not generate AI insights: {e}")

    # ── Anomaly detection ─────────────────────────────────────────────
    st.markdown("### 🔍 Anomaly Detection")
    with st.spinner("Checking for anomalies..."):
        try:
            anomalies = analytics_agent.detect_anomalies()
            if anomalies:
                for a in anomalies:
                    st.warning(f"⚠️ {a}")
            else:
                st.success("✅ No anomalies detected in the current dataset.")
        except Exception as e:
            st.warning(f"Anomaly detection unavailable: {e}")


# ─────────────────────────── CHART BUILDERS ────────────────────────

def create_payroll_trend_chart(data):
    """Plotly line chart for monthly payroll trends — dark theme, purple gradient."""
    fig = go.Figure()

    if data:
        df = pd.DataFrame(data)
        months = df.get("month_label", df.get("month", list(range(len(df))))).tolist()
        totals = df.get("total_net", df.get("total", pd.Series([0] * len(df)))).tolist()

        fig.add_trace(
            go.Scatter(
                x=months,
                y=totals,
                mode="lines+markers",
                name="Net Payroll",
                line=dict(color="#a855f7", width=3),
                marker=dict(size=8, color="#c084fc"),
                fill="tozeroy",
                fillcolor="rgba(168,85,247,0.15)",
            )
        )
    else:
        fig.add_annotation(text="No payroll data available", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color="#94a3b8"))

    fig.update_layout(
        title="📈 Monthly Payroll Trend",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#1e293b",
        font=dict(color="#e2e8f0"),
        xaxis=dict(gridcolor="#334155", title="Month"),
        yaxis=dict(gridcolor="#334155", title="Total Payroll ($)"),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def create_department_chart(data):
    """Plotly grouped bar chart for department expenses."""
    fig = go.Figure()

    if data:
        df = pd.DataFrame(data)
        departments = df.get("department", df.get("name", pd.Series())).tolist()
        totals = df.get("total_expense", df.get("total", pd.Series([0] * len(df)))).tolist()
        headcounts = df.get("headcount", df.get("count", pd.Series([1] * len(df)))).tolist()

        fig.add_trace(go.Bar(
            x=departments, y=totals,
            name="Total Expense ($)",
            marker_color="#6366f1",
        ))
        fig.add_trace(go.Bar(
            x=departments, y=headcounts,
            name="Headcount",
            marker_color="#22d3ee",
            yaxis="y2",
        ))
    else:
        fig.add_annotation(text="No department data", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color="#94a3b8"))

    fig.update_layout(
        title="🏢 Department Expense & Headcount",
        barmode="group",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#1e293b",
        font=dict(color="#e2e8f0"),
        xaxis=dict(gridcolor="#334155"),
        yaxis=dict(gridcolor="#334155", title="Total Expense ($)"),
        yaxis2=dict(overlaying="y", side="right", title="Headcount", showgrid=False),
        legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
        margin=dict(l=20, r=60, t=50, b=20),
    )
    return fig


def create_salary_distribution(data):
    """Plotly histogram of salary distribution."""
    fig = go.Figure()

    if data:
        df = pd.DataFrame(data)
        salaries = df.get("basic_salary", df.get("salary", pd.Series())).tolist()
        if salaries:
            fig.add_trace(go.Histogram(
                x=salaries,
                nbinsx=20,
                marker_color="#f59e0b",
                opacity=0.85,
                name="Salary Distribution",
            ))
    else:
        fig.add_annotation(text="No salary data", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color="#94a3b8"))

    fig.update_layout(
        title="📊 Salary Distribution",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#1e293b",
        font=dict(color="#e2e8f0"),
        xaxis=dict(gridcolor="#334155", title="Salary ($)"),
        yaxis=dict(gridcolor="#334155", title="Employees"),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def create_top_earners_chart(data):
    """Plotly horizontal bar chart — top 5 earners."""
    fig = go.Figure()

    if data:
        df = pd.DataFrame(data)
        names = df.get("full_name", df.get("name", pd.Series())).tolist()
        salaries = df.get("basic_salary", df.get("salary", pd.Series([0] * len(df)))).tolist()

        fig.add_trace(go.Bar(
            x=salaries,
            y=names,
            orientation="h",
            marker=dict(
                color=salaries,
                colorscale="Purples",
                showscale=False,
            ),
            name="Salary",
        ))
    else:
        fig.add_annotation(text="No data", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color="#94a3b8"))

    fig.update_layout(
        title="🏆 Top 5 Earners",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#1e293b",
        font=dict(color="#e2e8f0"),
        xaxis=dict(gridcolor="#334155", title="Salary ($)"),
        yaxis=dict(gridcolor="#334155"),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def create_attendance_heatmap(data):
    """Calendar-style attendance heatmap using Plotly."""
    fig = go.Figure()

    if data:
        df = pd.DataFrame(data)
        if "date" in df.columns and "present_count" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df["week"] = df["date"].dt.isocalendar().week.astype(int)
            df["weekday"] = df["date"].dt.weekday
            df["label"] = df["date"].dt.strftime("%Y-%m-%d")

            fig = go.Figure(data=go.Heatmap(
                x=df["week"].tolist(),
                y=df["weekday"].tolist(),
                z=df["present_count"].tolist(),
                text=df["label"].tolist(),
                colorscale="Purples",
                hoverongaps=False,
            ))

    fig.update_layout(
        title="📅 Attendance Heatmap",
        plot_bgcolor="#0f172a",
        paper_bgcolor="#1e293b",
        font=dict(color="#e2e8f0"),
        yaxis=dict(
            tickvals=[0, 1, 2, 3, 4, 5, 6],
            ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            gridcolor="#334155",
        ),
        xaxis=dict(title="Week of Year", gridcolor="#334155"),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig
