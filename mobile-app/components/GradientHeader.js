import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function GradientHeader({ subtitle }) {
  const staticSubtitle = 'Smart AI Farming';

  return (
    <View style={styles.outer}>
      <LinearGradient
        colors={['rgba(16,185,129,0.92)', 'rgba(59,130,246,0.72)', 'rgba(168,85,247,0.42)']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        <View style={styles.content}>
          <View style={styles.brandRow}>
            <MaterialCommunityIcons name="leaf-circle" size={34} color="#FFFFFF" />
            <Text style={styles.title}>Smarfa</Text>
          </View>
          <Text style={styles.subtitle}>{staticSubtitle}</Text>
        </View>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    width: '100%',
    borderRadius: 24,
    overflow: 'hidden',
    marginBottom: 24,
  },
  gradient: {
    paddingVertical: 24,
    paddingHorizontal: 20,
    backgroundColor: 'transparent',
  },
  content: {
    alignItems: 'center',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 34,
    fontWeight: '900',
    letterSpacing: 1,
  },
  subtitle: {
    marginTop: 8,
    color: 'rgba(255,255,255,0.94)',
    fontSize: 15,
    textAlign: 'center',
    maxWidth: '90%',
  },
});
