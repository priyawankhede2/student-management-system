import sqlite3
import os
import hashlib
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sms.db")

def hash_password(password: str) -> str:
    """Simple SHA-256 password hash for standard model compatibility."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('ADMIN', 'TEACHER', 'STUDENT')),
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
        employee_number TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        department_id INTEGER REFERENCES departments(id),
        designation TEXT,
        email TEXT,
        phone TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'INACTIVE')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
        admission_number TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        date_of_birth DATE,
        gender TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        department_id INTEGER REFERENCES departments(id),
        admission_date DATE NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'INACTIVE', 'GRADUATED', 'WITHDRAWN')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS academic_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id INTEGER REFERENCES departments(id),
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        credits REAL DEFAULT 3.0,
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS class_offerings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL REFERENCES courses(id),
        academic_session_id INTEGER NOT NULL REFERENCES academic_sessions(id),
        teacher_id INTEGER NOT NULL REFERENCES teachers(id),
        section TEXT DEFAULT 'A',
        semester TEXT DEFAULT 'Semester 1',
        capacity INTEGER DEFAULT 60,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        UNIQUE(course_id, academic_session_id, section)
    );

    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL REFERENCES students(id),
        class_offering_id INTEGER NOT NULL REFERENCES class_offerings(id),
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'WITHDRAWN', 'COMPLETED')),
        UNIQUE(student_id, class_offering_id)
    );

    CREATE TABLE IF NOT EXISTS class_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_offering_id INTEGER NOT NULL REFERENCES class_offerings(id),
        session_date DATE NOT NULL,
        topic TEXT,
        created_by_user_id INTEGER REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_session_id INTEGER NOT NULL REFERENCES class_sessions(id),
        student_id INTEGER NOT NULL REFERENCES students(id),
        status TEXT NOT NULL CHECK(status IN ('PRESENT', 'ABSENT', 'LATE', 'EXCUSED')),
        marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(class_session_id, student_id)
    );

    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_offering_id INTEGER NOT NULL REFERENCES class_offerings(id),
        name TEXT NOT NULL,
        assessment_type TEXT NOT NULL,
        assessment_date DATE,
        max_marks REAL NOT NULL,
        published INTEGER NOT NULL DEFAULT 0,
        created_by_teacher_id INTEGER REFERENCES teachers(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER NOT NULL REFERENCES assessments(id),
        student_id INTEGER NOT NULL REFERENCES students(id),
        marks_obtained REAL NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(assessment_id, student_id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor_name TEXT NOT NULL,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT,
        details TEXT,
        occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    seed_demo_data(conn)
    conn.close()

def log_audit(conn, actor_name: str, action: str, entity_type: str, entity_id: str, details: str):
    conn.execute(
        "INSERT INTO audit_logs (actor_name, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
        (actor_name, action, entity_type, str(entity_id), details)
    )

def seed_demo_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        return  # already seeded

    print("Seeding initial demo data...")

    # 1. Users
    users_data = [
        ("admin", "admin@school.edu", hash_password("admin123"), "ADMIN"),
        ("teacher_sharma", "sharma@school.edu", hash_password("teacher123"), "TEACHER"),
        ("teacher_verma", "verma@school.edu", hash_password("teacher123"), "TEACHER"),
        ("student_rahul", "rahul@school.edu", hash_password("student123"), "STUDENT"),
        ("student_priya", "priya@school.edu", hash_password("student123"), "STUDENT"),
        ("student_arjun", "arjun@school.edu", hash_password("student123"), "STUDENT"),
        ("student_ananya", "ananya@school.edu", hash_password("student123"), "STUDENT"),
    ]
    cursor.executemany(
        "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
        users_data
    )

    # 2. Departments
    depts = [
        ("CSE", "Computer Science & Engineering", "Computing, AI and Software Systems"),
        ("ECE", "Electronics & Communication", "Circuits, VLSI and Embedded Systems"),
        ("MECH", "Mechanical Engineering", "Thermodynamics and Robotics"),
        ("MGMT", "Management Studies", "Business Administration and Finance"),
    ]
    cursor.executemany("INSERT INTO departments (code, name, description) VALUES (?, ?, ?)", depts)

    # 3. Teachers
    teachers = [
        (2, "EMP-101", "Dr. Rajesh", "Sharma", 1, "Professor & HOD", "sharma@school.edu", "+91 98765 43210"),
        (3, "EMP-102", "Prof. Sunita", "Verma", 1, "Assistant Professor", "verma@school.edu", "+91 98765 43211"),
    ]
    cursor.executemany(
        """INSERT INTO teachers (user_id, employee_number, first_name, last_name, department_id, designation, email, phone) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", teachers
    )

    # 4. Students
    students = [
        (4, "STU-2026-001", "Rahul", "Kumar", "2004-05-15", "Male", "rahul@school.edu", "+91 91234 56780", "12 Patel Nagar, New Delhi", 1, "2024-08-01", "ACTIVE"),
        (5, "STU-2026-002", "Priya", "Singh", "2004-09-22", "Female", "priya@school.edu", "+91 91234 56781", "45 Mall Road, Jaipur", 1, "2024-08-01", "ACTIVE"),
        (6, "STU-2026-003", "Arjun", "Mehta", "2003-12-10", "Male", "arjun@school.edu", "+91 91234 56782", "88 Park Street, Kolkata", 1, "2024-08-01", "ACTIVE"),
        (7, "STU-2026-004", "Ananya", "Roy", "2004-02-18", "Female", "ananya@school.edu", "+91 91234 56783", "19 MG Road, Bengaluru", 2, "2024-08-01", "ACTIVE"),
    ]
    cursor.executemany(
        """INSERT INTO students (user_id, admission_number, first_name, last_name, date_of_birth, gender, email, phone, address, department_id, admission_date, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", students
    )

    # 5. Academic Sessions
    cursor.execute(
        "INSERT INTO academic_sessions (name, start_date, end_date, active) VALUES (?, ?, ?, ?)",
        ("2026-2027 Academic Year", "2026-08-01", "2027-05-31", 1)
    )

    # 6. Courses
    courses = [
        (1, "CS-301", "Data Structures & Algorithms", "Core computer science fundamentals, trees, graphs, dynamic programming.", 4.0),
        (1, "CS-302", "Database Management Systems", "Relational models, SQL, indexing, transactions, and ACID properties.", 4.0),
        (1, "CS-303", "Full-Stack Web Development", "Modern web architecture, RESTful APIs, responsive design.", 3.0),
        (2, "EC-201", "Digital Electronics", "Logic gates, combinatorial circuits, and microprocessors.", 3.5),
    ]
    cursor.executemany("INSERT INTO courses (department_id, code, name, description, credits) VALUES (?, ?, ?, ?, ?)", courses)

    # 7. Class Offerings
    offerings = [
        (1, 1, 1, "Sec-A", "Semester 3", 60),  # CS-301 taught by Dr. Sharma
        (2, 1, 1, "Sec-A", "Semester 3", 60),  # CS-302 taught by Dr. Sharma
        (3, 1, 2, "Sec-B", "Semester 3", 50),  # CS-303 taught by Prof. Verma
    ]
    cursor.executemany(
        "INSERT INTO class_offerings (course_id, academic_session_id, teacher_id, section, semester, capacity) VALUES (?, ?, ?, ?, ?, ?)",
        offerings
    )

    # 8. Enrollments (Rahul, Priya, Arjun in CS-301 and CS-302)
    enrollments = [
        (1, 1), (2, 1), (3, 1),  # Students 1, 2, 3 in CS-301
        (1, 2), (2, 2), (3, 2),  # Students 1, 2, 3 in CS-302
        (1, 3), (2, 3),          # Students 1, 2 in CS-303
    ]
    cursor.executemany("INSERT INTO enrollments (student_id, class_offering_id) VALUES (?, ?)", enrollments)

    # 9. Class Sessions & Attendance History
    sessions = [
        (1, "2026-10-20", "Introduction to Binary Search Trees", 2),
        (1, "2026-10-22", "AVL Trees and Tree Balancing", 2),
        (1, "2026-10-24", "Graph Traversal: BFS & DFS", 2),
        (2, "2026-10-21", "Relational Algebra and SQL Joins", 2),
        (2, "2026-10-23", "Database Normalization (1NF, 2NF, 3NF, BCNF)", 2),
    ]
    cursor.executemany("INSERT INTO class_sessions (class_offering_id, session_date, topic, created_by_user_id) VALUES (?, ?, ?, ?)", sessions)

    att_records = [
        # Session 1 (CS-301)
        (1, 1, "PRESENT"), (1, 2, "PRESENT"), (1, 3, "ABSENT"),
        # Session 2 (CS-301)
        (2, 1, "PRESENT"), (2, 2, "PRESENT"), (2, 3, "PRESENT"),
        # Session 3 (CS-301)
        (3, 1, "PRESENT"), (3, 2, "LATE"),    (3, 3, "PRESENT"),
        # Session 4 (CS-302)
        (4, 1, "PRESENT"), (4, 2, "PRESENT"), (4, 3, "PRESENT"),
        # Session 5 (CS-302)
        (5, 1, "PRESENT"), (5, 2, "ABSENT"),  (5, 3, "PRESENT"),
    ]
    cursor.executemany("INSERT INTO attendance (class_session_id, student_id, status) VALUES (?, ?, ?)", att_records)

    # 10. Assessments & Marks
    assessments = [
        (1, "Mid-Term Examination", "EXAM", "2026-10-15", 50.0, 1, 1),
        (1, "Assignment 1: Heap & Graph Implementation", "ASSIGNMENT", "2026-10-18", 20.0, 1, 1),
        (2, "DBMS Quiz 1", "QUIZ", "2026-10-19", 25.0, 1, 1),
        (2, "Mid-Term Examination", "EXAM", "2026-10-25", 50.0, 0, 1), # Unpublished exam
    ]
    cursor.executemany(
        "INSERT INTO assessments (class_offering_id, name, assessment_type, assessment_date, max_marks, published, created_by_teacher_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        assessments
    )

    marks = [
        # Mid-Term CS-301 (Max: 50)
        (1, 1, 46.5),  # Rahul: 46.5/50 (93%)
        (1, 2, 44.0),  # Priya: 44.0/50 (88%)
        (1, 3, 38.5),  # Arjun: 38.5/50 (77%)
        # Assignment 1 CS-301 (Max: 20)
        (2, 1, 19.0),
        (2, 2, 18.5),
        (2, 3, 17.0),
        # DBMS Quiz (Max: 25)
        (3, 1, 24.0),
        (3, 2, 23.5),
        (3, 3, 20.0),
        # DBMS Mid-Term (Max: 50) - unpublished
        (4, 1, 45.0),
        (4, 2, 42.0),
        (4, 3, 39.0),
    ]
    cursor.executemany("INSERT INTO marks (assessment_id, student_id, marks_obtained) VALUES (?, ?, ?)", marks)

    # 11. Initial Audit Logs
    audit_events = [
        ("System Admin", "INITIALIZE", "DATABASE", "1", "Initialized Student Management System schema with seed data"),
        ("System Admin", "CREATE", "STUDENT", "STU-2026-001", "Registered student Rahul Kumar (CSE)"),
        ("Dr. Rajesh Sharma", "PUBLISH", "ASSESSMENT", "1", "Published Mid-Term Examination marks for CS-301"),
        ("Dr. Rajesh Sharma", "ATTENDANCE", "SESSION", "3", "Marked attendance for Session 3 on 2026-10-24"),
    ]
    cursor.executemany(
        "INSERT INTO audit_logs (actor_name, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
        audit_events
    )

    conn.commit()
    print("Demo data seeded successfully.")

if __name__ == "__main__":
    init_db()
