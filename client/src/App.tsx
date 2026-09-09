import React, { useEffect, useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { RoleSelectionPage } from './pages/RoleSelectionPage';

// Teacher layout & pages
import { TeacherLayout } from './layouts/TeacherLayout';
import { DashboardPage } from './pages/DashboardPage';
import { StudentsPage } from './pages/StudentsPage';
import { StudentDetailPage } from './pages/StudentDetailPage';
import { InterventionsPage } from './pages/InterventionsPage';
import { DataImportPage } from './pages/DataImportPage';
import { ExamsPage } from './pages/teacher/ExamsPage';
import { TeacherMessagesPage } from './pages/teacher/TeacherMessagesPage';
import { TeacherAnnouncementsPage } from './pages/teacher/TeacherAnnouncementsPage';
import { TeacherTimetablePage } from './pages/teacher/TeacherTimetablePage';
import { TeacherAssignmentsPage } from './pages/teacher/TeacherAssignmentsPage';
import { TeacherDoubtsPage } from './pages/teacher/TeacherDoubtsPage';
import { TeacherMonthlyReportsPage } from './pages/teacher/TeacherMonthlyReportsPage';

// Principal layout & pages
import { PrincipalLayout } from './layouts/PrincipalLayout';
import { PrincipalDashboardPage } from './pages/principal/PrincipalDashboardPage';
import { PrincipalMonthlyAnalyticsPage } from './pages/principal/PrincipalMonthlyAnalyticsPage';
import { ClassManagementPage } from './pages/principal/ClassManagementPage';
import { TeacherManagementPage } from './pages/principal/TeacherManagementPage';
import { PrincipalReportsPage } from './pages/principal/PrincipalReportsPage';
import { AnnouncementsPage as PrincipalAnnouncementsPage } from './pages/principal/AnnouncementsPage';
import { TimetableManagementPage } from './pages/principal/TimetableManagementPage';
import { ExamManagementPage } from './pages/principal/ExamManagementPage';
import { PrincipalAssignmentsPage } from './pages/principal/PrincipalAssignmentsPage';

// Student layout & pages
import { StudentLayout } from './layouts/StudentLayout';
import { StudentDashboardPage } from './pages/student/StudentDashboardPage';
import { StudentMonthlyReportPage } from './pages/student/StudentMonthlyReportPage';
import { StudentAttendancePage } from './pages/student/StudentAttendancePage';
import { StudentMarksPage } from './pages/student/StudentMarksPage';
import { StudentMessagesPage } from './pages/student/StudentMessagesPage';
import { StudentAnnouncementsPage } from './pages/student/StudentAnnouncementsPage';
import { StudentTimetablePage } from './pages/student/StudentTimetablePage';
import { StudentAssignmentsPage } from './pages/student/StudentAssignmentsPage';
import { StudentDoubtsPage } from './pages/student/StudentDoubtsPage';

// Modals
import { InterventionModal } from './components/InterventionModal';
import { CreateStudentModal } from './components/CreateStudentModal';
import { EditStudentModal } from './components/EditStudentModal';
import { TakeAttendanceModal } from './components/TakeAttendanceModal';
import { classesApi } from './api/classes';
import { SchoolClass, Student } from './types';

const MainApp: React.FC = () => {
  const { currentUser, schoolId, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState<string>('');
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [classes, setClasses] = useState<SchoolClass[]>([]);

  // Modals state
  const [interventionStudent, setInterventionStudent] = useState<Student | null>(null);
  const [isInterventionModalOpen, setIsInterventionModalOpen] = useState(false);
  const [isCreateStudentOpen, setIsCreateStudentOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [isEditStudentOpen, setIsEditStudentOpen] = useState(false);
  const [attendanceClass, setAttendanceClass] = useState<{ id: string; name: string; students: Student[] } | null>(null);
  const [isAttendanceOpen, setIsAttendanceOpen] = useState(false);

  // Key to force refresh sub-views
  const [refreshKey, setRefreshKey] = useState(0);

  // Set default page when user role changes or logs in
  useEffect(() => {
    if (!currentUser) return;
    if (currentUser.role === 'STUDENT') {
      setCurrentPage('student-dashboard');
    } else if (currentUser.role === 'SCHOOL_ADMIN' || currentUser.role === 'ADMIN') {
      setCurrentPage('principal-dashboard');
    } else {
      setCurrentPage('teacher-dashboard');
    }
  }, [currentUser?.role]);

  useEffect(() => {
    async function loadSchoolClasses() {
      if (!schoolId) return;
      try {
        const clsList = await classesApi.listSchoolClasses(schoolId);
        setClasses(clsList);
      } catch (err) {
        console.error(err);
      }
    }
    loadSchoolClasses();
  }, [schoolId, refreshKey]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a', color: 'white' }}>
        Loading ClassPulse...
      </div>
    );
  }

  if (!currentUser) {
    return <RoleSelectionPage />;
  }

  const handleOpenIntervention = (student: Student) => {
    setInterventionStudent(student);
    setIsInterventionModalOpen(true);
  };

  const handleOpenEditStudent = (student: Student) => {
    setEditingStudent(student);
    setIsEditStudentOpen(true);
  };

  const handleOpenAttendance = (classId: string, className: string, students: Student[]) => {
    setAttendanceClass({ id: classId, name: className, students });
    setIsAttendanceOpen(true);
  };

  // 1. STUDENT VIEW
  if (currentUser.role === 'STUDENT') {
    return (
      <StudentLayout currentPage={currentPage} onNavigate={setCurrentPage}>
        {currentPage === 'student-monthly-report' && <StudentMonthlyReportPage />}
        {currentPage === 'student-assignments' && <StudentAssignmentsPage />}
        {currentPage === 'student-doubts' && <StudentDoubtsPage />}
        {currentPage === 'student-attendance' && <StudentAttendancePage />}
        {currentPage === 'student-marks' && <StudentMarksPage />}
        {currentPage === 'student-timetable' && <StudentTimetablePage />}
        {currentPage === 'student-messages' && <StudentMessagesPage />}
        {currentPage === 'student-announcements' && <StudentAnnouncementsPage />}
        {(currentPage === 'student-dashboard' || !currentPage) && (
          <StudentDashboardPage onNavigate={setCurrentPage} />
        )}
      </StudentLayout>
    );
  }

  // 2. PRINCIPAL / SCHOOL ADMIN VIEW
  if (currentUser.role === 'SCHOOL_ADMIN' || currentUser.role === 'ADMIN') {
    return (
      <PrincipalLayout currentPage={currentPage} onNavigate={setCurrentPage}>
        {currentPage === 'principal-dashboard' && <PrincipalDashboardPage />}
        {currentPage === 'principal-monthly-analytics' && <PrincipalMonthlyAnalyticsPage />}
        {currentPage === 'principal-assignments' && <PrincipalAssignmentsPage />}
        {currentPage === 'principal-classes' && <ClassManagementPage />}
        {currentPage === 'principal-teachers' && <TeacherManagementPage />}
        {currentPage === 'principal-timetables' && <TimetableManagementPage />}
        {currentPage === 'principal-exams' && <ExamManagementPage />}
        {currentPage === 'principal-reports' && <PrincipalReportsPage />}
        {currentPage === 'principal-announcements' && <PrincipalAnnouncementsPage />}
        {(currentPage === 'principal-dashboard' || !currentPage) && <PrincipalDashboardPage />}
      </PrincipalLayout>
    );
  }

  // 3. TEACHER VIEW (DEFAULT)
  const renderTeacherContent = () => {
    if (currentPage === 'student-detail' && selectedStudentId) {
      return (
        <StudentDetailPage
          key={`${selectedStudentId}-${refreshKey}`}
          studentId={selectedStudentId}
          onBack={() => setCurrentPage('teacher-students')}
          onOpenIntervention={handleOpenIntervention}
          onOpenEditStudent={handleOpenEditStudent}
        />
      );
    }

    switch (currentPage) {
      case 'teacher-monthly-reports':
        return <TeacherMonthlyReportsPage key={`monthly-reports-${refreshKey}`} />;
      case 'teacher-assignments':
        return <TeacherAssignmentsPage key={`assignments-${refreshKey}`} />;
      case 'teacher-doubts':
        return <TeacherDoubtsPage key={`doubts-${refreshKey}`} />;
      case 'teacher-timetable':
        return <TeacherTimetablePage key={`timetable-${refreshKey}`} />;
      case 'teacher-announcements':
        return <TeacherAnnouncementsPage key={`announcements-${refreshKey}`} />;
      case 'teacher-students':
        return (
          <StudentsPage
            key={`students-${refreshKey}`}
            onSelectStudent={(id) => {
              setSelectedStudentId(id);
              setCurrentPage('student-detail');
            }}
            onOpenIntervention={handleOpenIntervention}
            onOpenEditStudent={handleOpenEditStudent}
            onOpenCreateStudent={() => setIsCreateStudentOpen(true)}
            onOpenAttendance={handleOpenAttendance}
          />
        );
      case 'teacher-exams':
        return <ExamsPage key={`exams-${refreshKey}`} />;
      case 'teacher-interventions':
        return <InterventionsPage key={`interventions-${refreshKey}`} />;
      case 'teacher-import':
        return <DataImportPage />;
      case 'teacher-messages':
        return <TeacherMessagesPage key={`messages-${refreshKey}`} />;
      case 'teacher-dashboard':
      default:
        return (
          <DashboardPage
            key={`dashboard-${refreshKey}`}
            onSelectStudent={(id) => {
              setSelectedStudentId(id);
              setCurrentPage('student-detail');
            }}
            onOpenIntervention={handleOpenIntervention}
            onOpenAttendance={handleOpenAttendance}
            onOpenCreateStudent={() => setIsCreateStudentOpen(true)}
            onNavigate={setCurrentPage}
          />
        );
    }
  };

  return (
    <TeacherLayout currentPage={currentPage} onNavigate={setCurrentPage}>
      {renderTeacherContent()}

      {/* Intervention Modal */}
      {interventionStudent && (
        <InterventionModal
          studentId={interventionStudent.id}
          studentName={interventionStudent.name}
          schoolId={interventionStudent.school_id}
          classId={interventionStudent.class_id}
          isOpen={isInterventionModalOpen}
          onClose={() => setIsInterventionModalOpen(false)}
          onSuccess={() => {
            setRefreshKey((k) => k + 1);
            alert('Intervention action plan recorded successfully!');
          }}
        />
      )}

      {/* Create Student Modal */}
      {schoolId && (
        <CreateStudentModal
          schoolId={schoolId}
          classes={classes}
          isOpen={isCreateStudentOpen}
          onClose={() => setIsCreateStudentOpen(false)}
          onSuccess={() => {
            setRefreshKey((k) => k + 1);
            alert('Student enrolled successfully!');
          }}
        />
      )}

      {/* Edit Student Details Modal */}
      {editingStudent && (
        <EditStudentModal
          student={editingStudent}
          isOpen={isEditStudentOpen}
          onClose={() => setIsEditStudentOpen(false)}
          onSuccess={() => {
            setRefreshKey((k) => k + 1);
            alert('Student details updated successfully!');
          }}
        />
      )}

      {/* Class Attendance Taking Modal */}
      {attendanceClass && (
        <TakeAttendanceModal
          classId={attendanceClass.id}
          className={attendanceClass.name}
          students={attendanceClass.students}
          isOpen={isAttendanceOpen}
          onClose={() => setIsAttendanceOpen(false)}
          onSuccess={() => {
            setRefreshKey((k) => k + 1);
            alert('Class attendance sheet submitted successfully! Cohort analytics updated.');
          }}
        />
      )}
    </TeacherLayout>
  );
};

export function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

export default App;
