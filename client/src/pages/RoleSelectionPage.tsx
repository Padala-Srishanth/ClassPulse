import React, { useState } from 'react';
import { Activity, BookOpen, GraduationCap, Shield, ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';

type RoleChoice = 'TEACHER' | 'STUDENT' | 'SCHOOL_ADMIN';

interface RoleCard {
  role: RoleChoice;
  label: string;
  subtitle: string;
  description: string;
  icon: React.FC<any>;
  gradient: string;
  bgLight: string;
  accentColor: string;
  features: string[];
}

const ROLE_CARDS: RoleCard[] = [
  {
    role: 'TEACHER',
    label: 'Teacher',
    subtitle: 'Classroom Portal',
    description: 'Manage students, track attendance, conduct exams, and monitor learning gaps with AI-powered risk detection.',
    icon: BookOpen,
    gradient: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
    bgLight: '#eef2ff',
    accentColor: '#4f46e5',
    features: ['Student Management', 'Attendance Tracking', 'Exam & Grades', 'AI Risk Detection', 'Interventions'],
  },
  {
    role: 'STUDENT',
    label: 'Student',
    subtitle: 'Student Portal',
    description: 'View your attendance, marks, upcoming exams, and contact your teachers or principal.',
    icon: GraduationCap,
    gradient: 'linear-gradient(135deg, #0891b2 0%, #0e7490 100%)',
    bgLight: '#e0f2fe',
    accentColor: '#0891b2',
    features: ['My Attendance', 'My Marks & Grades', 'Teacher Messages', 'Announcements', 'Appointment Requests'],
  },
  {
    role: 'SCHOOL_ADMIN',
    label: 'Principal',
    subtitle: 'School Administration',
    description: 'Oversee the entire school: class analytics, teacher assignments, reports, and school-wide announcements.',
    icon: Shield,
    gradient: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
    bgLight: '#d1fae5',
    accentColor: '#059669',
    features: ['School Overview', 'Class Management', 'Teacher Assignments', 'Attendance Reports', 'Academic Analytics'],
  },
];

interface RoleSelectionPageProps {
  onRoleSelected?: (role: RoleChoice) => void;
}

export const RoleSelectionPage: React.FC<RoleSelectionPageProps> = ({ onRoleSelected }) => {
  const { loginAsDemo } = useAuth();
  const [hoveredRole, setHoveredRole] = useState<RoleChoice | null>(null);
  const [selectedRole, setSelectedRole] = useState<RoleChoice | null>(null);

  const handleRoleSelect = (role: RoleChoice) => {
    setSelectedRole(role);
    // Demo login directly — no intermediate login screen needed
    loginAsDemo(role as UserRole);
    if (onRoleSelected) onRoleSelected(role);
  };

  const handleTeacherPersonaSelect = (e: React.MouseEvent, teacherId: string) => {
    e.stopPropagation();
    setSelectedRole('TEACHER');
    loginAsDemo('TEACHER', 'school-001', teacherId);
    if (onRoleSelected) onRoleSelected('TEACHER');
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
      }}
    >
      {/* Animated background orbs */}
      <div style={{
        position: 'absolute', top: '-20%', left: '-10%',
        width: '600px', height: '600px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)',
        animation: 'pulse 6s ease-in-out infinite',
      }} />
      <div style={{
        position: 'absolute', bottom: '-20%', right: '-10%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.10) 0%, transparent 70%)',
        animation: 'pulse 8s ease-in-out infinite 2s',
      }} />

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '56px', position: 'relative', zIndex: 1 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '12px',
          marginBottom: '20px',
        }}>
          <div style={{
            width: '56px', height: '56px', borderRadius: '16px',
            background: 'linear-gradient(135deg, #6366f1, #a855f7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 40px rgba(99,102,241,0.4)',
          }}>
            <Activity size={30} color="white" />
          </div>
          <div style={{ textAlign: 'left' }}>
            <h1 style={{
              fontSize: '2rem', fontWeight: 900, color: 'white',
              letterSpacing: '-0.02em', margin: 0,
            }}>ClassPulse</h1>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              color: '#a78bfa', fontSize: '0.8rem', fontWeight: 600,
            }}>
              <Sparkles size={12} />
              <span>AI-Driven Early Learning Gap Detection</span>
            </div>
          </div>
        </div>

        <h2 style={{
          fontSize: '2.6rem', fontWeight: 800, color: 'white',
          marginBottom: '12px', letterSpacing: '-0.03em',
          lineHeight: 1.2,
        }}>
          Who are you?
        </h2>
        <p style={{
          color: '#94a3b8', fontSize: '1.05rem', maxWidth: '480px',
          lineHeight: 1.6,
        }}>
          Select your role to access your personalized ClassPulse portal.
        </p>
      </div>

      {/* Role Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '24px',
        maxWidth: '960px',
        width: '100%',
        position: 'relative',
        zIndex: 1,
      }}>
        {ROLE_CARDS.map((card) => {
          const Icon = card.icon;
          const isHovered = hoveredRole === card.role;
          const isSelected = selectedRole === card.role;

          return (
            <button
              key={card.role}
              id={`role-card-${card.role.toLowerCase()}`}
              onClick={() => handleRoleSelect(card.role)}
              onMouseEnter={() => setHoveredRole(card.role)}
              onMouseLeave={() => setHoveredRole(null)}
              style={{
                background: isHovered || isSelected
                  ? 'rgba(255,255,255,0.12)'
                  : 'rgba(255,255,255,0.06)',
                border: isSelected
                  ? `2px solid ${card.accentColor}`
                  : isHovered
                    ? '2px solid rgba(255,255,255,0.25)'
                    : '2px solid rgba(255,255,255,0.1)',
                borderRadius: '20px',
                padding: '32px 28px',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                transform: isHovered ? 'translateY(-6px) scale(1.02)' : 'translateY(0) scale(1)',
                boxShadow: isHovered
                  ? `0 20px 60px rgba(0,0,0,0.3), 0 0 40px ${card.accentColor}22`
                  : '0 4px 20px rgba(0,0,0,0.2)',
                backdropFilter: 'blur(10px)',
              }}
            >
              {/* Icon area */}
              <div style={{
                width: '60px', height: '60px', borderRadius: '16px',
                background: card.gradient,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: '20px',
                boxShadow: `0 8px 24px ${card.accentColor}44`,
                transition: 'transform 0.25s ease',
                transform: isHovered ? 'rotate(-4deg) scale(1.1)' : 'none',
              }}>
                <Icon size={28} color="white" />
              </div>

              <div style={{ marginBottom: '12px' }}>
                <h3 style={{
                  fontSize: '1.4rem', fontWeight: 800, color: 'white',
                  margin: '0 0 4px 0', letterSpacing: '-0.01em',
                }}>{card.label}</h3>
                <span style={{
                  fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em',
                  textTransform: 'uppercase', color: card.accentColor,
                }}>
                  {card.subtitle}
                </span>
              </div>

              <p style={{
                color: '#94a3b8', fontSize: '0.88rem', lineHeight: 1.65,
                marginBottom: '20px',
              }}>
                {card.description}
              </p>

              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 16px 0' }}>
                {card.features.map((f) => (
                  <li key={f} style={{
                    display: 'flex', alignItems: 'center', gap: '8px',
                    color: '#cbd5e1', fontSize: '0.82rem', marginBottom: '6px',
                  }}>
                    <div style={{
                      width: '6px', height: '6px', borderRadius: '50%',
                      background: card.accentColor, flexShrink: 0,
                    }} />
                    {f}
                  </li>
                ))}
              </ul>

              {card.role === 'TEACHER' && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '6px', fontWeight: 700, letterSpacing: '0.04em' }}>
                    QUICK-SELECT SUBJECT TEACHER:
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {[
                      { id: 'teacher-uid-001', label: '📐 Sarah Jenkins (Mathematics)' },
                      { id: 'teacher-uid-002', label: '⚛️ Rajesh Sharma (Physics)' },
                      { id: 'teacher-uid-005', label: '📖 Pooja Bose (English)' },
                    ].map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={(e) => handleTeacherPersonaSelect(e, t.id)}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '8px',
                          border: '1px solid rgba(124, 58, 237, 0.4)',
                          background: 'rgba(79, 70, 229, 0.15)',
                          color: '#c7d2fe',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'all 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'rgba(79, 70, 229, 0.35)';
                          e.currentTarget.style.color = '#ffffff';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(79, 70, 229, 0.15)';
                          e.currentTarget.style.color = '#c7d2fe';
                        }}
                      >
                        {t.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {card.role === 'STUDENT' && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '4px', fontWeight: 700, letterSpacing: '0.04em' }}>
                    DEMO STUDENT:
                  </div>
                  <div style={{
                    padding: '8px 12px', borderRadius: '8px',
                    background: 'rgba(8, 145, 178, 0.15)', border: '1px solid rgba(8, 145, 178, 0.4)',
                    color: '#bae6fd', fontSize: '0.76rem', fontWeight: 600,
                  }}>
                    👨🎓 Rahul Sharma — Class 10-A
                  </div>
                </div>
              )}

              {card.role === 'SCHOOL_ADMIN' && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '4px', fontWeight: 700, letterSpacing: '0.04em' }}>
                    DEMO PRINCIPAL:
                  </div>
                  <div style={{
                    padding: '8px 12px', borderRadius: '8px',
                    background: 'rgba(5, 150, 105, 0.15)', border: '1px solid rgba(5, 150, 105, 0.4)',
                    color: '#a7f3d0', fontSize: '0.76rem', fontWeight: 600,
                  }}>
                    👩💼 Dr. Evelyn Reed — Complete School Schedule
                  </div>
                </div>
              )}

              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              }}>
                <span style={{
                  fontSize: '0.82rem', fontWeight: 700,
                  color: isHovered ? card.accentColor : '#64748b',
                  transition: 'color 0.2s ease',
                }}>
                  {isSelected ? 'Entering...' : 'Enter Portal'}
                </span>
                <div style={{
                  width: '32px', height: '32px', borderRadius: '50%',
                  background: isHovered ? card.gradient : 'rgba(255,255,255,0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.25s ease',
                  transform: isHovered ? 'translateX(4px)' : 'none',
                }}>
                  <ArrowRight size={16} color="white" />
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Demo badge */}
      <div style={{
        marginTop: '48px', position: 'relative', zIndex: 1,
        background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.25)',
        borderRadius: '10px', padding: '12px 20px',
        display: 'flex', alignItems: 'center', gap: '8px',
        color: '#fbbf24', fontSize: '0.8rem', fontWeight: 600,
      }}>
        <Sparkles size={14} />
        <span>DEMO MODE — Click any card for instant access. No password required.</span>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.05); opacity: 0.7; }
        }
      `}</style>
    </div>
  );
};
