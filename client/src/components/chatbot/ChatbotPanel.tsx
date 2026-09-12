import React, { useEffect, useRef } from 'react';
import { Minus, Sparkles, X } from 'lucide-react';
import { ChatMessage, ChatMessageData } from './ChatMessage';
import { ChatInput } from './ChatInput';

interface ChatbotPanelProps {
  isPrincipal: boolean;
  messages: ChatMessageData[];
  suggestions: string[];
  isLoading: boolean;
  onSend: (text: string) => void;
  onMinimize: () => void;
  onClose: () => void;
  isMobile: boolean;
}

export const ChatbotPanel: React.FC<ChatbotPanelProps> = ({
  isPrincipal,
  messages,
  suggestions,
  isLoading,
  onSend,
  onMinimize,
  onClose,
  isMobile,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div
      role="dialog"
      aria-label="ClassPulse Assistant"
      style={{
        position: 'fixed',
        bottom: isMobile ? 0 : '96px',
        right: isMobile ? 0 : '24px',
        left: isMobile ? 0 : 'auto',
        width: isMobile ? '100%' : '368px',
        height: isMobile ? '100%' : 'min(560px, calc(100vh - 140px))',
        background: 'white',
        borderRadius: isMobile ? 0 : '16px',
        boxShadow: '0 20px 50px rgba(15, 23, 42, 0.25)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        zIndex: 9999,
        border: '1px solid #e2e8f0',
        fontFamily: "'Inter', sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
          color: 'white',
          padding: '14px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
          <div
            style={{
              width: '30px', height: '30px', borderRadius: '9px', flexShrink: 0,
              background: 'rgba(255,255,255,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <Sparkles size={16} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              ClassPulse Assistant
            </div>
            <div style={{ fontSize: '0.68rem', opacity: 0.85 }}>
              {isPrincipal ? 'School-wide analytics' : 'Your classes'}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '4px', flexShrink: 0 }}>
          <button
            onClick={onMinimize}
            aria-label="Minimize chat"
            style={{ background: 'rgba(255,255,255,0.12)', border: 'none', color: 'white', width: '26px', height: '26px', borderRadius: '7px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            <Minus size={14} />
          </button>
          <button
            onClick={onClose}
            aria-label="Close chat"
            style={{ background: 'rgba(255,255,255,0.12)', border: 'none', color: 'white', width: '26px', height: '26px', borderRadius: '7px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '12px', background: '#fafbfc' }}>
        {messages.length === 0 && (
          <div style={{ color: '#64748b', fontSize: '0.82rem', textAlign: 'center', marginTop: '24px', padding: '0 12px' }}>
            Ask me about attendance, homework, test scores, risk, or interventions
            {isPrincipal ? ' across the school' : ' for your classes'}.
          </div>
        )}
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}
        {isLoading && (
          <div style={{ display: 'flex', gap: '4px', padding: '4px 0 4px 34px' }}>
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                style={{
                  width: '6px', height: '6px', borderRadius: '50%', background: '#a5b4fc',
                  animation: `classpulse-chat-bounce 1.2s ${i * 0.15}s infinite ease-in-out`,
                }}
              />
            ))}
            <style>{`@keyframes classpulse-chat-bounce { 0%, 80%, 100% { opacity: 0.3; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-3px); } }`}</style>
          </div>
        )}
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && !isLoading && (
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', padding: '10px 12px 0', flexShrink: 0 }}>
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => onSend(s)}
              style={{
                whiteSpace: 'nowrap', fontSize: '0.72rem', padding: '6px 10px', borderRadius: '999px',
                border: '1px solid #e0e7ff', background: '#eef2ff', color: '#4338ca', cursor: 'pointer', flexShrink: 0,
              }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <ChatInput onSend={onSend} disabled={isLoading} />
    </div>
  );
};
