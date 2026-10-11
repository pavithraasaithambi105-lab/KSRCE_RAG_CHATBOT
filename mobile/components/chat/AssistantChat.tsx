import { useState } from 'react';

import { postJson } from '@/lib/api';
import { newId, now } from '@/lib/time';
import ChatView from './ChatView';
import { ChatMessage, DEFAULT_THEME } from './types';

const greeting = (name: string): ChatMessage => ({
  id: 'greeting',
  role: 'bot',
  text: `Hi ${name}! I'm your virtual assistant. How can I help you?`,
  time: now(),
});

export default function AssistantChat({ userName }: { userName: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => [greeting(userName)]);
  const [loading, setLoading] = useState(false);

  const addMessage = (message: Omit<ChatMessage, 'id' | 'time'>) => {
    setMessages((prev) => [...prev, { ...message, id: newId(), time: now() }]);
  };

  const sendMessage = async (question: string) => {
    if (loading) return;
    addMessage({ role: 'user', text: question });
    setLoading(true);

    try {
      const data = await postJson<{ answer: string; options?: ChatMessage['options'] }>('/chat', { question });
      addMessage({ role: 'bot', text: data.answer, options: data.options });
    } catch (error) {
      addMessage({
        role: 'bot',
        text: error instanceof Error ? error.message : 'The chat request failed. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ChatView
      messages={messages}
      loading={loading}
      onSend={sendMessage}
      theme={DEFAULT_THEME}
      userName={userName}
      onAttach={() => {}}
    />
  );
}
