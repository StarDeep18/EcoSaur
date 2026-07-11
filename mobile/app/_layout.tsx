import React, { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { useColorScheme } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { supabase } from '../src/services/supabase';
import { THEME } from '../src/theme';
import { Session } from '@supabase/supabase-js';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <SafeAreaProvider>
          <RootLayoutNav />
        </SafeAreaProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}

function RootLayoutNav() {
  const colorScheme = useColorScheme() ?? 'dark';
  const theme = THEME[colorScheme as 'light' | 'dark'] || THEME.dark;
  const router = useRouter();
  const segments = useSegments();

  const [session, setSession] = useState<Session | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    // Check current active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setAuthChecked(true);
    });

    // Listen for real-time authentication events
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setAuthChecked(true);
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!authChecked) return;

    const inAuthGroup = segments[0] === 'login' || segments[0] === 'register';

    if (!session && !inAuthGroup) {
      // Redirect to sign in if there's no session
      router.replace('/login');
    } else if (session && inAuthGroup) {
      // Redirect to home if user is logged in but hits auth routes
      router.replace('/');
    }
  }, [session, segments, authChecked]);

  return (
    <>
      <StatusBar style={colorScheme === 'dark' ? 'light' : 'dark'} />
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: theme.bg,
          },
          headerTintColor: theme.text,
          headerTitleStyle: {
            fontWeight: 'bold',
          },
          contentStyle: {
            backgroundColor: theme.bg,
          },
        }}
      >
        <Stack.Screen 
          name="index" 
          options={{ 
            headerShown: false, 
          }} 
        />
        <Stack.Screen 
          name="login" 
          options={{ 
            headerShown: false, 
          }} 
        />
        <Stack.Screen 
          name="register" 
          options={{ 
            headerShown: false, 
          }} 
        />
        <Stack.Screen 
          name="scan" 
          options={{ 
            title: 'Scan Label / Barcode',
            headerBackTitle: 'Back',
          }} 
        />
        <Stack.Screen 
          name="correction" 
          options={{ 
            title: 'Review Ingredients',
            headerBackTitle: 'Cancel',
          }} 
        />
        <Stack.Screen 
          name="results" 
          options={{ 
            title: 'Shopping Guide',
            headerBackTitle: 'Edit',
          }} 
        />
        <Stack.Screen 
          name="profile" 
          options={{ 
            title: 'Dietary Preferences',
            headerBackTitle: 'Home',
          }} 
        />
      </Stack>
    </>
  );
}
