// Student Management System - Google Material 3 Frontend Logic

const API_BASE = "/api";

// App State
let state = {
  currentUser: null,
  departments: [],
  offerings: [],
  activeAttendanceSession: null,
  activeAttendanceSheet: [],
  activeAssessment: null,
  activeMarksSheet: [],
  currentLogsTab: "db",
  autoRefreshTimer: null
};

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
  initDateDefaults();
  checkAuthSession();
  setupGlobalSearch();
});

function initDateDefaults() {
  const today = new Date().toISOString().split("T")[0];
  const sessionDateInput = document.getElementById("sessionDateInput");
  const assessmentDate = document.getElementById("assessmentDate");
  if (sessionDateInput) sessionDateInput.value = today;
  if (assessmentDate) assessmentDate.value = today;
}

// ==========================================
// AUTHENTICATION & LOGIN WORKFLOW
// ==========================================
function checkAuthSession() {
  const savedUser = localStorage.getItem("sms_user");
  if (savedUser) {
    try {
      state.currentUser = JSON.parse(savedUser);
      showAppShell();
      return;
    } catch (e) {
      localStorage.removeItem("sms_user");
    }
  }
  // Show Login Screen
  showLoginScreen();
}

function showLoginScreen() {
  document.getElementById("loginScreen").style.display = "flex";
  document.getElementById("mainAppShell").style.display = "none";
  const errBox = document.getElementById("loginErrorAlert");
  if (errBox) errBox.style.display = "none";
}

function showAppShell() {
  document.getElementById("loginScreen").style.display = "none";
  document.getElementById("mainAppShell").style.display = "block";
  updateUserChip();
  applyRoleVisibility();
  loadDepartments();
  loadDashboard();
  loadOfferingsDropdowns();

  if (state.currentUser.role === "STUDENT") {
    navigateTo("student-portal");
  } else if (state.currentUser.role === "TEACHER") {
    navigateTo("attendance");
  } else {
    navigateTo("dashboard");
  }
}

function handleMainLogin(e) {
  e.preventDefault();
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;
  executeLogin(username, password);
}

function fillAndLogin(username, password) {
  document.getElementById("loginUsername").value = username;
  document.getElementById("loginPassword").value = password;
  executeLogin(username, password);
}

function executeLogin(username, password) {
  const btn = document.getElementById("loginSubmitBtn");
  const errBox = document.getElementById("loginErrorAlert");
  const errText = document.getElementById("loginErrorText");
  if (btn) btn.textContent = "Verifying...";
  if (errBox) errBox.style.display = "none";

  fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: username, password: password })
  })
  .then(res => res.json())
  .then(res => {
    if (btn) btn.textContent = "Sign in";
    if (res.success) {
      state.currentUser = res.data;
      if (document.getElementById("loginRememberMe").checked) {
        localStorage.setItem("sms_user", JSON.stringify(res.data));
      }
      showToast(`Welcome back, ${res.data.first_name || res.data.username}!`);
      showAppShell();
    } else {
      if (errBox && errText) {
        errText.textContent = res.error || "Invalid username or password.";
        errBox.style.display = "flex";
      }
    }
  })
  .catch(err => {
    if (btn) btn.textContent = "Sign in";
    if (errBox && errText) {
      errText.textContent = "Connection error. Is the server running?";
      errBox.style.display = "flex";
    }
  });
}

function handleLogout() {
  if (confirm("Are you sure you want to sign out?")) {
    const user = state.currentUser ? state.currentUser.username : "User";
    fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user })
    }).finally(() => {
      localStorage.removeItem("sms_user");
      state.currentUser = null;
      if (state.autoRefreshTimer) clearInterval(state.autoRefreshTimer);
      showToast("Signed out successfully.");
      showLoginScreen();
    });
  }
}

// ==========================================
// NAVIGATION & ROLE SWITCHING
// ==========================================
function navigateTo(viewId, navEl) {
  document.querySelectorAll(".view-panel").forEach(p => p.style.display = "none");
  const target = document.getElementById(`view${capitalize(viewId)}`);
  if (target) target.style.display = "block";

  document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
  if (navEl) navEl.classList.add("active");

  if (viewId === "dashboard") loadDashboard();
  else if (viewId === "students") loadStudents();
  else if (viewId === "teachers") loadTeachers();
  else if (viewId === "courses") loadCourses();
  else if (viewId === "offerings") loadOfferings();
  else if (viewId === "attendance") loadAttendanceSessions();
  else if (viewId === "assessments") loadAssessments();
  else if (viewId === "student-portal") loadStudentPortal();
  else if (viewId === "audit") {
    if (state.currentLogsTab === "console") loadLiveFileLogs();
    else loadAuditLogs();
  }
}

function capitalize(s) {
  if (!s) return "";
  if (s === "student-portal") return "StudentPortal";
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function switchRole(newRole) {
  document.getElementById("roleBtnAdmin").classList.toggle("active", newRole === "ADMIN");
  document.getElementById("roleBtnTeacher").classList.toggle("active", newRole === "TEACHER");
  document.getElementById("roleBtnStudent").classList.toggle("active", newRole === "STUDENT");

  if (newRole === "ADMIN") {
    state.currentUser = {
      id: 1, username: "admin", email: "admin@school.edu", role: "ADMIN",
      first_name: "System", last_name: "Administrator"
    };
    navigateTo("dashboard");
  } else if (newRole === "TEACHER") {
    state.currentUser = {
      id: 2, username: "teacher_sharma", email: "sharma@school.edu", role: "TEACHER",
      first_name: "Dr. Rajesh", last_name: "Sharma", teacher_id: 1
    };
    navigateTo("attendance");
  } else if (newRole === "STUDENT") {
    state.currentUser = {
      id: 4, username: "student_rahul", email: "rahul@school.edu", role: "STUDENT",
      first_name: "Rahul", last_name: "Kumar", student_id: 1, admission_number: "STU-2026-001"
    };
    navigateTo("student-portal");
  }

  localStorage.setItem("sms_user", JSON.stringify(state.currentUser));
  updateUserChip();
  applyRoleVisibility();
  showToast(`Switched active profile to ${newRole} mode`);
}

function updateUserChip() {
  if (!state.currentUser) return;
  const u = state.currentUser;
  const name = `${u.first_name || ""} ${u.last_name || ""}`.trim() || u.username;
  document.getElementById("currentUserName").textContent = name;
  document.getElementById("currentUserRoleTag").textContent = `Role: ${u.role}`;
  document.getElementById("currentUserAvatar").textContent = name.charAt(0).toUpperCase();

  const avatar = document.getElementById("currentUserAvatar");
  if (u.role === "ADMIN") avatar.style.background = "var(--google-red)";
  else if (u.role === "TEACHER") avatar.style.background = "var(--google-green)";
  else avatar.style.background = "var(--google-blue)";
}

function applyRoleVisibility() {
  if (!state.currentUser) return;
  const isStudent = state.currentUser.role === "STUDENT";

  document.querySelectorAll(".admin-only").forEach(el => {
    el.style.display = isStudent ? "none" : "";
  });
  const adminSection = document.getElementById("navSectionAdmin");
  if (adminSection) adminSection.style.display = isStudent ? "none" : "";

  const stuItem = document.getElementById("navStudentPortalItem");
  if (stuItem) stuItem.style.display = isStudent ? "flex" : "";
  const stuSection = document.getElementById("navSectionStudent");
  if (stuSection) stuSection.style.display = isStudent ? "block" : "";
}

// ==========================================
// 1. DASHBOARD
// ==========================================
function loadDashboard() {
  fetch(`${API_BASE}/dashboard/stats`)
    .then(res => res.json())
    .then(res => {
      if (!res.success) return;
      const d = res.data;
      document.getElementById("dashTotalStudents").textContent = d.total_students;
      document.getElementById("dashTotalTeachers").textContent = d.total_teachers;
      document.getElementById("dashTotalCourses").textContent = d.total_courses;
      document.getElementById("dashAttendanceRate").textContent = `${d.attendance_rate}%`;

      document.getElementById("navStudentCount").textContent = d.total_students;
      document.getElementById("navTeacherCount").textContent = d.total_teachers;

      const deptBox = document.getElementById("deptDistributionList");
      deptBox.innerHTML = "";
      if (d.department_distribution && d.department_distribution.length > 0) {
        const maxVal = Math.max(...d.department_distribution.map(x => x.count), 1);
        d.department_distribution.forEach(dept => {
          const pct = Math.round((dept.count / maxVal) * 100);
          deptBox.innerHTML += `
            <div>
              <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:500; margin-bottom:4px;">
                <span>${dept.name}</span>
                <span style="color:var(--text-secondary);">${dept.count} students</span>
              </div>
              <div style="height:8px; background:var(--bg-surface-variant); border-radius:4px; overflow:hidden;">
                <div style="width:${pct}%; height:100%; background:var(--google-blue); border-radius:4px;"></div>
              </div>
            </div>
          `;
        });
      }

      const auditBox = document.getElementById("dashAuditList");
      auditBox.innerHTML = "";
      if (d.recent_audit && d.recent_audit.length > 0) {
        d.recent_audit.forEach(log => {
          auditBox.innerHTML += `
            <div style="padding:12px 20px; border-bottom:1px solid var(--border-subtle); display:flex; align-items:center; justify-content:space-between;">
              <div style="display:flex; align-items:center; gap:12px;">
                <span class="material-symbols-outlined" style="color:var(--google-blue); font-size:18px;">history</span>
                <div>
                  <div style="font-size:13px; font-weight:500;">${log.details}</div>
                  <div style="font-size:11px; color:var(--text-secondary);">By ${log.actor_name} &bull; ${log.occurred_at}</div>
                </div>
              </div>
              <span class="status-pill status-active" style="font-size:11px;">${log.action}</span>
            </div>
          `;
        });
      }
    })
    .catch(err => console.error("Error loading stats:", err));
}

// ==========================================
// 2. STUDENTS DIRECTORY
// ==========================================
function loadStudents() {
  const search = document.getElementById("studentFilterInput") ? document.getElementById("studentFilterInput").value : "";
  const deptId = document.getElementById("studentDeptFilter") ? document.getElementById("studentDeptFilter").value : "";
  const status = document.getElementById("studentStatusFilter") ? document.getElementById("studentStatusFilter").value : "";

  const url = `${API_BASE}/students?search=${encodeURIComponent(search)}&department_id=${encodeURIComponent(deptId)}&status=${encodeURIComponent(status)}`;
  fetch(url)
    .then(res => res.json())
    .then(res => {
      const tbody = document.getElementById("studentsTableBody");
      tbody.innerHTML = "";
      if (!res.data || res.data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:32px; color:var(--text-secondary);">No student records found matching filters.</td></tr>`;
        return;
      }
      res.data.forEach(s => {
        const statusClass = s.status === "ACTIVE" ? "status-active" : "status-inactive";
        tbody.innerHTML += `
          <tr>
            <td>
              <div style="display:flex; align-items:center; gap:10px;">
                <div class="avatar" style="width:30px; height:30px; font-size:12px;">${s.first_name.charAt(0)}</div>
                <div>
                  <div style="font-weight:600;">${s.first_name} ${s.last_name}</div>
                  <div style="font-size:11px; color:var(--text-secondary);">${s.gender || 'Not specified'} &bull; Adm: ${s.admission_date}</div>
                </div>
              </div>
            </td>
            <td style="font-weight:600; font-family:monospace; color:var(--google-blue);">${s.admission_number}</td>
            <td><span class="brand-badge">${s.department_code || s.department_name || 'Unassigned'}</span></td>
            <td>${s.email}</td>
            <td><span class="status-pill" style="background:var(--bg-surface-variant);">${s.enrolled_courses_count} Classes</span></td>
            <td><span class="status-pill ${statusClass}">${s.status}</span></td>
            <td>
              <div style="display:flex; gap:6px;">
                <button class="btn btn-outline btn-sm" onclick="toggleStudentStatus(${s.id}, '${s.status}')">
                  ${s.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            </td>
          </tr>
        `;
      });
    });
}

function toggleStudentStatus(id, currentStatus) {
  const nextStatus = currentStatus === "ACTIVE" ? "INACTIVE" : "ACTIVE";
  if (!confirm(`Are you sure you want to change this student to ${nextStatus}?`)) return;

  fetch(`${API_BASE}/students/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: nextStatus, actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Admin" })
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast(`Student status updated to ${nextStatus}`);
      loadStudents();
      loadDashboard();
    } else {
      showToast(res.error, "error");
    }
  });
}

function submitAddStudent(e) {
  e.preventDefault();
  const payload = {
    admission_number: document.getElementById("stuAdmissionNo").value,
    department_id: document.getElementById("stuDeptSelect").value,
    first_name: document.getElementById("stuFirstName").value,
    last_name: document.getElementById("stuLastName").value,
    email: document.getElementById("stuEmail").value,
    phone: document.getElementById("stuPhone").value,
    date_of_birth: document.getElementById("stuDob").value,
    gender: document.getElementById("stuGender").value,
    address: document.getElementById("stuAddress").value,
    actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Admin"
  };

  fetch(`${API_BASE}/students`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast("Student created successfully!");
      closeModal("addStudentModal");
      document.getElementById("addStudentForm").reset();
      loadStudents();
      loadDashboard();
      loadOfferingsDropdowns();
    } else {
      showToast(res.error, "error");
    }
  })
  .catch(err => showToast("Error: " + err, "error"));
}

// ==========================================
// 3. FACULTY / TEACHERS
// ==========================================
function loadTeachers() {
  fetch(`${API_BASE}/teachers`)
    .then(res => res.json())
    .then(res => {
      const tbody = document.getElementById("teachersTableBody");
      tbody.innerHTML = "";
      res.data.forEach(t => {
        tbody.innerHTML += `
          <tr>
            <td>
              <div style="display:flex; align-items:center; gap:10px;">
                <div class="avatar" style="background:var(--google-green); width:30px; height:30px; font-size:12px;">${t.first_name.charAt(0)}</div>
                <div style="font-weight:600;">${t.first_name} ${t.last_name}</div>
              </div>
            </td>
            <td style="font-family:monospace; font-weight:600;">${t.employee_number}</td>
            <td>${t.department_name || '-'}</td>
            <td>${t.designation || 'Faculty'}</td>
            <td>${t.email}</td>
            <td><span class="status-pill status-active">${t.active_classes_count} Assigned</span></td>
            <td><span class="status-pill status-active">${t.status}</span></td>
          </tr>
        `;
      });
    });
}

function submitAddTeacher(e) {
  e.preventDefault();
  const payload = {
    employee_number: document.getElementById("tchEmpNo").value,
    department_id: document.getElementById("tchDeptSelect").value,
    first_name: document.getElementById("tchFirstName").value,
    last_name: document.getElementById("tchLastName").value,
    designation: document.getElementById("tchDesignation").value,
    email: document.getElementById("tchEmail").value,
    actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Admin"
  };

  fetch(`${API_BASE}/teachers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast("Teacher created successfully!");
      closeModal("addTeacherModal");
      document.getElementById("addTeacherForm").reset();
      loadTeachers();
      loadDashboard();
      loadOfferingsDropdowns();
    } else {
      showToast(res.error, "error");
    }
  });
}

// ==========================================
// 4. COURSES & DEPARTMENTS
// ==========================================
function loadDepartments() {
  fetch(`${API_BASE}/departments`)
    .then(res => res.json())
    .then(res => {
      state.departments = res.data || [];
      const filterSelect = document.getElementById("studentDeptFilter");
      const stuSelect = document.getElementById("stuDeptSelect");
      const tchSelect = document.getElementById("tchDeptSelect");
      const courseSelect = document.getElementById("courseDeptSelect");

      if (filterSelect) {
        filterSelect.innerHTML = `<option value="">All Departments</option>`;
        state.departments.forEach(d => {
          filterSelect.innerHTML += `<option value="${d.id}">${d.name}</option>`;
        });
      }
      [stuSelect, tchSelect, courseSelect].forEach(sel => {
        if (sel) {
          sel.innerHTML = "";
          state.departments.forEach(d => {
            sel.innerHTML += `<option value="${d.id}">${d.name} (${d.code})</option>`;
          });
        }
      });
    });
}

function loadCourses() {
  fetch(`${API_BASE}/courses`)
    .then(res => res.json())
    .then(res => {
      const tbody = document.getElementById("coursesTableBody");
      tbody.innerHTML = "";
      res.data.forEach(c => {
        tbody.innerHTML += `
          <tr>
            <td style="font-weight:700; color:var(--google-blue);">${c.code}</td>
            <td style="font-weight:600;">${c.name}</td>
            <td><span class="brand-badge">${c.department_name}</span></td>
            <td><strong>${c.credits}</strong> Credits</td>
            <td style="max-width:320px; color:var(--text-secondary);">${c.description || '-'}</td>
            <td><span class="status-pill status-active">Active</span></td>
          </tr>
        `;
      });
    });
}

function submitAddCourse(e) {
  e.preventDefault();
  const payload = {
    code: document.getElementById("courseCode").value,
    name: document.getElementById("courseName").value,
    department_id: document.getElementById("courseDeptSelect").value,
    credits: document.getElementById("courseCredits").value,
    description: document.getElementById("courseDesc").value,
    actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Admin"
  };

  fetch(`${API_BASE}/courses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast("Course created successfully!");
      closeModal("addCourseModal");
      document.getElementById("addCourseForm").reset();
      loadCourses();
      loadDashboard();
      loadOfferingsDropdowns();
    } else {
      showToast(res.error, "error");
    }
  });
}

// ==========================================
// 5. CLASS OFFERINGS & ENROLLMENTS
// ==========================================
function loadOfferings() {
  fetch(`${API_BASE}/offerings`)
    .then(res => res.json())
    .then(res => {
      const tbody = document.getElementById("offeringsTableBody");
      tbody.innerHTML = "";
      res.data.forEach(o => {
        tbody.innerHTML += `
          <tr>
            <td>
              <div style="font-weight:600;">${o.course_name}</div>
              <div style="font-size:11px; color:var(--text-secondary); font-family:monospace;">${o.course_code} &bull; ${o.credits} credits</div>
            </td>
            <td><span class="brand-badge">${o.section}</span></td>
            <td>${o.semester} (${o.session_name})</td>
            <td><strong>${o.teacher_name}</strong></td>
            <td>${o.capacity} max</td>
            <td><span class="status-pill status-present">${o.enrolled_count} Students Enrolled</span></td>
            <td>
              <button class="btn btn-outline btn-sm" onclick="viewOfferingRoster(${o.id}, '${o.course_code}', '${o.section}')">
                View Roster
              </button>
            </td>
          </tr>
        `;
      });
    });
}

function loadOfferingsDropdowns() {
  fetch(`${API_BASE}/offerings`)
    .then(res => res.json())
    .then(res => {
      state.offerings = res.data || [];
      const attSel = document.getElementById("attOfferingSelect");
      const enrollOffSel = document.getElementById("enrollOfferingSelect");
      const sessOffSel = document.getElementById("sessionOfferingSelect");
      const assOffSel = document.getElementById("assessmentOfferingSelect");

      [attSel, enrollOffSel, sessOffSel, assOffSel].forEach(sel => {
        if (sel) {
          sel.innerHTML = "";
          state.offerings.forEach(o => {
            sel.innerHTML += `<option value="${o.id}">${o.course_code} - ${o.course_name} (${o.section})</option>`;
          });
        }
      });
    });

  fetch(`${API_BASE}/students?status=ACTIVE`)
    .then(res => res.json())
    .then(res => {
      const stuSel = document.getElementById("enrollStudentSelect");
      if (stuSel) {
        stuSel.innerHTML = "";
        (res.data || []).forEach(s => {
          stuSel.innerHTML += `<option value="${s.id}">${s.admission_number} - ${s.first_name} ${s.last_name}</option>`;
        });
      }
    });

  fetch(`${API_BASE}/courses`)
    .then(res => res.json())
    .then(res => {
      const cSel = document.getElementById("offeringCourseSelect");
      if (cSel) {
        cSel.innerHTML = "";
        (res.data || []).forEach(c => {
          cSel.innerHTML += `<option value="${c.id}">${c.code} - ${c.name}</option>`;
        });
      }
    });

  fetch(`${API_BASE}/teachers`)
    .then(res => res.json())
    .then(res => {
      const tSel = document.getElementById("offeringTeacherSelect");
      if (tSel) {
        tSel.innerHTML = "";
        (res.data || []).forEach(t => {
          tSel.innerHTML += `<option value="${t.id}">${t.first_name} ${t.last_name} (${t.employee_number})</option>`;
        });
      }
    });
}

function submitAddOffering(e) {
  e.preventDefault();
  const payload = {
    course_id: document.getElementById("offeringCourseSelect").value,
    academic_session_id: 1,
    teacher_id: document.getElementById("offeringTeacherSelect").value,
    section: document.getElementById("offeringSection").value,
    semester: document.getElementById("offeringSemester").value,
    capacity: 60,
    actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Admin"
  };

  fetch(`${API_BASE}/offerings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast("Class offering created!");
      closeModal("addOfferingModal");
      loadOfferings();
      loadOfferingsDropdowns();
    } else {
      showToast(res.error, "error");
    }
  });
}

function submitEnrollStudent(e) {
  e.preventDefault();
  const payload = {
    student_id: document.getElementById("enrollStudentSelect").value,
    class_offering_id: document.getElementById("enrollOfferingSelect").value,
    actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Admin"
  };

  fetch(`${API_BASE}/enrollments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast("Student enrolled successfully!");
      closeModal("enrollStudentModal");
      loadOfferings();
      loadStudents();
    } else {
      showToast(res.error, "error");
    }
  });
}

function viewOfferingRoster(offeringId, courseCode, section) {
  fetch(`${API_BASE}/offerings/${offeringId}/students`)
    .then(res => res.json())
    .then(res => {
      const count = res.data ? res.data.length : 0;
      let names = (res.data || []).map(s => `${s.admission_number}: ${s.first_name} ${s.last_name}`).join("\n");
      alert(`Enrolled Roster for ${courseCode} (${section}) - Total: ${count} students:\n\n${names || 'No students enrolled yet.'}`);
    });
}

// ==========================================
// 6. ATTENDANCE TRACKING
// ==========================================
function loadAttendanceSessions() {
  const offId = document.getElementById("attOfferingSelect").value;
  const url = offId ? `${API_BASE}/attendance/sessions?offering_id=${offId}` : `${API_BASE}/attendance/sessions`;

  fetch(url)
    .then(res => res.json())
    .then(res => {
      const tbody = document.getElementById("attendanceSessionsTableBody");
      tbody.innerHTML = "";
      if (!res.data || res.data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:24px; color:var(--text-secondary);">No sessions scheduled yet for this class offering. Click 'Create Session' to start.</td></tr>`;
        return;
      }
      res.data.forEach(s => {
        tbody.innerHTML += `
          <tr>
            <td style="font-weight:600;">${s.session_date}</td>
            <td><strong>${s.topic}</strong></td>
            <td><span class="brand-badge">${s.course_code} (${s.section})</span></td>
            <td><span class="status-pill status-present">${s.present_count || 0} / ${s.attendance_marked_count || 0} Marked</span></td>
            <td>
              <button class="btn btn-primary btn-sm" onclick="openAttendanceSheet(${s.id})">
                <span class="material-symbols-outlined" style="font-size:15px;">checklist</span> Mark / Edit Sheet
              </button>
            </td>
          </tr>
        `;
      });
    });
}

function submitCreateSession(e) {
  e.preventDefault();
  const payload = {
    class_offering_id: document.getElementById("sessionOfferingSelect").value,
    session_date: document.getElementById("sessionDateInput").value,
    topic: document.getElementById("sessionTopicInput").value,
    actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Teacher"
  };

  fetch(`${API_BASE}/attendance/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast("Class session created!");
      closeModal("createSessionModal");
      loadAttendanceSessions();
      openAttendanceSheet(res.data.id);
    } else {
      showToast(res.error, "error");
    }
  });
}

function openAttendanceSheet(sessionId) {
  state.activeAttendanceSession = sessionId;
  fetch(`${API_BASE}/attendance/session/${sessionId}`)
    .then(res => res.json())
    .then(res => {
      if (!res.success) {
        showToast(res.error, "error");
        return;
      }
      const data = res.data;
      state.activeAttendanceSheet = data.sheet;

      document.getElementById("activeSheetTitle").textContent = `Attendance: ${data.session.course_name} (${data.session.section})`;
      document.getElementById("activeSheetSubtitle").textContent = `Session Date: ${data.session.session_date} &bull; Topic: ${data.session.topic}`;

      renderAttendanceSheetTable();
      document.getElementById("activeAttendanceSheetCard").style.display = "block";
      document.getElementById("activeAttendanceSheetCard").scrollIntoView({ behavior: 'smooth' });
    });
}

function renderAttendanceSheetTable() {
  const tbody = document.getElementById("activeAttendanceSheetBody");
  tbody.innerHTML = "";

  state.activeAttendanceSheet.forEach((item, idx) => {
    tbody.innerHTML += `
      <tr>
        <td style="font-family:monospace; font-weight:600;">${item.admission_number}</td>
        <td style="font-weight:600;">${item.first_name} ${item.last_name}</td>
        <td>
          <div class="att-btn-group">
            <button class="att-option-btn ${item.attendance_status === 'PRESENT' ? 'selected-present' : ''}" onclick="setAttendanceStatus(${idx}, 'PRESENT')">PRESENT</button>
            <button class="att-option-btn ${item.attendance_status === 'ABSENT' ? 'selected-absent' : ''}" onclick="setAttendanceStatus(${idx}, 'ABSENT')">ABSENT</button>
            <button class="att-option-btn ${item.attendance_status === 'LATE' ? 'selected-late' : ''}" onclick="setAttendanceStatus(${idx}, 'LATE')">LATE</button>
            <button class="att-option-btn ${item.attendance_status === 'EXCUSED' ? 'selected-excused' : ''}" onclick="setAttendanceStatus(${idx}, 'EXCUSED')">EXCUSED</button>
          </div>
        </td>
      </tr>
    `;
  });

  updateAttendanceCounters();
}

function setAttendanceStatus(idx, status) {
  state.activeAttendanceSheet[idx].attendance_status = status;
  renderAttendanceSheetTable();
}

function markAllAttendance(status) {
  state.activeAttendanceSheet.forEach(item => item.attendance_status = status);
  renderAttendanceSheetTable();
  showToast(`Marked all students as ${status}`);
}

function updateAttendanceCounters() {
  const present = state.activeAttendanceSheet.filter(s => s.attendance_status === "PRESENT").length;
  const absent = state.activeAttendanceSheet.filter(s => s.attendance_status === "ABSENT").length;
  const late = state.activeAttendanceSheet.filter(s => s.attendance_status === "LATE").length;
  const excused = state.activeAttendanceSheet.filter(s => s.attendance_status === "EXCUSED").length;

  document.getElementById("attendanceStatsCounter").innerHTML = `
    <span style="color:var(--google-green);">Present: ${present}</span> &bull; 
    <span style="color:var(--google-red);">Absent: ${absent}</span> &bull; 
    <span style="color:var(--google-yellow);">Late: ${late}</span> &bull; 
    <span style="color:var(--google-blue);">Excused: ${excused}</span>
  `;
}

function saveActiveAttendance() {
  if (!state.activeAttendanceSession) return;
  const records = state.activeAttendanceSheet.map(s => ({
    student_id: s.student_id,
    status: s.attendance_status
  }));

  fetch(`${API_BASE}/attendance/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      class_session_id: state.activeAttendanceSession,
      records: records,
      actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Teacher"
    })
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast(res.message);
      loadAttendanceSessions();
      loadDashboard();
    } else {
      showToast(res.error, "error");
    }
  });
}

// ==========================================
// 7. ASSESSMENTS & MARKS
// ==========================================
function loadAssessments() {
  fetch(`${API_BASE}/assessments`)
    .then(res => res.json())
    .then(res => {
      const tbody = document.getElementById("assessmentsTableBody");
      tbody.innerHTML = "";
      res.data.forEach(a => {
        const pubBadge = a.published === 1 
          ? `<span class="status-pill status-present">Published</span>`
          : `<span class="status-pill status-inactive">Draft (Unpublished)</span>`;

        tbody.innerHTML += `
          <tr>
            <td style="font-weight:600;">${a.name}</td>
            <td><span class="brand-badge">${a.assessment_type}</span></td>
            <td>${a.course_code} (${a.section})</td>
            <td>${a.assessment_date}</td>
            <td><strong>${a.max_marks}</strong> pts</td>
            <td>${a.marks_entered_count} / ${a.total_students} Evaluated</td>
            <td>${pubBadge}</td>
            <td>
              <div style="display:flex; gap:6px;">
                <button class="btn btn-outline btn-sm" onclick="openMarksModal(${a.id})">
                  <span class="material-symbols-outlined" style="font-size:14px;">edit</span> Marks
                </button>
                <button class="btn ${a.published === 1 ? 'btn-outline' : 'btn-primary'} btn-sm" onclick="togglePublishAssessment(${a.id}, ${a.published})">
                  ${a.published === 1 ? 'Unpublish' : 'Publish'}
                </button>
              </div>
            </td>
          </tr>
        `;
      });
    });
}

function submitCreateAssessment(e) {
  e.preventDefault();
  const payload = {
    class_offering_id: document.getElementById("assessmentOfferingSelect").value,
    name: document.getElementById("assessmentName").value,
    assessment_type: document.getElementById("assessmentType").value,
    assessment_date: document.getElementById("assessmentDate").value,
    max_marks: document.getElementById("assessmentMaxMarks").value,
    actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Teacher"
  };

  fetch(`${API_BASE}/assessments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast("Assessment created successfully!");
      closeModal("createAssessmentModal");
      loadAssessments();
    } else {
      showToast(res.error, "error");
    }
  });
}

function togglePublishAssessment(assessmentId, currentPublished) {
  const next = currentPublished === 1 ? false : true;
  fetch(`${API_BASE}/assessments/${assessmentId}/publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ published: next, actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Teacher" })
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast(res.message);
      loadAssessments();
    } else {
      showToast(res.error, "error");
    }
  });
}

function openMarksModal(assessmentId) {
  state.activeAssessment = assessmentId;
  fetch(`${API_BASE}/assessments/${assessmentId}/marks`)
    .then(res => res.json())
    .then(res => {
      if (!res.success) {
        showToast(res.error, "error");
        return;
      }
      const data = res.data;
      state.activeMarksSheet = data.sheet;
      const maxMarks = data.assessment.max_marks;

      document.getElementById("marksModalTitle").textContent = `${data.assessment.name} (${data.assessment.course_code})`;
      document.getElementById("marksModalSubtitle").textContent = `Maximum Marks: ${maxMarks} | Evaluated by Teacher`;

      const tbody = document.getElementById("marksSheetTableBody");
      tbody.innerHTML = "";
      data.sheet.forEach((item, idx) => {
        const val = item.marks_obtained !== null ? item.marks_obtained : "";
        tbody.innerHTML += `
          <tr>
            <td style="font-family:monospace; font-weight:600;">${item.admission_number}</td>
            <td style="font-weight:600;">${item.first_name} ${item.last_name}</td>
            <td>
              <input type="number" step="0.5" min="0" max="${maxMarks}" class="form-control mark-input" 
                     id="markInput_${idx}" value="${val}" placeholder="0 - ${maxMarks}">
            </td>
            <td><span class="status-pill" id="markBadge_${idx}">${val !== "" ? 'Graded' : 'Pending'}</span></td>
          </tr>
        `;
      });

      openModal("marksEntryModal");
    });
}

function saveMarksSheet() {
  if (!state.activeAssessment) return;
  const marksList = [];
  for (let i = 0; i < state.activeMarksSheet.length; i++) {
    const input = document.getElementById(`markInput_${i}`);
    if (input && input.value !== "") {
      marksList.push({
        student_id: state.activeMarksSheet[i].student_id,
        marks_obtained: parseFloat(input.value)
      });
    }
  }

  fetch(`${API_BASE}/marks/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      assessment_id: state.activeAssessment,
      marks: marksList,
      actor_name: state.currentUser ? (state.currentUser.first_name || state.currentUser.username) : "Teacher"
    })
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      showToast(res.message);
      closeModal("marksEntryModal");
      loadAssessments();
    } else {
      showToast(res.error, "error");
    }
  });
}

// ==========================================
// 8. STUDENT PORTAL (MY ACADEMIC RECORD)
// ==========================================
function loadStudentPortal() {
  const stuId = (state.currentUser && state.currentUser.student_id) ? state.currentUser.student_id : 1;
  const name = state.currentUser ? `${state.currentUser.first_name || 'Rahul'} ${state.currentUser.last_name || 'Kumar'}` : "Rahul Kumar";
  document.getElementById("studentPortalName").textContent = `${name}'s Academic Dashboard`;
  document.getElementById("studentPortalAdm").textContent = `Admission: ${state.currentUser ? (state.currentUser.admission_number || 'STU-2026-001') : 'STU-2026-001'} | Status: ACTIVE`;

  fetch(`${API_BASE}/student/me/attendance?student_id=${stuId}`)
    .then(res => res.json())
    .then(res => {
      if (!res.success) return;
      const data = res.data;
      const overall = data.overall_percentage;
      document.getElementById("studentOverallAttPct").textContent = `${overall}%`;

      const badge = document.getElementById("studentAttStatusBadge");
      if (overall >= 75) {
        badge.className = "status-pill status-present";
        badge.textContent = `Eligible for Examinations (≥ 75%)`;
        document.getElementById("studentOverallAttPct").style.color = "var(--google-green)";
      } else if (overall >= 60) {
        badge.className = "status-pill status-late";
        badge.textContent = `Low Attendance Warning (< 75%)`;
        document.getElementById("studentOverallAttPct").style.color = "var(--google-yellow)";
      } else {
        badge.className = "status-pill status-absent";
        badge.textContent = `Critical: Ineligible (< 60%)`;
        document.getElementById("studentOverallAttPct").style.color = "var(--google-red)";
      }

      const list = document.getElementById("studentCourseAttList");
      list.innerHTML = "";
      data.courses.forEach(c => {
        const p = c.percentage;
        const color = p >= 75 ? "var(--google-green)" : p >= 60 ? "var(--google-yellow)" : "var(--google-red)";
        list.innerHTML += `
          <div>
            <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:600; margin-bottom:4px;">
              <span>${c.course_code}: ${c.course_name}</span>
              <span style="color:${color}">${p}% (${(c.present_count||0)+(c.late_count||0)} / ${c.total_sessions} sessions)</span>
            </div>
            <div style="height:8px; background:var(--bg-surface-variant); border-radius:4px; overflow:hidden;">
              <div style="width:${p}%; height:100%; background:${color}; border-radius:4px;"></div>
            </div>
          </div>
        `;
      });
    });

  fetch(`${API_BASE}/student/me/results?student_id=${stuId}`)
    .then(res => res.json())
    .then(res => {
      const tbody = document.getElementById("studentResultsTableBody");
      tbody.innerHTML = "";
      if (!res.data.results || res.data.results.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-secondary);">No examination results published yet.</td></tr>`;
        return;
      }
      res.data.results.forEach(r => {
        let gradeClass = "status-present";
        if (r.grade === "A+" || r.grade === "A") gradeClass = "status-present";
        else if (r.grade === "B" || r.grade === "C") gradeClass = "status-excused";
        else gradeClass = "status-absent";

        tbody.innerHTML += `
          <tr>
            <td style="font-weight:600;">${r.course_code}: ${r.course_name}</td>
            <td><strong>${r.assessment_name}</strong></td>
            <td><span class="brand-badge">${r.assessment_type}</span></td>
            <td>${r.max_marks}</td>
            <td style="font-weight:700; color:var(--google-blue);">${r.marks_obtained}</td>
            <td><strong>${r.percentage}%</strong></td>
            <td><span class="status-pill ${gradeClass}" style="font-weight:700;">${r.grade}</span></td>
          </tr>
        `;
      });
    });
}

// ==========================================
// 9. SYSTEM LOGS & AUDIT TRAIL
// ==========================================
function switchLogsTab(tab) {
  state.currentLogsTab = tab;
  document.getElementById("tabAuditDbBtn").classList.toggle("active", tab === "db");
  document.getElementById("tabAuditConsoleBtn").classList.toggle("active", tab === "console");

  document.getElementById("logSubTabDb").style.display = tab === "db" ? "block" : "none";
  document.getElementById("logSubTabConsole").style.display = tab === "console" ? "block" : "none";

  if (tab === "db") {
    loadAuditLogs();
  } else {
    loadLiveFileLogs();
  }
}

function refreshCurrentLogsTab() {
  if (state.currentLogsTab === "db") loadAuditLogs();
  else loadLiveFileLogs();
}

function loadAuditLogs() {
  const action = document.getElementById("auditActionFilter") ? document.getElementById("auditActionFilter").value : "";
  const search = document.getElementById("auditSearchInput") ? document.getElementById("auditSearchInput").value : "";
  const url = `${API_BASE}/audit-logs?action=${encodeURIComponent(action)}&search=${encodeURIComponent(search)}`;

  fetch(url)
    .then(res => res.json())
    .then(res => {
      const tbody = document.getElementById("auditTableBody");
      tbody.innerHTML = "";
      if (!res.data || res.data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:24px; color:var(--text-secondary);">No audit events recorded yet matching query.</td></tr>`;
        return;
      }
      res.data.forEach(l => {
        let badgeClass = "status-present";
        if (l.action.includes("FAIL") || l.action.includes("BLOCK")) badgeClass = "status-absent";
        else if (l.action.includes("UPDATE") || l.action.includes("STATUS")) badgeClass = "status-late";
        else if (l.action.includes("ATTEND") || l.action.includes("MARK")) badgeClass = "status-excused";

        tbody.innerHTML += `
          <tr>
            <td style="font-family:monospace; color:var(--text-secondary); white-space:nowrap;">${l.occurred_at}</td>
            <td><strong>${l.actor_name}</strong></td>
            <td><span class="status-pill ${badgeClass}" style="font-size:11px;">${l.action}</span></td>
            <td><strong>${l.entity_type}</strong></td>
            <td style="font-family:monospace;">${l.entity_id || '-'}</td>
            <td style="color:var(--text-primary); font-size:13px;">${l.details}</td>
          </tr>
        `;
      });
    });
}

function loadLiveFileLogs() {
  fetch(`${API_BASE}/logs/file`)
    .then(res => res.json())
    .then(res => {
      const win = document.getElementById("liveTerminalOutput");
      if (!res.success || !res.data || res.data.length === 0) {
        win.innerHTML = `<div class="terminal-line log-info">No server log entries found in sms.log yet. Activity will appear here live.</div>`;
        return;
      }
      win.innerHTML = "";
      res.data.forEach(line => {
        let cssClass = "log-info";
        if (line.includes("[WARNING]")) cssClass = "log-warn";
        else if (line.includes("[ERROR]")) cssClass = "log-err";

        const div = document.createElement("div");
        div.className = `terminal-line ${cssClass}`;
        div.textContent = line.trim();
        win.appendChild(div);
      });
      win.scrollTop = win.scrollHeight;
    });
}

function toggleAutoRefreshLogs(enabled) {
  if (state.autoRefreshTimer) clearInterval(state.autoRefreshTimer);
  if (enabled) {
    state.autoRefreshTimer = setInterval(() => {
      if (state.currentLogsTab === "console") {
        loadLiveFileLogs();
      }
    }, 3000);
    showToast("Live log streaming enabled (3s)");
  } else {
    showToast("Auto-refresh paused");
  }
}

// ==========================================
// 10. EXPORTS & CSV
// ==========================================
function exportStudentsCsv() {
  window.location.href = `${API_BASE}/reports/students.csv`;
}

function exportAttendanceCsv() {
  window.location.href = `${API_BASE}/reports/attendance.csv`;
}

// ==========================================
// MODAL & TOAST HELPERS
// ==========================================
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

function openAddStudentModal() { openModal("addStudentModal"); }
function openAddTeacherModal() { openModal("addTeacherModal"); }
function openAddCourseModal() { openModal("addCourseModal"); }
function openAddOfferingModal() { openModal("addOfferingModal"); }
function openEnrollStudentModal() { openModal("enrollStudentModal"); }
function openCreateSessionModal() { openModal("createSessionModal"); }
function openCreateAssessmentModal() { openModal("createAssessmentModal"); }

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `
    <span class="material-symbols-outlined" style="color: ${type === 'error' ? 'var(--google-red)' : 'var(--google-green)'};">
      ${type === 'error' ? 'error' : 'check_circle'}
    </span>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3500);
}

function setupGlobalSearch() {
  const search = document.getElementById("globalSearchInput");
  if (!search) return;
  search.addEventListener("input", (e) => {
    const val = e.target.value.toLowerCase().trim();
    if (val) {
      navigateTo("students");
      const stuInput = document.getElementById("studentFilterInput");
      if (stuInput) {
        stuInput.value = val;
        loadStudents();
      }
    }
  });
}
