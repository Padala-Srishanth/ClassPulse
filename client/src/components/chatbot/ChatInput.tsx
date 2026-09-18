import React, { useState } from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled }) => {
  const [value, setValue] = useState('');

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: '8px',
        padding: '10px',
        borderTop: '1px solid #e2e8f0',
        background: 'white',
      }}
    >
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder="Ask something…"
        rows={1}
        disabled={disabled}
        style={{
          flex: 1,
          resize: 'none',
          border: '1px solid #e2e8f0',
          borderRadius: '10px',
          padding: '9px 12px',
          fontSize: '0.85rem',
          fontFamily: 'inherit',
          outline: 'none',
          maxHeight: '90px',
          background: disabled ? '#f8fafc' : 'white',
        }}
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
        style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          border: 'none',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: disabled || !value.trim() ? 'not-allowed' : 'pointer',
          background: disabled || !value.trim() ? '#e2e8f0' : 'linear-gradient(135deg, #6366f1, #a855f7)',
          color: 'white',
        }}
      >
        <Send size={16} />
      </button>
    </div>
  );
};
