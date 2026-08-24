import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  BookOpen,
  ChevronDown,
  Database,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Megaphone,
  Users,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface TeacherLayoutProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  children: React.ReactNode;
}

const NAV_ITEMS = [
  { id: 'teacher-dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'teacher-announcements', label: 'Announcements', icon: Megaphone },
  { id: 'teacher-students', label: 'My Students', icon: Users },
  { id: 'teacher-exams', label: 'Exams & Marks', icon: BookOpen },
  { id: 'teacher-interventions', label: 'Interventions', icon: AlertCircle },
  { id: 'teacher-import', label: 'Import Data', icon: Database },
];

export const TeacherLayout: React.FC<TeacherLayoutProps> = ({ currentPage, onNavigate, children }) => {
  const { currentUser, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8fafc', fontFamily: "'Inter', sans-serif" }}>
      {/* Sidebar */}
      <aside style={{
        width: sidebarOpen ? '240px' : '72px',
        background: 'linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%)',
        display: 'flex', flexDirection: 'column',
        transition: 'width 0.3s ease',
        flexShrink: 0,
        position: 'fixed', top: 0, left: 0, bottom: 0,
        zIndex: 100,
        overflowX: 'hidden',
      }}>
        {/* Logo */}
        <div style={{
          padding: '20px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)',
          display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer',
        }} onClick={() => setSidebarOpen(!sidebarOpen)}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '10px', flexShrink: 0,
            background: 'linear-gradient(135deg, #6366f1, #a855f7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Activity size={22} color="white" />
          </div>
          {sidebarOpen && (
            <div>
              <div style={{ color: 'white', fontWeight: 800, fontSize: '1rem' }}>ClassPulse</div>
              <div style={{ color: '#a78bfa', fontSize: '0.7rem', fontWeight: 600 }}>Teacher Portal</div>
            </div>
          )}
        </div>

        {/* Nav items */}
        <nav style={{ padding: '12px 8px', flex: 1 }}>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                onClick={() => onNavigate(item.id)}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center',
                  gap: '12px', padding: '10px 12px', borderRadius: '10px',
                  border: 'none', cursor: 'pointer', marginBottom: '4px',
                  background: isActive ? 'rgba(99,102,241,0.2)' : 'transparent',
                  color: isActive ? '#a78bfa' : '#94a3b8',
                  transition: 'all 0.15s ease',
                  textAlign: 'left',
                  whiteSpace: 'nowrap', overflow: 'hidden',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.06)';
                }}
                onMouseLeave={(e) => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent';
                }}
              >
                <Icon size={18} style={{ flexShrink: 0 }} />
                {sidebarOpen && <span style={{ fontSize: '0.875rem', fontWeight: isActive ? 700 : 500 }}>{item.label}</span>}
                {isActive && sidebarOpen && (
                  <div style={{ marginLeft: 'auto', width: '6px', height: '6px', borderRadius: '50%', background: '#a78bfa' }} />
                )}
              </button>
            );
          })}
        </nav>

        {/* User + logout */}
        <div style={{ padding: '12px 8px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '10px',
            padding: '10px 12px', borderRadius: '10px',
            background: 'rgba(255,255,255,0.04)',
            overflow: 'hidden',
          }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontWeight: 700, fontSize: '0.8rem',
            }}>
              {currentUser?.name?.charAt(0) || 'T'}
            </div>
            {sidebarOpen && (
              <div style={{ overflow: 'hidden', flex: 1 }}>
                <div style={{ color: 'white', fontWeight: 600, fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {currentUser?.name || 'Teacher'}
                </div>
                <div style={{ color: '#64748b', fontSize: '0.7rem' }}>Teacher</div>
              </div>
            )}
          </div>
          <button
            onClick={logout}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: '12px',
              padding: '10px 12px', borderRadius: '10px', border: 'none',
              cursor: 'pointer', background: 'transparent', color: '#64748b',
              marginTop: '4px', transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,0.1)'; (e.currentTarget as HTMLElement).style.color = '#ef4444'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = '#64748b'; }}
          >
            <LogOut size={18} style={{ flexShrink: 0 }} />
            {sidebarOpen && <span style={{ fontSize: '0.85rem' }}>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{
        flex: 1, marginLeft: sidebarOpen ? '240px' : '72px',
        transition: 'margin-left 0.3s ease',
        minHeight: '100vh', display: 'flex', flexDirection: 'column',
      }}>
        {/* Top bar */}
        <header style={{
          background: 'white', borderBottom: '1px solid #e2e8f0',
          padding: '0 28px', height: '60px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          position: 'sticky', top: 0, zIndex: 50,
        }}>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              {NAV_ITEMS.find(n => n.id === currentPage)?.label || 'Teacher Dashboard'}
            </h2>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              background: '#eef2ff', color: '#4f46e5', padding: '4px 10px',
              borderRadius: '20px', fontSize: '0.72rem', fontWeight: 700,
            }}>TEACHER</span>
          </div>
        </header>

        <div style={{ padding: '28px', flex: 1 }}>
          {children}
        </div>
      </main>
    </div>
  );
};
