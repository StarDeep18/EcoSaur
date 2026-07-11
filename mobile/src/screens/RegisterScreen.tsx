import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, useColorScheme } from 'react-native';
import { useRouter } from 'expo-router';
import { supabase } from '../services/supabase';
import { THEME } from '../theme';

export default function RegisterScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme() ?? 'dark';
  const theme = THEME[colorScheme as 'light' | 'dark'];

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSignUp = async () => {
    if (!email.trim() || !password.trim()) {
      setErrorMsg('Please enter both email and password.');
      return;
    }
    if (password.length < 6) {
      setErrorMsg('Password must be at least 6 characters.');
      return;
    }
    setErrorMsg('');
    setLoading(true);

    try {
      const { error } = await supabase.auth.signUp({
        email: email.trim(),
        password: password,
      });

      setLoading(false);
      if (error) {
        setErrorMsg(error.message);
      } else {
        router.replace('/');
      }
    } catch (err: any) {
      setLoading(false);
      setErrorMsg('Failed to connect. Please check your internet connection.');
    }
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
      style={{ flex: 1, backgroundColor: theme.bg }}
    >
      <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', padding: 24 }}>
        
        {/* Header */}
        <View style={{ alignItems: 'center', marginBottom: 36 }}>
          <Text style={{ fontSize: 56, marginBottom: 12 }}>🦕</Text>
          <Text style={{ fontSize: 28, fontWeight: '800', color: theme.text, letterSpacing: -0.5 }}>
            Create Account
          </Text>
          <Text style={{ fontSize: 14, color: theme.muted, textAlign: 'center', marginTop: 6, paddingHorizontal: 20 }}>
            Join the EcoSaur community to start scanning and eating cleaner.
          </Text>
        </View>

        {/* Signup Card */}
        <View style={{
          backgroundColor: theme.card,
          borderWidth: 1,
          borderColor: theme.border,
          borderRadius: 24,
          padding: 24,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 6 },
          shadowOpacity: 0.1,
          shadowRadius: 12,
          elevation: 5,
        }}>
          {errorMsg ? (
            <View style={{
              backgroundColor: 'rgba(255, 69, 58, 0.1)',
              borderColor: 'rgba(255, 69, 58, 0.2)',
              borderWidth: 1,
              padding: 12,
              borderRadius: 12,
              marginBottom: 16,
            }}>
              <Text style={{ color: theme.error, fontSize: 13, fontWeight: '600', textAlign: 'center' }}>
                ⚠️ {errorMsg}
              </Text>
            </View>
          ) : null}

          {/* Email input */}
          <Text style={{ color: theme.text, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', marginBottom: 8, letterSpacing: 0.5 }}>
            Email Address
          </Text>
          <TextInput
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="example@mail.com"
            placeholderTextColor={theme.muted}
            style={{
              backgroundColor: theme.bg,
              color: theme.text,
              borderWidth: 1,
              borderColor: theme.border,
              borderRadius: 14,
              paddingHorizontal: 16,
              height: 48,
              fontSize: 14,
              marginBottom: 16,
            }}
          />

          {/* Password Input */}
          <Text style={{ color: theme.text, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', marginBottom: 8, letterSpacing: 0.5 }}>
            Password
          </Text>
          <TextInput
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
            placeholder="•••••••• (Min 6 chars)"
            placeholderTextColor={theme.muted}
            style={{
              backgroundColor: theme.bg,
              color: theme.text,
              borderWidth: 1,
              borderColor: theme.border,
              borderRadius: 14,
              paddingHorizontal: 16,
              height: 48,
              fontSize: 14,
              marginBottom: 24,
            }}
          />

          {/* Submit */}
          <TouchableOpacity
            onPress={handleSignUp}
            disabled={loading}
            style={{
              backgroundColor: theme.primary,
              borderRadius: 14,
              height: 48,
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={{ color: '#FFFFFF', fontWeight: 'bold', fontSize: 15 }}>
                Sign Up
              </Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Redirect prompt */}
        <View style={{ flexDirection: 'row', justifyContent: 'center', marginTop: 24 }}>
          <Text style={{ color: theme.muted, fontSize: 14 }}>Already have an account? </Text>
          <TouchableOpacity onPress={() => router.push('/login')}>
            <Text style={{ color: theme.primary, fontWeight: 'bold', fontSize: 14 }}>Sign In</Text>
          </TouchableOpacity>
        </View>
        
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
