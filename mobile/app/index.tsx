import React, { useState } from 'react';
import { View, Text, TouchableOpacity, useColorScheme, ScrollView, Animated, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { THEME } from '../theme';
import { api } from '../services/api';

export default function WelcomeScreen() {
  const colorScheme = useColorScheme() ?? 'dark';
  const theme = THEME[colorScheme as 'light' | 'dark'];
  const router = useRouter();
  
  const [currentStep, setCurrentStep] = useState(0);
  const totalSteps = 5;
  const [selectedMode, setSelectedMode] = useState('General');
  const [savingMode, setSavingMode] = useState(false);

  const handleNext = async () => {
    if (currentStep === 3) {
      setSavingMode(true);
      try {
        await api.updateUserPreferences(selectedMode);
      } catch (err) {
        console.warn('Failed to save user preference focus mode:', err);
      } finally {
        setSavingMode(false);
      }
    }
    
    if (currentStep < totalSteps - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      router.push('/scan');
    }
  };

  const handleSkip = () => {
    router.push('/scan');
  };

  const renderDots = () => {
    return (
      <View style={{ flexDirection: 'row', gap: 8, justifyContent: 'center', marginVertical: 24 }}>
        {Array.from({ length: totalSteps }).map((_, idx) => (
          <View
            key={idx}
            style={{
              width: idx === currentStep ? 24 : 8,
              height: 8,
              borderRadius: 4,
              backgroundColor: idx === currentStep ? theme.primary : theme.border,
            }}
          />
        ))}
      </View>
    );
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.bg }}>
      <StatusBar style={colorScheme === 'dark' ? 'light' : 'dark'} />
      <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'space-between', padding: 24 }}>
        
        {/* Top Header */}
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', height: 40 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Text style={{ fontSize: 20 }}>🦕</Text>
            <Text style={{ fontSize: 16, fontWeight: '700', color: theme.text, letterSpacing: -0.2 }}>EcoSaur</Text>
          </View>
          {currentStep < totalSteps - 1 && (
            <TouchableOpacity onPress={handleSkip}>
              <Text style={{ color: theme.muted, fontSize: 14, fontWeight: '500' }}>Skip</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Step Content */}
        <View style={{ flex: 1, justifyContent: 'center', marginVertical: 32 }}>
          {currentStep === 0 && (
            <View style={{ alignItems: 'center' }}>
              <View style={{
                width: 100,
                height: 100,
                borderRadius: 50,
                backgroundColor: theme.accentSoft,
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 28,
              }}>
                <Text style={{ fontSize: 56 }}>🦕</Text>
              </View>
              <Text style={{
                fontSize: 32,
                fontWeight: '800',
                color: theme.text,
                textAlign: 'center',
                marginBottom: 12,
                letterSpacing: -0.5,
                lineHeight: 38
              }}>
                Meet EcoSaur,{"\n"}your friendly shopping partner.
              </Text>
              <Text style={{
                fontSize: 15,
                color: theme.muted,
                textAlign: 'center',
                paddingHorizontal: 16,
                lineHeight: 22
              }}>
                EcoSaur decodes packaged food labels transparently and helps you find healthier homemade swaps without the fearmongering.
              </Text>
            </View>
          )}

          {currentStep === 1 && (
            <View style={{ alignItems: 'center' }}>
              {/* Simulated Scanner Mockup */}
              <View style={{
                width: '100%',
                height: 180,
                backgroundColor: theme.card,
                borderRadius: 24,
                borderWidth: 1,
                borderColor: theme.border,
                padding: 16,
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                overflow: 'hidden',
                marginBottom: 28
              }}>
                {/* Simulated ingredients label */}
                <View style={{ width: '90%', opacity: 0.4 }}>
                  <Text style={{ color: theme.text, fontSize: 11, fontFamily: 'monospace' }}>
                    INGREDIENTS: Sugar, Hydrogenated Palm Oil, High Fructose Corn Syrup, Disodium Guanylate, Preservatives (224), Tartrazine...
                  </Text>
                </View>
                {/* Viewfinder scanner box */}
                <View style={{
                  position: 'absolute',
                  width: '80%',
                  height: 100,
                  borderWidth: 2,
                  borderColor: theme.primary,
                  borderRadius: 12,
                  justifyContent: 'center',
                  alignItems: 'center'
                }}>
                  {/* Laser line */}
                  <View style={{
                    width: '95%',
                    height: 2,
                    backgroundColor: theme.primary,
                    shadowColor: theme.primary,
                    shadowOpacity: 0.8,
                    shadowRadius: 4,
                  }} />
                </View>
              </View>
              <Text style={{ fontSize: 13, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 8, letterSpacing: 0.5 }}>
                Step 1: Snap or Type
              </Text>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.text, textAlign: 'center', marginBottom: 10 }}>
                Analyze in Seconds
              </Text>
              <Text style={{ fontSize: 15, color: theme.muted, textAlign: 'center', paddingHorizontal: 20, lineHeight: 22 }}>
                Take a photo of any ingredient list or scan the barcode. EcoSaur uses rule-based logic to process facts instantly.
              </Text>
            </View>
          )}

          {currentStep === 2 && (
            <View style={{ alignItems: 'center' }}>
              {/* Simulated Swap Comparison Mockup */}
              <View style={{
                width: '100%',
                backgroundColor: theme.card,
                borderRadius: 24,
                borderWidth: 1,
                borderColor: theme.border,
                padding: 16,
                marginBottom: 28,
              }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <Text style={{ color: theme.text, fontWeight: '700', fontSize: 13 }}>Commercial Soda</Text>
                  <Text style={{ color: theme.error, fontWeight: '700', fontSize: 12 }}>High Sugar</Text>
                </View>
                
                {/* Arrow or Swap representation */}
                <View style={{ height: 1, backgroundColor: theme.border, marginVertical: 8 }} />
                
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
                  <Text style={{ color: theme.primary, fontWeight: '700', fontSize: 14 }}>💡 Fresh Buttermilk</Text>
                  <Text style={{ color: theme.success, fontWeight: '700', fontSize: 12 }}>-95% Sugar Swap</Text>
                </View>
              </View>
              <Text style={{ fontSize: 13, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 8, letterSpacing: 0.5 }}>
                Step 2: Better Alternatives
              </Text>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.text, textAlign: 'center', marginBottom: 10 }}>
                Craving-Matched Swaps
              </Text>
              <Text style={{ fontSize: 15, color: theme.muted, textAlign: 'center', paddingHorizontal: 20, lineHeight: 22 }}>
                Instead of empty calories, we suggest traditional, accessible Indian snacks and drinks matching the craving profile.
              </Text>
            </View>
          )}

          {currentStep === 3 && (
            <View style={{ alignItems: 'center', width: '100%' }}>
              <View style={{
                width: 70,
                height: 70,
                borderRadius: 35,
                backgroundColor: theme.accentSoft,
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 16,
              }}>
                <Text style={{ fontSize: 36 }}>🎯</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.text, textAlign: 'center', marginBottom: 8, letterSpacing: -0.4 }}>
                Select your wellness focus
              </Text>
              <Text style={{ fontSize: 14, color: theme.muted, textAlign: 'center', marginBottom: 24, paddingHorizontal: 20, lineHeight: 20 }}>
                Let's tailor EcoSaur to your lifestyle. We will adapt ingredient highlights and swap suggestions to match your personal focus.
              </Text>
              
              <View style={{ width: '100%', gap: 12 }}>
                {[
                  { mode: 'General', icon: '🌿', title: 'General Wellness', desc: 'A well-rounded, balanced daily wellness approach' },
                  { mode: 'Gym/Fitness', icon: '💪', title: 'Fitness & Gym', desc: 'Prioritizes clean protein content and active recovery' },
                  { mode: 'Weight Loss', icon: '🏃', title: 'Weight Management', desc: 'Highlights lighter, lower-calorie options to support your goals' },
                  { mode: 'Diabetic Friendly', icon: '🩸', title: 'Diabetic Friendly', desc: 'Monitors added sugars, artificial sweeteners, and glycemic loads' },
                  { mode: 'Child Friendly', icon: '👶', title: 'Child Friendly', desc: 'Flags artificial dyes, synthetic colors, and heavy preservatives' },
                ].map((item) => {
                  const isSelected = selectedMode === item.mode;
                  return (
                    <TouchableOpacity
                      key={item.mode}
                      onPress={() => setSelectedMode(item.mode)}
                      style={{
                        backgroundColor: isSelected ? theme.accentSoft : theme.card,
                        borderWidth: 1,
                        borderColor: isSelected ? theme.primary : theme.border,
                        borderRadius: 16,
                        paddingVertical: 14,
                        paddingHorizontal: 18,
                        flexDirection: 'row',
                        alignItems: 'center',
                        gap: 14,
                      }}
                    >
                      <Text style={{ fontSize: 24 }}>{item.icon}</Text>
                      <View style={{ flex: 1 }}>
                        <Text style={{ fontSize: 15, fontWeight: '700', color: isSelected ? theme.primary : theme.text }}>
                          {item.title}
                        </Text>
                        <Text style={{ fontSize: 12, color: theme.muted, marginTop: 2, lineHeight: 16 }}>
                          {item.desc}
                        </Text>
                      </View>
                      <View style={{
                        width: 20,
                        height: 20,
                        borderRadius: 10,
                        borderWidth: 1.5,
                        borderColor: isSelected ? theme.primary : theme.border,
                        justifyContent: 'center',
                        alignItems: 'center',
                      }}>
                        {isSelected && (
                          <View style={{
                            width: 10,
                            height: 10,
                            borderRadius: 5,
                            backgroundColor: theme.primary,
                          }} />
                        )}
                      </View>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          )}

          {currentStep === 4 && (
            <View style={{ alignItems: 'center' }}>
              <View style={{
                width: 90,
                height: 90,
                borderRadius: 45,
                backgroundColor: theme.accentSoft,
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 28,
              }}>
                <Text style={{ fontSize: 50 }}>🦖</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.text, textAlign: 'center', marginBottom: 12 }}>
                Ready to shop smarter?
              </Text>
              <Text style={{ fontSize: 15, color: theme.muted, textAlign: 'center', paddingHorizontal: 20, lineHeight: 22 }}>
                No anxiety, no brand bashing. Just honest, clear explanations and healthy swaps matching your mode: <Text style={{ fontWeight: 'bold', color: theme.primary }}>{selectedMode}</Text>.
              </Text>
            </View>
          )}
        </View>

        {/* Bottom Actions and Dots */}
        <View style={{ marginBottom: 10 }}>
          {renderDots()}

          <View style={{ gap: 12 }}>
            <TouchableOpacity
              onPress={handleNext}
              style={{
                backgroundColor: theme.primary,
                paddingVertical: 16,
                borderRadius: 16,
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Text style={{
                color: '#FFFFFF',
                fontSize: 16,
                fontWeight: '700'
              }}>
                {currentStep === totalSteps - 1 ? '🚀 Start Scanning' : 'Continue'}
              </Text>
            </TouchableOpacity>

            {currentStep === totalSteps - 1 && (
              <TouchableOpacity
                onPress={() => {
                  router.push('/scan');
                }}
                style={{
                  backgroundColor: theme.card,
                  paddingVertical: 14,
                  borderRadius: 16,
                  alignItems: 'center',
                  borderWidth: 1,
                  borderColor: theme.border
                }}
              >
                <Text style={{
                  color: theme.text,
                  fontSize: 15,
                  fontWeight: '600'
                }}>
                  🏷️ Enter Product Barcode
                </Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

