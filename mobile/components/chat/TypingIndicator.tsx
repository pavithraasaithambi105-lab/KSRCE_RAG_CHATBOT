import { useEffect, useRef } from 'react';
import { Animated, Platform, StyleSheet, Text, View } from 'react-native';

import { COLORS } from '@/constants/theme';
import Avatar from './Avatar';
import { ChatTheme, DEFAULT_THEME } from './types';

export default function TypingIndicator({ theme = DEFAULT_THEME }: { theme?: ChatTheme }) {
  const dot1 = useRef(new Animated.Value(0.3)).current;
  const dot2 = useRef(new Animated.Value(0.3)).current;
  const dot3 = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const animations = [dot1, dot2, dot3].map((dot, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(i * 150),
          Animated.timing(dot, { toValue: 1, duration: 300, useNativeDriver: Platform.OS !== 'web' }),
          Animated.timing(dot, { toValue: 0.3, duration: 300, useNativeDriver: Platform.OS !== 'web' }),
          Animated.delay((2 - i) * 150),
        ]),
      ),
    );
    animations.forEach((a) => a.start());
    return () => animations.forEach((a) => a.stop());
  }, [dot1, dot2, dot3]);

  return (
    <View style={styles.container}>
      <View style={styles.nameRow}>
        <Avatar role="bot" theme={theme} />
        <Text style={styles.name}>{theme.botName}</Text>
      </View>
      <View style={styles.bubble}>
        {[dot1, dot2, dot3].map((dot, i) => (
          <Animated.View key={i} style={[styles.dot, { opacity: dot }]} />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignSelf: 'flex-start', marginBottom: 14 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  name: { fontSize: 14, color: COLORS.muted },
  bubble: {
    flexDirection: 'row',
    gap: 5,
    backgroundColor: COLORS.botBubble,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: COLORS.muted },
});
