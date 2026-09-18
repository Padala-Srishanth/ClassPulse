import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { chatbotApi, ChatContext } from '../../api/chatbot';
import { ChatbotFloatingButton } from './ChatbotFloatingButton';
import { ChatbotPanel } from './ChatbotPanel';
import { ChatMessageData } from './ChatMessage';

type PanelState = 'closed' | 'open' | 'minimized';

let messageCounter = 0;
const nextId = () => `msg-${Date.now()}-${messageCounter++}`;

const DEFAULT_SUGGESTIONS_PRINCIPAL = [
  'Show all high-risk students.',
  'Which class has the lowest attendance?',
  'Show students with attendance below 75% and declining test scores.',
];
const DEFAULT_SUGGESTIONS_TEACHER = [
  'Who has attendance below 75%?',
  'Who has not completed homework?',
  'Which students in my class are currently high risk?',
];

/**
 * ClassPulse AI Assistant — floating widget.
 *
 * Deliberately mounted as a sibling of the existing Teacher/Principal
 * layouts (see App.tsx) rather than inside them, and uses `position: fixed`
 * throughout, so it never touches existing page structure, navigation, or
 * layout. It renders nothing at all for STUDENT (and any other) role — but
 * that's a UX convenience, not the security boundary: every request is
 * re-authorized server-side by app/api/v1/chatbot.py regardless of what the
 * frontend renders.
 */
export const ChatbotWidget: React.FC = () => {
  const { currentUser } = useAuth();
  const [panelState, setPanelState] = useState<PanelState>('closed');
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [context, setContext] = useState<ChatContext | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' ? window.innerWidth < 640 : false);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 640);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isPrincipal = currentUser?.role === 'SCHOOL_ADMIN' || currentUser?.role === 'ADMIN';
  const isEligible = isPrincipal || currentUser?.role === 'TEACHER';

  const send = useCallback(
    async (text: string) => {
      const userMsg: ChatMessageData = { id: nextId(), role: 'user', text };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      try {
        const result = await chatbotApi.sendMessage(text, context);
        setContext(result.context || null);
        setMessages((prev) => [...prev, { id: nextId(), role: 'assistant', text: result.reply }]);
      } catch (err: any) {
        setMessages((prev) => [
          ...prev,
          {
            id: nextId(),
            role: 'assistant',
            text: err?.message || "Sorry, I couldn't reach the assistant right now. Please try again.",
            isError: true,
          },
        ]);
      } finally {
        setIsLoading(false);
        if (panelState !== 'open') setHasUnread(true);
      }
    },
    [context, panelState]
  );

  if (!isEligible) return null;

  const suggestions = isPrincipal ? DEFAULT_SUGGESTIONS_PRINCIPAL : DEFAULT_SUGGESTIONS_TEACHER;

  return (
    <>
      {panelState === 'open' && (
        <ChatbotPanel
          isPrincipal={!!isPrincipal}
          messages={messages}
          suggestions={messages.length === 0 ? suggestions : []}
          isLoading={isLoading}
          onSend={send}
          onMinimize={() => setPanelState('minimized')}
          onClose={() => setPanelState('closed')}
          isMobile={isMobile}
        />
      )}
      <ChatbotFloatingButton
        isOpen={panelState === 'open'}
        hasUnread={hasUnread && panelState !== 'open'}
        onClick={() => {
          setHasUnread(false);
          setPanelState((prev) => (prev === 'open' ? 'closed' : 'open'));
        }}
      />
    </>
  );
};
