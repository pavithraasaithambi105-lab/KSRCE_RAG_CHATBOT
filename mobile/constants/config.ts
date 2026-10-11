import { Platform } from 'react-native';

const configuredApiUrl = process.env.EXPO_PUBLIC_API_URL?.trim();
const webHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
const defaultApiHost = Platform.OS === 'web' ? webHost : Platform.OS === 'android' ? '10.0.2.2' : 'localhost';

export const API_URL = (configuredApiUrl || `http://${defaultApiHost}:8000`).replace(/\/$/, '');

export const BOT_NAME = 'Assistant';
