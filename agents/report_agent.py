"""
report_agent.py - Report Generation Agent for PayrollPro AI
Generates PDF and Excel payroll reports using ReportLab and openpyxl.
"""
from datetime import date
from io import BytesIO


class ReportAgent:
    """Generates downloadable payroll, attendance, and employee reports."""

    # ── PAYROLL PDF ───────────────────────────────────────────────────

    def generate_payroll_pdf(self, month: int, year: int, records: list) -> bytes:
        """Generate a payroll PDF report and return bytes."""
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        except ImportError:
            raise RuntimeError("reportlab is not installed. Run: pip install reportlab")

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                                 leftMargin=1.5*cm, rightMargin=1.5*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", parent=styles["Title"],
                                      fontSize=16, spaceAfter=6, textColor=colors.HexColor("#1e293b"))
        sub_style = ParagraphStyle("sub", parent=styles["Normal"],
                                    fontSize=10, spaceAfter=12, textColor=colors.HexColor("#475569"))

        month_name = date(year, month, 1).strftime("%B %Y")
        story = [
            Paragraph("PayrollPro AI — Payroll Report", title_style),
            Paragraph(f"Month: {month_name} | Generated: {date.today().isoformat()}", sub_style),
            Spacer(1, 0.3*cm),
        ]

        if records:
            headers = ["Emp ID", "Name", "Department", "Basic", "Gross", "Deductions", "Net Salary", "Status"]
            data = [headers]
            for r in records:
                data.append([
                    r.get("emp_code", r.get("employee_id", "")),
                    r.get("full_name", ""),
                    r.get("department", ""),
                    f"${r.get('basic_salary', 0):,.2f}",
                    f"${r.get('gross_salary', 0):,.2f}",
                    f"${r.get('total_deductions', 0):,.2f}",
                    f"${r.get('net_salary', 0):,.2f}",
                    r.get("status", ""),
                ])
            # Totals row
            total_net = sum(r.get("net_salary", 0) for r in records)
            total_gross = sum(r.get("gross_salary", 0) for r in records)
            data.append(["", "TOTAL", "", "", f"${total_gross:,.2f}", "", f"${total_net:,.2f}", ""])

            col_widths = [2.5*cm, 5*cm, 4*cm, 3*cm, 3*cm, 3.5*cm, 3.5*cm, 2.5*cm]
            tbl = Table(data, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (1, 1), (1, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWHEIGHT", (0, 0), (-1, -1), 18),
            ]))
            story.append(tbl)
        else:
            story.append(Paragraph("No payroll records found for this month.", styles["Normal"]))

        doc.build(story)
        return buf.getvalue()

    # ── ATTENDANCE EXCEL ──────────────────────────────────────────────

    def generate_attendance_excel(self, records: list, month: int, year: int) -> bytes:
        """Generate an attendance report Excel file."""
        import pandas as pd
        df = pd.DataFrame(records) if records else pd.DataFrame()
        buf = BytesIO()
        df.to_excel(buf, index=False, engine="openpyxl",
                    sheet_name=f"Attendance_{date(year, month, 1).strftime('%b%Y')}")
        return buf.getvalue()

    # ── EMPLOYEE CSV ──────────────────────────────────────────────────

    def generate_employee_csv(self, records: list) -> bytes:
        """Generate employee CSV."""
        import pandas as pd
        df = pd.DataFrame(records) if records else pd.DataFrame()
        for col in ["password_hash", "password"]:
            if col in df.columns:
                df = df.drop(columns=[col])
        return df.to_csv(index=False).encode("utf-8")
