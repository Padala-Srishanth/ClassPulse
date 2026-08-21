import React from 'react';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ currentPage, onNavigate, children }) => {
  return (
    <div className="app-container">
      <Sidebar currentPage={currentPage} onNavigate={onNavigate} />
      <div className="main-content">
        <Navbar />
        <main className="page-body">{children}</main>
      </div>
    </div>
  );
};
