import Constants from 'expo-constants';
import { Platform } from 'react-native';

export const getApiBaseUrl = () => {
  // When running in a browser (web platform), always use localhost
  if (Platform.OS === 'web') {
    return 'http://127.0.0.1:8000';
  }

  // Check modern Expo SDK host fields first (works for Expo Go on device)
  const hostUri = Constants.expoConfig?.hostUri || Constants.manifest2?.extra?.expoGo?.hostUri;
  if (hostUri) {
    const host = hostUri.split(':')[0];
    return `http://${host}:8000`;
  }

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

  // Fallback for iOS physical device on local network
  return 'http://192.168.29.181:8000';
};
