import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { COLORS } from '@/constants/theme';
import { IconName } from './types';

export type Tab<K extends string> = {
  key: K;
  label: string;
  icon: IconName;
  accent: string;
};

type Props<K extends string> = {
  tabs: Tab<K>[];
  active: K;
  onChange: (key: K) => void;
};

export default function ChatTabs<K extends string>({ tabs, active, onChange }: Props<K>) {
  return (
    <View style={styles.container}>
      {tabs.map((tab) => {
        const selected = tab.key === active;
        return (
          <Pressable
            key={tab.key}
            onPress={() => onChange(tab.key)}
            style={[styles.tab, selected && { backgroundColor: tab.accent }]}
            accessibilityRole="tab"
            accessibilityState={{ selected }}
          >
            <MaterialCommunityIcons name={tab.icon} size={17} color={selected ? '#fff' : COLORS.muted} />
            <Text style={[styles.label, selected && styles.labelSelected]}>{tab.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    gap: 6,
    margin: 12,
    padding: 4,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 9,
    borderRadius: 9,
  },
  label: { fontSize: 14, fontWeight: '600', color: COLORS.muted },
  labelSelected: { color: '#fff' },
});
