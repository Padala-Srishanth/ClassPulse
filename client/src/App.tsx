import React, { useEffect, useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { StudentsPage } from './pages/StudentsPage';
import { StudentDetailPage } from './pages/StudentDetailPage';
import { InterventionsPage } from './pages/InterventionsPage';
import { DataImportPage } from './pages/DataImportPage';
import { InterventionModal } from './components/InterventionModal';
import { CreateStudentModal } from './components/CreateStudentModal';
import { EditStudentModal } from './components/EditStudentModal';
import { TakeAttendanceModal } from './components/TakeAttendanceModal';
import { classesApi } from './api/classes';
import { SchoolClass, Student } from './types';

const MainApp: React.FC = () => {
  const { currentUser, schoolId, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
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

  // Key to force refresh sub-views after creation/update
  const [refreshKey, setRefreshKey] = useState(0);

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
    return <LoginPage />;
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

  const renderContent = () => {
    if (currentPage === 'student-detail' && selectedStudentId) {
      return (
        <StudentDetailPage
          key={`${selectedStudentId}-${refreshKey}`}
          studentId={selectedStudentId}
          onBack={() => setCurrentPage('students')}
          onOpenIntervention={handleOpenIntervention}
          onOpenEditStudent={handleOpenEditStudent}
        />
      );
    }

    switch (currentPage) {
      case 'dashboard':
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
          />
        );
      case 'students':
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
      case 'interventions':
        return <InterventionsPage key={`interventions-${refreshKey}`} />;
      case 'import':
        return <DataImportPage />;
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
          />
        );
    }
  };

  return (
    <Layout currentPage={currentPage} onNavigate={setCurrentPage}>
      {renderContent()}

      {/* 1. Intervention Modal */}
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

      {/* 2. Create Student Modal */}
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

      {/* 3. Edit Student Details Modal */}
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

      {/* 4. Class Attendance Taking Modal */}
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
    </Layout>
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
