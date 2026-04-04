import React from 'react';
import { Platform, View, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import AppNavigator from './navigation/AppNavigator';

export default function App() {
  const nav = (
    <NavigationContainer>
      <AppNavigator />
    </NavigationContainer>
  );

  if (Platform.OS !== 'web') return nav;

  return (
    <View style={styles.bg}>
      <View style={styles.phone}>
        {nav}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bg: {
    flex: 1,
    backgroundColor: '#0D1117',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
  },
  phone: {
    width: 390,
    height: 844,
    borderRadius: 50,
    overflow: 'hidden',
    borderWidth: 8,
    borderColor: '#1E3A5F',
    backgroundColor: '#0F172A',
    shadowColor: '#10B981',
    shadowOpacity: 0.25,
    shadowRadius: 40,
    elevation: 20,
  },
});
