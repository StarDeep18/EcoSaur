import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '';

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
        storage: AsyncStorage,
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
