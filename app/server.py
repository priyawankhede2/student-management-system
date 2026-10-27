import http.server
import socketserver
import json
import urllib.parse
import os
import csv
import io
import mimetypes
import logging
from datetime import datetime, date

from .database import get_db, init_db, log_audit, hash_password

PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sms.log")

# Setup Comprehensive System File Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SMS-Core] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SMS-Server")

class SMSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format, *args):
        # Override default to write to logger file
        logger.info(f"{self.client_address[0]} - {format % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        logger.warning(f"API Error {status}: {message}")
        self.send_json({"success": False, "error": message}, status=status)

    def read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            raw_data = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw_data)
        except Exception as e:
            logger.error(f"Error parsing JSON payload: {e}")
            return None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Route API requests
        if path.startswith("/api/"):
            try:
                self.handle_api_get(path, query)
            except Exception as e:
                logger.error(f"Internal exception handling {path}: {e}", exc_info=True)
                self.send_error_json(f"Internal server error: {str(e)}", 500)
            return

        # Fallback to single-page app or static assets
        if path == "/" or not os.path.exists(os.path.join(STATIC_DIR, path.lstrip("/"))):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            try:
                self.handle_api_post(path)
            except Exception as e:
                logger.error(f"Internal exception handling {path}: {e}", exc_info=True)
                self.send_error_json(f"Internal server error: {str(e)}", 500)
            return
        self.send_error_json("Not Found", 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            try:
                self.handle_api_put(path)
            except Exception as e:
                logger.error(f"Internal exception handling {path}: {e}", exc_info=True)
                self.send_error_json(f"Internal server error: {str(e)}", 500)
            return
        self.send_error_json("Not Found", 404)

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            try:
                self.handle_api_patch(path)
            except Exception as e:
                logger.error(f"Internal exception handling {path}: {e}", exc_info=True)
                self.send_error_json(f"Internal server error: {str(e)}", 500)
            return
        self.send_error_json("Not Found", 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            try:
                self.handle_api_delete(path)
            except Exception as e:
                logger.error(f"Internal exception handling {path}: {e}", exc_info=True)
                self.send_error_json(f"Internal server error: {str(e)}", 500)
            return
        self.send_error_json("Not Found", 404)

    # ==========================================
    # API GET HANDLERS
    # ==========================================
    def handle_api_get(self, path, query):
        conn = get_db()
        cursor = conn.cursor()

        # 1. Live Server File Logs
        if path == "/api/logs/file":
            lines_to_return = []
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    all_lines = f.readlines()
                    lines_to_return = all_lines[-200:]  # latest 200 lines
            self.send_json({"success": True, "data": lines_to_return, "count": len(lines_to_return)})
            conn.close()
            return

        # 2. Download Raw Log File
        if path == "/api/logs/download":
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="sms_server.log"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error_json("Log file does not exist yet.", 404)
            conn.close()
            return

        # 3. Dashboard Stats
        if path == "/api/dashboard/stats":
            cursor.execute("SELECT COUNT(*) FROM students WHERE status='ACTIVE'")
            active_students = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM teachers WHERE status='ACTIVE'")
            total_teachers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM courses WHERE active=1")
            total_courses = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM class_offerings WHERE status='ACTIVE'")
            total_offerings = cursor.fetchone()[0]

            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('PRESENT', 'LATE') THEN 1 ELSE 0 END) as attended
                FROM attendance
            """)
            att_row = cursor.fetchone()
            total_att = att_row["total"] or 0
            attended = att_row["attended"] or 0
            att_pct = round((attended / total_att * 100), 1) if total_att > 0 else 0

            cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 5")
            recent_audit = [dict(row) for row in cursor.fetchall()]

            cursor.execute("""
                SELECT d.name, COUNT(s.id) as count
                FROM departments d
                LEFT JOIN students s ON s.department_id = d.id AND s.status = 'ACTIVE'
                GROUP BY d.id
            """)
            dept_stats = [dict(row) for row in cursor.fetchall()]

            self.send_json({
                "success": True,
                "data": {
                    "total_students": total_students,
                    "active_students": active_students,
                    "total_teachers": total_teachers,
                    "total_courses": total_courses,
                    "total_offerings": total_offerings,
                    "attendance_rate": att_pct,
                    "recent_audit": recent_audit,
                    "department_distribution": dept_stats
                }
            })
            conn.close()
            return

        # 4. Students List
        if path == "/api/students":
            search = query.get("search", [""])[0].strip()
            dept_id = query.get("department_id", [""])[0].strip()
            status = query.get("status", [""])[0].strip()

            sql = """
                SELECT s.*, d.name as department_name, d.code as department_code,
                       (SELECT COUNT(*) FROM enrollments e WHERE e.student_id = s.id AND e.status = 'ACTIVE') as enrolled_courses_count
                FROM students s
                LEFT JOIN departments d ON s.department_id = d.id
                WHERE 1=1
            """
            params = []
            if search:
                sql += " AND (s.first_name LIKE ? OR s.last_name LIKE ? OR s.admission_number LIKE ? OR s.email LIKE ?)"
                like = f"%{search}%"
                params.extend([like, like, like, like])
            if dept_id:
                sql += " AND s.department_id = ?"
                params.append(dept_id)
            if status:
                sql += " AND s.status = ?"
                params.append(status)

            sql += " ORDER BY s.id DESC"
            cursor.execute(sql, params)
            students = [dict(row) for row in cursor.fetchall()]
            self.send_json({"success": True, "data": students})
            conn.close()
            return

        # 5. Single Student Details
        if path.startswith("/api/students/"):
            parts = path.strip("/").split("/")
            if len(parts) == 3 and parts[2].isdigit():
                stu_id = int(parts[2])
                cursor.execute("""
                    SELECT s.*, d.name as department_name, u.username
                    FROM students s
                    LEFT JOIN departments d ON s.department_id = d.id
                    LEFT JOIN users u ON s.user_id = u.id
                    WHERE s.id = ?
                """, (stu_id,))
                stu = cursor.fetchone()
                if not stu:
                    self.send_error_json("Student not found", 404)
                else:
                    self.send_json({"success": True, "data": dict(stu)})
                conn.close()
                return

        # 6. Teachers List
        if path == "/api/teachers":
            cursor.execute("""
                SELECT t.*, d.name as department_name,
                       (SELECT COUNT(*) FROM class_offerings co WHERE co.teacher_id = t.id AND co.status='ACTIVE') as active_classes_count
                FROM teachers t
                LEFT JOIN departments d ON t.department_id = d.id
                ORDER BY t.id ASC
            """)
            teachers = [dict(row) for row in cursor.fetchall()]
            self.send_json({"success": True, "data": teachers})
            conn.close()
            return

        # 7. Departments List
        if path == "/api/departments":
            cursor.execute("SELECT * FROM departments WHERE active=1 ORDER BY name ASC")
            depts = [dict(row) for row in cursor.fetchall()]
            self.send_json({"success": True, "data": depts})
            conn.close()
            return

        # 8. Courses List
        if path == "/api/courses":
            cursor.execute("""
                SELECT c.*, d.name as department_name, d.code as department_code
                FROM courses c
                LEFT JOIN departments d ON c.department_id = d.id
                ORDER BY c.code ASC
            """)
            courses = [dict(row) for row in cursor.fetchall()]
            self.send_json({"success": True, "data": courses})
            conn.close()
            return

        # 9. Class Offerings
        if path == "/api/offerings":
            teacher_id = query.get("teacher_id", [""])[0].strip()
            sql = """
                SELECT co.*, c.code as course_code, c.name as course_name, c.credits,
                       t.first_name || ' ' || t.last_name as teacher_name,
                       a.name as session_name,
                       (SELECT COUNT(*) FROM enrollments e WHERE e.class_offering_id = co.id AND e.status = 'ACTIVE') as enrolled_count
                FROM class_offerings co
                JOIN courses c ON co.course_id = c.id
                JOIN academic_sessions a ON co.academic_session_id = a.id
                JOIN teachers t ON co.teacher_id = t.id
                WHERE co.status = 'ACTIVE'
            """
            params = []
            if teacher_id:
                sql += " AND co.teacher_id = ?"
                params.append(teacher_id)
            sql += " ORDER BY c.code ASC"
            cursor.execute(sql, params)
            offerings = [dict(row) for row in cursor.fetchall()]
            self.send_json({"success": True, "data": offerings})
            conn.close()
            return

        # 10. Students enrolled in offering
        if path.startswith("/api/offerings/") and path.endswith("/students"):
            offering_id = int(path.split("/")[3])
            cursor.execute("""
                SELECT s.id as student_id, s.admission_number, s.first_name, s.last_name, s.email, e.id as enrollment_id,
                       e.status as enrollment_status, e.enrolled_at
                FROM enrollments e
                JOIN students s ON e.student_id = s.id
                WHERE e.class_offering_id = ? AND e.status = 'ACTIVE'
                ORDER BY s.first_name ASC
            """, (offering_id,))
            students = [dict(row) for row in cursor.fetchall()]
            self.send_json({"success": True, "data": students})
            conn.close()
            return

        # 11. Sessions for attendance
        if path == "/api/attendance/sessions":
            offering_id = query.get("offering_id", [""])[0].strip()
            sql = """
                SELECT cs.*, co.section, c.code as course_code, c.name as course_name,
                       (SELECT COUNT(*) FROM attendance a WHERE a.class_session_id = cs.id) as attendance_marked_count,
                       (SELECT SUM(CASE WHEN a.status IN ('PRESENT', 'LATE') THEN 1 ELSE 0 END) FROM attendance a WHERE a.class_session_id = cs.id) as present_count
                FROM class_sessions cs
                JOIN class_offerings co ON cs.class_offering_id = co.id
                JOIN courses c ON co.course_id = c.id
                WHERE 1=1
            """
            params = []
            if offering_id:
                sql += " AND cs.class_offering_id = ?"
                params.append(offering_id)
            sql += " ORDER BY cs.session_date DESC, cs.id DESC"
            cursor.execute(sql, params)
            sessions = [dict(row) for row in cursor.fetchall()]
            self.send_json({"success": True, "data": sessions})
            conn.close()
            return

        # 12. Attendance Sheet for a Session
        if path.startswith("/api/attendance/session/"):
            session_id = int(path.split("/")[4])
            cursor.execute("""
                SELECT cs.*, co.id as offering_id, c.name as course_name, c.code as course_code, co.section
                FROM class_sessions cs
                JOIN class_offerings co ON cs.class_offering_id = co.id
                JOIN courses c ON co.course_id = c.id
                WHERE cs.id = ?
            """, (session_id,))
            session_meta = cursor.fetchone()
            if not session_meta:
                self.send_error_json("Session not found", 404)
                conn.close()
                return

            cursor.execute("""
                SELECT s.id as student_id, s.admission_number, s.first_name, s.last_name,
                       COALESCE(a.status, 'PRESENT') as attendance_status,
                       a.id as attendance_id
                FROM enrollments e
                JOIN students s ON e.student_id = s.id
                LEFT JOIN attendance a ON a.class_session_id = ? AND a.student_id = s.id
                WHERE e.class_offering_id = ? AND e.status = 'ACTIVE'
                ORDER BY s.first_name ASC
            """, (session_id, session_meta["offering_id"]))
            student_sheet = [dict(row) for row in cursor.fetchall()]

            self.send_json({
                "success": True,
                "data": {
                    "session": dict(session_meta),
                    "sheet": student_sheet
                }
            })
            conn.close()
            return

        # 13. Assessments List
        if path == "/api/assessments":
            offering_id = query.get("offering_id", [""])[0].strip()
            teacher_id = query.get("teacher_id", [""])[0].strip()
            sql = """
                SELECT a.*, c.code as course_code, c.name as course_name, co.section,
                       (SELECT COUNT(*) FROM marks m WHERE m.assessment_id = a.id) as marks_entered_count,
                       (SELECT COUNT(*) FROM enrollments e WHERE e.class_offering_id = a.class_offering_id AND e.status = 'ACTIVE') as total_students
                FROM assessments a
                JOIN class_offerings co ON a.class_offering_id = co.id
                JOIN courses c ON co.course_id = c.id
                WHERE 1=1
            """
            params = []
            if offering_id:
                sql += " AND a.class_offering_id = ?"
                params.append(offering_id)
            if teacher_id:
                sql += " AND co.teacher_id = ?"
                params.append(teacher_id)
            sql += " ORDER BY a.id DESC"
            cursor.execute(sql, params)
            assessments = [dict(row) for row in cursor.fetchall()]
            self.send_json({"success": True, "data": assessments})
            conn.close()
            return

        # 14. Marks Sheet for Assessment
        if path.startswith("/api/assessments/") and path.endswith("/marks"):
            assessment_id = int(path.split("/")[3])
            cursor.execute("""
                SELECT a.*, c.code as course_code, c.name as course_name, co.section
                FROM assessments a
                JOIN class_offerings co ON a.class_offering_id = co.id
                JOIN courses c ON co.course_id = c.id
                WHERE a.id = ?
            """, (assessment_id,))
            assessment_meta = cursor.fetchone()
            if not assessment_meta:
                self.send_error_json("Assessment not found", 404)
                conn.close()
                return

            cursor.execute("""
                SELECT s.id as student_id, s.admission_number, s.first_name, s.last_name,
                       m.marks_obtained, m.id as mark_id
                FROM enrollments e
                JOIN students s ON e.student_id = s.id
                LEFT JOIN marks m ON m.assessment_id = ? AND m.student_id = s.id
                WHERE e.class_offering_id = ? AND e.status = 'ACTIVE'
                ORDER BY s.first_name ASC
            """, (assessment_id, assessment_meta["class_offering_id"]))
            sheet = [dict(row) for row in cursor.fetchall()]

            self.send_json({
                "success": True,
                "data": {
                    "assessment": dict(assessment_meta),
                    "sheet": sheet
                }
            })
            conn.close()
            return

        # 15. Student Portal: My Attendance
        if path == "/api/student/me/attendance":
            student_id = query.get("student_id", ["1"])[0].strip()
            cursor.execute("""
                SELECT 
                    co.id as offering_id, c.code as course_code, c.name as course_name, c.credits,
                    t.first_name || ' ' || t.last_name as teacher_name,
                    COUNT(cs.id) as total_sessions,
                    SUM(CASE WHEN a.status = 'PRESENT' THEN 1 ELSE 0 END) as present_count,
                    SUM(CASE WHEN a.status = 'LATE' THEN 1 ELSE 0 END) as late_count,
                    SUM(CASE WHEN a.status = 'ABSENT' THEN 1 ELSE 0 END) as absent_count,
                    SUM(CASE WHEN a.status = 'EXCUSED' THEN 1 ELSE 0 END) as excused_count
                FROM enrollments e
                JOIN class_offerings co ON e.class_offering_id = co.id
                JOIN courses c ON co.course_id = c.id
                JOIN teachers t ON co.teacher_id = t.id
                LEFT JOIN class_sessions cs ON cs.class_offering_id = co.id
                LEFT JOIN attendance a ON a.class_session_id = cs.id AND a.student_id = e.student_id
                WHERE e.student_id = ? AND e.status = 'ACTIVE'
                GROUP BY co.id
            """, (student_id,))
            courses_att = []
            total_all_sessions = 0
            total_all_attended = 0

            for row in cursor.fetchall():
                d = dict(row)
                tot = d["total_sessions"] or 0
                pres = (d["present_count"] or 0) + (d["late_count"] or 0)
                pct = round((pres / tot * 100), 1) if tot > 0 else 100.0
                d["percentage"] = pct
                total_all_sessions += tot
                total_all_attended += pres
                courses_att.append(d)

            overall_pct = round((total_all_attended / total_all_sessions * 100), 1) if total_all_sessions > 0 else 100.0

            cursor.execute("""
                SELECT cs.session_date, cs.topic, c.code as course_code, c.name as course_name, a.status
                FROM attendance a
                JOIN class_sessions cs ON a.class_session_id = cs.id
                JOIN class_offerings co ON cs.class_offering_id = co.id
                JOIN courses c ON co.course_id = c.id
                WHERE a.student_id = ?
                ORDER BY cs.session_date DESC LIMIT 10
            """, (student_id,))
            recent = [dict(r) for r in cursor.fetchall()]

            self.send_json({
                "success": True,
                "data": {
                    "overall_percentage": overall_pct,
                    "courses": courses_att,
                    "recent_attendance": recent
                }
            })
            conn.close()
            return

        # 16. Student Portal: My Published Results
        if path == "/api/student/me/results":
            student_id = query.get("student_id", ["1"])[0].strip()
            cursor.execute("""
                SELECT 
                    a.id as assessment_id, a.name as assessment_name, a.assessment_type, a.max_marks,
                    c.code as course_code, c.name as course_name,
                    m.marks_obtained,
                    ROUND((m.marks_obtained / a.max_marks * 100), 1) as percentage
                FROM marks m
                JOIN assessments a ON m.assessment_id = a.id
                JOIN class_offerings co ON a.class_offering_id = co.id
                JOIN courses c ON co.course_id = c.id
                WHERE m.student_id = ? AND a.published = 1
                ORDER BY a.id DESC
            """, (student_id,))
            results = []
            total_max = 0
            total_obt = 0
            for r in cursor.fetchall():
                d = dict(r)
                pct = d["percentage"] or 0
                if pct >= 90: d["grade"] = "A+"
                elif pct >= 80: d["grade"] = "A"
                elif pct >= 70: d["grade"] = "B"
                elif pct >= 60: d["grade"] = "C"
                elif pct >= 50: d["grade"] = "D"
                else: d["grade"] = "F"
                total_max += d["max_marks"]
                total_obt += d["marks_obtained"]
                results.append(d)

            gpa_pct = round((total_obt / total_max * 100), 1) if total_max > 0 else 0
            self.send_json({
                "success": True,
                "data": {
                    "results": results,
                    "overall_percentage": gpa_pct
                }
            })
            conn.close()
            return

        # 17. Audit Logs with Filtering
        if path == "/api/audit-logs":
            action_filter = query.get("action", [""])[0].strip()
            search = query.get("search", [""])[0].strip()

            sql = "SELECT * FROM audit_logs WHERE 1=1"
            params = []
            if action_filter:
                sql += " AND action = ?"
                params.append(action_filter)
            if search:
                sql += " AND (actor_name LIKE ? OR details LIKE ? OR entity_type LIKE ?)"
                like = f"%{search}%"
                params.extend([like, like, like])

            sql += " ORDER BY id DESC LIMIT 100"
            cursor.execute(sql, params)
            logs = [dict(row) for row in cursor.fetchall()]
            self.send_json({"success": True, "data": logs})
            conn.close()
            return

        # 18. CSV Reports Export
        if path == "/api/reports/students.csv":
            cursor.execute("""
                SELECT s.admission_number, s.first_name, s.last_name, s.email, s.phone,
                       d.name as department, s.admission_date, s.status
                FROM students s
                LEFT JOIN departments d ON s.department_id = d.id
                ORDER BY s.admission_number ASC
            """)
            rows = cursor.fetchall()
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Admission No", "First Name", "Last Name", "Email", "Phone", "Department", "Admission Date", "Status"])
            for row in rows:
                writer.writerow(list(row))
            csv_data = output.getvalue().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="students_report.csv"')
            self.send_header("Content-Length", str(len(csv_data)))
            self.end_headers()
            self.wfile.write(csv_data)
            conn.close()
            return

        if path == "/api/reports/attendance.csv":
            cursor.execute("""
                SELECT cs.session_date, c.code as course_code, c.name as course,
                       s.admission_number, s.first_name || ' ' || s.last_name as student_name,
                       a.status, a.marked_at
                FROM attendance a
                JOIN class_sessions cs ON a.class_session_id = cs.id
                JOIN class_offerings co ON cs.class_offering_id = co.id
                JOIN courses c ON co.course_id = c.id
                JOIN students s ON a.student_id = s.id
                ORDER BY cs.session_date DESC, s.admission_number ASC
            """)
            rows = cursor.fetchall()
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Date", "Course Code", "Course Name", "Admission No", "Student Name", "Attendance Status", "Marked At"])
            for row in rows:
                writer.writerow(list(row))
            csv_data = output.getvalue().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="attendance_report.csv"')
            self.send_header("Content-Length", str(len(csv_data)))
            self.end_headers()
            self.wfile.write(csv_data)
            conn.close()
            return

        self.send_error_json("Endpoint Not Found", 404)
        conn.close()

    # ==========================================
    # API POST HANDLERS
    # ==========================================
    def handle_api_post(self, path):
        body = self.read_json_body()
        if body is None:
            self.send_error_json("Invalid JSON body", 400)
            return

        conn = get_db()
        cursor = conn.cursor()

        # 1. Login with Detailed Logging
        if path == "/api/auth/login":
            username_or_email = body.get("username", "").strip()
            password = body.get("password", "")

            cursor.execute("""
                SELECT id, username, email, password_hash, role, enabled
                FROM users
                WHERE (username = ? OR email = ?)
            """, (username_or_email, username_or_email))
            user = cursor.fetchone()

            if not user:
                logger.warning(f"LOGIN FAILED: User '{username_or_email}' not found.")
                log_audit(conn, username_or_email or "UNKNOWN", "FAILED_LOGIN", "USER", None, f"Failed login attempt: User not found from {self.client_address[0]}")
                conn.commit()
                conn.close()
                self.send_error_json("Invalid credentials. Please check username or password.", 401)
                return

            if user["enabled"] != 1:
                logger.warning(f"LOGIN BLOCKED: User '{username_or_email}' is disabled.")
                log_audit(conn, user["username"], "BLOCKED_LOGIN", "USER", user["id"], "Attempted login to disabled account")
                conn.commit()
                conn.close()
                self.send_error_json("This account has been deactivated by administrator.", 403)
                return

            if user["password_hash"] != hash_password(password):
                logger.warning(f"LOGIN FAILED: Invalid password for user '{username_or_email}'.")
                log_audit(conn, user["username"], "FAILED_LOGIN", "USER", user["id"], f"Incorrect password attempt from {self.client_address[0]}")
                conn.commit()
                conn.close()
                self.send_error_json("Invalid password entered. Please try again.", 401)
                return

            # Success
            profile = {"id": user["id"], "username": user["username"], "email": user["email"], "role": user["role"]}
            if user["role"] == "STUDENT":
                cursor.execute("SELECT id as student_id, admission_number, first_name, last_name, department_id FROM students WHERE user_id = ?", (user["id"],))
                stu = cursor.fetchone()
                if stu: profile.update(dict(stu))
            elif user["role"] == "TEACHER":
                cursor.execute("SELECT id as teacher_id, employee_number, first_name, last_name, designation, department_id FROM teachers WHERE user_id = ?", (user["id"],))
                tch = cursor.fetchone()
                if tch: profile.update(dict(tch))

            logger.info(f"LOGIN SUCCESS: User '{user['username']}' authenticated with role [{user['role']}].")
            log_audit(conn, user["username"], "LOGIN", "USER", user["id"], f"Successful login with role {user['role']} from IP {self.client_address[0]}")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "data": profile})
            return

        # 2. Logout with Audit
        if path == "/api/auth/logout":
            username = body.get("username", "Anonymous")
            logger.info(f"LOGOUT: User '{username}' signed out.")
            log_audit(conn, username, "LOGOUT", "USER", None, f"User signed out from IP {self.client_address[0]}")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Signed out successfully"})
            return

        # 3. Add Student
        if path == "/api/students":
            adm_no = body.get("admission_number", "").strip()
            first_name = body.get("first_name", "").strip()
            last_name = body.get("last_name", "").strip()
            email = body.get("email", "").strip()
            phone = body.get("phone", "").strip()
            dept_id = body.get("department_id")
            dob = body.get("date_of_birth") or None
            gender = body.get("gender") or "Other"
            address = body.get("address", "")
            adm_date = body.get("admission_date") or date.today().isoformat()
            actor = body.get("actor_name", "Admin")

            if not adm_no or not first_name or not last_name or not email:
                self.send_error_json("Admission Number, First Name, Last Name, and Email are required.")
                conn.close()
                return

            try:
                username = f"student_{adm_no.lower().replace('-', '_')}"
                default_pwd = hash_password("student123")
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, 'STUDENT')",
                    (username, email, default_pwd)
                )
                user_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO students (user_id, admission_number, first_name, last_name, date_of_birth, gender, email, phone, address, department_id, admission_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
                """, (user_id, adm_no, first_name, last_name, dob, gender, email, phone, address, dept_id, adm_date))
                stu_id = cursor.lastrowid

                logger.info(f"STUDENT CREATED: {first_name} {last_name} ({adm_no}) by {actor}")
                log_audit(conn, actor, "CREATE", "STUDENT", stu_id, f"Registered new student {first_name} {last_name} ({adm_no})")
                conn.commit()
                self.send_json({"success": True, "message": "Student created successfully", "data": {"id": stu_id, "user_id": user_id}})
            except sqlite3.IntegrityError as e:
                conn.rollback()
                logger.warning(f"Integrity error registering student: {e}")
                self.send_error_json(f"Student with admission number or email already exists.")
            conn.close()
            return

        # 4. Add Teacher
        if path == "/api/teachers":
            emp_no = body.get("employee_number", "").strip()
            first_name = body.get("first_name", "").strip()
            last_name = body.get("last_name", "").strip()
            email = body.get("email", "").strip()
            phone = body.get("phone", "").strip()
            dept_id = body.get("department_id")
            designation = body.get("designation", "Faculty")
            actor = body.get("actor_name", "Admin")

            if not emp_no or not first_name or not last_name or not email:
                self.send_error_json("Employee Number, Name, and Email are required.")
                conn.close()
                return

            try:
                username = f"teacher_{emp_no.lower().replace('-', '_')}"
                default_pwd = hash_password("teacher123")
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, 'TEACHER')",
                    (username, email, default_pwd)
                )
                user_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO teachers (user_id, employee_number, first_name, last_name, department_id, designation, email, phone, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
                """, (user_id, emp_no, first_name, last_name, dept_id, designation, email, phone))
                teacher_id = cursor.lastrowid

                logger.info(f"FACULTY ADDED: {first_name} {last_name} ({emp_no}) by {actor}")
                log_audit(conn, actor, "CREATE", "TEACHER", teacher_id, f"Added faculty {first_name} {last_name} ({emp_no})")
                conn.commit()
                self.send_json({"success": True, "message": "Teacher created successfully", "data": {"id": teacher_id}})
            except sqlite3.IntegrityError as e:
                conn.rollback()
                self.send_error_json(f"Teacher already exists: {str(e)}")
            conn.close()
            return

        # 5. Add Course
        if path == "/api/courses":
            code = body.get("code", "").strip().upper()
            name = body.get("name", "").strip()
            dept_id = body.get("department_id")
            credits = float(body.get("credits", 3.0))
            description = body.get("description", "")
            actor = body.get("actor_name", "Admin")

            try:
                cursor.execute("""
                    INSERT INTO courses (code, name, department_id, credits, description, active)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (code, name, dept_id, credits, description))
                course_id = cursor.lastrowid
                logger.info(f"COURSE ADDED: {code} - {name} by {actor}")
                log_audit(conn, actor, "CREATE", "COURSE", course_id, f"Added course {code} - {name}")
                conn.commit()
                self.send_json({"success": True, "message": "Course created successfully", "data": {"id": course_id}})
            except sqlite3.IntegrityError:
                conn.rollback()
                self.send_error_json("Course with this code already exists.")
            conn.close()
            return

        # 6. Add Class Offering
        if path == "/api/offerings":
            course_id = body.get("course_id")
            session_id = body.get("academic_session_id", 1)
            teacher_id = body.get("teacher_id")
            section = body.get("section", "A")
            semester = body.get("semester", "Semester 1")
            capacity = int(body.get("capacity", 60))
            actor = body.get("actor_name", "Admin")

            try:
                cursor.execute("""
                    INSERT INTO class_offerings (course_id, academic_session_id, teacher_id, section, semester, capacity, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
                """, (course_id, session_id, teacher_id, section, semester, capacity))
                offering_id = cursor.lastrowid
                logger.info(f"OFFERING CREATED: Course #{course_id} Sec {section} by {actor}")
                log_audit(conn, actor, "CREATE", "CLASS_OFFERING", offering_id, f"Created class offering for course #{course_id} section {section}")
                conn.commit()
                self.send_json({"success": True, "message": "Class offering created", "data": {"id": offering_id}})
            except sqlite3.IntegrityError:
                conn.rollback()
                self.send_error_json("An offering for this course, session, and section already exists.")
            conn.close()
            return

        # 7. Enroll Student
        if path == "/api/enrollments":
            student_id = body.get("student_id")
            offering_id = body.get("class_offering_id")
            actor = body.get("actor_name", "Admin")

            try:
                cursor.execute("""
                    INSERT INTO enrollments (student_id, class_offering_id, status)
                    VALUES (?, ?, 'ACTIVE')
                """, (student_id, offering_id))
                eid = cursor.lastrowid
                logger.info(f"ENROLLMENT: Student #{student_id} into offering #{offering_id} by {actor}")
                log_audit(conn, actor, "ENROLL", "ENROLLMENT", eid, f"Enrolled student #{student_id} into offering #{offering_id}")
                conn.commit()
                self.send_json({"success": True, "message": "Student enrolled successfully", "data": {"id": eid}})
            except sqlite3.IntegrityError:
                conn.rollback()
                self.send_error_json("Student is already enrolled in this course offering.")
            conn.close()
            return

        # 8. Create Class Session
        if path == "/api/attendance/sessions":
            offering_id = body.get("class_offering_id")
            session_date = body.get("session_date") or date.today().isoformat()
            topic = body.get("topic", "Lecture")
            actor = body.get("actor_name", "Teacher")

            cursor.execute("""
                INSERT INTO class_sessions (class_offering_id, session_date, topic)
                VALUES (?, ?, ?)
            """, (offering_id, session_date, topic))
            session_id = cursor.lastrowid
            logger.info(f"SESSION CREATED: Offering #{offering_id} Date {session_date} by {actor}")
            log_audit(conn, actor, "CREATE", "CLASS_SESSION", session_id, f"Created session for offering #{offering_id} on {session_date}")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Class session created", "data": {"id": session_id}})
            return

        # 9. Save Attendance Batch
        if path == "/api/attendance/save":
            session_id = body.get("class_session_id")
            records = body.get("records", [])
            actor = body.get("actor_name", "Teacher")

            for item in records:
                stu_id = item.get("student_id")
                st = item.get("status", "PRESENT")
                cursor.execute("""
                    INSERT INTO attendance (class_session_id, student_id, status, marked_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(class_session_id, student_id)
                    DO UPDATE SET status = excluded.status, marked_at = CURRENT_TIMESTAMP
                """, (session_id, stu_id, st))

            logger.info(f"ATTENDANCE MARKED: Session #{session_id} - {len(records)} students by {actor}")
            log_audit(conn, actor, "ATTENDANCE", "SESSION", session_id, f"Marked attendance for {len(records)} students in session #{session_id}")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": f"Saved attendance for {len(records)} students"})
            return

        # 10. Create Assessment
        if path == "/api/assessments":
            offering_id = body.get("class_offering_id")
            name = body.get("name", "").strip()
            atype = body.get("assessment_type", "EXAM")
            adate = body.get("assessment_date") or date.today().isoformat()
            max_marks = float(body.get("max_marks", 100))
            actor = body.get("actor_name", "Teacher")

            cursor.execute("""
                INSERT INTO assessments (class_offering_id, name, assessment_type, assessment_date, max_marks, published)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (offering_id, name, atype, adate, max_marks))
            aid = cursor.lastrowid
            logger.info(f"ASSESSMENT CREATED: '{name}' Max {max_marks} by {actor}")
            log_audit(conn, actor, "CREATE", "ASSESSMENT", aid, f"Created assessment '{name}' (Max: {max_marks})")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Assessment created", "data": {"id": aid}})
            return

        # 11. Publish Assessment
        if path.startswith("/api/assessments/") and path.endswith("/publish"):
            aid = int(path.split("/")[3])
            published = 1 if body.get("published", True) else 0
            actor = body.get("actor_name", "Teacher")

            cursor.execute("UPDATE assessments SET published = ? WHERE id = ?", (published, aid))
            action_name = "PUBLISH" if published == 1 else "UNPUBLISH"
            logger.info(f"ASSESSMENT {action_name}: Assessment #{aid} by {actor}")
            log_audit(conn, actor, action_name, "ASSESSMENT", aid, f"{action_name} assessment #{aid} published={published}")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": f"Assessment result publication updated to {published == 1}"})
            return

        # 12. Save Marks Batch
        if path == "/api/marks/save":
            aid = body.get("assessment_id")
            marks_list = body.get("marks", [])
            actor = body.get("actor_name", "Teacher")

            cursor.execute("SELECT max_marks FROM assessments WHERE id = ?", (aid,))
            ass = cursor.fetchone()
            if not ass:
                self.send_error_json("Assessment not found", 404)
                conn.close()
                return

            max_m = ass["max_marks"]
            for item in marks_list:
                stu_id = item.get("student_id")
                obt = float(item.get("marks_obtained", 0.0))
                if obt < 0 or obt > max_m:
                    conn.close()
                    self.send_error_json(f"Marks {obt} out of range (0 - {max_m})")
                    return

                cursor.execute("""
                    INSERT INTO marks (assessment_id, student_id, marks_obtained, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(assessment_id, student_id)
                    DO UPDATE SET marks_obtained = excluded.marks_obtained, updated_at = CURRENT_TIMESTAMP
                """, (aid, stu_id, obt))

            logger.info(f"MARKS RECORDED: Assessment #{aid} for {len(marks_list)} students by {actor}")
            log_audit(conn, actor, "MARKS", "ASSESSMENT", aid, f"Saved marks for {len(marks_list)} students in assessment #{aid}")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": f"Saved marks for {len(marks_list)} students"})
            return

        self.send_error_json("Endpoint Not Found", 404)
        conn.close()

    def handle_api_put(self, path):
        body = self.read_json_body()
        conn = get_db()
        cursor = conn.cursor()

        if path.startswith("/api/students/"):
            stu_id = int(path.split("/")[3])
            first_name = body.get("first_name", "").strip()
            last_name = body.get("last_name", "").strip()
            email = body.get("email", "").strip()
            phone = body.get("phone", "").strip()
            address = body.get("address", "")
            dept_id = body.get("department_id")
            actor = body.get("actor_name", "Admin")

            cursor.execute("""
                UPDATE students
                SET first_name=?, last_name=?, email=?, phone=?, address=?, department_id=?
                WHERE id=?
            """, (first_name, last_name, email, phone, address, dept_id, stu_id))
            logger.info(f"STUDENT UPDATED: Student #{stu_id} by {actor}")
            log_audit(conn, actor, "UPDATE", "STUDENT", stu_id, f"Updated profile for student #{stu_id}")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Student updated successfully"})
            return

        self.send_error_json("Endpoint Not Found", 404)
        conn.close()

    def handle_api_patch(self, path):
        body = self.read_json_body()
        conn = get_db()
        cursor = conn.cursor()

        if path.startswith("/api/students/") and path.endswith("/status"):
            stu_id = int(path.split("/")[3])
            new_status = body.get("status", "ACTIVE")
            actor = body.get("actor_name", "Admin")

            cursor.execute("UPDATE students SET status=? WHERE id=?", (new_status, stu_id))
            logger.info(f"STUDENT STATUS: Student #{stu_id} changed to {new_status} by {actor}")
            log_audit(conn, actor, "STATUS_CHANGE", "STUDENT", stu_id, f"Changed student status to {new_status}")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": f"Status updated to {new_status}"})
            return

        self.send_error_json("Endpoint Not Found", 404)
        conn.close()

    def handle_api_delete(self, path):
        conn = get_db()
        cursor = conn.cursor()

        if path.startswith("/api/enrollments/"):
            eid = int(path.split("/")[3])
            cursor.execute("DELETE FROM enrollments WHERE id=?", (eid,))
            logger.info(f"ENROLLMENT REMOVED: Enrollment #{eid}")
            log_audit(conn, "Admin", "WITHDRAW", "ENROLLMENT", eid, f"Withdrew enrollment #{eid}")
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Enrollment removed"})
            return

        self.send_error_json("Endpoint Not Found", 404)
        conn.close()

def run_server(port=PORT):
    init_db()
    server_address = ("", port)
    httpd = socketserver.TCPServer(server_address, SMSHandler)
    logger.info(f"Student Management System Server started on http://localhost:{port}/")
    print(f"============================================================")
    print(f"  Google-Style Student Management System (SMS) Backend")
    print(f"  Server URL: http://localhost:{port}/")
    print(f"  System Log: {LOG_FILE}")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
