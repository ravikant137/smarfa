import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Animated } from 'react-native';
import { LinearGradient } from 'react-native-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import AnimatedButton from '../components/AnimatedButton';
import axios from 'axios';

export default function HomeScreen({ navigation }) {
  const [stats, setStats] = useState({ cropHeight: 12.4, moisture: 52, temperature: 28, intrusionAlerts: 0 });
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 800, useNativeDriver: true }).start();
    // In a real app: fetch backend status / analytics.
    // axios.get('http://10.0.2.2:8000/summary').then(response => setStats(response.data)).catch(() => {});
  }, [fadeAnim]);

  return (
    <LinearGradient colors={['#0F172A', '#1E293B']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Animated.View style={[styles.header, { opacity: fadeAnim }]}>
          <Ionicons name="leaf" size={40} color="#10B981" />
          <Text style={styles.welcome}>Welcome, Farmer</Text>
          <Text style={styles.subtitle}>Your crops are under expert watch</Text>
        </Animated.View>

        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <MaterialCommunityIcons name="ruler" size={32} color="#3B82F6" />
            <Text style={styles.statValue}>{stats.cropHeight} cm</Text>
            <Text style={styles.statLabel}>Crop Height</Text>
          </View>
          <View style={styles.statCard}>
            <Ionicons name="water" size={32} color="#06B6D4" />
            <Text style={styles.statValue}>{stats.moisture}%</Text>
            <Text style={styles.statLabel}>Soil Moisture</Text>
          </View>
          <View style={styles.statCard}>
            <MaterialCommunityIcons name="thermometer" size={32} color="#EF4444" />
            <Text style={styles.statValue}>{stats.temperature}°C</Text>
            <Text style={styles.statLabel}>Temperature</Text>
          </View>
          <View style={styles.statCard}>
            <Ionicons name="warning" size={32} color="#F59E0B" />
            <Text style={styles.statValue}>{stats.intrusionAlerts}</Text>
            <Text style={styles.statLabel}>Alerts</Text>
          </View>
        </View>

        <AnimatedButton title="View Expert Alerts" onPress={() => navigation.navigate('Alerts')} colors={['#10B981', '#059669']} />
        <AnimatedButton title="Report Issue" onPress={() => alert('Contact support for immediate assistance')} colors={['#F59E0B', '#D97706']} />

        <Text style={styles.tip}>
          <Ionicons name="bulb" size={16} color="#FCD34D" /> Tip: Monitor alerts daily for optimal yield. Our AI expert analyzes 30+ years of farming data.
        </Text>
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
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  welcome: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '900',
    marginTop: 12,
  },
  subtitle: {
    color: '#CBD5E1',
    fontSize: 16,
    marginTop: 4,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 32,
  },
  statCard: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 16,
    padding: 20,
    width: '48%',
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 12,
    elevation: 8,
  },
  statValue: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '800',
    marginTop: 8,
  },
  statLabel: {
    color: '#CBD5E1',
    fontSize: 14,
    marginTop: 4,
  },
  tip: {
    marginTop: 24,
    color: '#E2E8F0',
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
});
