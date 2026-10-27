-- Student Management System Baseline Schema (MySQL)
-- Based on TRD v1.0

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(500),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS teachers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNIQUE,
    employee_number VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    department_id BIGINT,
    designation VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_teachers_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_teachers_dept FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS students (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNIQUE,
    admission_number VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20),
    email VARCHAR(254),
    phone VARCHAR(30),
    address VARCHAR(500),
    department_id BIGINT,
    admission_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_students_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_students_dept FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS academic_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS courses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    department_id BIGINT,
    code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    credits DECIMAL(4,1) DEFAULT 3.0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_courses_dept FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS class_offerings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    course_id BIGINT NOT NULL,
    academic_session_id BIGINT NOT NULL,
    teacher_id BIGINT NOT NULL,
    section VARCHAR(30) DEFAULT 'A',
    semester VARCHAR(30),
    capacity INT DEFAULT 60,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT fk_offering_course FOREIGN KEY (course_id) REFERENCES courses(id),
    CONSTRAINT fk_offering_session FOREIGN KEY (academic_session_id) REFERENCES academic_sessions(id),
    CONSTRAINT fk_offering_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(id),
    CONSTRAINT uq_offering UNIQUE (course_id, academic_session_id, section)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_id BIGINT NOT NULL,
    class_offering_id BIGINT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT fk_enroll_student FOREIGN KEY (student_id) REFERENCES students(id),
    CONSTRAINT fk_enroll_offering FOREIGN KEY (class_offering_id) REFERENCES class_offerings(id),
    CONSTRAINT uq_student_enrollment UNIQUE (student_id, class_offering_id)
);

CREATE TABLE IF NOT EXISTS class_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    class_offering_id BIGINT NOT NULL,
    session_date DATE NOT NULL,
    topic VARCHAR(200),
    created_by_user_id BIGINT,
    CONSTRAINT fk_session_offering FOREIGN KEY (class_offering_id) REFERENCES class_offerings(id),
    CONSTRAINT fk_session_user FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    class_session_id BIGINT NOT NULL,
    student_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_att_session FOREIGN KEY (class_session_id) REFERENCES class_sessions(id),
    CONSTRAINT fk_att_student FOREIGN KEY (student_id) REFERENCES students(id),
    CONSTRAINT uq_session_student_att UNIQUE (class_session_id, student_id)
);

CREATE TABLE IF NOT EXISTS assessments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    class_offering_id BIGINT NOT NULL,
    name VARCHAR(150) NOT NULL,
    assessment_type VARCHAR(40) NOT NULL,
    assessment_date DATE,
    max_marks DECIMAL(7,2) NOT NULL,
    published BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_teacher_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_assess_offering FOREIGN KEY (class_offering_id) REFERENCES class_offerings(id),
    CONSTRAINT fk_assess_teacher FOREIGN KEY (created_by_teacher_id) REFERENCES teachers(id)
);

CREATE TABLE IF NOT EXISTS marks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    assessment_id BIGINT NOT NULL,
    student_id BIGINT NOT NULL,
    marks_obtained DECIMAL(7,2) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_marks_assessment FOREIGN KEY (assessment_id) REFERENCES assessments(id),
    CONSTRAINT fk_marks_student FOREIGN KEY (student_id) REFERENCES students(id),
    CONSTRAINT uq_assessment_student_mark UNIQUE (assessment_id, student_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    actor_user_id BIGINT,
    actor_name VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100),
    details TEXT,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
