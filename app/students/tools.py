"""Tool definitions the assistant agent can call. Each maps to one query in queries.py."""
from app.students import queries as q

_DEPT = {"type": "string", "enum": q.DEPARTMENTS, "description": "Department"}
_YEAR = {"type": "integer", "minimum": 1, "maximum": 4, "description": "Year of study, 1 to 4"}
_SECTION = {"type": "string", "enum": ["A", "B"], "description": "Section"}
_STUDENT = {"type": "string", "description": "Roll number (e.g. 24CS015) or student ID (e.g. STU10615)"}
_LIMIT = {"type": "integer", "description": "Maximum rows to return (default 50)"}


def _tool(name, description, properties, required=()):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": list(required)},
        },
    }


TOOLS = [
    _tool("find_student",
          "Get one student's full profile (contact, parent, address, blood group, CGPA...) by roll number "
          "or student ID, or search students by (part of) their name.",
          {"identifier": _STUDENT, "name": {"type": "string", "description": "Full or partial student name"}}),
    _tool("list_students",
          "List students filtered by department, year, section, gender, hostel/day scholar, admission type, "
          "city or CGPA range. Sort by cgpa for toppers or lowest performers.",
          {"department": _DEPT, "year": _YEAR, "section": _SECTION,
           "gender": {"type": "string", "enum": ["Male", "Female"]},
           "residence": {"type": "string", "enum": ["Hosteller", "Day Scholar"]},
           "admission_type": {"type": "string", "enum": ["Counselling", "Management"]},
           "city": {"type": "string"},
           "min_cgpa": {"type": "number"}, "max_cgpa": {"type": "number"},
           "sort_by": {"type": "string", "enum": ["roll_number", "name", "cgpa"]},
           "descending": {"type": "boolean", "description": "true for highest first"},
           "limit": _LIMIT}),
    _tool("get_attendance",
          "One student's attendance for the current semester: working days, present, absent, OD, percentage, "
          "shortage (<75%) and the dates absent. Optional date range (YYYY-MM-DD).",
          {"student": _STUDENT, "from_date": {"type": "string"}, "to_date": {"type": "string"}},
          ["student"]),
    _tool("attendance_report",
          "Attendance percentages for many students, e.g. a class list or everyone below 75% (shortage). "
          "Filter by department/year/section and a percentage threshold.",
          {"department": _DEPT, "year": _YEAR, "section": _SECTION,
           "below_percentage": {"type": "number", "description": "Only students below this %, e.g. 75"},
           "above_percentage": {"type": "number", "description": "Only students at or above this %"},
           "lowest_first": {"type": "boolean", "description": "Sort lowest attendance first (default true)"},
           "limit": _LIMIT}),
    _tool("attendance_on_date",
          "Who was Absent / Present / on OD on a specific date (YYYY-MM-DD), optionally for one class.",
          {"date": {"type": "string"}, "status": {"type": "string", "enum": ["Absent", "Present", "OD"]},
           "department": _DEPT, "year": _YEAR, "section": _SECTION},
          ["date"]),
    _tool("get_marks",
          "One student's exam marks (internal /40, external /60, total, grade, pass/fail) per subject, with a "
          "per-semester summary and CGPA. Optionally for one semester.",
          {"student": _STUDENT, "semester": {"type": "integer", "minimum": 1, "maximum": 8}},
          ["student"]),
    _tool("get_arrears",
          "One student's arrears (failed subjects): pending and cleared, attempts, session cleared.",
          {"student": _STUDENT, "status": {"type": "string", "enum": ["Pending", "Cleared"]}},
          ["student"]),
    _tool("arrears_report",
          "Students who have arrears, with their arrear count, filtered by department/year/section. "
          "Use min_count for e.g. 'more than 3 arrears'.",
          {"department": _DEPT, "year": _YEAR, "section": _SECTION,
           "status": {"type": "string", "enum": ["Pending", "Cleared"], "description": "Default Pending"},
           "min_count": {"type": "integer", "description": "Minimum arrears per student (default 1)"},
           "limit": _LIMIT}),
    _tool("subject_performance",
          "Results of a subject (by code like CS302 or name like 'Data Structures'): pass %, failures, "
          "average and highest marks, grade distribution and toppers. Searches all departments and batches "
          "at once; only add department/year filters if the user asks for them.",
          {"subject": {"type": "string"}, "department": _DEPT,
           "year": {**_YEAR, "description": "Students' CURRENT year of study (not the year the subject is "
                                            "taught). Usually leave empty."},
           "top": {"type": "integer", "description": "Number of toppers to list (default 5)"}},
          ["subject"]),
    _tool("list_subjects",
          "Subjects (code, name, credits) offered by a department in a semester.",
          {"department": _DEPT, "semester": {"type": "integer", "minimum": 1, "maximum": 8}}),
    _tool("class_summary",
          "Overview per department/year/section: number of students, gender split, hostellers, average CGPA, "
          "average attendance, attendance shortage count and students with pending arrears. Good for comparisons: "
          "leave department empty to get every department in ONE call.",
          {"department": _DEPT, "year": _YEAR, "section": _SECTION,
           "group_by": {"type": "string", "enum": ["department", "year", "department_year", "section"],
                        "description": "Level of the totals: per department, per year, per department+year "
                                       "(default) or per individual section"}}),
]

FUNCTIONS = {
    "find_student": q.find_student,
    "list_students": q.list_students,
    "get_attendance": q.get_attendance,
    "attendance_report": q.attendance_report,
    "attendance_on_date": q.attendance_on_date,
    "get_marks": q.get_marks,
    "get_arrears": q.get_arrears,
    "arrears_report": q.arrears_report,
    "subject_performance": q.subject_performance,
    "list_subjects": q.list_subjects,
    "class_summary": q.class_summary,
}


def run_tool(name: str, arguments: dict) -> dict:
    """Run a tool and always return a dict (errors become {"error": ...} for the model to read)."""
    func = FUNCTIONS.get(name)
    if func is None:
        return {"error": f"Unknown tool {name}"}
    try:
        return func(**arguments)
    except q.NotFound as e:
        return {"error": str(e)}
    except (TypeError, ValueError) as e:
        return {"error": f"Bad arguments for {name}: {e}"}
