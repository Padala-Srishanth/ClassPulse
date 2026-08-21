import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { StudentsPage } from './pages/StudentsPage';
import { StudentDetailPage } from './pages/StudentDetailPage';
import { InterventionsPage } from './pages/InterventionsPage';
import { DataImportPage } from './pages/DataImportPage';
import { InterventionModal } from './components/InterventionModal';
import { Student } from './types';

const MainApp: React.FC = () => {
  const { currentUser, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);

  // Intervention Modal State
  const [interventionStudent, setInterventionStudent] = useState<Student | null>(null);
  const [isInterventionModalOpen, setIsInterventionModalOpen] = useState(false);

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

  const renderContent = () => {
    if (currentPage === 'student-detail' && selectedStudentId) {
      return (
        <StudentDetailPage
          studentId={selectedStudentId}
          onBack={() => setCurrentPage('students')}
          onOpenIntervention={handleOpenIntervention}
        />
      );
    }

    switch (currentPage) {
      case 'dashboard':
        return (
          <DashboardPage
            onSelectStudent={(id) => {
              setSelectedStudentId(id);
              setCurrentPage('student-detail');
            }}
            onOpenIntervention={handleOpenIntervention}
          />
        );
      case 'students':
        return (
          <StudentsPage
            onSelectStudent={(id) => {
              setSelectedStudentId(id);
              setCurrentPage('student-detail');
            }}
            onOpenIntervention={handleOpenIntervention}
          />
        );
      case 'interventions':
        return <InterventionsPage />;
      case 'import':
        return <DataImportPage />;
      default:
        return (
          <DashboardPage
            onSelectStudent={(id) => {
              setSelectedStudentId(id);
              setCurrentPage('student-detail');
            }}
            onOpenIntervention={handleOpenIntervention}
          />
        );
    }
  };

  return (
    <Layout currentPage={currentPage} onNavigate={setCurrentPage}>
      {renderContent()}

      {interventionStudent && (
        <InterventionModal
          studentId={interventionStudent.id}
          studentName={interventionStudent.name}
          schoolId={interventionStudent.school_id}
          classId={interventionStudent.class_id}
          isOpen={isInterventionModalOpen}
          onClose={() => setIsInterventionModalOpen(false)}
          onSuccess={() => {
            alert('Intervention action plan recorded successfully!');
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
