import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, ActivityIndicator, Alert, useColorScheme } from 'react-native';
import { useRouter } from 'expo-router';
import { supabase } from '../services/supabase';
import { api } from '../services/api';
import { THEME } from '../theme';

const HEALTH_MODES = [
  { id: 'General', label: 'General Wellness', icon: '🌿', desc: 'Standard science-backed nutritional parameters.' },
  { id: 'Weight Loss', label: 'Weight Management', icon: '🏃', desc: 'Alerts on high calorie or empty starch loads.' },
  { id: 'Gym/Fitness', label: 'Gym & Fitness', icon: '💪', desc: 'Highlights protein density and amino counts.' },
  { id: 'Diabetic Friendly', label: 'Diabetic Friendly', icon: '🩸', desc: 'Strict warnings on simple glycemic sweeteners.' },
  { id: 'Child Friendly', label: 'Child Friendly', icon: '👶', desc: 'Flags synthetic colors, dyes, and excess preservatives.' },
  { id: 'Low Sugar', label: 'Sugar Conscious', icon: '🍎', desc: 'Zeroes in on added sucrose and simple syrups.' },
  { id: 'Low Sodium', label: 'Heart Conscious (Low Sodium)', icon: '❤️', desc: 'Alerts on processing sodium/salt densities.' },
  { id: 'Vegetarian', label: 'Vegetarian', icon: '🥗', desc: 'Verifies ingredients are free of meat derivatives.' },
  { id: 'Vegan', label: 'Vegan', icon: '🌱', desc: 'Ensures zero animal/dairy components.' }
];

export default function ProfileScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme() ?? 'dark';
  const theme = THEME[colorScheme as 'light' | 'dark'];

  const [email, setEmail] = useState('');
  const [selectedMode, setSelectedMode] = useState('General');
  const [loading, setLoading] = useState(true);
  const [savingMode, setSavingMode] = useState<string | null>(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.replace('/login');
        return;
      }
      setEmail(session.user.email || '');

      const prefs = await api.getUserPreferences();
      if (prefs && prefs.health_mode) {
        setSelectedMode(prefs.health_mode);
      }
      setLoading(false);
    } catch (err) {
      setLoading(false);
      Alert.alert('Error', 'Failed to retrieve profile configuration settings.');
    }
  };

  const handleSelectMode = async (modeId: string) => {
    if (savingMode) return;
    setSavingMode(modeId);
    
    try {
      await api.updateUserPreferences(modeId);
      setSelectedMode(modeId);
      setSavingMode(null);
      Alert.alert('Success', `Dietary focus updated to ${modeId}!`);
    } catch (err) {
      setSavingMode(null);
      Alert.alert('Error', 'Failed to update dietary settings.');
    }
  };

  const handleSignOut = async () => {
    Alert.alert('Log Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Log Out',
        style: 'destructive',
        onPress: async () => {
          await supabase.auth.signOut();
          router.replace('/');
        }
      }
    ]);
  };

  const handleDeleteHistory = () => {
    Alert.alert(
      'Clear Scan History',
      'Are you sure you want to permanently clear all your scan logs? This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear History',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deleteHistory();
              Alert.alert('History Cleared', 'Your scan logs have been purged.');
            } catch (err: any) {
              Alert.alert('Error', err.message || 'Failed to clear history.');
            }
          }
        }
      ]
    );
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      '⚠️ Delete Account',
      'CRITICAL: This will permanently delete your user profile, scan histories, preferences, and details from EcoSaur. This action is irreversible.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete Permanently',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deleteAccount();
              await supabase.auth.signOut();
              router.replace('/');
              Alert.alert('Account Deleted', 'Your profile and logs have been wiped from the database.');
            } catch (err: any) {
              Alert.alert('Error', err.message || 'Failed to delete account data.');
            }
          }
        }
      ]
    );
  };

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.bg, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={theme.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.bg }} contentContainerStyle={{ padding: 20, paddingBottom: 60 }}>
      
      {/* Account Info Header */}
      <View style={{
        backgroundColor: theme.card,
        borderWidth: 1,
        borderColor: theme.border,
        borderRadius: 24,
        padding: 20,
        alignItems: 'center',
        marginBottom: 24,
      }}>
        <Text style={{ fontSize: 50, marginBottom: 8 }}>🦕</Text>
        <Text style={{ fontSize: 18, fontWeight: '800', color: theme.text }}>
          {email}
        </Text>
        <Text style={{ fontSize: 12, color: theme.muted, marginTop: 4 }}>
          EcoSaur wellness community member
        </Text>
      </View>

      {/* Focus Modes Selection */}
      <Text style={{ fontSize: 12, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 12, letterSpacing: 0.5 }}>
        Personalized Dietary Focus Mode
      </Text>
      
      <View style={{ gap: 10, marginBottom: 24 }}>
        {HEALTH_MODES.map((mode) => {
          const isSelected = selectedMode === mode.id;
          const isSaving = savingMode === mode.id;

          return (
            <TouchableOpacity
              key={mode.id}
              onPress={() => handleSelectMode(mode.id)}
              disabled={!!savingMode}
              style={{
                backgroundColor: isSelected ? theme.accentSoft : theme.card,
                borderWidth: 1.5,
                borderColor: isSelected ? theme.primary : theme.border,
                borderRadius: 18,
                padding: 16,
                flexDirection: 'row',
                alignItems: 'center',
              }}
            >
              <Text style={{ fontSize: 26, marginRight: 16 }}>{mode.icon}</Text>
              
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 14, fontWeight: '700', color: theme.text }}>
                  {mode.label}
                </Text>
                <Text style={{ fontSize: 11, color: theme.muted, marginTop: 2, lineHeight: 14 }}>
                  {mode.desc}
                </Text>
              </View>
              
              {isSaving ? (
                <ActivityIndicator size="small" color={theme.primary} />
              ) : isSelected ? (
                <Text style={{ fontSize: 18, color: theme.primary, fontWeight: 'bold' }}>✓</Text>
              ) : null}
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Privacy GDPR Section */}
      <View style={{
        backgroundColor: theme.card,
        borderWidth: 1,
        borderColor: theme.border,
        borderRadius: 20,
        padding: 20,
        marginBottom: 24,
        gap: 12
      }}>
        <Text style={{ fontSize: 12, fontWeight: '700', color: theme.text, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          🛡️ Privacy & Account Management
        </Text>
        
        <TouchableOpacity
          onPress={handleDeleteHistory}
          style={{
            backgroundColor: theme.bg,
            borderWidth: 1,
            borderColor: theme.border,
            borderRadius: 14,
            height: 44,
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          <Text style={{ color: theme.text, fontWeight: '600', fontSize: 13 }}>
            🗑️ Clear Scan History
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={handleDeleteAccount}
          style={{
            backgroundColor: 'rgba(255, 69, 58, 0.05)',
            borderWidth: 1,
            borderColor: 'rgba(255, 69, 58, 0.2)',
            borderRadius: 14,
            height: 44,
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          <Text style={{ color: theme.error, fontWeight: '700', fontSize: 13 }}>
            ⚠️ Permanently Delete Account
          </Text>
        </TouchableOpacity>
      </View>

      {/* Logout Action */}
      <TouchableOpacity
        onPress={handleSignOut}
        style={{
          borderWidth: 1.5,
          borderColor: theme.error,
          borderRadius: 14,
          height: 48,
          justifyContent: 'center',
          alignItems: 'center',
          backgroundColor: 'transparent',
        }}
      >
        <Text style={{ color: theme.error, fontWeight: '700', fontSize: 14 }}>
          🚪 Sign Out of Account
        </Text>
      </TouchableOpacity>

    </ScrollView>
  );
}
