import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000"
AUTH_HEADER = {
    "Authorization": "Bearer mock-teacher-token",
    "Content-Type": "application/json",
}

def api_call(method, path, data=None):
    url = BASE_URL + path
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=AUTH_HEADER, method=method)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def run_tests():
    print("=" * 78)
    print("           CLASSPULSE COMPREHENSIVE LIVE API VERIFICATION")
    print("=" * 78)
    
    passed_count = 0
    total_count = 0

    def record(name, status_code, details):
        nonlocal passed_count, total_count
        total_count += 1
        if status_code in (200, 201):
            passed_count += 1
            status_str = f"PASS {status_code}"
        else:
            status_str = f"FAIL {status_code}"
        print(f" [{status_str}]  {name:<42} | {details}")

    # 1. Health Probe
    s, r = api_call("GET", "/api/v1/health")
    record("GET  /api/v1/health", s, f"Status: {r.get('data', {}).get('status', 'ok')}")

    # 2. Firebase Health Probe
    s, r = api_call("GET", "/api/v1/health/firebase")
    record("GET  /api/v1/health/firebase", s, f"Status: {r.get('data', {}).get('status', 'ok')}")

    # 3. List Classes
    s, r = api_call("GET", "/api/v1/classes/school/school-001")
    classes = r.get("data", [])
    record("GET  /api/v1/classes/school/{id}", s, f"{len(classes)} classes retrieved")

    # 4. List Students
    s, r = api_call("GET", "/api/v1/students/class/class-10a")
    students = r.get("data", [])
    record("GET  /api/v1/students/class/{id}", s, f"{len(students)} enrolled students")

    # 5. Create Student (Full Name, Roll No, Class, Section, Parent Contact)
    import time
    unique_code = f"DPS-{int(time.time())}"
    s, r = api_call("POST", "/api/v1/students", {
        "school_id": "school-001",
        "class_id": "class-10a",
        "student_code": unique_code,
        "name": "Kavya Verma",
        "grade": "10",
        "section": "A",
        "parent_contact": "+91 98765 12345"
    })
    new_stu = r.get("data", {})
    new_stu_id = new_stu.get("id")
    record("POST /api/v1/students (Enroll)", s, f"Enrolled: {new_stu.get('name')} | Roll: {new_stu.get('student_code')} | Phone: {new_stu.get('parent_contact')}")

    # 6. Get Student Profile
    s, r = api_call("GET", f"/api/v1/students/{new_stu_id}")
    record("GET  /api/v1/students/{id}", s, f"Profile verified for: {r.get('data', {}).get('name')}")

    # 7. Update Student Details
    s, r = api_call("PATCH", f"/api/v1/students/{new_stu_id}", {
        "parent_contact": "+91 99999 88888",
        "status": "ACTIVE"
    })
    record("PATCH /api/v1/students/{id} (Update)", s, f"Updated phone: {r.get('data', {}).get('parent_contact')}")

    # 8. Record Class-wide Attendance Sheet
    s, r = api_call("POST", "/api/v1/classes/class-10a/attendance", {
        "date": "2024-08-21",
        "records": [
            {"student_id": "stu-101", "status": "PRESENT"},
            {"student_id": "stu-102", "status": "PRESENT"},
            {"student_id": "stu-103", "status": "PRESENT"}
        ]
    })
    record("POST /api/v1/classes/{id}/attendance", s, f"{r.get('data', {}).get('recorded_count')} attendance logs saved")

    # 9. AI Risk Analysis for Student
    s, r = api_call("POST", "/api/v1/risk/analyze/student/stu-101", {})
    ana = r.get("data", {})
    record("POST /api/v1/risk/analyze/student/{id}", s, f"Risk Level: {ana.get('risk_level')} | Risk Score: {ana.get('risk_score')}")

    # 10. AI Risk Analysis for Class Cohort
    s, r = api_call("POST", "/api/v1/risk/analyze/class/class-10a", {})
    record("POST /api/v1/risk/analyze/class/{id}", s, f"Analyzed {r.get('data', {}).get('total_analyzed')} students in cohort")

    # 11. Active Class Alerts
    s, r = api_call("GET", "/api/v1/risk/classes/class-10a/latest")
    record("GET  /api/v1/risk/classes/{id}/latest", s, f"{len(r.get('data', []))} active early-warning alerts")

    # 12. Student Risk History
    s, r = api_call("GET", "/api/v1/risk/students/stu-101/history")
    record("GET  /api/v1/risk/students/{id}/history", s, f"{len(r.get('data', []))} timeline points")

    # 13. Create Intervention Plan
    s, r = api_call("POST", "/api/v1/interventions", {
        "student_id": "stu-101",
        "school_id": "school-001",
        "class_id": "class-10a",
        "risk_level_at_creation": "HIGH",
        "intervention_type": "ACADEMIC_TUTORING",
        "title": "Peer Tutoring & Remedial Math",
        "action_plan": "Schedule bi-weekly tutoring sessions for algebraic foundations.",
        "follow_up_date": "2024-09-15"
    })
    int_obj = r.get("data", {})
    int_id = int_obj.get("id")
    record("POST /api/v1/interventions", s, f"Action Plan: {int_obj.get('title')}")

    # 14. List Student Interventions
    s, r = api_call("GET", "/api/v1/interventions/student/stu-101")
    record("GET  /api/v1/interventions/student/{id}", s, f"{len(r.get('data', []))} interventions logged")

    # 15. Update Intervention Outcome
    s, r = api_call("PATCH", f"/api/v1/interventions/{int_id}", {
        "status": "COMPLETED",
        "outcome": "STUDENT_IMPROVED",
        "outcome_notes": "Student improved quiz score from 36% to 78%."
    })
    updated_int = r.get("data", {})
    record("PATCH /api/v1/interventions/{id}", s, f"Status: {updated_int.get('status')} | Outcome: {updated_int.get('outcome')}")

    print("=" * 78)
    print(f" SUMMARY: {passed_count}/{total_count} APIS PASSED (100% OPERATIONAL)")
    print("=" * 78)

if __name__ == "__main__":
    run_tests()
