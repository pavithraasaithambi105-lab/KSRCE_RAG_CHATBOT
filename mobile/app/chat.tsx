import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import AssistantChat from '@/components/chat/AssistantChat';
import ChatHeader from '@/components/chat/ChatHeader';
import ChatTabs, { Tab } from '@/components/chat/ChatTabs';
import StudentInfoChat from '@/components/student/StudentInfoChat';
import { COLORS } from '@/constants/theme';

type TabKey = 'assistant' | 'student';

const TABS: (Tab<TabKey> & { title: string })[] = [
  { key: 'assistant', label: 'Assistant', icon: 'robot-outline', accent: COLORS.primary, title: 'Virtual assistant' },
  { key: 'student', label: 'Student Info', icon: 'account-search-outline', accent: COLORS.studentAccent, title: 'Student info' },
];

export default function ChatScreen() {
  const params = useLocalSearchParams<{ name?: string }>();
  const userName = params.name || 'You';

  const [activeTab, setActiveTab] = useState<TabKey>('assistant');
  const current = TABS.find((t) => t.key === activeTab)!;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: current.accent }]} edges={['top', 'bottom']}>
      <ChatHeader title={current.title} color={current.accent} onMinimize={() => router.back()} />

      <View style={styles.body}>
        <ChatTabs tabs={TABS} active={activeTab} onChange={setActiveTab} />

        {/* Both chats stay mounted so each keeps its conversation when switching tabs. */}
        <View style={[styles.flex, activeTab !== 'assistant' && styles.hidden]}>
          <AssistantChat userName={userName} />
        </View>
        <View style={[styles.flex, activeTab !== 'student' && styles.hidden]}>
          <StudentInfoChat userName={userName} />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  body: { flex: 1, backgroundColor: COLORS.background },
  flex: { flex: 1 },
  hidden: { display: 'none' },
});
