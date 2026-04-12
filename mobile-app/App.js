import React from 'react';
import { Platform } from 'react-native';
import StaticAuthUI from './StaticAuthUI';
import { NavigationContainer } from '@react-navigation/native';
import AppNavigator from './navigation/AppNavigator';

export default function App() {
  if (Platform.OS === 'web') {
    return <StaticAuthUI />;
  }
  return (
    <NavigationContainer>
      <AppNavigator />
    </NavigationContainer>
  );
}
