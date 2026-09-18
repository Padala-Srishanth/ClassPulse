import React from 'react';
import { MessageCircle, X } from 'lucide-react';

interface ChatbotFloatingButtonProps {
  isOpen: boolean;
  hasUnread: boolean;
  onClick: () => void;
}

export const ChatbotFloatingButton: React.FC<ChatbotFloatingButtonProps> = ({ isOpen, hasUnread, onClick }) => {
  return (
    <button
      onClick={onClick}
      aria-label={isOpen ? 'Close ClassPulse Assistant' : 'Open ClassPulse Assistant'}
      title="ClassPulse Assistant"
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        border: 'none',
        cursor: 'pointer',
        background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 8px 24px rgba(79, 70, 229, 0.45)',
        zIndex: 9998,
        transition: 'transform 0.15s ease, box-shadow 0.15s ease',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.transform = 'scale(1.06)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.transform = 'scale(1)';
      }}
    >
      {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      {!isOpen && hasUnread && (
        <span
          style={{
            position: 'absolute',
            top: '2px',
            right: '2px',
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            background: '#22c55e',
            border: '2px solid white',
          }}
        />
      )}
    </button>
  );
};
