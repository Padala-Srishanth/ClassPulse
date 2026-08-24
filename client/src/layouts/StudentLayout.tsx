import React, { useState } from 'react';
import {
  Activity,
  Bell,
  BookOpen,
  CalendarDays,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  MessageCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface StudentLayoutProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  children: React.ReactNode;
}

const NAV_ITEMS = [
  { id: 'student-dashboard', label: 'My Dashboard', icon: LayoutDashboard },
  { id: 'student-attendance', label: 'Attendance', icon: CalendarDays },
  { id: 'student-marks', label: 'My Marks', icon: BookOpen },
  { id: 'student-messages', label: 'Messages', icon: MessageCircle },
  { id: 'student-announcements', label: 'Announcements', icon: Bell },
];

export const StudentLayout: React.FC<StudentLayoutProps> = ({ currentPage, onNavigate, children }) => {
  const { currentUser, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f0f9ff', fontFamily: "'Inter', sans-serif" }}>
      {/* Sidebar */}
      <aside style={{
        width: sidebarOpen ? '240px' : '72px',
        background: 'linear-gradient(180deg, #0c4a6e 0%, #075985 100%)',
        display: 'flex', flexDirection: 'column',
        transition: 'width 0.3s ease', flexShrink: 0,
        position: 'fixed', top: 0, left: 0, bottom: 0,
        zIndex: 100, overflowX: 'hidden',
      }}>
        {/* Logo */}
        <div style={{
          padding: '20px 16px', borderBottom: '1px solid rgba(255,255,255,0.1)',
          display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer',
        }} onClick={() => setSidebarOpen(!sidebarOpen)}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '10px', flexShrink: 0,
            background: 'linear-gradient(135deg, #0891b2, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <GraduationCap size={22} color="white" />
          </div>
          {sidebarOpen && (
            <div>
              <div style={{ color: 'white', fontWeight: 800, fontSize: '1rem' }}>ClassPulse</div>
              <div style={{ color: '#7dd3fc', fontSize: '0.7rem', fontWeight: 600 }}>Student Portal</div>
            </div>
          )}
        </div>

        {/* Nav */}
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
                  background: isActive ? 'rgba(14,165,233,0.2)' : 'transparent',
                  color: isActive ? '#7dd3fc' : '#bae6fd',
                  transition: 'all 0.15s ease', textAlign: 'left',
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
                  <div style={{ marginLeft: 'auto', width: '6px', height: '6px', borderRadius: '50%', background: '#38bdf8' }} />
                )}
              </button>
            );
          })}
        </nav>

        {/* User */}
        <div style={{ padding: '12px 8px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '10px',
            padding: '10px 12px', borderRadius: '10px',
            background: 'rgba(255,255,255,0.06)', overflow: 'hidden',
          }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
              background: 'linear-gradient(135deg, #0891b2, #06b6d4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontWeight: 700, fontSize: '0.8rem',
            }}>
              {currentUser?.name?.charAt(0) || 'S'}
            </div>
            {sidebarOpen && (
              <div style={{ overflow: 'hidden', flex: 1 }}>
                <div style={{ color: 'white', fontWeight: 600, fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {currentUser?.name || 'Student'}
                </div>
                <div style={{ color: '#7dd3fc', fontSize: '0.7rem' }}>Student</div>
              </div>
            )}
          </div>
          <button
            onClick={logout}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: '12px',
              padding: '10px 12px', borderRadius: '10px', border: 'none',
              cursor: 'pointer', background: 'transparent', color: '#7dd3fc',
              marginTop: '4px', transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,0.15)'; (e.currentTarget as HTMLElement).style.color = '#fca5a5'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = '#7dd3fc'; }}
          >
            <LogOut size={18} style={{ flexShrink: 0 }} />
            {sidebarOpen && <span style={{ fontSize: '0.85rem' }}>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main style={{
        flex: 1, marginLeft: sidebarOpen ? '240px' : '72px',
        transition: 'margin-left 0.3s ease',
        minHeight: '100vh', display: 'flex', flexDirection: 'column',
      }}>
        <header style={{
          background: 'white', borderBottom: '1px solid #bae6fd',
          padding: '0 28px', height: '60px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          position: 'sticky', top: 0, zIndex: 50,
        }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#0c4a6e', margin: 0 }}>
            {NAV_ITEMS.find(n => n.id === currentPage)?.label || 'My Dashboard'}
          </h2>
          <span style={{
            background: '#e0f2fe', color: '#0369a1', padding: '4px 10px',
            borderRadius: '20px', fontSize: '0.72rem', fontWeight: 700,
          }}>STUDENT</span>
        </header>

        <div style={{ padding: '28px', flex: 1 }}>
          {children}
        </div>
      </main>
    </div>
  );
};
