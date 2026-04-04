import React from 'react';
import { View, Text, StyleSheet, ScrollView, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import AnimatedButton from '../components/AnimatedButton';
import GradientHeader from '../components/GradientHeader';

export default function ProfileScreen({ navigation, route }) {
  const username = route.params?.username || 'Farmer';
  const userId = route.params?.userId || '';
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }).start();
  }, [fadeAnim]);

  const logout = () => {
    navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
  };

  return (
    <LinearGradient colors={['#0F172A', '#1E293B']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <GradientHeader subtitle="Your farming profile" />
        <Animated.View style={{ opacity: fadeAnim, alignItems: 'center' }}>
          <View style={styles.avatarContainer}>
            <LinearGradient colors={['#10B981', '#3B82F6']} style={styles.avatar}>
              <Ionicons name="person" size={60} color="#fff" />
            </LinearGradient>
          </View>

          <Text style={styles.username}>{username}</Text>
          {userId ? <Text style={styles.userId}>ID: {userId}</Text> : null}

          <View style={styles.infoCard}>
            <View style={styles.infoRow}>
              <MaterialCommunityIcons name="email-outline" size={22} color="#10B981" />
              <Text style={styles.infoLabel}>Email</Text>
              <Text style={styles.infoValue}>{username}</Text>
            </View>
            <View style={styles.divider} />
            <View style={styles.infoRow}>
              <MaterialCommunityIcons name="shield-check" size={22} color="#3B82F6" />
              <Text style={styles.infoLabel}>Status</Text>
              <Text style={[styles.infoValue, { color: '#10B981' }]}>Active</Text>
            </View>
            <View style={styles.divider} />
            <View style={styles.infoRow}>
              <MaterialCommunityIcons name="sprout" size={22} color="#F59E0B" />
              <Text style={styles.infoLabel}>Plan</Text>
              <Text style={styles.infoValue}>Smart Farmer</Text>
            </View>
          </View>

          <View style={styles.buttonContainer}>
            <AnimatedButton
              title="Logout"
              onPress={logout}
              colors={['#EF4444', '#DC2626']}
            />
          </View>
        </Animated.View>
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 60,
  },
  avatarContainer: {
    marginBottom: 16,
  },
  avatar: {
    width: 110,
    height: 110,
    borderRadius: 55,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 12,
    elevation: 10,
  },
  username: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '800',
    marginBottom: 4,
  },
  userId: {
    color: '#94A3B8',
    fontSize: 14,
    marginBottom: 24,
  },
  infoCard: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 20,
    padding: 20,
    width: '100%',
    marginBottom: 24,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  infoLabel: {
    color: '#94A3B8',
    fontSize: 15,
    marginLeft: 12,
    flex: 1,
  },
  infoValue: {
    color: '#E2E8F0',
    fontSize: 15,
    fontWeight: '600',
    flexShrink: 1,
    textAlign: 'right',
  },
  divider: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.08)',
  },
  buttonContainer: {
    width: '100%',
  },
});
