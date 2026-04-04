import Constants from 'expo-constants';
import { Platform } from 'react-native';

export const getApiBaseUrl = () => {
  const debuggerHost =
    Constants.manifest?.debuggerHost ||
    Constants.manifest?.packagerOpts?.host ||
    Constants.expoConfig?.extra?.debuggerHost;

  if (debuggerHost) {
    const host = debuggerHost.split(':')[0];
    return `http://${host}:8000`;
  }

  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }

  return 'http://localhost:8000';
};
