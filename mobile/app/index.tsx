import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { COLORS } from '@/constants/theme';

type Role = 'Student' | 'Staff';

const ROLES: Role[] = ['Student', 'Staff'];

export default function HomeScreen() {
  const [name, setName] = useState('');
  const [role, setRole] = useState<Role>('Student');
  const canEnter = name.trim().length > 0;

  const enterChat = () => {
    if (!canEnter) return;
    router.push({ pathname: '/chat', params: { name: name.trim(), role } });
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.content}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.iconCircle}>
          <MaterialCommunityIcons name="robot-outline" size={48} color="#fff" />
        </View>
        <Text style={styles.title}>Virtual Assistant</Text>
        <Text style={styles.subtitle}>Ask doubts, revise topics and get help anytime. Tell me who you are to get started.</Text>

        <View style={styles.form}>
          <Text style={styles.label}>I am a</Text>
          <View style={styles.roleRow}>
            {ROLES.map((r) => {
              const selected = r === role;
              return (
                <Pressable
                  key={r}
                  onPress={() => setRole(r)}
                  style={[styles.roleButton, selected && styles.roleButtonSelected]}
                >
                  <MaterialCommunityIcons
                    name={r === 'Student' ? 'school-outline' : 'briefcase-outline'}
                    size={18}
                    color={selected ? '#fff' : COLORS.primary}
                  />
                  <Text style={[styles.roleText, selected && styles.roleTextSelected]}>{r}</Text>
                </Pressable>
              );
            })}
          </View>

          <Text style={styles.label}>Your name</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder={role === 'Student' ? 'e.g. Priya' : 'e.g. Dr. Kumar'}
            placeholderTextColor={COLORS.placeholder}
            autoCapitalize="words"
            returnKeyType="go"
            onSubmitEditing={enterChat}
          />

          <Pressable
            style={[styles.button, !canEnter && styles.buttonDisabled]}
            onPress={enterChat}
            disabled={!canEnter}
          >
            <Text style={styles.buttonText}>Enter chat</Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  iconCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.text, marginTop: 20 },
  subtitle: { fontSize: 15, color: COLORS.muted, textAlign: 'center', marginTop: 8, lineHeight: 22 },
  form: { alignSelf: 'stretch', maxWidth: 400, width: '100%', marginTop: 32, alignItems: 'stretch' },
  label: { fontSize: 14, fontWeight: '600', color: COLORS.text, marginBottom: 8 },
  roleRow: { flexDirection: 'row', gap: 12, marginBottom: 20 },
  roleButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    borderRadius: 10,
    paddingVertical: 11,
  },
  roleButtonSelected: { backgroundColor: COLORS.primary },
  roleText: { fontSize: 15, fontWeight: '600', color: COLORS.primary },
  roleTextSelected: { color: '#fff' },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: COLORS.text,
  },
  button: {
    marginTop: 24,
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  buttonDisabled: { backgroundColor: '#A5B4FC' },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
