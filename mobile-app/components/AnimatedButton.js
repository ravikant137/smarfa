import React from 'react';
import { TouchableOpacity, Text, StyleSheet, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

export default function AnimatedButton({ title, onPress, colors = ['#4CAF50', '#2E7D32'], disabled = false }) {
  const scale = React.useRef(new Animated.Value(1)).current;

  const onPressIn = () => {
    if (!disabled) {
      Animated.spring(scale, { toValue: 0.95, useNativeDriver: true }).start();
    }
  };

  const onPressOut = () => {
    if (!disabled) {
      Animated.spring(scale, { toValue: 1, friction: 3, useNativeDriver: true }).start();
    }
  };

  return (
    <Animated.View style={[{ transform: [{ scale }] }, styles.wrapper]}>
      <TouchableOpacity
        style={[styles.button, disabled && styles.disabledButton]}
        onPress={onPress}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        activeOpacity={0.8}
        disabled={disabled}
      >
        <LinearGradient colors={colors} style={[styles.gradient, disabled && styles.disabledGradient]}>
          <Text style={styles.text}>{title}</Text>
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    width: '100%',
    marginVertical: 12,
  },
  button: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 12,
    elevation: 8,
  },
  disabledButton: {
    opacity: 0.75,
  },
  gradient: {
    paddingVertical: 18,
    alignItems: 'center',
  },
  disabledGradient: {
    opacity: 0.75,
  },
  text: {
    color: '#fff',
    fontWeight: '800',
    fontSize: 18,
    letterSpacing: 0.5,
  },
});
