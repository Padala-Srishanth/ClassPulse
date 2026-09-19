import React, { useState } from 'react';
import { Activity, AlertCircle, ArrowLeft, BookOpen, Lock, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';

interface TeacherLoginPageProps {
  onBack: () => void;
  onSuccess: () => void;
}

const TEACHER_HINTS = [
  { id: 'teacher-uid-001', name: 'Sarah Jenkins (Mathematics)' },
  { id: 'teacher-uid-002', name: 'Rajesh Sharma (Physics)' },
  { id: 'teacher-uid-005', name: 'Pooja Bose (English)' },
];

export const TeacherLoginPage: React.FC<TeacherLoginPageProps> = ({ onBack, onSuccess }) => {
  const { loginWithCredentials } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSlowLoading, setIsSlowLoading] = useState(false);

  React.useEffect(() => {
    let timer: any;
    if (isLoading) {
      timer = setTimeout(() => setIsSlowLoading(true), 3500);
    } else {
      setIsSlowLoading(false);
    }
    return () => clearTimeout(timer);
  }, [isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please enter your Teacher ID and password.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const result = await authApi.login('TEACHER', username.trim(), password.trim());
      loginWithCredentials(result.user as any, result.token);
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Invalid credentials. Please check your Teacher ID.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickSelect = (teacherId: string) => {
    setUsername(teacherId);
    setPassword(teacherId);
    setError(null);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: "'Inter', 'Outfit', system-ui, sans-serif",
      }}
    >
      {/* Background orbs */}
      <div style={{
        position: 'absolute', top: '-20%', left: '-10%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)',
      }} />
      <div style={{
        position: 'absolute', bottom: '-15%', right: '-10%',
        width: '400px', height: '400px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.10) 0%, transparent 70%)',
      }} />

      {/* Card */}
      <div style={{
        maxWidth: '460px', width: '100%',
        background: 'rgba(255,255,255,0.04)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(99,102,241,0.25)',
        borderRadius: '24px',
        padding: '40px 36px',
        boxShadow: '0 25px 60px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05)',
        position: 'relative', zIndex: 1,
      }}>
        {/* Back button */}
        <button
          onClick={onBack}
          style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#94a3b8', fontSize: '0.82rem', fontWeight: 600,
            marginBottom: '28px', padding: '0', transition: 'color 0.2s ease',
          }}
          onMouseEnter={e => (e.currentTarget.style.color = '#6366f1')}
          onMouseLeave={e => (e.currentTarget.style.color = '#94a3b8')}
        >
          <ArrowLeft size={16} />
          Back to role selection
        </button>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '64px', height: '64px', borderRadius: '18px',
            background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '16px',
            boxShadow: '0 8px 24px rgba(79,70,229,0.35)',
          }}>
            <BookOpen size={32} color="white" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
            <Activity size={18} color="#6366f1" />
            <span style={{ fontSize: '0.95rem', fontWeight: 800, color: 'white', letterSpacing: '-0.01em' }}>ClassPulse</span>
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'white', margin: '0 0 6px', letterSpacing: '-0.02em' }}>
            Teacher Login
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: 0, lineHeight: 1.5 }}>
            Enter your Teacher ID to access your classroom portal
          </p>
        </div>

        {/* Quick-select teacher buttons */}
        <div style={{ marginBottom: '20px' }}>
          <p style={{ color: '#64748b', fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '8px', margin: '0 0 8px' }}>
            Quick Select Teacher:
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {TEACHER_HINTS.map(t => (
              <button
                key={t.id}
                type="button"
                onClick={() => handleQuickSelect(t.id)}
                style={{
                  padding: '8px 12px', borderRadius: '10px',
                  border: username === t.id ? '1px solid rgba(99,102,241,0.6)' : '1px solid rgba(99,102,241,0.25)',
                  background: username === t.id ? 'rgba(79,70,229,0.25)' : 'rgba(79,70,229,0.08)',
                  color: username === t.id ? '#c7d2fe' : '#94a3b8',
                  fontSize: '0.8rem', fontWeight: 600,
                  cursor: 'pointer', textAlign: 'left',
                  transition: 'all 0.15s ease',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}
              >
                <span>{t.name}</span>
                <span style={{ fontSize: '0.72rem', color: '#6366f1', fontFamily: 'monospace' }}>{t.id}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '10px',
            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
            color: '#fca5a5', padding: '12px 16px', borderRadius: '12px',
            marginBottom: '16px', fontSize: '0.85rem', fontWeight: 500,
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', color: '#cbd5e1', fontSize: '0.82rem', fontWeight: 700, marginBottom: '8px', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Teacher ID
            </label>
            <div style={{ position: 'relative' }}>
              <User size={16} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
              <input
                id="teacher-username"
                type="text"
                value={username}
                onChange={e => { setUsername(e.target.value); setError(null); }}
                placeholder="e.g. teacher-uid-001"
                autoComplete="username"
                style={{
                  width: '100%', boxSizing: 'border-box',
                  paddingLeft: '42px', paddingRight: '14px', paddingTop: '12px', paddingBottom: '12px',
                  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '12px', color: 'white', fontSize: '0.95rem',
                  outline: 'none', transition: 'border-color 0.2s ease',
                  fontFamily: 'monospace',
                }}
                onFocus={e => (e.target.style.borderColor = 'rgba(99,102,241,0.6)')}
                onBlur={e => (e.target.style.borderColor = 'rgba(255,255,255,0.12)')}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', color: '#cbd5e1', fontSize: '0.82rem', fontWeight: 700, marginBottom: '8px', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
              <input
                id="teacher-password"
                type="password"
                value={password}
                onChange={e => { setPassword(e.target.value); setError(null); }}
                placeholder="Same as your Teacher ID"
                autoComplete="current-password"
                style={{
                  width: '100%', boxSizing: 'border-box',
                  paddingLeft: '42px', paddingRight: '14px', paddingTop: '12px', paddingBottom: '12px',
                  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '12px', color: 'white', fontSize: '0.95rem',
                  outline: 'none', transition: 'border-color 0.2s ease',
                }}
                onFocus={e => (e.target.style.borderColor = 'rgba(99,102,241,0.6)')}
                onBlur={e => (e.target.style.borderColor = 'rgba(255,255,255,0.12)')}
              />
            </div>
          </div>

          <button
            id="teacher-login-submit"
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: '8px',
              padding: '13px',
              background: isLoading
                ? 'rgba(79,70,229,0.4)'
                : 'linear-gradient(135deg, #4f46e5, #7c3aed)',
              border: 'none', borderRadius: '12px', color: 'white',
              fontSize: '1rem', fontWeight: 700, cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: isLoading ? 'none' : '0 4px 20px rgba(79,70,229,0.35)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            }}
            onMouseEnter={e => { if (!isLoading) e.currentTarget.style.transform = 'translateY(-1px)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
          >
            {isLoading ? 'Signing in...' : 'Sign In to Teacher Portal'}
          </button>

          {isLoading && isSlowLoading && (
            <p style={{ color: '#fbbf24', fontSize: '0.8rem', margin: '10px 0 0', textAlign: 'center', lineHeight: 1.4 }}>
              ⚡ Waking up cloud server (free-tier spin-up takes ~45s if idle)...
            </p>
          )}
        </form>

        {/* Hint */}
        <div style={{
          marginTop: '20px', padding: '14px 16px',
          background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)',
          borderRadius: '10px',
        }}>
          <p style={{ color: '#a5b4fc', fontSize: '0.78rem', margin: '0 0 4px', fontWeight: 600 }}>
            💡 Your credentials:
          </p>
          <p style={{ color: '#94a3b8', fontSize: '0.76rem', margin: 0, lineHeight: 1.6 }}>
            Format: <strong style={{ color: '#a5b4fc' }}>teacher-uid-001</strong> through <strong style={{ color: '#a5b4fc' }}>teacher-uid-035</strong><br />
            Password = same as your Teacher ID.<br />
            Use the Quick Select buttons above to auto-fill.
          </p>
        </div>
      </div>

      <style>{`
        input::placeholder { color: #475569; }
      `}</style>
    </div>
  );
};
