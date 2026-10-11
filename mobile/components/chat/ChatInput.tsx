import { Feather } from '@expo/vector-icons';
import { useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { COLORS } from '@/constants/theme';

type Props = {
  onSend: (text: string) => void;
  onAttach?: () => void;
  disabled?: boolean;
  placeholder?: string;
  accent?: string;
};

export default function ChatInput({
  onSend,
  onAttach,
  disabled,
  placeholder = 'Type a message',
  accent = COLORS.primary,
}: Props) {
  const [text, setText] = useState('');
  const canSend = text.trim().length > 0 && !disabled;

  const handleSend = () => {
    if (!canSend) return;
    onSend(text.trim());
    setText('');
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        value={text}
        onChangeText={setText}
        placeholder={placeholder}
        placeholderTextColor={COLORS.placeholder}
        onSubmitEditing={handleSend}
        returnKeyType="send"
      />
      {onAttach && (
        <Pressable onPress={onAttach} hitSlop={8} style={styles.iconButton} accessibilityLabel="Attach file">
          <Feather name="paperclip" size={20} color={COLORS.placeholder} />
        </Pressable>
      )}
      <Pressable
        onPress={handleSend}
        disabled={!canSend}
        hitSlop={8}
        style={styles.iconButton}
        accessibilityLabel="Send message"
      >
        <Feather name="send" size={21} color={canSend ? accent : COLORS.placeholder} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: COLORS.background,
  },
  input: { flex: 1, fontSize: 15, color: COLORS.text, paddingVertical: 8 },
  iconButton: { marginLeft: 14 },
});
