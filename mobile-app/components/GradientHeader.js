import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Dimensions } from 'react-native';
import { LinearGradient } from 'react-native-linear-gradient';

const { width } = Dimensions.get('window');

export default function GradientHeader({ subtitle }) {
  const shiftAnim = useRef(new Animated.Value(0)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.loop(
        Animated.sequence([
          Animated.timing(shiftAnim, {
            toValue: 1,
            duration: 4500,
            useNativeDriver: false,
          }),
          Animated.timing(shiftAnim, {
            toValue: 0,
            duration: 4500,
            useNativeDriver: false,
          }),
        ])
      ),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
  }, [shiftAnim, opacityAnim]);

  const translateX = shiftAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, width * 0.05],
  });

  return (
    <Animated.View style={[styles.outer, { opacity: opacityAnim, transform: [{ translateX }] }]}> 
      <LinearGradient
        colors={['rgba(16,185,129,0.92)', 'rgba(59,130,246,0.72)', 'rgba(168,85,247,0.42)']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        <View style={styles.content}>
          <Text style={styles.title}>Smarfa</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>
        </View>
      </LinearGradient>
    </Animated.View>
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
