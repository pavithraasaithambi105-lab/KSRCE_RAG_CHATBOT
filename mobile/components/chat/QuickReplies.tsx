import { Pressable, StyleSheet, Text, View } from 'react-native';

import { COLORS } from '@/constants/theme';
import { QuickReplyOption } from './types';

type Props = {
  options: QuickReplyOption[];
  onSelect: (label: string) => void;
  accent?: string;
  disabled?: boolean;
};

export default function QuickReplies({ options, onSelect, accent = COLORS.primary, disabled }: Props) {
  return (
    <View style={styles.row}>
      {options.map((option) => {
        const color = option.variant === 'danger' ? COLORS.danger : accent;
        return (
          <Pressable
            key={option.label}
            onPress={() => onSelect(option.label)}
            disabled={disabled}
            style={({ pressed }) => [
              styles.button,
              { borderColor: color },
              pressed && { backgroundColor: `${color}14` },
              disabled && styles.disabled,
            ]}
          >
            <Text style={[styles.label, { color }]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 10 },
  button: {
    minWidth: 66,
    borderWidth: 1.5,
    borderRadius: 6,
    paddingHorizontal: 18,
    paddingVertical: 7,
    alignItems: 'center',
  },
  label: { fontSize: 14, fontWeight: '500' },
  disabled: { opacity: 0.5 },
});
