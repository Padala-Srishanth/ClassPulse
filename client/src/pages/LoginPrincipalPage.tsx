import React, { useState } from 'react';
import { Activity, AlertCircle, ArrowLeft, Lock, Shield, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';

interface PrincipalLoginPageProps {
  onBack: () => void;
  onSuccess: () => void;
}

export const PrincipalLoginPage: React.FC<PrincipalLoginPageProps> = ({ onBack, onSuccess }) => {
  const { loginWithCredentials } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please enter your Principal ID and password.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const result = await authApi.login('PRINCIPAL', username.trim(), password.trim());
      loginWithCredentials(result.user as any, result.token);
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Invalid credentials. Please check your Principal ID.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = () => {
    setUsername('sadmin-uid-001');
    setPassword('sadmin-uid-001');
    setError(null);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #064e3b 50%, #0f172a 100%)',
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
        background: 'radial-gradient(circle, rgba(5,150,105,0.12) 0%, transparent 70%)',
      }} />
      <div style={{
        position: 'absolute', bottom: '-15%', right: '-10%',
        width: '400px', height: '400px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(4,120,87,0.10) 0%, transparent 70%)',
      }} />

      {/* Card */}
      <div style={{
        maxWidth: '440px', width: '100%',
        background: 'rgba(255,255,255,0.04)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(5,150,105,0.25)',
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
          onMouseEnter={e => (e.currentTarget.style.color = '#059669')}
          onMouseLeave={e => (e.currentTarget.style.color = '#94a3b8')}
        >
          <ArrowLeft size={16} />
          Back to role selection
        </button>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '64px', height: '64px', borderRadius: '18px',
            background: 'linear-gradient(135deg, #059669, #047857)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '16px',
            boxShadow: '0 8px 24px rgba(5,150,105,0.35)',
          }}>
            <Shield size={32} color="white" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
            <Activity size={18} color="#6366f1" />
            <span style={{ fontSize: '0.95rem', fontWeight: 800, color: 'white', letterSpacing: '-0.01em' }}>ClassPulse</span>
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'white', margin: '0 0 6px', letterSpacing: '-0.02em' }}>
            Principal Login
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: 0, lineHeight: 1.5 }}>
            Enter your Principal ID to access the school administration portal
          </p>
        </div>

        {/* Quick select */}
        <div style={{ marginBottom: '20px' }}>
          <p style={{ color: '#64748b', fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', margin: '0 0 8px' }}>
            Quick Select:
          </p>
          <button
            type="button"
            onClick={handleQuickFill}
            style={{
              width: '100%', padding: '10px 14px', borderRadius: '10px',
              border: username === 'sadmin-uid-001' ? '1px solid rgba(5,150,105,0.6)' : '1px solid rgba(5,150,105,0.25)',
              background: username === 'sadmin-uid-001' ? 'rgba(5,150,105,0.2)' : 'rgba(5,150,105,0.08)',
              color: username === 'sadmin-uid-001' ? '#a7f3d0' : '#94a3b8',
              fontSize: '0.82rem', fontWeight: 600,
              cursor: 'pointer', textAlign: 'left',
              transition: 'all 0.15s ease',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}
          >
            <span>👩‍💼 Dr. Evelyn Reed (Principal)</span>
            <span style={{ fontSize: '0.72rem', color: '#6ee7b7', fontFamily: 'monospace' }}>sadmin-uid-001</span>
          </button>
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
              Principal ID
            </label>
            <div style={{ position: 'relative' }}>
              <User size={16} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
              <input
                id="principal-username"
                type="text"
                value={username}
                onChange={e => { setUsername(e.target.value); setError(null); }}
                placeholder="e.g. sadmin-uid-001"
                autoComplete="username"
                style={{
                  width: '100%', boxSizing: 'border-box',
                  paddingLeft: '42px', paddingRight: '14px', paddingTop: '12px', paddingBottom: '12px',
                  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '12px', color: 'white', fontSize: '0.95rem',
                  outline: 'none', transition: 'border-color 0.2s ease',
                  fontFamily: 'monospace',
                }}
                onFocus={e => (e.target.style.borderColor = 'rgba(5,150,105,0.6)')}
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
                id="principal-password"
                type="password"
                value={password}
                onChange={e => { setPassword(e.target.value); setError(null); }}
                placeholder="Same as your Principal ID"
                autoComplete="current-password"
                style={{
                  width: '100%', boxSizing: 'border-box',
                  paddingLeft: '42px', paddingRight: '14px', paddingTop: '12px', paddingBottom: '12px',
                  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '12px', color: 'white', fontSize: '0.95rem',
                  outline: 'none', transition: 'border-color 0.2s ease',
                }}
                onFocus={e => (e.target.style.borderColor = 'rgba(5,150,105,0.6)')}
                onBlur={e => (e.target.style.borderColor = 'rgba(255,255,255,0.12)')}
              />
            </div>
          </div>

          <button
            id="principal-login-submit"
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: '8px',
              padding: '13px',
              background: isLoading
                ? 'rgba(5,150,105,0.4)'
                : 'linear-gradient(135deg, #059669, #047857)',
              border: 'none', borderRadius: '12px', color: 'white',
              fontSize: '1rem', fontWeight: 700, cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: isLoading ? 'none' : '0 4px 20px rgba(5,150,105,0.35)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            }}
            onMouseEnter={e => { if (!isLoading) e.currentTarget.style.transform = 'translateY(-1px)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
          >
            {isLoading ? 'Signing in...' : 'Sign In to Principal Portal'}
          </button>
        </form>

        {/* Hint */}
        <div style={{
          marginTop: '20px', padding: '14px 16px',
          background: 'rgba(5,150,105,0.08)', border: '1px solid rgba(5,150,105,0.2)',
          borderRadius: '10px',
        }}>
          <p style={{ color: '#6ee7b7', fontSize: '0.78rem', margin: '0 0 4px', fontWeight: 600 }}>
            💡 Your credentials:
          </p>
          <p style={{ color: '#94a3b8', fontSize: '0.76rem', margin: 0, lineHeight: 1.6 }}>
            Principal ID: <strong style={{ color: '#6ee7b7' }}>sadmin-uid-001</strong><br />
            Password = same as your Principal ID.<br />
            Use the Quick Select button above to auto-fill.
          </p>
        </div>
      </div>

      <style>{`
        input::placeholder { color: #475569; }
      `}</style>
    </div>
  );
};
