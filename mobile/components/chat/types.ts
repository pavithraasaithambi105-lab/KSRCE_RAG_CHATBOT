import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ComponentProps } from 'react';

import { COLORS } from '@/constants/theme';
import { BOT_NAME } from '@/constants/config';

export type IconName = ComponentProps<typeof MaterialCommunityIcons>['name'];

export type QuickReplyOption = {
  label: string;
  variant?: 'primary' | 'danger';
};

export type Student = {
  name: string;
  rollNo: string;
  department: string;
  year: string;
  attendance: number | null;
  cgpa: number | null; // null for first-years (no results yet)
  arrears: number;
  email: string;
};

export type ChatMessage = {
  id: string;
  role: 'user' | 'bot';
  text: string;
  time: string;
  options?: QuickReplyOption[];
  students?: Student[];
};

/** Visual identity of a chatbot, so each tab can look different. */
export type ChatTheme = {
  accent: string;
  botName: string;
  botIcon: IconName;
  placeholder: string;
};

export const DEFAULT_THEME: ChatTheme = {
  accent: COLORS.primary,
  botName: BOT_NAME,
  botIcon: 'robot-outline',
  placeholder: 'Type a message',
};
