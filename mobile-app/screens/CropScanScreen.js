import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, Image, Animated, ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import AnimatedButton from '../components/AnimatedButton';
import GradientHeader from '../components/GradientHeader';
import { getApiBaseUrl } from '../utils/api';
import axios from 'axios';

export default function CropScanScreen() {
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }).start();
    loadHistory();
  }, [fadeAnim]);

  const loadHistory = async () => {
    try {
      const response = await axios.get(`${getApiBaseUrl()}/scan_history?limit=8`, { timeout: 10000 });
      setHistory(Array.isArray(response.data) ? response.data : []);
    } catch {
      setHistory([]);
    }
  };

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      setError('Permission to access gallery is required.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.7,
      base64: true,
    });
    if (!result.canceled && result.assets?.[0]) {
      setImage(result.assets[0]);
      setAnalysis(null);
      setError('');
    }
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      setError('Permission to access camera is required.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      quality: 0.7,
      base64: true,
    });
    if (!result.canceled && result.assets?.[0]) {
      setImage(result.assets[0]);
      setAnalysis(null);
      setError('');
    }
  };

  const analyzeImage = async () => {
    if (!image?.base64) {
      setError('Please select or capture an image first.');
      return;
    }
    setLoading(true);
    setError('');
    setAnalysis(null);
    try {
      const response = await axios.post(`${getApiBaseUrl()}/analyze_crop`, {
        image_base64: image.base64,
      }, { timeout: 60000 });
      setAnalysis(response.data);
      loadHistory();
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#EF4444';
      case 'warning': return '#F59E0B';
      case 'healthy': return '#10B981';
      default: return '#3B82F6';
    }
  };

  return (
    <LinearGradient colors={['#0F172A', '#1E293B']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <GradientHeader subtitle="AI-powered crop health analysis" />
        <Animated.View style={{ opacity: fadeAnim }}>
          {image ? (
            <View style={styles.imageContainer}>
              <Image source={{ uri: image.uri }} style={styles.preview} />
            </View>
          ) : (
            <View style={styles.placeholder}>
              <MaterialCommunityIcons name="leaf-circle-outline" size={80} color="#10B981" />
              <Text style={styles.placeholderText}>Capture or select a crop image</Text>
            </View>
          )}

          <View style={styles.buttonRow}>
            <View style={styles.halfButton}>
              <AnimatedButton title="Camera" onPress={takePhoto} colors={['#3B82F6', '#2563EB']} />
            </View>
            <View style={styles.halfButton}>
              <AnimatedButton title="Gallery" onPress={pickImage} colors={['#8B5CF6', '#7C3AED']} />
            </View>
          </View>

          {image && (
            <AnimatedButton
              title={loading ? 'Analyzing...' : 'Analyze Crop'}
              onPress={analyzeImage}
              colors={['#10B981', '#059669']}
              disabled={loading}
            />
          )}

          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#10B981" />
              <Text style={styles.loadingText}>AI is analyzing your crop...</Text>
            </View>
          )}

          {error ? <Text style={styles.errorText}>{error}</Text> : null}

          {analysis && (
            <View style={styles.analysisContainer}>
              <View style={[styles.severityBadge, { backgroundColor: getSeverityColor(analysis.severity) + '30', borderColor: getSeverityColor(analysis.severity) }]}>
                <MaterialCommunityIcons
                  name={analysis.severity === 'healthy' ? 'check-circle' : 'alert-circle'}
                  size={24}
                  color={getSeverityColor(analysis.severity)}
                />
                <Text style={[styles.severityText, { color: getSeverityColor(analysis.severity) }]}>
                  {(analysis.severity || 'info').toUpperCase()}
                </Text>
              </View>

              <Text style={styles.cropName}>{analysis.crop_detected || 'Unknown Crop'}</Text>

              <Text style={styles.sectionTitle}>
                <MaterialCommunityIcons name="stethoscope" size={18} color="#3B82F6" /> Health Assessment
              </Text>
              <Text style={styles.analysisText}>{analysis.health_assessment}</Text>

              {analysis.issues?.length > 0 && (
                <>
                  <Text style={styles.sectionTitle}>
                    <Ionicons name="warning" size={18} color="#F59E0B" /> Issues Detected
                  </Text>
                  {analysis.issues.map((issue, idx) => (
                    <View key={idx} style={styles.issueCard}>
                      <Text style={styles.issueName}>{issue.name}</Text>
                      <Text style={styles.issueDesc}>{issue.description}</Text>
                    </View>
                  ))}
                </>
              )}

              {analysis.recommendations?.length > 0 && (
                <>
                  <Text style={styles.sectionTitle}>
                    <MaterialCommunityIcons name="lightbulb-on" size={18} color="#10B981" /> Recommendations
                  </Text>
                  {analysis.recommendations.map((rec, idx) => (
                    <View key={idx} style={styles.recCard}>
                      <MaterialCommunityIcons name="check-decagram" size={18} color="#10B981" />
                      <Text style={styles.recText}>{rec}</Text>
                    </View>
                  ))}
                </>
              )}

              {analysis.growth_needs && (
                <>
                  <Text style={styles.sectionTitle}>
                    <MaterialCommunityIcons name="sprout" size={18} color="#8B5CF6" /> Growth Needs
                  </Text>
                  <Text style={styles.analysisText}>{analysis.growth_needs}</Text>
                </>
              )}
            </View>
          )}

          {history.length > 0 && (
            <View style={styles.analysisContainer}>
              <Text style={styles.sectionTitle}>
                <MaterialCommunityIcons name="history" size={18} color="#3B82F6" /> Scan History
              </Text>
              {history.map((item) => (
                <View key={item.id} style={styles.issueCard}>
                  <Text style={styles.issueName}>
                    {item.crop_detected} • {(item.severity || 'info').toUpperCase()} • {Math.round(item.ai_confidence || 0)}%
                  </Text>
                  <Text style={styles.issueDesc}>{new Date(item.timestamp).toLocaleString()}</Text>
                </View>
              ))}
            </View>
          )}
        </Animated.View>
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 20, paddingTop: 60, paddingBottom: 40 },
  imageContainer: {
    borderRadius: 20,
    overflow: 'hidden',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 12,
    elevation: 8,
  },
  preview: {
    width: '100%',
    height: 250,
    borderRadius: 20,
  },
  placeholder: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 20,
    borderWidth: 2,
    borderColor: 'rgba(16,185,129,0.3)',
    borderStyle: 'dashed',
    padding: 40,
    alignItems: 'center',
    marginBottom: 16,
  },
  placeholderText: {
    color: '#94A3B8',
    fontSize: 16,
    marginTop: 12,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  halfButton: { flex: 1 },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    color: '#10B981',
    marginTop: 12,
    fontSize: 15,
  },
  errorText: {
    color: '#EF4444',
    textAlign: 'center',
    marginTop: 12,
    fontWeight: '700',
  },
  analysisContainer: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 20,
    padding: 20,
    marginTop: 20,
  },
  severityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    borderRadius: 12,
    borderWidth: 1.5,
    paddingHorizontal: 14,
    paddingVertical: 6,
    marginBottom: 12,
  },
  severityText: {
    fontWeight: '800',
    fontSize: 14,
    marginLeft: 6,
  },
  cropName: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '800',
    marginBottom: 16,
  },
  sectionTitle: {
    color: '#CBD5E1',
    fontSize: 16,
    fontWeight: '700',
    marginTop: 16,
    marginBottom: 8,
  },
  analysisText: {
    color: '#E2E8F0',
    fontSize: 14,
    lineHeight: 22,
  },
  issueCard: {
    backgroundColor: 'rgba(239,68,68,0.1)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  issueName: {
    color: '#F87171',
    fontWeight: '700',
    fontSize: 14,
    marginBottom: 4,
  },
  issueDesc: {
    color: '#E2E8F0',
    fontSize: 13,
    lineHeight: 20,
  },
  recCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  recText: {
    color: '#E2E8F0',
    fontSize: 14,
    lineHeight: 20,
    marginLeft: 8,
    flex: 1,
  },
});
