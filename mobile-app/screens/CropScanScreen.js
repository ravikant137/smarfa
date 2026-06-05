import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, Image, Animated,
  ActivityIndicator, TouchableOpacity, Platform, Easing
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import GradientHeader from '../components/GradientHeader';
import { getApiBaseUrl } from '../utils/api';
import axios from 'axios';

const CROPS = ['Auto Detect', 'Tomato', 'Wheat', 'Rice', 'Corn', 'Apple', 'Potato', 'Grape'];

async function toBase64(asset) {
  if (asset.base64) return asset.base64;
  if (asset.uri && asset.uri.startsWith('data:')) {
    return asset.uri.split(',')[1];
  }
  
  const resp = await fetch(asset.uri);
  const blob = await resp.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export default function CropScanScreen() {
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');
  const [selectedCrop, setSelectedCrop] = useState('Auto Detect');
  const [showCropPicker, setShowCropPicker] = useState(false);

  // Animations
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const scanLineAnim = useRef(new Animated.Value(0)).current;
  const resultsSlideAnim = useRef(new Animated.Value(100)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
      Animated.spring(slideAnim, { toValue: 0, tension: 50, friction: 8, useNativeDriver: true })
    ]).start();
  }, []);

  useEffect(() => {
    if (loading) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.05, duration: 800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 800, easing: Easing.inOut(Easing.ease), useNativeDriver: true })
        ])
      ).start();

      Animated.loop(
        Animated.sequence([
          Animated.timing(scanLineAnim, { toValue: 250, duration: 2000, easing: Easing.linear, useNativeDriver: true }),
          Animated.timing(scanLineAnim, { toValue: 0, duration: 0, useNativeDriver: true })
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
      scanLineAnim.setValue(0);
    }
  }, [loading]);

  useEffect(() => {
    if (analysis) {
      resultsSlideAnim.setValue(100);
      Animated.spring(resultsSlideAnim, { toValue: 0, tension: 60, friction: 7, useNativeDriver: true }).start();
    }
  }, [analysis]);

  const handleImagePick = async (useCamera = false) => {
    const permMethod = useCamera ? ImagePicker.requestCameraPermissionsAsync : ImagePicker.requestMediaLibraryPermissionsAsync;
    const launchMethod = useCamera ? ImagePicker.launchCameraAsync : ImagePicker.launchImageLibraryAsync;
    
    const { status } = await permMethod();
    if (status !== 'granted') { setError('Permission required.'); return; }
    
    const result = await launchMethod({ mediaTypes: ['images'], quality: 0.85, base64: true });
    if (!result.canceled && result.assets?.[0]) {
      setImage(result.assets[0]);
      setAnalysis(null);
      setError('');
    }
  };

  const analyzeImage = async () => {
    if (!image) return setError('Please select an image first.');
    setLoading(true); setError(''); setAnalysis(null);
    try {
      const b64 = await toBase64(image);
      const payload = { image_base64: b64, ...(selectedCrop !== 'Auto Detect' && { crop_hint: selectedCrop }) };
      const response = await axios.post(`${getApiBaseUrl()}/api/v1/scan`, payload, { timeout: 300000 });
      if (response.data.success === false) throw new Error(response.data.message);
      
      const analysisData = response.data.data || response.data;
      setAnalysis(analysisData);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (s) => s === 'critical' ? '#FF4B4B' : s === 'warning' ? '#FFB800' : '#00E676';
  const getSeverityIcon = (s) => s === 'critical' ? 'alert-octagon' : s === 'warning' ? 'alert' : 'check-decagram';

  return (
    <LinearGradient colors={['#09090E', '#141421']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <GradientHeader subtitle="Next-Gen AI Crop Diagnostics" />
        
        <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
          
          {/* Glassmorphic Image Container */}
          <Animated.View style={[styles.glassCard, loading && { transform: [{ scale: pulseAnim }] }]}>
            {image ? (
              <View style={styles.imageWrapper}>
                <Image source={{ uri: image.uri }} style={styles.preview} />
                {loading && (
                  <Animated.View style={[styles.scanLine, { transform: [{ translateY: scanLineAnim }] }]} />
                )}
                {loading && <View style={styles.scanningOverlay} />}
              </View>
            ) : (
              <View style={styles.placeholder}>
                <MaterialCommunityIcons name="leaf-circle-outline" size={80} color="#00E676" style={styles.glowIcon} />
                <Text style={styles.placeholderText}>Upload crop image</Text>
                <Text style={styles.placeholderSub}>AI vision analyzes down to the pixel</Text>
              </View>
            )}
          </Animated.View>

          {/* Action Row */}
          <View style={styles.actionRow}>
            <TouchableOpacity style={styles.actionBtn} onPress={() => handleImagePick(true)}>
              <LinearGradient colors={['#2979FF', '#1565C0']} style={styles.btnGradient}>
                <Ionicons name="camera-outline" size={22} color="#FFF" />
                <Text style={styles.btnText}>Camera</Text>
              </LinearGradient>
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionBtn} onPress={() => handleImagePick(false)}>
              <LinearGradient colors={['#8E24AA', '#512DA8']} style={styles.btnGradient}>
                <Ionicons name="image-outline" size={22} color="#FFF" />
                <Text style={styles.btnText}>Gallery</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>

          {/* Crop Selector */}
          <View style={styles.selectorWrapper}>
            <TouchableOpacity style={styles.selectorBtn} onPress={() => setShowCropPicker(!showCropPicker)}>
              <Text style={styles.selectorLabel}>Crop Type</Text>
              <View style={styles.selectorValueGroup}>
                <Text style={styles.selectorValue}>{selectedCrop}</Text>
                <Ionicons name={showCropPicker ? "chevron-up" : "chevron-down"} size={18} color="#00E676" />
              </View>
            </TouchableOpacity>
            {showCropPicker && (
              <View style={styles.dropdown}>
                {CROPS.map(c => (
                  <TouchableOpacity key={c} style={styles.dropdownItem} onPress={() => { setSelectedCrop(c); setShowCropPicker(false); }}>
                    <Text style={[styles.dropdownItemText, selectedCrop === c && styles.dropdownItemActive]}>{c}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          {/* Analyze Button */}
          {image && (
            <TouchableOpacity onPress={analyzeImage} disabled={loading} style={styles.analyzeBtnWrapper}>
              <LinearGradient colors={loading ? ['#424242', '#212121'] : ['#00E676', '#00C853']} style={styles.analyzeBtn}>
                {loading ? <ActivityIndicator color="#00E676" /> : <MaterialCommunityIcons name="brain" size={24} color="#FFF" />}
                <Text style={styles.analyzeBtnText}>{loading ? 'AI Analyzing...' : 'Run Diagnostics'}</Text>
              </LinearGradient>
            </TouchableOpacity>
          )}

          {error ? (
            <View style={styles.errorCard}>
              <Ionicons name="warning" size={20} color="#FF5252" />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          {/* Premium Animated Results */}
          {analysis && (
            <Animated.View style={[styles.resultsContainer, { opacity: fadeAnim, transform: [{ translateY: resultsSlideAnim }] }]}>
              
              <View style={styles.resultHeader}>
                <View>
                  <Text style={styles.cropTitle}>{analysis.crop_detected}</Text>
                  <Text style={styles.diseaseTitle}>{analysis.disease === 'Healthy' ? 'No Disease Detected' : analysis.disease}</Text>
                </View>
                <View style={[styles.badge, { backgroundColor: getSeverityColor(analysis.severity) + '1A', borderColor: getSeverityColor(analysis.severity) }]}>
                  <MaterialCommunityIcons name={getSeverityIcon(analysis.severity)} size={18} color={getSeverityColor(analysis.severity)} />
                  <Text style={[styles.badgeText, { color: getSeverityColor(analysis.severity) }]}>{analysis.severity.toUpperCase()}</Text>
                </View>
              </View>

              <View style={styles.confidenceBg}>
                <View style={[styles.confidenceFill, { width: `${analysis.ai_confidence}%`, backgroundColor: getSeverityColor(analysis.severity) }]} />
              </View>
              <Text style={styles.confidenceText}>AI Confidence: {Math.round(analysis.ai_confidence)}%</Text>

              <View style={styles.cardSection}>
                <Text style={styles.sectionHeading}><MaterialCommunityIcons name="text-box-search" size={18} /> Assessment</Text>
                <Text style={styles.sectionBody}>{analysis.health_assessment}</Text>
              </View>

              {analysis.issues?.length > 0 && (
                <View style={styles.cardSection}>
                  <Text style={[styles.sectionHeading, { color: '#FFB800' }]}><MaterialCommunityIcons name="alert" size={18} /> Issues Found</Text>
                  {analysis.issues.map((i, idx) => (
                    <View key={idx} style={styles.issueItem}>
                      <Text style={styles.issueTitle}>{i.name}</Text>
                      <Text style={styles.issueDesc}>{i.description}</Text>
                    </View>
                  ))}
                </View>
              )}

              {analysis.recommendations?.length > 0 && (
                <View style={styles.cardSection}>
                  <Text style={[styles.sectionHeading, { color: '#00E676' }]}><MaterialCommunityIcons name="shield-check" size={18} /> Recommendations</Text>
                  {analysis.recommendations.map((r, idx) => (
                    <View key={idx} style={styles.recItem}>
                      <View style={styles.recDot} />
                      <Text style={styles.recText}>{r}</Text>
                    </View>
                  ))}
                </View>
              )}

            </Animated.View>
          )}

        </Animated.View>
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 20, paddingTop: 60, paddingBottom: 60 },
  
  glassCard: {
    backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 24, padding: 16,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)', marginBottom: 20,
    shadowColor: '#00E676', shadowOpacity: 0.1, shadowRadius: 20, shadowOffset: { width: 0, height: 10 }
  },
  imageWrapper: { borderRadius: 16, overflow: 'hidden', position: 'relative' },
  preview: { width: '100%', height: 250 },
  scanningOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,230,118,0.1)' },
  scanLine: { position: 'absolute', width: '100%', height: 3, backgroundColor: '#00E676', shadowColor: '#00E676', shadowOpacity: 1, shadowRadius: 10, elevation: 10 },
  
  placeholder: { padding: 40, alignItems: 'center' },
  glowIcon: { textShadowColor: 'rgba(0,230,118,0.5)', textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 20, marginBottom: 12 },
  placeholderText: { color: '#FFF', fontSize: 18, fontWeight: '700' },
  placeholderSub: { color: '#8892B0', fontSize: 13, marginTop: 8 },

  actionRow: { flexDirection: 'row', gap: 12, marginBottom: 20 },
  actionBtn: { flex: 1, borderRadius: 16, overflow: 'hidden' },
  btnGradient: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 16, gap: 8 },
  btnText: { color: '#FFF', fontWeight: '700', fontSize: 15 },

  selectorWrapper: { backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 16, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(255,255,255,0.05)' },
  selectorBtn: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  selectorLabel: { color: '#8892B0', fontSize: 14, fontWeight: '600' },
  selectorValueGroup: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  selectorValue: { color: '#FFF', fontSize: 15, fontWeight: '700' },
  dropdown: { borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.05)' },
  dropdownItem: { padding: 16, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.02)' },
  dropdownItemText: { color: '#8892B0', fontSize: 14 },
  dropdownItemActive: { color: '#00E676', fontWeight: '700' },

  analyzeBtnWrapper: { borderRadius: 16, overflow: 'hidden', marginBottom: 20, shadowColor: '#00E676', shadowOpacity: 0.3, shadowRadius: 15, shadowOffset: { width: 0, height: 8 } },
  analyzeBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 18, gap: 10 },
  analyzeBtnText: { color: '#FFF', fontSize: 17, fontWeight: '800', letterSpacing: 0.5 },

  errorCard: { backgroundColor: 'rgba(255,82,82,0.1)', borderWidth: 1, borderColor: 'rgba(255,82,82,0.3)', padding: 16, borderRadius: 16, flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 },
  errorText: { color: '#FF8A80', flex: 1, fontSize: 14 },

  resultsContainer: { backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 24, padding: 24, borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)' },
  resultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 },
  cropTitle: { color: '#FFF', fontSize: 26, fontWeight: '900', letterSpacing: -0.5 },
  diseaseTitle: { color: '#A0ABC0', fontSize: 16, fontWeight: '600', marginTop: 4 },
  badge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12, borderWidth: 1 },
  badgeText: { fontWeight: '800', fontSize: 12, letterSpacing: 0.5 },

  confidenceBg: { height: 6, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 3, overflow: 'hidden', marginBottom: 8 },
  confidenceFill: { height: '100%', borderRadius: 3 },
  confidenceText: { color: '#8892B0', fontSize: 12, fontWeight: '600', alignSelf: 'flex-end', marginBottom: 24 },

  cardSection: { marginBottom: 24 },
  sectionHeading: { color: '#00E676', fontSize: 16, fontWeight: '800', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 },
  sectionBody: { color: '#D1D5DB', fontSize: 15, lineHeight: 24 },

  issueItem: { backgroundColor: 'rgba(255,255,255,0.03)', padding: 16, borderRadius: 12, marginBottom: 10 },
  issueTitle: { color: '#FFB800', fontWeight: '700', fontSize: 15, marginBottom: 6 },
  issueDesc: { color: '#A0ABC0', fontSize: 14, lineHeight: 22 },

  recItem: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 12, gap: 12 },
  recDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#00E676', marginTop: 8, shadowColor: '#00E676', shadowOpacity: 0.8, shadowRadius: 6 },
  recText: { color: '#D1D5DB', flex: 1, fontSize: 15, lineHeight: 24 }
});
