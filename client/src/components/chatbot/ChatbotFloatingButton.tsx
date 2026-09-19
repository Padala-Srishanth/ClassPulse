import React, { useState } from 'react';
import { MessageCircle, X } from 'lucide-react';

interface ChatbotFloatingButtonProps {
  isOpen: boolean;
  hasUnread: boolean;
  onClick: () => void;
}

export const ChatbotFloatingButton: React.FC<ChatbotFloatingButtonProps> = ({ isOpen, hasUnread, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isPressed, setIsPressed] = useState(false);

  // Dynamic glowing aura and icon drop-shadow
  let currentBoxShadow = '0 8px 24px rgba(79, 70, 229, 0.45)';
  let currentBorder = '2px solid rgba(255, 255, 255, 0.15)';
  let iconFilter = 'none';

  if (isPressed) {
    // Clicked / Active: intense radiant pulse glow
    currentBoxShadow = '0 0 35px rgba(168, 85, 247, 0.95), 0 0 70px rgba(99, 102, 241, 0.85), inset 0 0 14px rgba(255, 255, 255, 0.4)';
    currentBorder = '2px solid rgba(255, 255, 255, 0.7)';
    iconFilter = 'drop-shadow(0 0 8px #ffffff) drop-shadow(0 0 16px #c084fc)';
  } else if (isHovered) {
    // Hovered: brilliant ambient halo glow
    currentBoxShadow = '0 0 24px rgba(99, 102, 241, 0.85), 0 0 48px rgba(168, 85, 247, 0.6), 0 8px 25px rgba(79, 70, 229, 0.5)';
    currentBorder = '2px solid rgba(255, 255, 255, 0.5)';
    iconFilter = 'drop-shadow(0 0 6px rgba(255, 255, 255, 0.9)) drop-shadow(0 0 12px rgba(165, 180, 252, 0.8))';
  } else if (isOpen) {
    // Open state: steady elegant accent glow
    currentBoxShadow = '0 0 20px rgba(124, 58, 237, 0.65), 0 0 35px rgba(99, 102, 241, 0.4), 0 8px 24px rgba(79, 70, 229, 0.4)';
    currentBorder = '2px solid rgba(255, 255, 255, 0.35)';
    iconFilter = 'drop-shadow(0 0 5px rgba(255, 255, 255, 0.8))';
  }

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        setIsPressed(false);
      }}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      aria-label={isOpen ? 'Close ClassPulse Assistant' : 'Open ClassPulse Assistant'}
      title="ClassPulse Assistant"
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        border: currentBorder,
        cursor: 'pointer',
        background: isPressed
          ? 'linear-gradient(135deg, #4338ca, #9333ea)'
          : isHovered
            ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
            : 'linear-gradient(135deg, #4f46e5, #7c3aed)',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: currentBoxShadow,
        zIndex: 9998,
        transition: 'box-shadow 0.25s ease, border 0.25s ease, background 0.25s ease',
        outline: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          filter: iconFilter,
          transition: 'filter 0.25s ease',
        }}
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </div>
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
            boxShadow: '0 0 8px rgba(34, 197, 94, 0.8)',
          }}
        />
      )}
    </button>
  );
};
