import { apiClient } from './client';

/**
 * ChatContext is opaque, backend-owned state. The frontend's only job is to
 * hold on to whatever the last response returned and send it back unchanged
 * on the next turn — this is what gives the assistant multi-turn memory
 * ("Only Grade 10." / "Which of those...?") without a server-side session.
 * The backend re-derives authorization from the caller's token on every
 * single request, so this object can never be used to widen access.
 */
export type ChatContext = Record<string, unknown>;

export interface ChatMessageResponsePayload {
  reply: string;
  data: unknown;
  context: ChatContext;
  suggestions: string[];
}

export interface ChatCapabilities {
  role: string;
  is_principal: boolean;
  school_id: string | null;
  authorized_class_count: number;
  example_questions: string[];
}

export const chatbotApi = {
  sendMessage: (message: string, context?: ChatContext | null) =>
    apiClient<ChatMessageResponsePayload>('/api/v1/chatbot/message', {
      method: 'POST',
      body: JSON.stringify({ message, context: context || null }),
    }),

  getCapabilities: () => apiClient<ChatCapabilities>('/api/v1/chatbot/capabilities'),
};
