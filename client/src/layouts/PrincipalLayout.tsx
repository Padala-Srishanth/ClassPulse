import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  BarChart3,
  Bell,
  BookOpen,
  LayoutDashboard,
  LogOut,
  Megaphone,
  Shield,
  Users,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface PrincipalLayoutProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  children: React.ReactNode;
}

const NAV_ITEMS = [
  { id: 'principal-dashboard', label: 'School Overview', icon: LayoutDashboard },
  { id: 'principal-classes', label: 'Class Management', icon: BookOpen },
  { id: 'principal-teachers', label: 'Teachers', icon: Users },
  { id: 'principal-reports', label: 'Reports & Analytics', icon: BarChart3 },
  { id: 'principal-announcements', label: 'Announcements', icon: Megaphone },
];

export const PrincipalLayout: React.FC<PrincipalLayoutProps> = ({ currentPage, onNavigate, children }) => {
  const { currentUser, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f0fdf4', fontFamily: "'Inter', sans-serif" }}>
      {/* Sidebar */}
      <aside style={{
        width: sidebarOpen ? '252px' : '72px',
        background: 'linear-gradient(180deg, #064e3b 0%, #065f46 100%)',
        display: 'flex', flexDirection: 'column',
        transition: 'width 0.3s ease',
        flexShrink: 0,
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
            background: 'linear-gradient(135deg, #059669, #10b981)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Shield size={22} color="white" />
          </div>
          {sidebarOpen && (
            <div>
              <div style={{ color: 'white', fontWeight: 800, fontSize: '1rem' }}>ClassPulse</div>
              <div style={{ color: '#6ee7b7', fontSize: '0.7rem', fontWeight: 600 }}>Principal Portal</div>
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
                  background: isActive ? 'rgba(16,185,129,0.2)' : 'transparent',
                  color: isActive ? '#6ee7b7' : '#a7f3d0',
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
                  <div style={{ marginLeft: 'auto', width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
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
              background: 'linear-gradient(135deg, #059669, #10b981)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontWeight: 700, fontSize: '0.8rem',
            }}>
              {currentUser?.name?.charAt(0) || 'P'}
            </div>
            {sidebarOpen && (
              <div style={{ overflow: 'hidden', flex: 1 }}>
                <div style={{ color: 'white', fontWeight: 600, fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {currentUser?.name || 'Principal'}
                </div>
                <div style={{ color: '#6ee7b7', fontSize: '0.7rem' }}>School Admin</div>
              </div>
            )}
          </div>
          <button
            onClick={logout}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: '12px',
              padding: '10px 12px', borderRadius: '10px', border: 'none',
              cursor: 'pointer', background: 'transparent', color: '#6ee7b7',
              marginTop: '4px', transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,0.15)'; (e.currentTarget as HTMLElement).style.color = '#fca5a5'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = '#6ee7b7'; }}
          >
            <LogOut size={18} style={{ flexShrink: 0 }} />
            {sidebarOpen && <span style={{ fontSize: '0.85rem' }}>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{
        flex: 1, marginLeft: sidebarOpen ? '252px' : '72px',
        transition: 'margin-left 0.3s ease',
        minHeight: '100vh', display: 'flex', flexDirection: 'column',
      }}>
        <header style={{
          background: 'white', borderBottom: '1px solid #d1fae5',
          padding: '0 28px', height: '60px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          position: 'sticky', top: 0, zIndex: 50,
        }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#064e3b', margin: 0 }}>
            {NAV_ITEMS.find(n => n.id === currentPage)?.label || 'School Overview'}
          </h2>
          <span style={{
            background: '#d1fae5', color: '#065f46', padding: '4px 10px',
            borderRadius: '20px', fontSize: '0.72rem', fontWeight: 700,
          }}>PRINCIPAL</span>
        </header>

        <div style={{ padding: '28px', flex: 1 }}>
          {children}
        </div>
      </main>
    </div>
  );
};
