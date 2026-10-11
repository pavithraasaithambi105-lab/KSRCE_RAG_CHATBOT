import { Pressable, StyleSheet, Text, View } from 'react-native';

import { COLORS } from '@/constants/theme';

type Props = {
  title: string;
  color?: string;
  onMinimize?: () => void;
};

export default function ChatHeader({ title, color = COLORS.primary, onMinimize }: Props) {
  return (
    <View style={[styles.header, { backgroundColor: color }]}>
      <Text style={styles.title}>{title}</Text>
      {onMinimize && (
        <Pressable onPress={onMinimize} hitSlop={12} accessibilityLabel="Minimize chat">
          <View style={styles.minimize} />
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  title: { color: '#fff', fontSize: 18, fontWeight: '600' },
  minimize: { width: 18, height: 3, borderRadius: 2, backgroundColor: '#fff' },
});
