import React from 'react';
import {
  Activity,
  AlertOctagon,
  BookOpen,
  FileSpreadsheet,
  GraduationCap,
  LayoutDashboard,
  Users,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onNavigate }) => {
  const { currentUser, role } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-pulse">
          <Activity size={20} />
        </div>
        <div className="logo-text">
          <h2>ClassPulse</h2>
          <p>Early Learning Gap AI</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        <button
          className={`nav-item ${currentPage === 'dashboard' ? 'active' : ''}`}
          onClick={() => onNavigate('dashboard')}
        >
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </button>

        <button
          className={`nav-item ${currentPage === 'students' ? 'active' : ''}`}
          onClick={() => onNavigate('students')}
        >
          <Users size={18} />
          <span>Students & Risks</span>
        </button>

        <button
          className={`nav-item ${currentPage === 'interventions' ? 'active' : ''}`}
          onClick={() => onNavigate('interventions')}
        >
          <GraduationCap size={18} />
          <span>Interventions</span>
        </button>

        {role === 'SCHOOL_ADMIN' || role === 'ADMIN' ? (
          <button
            className={`nav-item ${currentPage === 'import' ? 'active' : ''}`}
            onClick={() => onNavigate('import')}
          >
            <FileSpreadsheet size={18} />
            <span>Data Ingestion</span>
          </button>
        ) : null}
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile-badge">
          <div className="user-info">
            <h4>{currentUser?.name || 'ClassPulse User'}</h4>
            <p>{role?.replace(/_/g, ' ')}</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
