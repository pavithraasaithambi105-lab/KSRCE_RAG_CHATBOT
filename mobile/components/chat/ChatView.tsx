import { useRef } from 'react';
import { FlatList, KeyboardAvoidingView, Platform, StyleSheet } from 'react-native';

import { COLORS } from '@/constants/theme';
import ChatInput from './ChatInput';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import { ChatMessage, ChatTheme } from './types';

type Props = {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => void;
  theme: ChatTheme;
  userName: string;
  onAttach?: () => void;
  /** Optional extra content under a message bubble (e.g. a student card). */
  renderExtra?: (message: ChatMessage) => React.ReactNode;
};

/** Message list + typing indicator + input bar, shared by every chatbot tab. */
export default function ChatView({ messages, loading, onSend, theme, userName, onAttach, renderExtra }: Props) {
  const listRef = useRef<FlatList<ChatMessage>>(null);
  const lastMessageId = messages[messages.length - 1]?.id;

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
        renderItem={({ item }) => (
          <MessageBubble
            message={item}
            userName={userName}
            theme={theme}
            onQuickReply={onSend}
            showQuickReplies={item.id === lastMessageId && !loading}
          >
            {renderExtra?.(item)}
          </MessageBubble>
        )}
        ListFooterComponent={loading ? <TypingIndicator theme={theme} /> : null}
      />
      <ChatInput
        onSend={onSend}
        onAttach={onAttach}
        disabled={loading}
        placeholder={theme.placeholder}
        accent={theme.accent}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: 16 },
});
