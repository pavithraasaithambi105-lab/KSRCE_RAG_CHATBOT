import { useState } from 'react';
import { View } from 'react-native';

import ChatView from '@/components/chat/ChatView';
import { ChatMessage, ChatTheme, Student } from '@/components/chat/types';
import { API_URL } from '@/constants/config';
import { postJson } from '@/lib/api';
import { COLORS } from '@/constants/theme';
import { newId, now } from '@/lib/time';
import StudentCard from './StudentCard';

export const STUDENT_THEME: ChatTheme = {
  accent: COLORS.studentAccent,
  botName: 'Student Info',
  botIcon: 'account-search-outline',
  placeholder: 'Search by name or roll number',
};

const GREETING: ChatMessage = {
  id: 'student-greeting',
  role: 'bot',
  text: 'Hi! I can look up student details like attendance, marks, arrears and contact info. Who are you looking for?',
  time: now(),
  options: [
    { label: 'Details of 24CS022' },
    { label: 'Attendance of 25EC047' },
    { label: 'Students with arrears in MECH final year' },
  ],
};

const HISTORY_TURNS = 10; // earlier messages sent along, so follow-ups like "and his marks?" work

/** Student card as returned by POST /students/assistant. */
type ApiStudent = {
  roll_number: string;
  name: string;
  department: string;
  year: number;
  cgpa: number | null;
  email: string;
  attendance_percentage: number | null;
  pending_arrears: number;
};

const ordinal = (n: number) => `${n}${['th', 'st', 'nd', 'rd'][n] ?? 'th'} Year`;

const toStudent = (s: ApiStudent): Student => ({
  name: s.name,
  rollNo: s.roll_number,
  department: s.department,
  year: ordinal(s.year),
  attendance: s.attendance_percentage,
  cgpa: s.cgpa,
  arrears: s.pending_arrears,
  email: s.email,
});

export default function StudentInfoChat({ userName }: { userName: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [loading, setLoading] = useState(false);

  const addMessage = (message: Omit<ChatMessage, 'id' | 'time'>) => {
    setMessages((prev) => [...prev, { ...message, id: newId(), time: now() }]);
  };

  const sendMessage = async (question: string) => {
    if (loading) return;
    const history = messages
      .filter((m) => m.id !== GREETING.id)
      .slice(-HISTORY_TURNS)
      .map((m) => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text }));
    addMessage({ role: 'user', text: question });
    setLoading(true);

    try {
      const data = await postJson<{ answer: string; students?: ApiStudent[] }>('/students/assistant', { question, history });
      addMessage({ role: 'bot', text: data.answer, students: (data.students ?? []).map(toStudent) });
    } catch (error) {
      addMessage({
        role: 'bot',
        text: error instanceof Error ? error.message : 'The request failed. Please try again.',
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
      theme={STUDENT_THEME}
      userName={userName}
      renderExtra={(message) =>
        message.students?.length ? (
          <View>
            {message.students.map((student) => (
              <StudentCard key={student.rollNo} student={student} accent={STUDENT_THEME.accent} />
            ))}
          </View>
        ) : null
      }
    />
  );
}
