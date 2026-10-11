"""Fill data/college.db with realistic dummy student data: python -m app.seed

Uses Faker (Indian locale) for dates and addresses, with a fixed seed, so every run produces the same data.
Academic year 2026-27, odd semester: 1st years are in semester 1, 2nd years in 3,
3rd years in 5 and 4th years in 7. Marks exist for every completed semester and
attendance for every working day of the current semester so far.
"""
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

from app.config import settings
from app.db import connect, create_schema

SEED = 42
STUDENTS_PER_SECTION = 30
SECTIONS = ["A", "B"]
ACADEMIC_YEAR_START = 2026  # 2026-27
TODAY = date(2026, 10, 9)

DEPARTMENTS = {  # department -> roll number code
    "CSE": "CS",
    "ECE": "EC",
    "EEE": "EE",
    "IT": "IT",
    "MECH": "ME",
}

CITIES = [
    "Tiruchengode", "Namakkal", "Salem", "Erode", "Rasipuram", "Komarapalayam", "Sankagiri",
    "Coimbatore", "Tiruppur", "Karur", "Dharmapuri", "Krishnagiri", "Attur", "Bhavani",
    "Gobichettipalayam", "Madurai", "Tiruchirappalli", "Chennai", "Dindigul", "Pollachi",
]
# Tamil Nadu style names: given name + father's initial, e.g. "Karthik R" (father "Ramesh K").
MALE_NAMES = [
    "Karthik", "Arun", "Vignesh", "Praveen", "Surya", "Dinesh", "Gokul", "Hari", "Ajith", "Vijay",
    "Naveen", "Ragul", "Santhosh", "Mohan", "Sanjay", "Pranav", "Kishore", "Lokesh", "Barath",
    "Dhanush", "Kavin", "Nithish", "Tamilselvan", "Sabari", "Yuvaraj", "Ashwin", "Manoj", "Prakash",
    "Rajesh", "Saravanan", "Senthil", "Gowtham", "Bala", "Deepak", "Jeeva", "Kumaran", "Madhan",
    "Muthu", "Prabhu", "Ramkumar", "Sriram", "Thiru", "Vasanth", "Vishnu", "Aravind", "Elango",
    "Ganesh", "Inban", "Kathir", "Mukesh", "Nandha", "Pugazh", "Sathish", "Sudharsan", "Tharun",
]
FEMALE_NAMES = [
    "Priya", "Divya", "Keerthana", "Kavya", "Swetha", "Harini", "Nandhini", "Pavithra", "Deepika",
    "Janani", "Abinaya", "Sowmiya", "Gayathri", "Monisha", "Dharshini", "Kaviya", "Sandhiya", "Yazhini",
    "Ishwarya", "Madhumitha", "Revathi", "Sangeetha", "Thenmozhi", "Varsha", "Akshaya", "Bhuvana",
    "Durga", "Hema", "Indhu", "Jayashree", "Kalaivani", "Lakshmi", "Malini", "Nivetha", "Oviya",
    "Preethi", "Ramya", "Sneha", "Tamilarasi", "Vaishnavi", "Anitha", "Brindha", "Charumathi",
    "Elakkiya", "Gomathi", "Haritha", "Kanimozhi", "Mahalakshmi", "Nisha", "Poorani", "Shalini",
]
FATHER_NAMES = [
    "Ramesh", "Kumar", "Murugan", "Selvam", "Rajendran", "Subramani", "Palanisamy", "Velusamy",
    "Kandasamy", "Shanmugam", "Raju", "Mani", "Arumugam", "Chinnasamy", "Duraisamy", "Ganesan",
    "Krishnan", "Mohan", "Natarajan", "Periyasamy", "Ravi", "Sekar", "Senthilkumar", "Thangaraj",
    "Venkatesan", "Elango", "Jayakumar", "Karuppusamy", "Loganathan", "Muthusamy", "Prabhakaran",
    "Ramasamy", "Sivakumar", "Balasubramanian", "Govindaraj", "Saravanan", "Ponnusamy", "Annadurai",
]
INITIALS = "ABCDEGJKMNPRSTV"
BLOOD_GROUPS = ["O+", "B+", "A+", "AB+", "O-", "B-", "A-", "AB-"]
BLOOD_WEIGHTS = [37, 30, 22, 6, 2, 1.5, 1, 0.5]

# Anna University style grading: (minimum total, grade, grade points)
GRADES = [(91, "O", 10), (81, "A+", 9), (71, "A", 8), (61, "B+", 7), (56, "B", 6), (50, "C", 5)]

# Holidays in the current semester (weekdays only matter).
HOLIDAYS = {date(2026, 8, 15), date(2026, 9, 14), date(2026, 10, 2)}
SEMESTER_START = {1: date(2026, 8, 17), 3: date(2026, 7, 1), 5: date(2026, 7, 1), 7: date(2026, 7, 1)}

COMMON_SUBJECTS = {
    1: [("MA101", "Engineering Mathematics I", 4), ("PH101", "Engineering Physics", 3),
        ("CY101", "Engineering Chemistry", 3), ("GE101", "Problem Solving and Python Programming", 3),
        ("EN101", "Professional English I", 3), ("GE102", "Engineering Graphics", 4)],
    2: [("MA102", "Engineering Mathematics II", 4), ("PH102", "Physics for Engineering Sciences", 3),
        ("EN102", "Professional English II", 3), ("GE103", "Programming in C", 3),
        ("GE104", "Basic Electrical and Electronics Engineering", 3),
        ("GE105", "Environmental Science and Sustainability", 2)],
}

DEPARTMENT_SUBJECTS = {  # semesters 3 to 7, five subjects each
    "CSE": [
        ["Discrete Mathematics", "Data Structures", "Object Oriented Programming", "Digital Principles and Computer Organization", "Foundations of Data Science"],
        ["Probability and Queueing Theory", "Design and Analysis of Algorithms", "Database Management Systems", "Operating Systems", "Theory of Computation"],
        ["Computer Networks", "Compiler Design", "Artificial Intelligence", "Software Engineering", "Web Technologies"],
        ["Machine Learning", "Cloud Computing", "Object Oriented Software Engineering", "Embedded Systems and IoT", "Cryptography and Network Security"],
        ["Deep Learning", "Big Data Analytics", "Human Values and Ethics", "Distributed Systems", "Natural Language Processing"],
    ],
    "IT": [
        ["Discrete Mathematics", "Data Structures and Algorithms", "Java Programming", "Digital Logic and Computer Design", "Information Theory and Coding"],
        ["Probability and Statistics", "Database Management Systems", "Operating Systems", "Computer Architecture", "Software Engineering"],
        ["Computer Networks", "Web Application Development", "Artificial Intelligence", "Data Warehousing and Data Mining", "Mobile Application Development"],
        ["Machine Learning Techniques", "Cloud Computing", "Information Security", "Internet of Things", "Full Stack Development"],
        ["Deep Learning", "DevOps", "Human Values and Ethics", "Blockchain Technologies", "Big Data Analytics"],
    ],
    "ECE": [
        ["Random Processes and Linear Algebra", "Electronic Devices and Circuits", "Signals and Systems", "Digital Systems Design", "Circuit Analysis"],
        ["Electromagnetic Fields", "Linear Integrated Circuits", "Analog Communication", "Microprocessors and Microcontrollers", "Control Systems"],
        ["Digital Communication", "Digital Signal Processing", "Transmission Lines and RF Systems", "VLSI Design", "Embedded Systems"],
        ["Wireless Communication", "Antennas and Wave Propagation", "Optical Communication", "Internet of Things", "Computer Networks"],
        ["Satellite Communication", "Microwave Engineering", "Human Values and Ethics", "Image Processing", "Radar and Navigational Aids"],
    ],
    "EEE": [
        ["Transforms and Partial Differential Equations", "Electric Circuit Analysis", "Electron Devices and Circuits", "Electrical Machines I", "Electromagnetic Theory"],
        ["Numerical Methods", "Electrical Machines II", "Linear Integrated Circuits", "Measurements and Instrumentation", "Control Systems"],
        ["Power System Analysis", "Power Electronics", "Microprocessors and Microcontrollers", "Digital Signal Processing", "Transmission and Distribution"],
        ["Protection and Switchgear", "Solid State Drives", "Renewable Energy Systems", "Power System Operation and Control", "Electric Vehicles"],
        ["High Voltage Engineering", "Smart Grid", "Human Values and Ethics", "Embedded Systems", "Energy Auditing and Conservation"],
    ],
    "MECH": [
        ["Transforms and Partial Differential Equations", "Engineering Mechanics", "Engineering Thermodynamics", "Manufacturing Technology I", "Fluid Mechanics and Machinery"],
        ["Statistics and Numerical Methods", "Theory of Machines", "Strength of Materials", "Manufacturing Technology II", "Thermal Engineering"],
        ["Design of Machine Elements", "Heat and Mass Transfer", "Metrology and Measurements", "CAD/CAM", "Hydraulics and Pneumatics"],
        ["Finite Element Analysis", "Mechatronics", "Automobile Engineering", "Industrial Engineering", "Refrigeration and Air Conditioning"],
        ["Robotics", "Power Plant Engineering", "Human Values and Ethics", "Additive Manufacturing", "Operations Research"],
    ],
}


def build_subjects():
    rows = []
    for sem, subjects in COMMON_SUBJECTS.items():
        rows += [(code, name, "ALL", sem, credits) for code, name, credits in subjects]
    for dept, semesters in DEPARTMENT_SUBJECTS.items():
        code = DEPARTMENTS[dept]
        for offset, names in enumerate(semesters):
            sem = offset + 3
            rows += [(f"{code}{sem}{i + 1:02d}", name, dept, sem, 4 if i < 2 else 3) for i, name in enumerate(names)]
    return rows


def subjects_for(subjects, dept, sem):
    return [s for s in subjects if s[3] == sem and s[2] in ("ALL", dept)]


def exam_session(batch_start: int, sem: int) -> str:
    year = batch_start + (sem - 1) // 2 + (0 if sem % 2 else 1)
    return f"Nov/Dec {year}" if sem % 2 else f"Apr/May {year}"


def grade_for(total: int):
    for minimum, grade, points in GRADES:
        if total >= minimum:
            return grade, points
    return "U", 0


def working_days(start: date, end: date):
    day = start
    while day <= end:
        if day.weekday() < 5 and day not in HOLIDAYS:
            yield day
        day += timedelta(days=1)


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def main():
    fake = Faker("en_IN")
    Faker.seed(SEED)
    rng = random.Random(SEED)

    db_path = Path(settings.database_path)
    if db_path.exists():
        db_path.unlink()  # always rebuild from scratch
    conn = connect(str(db_path))
    create_schema(conn)

    subjects = build_subjects()
    conn.executemany("INSERT INTO subjects VALUES (?, ?, ?, ?, ?)", subjects)

    students, attendance, marks, arrears = [], [], [], []
    student_no = 10000
    for year in range(1, 5):
        batch_start = ACADEMIC_YEAR_START - (year - 1)
        current_sem = 2 * year - 1
        for dept, code in DEPARTMENTS.items():
            roll_no = 0
            for section in SECTIONS:
                for _ in range(STUDENTS_PER_SECTION):
                    student_no += 1
                    roll_no += 1
                    sid = f"STU{student_no}"
                    roll = f"{batch_start % 100}{code}{roll_no:03d}"

                    gender = rng.choices(["Male", "Female"], weights=[60, 40])[0]
                    first = rng.choice(MALE_NAMES if gender == "Male" else FEMALE_NAMES)
                    father = rng.choice(FATHER_NAMES)
                    name = f"{first} {father[0]}"
                    dob = fake.date_between(date(batch_start - 18, 6, 1), date(batch_start - 17, 7, 31))
                    city = rng.choice(CITIES)

                    # Hidden traits that make each student's data consistent.
                    ability = clip(rng.gauss(0.68, 0.13), 0.30, 0.97)
                    regularity = clip(rng.gauss(0.68, 0.06), 0.50, 0.80) if rng.random() < 0.1 \
                        else clip(rng.gauss(0.88 + (ability - 0.68) * 0.15, 0.05), 0.72, 0.99)

                    # Marks and arrears for completed semesters.
                    credit_points = credits_total = 0
                    for sem in range(1, current_sem):
                        session = exam_session(batch_start, sem)
                        for subj_code, _, _, _, credits in subjects_for(subjects, dept, sem):
                            internal = round(40 * clip(ability + rng.gauss(0.05, 0.08), 0.25, 1.0))
                            external = round(60 * clip(ability + rng.gauss(0.02, 0.11), 0.10, 1.0))
                            total = internal + external
                            passed = external >= 27 and total >= 50
                            grade, points = grade_for(total) if passed else ("U", 0)
                            marks.append((sid, subj_code, sem, session, internal, external, total, grade,
                                          "PASS" if passed else "FAIL"))
                            if passed:
                                credit_points += points * credits
                                credits_total += credits
                                continue
                            # Failed: an arrear. Older arrears are more likely to be cleared.
                            exams_since = current_sem - 1 - sem
                            cleared = exams_since > 0 and rng.random() < 0.55 + 0.1 * exams_since
                            attempts = 1 + (rng.randint(1, exams_since) if cleared else exams_since)
                            cleared_in = exam_session(batch_start, sem + attempts - 1) if cleared else None
                            arrears.append((sid, subj_code, sem, attempts, "Cleared" if cleared else "Pending", cleared_in))
                            if cleared:
                                credit_points += rng.choice([5, 5, 6]) * credits
                                credits_total += credits
                    cgpa = round(credit_points / credits_total, 2) if credits_total else None

                    # Daily attendance for the current semester.
                    for day in working_days(SEMESTER_START[current_sem], TODAY):
                        if rng.random() < regularity:
                            status = "OD" if rng.random() < 0.03 else "Present"
                        else:
                            status = "Absent"
                        attendance.append((sid, day.isoformat(), status))

                    students.append((
                        sid, roll, name, gender, dob.isoformat(), dept, year, current_sem, section,
                        f"{batch_start}-{batch_start + 4}",
                        f"{first.lower()}.{roll.lower()}@ksrce.ac.in",
                        f"{rng.choice('6789')}{rng.randint(0, 999999999):09d}",
                        f"{father} {rng.choice(INITIALS)}",
                        f"{rng.choice('6789')}{rng.randint(0, 999999999):09d}",
                        f"{fake.building_number()}, {fake.street_name()}, {city}, Tamil Nadu {rng.randint(600001, 643253)}",
                        city,
                        rng.choices(BLOOD_GROUPS, weights=BLOOD_WEIGHTS)[0],
                        rng.choices(["Counselling", "Management"], weights=[70, 30])[0],
                        rng.choices(["Hosteller", "Day Scholar"], weights=[45, 55])[0],
                        cgpa,
                    ))

    conn.executemany("INSERT INTO students VALUES (" + ",".join("?" * 20) + ")", students)
    conn.executemany("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)", attendance)
    conn.executemany(
        "INSERT INTO marks (student_id, subject_code, semester, exam_session, internal_marks, "
        "external_marks, total_marks, grade, result) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", marks)
    conn.executemany(
        "INSERT INTO arrears (student_id, subject_code, semester, attempts, status, cleared_session) "
        "VALUES (?, ?, ?, ?, ?, ?)", arrears)
    conn.commit()

    for table in ("students", "subjects", "attendance", "marks", "arrears"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:12} {count:>7} rows")
    print(f"Database: {db_path}")


if __name__ == "__main__":
    main()
