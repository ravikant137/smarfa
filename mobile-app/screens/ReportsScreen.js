import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import GradientHeader from '../components/GradientHeader';
import { getApiBaseUrl } from '../utils/api';

const SEV_COLOR = { healthy: '#10B981', warning: '#F59E0B', critical: '#EF4444' };
const SEV_ICON = { healthy: 'leaf', warning: 'alert', critical: 'virus' };

function severityColor(sev) { return SEV_COLOR[sev] || '#6B7280'; }
function severityIcon(sev) { return SEV_ICON[sev] || 'help-circle'; }

export default function ReportsScreen() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [report, setReport] = useState(null);

  const loadReport = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${getApiBaseUrl()}/reports/overview`, { timeout: 15000 });
      setReport(res.data);
    } catch (err) {
      setError('Could not load reports. Make sure the server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadReport(); }, []);

  const healthColor = (s) => s >= 80 ? '#10B981' : s >= 50 ? '#F59E0B' : '#EF4444';
  const healthLabel = (s) => s >= 80 ? 'Great' : s >= 50 ? 'Fair' : 'Poor';

  return (
    <LinearGradient colors={['#0F172A', '#1E293B']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <GradientHeader />

        {loading && (
          <View style={styles.center}>
            <ActivityIndicator size="large" color="#10B981" />
            <Text style={styles.loadingText}>Loading reportsâ€¦</Text>
          </View>
        )}

        {!loading && error ? (
          <View style={styles.errorCard}>
            <MaterialCommunityIcons name="wifi-off" size={28} color="#EF4444" />
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity onPress={loadReport} style={styles.retryBtn}>
              <Text style={styles.retryTxt}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {!loading && report ? (
          <>
            {/* Health Score */}
            <View style={[styles.scoreCard, { borderColor: healthColor(report.health_score || 0) }]}>
              <LinearGradient
                colors={['rgba(16,185,129,0.12)', 'rgba(59,130,246,0.10)']}
                style={styles.scoreInner}>
                <MaterialCommunityIcons name="heart-pulse" size={32} color={healthColor(report.health_score || 0)} />
                <Text style={[styles.scoreNum, { color: healthColor(report.health_score || 0) }]}>
                  {report.health_score ?? 0}%
                </Text>
                <Text style={styles.scoreLabel}>
                  Farm Health â€” {healthLabel(report.health_score || 0)}
                </Text>
              </LinearGradient>
            </View>

            {/* Stats Row */}
            <View style={styles.grid}>
              <View style={styles.stat}>
                <MaterialCommunityIcons name="barcode-scan" size={22} color="#10B981" />
                <Text style={styles.statVal}>{report.total_scans ?? 0}</Text>
                <Text style={styles.statLbl}>Total Scans</Text>
              </View>
              <View style={styles.stat}>
                <MaterialCommunityIcons name="sprout" size={22} color="#3B82F6" />
                <Text style={styles.statVal}>{report.total_crops ?? 0}</Text>
                <Text style={styles.statLbl}>Crops Found</Text>
              </View>
              <View style={styles.stat}>
                <MaterialCommunityIcons name="brain" size={22} color="#A855F7" />
                <Text style={styles.statVal}>{report.avg_confidence ?? 0}%</Text>
                <Text style={styles.statLbl}>Avg AI Score</Text>
              </View>
              <View style={styles.stat}>
                <MaterialCommunityIcons name="bell-alert" size={22} color="#F59E0B" />
                <Text style={styles.statVal}>{report.week_summary?.alerts_count ?? 0}</Text>
                <Text style={styles.statLbl}>Alerts (7d)</Text>
              </View>
            </View>

            {/* Recent Scans */}
            {(report.recent_scans || []).length > 0 && (
              <View style={styles.panel}>
                <Text style={styles.panelTitle}>
                  <MaterialCommunityIcons name="history" size={16} color="#10B981" />  Recent Scans
                </Text>
                {(report.recent_scans || []).map((scan) => (
                  <View key={scan.id} style={[styles.scanRow, { borderLeftColor: severityColor(scan.severity) }]}>
                    <View style={styles.scanLeft}>
                      <MaterialCommunityIcons name={severityIcon(scan.severity)} size={20} color={severityColor(scan.severity)} />
                      <View style={{ marginLeft: 10, flex: 1 }}>
                        <Text style={styles.scanCrop}>{scan.crop_detected}</Text>
                        <Text style={styles.scanDetail}>
                          {scan.severity?.toUpperCase()}  Â·  {scan.ai_confidence}% confidence
                        </Text>
                        {scan.health_assessment ? (
                          <Text style={styles.scanAssess} numberOfLines={2}>{scan.health_assessment}</Text>
                        ) : null}
                      </View>
                    </View>
                    <Text style={styles.scanTime}>
                      {new Date(scan.timestamp).toLocaleDateString()}
                    </Text>
                  </View>
                ))}
              </View>
            )}

            {(report.recent_scans || []).length === 0 && (
              <View style={styles.panel}>
                <Text style={styles.panelTitle}>Recent Scans</Text>
                <Text style={styles.emptyText}>No scans yet. Use Crop Scan to analyse your crops!</Text>
              </View>
            )}

            {/* Weekly sensor summary */}
            {(report.week_summary?.readings_count ?? 0) > 0 && (
              <View style={styles.panel}>
                <Text style={styles.panelTitle}>
                  <MaterialCommunityIcons name="thermometer" size={16} color="#3B82F6" />  Sensor Summary (7 days)
                </Text>
                <View style={styles.sensorGrid}>
                  <View style={styles.sensorItem}>
                    <MaterialCommunityIcons name="thermometer" size={18} color="#F59E0B" />
                    <Text style={styles.sensorVal}>{report.week_summary.avg_temp}Â°C</Text>
                    <Text style={styles.sensorLbl}>Avg Temp</Text>
                  </View>
                  <View style={styles.sensorItem}>
                    <MaterialCommunityIcons name="water-percent" size={18} color="#06B6D4" />
                    <Text style={styles.sensorVal}>{report.week_summary.avg_moisture}%</Text>
                    <Text style={styles.sensorLbl}>Avg Moisture</Text>
                  </View>
                  <View style={styles.sensorItem}>
                    <MaterialCommunityIcons name="arrow-up-bold" size={18} color="#10B981" />
                    <Text style={styles.sensorVal}>{report.week_summary.avg_height} cm</Text>
                    <Text style={styles.sensorLbl}>Avg Height</Text>
                  </View>
                  <View style={styles.sensorItem}>
                    <MaterialCommunityIcons name="pump" size={18} color="#A855F7" />
                    <Text style={styles.sensorVal}>{report.week_summary.pump_activations}</Text>
                    <Text style={styles.sensorLbl}>Pump Runs</Text>
                  </View>
                </View>
              </View>
            )}
          </>
        ) : null}
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: 16, paddingBottom: 40 },
  center: { alignItems: 'center', paddingVertical: 40 },
  loadingText: { color: '#94A3B8', marginTop: 10, fontSize: 14 },
  errorCard: {
    backgroundColor: 'rgba(239,68,68,0.1)',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    gap: 10,
    marginTop: 20,
  },
  errorText: { color: '#FCA5A5', fontSize: 14, textAlign: 'center' },
  retryBtn: {
    backgroundColor: 'rgba(16,185,129,0.2)',
    paddingHorizontal: 24,
    paddingVertical: 8,
    borderRadius: 20,
  },
  retryTxt: { color: '#10B981', fontWeight: '700' },
  scoreCard: {
    borderRadius: 20,
    borderWidth: 1.5,
    overflow: 'hidden',
    marginBottom: 16,
  },
  scoreInner: { padding: 22, alignItems: 'center' },
  scoreNum: { fontSize: 48, fontWeight: '900', marginTop: 6 },
  scoreLabel: { color: '#CBD5E1', fontSize: 14, marginTop: 4 },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
    gap: 10,
  },
  stat: {
    width: '47%',
    backgroundColor: 'rgba(255,255,255,0.07)',
    borderRadius: 14,
    padding: 14,
    alignItems: 'center',
    gap: 4,
  },
  statVal: { color: '#fff', fontSize: 22, fontWeight: '800' },
  statLbl: { color: '#94A3B8', fontSize: 11 },
  panel: {
    backgroundColor: 'rgba(255,255,255,0.07)',
    borderRadius: 16,
    padding: 14,
    marginBottom: 14,
  },
  panelTitle: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 12,
  },
  scanRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    borderLeftWidth: 3,
    paddingLeft: 10,
    marginBottom: 12,
  },
  scanLeft: { flexDirection: 'row', alignItems: 'flex-start', flex: 1 },
  scanCrop: { color: '#fff', fontWeight: '700', fontSize: 14 },
  scanDetail: { color: '#94A3B8', fontSize: 11, marginTop: 2 },
  scanAssess: { color: '#CBD5E1', fontSize: 11, marginTop: 3, fontStyle: 'italic' },
  scanTime: { color: '#64748B', fontSize: 10, marginLeft: 8, marginTop: 2 },
  emptyText: { color: '#94A3B8', fontSize: 13, textAlign: 'center', paddingVertical: 10 },
  sensorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    justifyContent: 'space-between',
  },
  sensorItem: {
    width: '47%',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 10,
    padding: 12,
    alignItems: 'center',
    gap: 4,
  },
  sensorVal: { color: '#fff', fontWeight: '700', fontSize: 16 },
  sensorLbl: { color: '#94A3B8', fontSize: 10 },
});
