"""Read-only queries on the student database (data/college.db).

Each function runs one fixed, parameterized SQL query and returns plain dicts. They are used by
the Student Info endpoints directly and by the assistant agent as tools.
"""
from typing import Optional

from app.db import connect

conn = connect()

STUDENT_COLUMNS = (
    "student_id, roll_number, name, gender, department, year, semester, section, batch, cgpa, "
    "residence, city"
)
DEPARTMENTS = ["CSE", "ECE", "EEE", "IT", "MECH"]
_GRADE_POINTS = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "U": 0}


class NotFound(Exception):
    pass


def _rows(sql: str, params=()) -> list:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _filters(**values) -> tuple:
    """Build a WHERE clause from the given column=value pairs, skipping None."""
    clauses, params = [], []
    for column, value in values.items():
        if value is None:
            continue
        if isinstance(value, str):
            clauses.append(f"UPPER({column}) = UPPER(?)")
        else:
            clauses.append(f"{column} = ?")
        params.append(value)
    return (" AND ".join(clauses) or "1=1"), params


def resolve_student(identifier: str) -> dict:
    """Find one student by roll number (24CS015) or student ID (STU10615)."""
    key = identifier.strip().upper()
    rows = _rows("SELECT student_id, roll_number, name FROM students WHERE student_id = ? OR roll_number = ?", (key, key))
    if not rows:
        raise NotFound(f"No student with roll number or student ID '{identifier}'.")
    return rows[0]


# ---------- students ----------

def find_student(identifier: Optional[str] = None, name: Optional[str] = None) -> dict:
    if identifier:
        sid = resolve_student(identifier)["student_id"]
        return {"student": _rows("SELECT * FROM students WHERE student_id = ?", (sid,))[0]}
    if name:
        matches = _rows(
            f"SELECT {STUDENT_COLUMNS} FROM students WHERE name LIKE ? ORDER BY roll_number LIMIT 50",
            (f"%{name.strip()}%",),
        )
        return {"matches": len(matches), "students": matches}
    raise ValueError("Give a roll number / student ID or a name.")


def list_students(
    department: Optional[str] = None, year: Optional[int] = None, section: Optional[str] = None,
    gender: Optional[str] = None, residence: Optional[str] = None, admission_type: Optional[str] = None,
    city: Optional[str] = None, min_cgpa: Optional[float] = None, max_cgpa: Optional[float] = None,
    sort_by: str = "roll_number", descending: bool = False, limit: int = 50,
) -> dict:
    where, params = _filters(department=department, year=year, section=section, gender=gender,
                             residence=residence, admission_type=admission_type, city=city)
    if min_cgpa is not None:
        where += " AND cgpa >= ?"
        params.append(min_cgpa)
    if max_cgpa is not None:
        where += " AND cgpa <= ?"
        params.append(max_cgpa)
    sort = sort_by if sort_by in ("roll_number", "name", "cgpa") else "roll_number"
    order = "DESC" if descending else "ASC"
    total = conn.execute(f"SELECT COUNT(*) FROM students WHERE {where}", params).fetchone()[0]
    rows = _rows(
        f"SELECT {STUDENT_COLUMNS} FROM students WHERE {where} "
        f"ORDER BY {sort} IS NULL, {sort} {order} LIMIT ?",
        params + [min(limit, 200)],
    )
    return {"total_matching": total, "returned": len(rows), "students": rows}


# ---------- attendance ----------

def get_attendance(student: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> dict:
    s = resolve_student(student)
    where, params = "student_id = ?", [s["student_id"]]
    if from_date:
        where += " AND date >= ?"
        params.append(from_date)
    if to_date:
        where += " AND date <= ?"
        params.append(to_date)
    summary = _rows(
        f"""SELECT COUNT(*) AS working_days,
                   SUM(status IN ('Present','OD')) AS days_present,
                   SUM(status = 'Absent') AS days_absent,
                   SUM(status = 'OD') AS days_on_duty,
                   ROUND(100.0 * SUM(status IN ('Present','OD')) / COUNT(*), 2) AS attendance_percentage,
                   MIN(date) AS from_date, MAX(date) AS to_date
            FROM attendance WHERE {where}""", params)[0]
    absent = [r["date"] for r in _rows(f"SELECT date FROM attendance WHERE {where} AND status = 'Absent' ORDER BY date", params)]
    on_duty = [r["date"] for r in _rows(f"SELECT date FROM attendance WHERE {where} AND status = 'OD' ORDER BY date", params)]
    pct = summary["attendance_percentage"] or 0
    return {**s, **summary, "shortage_below_75": pct < 75, "absent_dates": absent, "on_duty_dates": on_duty}


def attendance_report(
    department: Optional[str] = None, year: Optional[int] = None, section: Optional[str] = None,
    below_percentage: Optional[float] = None, above_percentage: Optional[float] = None,
    lowest_first: bool = True, limit: int = 50,
) -> dict:
    where, params = _filters(department=department, year=year, section=section)
    if below_percentage is not None:
        where += " AND attendance_percentage < ?"
        params.append(below_percentage)
    if above_percentage is not None:
        where += " AND attendance_percentage >= ?"
        params.append(above_percentage)
    total = conn.execute(f"SELECT COUNT(*) FROM attendance_summary WHERE {where}", params).fetchone()[0]
    order = "ASC" if lowest_first else "DESC"
    rows = _rows(
        f"SELECT * FROM attendance_summary WHERE {where} ORDER BY attendance_percentage {order}, roll_number LIMIT ?",
        params + [min(limit, 200)],
    )
    return {"total_matching": total, "returned": len(rows), "students": rows}


def attendance_on_date(
    date: str, status: str = "Absent", department: Optional[str] = None,
    year: Optional[int] = None, section: Optional[str] = None,
) -> dict:
    where, params = _filters(**{"s.department": department, "s.year": year, "s.section": section})
    rows = _rows(
        f"""SELECT s.roll_number, s.name, s.department, s.year, s.section, a.status
            FROM attendance a JOIN students s USING (student_id)
            WHERE a.date = ? AND a.status = ? AND {where} ORDER BY s.roll_number""",
        [date, status.capitalize() if status.upper() != "OD" else "OD"] + params,
    )
    held = conn.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (date,)).fetchone()[0]
    note = None if held else "No attendance recorded on this date (holiday, weekend or outside the semester)."
    return {"date": date, "status": status, "count": len(rows), "students": rows, "note": note}


# ---------- marks & arrears ----------

def get_marks(student: str, semester: Optional[int] = None) -> dict:
    s = resolve_student(student)
    where, params = "m.student_id = ?", [s["student_id"]]
    if semester is not None:
        where += " AND m.semester = ?"
        params.append(semester)
    rows = _rows(
        f"""SELECT m.semester, m.exam_session, m.subject_code, sub.subject_name, sub.credits,
                   m.internal_marks, m.external_marks, m.total_marks, m.grade, m.result
            FROM marks m JOIN subjects sub USING (subject_code)
            WHERE {where} ORDER BY m.semester, m.subject_code""", params)

    semesters = {}
    for r in rows:
        sem = semesters.setdefault(r["semester"], {"semester": r["semester"], "subjects": 0, "passed": 0, "failed": 0, "_pts": 0, "_cr": 0})
        sem["subjects"] += 1
        if r["result"] == "PASS":
            sem["passed"] += 1
            sem["_pts"] += _GRADE_POINTS[r["grade"]] * r["credits"]
            sem["_cr"] += r["credits"]
        else:
            sem["failed"] += 1
    summary = []
    for sem in semesters.values():
        sem["gpa_passed_subjects"] = round(sem.pop("_pts") / sem.pop("_cr"), 2) if sem["_cr"] else None
        summary.append(sem)
    cgpa = conn.execute("SELECT cgpa FROM students WHERE student_id = ?", (s["student_id"],)).fetchone()[0]
    note = None if rows else "No exam results yet (first-year students have not written semester exams)."
    return {**s, "cgpa": cgpa, "semester_summary": summary, "marks": rows, "note": note}


def get_arrears(student: str, status: Optional[str] = None) -> dict:
    s = resolve_student(student)
    where, params = "a.student_id = ?", [s["student_id"]]
    if status:
        where += " AND UPPER(a.status) = UPPER(?)"
        params.append(status)
    rows = _rows(
        f"""SELECT a.subject_code, sub.subject_name, a.semester, a.attempts, a.status, a.cleared_session
            FROM arrears a JOIN subjects sub USING (subject_code)
            WHERE {where} ORDER BY a.status DESC, a.semester""", params)
    pending = sum(r["status"] == "Pending" for r in rows)
    return {**s, "pending_count": pending, "cleared_count": len(rows) - pending, "arrears": rows}


def arrears_report(
    department: Optional[str] = None, year: Optional[int] = None, section: Optional[str] = None,
    status: str = "Pending", min_count: int = 1, limit: int = 50,
) -> dict:
    where, params = _filters(**{"s.department": department, "s.year": year, "s.section": section})
    rows = _rows(
        f"""SELECT s.roll_number, s.name, s.department, s.year, s.section, s.cgpa, COUNT(*) AS arrear_count
            FROM arrears a JOIN students s USING (student_id)
            WHERE UPPER(a.status) = UPPER(?) AND {where}
            GROUP BY s.student_id HAVING COUNT(*) >= ?
            ORDER BY arrear_count DESC, s.roll_number""",
        [status] + params + [min_count])
    return {"status": status, "total_matching": len(rows), "returned": min(len(rows), limit), "students": rows[:limit]}


def subject_performance(
    subject: str, department: Optional[str] = None, year: Optional[int] = None, top: int = 5,
) -> dict:
    """Results of one subject, by code (CS302) or name (Data Structures)."""
    subjects = _rows(
        "SELECT * FROM subjects WHERE UPPER(subject_code) = UPPER(?) OR subject_name LIKE ?",
        (subject.strip(), f"%{subject.strip()}%"))
    if department:
        subjects = [s for s in subjects if s["department"] in (department.upper(), "ALL")]
    if not subjects:
        raise NotFound(f"No subject matching '{subject}'.")
    results = []
    for sub in subjects[:5]:
        where, params = _filters(**{"s.department": department, "s.year": year})
        base = f"FROM marks m JOIN students s USING (student_id) WHERE m.subject_code = ? AND {where}"
        p = [sub["subject_code"]] + params
        stats = _rows(
            f"""SELECT COUNT(*) AS students, SUM(m.result = 'PASS') AS passed, SUM(m.result = 'FAIL') AS failed,
                       ROUND(100.0 * SUM(m.result = 'PASS') / COUNT(*), 2) AS pass_percentage,
                       ROUND(AVG(m.total_marks), 2) AS average_marks, MAX(m.total_marks) AS highest_marks
                {base}""", p)[0]
        toppers = _rows(f"SELECT s.roll_number, s.name, s.department, m.total_marks, m.grade {base} "
                        "ORDER BY m.total_marks DESC LIMIT ?", p + [top])
        grades = _rows(f"SELECT m.grade, COUNT(*) AS count {base} GROUP BY m.grade ORDER BY count DESC", p)
        if not stats["students"]:
            results.append({**sub, "students": 0, "note": "No students matching these filters have taken "
                            "this subject's exam yet (check the department/year filters)."})
            continue
        results.append({**sub, **stats, "grade_distribution": grades, "toppers": toppers})
    return {"subjects": results}


def list_subjects(department: Optional[str] = None, semester: Optional[int] = None) -> dict:
    where, params = "1=1", []
    if department:
        where += " AND department IN (UPPER(?), 'ALL')"
        params.append(department)
    if semester is not None:
        where += " AND semester = ?"
        params.append(semester)
    rows = _rows(f"SELECT * FROM subjects WHERE {where} ORDER BY semester, subject_code", params)
    return {"count": len(rows), "subjects": rows}


_GROUPINGS = {
    "department": "s.department",
    "year": "s.year",
    "department_year": "s.department, s.year",
    "section": "s.department, s.year, s.section",
}


def class_summary(
    department: Optional[str] = None, year: Optional[int] = None, section: Optional[str] = None,
    group_by: str = "department_year",
) -> dict:
    """Totals per group (department, year, department+year or section): strength, CGPA, attendance,
    shortage and arrears. Totals are computed here so the model never has to add numbers up."""
    where, params = _filters(**{"s.department": department, "s.year": year, "s.section": section})
    group = _GROUPINGS.get(group_by, _GROUPINGS["department_year"])
    rows = _rows(
        f"""SELECT {group},
                   COUNT(*) AS students,
                   SUM(s.gender = 'Male') AS male, SUM(s.gender = 'Female') AS female,
                   SUM(s.residence = 'Hosteller') AS hostellers,
                   ROUND(AVG(s.cgpa), 2) AS average_cgpa,
                   ROUND(AVG(att.attendance_percentage), 2) AS average_attendance,
                   SUM(att.attendance_percentage < 75) AS attendance_shortage,
                   SUM(EXISTS (SELECT 1 FROM arrears a WHERE a.student_id = s.student_id AND a.status = 'Pending'))
                       AS students_with_pending_arrears
            FROM students s JOIN attendance_summary att USING (student_id)
            WHERE {where}
            GROUP BY {group}
            ORDER BY {group}""", params)
    return {"group_by": group_by, "groups": rows}


def student_card(student_id: str) -> dict:
    """Headline numbers for the app's student card."""
    return _rows(
        """SELECT s.student_id, s.roll_number, s.name, s.department, s.year, s.section, s.cgpa, s.email,
                  att.attendance_percentage,
                  (SELECT COUNT(*) FROM arrears a WHERE a.student_id = s.student_id AND a.status = 'Pending')
                      AS pending_arrears
           FROM students s LEFT JOIN attendance_summary att USING (student_id)
           WHERE s.student_id = ?""", (student_id,))[0]


def data_range() -> dict:
    row = conn.execute("SELECT MIN(date), MAX(date) FROM attendance").fetchone()
    return {"attendance_from": row[0], "attendance_to": row[1]}
