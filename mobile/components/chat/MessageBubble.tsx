import { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { COLORS } from '@/constants/theme';
import Avatar from './Avatar';
import QuickReplies from './QuickReplies';
import { ChatMessage, ChatTheme, DEFAULT_THEME } from './types';

type Props = {
  message: ChatMessage;
  userName?: string;
  theme?: ChatTheme;
  onQuickReply?: (label: string) => void;
  showQuickReplies?: boolean;
  /** Extra content shown under the bubble, e.g. a student card. */
  children?: ReactNode;
};

export default function MessageBubble({
  message,
  userName = 'You',
  theme = DEFAULT_THEME,
  onQuickReply,
  showQuickReplies,
  children,
}: Props) {
  const isUser = message.role === 'user';

  return (
    <View style={[styles.container, isUser ? styles.alignRight : styles.alignLeft]}>
      {/* Avatar + name */}
      <View style={[styles.nameRow, isUser && styles.nameRowUser]}>
        <Avatar role={message.role} theme={theme} />
        <Text style={styles.name}>{isUser ? userName : theme.botName}</Text>
      </View>

      {/* Bubble */}
      <View style={[styles.bubble, isUser ? { backgroundColor: theme.accent } : styles.botBubble]}>
        <Text style={[styles.text, isUser && styles.userText]}>{message.text}</Text>
      </View>

      {children}

      {!isUser && showQuickReplies && message.options && onQuickReply && (
        <QuickReplies options={message.options} onSelect={onQuickReply} accent={theme.accent} />
      )}

      <Text style={styles.time}>{message.time}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginBottom: 14, maxWidth: '85%' },
  alignLeft: { alignSelf: 'flex-start', alignItems: 'flex-start' },
  alignRight: { alignSelf: 'flex-end', alignItems: 'flex-end' },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  nameRowUser: { flexDirection: 'row-reverse' },
  name: { fontSize: 14, color: COLORS.muted },
  bubble: { paddingHorizontal: 14, paddingVertical: 11, borderRadius: 12 },
  botBubble: { backgroundColor: COLORS.botBubble },
  text: { fontSize: 14, lineHeight: 21, color: COLORS.text },
  userText: { color: '#fff' },
  time: { fontSize: 11, color: COLORS.muted, marginTop: 6 },
});
