import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import { LinearGradient } from 'react-native-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import AnimatedButton from '../components/AnimatedButton';
import GradientHeader from '../components/GradientHeader';

export default function RegisterScreen({ navigation }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const slideAnim = React.useRef(new Animated.Value(300)).current;

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
          <AnimatedButton title="Register" onPress={() => navigation.navigate('Home')} colors={['#059669', '#047857']} />
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
