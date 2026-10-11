"""SQLite database with student data: students, subjects, attendance, marks and arrears."""
import sqlite3
from pathlib import Path

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id      TEXT PRIMARY KEY,          -- e.g. STU10001
    roll_number     TEXT UNIQUE NOT NULL,      -- e.g. 24CS015 (batch year + dept + number)
    name            TEXT NOT NULL,
    gender          TEXT NOT NULL,
    date_of_birth   TEXT NOT NULL,
    department      TEXT NOT NULL,             -- CSE, ECE, EEE, IT, MECH
    year            INTEGER NOT NULL,          -- 1 to 4
    semester        INTEGER NOT NULL,          -- current semester
    section         TEXT NOT NULL,             -- A or B
    batch           TEXT NOT NULL,             -- e.g. 2024-2028
    email           TEXT NOT NULL,
    phone           TEXT NOT NULL,
    parent_name     TEXT NOT NULL,
    parent_phone    TEXT NOT NULL,
    address         TEXT NOT NULL,
    city            TEXT NOT NULL,
    blood_group     TEXT NOT NULL,
    admission_type  TEXT NOT NULL,             -- Counselling or Management
    residence       TEXT NOT NULL,             -- Hosteller or Day Scholar
    cgpa            REAL                       -- NULL for first-years (no results yet)
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_code    TEXT PRIMARY KEY,
    subject_name    TEXT NOT NULL,
    department      TEXT NOT NULL,             -- ALL for common first-year subjects
    semester        INTEGER NOT NULL,
    credits         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT NOT NULL REFERENCES students(student_id),
    date            TEXT NOT NULL,             -- YYYY-MM-DD
    status          TEXT NOT NULL,             -- Present, Absent, OD (on duty)
    UNIQUE (student_id, date)
);

CREATE TABLE IF NOT EXISTS marks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT NOT NULL REFERENCES students(student_id),
    subject_code    TEXT NOT NULL REFERENCES subjects(subject_code),
    semester        INTEGER NOT NULL,
    exam_session    TEXT NOT NULL,             -- e.g. Nov/Dec 2025
    internal_marks  INTEGER NOT NULL,          -- out of 40
    external_marks  INTEGER NOT NULL,          -- out of 60
    total_marks     INTEGER NOT NULL,          -- out of 100
    grade           TEXT NOT NULL,             -- O, A+, A, B+, B, C, U (fail)
    result          TEXT NOT NULL              -- PASS or FAIL
);

CREATE TABLE IF NOT EXISTS arrears (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT NOT NULL REFERENCES students(student_id),
    subject_code    TEXT NOT NULL REFERENCES subjects(subject_code),
    semester        INTEGER NOT NULL,
    attempts        INTEGER NOT NULL,          -- exams written so far for this subject
    status          TEXT NOT NULL,             -- Pending or Cleared
    cleared_session TEXT                       -- exam session it was cleared in
);

CREATE INDEX IF NOT EXISTS idx_students_dept_year ON students(department, year);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id);
CREATE INDEX IF NOT EXISTS idx_arrears_student ON arrears(student_id);

-- Attendance % per student for the current semester (OD counts as present).
CREATE VIEW IF NOT EXISTS attendance_summary AS
SELECT
    s.student_id, s.roll_number, s.name, s.department, s.year, s.section,
    COUNT(a.id)                                         AS working_days,
    SUM(a.status IN ('Present', 'OD'))                  AS days_present,
    SUM(a.status = 'Absent')                            AS days_absent,
    SUM(a.status = 'OD')                                AS days_on_duty,
    ROUND(100.0 * SUM(a.status IN ('Present', 'OD')) / COUNT(a.id), 2) AS attendance_percentage
FROM students s
JOIN attendance a ON a.student_id = s.student_id
GROUP BY s.student_id;
"""


def connect(path: str = settings.database_path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection):
    conn.executescript(SCHEMA)
