import { MaterialCommunityIcons } from '@expo/vector-icons';
import { StyleSheet, Text, View } from 'react-native';

import { Student } from '@/components/chat/types';
import { COLORS } from '@/constants/theme';

const initials = (name: string) =>
  name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

type Props = {
  student: Student;
  accent?: string;
};

export default function StudentCard({ student, accent = COLORS.studentAccent }: Props) {
  const attendanceLow = student.attendance !== null && student.attendance < 75;

  return (
    <View style={styles.card}>
      {/* Top: avatar, name, roll number */}
      <View style={styles.top}>
        <View style={[styles.avatar, { backgroundColor: `${accent}1A` }]}>
          <Text style={[styles.avatarText, { color: accent }]}>{initials(student.name)}</Text>
        </View>
        <View style={styles.identity}>
          <Text style={styles.name}>{student.name}</Text>
          <Text style={styles.meta}>
            {student.rollNo} · {student.department} · {student.year}
          </Text>
        </View>
      </View>

      {/* Stats */}
      <View style={styles.stats}>
        <Stat
          label="Attendance"
          value={student.attendance === null ? '—' : `${student.attendance}%`}
          color={attendanceLow ? COLORS.danger : accent}
        />
        <View style={styles.divider} />
        <Stat label="CGPA" value={student.cgpa === null ? '—' : student.cgpa.toFixed(2)} color={COLORS.text} />
        <View style={styles.divider} />
        <Stat
          label="Arrears"
          value={String(student.arrears)}
          color={student.arrears > 0 ? COLORS.danger : COLORS.text}
        />
      </View>

      {/* Contact */}
      <View style={styles.contact}>
        <MaterialCommunityIcons name="email-outline" size={15} color={COLORS.muted} />
        <Text style={styles.contactText}>{student.email}</Text>
      </View>
    </View>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={styles.stat}>
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginTop: 10,
    width: 280,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 14,
    backgroundColor: COLORS.background,
  },
  top: { flexDirection: 'row', alignItems: 'center' },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontSize: 16, fontWeight: '700' },
  identity: { marginLeft: 12, flex: 1 },
  name: { fontSize: 16, fontWeight: '600', color: COLORS.text },
  meta: { fontSize: 12, color: COLORS.muted, marginTop: 2 },
  stats: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 14,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#F9FAFB',
  },
  stat: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 17, fontWeight: '700' },
  statLabel: { fontSize: 11, color: COLORS.muted, marginTop: 2 },
  divider: { width: 1, height: 28, backgroundColor: COLORS.border },
  contact: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 12 },
  contactText: { fontSize: 13, color: COLORS.muted },
});
