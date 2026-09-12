import React from 'react';
import { Bot, User as UserIcon } from 'lucide-react';

export interface ChatMessageData {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  isError?: boolean;
}

export const ChatMessage: React.FC<{ message: ChatMessageData }> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        gap: '8px',
        alignItems: 'flex-start',
        flexDirection: isUser ? 'row-reverse' : 'row',
      }}
    >
      <div
        style={{
          width: '26px',
          height: '26px',
          borderRadius: '50%',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: isUser ? '#e0e7ff' : 'linear-gradient(135deg, #6366f1, #a855f7)',
          color: isUser ? '#4338ca' : 'white',
        }}
      >
        {isUser ? <UserIcon size={14} /> : <Bot size={14} />}
      </div>
      <div
        style={{
          maxWidth: '78%',
          padding: '9px 13px',
          borderRadius: isUser ? '14px 14px 3px 14px' : '14px 14px 14px 3px',
          background: message.isError ? '#fef2f2' : isUser ? '#6366f1' : '#f1f5f9',
          color: message.isError ? '#b91c1c' : isUser ? 'white' : '#1e293b',
          fontSize: '0.85rem',
          lineHeight: 1.45,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          border: message.isError ? '1px solid #fecaca' : 'none',
        }}
      >
        {message.text}
      </div>
    </div>
  );
};
