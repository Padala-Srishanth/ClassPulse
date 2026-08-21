import React, { createContext, useContext, useEffect, useState } from 'react';
import { User as FirebaseUser, signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { auth } from '../firebase/config';
import { User, UserRole } from '../types';

interface AuthContextType {
  firebaseUser: FirebaseUser | null;
  currentUser: User | null;
  token: string | null;
  role: UserRole | null;
  schoolId: string | null;
  loading: boolean;
  loginWithEmail: (email: string, pass: string) => Promise<void>;
  loginAsDemo: (role: UserRole, schoolId?: string) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize demo state by default for instant developer usability
  useEffect(() => {
    const savedDemo = localStorage.getItem('classpulse_demo_user');
    if (savedDemo) {
      try {
        const parsed = JSON.parse(savedDemo);
        setCurrentUser(parsed.user);
        setToken(parsed.token);
        setLoading(false);
        return;
      } catch (e) {
        localStorage.removeItem('classpulse_demo_user');
      }
    }

    // Default to Teacher mode for seamless onboarding
    const defaultTeacher: User = {
      id: 'teacher-uid-001',
      firebase_uid: 'teacher-uid-001',
      email: 'teacher@school-001.example.com',
      name: 'Sarah Jenkins',
      role: 'TEACHER',
      school_id: 'school-001',
      status: 'ACTIVE',
    };
    setCurrentUser(defaultTeacher);
    setToken('mock-teacher-token');
    setLoading(false);
  }, []);

  const loginWithEmail = async (email: string, pass: string) => {
    setLoading(true);
    try {
      const cred = await signInWithEmailAndPassword(auth, email, pass);
      const idToken = await cred.user.getIdToken();
      setFirebaseUser(cred.user);
      setToken(idToken);
      
      // Fetch user profile from backend
      const res = await fetch('/api/v1/users/me', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      const data = await res.json();
      if (data.success) {
        setCurrentUser(data.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const loginAsDemo = (role: UserRole, schoolId: string = 'school-001') => {
    let demoUser: User;
    let mockToken = 'mock-token';

    if (role === 'ADMIN') {
      demoUser = {
        id: 'admin-uid-001',
        firebase_uid: 'admin-uid-001',
        email: 'admin@classpulse.example.com',
        name: 'Platform Administrator',
        role: 'ADMIN',
        school_id: null,
        status: 'ACTIVE',
      };
      mockToken = 'mock-admin-token';
    } else if (role === 'SCHOOL_ADMIN') {
      demoUser = {
        id: 'sadmin-uid-001',
        firebase_uid: 'sadmin-uid-001',
        email: 'principal@school-001.example.com',
        name: 'Dr. Evelyn Reed (Principal)',
        role: 'SCHOOL_ADMIN',
        school_id: schoolId,
        status: 'ACTIVE',
      };
      mockToken = 'mock-school-admin-token';
    } else {
      demoUser = {
        id: 'teacher-uid-001',
        firebase_uid: 'teacher-uid-001',
        email: 'teacher@school-001.example.com',
        name: 'Sarah Jenkins (Class 10 Lead)',
        role: 'TEACHER',
        school_id: schoolId,
        status: 'ACTIVE',
      };
      mockToken = 'mock-teacher-token';
    }

    setCurrentUser(demoUser);
    setToken(mockToken);
    localStorage.setItem(
      'classpulse_demo_user',
      JSON.stringify({ user: demoUser, token: mockToken })
    );
  };

  const logout = async () => {
    try {
      await signOut(auth);
    } catch (e) {
      // ignore
    }
    setFirebaseUser(null);
    setCurrentUser(null);
    setToken(null);
    localStorage.removeItem('classpulse_demo_user');
  };

  return (
    <AuthContext.Provider
      value={{
        firebaseUser,
        currentUser,
        token,
        role: currentUser?.role || null,
        schoolId: currentUser?.school_id || null,
        loading,
        loginWithEmail,
        loginAsDemo,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
