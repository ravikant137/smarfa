import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, Animated, TouchableOpacity, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import GradientHeader from '../components/GradientHeader';
import { getApiBaseUrl } from '../utils/api';
import axios from 'axios';

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const [alertsRes, scansRes] = await Promise.all([
        axios.get(`${getApiBaseUrl()}/alerts`).catch(() => ({ data: [] })),
        axios.get(`${getApiBaseUrl()}/scan_history?limit=20`).catch(() => ({ data: [] })),
      ]);

      const systemAlerts = (alertsRes.data || []).map((a) => ({
        id: `sys_${a.id}`,
        type: a.type,
        message: a.message,
        crop_id: a.crop_id,
        timestamp: a.timestamp,
        source: 'system',
      }));

      const scanAlerts = (scansRes.data || []).map((s) => ({
        id: `scan_${s.id}`,
        type: `crop_${s.severity}`,
        message: `${s.crop_detected} — ${s.severity?.toUpperCase()} detected at ${s.ai_confidence}% confidence.\n${s.health_assessment || ''}`,
        crop_id: s.crop_detected,
        timestamp: s.timestamp,
        source: 'scan',
      }));

      const merged = [...systemAlerts, ...scanAlerts].sort(
        (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
      );

      setAlerts(merged.length > 0 ? merged : getDefaultAlerts());
    } catch {
      setAlerts(getDefaultAlerts());
    } finally {
      setLoading(false);
      Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }).start();
    }
  };

  React.useEffect(() => {
    loadAlerts();
  }, []);

  function getDefaultAlerts() {
    return [
      {
        id: 'd1', type: 'intrusion_alarm', source: 'system',
        crop_id: 'field-1',
        message: 'Motion detected on land; possible intrusion. Solution: Check perimeter fencing and install motion-activated lights to deter wildlife.',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'd2', type: 'moisture_warning', source: 'system',
        crop_id: 'field-1',
        message: 'Soil moisture at 26% — too low for optimal growth. Solution: Irrigate immediately with drip system to maintain 40-60% moisture.',
        timestamp: new Date().toISOString(),
      },
    ];
  }

  const getAlertIcon = (type) => {
    if (type?.startsWith('crop_healthy')) return 'leaf-circle';
    if (type?.startsWith('crop_')) return 'virus';
    switch (type) {
      case 'intrusion_alarm': return 'shield-alert';
      case 'moisture_warning': return 'water-alert';
      case 'temp_warning': return 'thermometer-alert';
      case 'growth_drop': return 'trending-down';
      default: return 'alert-circle';
    }
  };

  const getAlertColor = (type) => {
    if (type === 'crop_healthy') return '#10B981';
    if (type?.startsWith('crop_critical')) return '#EF4444';
    if (type?.startsWith('crop_')) return '#F59E0B';
    switch (type) {
      case 'intrusion_alarm': return '#EF4444';
      case 'moisture_warning': return '#06B6D4';
      case 'temp_warning': return '#F59E0B';
      case 'growth_drop': return '#8B5CF6';
      default: return '#6B7280';
    }
  };

  return (
    <LinearGradient colors={['#0F172A', '#1E293B']} style={styles.container}>
      <GradientHeader />
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#10B981" />
          <Text style={styles.loadingText}>Loading alerts…</Text>
        </View>
      ) : (
        <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
          <FlatList
            data={alerts}
            keyExtractor={(item) => item.id.toString()}
            ListHeaderComponent={
              <View style={styles.listHeader}>
                <Text style={styles.countText}>{alerts.length} alert{alerts.length !== 1 ? 's' : ''}</Text>
                <TouchableOpacity onPress={loadAlerts}>
                  <MaterialCommunityIcons name="refresh" size={20} color="#10B981" />
                </TouchableOpacity>
              </View>
            }
            renderItem={({ item }) => (
              <Animated.View style={[styles.alertCard, {
                backgroundColor: getAlertColor(item.type) + '18',
                borderColor: getAlertColor(item.type),
              }]}>
                <View style={styles.alertHeader}>
                  <MaterialCommunityIcons name={getAlertIcon(item.type)} size={26} color={getAlertColor(item.type)} />
                  <Text style={[styles.alertType, { color: getAlertColor(item.type) }]}>
                    {item.type.replace(/_/g, ' ').toUpperCase()}
                  </Text>
                  {item.source === 'scan' && (
                    <View style={styles.badge}>
                      <Text style={styles.badgeTxt}>AI SCAN</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.alertCrop}>{item.crop_id}</Text>
                <Text style={styles.alertMsg}>{item.message}</Text>
                <Text style={styles.alertTime}>
                  {new Date(item.timestamp).toLocaleString()}
                </Text>
              </Animated.View>
            )}
            contentContainerStyle={styles.listContent}
          />
        </Animated.View>
      )}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10 },
  loadingText: { color: '#94A3B8', fontSize: 14 },
  listHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 4,
    marginBottom: 8,
  },
  countText: { color: '#94A3B8', fontSize: 13 },
  listContent: { padding: 16, paddingBottom: 30 },
  alertCard: {
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1.5,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 8,
    elevation: 5,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    gap: 8,
    flexWrap: 'wrap',
  },
  alertType: { fontWeight: '800', fontSize: 13, flex: 1 },
  badge: {
    backgroundColor: 'rgba(168,85,247,0.2)',
    borderRadius: 10,
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  badgeTxt: { color: '#A855F7', fontSize: 9, fontWeight: '800' },
  alertCrop: { color: '#CBD5E1', fontWeight: '600', marginBottom: 4, fontSize: 12 },
  alertMsg: { color: '#E2E8F0', fontSize: 13, lineHeight: 19, marginBottom: 8 },
  alertTime: { color: '#64748B', fontSize: 11 },
});

