import React from 'react';
import { Stack } from 'expo-router';
import { useColorScheme } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { THEME } from '../theme';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function RootLayout() {
  const colorScheme = useColorScheme() ?? 'dark';
  const theme = THEME[colorScheme as 'light' | 'dark'] || THEME.dark;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <SafeAreaProvider>
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
          </Stack>
        </SafeAreaProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
