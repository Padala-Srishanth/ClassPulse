import React from 'react';
import { Bell, LogOut, School, ShieldCheck, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';

export const Navbar: React.FC = () => {
  const { currentUser, role, schoolId, loginAsDemo, logout } = useAuth();

  return (
    <header className="navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#475569', fontSize: '0.88rem' }}>
          <School size={18} color="#4f46e5" />
          <span>School: <strong>{schoolId || 'ClassPulse Central'}</strong></span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Role Quick Switcher for Easy Demonstration */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#f1f5f9', padding: '4px 8px', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Role:</span>
          <button
            onClick={() => loginAsDemo('TEACHER')}
            style={{
              padding: '3px 8px',
              fontSize: '0.75rem',
              fontWeight: 600,
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              background: role === 'TEACHER' ? '#4f46e5' : 'transparent',
              color: role === 'TEACHER' ? 'white' : '#64748b',
            }}
          >
            Teacher
          </button>
          <button
            onClick={() => loginAsDemo('SCHOOL_ADMIN')}
            style={{
              padding: '3px 8px',
              fontSize: '0.75rem',
              fontWeight: 600,
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              background: role === 'SCHOOL_ADMIN' ? '#4f46e5' : 'transparent',
              color: role === 'SCHOOL_ADMIN' ? 'white' : '#64748b',
            }}
          >
            Principal / Admin
          </button>
        </div>

        <button
          onClick={logout}
          className="btn btn-outline btn-sm"
          title="Sign out"
          style={{ padding: '6px 10px' }}
        >
          <LogOut size={15} />
          Sign Out
        </button>
      </div>
    </header>
  );
};
