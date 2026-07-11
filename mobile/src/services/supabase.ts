import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '';

const inMemoryStorage: Record<string, string> = {};

const safeAsyncStorage = {
  getItem: async (key: string) => {
    try {
      // Direct access check to see if the module works
      return await AsyncStorage.getItem(key);
    } catch (e) {
      console.warn("⚠️ AsyncStorage.getItem failed, using in-memory fallback:", e);
      return inMemoryStorage[key] || null;
    }
  },
  setItem: async (key: string, value: string) => {
    try {
      await AsyncStorage.setItem(key, value);
    } catch (e) {
      console.warn("⚠️ AsyncStorage.setItem failed, using in-memory fallback:", e);
      inMemoryStorage[key] = value;
    }
  },
  removeItem: async (key: string) => {
    try {
      await AsyncStorage.removeItem(key);
    } catch (e) {
      console.warn("⚠️ AsyncStorage.removeItem failed, using in-memory fallback:", e);
      delete inMemoryStorage[key];
    }
  }
};

let supabaseClient: any;

try {
  const isValidUrl = supabaseUrl && supabaseUrl.startsWith('http') && !supabaseUrl.includes('YOUR_SUPABASE');
  if (!isValidUrl) {
    console.warn("⚠️ Supabase is not configured or URL is invalid. Mocking client to prevent app crash.");
    supabaseClient = {
      auth: {
        signUp: async () => ({ data: { user: null }, error: new Error("Supabase is not configured.") }),
        signInWithPassword: async () => ({ data: { user: null }, error: new Error("Supabase is not configured.") }),
        signOut: async () => ({ error: null }),
        getSession: async () => ({ data: { session: null }, error: null }),
        onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
      },
      storage: {
        from: () => ({
          upload: async () => ({ data: null, error: new Error("Supabase is not configured.") }),
          getPublicUrl: () => ({ data: { publicUrl: '' } }),
        })
      }
    };
  } else {
    supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        storage: safeAsyncStorage,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false,
      },
    });
  }
} catch (error) {
  console.error("❌ Failed to initialize Supabase client:", error);
}

export const supabase = supabaseClient;
