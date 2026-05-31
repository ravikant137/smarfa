import React from 'react';
import { Platform } from 'react-native';
import StaticAuthUI from './StaticAuthUI';
import { NavigationContainer } from '@react-navigation/native';
import AppNavigator from './navigation/AppNavigator';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = React.useState(Platform.OS !== 'web');

  if (!isAuthenticated && Platform.OS === 'web') {
    return <StaticAuthUI onAuth={() => setIsAuthenticated(true)} />;
  }

  return (
    <NavigationContainer>
      <AppNavigator initialRoute={Platform.OS === 'web' ? 'Home' : 'Login'} />
    </NavigationContainer>
  );
}
