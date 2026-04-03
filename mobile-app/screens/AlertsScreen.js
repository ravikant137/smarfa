import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, Animated } from 'react-native';
import { LinearGradient } from 'react-native-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import GradientHeader from '../components/GradientHeader';
import axios from 'axios';

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState([]);
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }).start();
    axios.get('http://10.0.2.2:8000/alerts')
      .then((res) => setAlerts(res.data))
      .catch(() => {
        setAlerts([
          {
            id: 1,
            crop_id: 'field-1',
            type: 'intrusion_alarm',
            message: 'Motion detected on land; possible intrusion. Solution: Check perimeter fencing and install motion-activated lights to deter wildlife.',
            timestamp: new Date().toISOString()
          },
          {
            id: 2,
            crop_id: 'field-1',
            type: 'moisture_warning',
            message: 'Soil moisture at 26% - too low for optimal growth. Solution: Irrigate immediately with drip system to maintain 40-60% moisture for healthy root development.',
            timestamp: new Date().toISOString()
          },
          {
            id: 3,
            crop_id: 'field-1',
            type: 'temp_warning',
            message: 'Temperature at 14°C - below safe range. Solution: Apply frost protection covers or use windbreaks to shield crops from cold stress.',
            timestamp: new Date().toISOString()
          },
        ]);
      });
  }, [fadeAnim]);

  const getAlertIcon = (type) => {
    switch (type) {
      case 'intrusion_alarm': return 'shield-alert';
      case 'moisture_warning': return 'water-alert';
      case 'temp_warning': return 'thermometer-alert';
      case 'growth_drop': return 'trending-down';
      default: return 'alert-circle';
    }
  };

  const getAlertColor = (type) => {
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
      <GradientHeader subtitle="Actionable alerts for better yield" />
      <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
        <FlatList
        data={alerts}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <Animated.View style={[styles.alertCard, { backgroundColor: getAlertColor(item.type) + '20', borderColor: getAlertColor(item.type) }]}>
            <View style={styles.alertHeader}>
              <MaterialCommunityIcons name={getAlertIcon(item.type)} size={28} color={getAlertColor(item.type)} />
              <Text style={[styles.alertType, { color: getAlertColor(item.type) }]}>
                {item.type.replace(/_/g, ' ').toUpperCase()}
              </Text>
            </View>
            <Text style={styles.alertCrop}>Field: {item.crop_id}</Text>
            <Text style={styles.alertMsg}>{item.message}</Text>
            <Text style={styles.alertTime}>
              <Ionicons name="time" size={14} color="#9CA3AF" /> {new Date(item.timestamp).toLocaleString()}
            </Text>
          </Animated.View>
        )}
        contentContainerStyle={styles.listContent}
      />
      </Animated.View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 28,
    color: '#FFF',
    fontWeight: '900',
    marginTop: 12,
  },
  subtitle: {
    color: '#CBD5E1',
    fontSize: 14,
    marginTop: 4,
  },
  listContent: {
    padding: 20,
  },
  alertCard: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowOffset: { width: 0, height: 6 },
    shadowRadius: 10,
    elevation: 6,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  alertType: {
    fontWeight: '900',
    fontSize: 16,
    marginLeft: 8,
  },
  alertCrop: {
    color: '#374151',
    fontWeight: '600',
    marginBottom: 4,
  },
  alertMsg: {
    color: '#1F2937',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
  },
  alertTime: {
    color: '#6B7280',
    fontSize: 12,
    alignItems: 'center',
  },
});
