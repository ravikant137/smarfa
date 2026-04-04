import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, Animated, Easing, Dimensions, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import AnimatedButton from '../components/AnimatedButton';
import GradientHeader from '../components/GradientHeader';
import axios from 'axios';

const { width, height } = Dimensions.get('window');

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const progress = React.useRef(new Animated.Value(0)).current;
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  const login = async () => {
    setError('');
    setLoading(true);
    try {
      const response = await axios.post('http://10.0.2.2:8000/login', {
        username: email.trim(),
        password,
      });
      setLoading(false);
      if (response.data?.status === 'login successful') {
        navigation.navigate('Home');
      }
    } catch (err) {
      setLoading(false);
      setError(err.response?.data?.detail || 'Login failed. Check credentials and try again.');
    }
  };

  React.useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(progress, { toValue: 1, duration: 2000, useNativeDriver: true, easing: Easing.out(Easing.quad) }),
        Animated.timing(progress, { toValue: 0, duration: 2000, useNativeDriver: true, easing: Easing.in(Easing.quad) }),
      ])
    ).start();
    Animated.timing(fadeAnim, { toValue: 1, duration: 1000, useNativeDriver: true }).start();
  }, [progress, fadeAnim]);

  const backgroundInterpolation = progress.interpolate({
    inputRange: [0, 1],
    outputRange: ['#1E3A8A', '#059669'],
  });

  return (
    <Animated.View style={[styles.container, { backgroundColor: backgroundInterpolation }]}> 
      <GradientHeader subtitle="Farm smarter with AI-powered insights" />
      <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
        <View style={styles.card}>
          <View style={styles.inputContainer}>
            <Ionicons name="mail" size={24} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              keyboardType="email-address"
              placeholder="Email"
              value={email}
              onChangeText={setEmail}
              placeholderTextColor="#999"
            />
          </View>
          <View style={styles.inputContainer}>
            <Ionicons name="lock-closed" size={24} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              secureTextEntry
              placeholder="Password"
              value={password}
              onChangeText={setPassword}
              placeholderTextColor="#999"
            />
          </View>
          <AnimatedButton title={loading ? 'Signing in...' : 'Login'} onPress={login} colors={['#059669', '#047857']} />
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
          <TouchableOpacity onPress={() => navigation.navigate('Register')} style={styles.link}>
            <Text style={styles.linkText}>New farmer? Create account</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  content: {
    alignItems: 'center',
  },
  icon: {
    marginBottom: 20,
  },
  title: {
    color: '#fff',
    fontSize: 32,
    fontWeight: '900',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    color: '#E0F2FE',
    textAlign: 'center',
    marginBottom: 32,
    fontSize: 16,
  },
  card: {
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderRadius: 24,
    padding: 24,
    width: '100%',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowOffset: { width: 0, height: 12 },
    shadowRadius: 16,
    elevation: 12,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    marginBottom: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    color: '#1F2937',
    fontSize: 16,
  },
  link: {
    marginTop: 16,
    alignSelf: 'center',
  },
  errorText: {
    color: '#EF4444',
    marginTop: 8,
    textAlign: 'center',
    fontWeight: '700',
  },
  linkText: {
    color: '#059669',
    fontSize: 16,
    fontWeight: '600',
  },
});
