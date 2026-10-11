import { MaterialCommunityIcons } from '@expo/vector-icons';
import { StyleSheet, View } from 'react-native';

import { COLORS } from '@/constants/theme';
import { ChatTheme, DEFAULT_THEME } from './types';

type Props = {
  role: 'user' | 'bot';
  theme?: ChatTheme;
};

export default function Avatar({ role, theme = DEFAULT_THEME }: Props) {
  const isBot = role === 'bot';
  return (
    <View style={[styles.avatar, { backgroundColor: isBot ? theme.accent : COLORS.userAvatar }]}>
      <MaterialCommunityIcons name={isBot ? theme.botIcon : 'account-outline'} size={17} color="#fff" />
    </View>
  );
}

const styles = StyleSheet.create({
  avatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
