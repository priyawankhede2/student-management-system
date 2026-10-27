# Technical Requirements Document (TRD)
## Student Management System — Java

**Document Version:** 1.0  
**Status:** Initial Technical Baseline  
**Related Document:** `Student_Management_System_PRD.md`  
**Application Type:** Web application  
**Primary Stack:** Java 21, Spring Boot, Spring Security, Spring Data JPA, MySQL, Thymeleaf, Maven

---

## 1. Purpose

This Technical Requirements Document (TRD) translates the Student Management System PRD into a technical implementation plan. It defines the proposed architecture, technology stack, package structure, database model, application behavior, security controls, API contracts, testing approach, and delivery sequence.

This document is an implementation baseline. Confirm institutional rules—especially attendance calculation, grading, enrollment, retention, and user provisioning—before treating them as final.

## 2. Technical Goals

The application must:

1. Provide separate, authenticated workflows for administrators, teachers, and students.
2. Persist student and academic records in MySQL.
3. Enforce business rules in the backend, not only in the UI.
4. Protect student records with role-based and record-level authorization.
5. Be testable, maintainable, and deployable using repeatable steps.
6. Support future modules without tightly coupling them to the presentation layer.

## 3. Scope and Assumptions

### 3.1 MVP Modules

- Authentication and account management
- Student management
- Teacher management
- Department and course management
- Academic sessions and class offerings
- Student enrollment
- Class sessions and attendance
- Assessments and marks
- Result publication and viewing
- Dashboards and reports
- Audit logging

### 3.2 Assumptions

- The first release is a single-institution web application.
- The initial UI uses Thymeleaf, HTML, CSS, Bootstrap, and JavaScript.
- MySQL is the relational database.
- An administrator provisions initial user accounts.
- Fees, parent accounts, online payments, messaging integrations, and native mobile apps are out of scope for the MVP.
- Java 21 LTS is the target runtime; select a compatible, supported Spring Boot release when creating the project.

---

## 4. Technology Stack

| Area | Technology | Usage |
|---|---|---|
| Language | Java 21 LTS | Application code |
| Framework | Spring Boot | Application configuration and dependency integration |
| Web | Spring MVC | HTTP routes and request handling |
| Views | Thymeleaf | Server-rendered pages |
| UI | HTML, CSS, Bootstrap, JavaScript | Responsive interface |
| Security | Spring Security | Authentication, authorization, session security |
| Persistence | Spring Data JPA / Hibernate | Object-relational mapping |
| Database | MySQL 8.x | Persistent storage |
| Validation | Jakarta Bean Validation | Request and field validation |
| Build | Maven | Dependency management and builds |
| Migration | Flyway | Version-controlled database migrations |
| Testing | JUnit 5, Mockito, Spring Boot Test | Automated tests |
| Integration testing | Testcontainers (recommended) | Tests against a real MySQL-compatible environment |
| API testing | Postman or Bruno | Manual endpoint verification |
| Version control | Git | Change tracking |
| CI | GitHub Actions (optional) | Automated build and tests |
| Deployment | Executable JAR; Docker optional | Runtime packaging |

Use Spring Initializr to generate the initial project. Pin compatible dependency versions through the Spring Boot dependency management system rather than independently selecting arbitrary versions.

---

## 5. Architecture

### 5.1 Architecture Style

Use a layered monolithic application for the MVP. This is simpler to develop and deploy than microservices and is sufficient for the expected initial scope.

```text
Browser
   |
   v
Thymeleaf Pages / Spring MVC Controllers
   |
   v
Application Services (business rules, transactions)
   |
   v
Spring Data JPA Repositories
   |
   v
MySQL Database
```

Cross-cutting concerns include Spring Security, validation, exception handling, logging, and audit events.

### 5.2 Layer Responsibilities

**Presentation**
- Renders pages and forms.
- Displays validation and business errors.
- Does not implement business rules or directly access repositories.

**Controller**
- Maps HTTP requests to application operations.
- Validates request objects.
- Calls service methods and chooses a view or redirect.
- Does not contain substantial business logic.

**Service**
- Enforces business rules and authorization-related ownership checks.
- Coordinates repositories.
- Uses transactions for multi-step writes.
- Calculates attendance and result summaries.

**Repository**
- Performs database reads and writes.
- Provides explicit queries and pagination.
- Does not contain presentation logic.

**Domain / Entity**
- Represents persisted concepts and relationships.
- Defines appropriate constraints and state.
- Avoids exposing entities directly as external API payloads.

**DTO**
- Carries form and request data.
- Uses validation annotations.
- Prevents accidental mass assignment of protected fields.

---

## 6. Suggested Project Structure

```text
student-management-system/
├── pom.xml
├── README.md
├── .gitignore
├── .env.example
├── src/
│   ├── main/
│   │   ├── java/com/example/sms/
│   │   │   ├── StudentManagementApplication.java
│   │   │   ├── config/
│   │   │   │   └── SecurityConfig.java
│   │   │   ├── security/
│   │   │   │   ├── CustomUserDetailsService.java
│   │   │   │   └── CurrentUserService.java
│   │   │   ├── controller/
│   │   │   │   ├── AuthController.java
│   │   │   │   ├── DashboardController.java
│   │   │   │   ├── StudentController.java
│   │   │   │   ├── TeacherController.java
│   │   │   │   ├── CourseController.java
│   │   │   │   ├── EnrollmentController.java
│   │   │   │   ├── AttendanceController.java
│   │   │   │   ├── AssessmentController.java
│   │   │   │   ├── ResultController.java
│   │   │   │   └── ReportController.java
│   │   │   ├── service/
│   │   │   │   ├── StudentService.java
│   │   │   │   ├── TeacherService.java
│   │   │   │   ├── CourseService.java
│   │   │   │   ├── EnrollmentService.java
│   │   │   │   ├── AttendanceService.java
│   │   │   │   ├── AssessmentService.java
│   │   │   │   ├── ResultService.java
│   │   │   │   └── AuditService.java
│   │   │   ├── repository/
│   │   │   ├── entity/
│   │   │   ├── dto/
│   │   │   ├── mapper/
│   │   │   ├── exception/
│   │   │   └── validation/
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── db/migration/
│   │       ├── templates/
│   │       │   ├── auth/
│   │       │   ├── dashboard/
│   │       │   ├── students/
│   │       │   ├── teachers/
│   │       │   ├── courses/
│   │       │   ├── attendance/
│   │       │   ├── assessments/
│   │       │   ├── results/
│   │       │   └── reports/
│   │       └── static/
│   │           ├── css/
│   │           ├── js/
│   │           └── images/
│   └── test/
│       └── java/com/example/sms/
│           ├── controller/
│           ├── service/
│           ├── repository/
│           └── security/
└── docs/
    ├── PRD.md
    ├── TRD.md
    └── diagrams/
```

Replace `com.example.sms` with the final organization or project package name before implementation. Keep package names lowercase.

---

## 7. Domain Model and Database Design

Use generated numeric IDs or UUIDs consistently. For a conventional MySQL project, `BIGINT` generated IDs are acceptable. Store timestamps consistently and configure the application's time zone deliberately.

### 7.1 Core Tables

#### `users`

| Column | Suggested Type | Constraints / Notes |
|---|---|---|
| `id` | BIGINT | Primary key, generated |
| `username` | VARCHAR(80) | Not null, unique |
| `email` | VARCHAR(254) | Not null, unique if institutional policy requires |
| `password_hash` | VARCHAR(255) | Not null; never store plaintext |
| `role` | VARCHAR(20) | Not null; ADMIN, TEACHER, STUDENT |
| `enabled` | BOOLEAN | Not null, default true |
| `created_at` | TIMESTAMP | Not null |
| `updated_at` | TIMESTAMP | Not null |

Use an enum or validated role mapping. If the system later needs multiple roles per account, replace the single role field with normalized user-role tables through a planned migration.

#### `students`

| Column | Suggested Type | Constraints / Notes |
|---|---|---|
| `id` | BIGINT | Primary key |
| `user_id` | BIGINT | Foreign key to `users`, unique if one account per student |
| `admission_number` | VARCHAR(50) | Not null, unique |
| `first_name` | VARCHAR(100) | Not null |
| `last_name` | VARCHAR(100) | Not null |
| `date_of_birth` | DATE | Nullable if not required |
| `email` | VARCHAR(254) | Optional contact email |
| `phone` | VARCHAR(30) | Optional; store as text |
| `address` | VARCHAR(500) | Optional |
| `department_id` | BIGINT | Foreign key, nullable if not assigned |
| `admission_date` | DATE | Not null |
| `status` | VARCHAR(20) | ACTIVE, INACTIVE, GRADUATED, WITHDRAWN |
| `created_at` | TIMESTAMP | Not null |
| `updated_at` | TIMESTAMP | Not null |

#### `teachers`

| Column | Suggested Type | Constraints / Notes |
|---|---|---|
| `id` | BIGINT | Primary key |
| `user_id` | BIGINT | Foreign key to `users`, unique |
| `employee_number` | VARCHAR(50) | Not null, unique |
| `first_name` | VARCHAR(100) | Not null |
| `last_name` | VARCHAR(100) | Not null |
| `department_id` | BIGINT | Foreign key |
| `designation` | VARCHAR(100) | Optional |
| `status` | VARCHAR(20) | ACTIVE, INACTIVE |
| `created_at` | TIMESTAMP | Not null |
| `updated_at` | TIMESTAMP | Not null |

#### `departments`

- `id` BIGINT primary key
- `code` VARCHAR(30), unique and not null
- `name` VARCHAR(150), unique within the chosen institutional policy
- `description` VARCHAR(500), optional
- `active` BOOLEAN, not null

#### `courses`

- `id` BIGINT primary key
- `department_id` BIGINT foreign key
- `code` VARCHAR(30), unique and not null
- `name` VARCHAR(150), not null
- `description` TEXT, optional
- `credits` DECIMAL(4,1), optional
- `active` BOOLEAN, not null

#### `academic_sessions`

- `id` BIGINT primary key
- `name` VARCHAR(80), unique and not null (for example, an academic year)
- `start_date` DATE, not null
- `end_date` DATE, not null
- `active` BOOLEAN, not null

Validation: `end_date` must be on or after `start_date`. The rule for which session is active must be defined institutionally.

#### `class_offerings`

Represents a course delivered to a particular group during an academic session.

- `id` BIGINT primary key
- `course_id` BIGINT foreign key, not null
- `academic_session_id` BIGINT foreign key, not null
- `teacher_id` BIGINT foreign key to `teachers`, not null
- `section` VARCHAR(30), optional
- `semester` VARCHAR(30), optional
- `capacity` INT, optional and positive when set
- `status` VARCHAR(20), not null

Add a unique constraint based on the agreed business key, such as course, academic session, and section. Confirm whether multiple teachers or sections require a different model.

#### `enrollments`

- `id` BIGINT primary key
- `student_id` BIGINT foreign key, not null
- `class_offering_id` BIGINT foreign key, not null
- `enrolled_at` TIMESTAMP, not null
- `status` VARCHAR(20), not null: ACTIVE, WITHDRAWN, COMPLETED

Enforce uniqueness for `(student_id, class_offering_id)` if re-enrollment is not represented as multiple historical rows. If the institution needs multiple enrollment attempts, use a separate history model or a carefully defined versioned enrollment policy.

#### `class_sessions`

- `id` BIGINT primary key
- `class_offering_id` BIGINT foreign key, not null
- `session_date` DATE, not null
- `start_time` TIME, optional
- `end_time` TIME, optional
- `topic` VARCHAR(200), optional
- `created_by_user_id` BIGINT foreign key to `users`, not null

Validate that the end time is later than the start time when both are supplied. Decide whether a class offering can have multiple sessions on one date before defining a uniqueness constraint.

#### `attendance`

- `id` BIGINT primary key
- `class_session_id` BIGINT foreign key, not null
- `student_id` BIGINT foreign key, not null
- `status` VARCHAR(20), not null: PRESENT, ABSENT, LATE, EXCUSED
- `marked_by_user_id` BIGINT foreign key to `users`, not null
- `marked_at` TIMESTAMP, not null
- `updated_at` TIMESTAMP, not null

Enforce uniqueness for `(class_session_id, student_id)`. Validate that the student has an active or otherwise eligible enrollment in the class offering before saving attendance.

#### `assessments`

- `id` BIGINT primary key
- `class_offering_id` BIGINT foreign key, not null
- `name` VARCHAR(150), not null
- `assessment_type` VARCHAR(40), not null
- `assessment_date` DATE, optional
- `max_marks` DECIMAL(7,2), not null and greater than zero
- `published` BOOLEAN, not null, default false
- `created_by_teacher_id` BIGINT foreign key to `teachers`, not null
- `created_at` TIMESTAMP, not null
- `updated_at` TIMESTAMP, not null

#### `marks`

- `id` BIGINT primary key
- `assessment_id` BIGINT foreign key, not null
- `student_id` BIGINT foreign key, not null
- `marks_obtained` DECIMAL(7,2), not null
- `entered_by_user_id` BIGINT foreign key to `users`, not null
- `created_at` TIMESTAMP, not null
- `updated_at` TIMESTAMP, not null

Enforce uniqueness for `(assessment_id, student_id)`. Validate `0 <= marks_obtained <= assessments.max_marks` in the service layer and in any additional database constraints that can be maintained safely. The service must also verify enrollment in the relevant class offering.

#### `audit_logs`

- `id` BIGINT primary key
- `actor_user_id` BIGINT foreign key to `users`, nullable for certain system events
- `action` VARCHAR(100), not null
- `entity_type` VARCHAR(100), not null
- `entity_id` VARCHAR(100), optional
- `occurred_at` TIMESTAMP, not null
- `details` JSON or TEXT, limited to approved, non-sensitive change metadata
- `request_id` VARCHAR(100), optional

Never log passwords, session identifiers, access tokens, or unnecessary sensitive personal data. Restrict audit-log access and consider append-only permissions for the application account.

### 7.2 Relationship Summary

- One department has many students, teachers, and courses.
- One course has many class offerings.
- One academic session has many class offerings.
- One teacher can be assigned to many class offerings.
- Students and class offerings are linked through enrollments.
- One class offering has many class sessions and assessments.
- One class session has attendance records for students.
- One assessment has marks records for students.
- A user account is linked to a student or teacher profile where appropriate.

### 7.3 Indexing

Create indexes for frequent lookups, including:
- `students.admission_number` (unique index)
- `students.last_name` and/or other approved search fields
- `teachers.employee_number` (unique index)
- `courses.code` (unique index)
- `enrollments.student_id`
- `enrollments.class_offering_id`
- `class_sessions.class_offering_id, session_date`
- `attendance.class_session_id, student_id` (unique index)
- `assessments.class_offering_id`
- `marks.assessment_id, student_id` (unique index)
- Foreign-key columns used in joins

Confirm indexes using query plans and realistic data rather than adding indexes indiscriminately.

---

## 8. Entity and Relationship Rules

1. Use JPA `@ManyToOne`, `@OneToMany`, and other mappings only where useful.
2. Avoid unrestricted bidirectional entity graphs that cause recursive JSON serialization.
3. Prefer DTOs for forms and API responses.
4. Avoid `CascadeType.REMOVE` across historical academic relationships unless deletion behavior is explicitly approved.
5. Use `BigDecimal` for marks and credits when fractional values are supported.
6. Store phone numbers as strings, not numeric types.
7. Use enums or validated constants for statuses.
8. Use optimistic locking (`@Version`) for records where concurrent edits could overwrite important data.
9. Do not rely only on Java validation for uniqueness; enforce uniqueness in MySQL too.
10. Define a consistent archival and retention policy before enabling record deletion.

---

## 9. Package and Class Responsibilities

| Package / Class | Responsibility |
|---|---|
| `config.SecurityConfig` | Configure login, logout, access rules, CSRF, and password encoder |
| `security.CustomUserDetailsService` | Load user accounts for Spring Security |
| `security.CurrentUserService` | Resolve the authenticated user safely |
| `controller.*Controller` | Handle routes, bind forms, validate input, return views |
| `service.StudentService` | Student creation, updates, search, and status changes |
| `service.TeacherService` | Teacher administration |
| `service.CourseService` | Departments, courses, sessions, and offerings |
| `service.EnrollmentService` | Enrollment rules and history |
| `service.AttendanceService` | Class sessions, attendance, and summaries |
| `service.AssessmentService` | Assessment setup and marks entry |
| `service.ResultService` | Result publication and student result retrieval |
| `service.AuditService` | Record approved audit events |
| `repository.*Repository` | Persistence queries |
| `dto.*` | Form and response models |
| `exception.GlobalExceptionHandler` | Consistent error handling |
| `mapper.*Mapper` | Map between entities and DTOs where useful |

Suggested repository interfaces include `UserRepository`, `StudentRepository`, `TeacherRepository`, `DepartmentRepository`, `CourseRepository`, `AcademicSessionRepository`, `ClassOfferingRepository`, `EnrollmentRepository`, `ClassSessionRepository`, `AttendanceRepository`, `AssessmentRepository`, `MarksRepository`, and `AuditLogRepository`.

---

## 10. Authentication and Authorization

### 10.1 Authentication

- Use Spring Security form login for the Thymeleaf MVP.
- Store only password hashes generated by a configured `PasswordEncoder`.
- Prefer a secure adaptive hash such as BCrypt or Argon2.
- Use generic login failure messages to avoid revealing whether a username exists.
- Disable login for disabled accounts.
- Apply session fixation protection and secure session settings.
- Configure session cookies as `HttpOnly` and `Secure` in HTTPS production deployments.
- Provide password reset only after a verified identity workflow is designed.
- Rate-limit or otherwise protect repeated login failures at the application or infrastructure layer.

### 10.2 Authorization

Use role rules such as:
- `ROLE_ADMIN`: institution-level administration.
- `ROLE_TEACHER`: assigned classes, attendance, assessments, and permitted marks operations.
- `ROLE_STUDENT`: own profile fields permitted by policy, own attendance, and own published results.

Authorization must be checked on every server-side operation. Hiding a button or link is not authorization.

### 10.3 Record-Level Access

- Students must only retrieve their own profile, attendance, and results.
- Teachers must only manage assigned class offerings unless explicitly granted additional permission.
- Administrators may access institution-level records according to policy.
- The backend must derive the current user's identity from the authenticated session, not trust a user ID supplied by the browser.

### 10.4 Browser Security

- Keep CSRF protection enabled for session-authenticated state-changing forms.
- Use Thymeleaf's escaped output by default; avoid unescaped output for user-controlled values.
- Validate inputs on the server.
- Use HTTPS in deployed environments.
- Do not place secrets in source code, templates, URLs, or logs.
- Use secure headers appropriate to the deployment.
- Keep dependencies updated and scan for known vulnerabilities.

---

## 11. Validation and Business Logic

Use Jakarta Bean Validation on DTOs and repeat essential rules in service methods.

| Field / Operation | Validation |
|---|---|
| Admission number | Required, length limit, unique |
| Employee number | Required, length limit, unique |
| Email | Valid format and uniqueness according to policy |
| Student name | Required, sensible length limits |
| Academic session | End date must not precede start date |
| Enrollment | Student and offering must exist; duplicate enrollment rejected |
| Attendance | Valid status; student enrolled in the offering; no duplicate session record |
| Assessment maximum marks | Greater than zero |
| Marks | Non-negative and not above maximum marks |
| Result visibility | Only published results are visible to students |
| Status changes | Valid transition and authorized actor |
| Search / pagination | Bounded page size and validated filters |

Validation errors should be presented in a clear, field-specific manner. Database constraint violations should be translated into safe user-facing messages.

---

## 12. Attendance and Result Calculations

### 12.1 Attendance

Define the institution's policy before implementation. A possible default is:

`attendance percentage = eligible attended sessions / eligible total sessions × 100`

The product owner must specify:
- Whether `LATE` counts as attended.
- Whether `EXCUSED` sessions are excluded from the denominator.
- How cancelled sessions are handled.
- Whether attendance can be edited after a deadline.
- Whether attendance is calculated per course offering, semester, or academic session.

Use decimal arithmetic and define rounding rules. Avoid dividing by zero; when no eligible sessions exist, display “Not available” or the agreed equivalent.

### 12.2 Results

- Validate marks against each assessment's maximum marks.
- Calculate percentages only according to approved rules.
- Keep grade boundaries and pass criteria configurable.
- Do not show unpublished results to students.
- Restrict changes after publication to a documented correction workflow.
- Record who published or corrected a result and when.

If result publication needs stronger traceability, add a result-publication history table rather than relying only on a boolean field.

---

## 13. Web Routes / API Contract

The MVP may use server-rendered MVC routes. Suggested route groups:

| Method | Route | Access | Purpose |
|---|---|---|---|
| `GET` | `/login` | Public | Login page |
| `POST` | Spring Security login processing route | Public | Authenticate user |
| `POST` | Spring Security logout route | Authenticated | Logout |
| `GET` | `/admin/dashboard` | ADMIN | Admin dashboard |
| `GET` | `/admin/students` | ADMIN | Student list |
| `GET` | `/admin/students/new` | ADMIN | Student creation form |
| `POST` | `/admin/students` | ADMIN | Create student |
| `GET` | `/admin/students/{id}/edit` | ADMIN | Edit form |
| `POST` or `PUT` | `/admin/students/{id}` | ADMIN | Update student |
| `GET` | `/admin/teachers` | ADMIN | Teacher list |
| `GET` | `/admin/courses` | ADMIN | Course and offering management |
| `GET` | `/teacher/dashboard` | TEACHER | Teacher dashboard |
| `GET` | `/teacher/classes/{offeringId}/attendance` | Assigned teacher | Attendance page |
| `POST` | `/teacher/classes/{offeringId}/attendance` | Assigned teacher | Save attendance |
| `GET` | `/teacher/classes/{offeringId}/assessments` | Assigned teacher | Assessments |
| `POST` | `/teacher/assessments` | Authorized teacher | Create assessment |
| `POST` | `/teacher/assessments/{id}/marks` | Assigned teacher | Save marks |
| `POST` | `/teacher/assessments/{id}/publish` | Authorized teacher/admin | Publish results |
| `GET` | `/student/dashboard` | STUDENT | Student dashboard |
| `GET` | `/student/profile` | STUDENT | Own profile |
| `GET` | `/student/attendance` | STUDENT | Own attendance |
| `GET` | `/student/results` | STUDENT | Own published results |

Use Spring Security's configured login and logout endpoints rather than writing custom credential handling unnecessarily. Choose one consistent HTTP method and form-handling pattern for each route.

If a REST API is later introduced, use versioned routes such as `/api/v1/students`, DTOs, pagination, standardized error responses, and the same authorization rules.

---

## 14. Error Handling and Logging

### 14.1 Error Handling

- Use centralized exception handling for MVC and REST responses.
- Return user-friendly messages for expected validation errors.
- Do not expose SQL, stack traces, internal paths, or secrets.
- Distinguish validation errors, not-found errors, forbidden operations, and unexpected failures.
- Log unexpected exceptions with a correlation/request ID where feasible.

### 14.2 Logging

- Use structured application logs where practical.
- Record security-relevant events without logging credentials or tokens.
- Restrict log access.
- Define log retention and rotation.
- Audit high-impact changes to student profiles, attendance, marks, roles, and publication status.

Audit logging should not silently fail for critical changes. Decide whether audit records are written in the same transaction or through a reliable event mechanism.

---

## 15. Configuration and Secrets

Use profile-specific configuration:
- `application.yml` for safe defaults.
- `application-dev.yml` for local development settings.
- `application-test.yml` for tests.
- `application-prod.yml` for production-specific non-secret settings.

Supply secrets through environment variables or a secret manager. Do not commit `.env` files containing credentials.

Example environment variable names:

```text
SPRING_DATASOURCE_URL
SPRING_DATASOURCE_USERNAME
SPRING_DATASOURCE_PASSWORD
APP_ADMIN_BOOTSTRAP_ENABLED
```

Do not commit real database passwords. Disable development-only bootstrap behavior in production unless the process has been explicitly designed and secured.

Use Flyway migrations to evolve the database. In production, prefer schema migration scripts over automatic schema creation or destructive update behavior.

---

## 16. Testing Strategy

### 16.1 Unit Tests

Test service rules with JUnit and Mockito:
- Duplicate admission number rejection.
- Enrollment validation.
- Attendance percentage calculations.
- Marks boundary validation.
- Result publication rules.
- Role and ownership decisions.

### 16.2 Repository Tests

Test:
- Unique constraints.
- Foreign-key relationships.
- Filtering and pagination queries.
- Attendance and marks uniqueness.
- Query correctness against MySQL-compatible behavior.

### 16.3 Integration Tests

Test full flows:
- Login and role-based routing.
- Create, update, search, and deactivate a student.
- Enroll a student.
- Record attendance and calculate summaries.
- Create an assessment, enter marks, and publish results.
- Verify unauthorized requests are rejected.
- Verify transaction rollback for failed multi-step writes.

### 16.4 Security Tests

- Student attempts to access another student's record.
- Teacher attempts to edit an unassigned class.
- Student attempts to access administrator pages.
- Disabled user attempts to log in.
- Invalid or forged form submissions.
- CSRF protection on state-changing requests.
- Sensitive data is absent from user-facing errors and logs.

### 16.5 Quality Gates

A build is acceptable when:
- Compilation succeeds.
- Automated tests pass.
- Critical authorization tests pass.
- No unresolved critical or high-severity security issue remains without an approved risk decision.
- Database migrations apply cleanly to a fresh test database.
- Manual acceptance tests pass for each user role.

---

## 17. Development Environment Setup

### Prerequisites

- JDK 21
- Maven (or the Maven Wrapper included in the repository)
- MySQL 8.x
- Git
- IDE such as IntelliJ IDEA or VS Code with Java extensions

### Initial Setup

1. Generate a Spring Boot project with Spring Web, Thymeleaf, Spring Security, Spring Data JPA, Validation, MySQL Driver, Flyway, and Spring Boot Test.
2. Initialize a Git repository.
3. Configure a local database and a dedicated least-privilege database user.
4. Configure database connection values through environment variables.
5. Add the first Flyway migration.
6. Create a minimal health or landing route.
7. Run the application and verify database connectivity.
8. Add automated tests before implementing business modules.

Example commands:

```bash
./mvnw test
./mvnw spring-boot:run
./mvnw clean package
```

On Windows, use `mvnw.cmd` where needed.

---

## 18. Implementation Plan

Implement in dependency order:

### Phase 1 — Foundation
- Create project and package structure.
- Configure profiles, database connection, and Flyway.
- Add global exception handling and validation conventions.
- Establish formatting, Git workflow, and automated test execution.

**Exit criteria:** Application starts locally and migrations run against an empty database.

### Phase 2 — Identity and Security
- Create `users` and role model.
- Implement Spring Security login and logout.
- Add secure password encoding.
- Add role-based route protection.
- Add tests for access restrictions.

**Exit criteria:** Each role can log in and is restricted to authorized routes.

### Phase 3 — Academic Setup
- Implement departments, courses, academic sessions, and class offerings.
- Add repositories, services, DTOs, controllers, and views.
- Validate unique codes and relationships.

**Exit criteria:** Administrator can configure valid academic offerings.

### Phase 4 — Student and Teacher Management
- Implement profiles and account associations.
- Add create, list, search, update, and deactivate flows.
- Add server-side validation and database constraints.

**Exit criteria:** Authorized administrators can manage records without losing historical relationships.

### Phase 5 — Enrollment
- Implement enrollment workflows and history rules.
- Enforce duplicate and eligibility checks.
- Add transaction and concurrency tests where relevant.

**Exit criteria:** Students can be enrolled only in valid offerings.

### Phase 6 — Attendance
- Implement class sessions and attendance.
- Add attendance status validation and uniqueness constraints.
- Implement policy-based summary calculations.

**Exit criteria:** Authorized teachers can record attendance and view accurate summaries.

### Phase 7 — Assessments and Results
- Implement assessments and marks.
- Add mark validation, publication, and correction workflows.
- Restrict student views to their own published results.

**Exit criteria:** Results are calculated and exposed according to approved policy.

### Phase 8 — Dashboard and Reports
- Implement role-specific summaries.
- Add bounded search, filters, pagination, and CSV export if approved.
- Verify that reports obey authorization rules.

**Exit criteria:** Dashboard and reports match database records and role permissions.

### Phase 9 — Hardening and Release
- Run full automated and manual tests.
- Review dependencies and security settings.
- Verify migrations and backup restoration.
- Document deployment and operations.

**Exit criteria:** Release quality gates are satisfied.

---

## 19. Deployment Requirements

- Package the application as an executable JAR or a container image.
- Use a managed or properly maintained MySQL instance.
- Use HTTPS for all production traffic.
- Keep the database private and limit network access.
- Use separate credentials for development, test, and production.
- Run migrations as part of a controlled release process.
- Configure health checks, logs, and monitoring.
- Back up the database on a defined schedule.
- Test restore procedures and document recovery objectives.
- Avoid exposing database administration interfaces publicly.
- Document how to rotate credentials and recover a compromised account.

Docker is optional for the first local version but useful for repeatable deployments.

---

## 20. Risks and Technical Decisions

| Decision / Risk | Initial Recommendation | Revisit When |
|---|---|---|
| Monolith vs. microservices | Layered monolith | Independent scaling or team ownership becomes necessary |
| Thymeleaf vs. SPA | Thymeleaf for MVP | Separate frontend experience is required |
| Single role vs. multiple roles | One role per account initially | Users need multiple simultaneous roles |
| Hard delete vs. archive | Prefer deactivation/archival | Retention policy is finalized |
| Attendance calculation | Configurable policy | Institution approves precise rules |
| Grading | Configurable grading rules | Academic policy is supplied |
| Result audit | Audit every publication/correction | Final workflow is designed |
| Reports | CSV first; PDF optional | Output requirements are confirmed |

---

## 21. Definition of Technical Completion

The implementation is technically complete when:

- The agreed MVP modules are implemented.
- Source code follows the agreed package and layer structure.
- Database migrations are versioned and reproducible.
- Validation and business rules are enforced server-side.
- Role and record-level access tests pass.
- Sensitive values are externalized from source code.
- Critical unit, integration, and security tests pass.
- Error handling and audit logging are implemented.
- Backup and restore procedures are documented and tested.
- Build, local setup, and deployment instructions are documented.

---

## 22. Suggested Repository Deliverables

```text
student-management-system/
├── src/
├── pom.xml
├── mvnw
├── mvnw.cmd
├── .gitignore
├── .env.example
├── README.md
└── docs/
    ├── Student_Management_System_PRD.md
    ├── Student_Management_System_TRD.md
    ├── ER_DIAGRAM.md
    ├── API_SPECIFICATION.md
    ├── TEST_PLAN.md
    └── DEPLOYMENT_GUIDE.md
```

Do not include actual secrets, production data, database dumps containing personal information, or generated build output in the repository.

---

## 23. Recommended Next Step

Before writing all modules, create the ER diagram and initial Flyway migration, then implement the project foundation and authentication.

**Recommended sequence:**

`PRD → TRD → ER Diagram → Project Setup → Database Migration → Authentication → Student Management → Academic Modules → Testing → Security Review → Deployment`

This approach keeps the implementation aligned with requirements and makes each development phase verifiable.
