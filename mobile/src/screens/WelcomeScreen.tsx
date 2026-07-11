import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, useColorScheme, ScrollView, ActivityIndicator, StyleSheet, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { THEME } from '../theme';
import { api } from '../services/api';
import { supabase } from '../services/supabase';

interface HistoryItem {
  id: string;
  date: string;
  corrected_text: string;
  score: number;
  grade: string;
  explanation: string;
  alternative: {
    name: string;
    recipe: string;
    prep_time_mins: number;
    approx_cost_inr: number;
  };
  breakdown: Array<{ reason: string; impact: number }>;
  confidence?: {
    ocr_score: number;
    ocr_level: string;
    match_score: number;
    match_level: string;
  };
}

export default function WelcomeScreen() {
  const colorScheme = useColorScheme() ?? 'dark';
  const theme = THEME[colorScheme as 'light' | 'dark'];
  const router = useRouter();
  
  const [currentStep, setCurrentStep] = useState(0);
  const totalSteps = 5;
  const [selectedMode, setSelectedMode] = useState('General');
  const [savingMode, setSavingMode] = useState(false);

  // Dashboard & History States
  const [isNewUser, setIsNewUser] = useState(true);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    checkUserOnboarding();
  }, []);

  const checkUserOnboarding = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setCheckingAuth(false);
        return;
      }
      
      // Fetch user preference to see if onboarded
      const prefs = await api.getUserPreferences();
      if (prefs && prefs.health_mode) {
        setSelectedMode(prefs.health_mode);
        setIsNewUser(false);
        setCurrentStep(5); // Go directly to Dashboard step
        fetchHistory();
      } else {
        setCheckingAuth(false);
      }
    } catch (err) {
      setCheckingAuth(false);
    }
  };

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await api.getScanHistory(10);
      setHistory(data);
    } catch (err) {
      console.warn('Failed to load history list:', err);
    } finally {
      setLoadingHistory(false);
      setCheckingAuth(false);
    }
  };

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
      setIsNewUser(false);
      setCurrentStep(5); // Transition to Dashboard
      fetchHistory();
    }
  };

  const handleSkip = () => {
    setIsNewUser(false);
    setCurrentStep(5);
    fetchHistory();
  };

  const handleHistoryPress = (item: HistoryItem) => {
    // Reconstruct Results screen compatible payload
    const scoreVal = item.score;
    const grade = item.grade;
    
    const resultsPayload = {
      scorecard: {
        nova_group: grade === 'S' || grade === 'A' ? 1 : grade === 'B' ? 2 : grade === 'C' ? 3 : 4,
        additive_density: scoreVal >= 85 ? 'Low' : scoreVal >= 65 ? 'Medium' : 'High',
        sugar_load: scoreVal >= 85 ? 'Low' : scoreVal >= 70 ? 'Moderate' : 'High',
        sodium_load: 'Low',
        transparency_index: 'High',
        protein_quality: 'Standard',
        fiber_quality: 'Standard',
      },
      explanation: item.explanation,
      alternative: item.alternative,
      breakdown: item.breakdown,
      corrected_text: item.corrected_text,
      confidence: item.confidence || {
        ocr_score: 95,
        ocr_level: 'High',
        match_score: 95,
        match_level: 'High'
      }
    };

    router.push({
      pathname: '/results',
      params: {
        resultsPayload: JSON.stringify(resultsPayload),
        productName: item.alternative?.name ? item.alternative.name.replace('Homemade ', '').replace('Alternative ', '') : 'Scanned Snack'
      }
    });
  };

  const renderDots = () => {
    if (currentStep >= totalSteps) return null;
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

  if (checkingAuth) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.bg, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={theme.primary} />
      </View>
    );
  }

  // DASHBOARD LAYOUT (ONBOARDED USERS)
  if (currentStep >= 5) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: theme.bg }}>
        <StatusBar style={colorScheme === 'dark' ? 'light' : 'dark'} />
        
        {/* Dashboard Header */}
        <View style={{
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingHorizontal: 24,
          paddingVertical: 14,
          borderBottomWidth: 1,
          borderBottomColor: theme.border,
        }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <Text style={{ fontSize: 24 }}>🦕</Text>
            <View>
              <Text style={{ fontSize: 16, fontWeight: '800', color: theme.text }}>EcoSaur</Text>
              <Text style={{ fontSize: 11, color: theme.primary, fontWeight: '600' }}>
                🎯 Focus: {selectedMode}
              </Text>
            </View>
          </View>
          
          <TouchableOpacity 
            onPress={() => router.push('/profile')}
            style={{
              backgroundColor: theme.card,
              padding: 8,
              borderRadius: 12,
              borderWidth: 1,
              borderColor: theme.border,
            }}
          >
            <Text style={{ fontSize: 12, color: theme.text, fontWeight: '600' }}>⚙️ Profile</Text>
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 40 }}>
          
          {/* Main Action Banner */}
          <View style={{
            backgroundColor: theme.card,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: theme.border,
            padding: 24,
            alignItems: 'center',
            marginBottom: 28,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 6 },
            shadowOpacity: 0.1,
            shadowRadius: 12,
            elevation: 4,
          }}>
            <Text style={{ fontSize: 44, marginBottom: 8 }}>📷</Text>
            <Text style={{ fontSize: 20, fontWeight: '800', color: theme.text, letterSpacing: -0.3, textAlign: 'center' }}>
              Check Food Ingredients
            </Text>
            <Text style={{ fontSize: 13, color: theme.muted, textAlign: 'center', marginTop: 6, marginBottom: 20, paddingHorizontal: 16, lineHeight: 18 }}>
              Snap an ingredients label or scan a barcode to see grading, additives, and healthy swaps.
            </Text>
            
            <TouchableOpacity
              onPress={() => router.push('/scan')}
              style={{
                backgroundColor: theme.primary,
                width: '100%',
                paddingVertical: 14,
                borderRadius: 14,
                alignItems: 'center',
              }}
            >
              <Text style={{ color: '#FFFFFF', fontWeight: '800', fontSize: 14 }}>
                🚀 Launch Scanner
              </Text>
            </TouchableOpacity>
          </View>

          {/* Scan History Title */}
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <Text style={{ fontSize: 12, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              📜 Recent Scans ({history.length})
            </Text>
            {history.length > 0 && (
              <TouchableOpacity onPress={fetchHistory}>
                <Text style={{ fontSize: 11, color: theme.muted }}>Refresh</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* History List or Empty View */}
          {loadingHistory ? (
            <ActivityIndicator size="small" color={theme.primary} style={{ marginVertical: 20 }} />
          ) : history.length === 0 ? (
            <View style={{
              backgroundColor: theme.card,
              borderRadius: 24,
              padding: 24,
              borderWidth: 1,
              borderColor: theme.border,
            }}>
              <View style={{ alignItems: 'center', marginBottom: 20 }}>
                <Text style={{ fontSize: 40, marginBottom: 8 }}>🥗</Text>
                <Text style={{ color: theme.text, fontWeight: '800', fontSize: 15 }}>No scans logged yet</Text>
                <Text style={{ color: theme.muted, fontSize: 12, textAlign: 'center', marginTop: 4, lineHeight: 16 }}>
                  Once you analyze product labels, your scan logs and diagnostic insights will appear here.
                </Text>
              </View>

              <View style={{ borderTopWidth: 1, borderTopColor: theme.border, paddingTop: 16, gap: 14 }}>
                <Text style={{ fontSize: 11, fontWeight: '800', color: theme.primary, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>
                  How to get started
                </Text>

                <View style={{ flexDirection: 'row', gap: 12, alignItems: 'flex-start' }}>
                  <View style={{ width: 28, height: 28, borderRadius: 14, backgroundColor: theme.accentSoft, alignItems: 'center', justifyContent: 'center', marginTop: 2 }}>
                    <Text style={{ fontSize: 14 }}>📷</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={{ color: theme.text, fontSize: 13, fontWeight: '700' }}>1. Capture Ingredients Label</Text>
                    <Text style={{ color: theme.muted, fontSize: 11, marginTop: 2, lineHeight: 14 }}>
                      Tap the scanner button and position the camera over the back-of-pack ingredients table.
                    </Text>
                  </View>
                </View>

                <View style={{ flexDirection: 'row', gap: 12, alignItems: 'flex-start' }}>
                  <View style={{ width: 28, height: 28, borderRadius: 14, backgroundColor: theme.accentSoft, alignItems: 'center', justifyContent: 'center', marginTop: 2 }}>
                    <Text style={{ fontSize: 14 }}>✏️</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={{ color: theme.text, fontSize: 13, fontWeight: '700' }}>2. Review & Spellcheck</Text>
                    <Text style={{ color: theme.muted, fontSize: 11, marginTop: 2, lineHeight: 14 }}>
                      Correct any blurry or misspelled words with spelling suggestions in the visual feedback box.
                    </Text>
                  </View>
                </View>

                <View style={{ flexDirection: 'row', gap: 12, alignItems: 'flex-start' }}>
                  <View style={{ width: 28, height: 28, borderRadius: 14, backgroundColor: theme.accentSoft, alignItems: 'center', justifyContent: 'center', marginTop: 2 }}>
                    <Text style={{ fontSize: 14 }}>🌿</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={{ color: theme.text, fontSize: 13, fontWeight: '700' }}>3. Browse Swaps & Insights</Text>
                    <Text style={{ color: theme.muted, fontSize: 11, marginTop: 2, lineHeight: 14 }}>
                      Review chemical alerts and swipe to find premium regional Indian food alternatives.
                    </Text>
                  </View>
                </View>
              </View>
            </View>
          ) : (
            <View style={{ gap: 10 }}>
              {history.map((item) => {
                // Color mapping for grades
                const isPositive = item.grade === 'S' || item.grade === 'A';
                const isModerate = item.grade === 'B' || item.grade === 'C';
                const gradeColor = isPositive ? theme.success : isModerate ? theme.warning : theme.error;

                const formattedDate = item.date ? new Date(item.date).toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric'
                }) : 'Recently';

                return (
                  <TouchableOpacity
                    key={item.id}
                    onPress={() => handleHistoryPress(item)}
                    style={{
                      backgroundColor: theme.card,
                      borderWidth: 1,
                      borderColor: theme.border,
                      borderRadius: 16,
                      padding: 16,
                      flexDirection: 'row',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <View style={{ flex: 1, marginRight: 12 }}>
                      <Text style={{ fontSize: 14, fontWeight: '800', color: theme.text }} numberOfLines={1}>
                        {item.alternative?.name ? item.alternative.name.replace('Homemade ', '') : 'Scanned Snack'}
                      </Text>
                      <Text style={{ fontSize: 11, color: theme.muted, marginTop: 4 }}>
                        📅 {formattedDate} • {item.breakdown?.length || 0} alerts
                      </Text>
                    </View>
                    
                    <View style={{
                      backgroundColor: theme.bg,
                      borderRadius: 12,
                      width: 44,
                      height: 44,
                      justifyContent: 'center',
                      alignItems: 'center',
                      borderWidth: 1,
                      borderColor: theme.border,
                    }}>
                      <Text style={{ fontSize: 15, fontWeight: '900', color: gradeColor }}>
                        {item.grade}
                      </Text>
                      <Text style={{ fontSize: 9, color: theme.muted, marginTop: -2 }}>
                        {item.score}
                      </Text>
                    </View>
                  </TouchableOpacity>
                );
              })}
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    );
  }

  // ONBOARDING WIZARD STEPS
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
                <View style={{ width: '90%', opacity: 0.4 }}>
                  <Text style={{ color: theme.text, fontSize: 11, fontFamily: 'monospace' }}>
                    INGREDIENTS: Sugar, Hydrogenated Palm Oil, High Fructose Corn Syrup, Disodium Guanylate, Preservatives (224), Tartrazine...
                  </Text>
                </View>
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

        {/* Bottom Actions */}
        <View style={{ marginBottom: 10 }}>
          {renderDots()}

          <View style={{ gap: 12 }}>
            <TouchableOpacity
              onPress={handleNext}
              disabled={savingMode}
              style={{
                backgroundColor: theme.primary,
                paddingVertical: 16,
                borderRadius: 16,
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {savingMode ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={{
                  color: '#FFFFFF',
                  fontSize: 16,
                  fontWeight: '700'
                }}>
                  {currentStep === totalSteps - 1 ? '🚀 Start Scanning' : 'Continue'}
                </Text>
              )}
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
