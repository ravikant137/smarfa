import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import AnimatedButton from '../components/AnimatedButton';
import GradientHeader from '../components/GradientHeader';
import { getApiBaseUrl } from '../utils/api';
import axios from 'axios';

export default function RegisterScreen({ navigation }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const slideAnim = React.useRef(new Animated.Value(300)).current;

  const register = async () => {
    setError('');

    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password.');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${getApiBaseUrl()}/register`, {
        username: email.trim().toLowerCase(),
        password,
      });

      if (response.data?.status === 'user registered') {
        navigation.navigate('Home');
      } else {
        setError(response.data?.detail || 'Registration failed. Please try again.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true }).start();
  }, [slideAnim]);

  return (
    <LinearGradient colors={['#065F46', '#047857']} style={styles.container}>
      <GradientHeader subtitle="Create your farm intelligence dashboard" />
      <Animated.View style={[styles.content, { transform: [{ translateY: slideAnim }] }]}>
        <Ionicons name="person-add" size={60} color="#FFD700" style={styles.icon} />
        <Text style={styles.header}>Join Smart Farming</Text>
        <Text style={styles.subHeader}>Get expert crop insights instantly</Text>
        <View style={styles.card}>
          <View style={styles.inputContainer}>
            <Ionicons name="person" size={24} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Full Name"
              value={name}
              onChangeText={setName}
              placeholderTextColor="#999"
            />
          </View>
          <View style={styles.inputContainer}>
            <Ionicons name="mail" size={24} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Email"
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
              placeholderTextColor="#999"
            />
          </View>
          <View style={styles.inputContainer}>
            <Ionicons name="lock-closed" size={24} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Password"
              secureTextEntry
              value={password}
              onChangeText={setPassword}
              placeholderTextColor="#999"
            />
          </View>
          <AnimatedButton
            title={loading ? 'Creating account...' : 'Register'}
            onPress={register}
            colors={['#059669', '#047857']}
            disabled={loading}
          />
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.link}>
            <Text style={styles.linkText}>Already have account? Sign in</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    </LinearGradient>
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
  header: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '900',
    marginBottom: 8,
  },
  subHeader: {
    color: '#D1FAE5',
    textAlign: 'center',
    marginBottom: 24,
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
  errorText: {
    color: '#EF4444',
    marginTop: 8,
    textAlign: 'center',
    fontWeight: '700',
  },
  link: {
    marginTop: 16,
    alignSelf: 'center',
  },
  linkText: {
    color: '#059669',
    fontSize: 16,
    fontWeight: '600',
  },
});
