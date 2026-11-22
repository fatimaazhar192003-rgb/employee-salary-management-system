"""
database.py - Complete DatabaseManager for PayrollPro AI
SQLite-backed persistence layer covering all application entities.
"""
import sqlite3
import os
from datetime import date, datetime
from contextlib import contextmanager
from config import DB_PATH, DEFAULT_COMPANY, DEFAULT_SALARY_COMPONENTS
from utils.security import hash_password


class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _fetchall(self, sql, params=()):
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def _fetchone(self, sql, params=()):
        with self._conn() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def _execute(self, sql, params=()):
        with self._conn() as conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid

    # ─────────────────────────── SCHEMA ──────────────────────────────

    def initialize_database(self):
        """Create all tables and seed initial data."""
        ddl = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'hr',
            full_name TEXT,
            email TEXT,
            is_active INTEGER DEFAULT 1,
            force_password_change INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            manager_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            department_id INTEGER REFERENCES departments(id),
            designation TEXT,
            joining_date TEXT,
            employment_status TEXT DEFAULT 'Full-time',
            basic_salary REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL REFERENCES employees(id),
            date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'present',
            check_in TEXT,
            check_out TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(employee_id, date)
        );

        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL REFERENCES employees(id),
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days INTEGER DEFAULT 1,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            approved_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS salary_structures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL REFERENCES employees(id),
            basic_salary REAL DEFAULT 0,
            hra_percent REAL DEFAULT 40,
            medical_percent REAL DEFAULT 10,
            transport_percent REAL DEFAULT 5,
            pf_percent REAL DEFAULT 12,
            tax_percent REAL DEFAULT 10,
            other_deduction_percent REAL DEFAULT 0,
            bonus REAL DEFAULT 0,
            effective_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL REFERENCES employees(id),
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            basic_salary REAL DEFAULT 0,
            hra REAL DEFAULT 0,
            medical REAL DEFAULT 0,
            transport REAL DEFAULT 0,
            bonus REAL DEFAULT 0,
            overtime REAL DEFAULT 0,
            gross_salary REAL DEFAULT 0,
            pf REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            other_deductions REAL DEFAULT 0,
            total_deductions REAL DEFAULT 0,
            net_salary REAL DEFAULT 0,
            working_days INTEGER DEFAULT 26,
            present_days INTEGER DEFAULT 26,
            status TEXT DEFAULT 'draft',
            processed_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(employee_id, month, year)
        );

        CREATE TABLE IF NOT EXISTS company_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS ai_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            user_query TEXT,
            agent_used TEXT,
            task_type TEXT,
            status TEXT DEFAULT 'success',
            result TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self._conn() as conn:
            conn.executescript(ddl)

        self._seed_defaults()

    def _seed_defaults(self):
        """Seed admin user, default departments, company settings."""
        # Admin user
        if not self._fetchone("SELECT id FROM users WHERE username=?", ("admin",)):
            self._execute(
                "INSERT INTO users (username,password_hash,role,full_name,email,force_password_change) VALUES (?,?,?,?,?,?)",
                ("admin", hash_password("admin123"), "admin", "System Administrator", "admin@payrollpro.com", 0),
            )

        # Default departments
        for dept in ["Engineering", "Human Resources", "Finance", "Marketing", "Operations"]:
            if not self._fetchone("SELECT id FROM departments WHERE name=?", (dept,)):
                self._execute("INSERT INTO departments (name) VALUES (?)", (dept,))

        # Company settings
        for key, val in DEFAULT_COMPANY.items():
            if not self._fetchone("SELECT id FROM company_settings WHERE key=?", (key,)):
                self._execute("INSERT INTO company_settings (key,value) VALUES (?,?)", (key, str(val)))

        for key, val in DEFAULT_SALARY_COMPONENTS.items():
            if not self._fetchone("SELECT id FROM company_settings WHERE key=?", (key,)):
                self._execute("INSERT INTO company_settings (key,value) VALUES (?,?)", (key, str(val)))

    # ─────────────────────────── USERS ───────────────────────────────

    def get_user(self, username: str):
        return self._fetchone("SELECT * FROM users WHERE username=? AND is_active=1", (username,))

    def get_all_users(self):
        return self._fetchall("SELECT id,username,full_name,email,role,is_active,last_login FROM users ORDER BY id")

    def create_user(self, username, password_hash, role, full_name, email, force_password_change=True):
        self._execute(
            "INSERT INTO users (username,password_hash,role,full_name,email,force_password_change) VALUES (?,?,?,?,?,?)",
            (username, password_hash, role, full_name, email, int(force_password_change)),
        )

    def update_last_login(self, username: str):
        self._execute("UPDATE users SET last_login=? WHERE username=?", (datetime.now().isoformat(), username))

    def update_password(self, username: str, password_hash: str, force_change: bool = False):
        self._execute(
            "UPDATE users SET password_hash=?,force_password_change=? WHERE username=?",
            (password_hash, int(force_change), username),
        )

    # ─────────────────────────── DEPARTMENTS ─────────────────────────

    def get_all_departments(self):
        return self._fetchall(
            "SELECT d.*, e.full_name AS manager_name FROM departments d "
            "LEFT JOIN employees e ON e.id=d.manager_id ORDER BY d.name"
        )

    def add_department(self, name: str, description: str = ""):
        self._execute("INSERT INTO departments (name,description) VALUES (?,?)", (name, description))

    def update_department(self, dept_id: int, name: str, description: str = ""):
        self._execute("UPDATE departments SET name=?,description=? WHERE id=?", (name, description, dept_id))

    def get_department(self, dept_id: int):
        return self._fetchone("SELECT * FROM departments WHERE id=?", (dept_id,))

    # ─────────────────────────── EMPLOYEES ───────────────────────────

    def get_all_employees(self, status=None, department_id=None):
        sql = """
            SELECT e.*, d.name AS department_name
            FROM employees e
            LEFT JOIN departments d ON d.id=e.department_id
            WHERE 1=1
        """
        params = []
        if status:
            sql += " AND e.employment_status=?"
            params.append(status)
        if department_id:
            sql += " AND e.department_id=?"
            params.append(department_id)
        sql += " ORDER BY e.full_name"
        return self._fetchall(sql, params)

    def get_employee(self, emp_id: int):
        return self._fetchone(
            "SELECT e.*,d.name AS department_name FROM employees e "
            "LEFT JOIN departments d ON d.id=e.department_id WHERE e.id=?",
            (emp_id,),
        )

    def add_employee(self, employee_id, full_name, email, phone, address,
                     department_id, designation, joining_date, employment_status, basic_salary):
        return self._execute(
            """INSERT INTO employees
               (employee_id,full_name,email,phone,address,department_id,designation,
                joining_date,employment_status,basic_salary)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (employee_id, full_name, email, phone, address, department_id,
             designation, joining_date, employment_status, basic_salary),
        )

    def update_employee(self, emp_id, full_name, email, phone, address,
                        department_id, designation, employment_status, basic_salary, is_active):
        self._execute(
            """UPDATE employees SET full_name=?,email=?,phone=?,address=?,department_id=?,
               designation=?,employment_status=?,basic_salary=?,is_active=?,updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (full_name, email, phone, address, department_id, designation,
             employment_status, basic_salary, int(is_active), emp_id),
        )

    def delete_employee(self, emp_id: int):
        self._execute("UPDATE employees SET is_active=0 WHERE id=?", (emp_id,))

    def get_next_employee_sequence(self):
        row = self._fetchone("SELECT MAX(CAST(SUBSTR(employee_id,5) AS INTEGER)) AS mx FROM employees WHERE employee_id LIKE 'EMP-%'")
        return (row["mx"] or 0) + 1 if row else 1

    # ─────────────────────────── ATTENDANCE ──────────────────────────

    def mark_attendance(self, employee_id, att_date, status, check_in=None, check_out=None, notes=None):
        self._execute(
            """INSERT INTO attendance (employee_id,date,status,check_in,check_out,notes)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(employee_id,date) DO UPDATE SET
               status=excluded.status, check_in=excluded.check_in,
               check_out=excluded.check_out, notes=excluded.notes""",
            (employee_id, att_date, status, check_in, check_out, notes),
        )

    def get_attendance_record(self, employee_id, att_date):
        return self._fetchone("SELECT * FROM attendance WHERE employee_id=? AND date=?", (employee_id, att_date))

    def get_attendance_history(self, employee_id=None, month=None, year=None):
        sql = """
            SELECT a.*, e.full_name AS employee_name, e.employee_id AS emp_code
            FROM attendance a
            JOIN employees e ON e.id=a.employee_id
            WHERE 1=1
        """
        params = []
        if employee_id:
            sql += " AND a.employee_id=?"
            params.append(employee_id)
        if month and year:
            sql += " AND strftime('%m',a.date)=? AND strftime('%Y',a.date)=?"
            params += [f"{month:02d}", str(year)]
        sql += " ORDER BY a.date DESC"
        return self._fetchall(sql, params)

    def get_attendance_heatmap_data(self, start_date, end_date):
        return self._fetchall(
            """SELECT date, COUNT(*) AS total,
               SUM(CASE WHEN status IN ('present','late','half_day') THEN 1 ELSE 0 END) AS present_count
               FROM attendance WHERE date BETWEEN ? AND ?
               GROUP BY date ORDER BY date""",
            (start_date, end_date),
        )

    # ─────────────────────────── LEAVES ──────────────────────────────

    def apply_leave(self, employee_id, leave_type, start_date, end_date, days, reason):
        self._execute(
            "INSERT INTO leaves (employee_id,leave_type,start_date,end_date,days,reason) VALUES (?,?,?,?,?,?)",
            (employee_id, leave_type, start_date, end_date, days, reason),
        )

    def get_leaves_by_status(self, status: str):
        return self._fetchall(
            "SELECT l.*,e.full_name AS employee_name FROM leaves l "
            "JOIN employees e ON e.id=l.employee_id WHERE l.status=? ORDER BY l.created_at DESC",
            (status,),
        )

    def get_all_leaves(self, employee_id=None):
        if employee_id:
            return self._fetchall(
                "SELECT l.*,e.full_name AS employee_name FROM leaves l "
                "JOIN employees e ON e.id=l.employee_id WHERE l.employee_id=? ORDER BY l.created_at DESC",
                (employee_id,),
            )
        return self._fetchall(
            "SELECT l.*,e.full_name AS employee_name FROM leaves l "
            "JOIN employees e ON e.id=l.employee_id ORDER BY l.created_at DESC"
        )

    def update_leave_status(self, leave_id, status, approved_by=None):
        self._execute(
            "UPDATE leaves SET status=?,approved_by=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, approved_by, leave_id),
        )

    # ─────────────────────────── SALARY STRUCTURE ────────────────────

    def get_salary_structure(self, employee_id: int):
        return self._fetchone(
            "SELECT * FROM salary_structures WHERE employee_id=? ORDER BY created_at DESC LIMIT 1",
            (employee_id,),
        )

    def save_salary_structure(self, employee_id, basic_salary, hra_percent, medical_percent,
                               transport_percent, pf_percent, tax_percent, other_deduction_percent,
                               bonus=0, effective_date=None):
        effective_date = effective_date or date.today().isoformat()
        self._execute(
            """INSERT INTO salary_structures
               (employee_id,basic_salary,hra_percent,medical_percent,transport_percent,
                pf_percent,tax_percent,other_deduction_percent,bonus,effective_date)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (employee_id, basic_salary, hra_percent, medical_percent, transport_percent,
             pf_percent, tax_percent, other_deduction_percent, bonus, effective_date),
        )

    def get_all_salary_structures(self):
        return self._fetchall(
            "SELECT ss.*,e.full_name,e.employee_id AS emp_code FROM salary_structures ss "
            "JOIN employees e ON e.id=ss.employee_id ORDER BY ss.created_at DESC"
        )

    # ─────────────────────────── PAYROLL ─────────────────────────────

    def get_payroll_by_month(self, month: int, year: int):
        return self._fetchall(
            "SELECT p.*,e.full_name,e.employee_id AS emp_code,d.name AS department "
            "FROM payroll p JOIN employees e ON e.id=p.employee_id "
            "LEFT JOIN departments d ON d.id=e.department_id "
            "WHERE p.month=? AND p.year=? ORDER BY e.full_name",
            (month, year),
        )

    def save_payroll(self, employee_id, month, year, basic_salary, hra, medical, transport,
                     bonus, overtime, gross_salary, pf, tax, other_deductions,
                     total_deductions, net_salary, working_days, present_days, processed_by=None):
        self._execute(
            """INSERT INTO payroll
               (employee_id,month,year,basic_salary,hra,medical,transport,bonus,overtime,
                gross_salary,pf,tax,other_deductions,total_deductions,net_salary,
                working_days,present_days,status,processed_by)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'processed',?)
               ON CONFLICT(employee_id,month,year) DO UPDATE SET
               basic_salary=excluded.basic_salary,hra=excluded.hra,medical=excluded.medical,
               transport=excluded.transport,bonus=excluded.bonus,overtime=excluded.overtime,
               gross_salary=excluded.gross_salary,pf=excluded.pf,tax=excluded.tax,
               other_deductions=excluded.other_deductions,total_deductions=excluded.total_deductions,
               net_salary=excluded.net_salary,working_days=excluded.working_days,
               present_days=excluded.present_days,status='processed',processed_by=excluded.processed_by""",
            (employee_id, month, year, basic_salary, hra, medical, transport, bonus, overtime,
             gross_salary, pf, tax, other_deductions, total_deductions, net_salary,
             working_days, present_days, processed_by),
        )

    def get_payroll_record(self, employee_id, month, year):
        return self._fetchone(
            "SELECT * FROM payroll WHERE employee_id=? AND month=? AND year=?",
            (employee_id, month, year),
        )

    # ─────────────────────────── ANALYTICS ───────────────────────────

    def get_dashboard_stats(self):
        today = date.today().isoformat()
        total = self._fetchone("SELECT COUNT(*) AS c FROM employees WHERE is_active=1")
        present = self._fetchone(
            "SELECT COUNT(*) AS c FROM attendance WHERE date=? AND status IN ('present','late','half_day')", (today,)
        )
        absent = self._fetchone(
            "SELECT COUNT(*) AS c FROM attendance WHERE date=? AND status='absent'", (today,)
        )
        pending_leaves = self._fetchone("SELECT COUNT(*) AS c FROM leaves WHERE status='pending'")
        avg_sal = self._fetchone("SELECT AVG(basic_salary) AS v FROM employees WHERE is_active=1")
        this_month = self._fetchone(
            "SELECT SUM(net_salary) AS v FROM payroll WHERE month=? AND year=?",
            (date.today().month, date.today().year),
        )
        return {
            "total_employees": total["c"] if total else 0,
            "active_employees": total["c"] if total else 0,
            "present_today": present["c"] if present else 0,
            "absent_today": absent["c"] if absent else 0,
            "pending_leaves": pending_leaves["c"] if pending_leaves else 0,
            "avg_salary": round(avg_sal["v"] or 0, 2) if avg_sal else 0,
            "total_payroll_month": round(this_month["v"] or 0, 2) if this_month else 0,
            "pending_payroll": 0,
        }

    def get_payroll_trends(self, start_date, end_date):
        return self._fetchall(
            """SELECT year||'-'||printf('%02d',month) AS month_label,
               SUM(net_salary) AS total_net, COUNT(*) AS headcount
               FROM payroll WHERE created_at BETWEEN ? AND ?
               GROUP BY year,month ORDER BY year,month""",
            (start_date, end_date),
        )

    def get_monthly_payroll_trend(self):
        return self._fetchall(
            """SELECT year||'-'||printf('%02d',month) AS month,
               SUM(net_salary) AS total FROM payroll
               GROUP BY year,month ORDER BY year,month LIMIT 12"""
        )

    def get_department_expenses(self, start_date, end_date):
        return self._fetchall(
            """SELECT d.name AS department, SUM(p.net_salary) AS total_expense,
               COUNT(DISTINCT p.employee_id) AS headcount
               FROM payroll p JOIN employees e ON e.id=p.employee_id
               JOIN departments d ON d.id=e.department_id
               WHERE p.created_at BETWEEN ? AND ?
               GROUP BY d.name ORDER BY total_expense DESC""",
            (start_date, end_date),
        )

    def get_department_salary_expenses(self):
        return self._fetchall(
            """SELECT d.name AS department, SUM(e.basic_salary) AS total_salary,
               COUNT(e.id) AS headcount
               FROM employees e JOIN departments d ON d.id=e.department_id
               WHERE e.is_active=1 GROUP BY d.name ORDER BY total_salary DESC"""
        )

    def get_salary_distribution(self):
        return self._fetchall("SELECT basic_salary FROM employees WHERE is_active=1 ORDER BY basic_salary")

    def get_top_earners(self, limit=5):
        return self._fetchall(
            "SELECT full_name,basic_salary FROM employees WHERE is_active=1 ORDER BY basic_salary DESC LIMIT ?",
            (limit,),
        )

    # ─────────────────────────── SETTINGS ────────────────────────────

    def get_company_settings(self):
        rows = self._fetchall("SELECT key,value FROM company_settings")
        return {r["key"]: r["value"] for r in rows}

    def save_company_settings(self, settings: dict):
        for key, val in settings.items():
            self._execute(
                "INSERT INTO company_settings (key,value) VALUES (?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(val)),
            )

    def get_salary_defaults(self):
        keys = list(DEFAULT_SALARY_COMPONENTS.keys())
        rows = self._fetchall(
            f"SELECT key,value FROM company_settings WHERE key IN ({','.join('?'*len(keys))})", keys
        )
        result = {}
        for r in rows:
            try:
                result[r["key"]] = float(r["value"])
            except (ValueError, TypeError):
                result[r["key"]] = r["value"]
        return result

    def save_salary_defaults(self, defaults: dict):
        self.save_company_settings(defaults)

    # ─────────────────────────── AI LOGS ─────────────────────────────

    def log_ai_execution(self, username, user_query, agent_used, task_type, status="success", result=None):
        self._execute(
            "INSERT INTO ai_logs (username,user_query,agent_used,task_type,status,result) VALUES (?,?,?,?,?,?)",
            (username, user_query, agent_used, task_type, status, str(result) if result else None),
        )

    def get_ai_logs(self, limit=100):
        return self._fetchall(
            "SELECT * FROM ai_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
