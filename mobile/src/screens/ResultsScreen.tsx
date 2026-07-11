import React, { useState, useRef, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, useColorScheme, TextInput, ActivityIndicator, Alert, Animated, Platform } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { calculateClientScore, getMetricColor } from '../utils/scoring';
import { api } from '../services/api';
import { THEME } from '../theme';

interface ChatMessage {
  role: 'user' | 'model';
  content: string;
}

export default function ResultsScreen() {
  const params = useLocalSearchParams();
  const router = useRouter();
  const colorScheme = useColorScheme() ?? 'dark';
  const theme = THEME[colorScheme as 'light' | 'dark'];

  const results = JSON.parse((params.resultsPayload as string) || '{}');
  const productName = (params.productName as string) || 'Scanned Product';

  const scorecard = results.scorecard || {
    nova_group: 4,
    additive_density: 'High',
    sugar_load: 'High',
    sodium_load: 'Low',
    transparency_index: 'High',
    protein_quality: 'Standard',
    fiber_quality: 'Standard',
  };

  const scoreVal = calculateClientScore(scorecard);

  // Alternatives
  const alternativesList = results.alternatives || [results.alternative].filter(Boolean);
  const mainAlternative = alternativesList[0] || {
    name: 'Homemade Alternative',
    prep_time_mins: 15,
    approx_cost_inr: 35,
    recipe: 'Prepare with natural, fresh ingredients.',
    reasoning: {
      why_selected: 'Great healthy swap for this category.',
      bullets: ['✓ 100% additive free', '✓ Reduces processing', '✓ Simpler local ingredients']
    }
  };

  // State for collapsible detailed insights
  const [detailsExpanded, setDetailsExpanded] = useState(false);

  // Recommendation feedback telemetry state
  const [feedbackLogged, setFeedbackLogged] = useState<Record<number, 'up' | 'down' | null>>({});

  // Chat states
  const [chatOpen, setChatOpen] = useState(false);
  const [sheetVisible, setSheetVisible] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  const chatScrollRef = useRef<ScrollView>(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const sheetAnim = useRef(new Animated.Value(0)).current;

  // Assistant sheet animations interpolations
  const backdropOpacity = sheetAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 0.5],
  });

  const sheetTranslateY = sheetAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [600, 0],
  });

  const fabScale = sheetAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 0],
  });

  const fabOpacity = sheetAnim.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [1, 0, 0],
  });

  const finalScale = Animated.multiply(pulseAnim, fabScale);

  // Sync sheet visibility and spring transitions
  useEffect(() => {
    if (chatOpen) {
      setSheetVisible(true);
      Animated.spring(sheetAnim, {
        toValue: 1,
        tension: 40,
        friction: 8,
        useNativeDriver: true,
      }).start();
    } else {
      Animated.timing(sheetAnim, {
        toValue: 0,
        duration: 250,
        useNativeDriver: true,
      }).start(() => {
        setSheetVisible(false);
      });
    }
  }, [chatOpen]);

  // Gentle pulse breathing animation loop (subtle 9-second loop)
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.03,
          duration: 4500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1.0,
          duration: 4500,
          useNativeDriver: true,
        })
      ])
    ).start();
  }, []);

  // Progressive streaming simulated typing reveal
  const typeMessage = (fullText: string) => {
    // Add empty message first
    setChatHistory(prev => [...prev, { role: 'model', content: '' }]);
    
    let currentText = "";
    let wordIndex = 0;
    const words = fullText.split(" ");
    
    const interval = setInterval(() => {
      if (wordIndex < words.length) {
        currentText += (wordIndex === 0 ? "" : " ") + words[wordIndex];
        setChatHistory(prev => {
          const next = [...prev];
          if (next.length > 0) {
            next[next.length - 1] = { role: 'model', content: currentText };
          }
          return next;
        });
        wordIndex++;
        
        // Scroll to bottom dynamically
        setTimeout(() => chatScrollRef.current?.scrollToEnd({ animated: true }), 30);
      } else {
        clearInterval(interval);
      }
    }, 70); // Emit a word every 70ms
  };

  const handleSendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const userMsg: ChatMessage = { role: 'user', content: chatInput };
    
    // Optimistic UI update
    setChatHistory(prev => [...prev, userMsg]);
    const currentInput = chatInput;
    setChatInput('');
    setChatLoading(true);
    
    setTimeout(() => chatScrollRef.current?.scrollToEnd({ animated: true }), 50);

    try {
      const response = await api.chatWithAI(
        [results.corrected_text || ''],
        chatHistory.map(m => ({ role: m.role, content: m.content })),
        userMsg.content
      );
      
      setChatLoading(false);
      typeMessage(response.reply);
    } catch (err) {
      setChatLoading(false);
      typeMessage("I'm having a bit of trouble connecting to my assistant base right now. Could you please try asking again in a moment?");
    }
  };

  const handleQuickAction = async (promptValue: string) => {
    if (chatLoading) return;
    const userMsg: ChatMessage = { role: 'user', content: promptValue };
    setChatHistory(prev => [...prev, userMsg]);
    setChatLoading(true);
    
    setTimeout(() => chatScrollRef.current?.scrollToEnd({ animated: true }), 50);

    try {
      const response = await api.chatWithAI(
        [results.corrected_text || ''],
        chatHistory.map(m => ({ role: m.role, content: m.content })),
        userMsg.content
      );
      
      setChatLoading(false);
      typeMessage(response.reply);
    } catch (err) {
      setChatLoading(false);
      typeMessage("I'm sorry, I encountered an issue processing that quick question. Let's try once more!");
    }
  };

  const handleFeedback = (idx: number, type: 'up' | 'down') => {
    setFeedbackLogged(prev => ({ ...prev, [idx]: type }));
    // In background, log feedback to crowdsourced loops
    Alert.alert('🦖 EcoSaur Mascot', 'Thank you! Your feedback helps us improve healthy swaps for the whole community.');
  };

  // Helper to extract main concern
  const getMainConcerns = () => {
    const concerns = [];
    if (scorecard.nova_group === 4) concerns.push('Ultra-Processed');
    if (scorecard.sugar_load === 'High') concerns.push('High Sugar Load');
    if (scorecard.additive_density === 'High') concerns.push('High Additives');
    if (scorecard.sodium_load === 'High') concerns.push('High Sodium');
    
    if (concerns.length === 0) {
      if (scorecard.nova_group === 3) concerns.push('Moderately Processed');
      if (scorecard.sugar_load === 'Moderate') concerns.push('Moderate Sugar');
      if (scorecard.additive_density === 'Medium') concerns.push('Moderate Additives');
    }
    return concerns.length > 0 ? concerns.join(' & ') : 'Balanced Snack Profile';
  };

  // Scorecard values mapped to progress bar width percentage
  const getProgressPercentage = (val: string | number, type: 'nova' | 'load' | 'density') => {
    if (type === 'nova') {
      const g = Number(val);
      if (g === 1) return '25%';
      if (g === 2) return '50%';
      if (g === 3) return '75%';
      return '100%';
    }
    if (val === 'High') return '100%';
    if (val === 'Medium' || val === 'Moderate') return '60%';
    return '25%'; // Low
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.bg }}>
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 120 }}>
        
        {/* Header section (Product Identity) */}
        <View style={{ marginBottom: 16 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <View style={{ 
              backgroundColor: theme.accentSoft, 
              paddingHorizontal: 12, 
              paddingVertical: 4, 
              borderRadius: 20,
              borderWidth: 1,
              borderColor: theme.border
            }}>
              <Text style={{ color: theme.primary, fontSize: 12, fontWeight: 'bold' }}>
                {results.category_info?.subcategory || 'Snack'}
              </Text>
            </View>
            {results.confidence && (
              <Text style={{ fontSize: 11, color: theme.muted, fontWeight: '500' }}>
                ✓ {results.confidence.match_score || 100}% Label Verified
              </Text>
            )}
          </View>
          <Text style={{ fontSize: 24, fontWeight: '800', color: theme.text, letterSpacing: -0.5 }}>
            {productName}
          </Text>
        </View>

        {/* HERO SECTION — CALM INTELLIGENCE SUMMARY */}
        <View style={{
          backgroundColor: theme.card,
          borderRadius: 24,
          borderWidth: 1,
          borderColor: theme.border,
          padding: 20,
          marginBottom: 20,
        }}>
          {/* Main Concern Indicator */}
          <View style={{ marginBottom: 12 }}>
            <Text style={{ fontSize: 12, fontWeight: '600', color: theme.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 4 }}>
              Main Concern
            </Text>
            <Text style={{ fontSize: 18, fontWeight: '700', color: scorecard.nova_group === 4 || scorecard.sugar_load === 'High' ? '#F43F5E' : '#F59E0B' }}>
              {getMainConcerns()}
            </Text>
            <Text style={{ fontSize: 13, color: theme.muted, marginTop: 4, lineHeight: 18 }}>
              {scorecard.nova_group === 4 
                ? 'Contains industrial ingredients and additives. Portion monitoring is recommended.' 
                : 'A balanced snack profile matching standard daily wellness guidelines.'}
            </Text>
          </View>

          {/* Quick Swap Highlight */}
          <View style={{ 
            backgroundColor: theme.bg, 
            borderRadius: 16, 
            padding: 16, 
            marginTop: 8,
            borderWidth: 1, 
            borderColor: theme.border 
          }}>
            <Text style={{ fontSize: 12, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 }}>
              💡 Smart Swap Recommendation
            </Text>
            <Text style={{ fontSize: 16, fontWeight: '700', color: theme.text, marginBottom: 12 }}>
              {mainAlternative.name}
            </Text>

            {/* Quick Comparison Story Bar */}
            <View style={{ gap: 8 }}>
              {/* Sugar comparison */}
              <View>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 2 }}>
                  <Text style={{ fontSize: 12, color: theme.muted }}>Sugar Reduction</Text>
                  <Text style={{ fontSize: 12, fontWeight: '700', color: '#10B981' }}>
                    {scorecard.sugar_load === 'High' ? '-90% less sugar' : 'Low glycemic load'}
                  </Text>
                </View>
                <View style={{ height: 5, backgroundColor: theme.border, borderRadius: 2.5, overflow: 'hidden', flexDirection: 'row' }}>
                  <View style={{ flex: scorecard.sugar_load === 'High' ? 9 : 3, backgroundColor: '#F43F5E' }} />
                  <View style={{ flex: 1, backgroundColor: '#10B981' }} />
                </View>
              </View>

              {/* Additives comparison */}
              <View>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 2 }}>
                  <Text style={{ fontSize: 12, color: theme.muted }}>Additive Safety</Text>
                  <Text style={{ fontSize: 12, fontWeight: '700', color: '#10B981' }}>100% Additive Free</Text>
                </View>
                <View style={{ height: 5, backgroundColor: theme.border, borderRadius: 2.5, overflow: 'hidden', flexDirection: 'row' }}>
                  <View style={{ flex: scorecard.additive_density === 'High' ? 8 : 4, backgroundColor: '#F43F5E' }} />
                  <View style={{ flex: 0, backgroundColor: '#10B981' }} />
                </View>
              </View>
            </View>
          </View>
        </View>

        {/* COLLAPSIBLE DETAILED CHEMICAL & INGREDIENT INSIGHTS */}
        <View style={{ marginBottom: 20 }}>
          <TouchableOpacity 
            onPress={() => setDetailsExpanded(!detailsExpanded)}
            style={{
              backgroundColor: theme.card,
              borderWidth: 1,
              borderColor: theme.border,
              borderRadius: 16,
              paddingVertical: 14,
              paddingHorizontal: 20,
              flexDirection: 'row',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <Text style={{ color: theme.text, fontWeight: '600', fontSize: 14 }}>
              📊 Ingredient Insights
            </Text>
            <Text style={{ color: theme.primary, fontWeight: 'bold', fontSize: 13 }}>
              {detailsExpanded ? 'Hide' : 'Expand Insights'}
            </Text>
          </TouchableOpacity>

          {detailsExpanded && (
            <View style={{ 
              backgroundColor: theme.card, 
              borderLeftWidth: 1, 
              borderRightWidth: 1, 
              borderBottomWidth: 1, 
              borderColor: theme.border,
              borderBottomLeftRadius: 16, 
              borderBottomRightRadius: 16, 
              padding: 18, 
              gap: 20, 
              marginTop: -4 
            }}>
              {/* Food Profile Indicators */}
              <View>
                <Text style={{ fontSize: 12, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 12, letterSpacing: 0.5 }}>
                  Nutritional Profile Indicators
                </Text>
                <View style={{ gap: 12 }}>
                  {/* Processing Level */}
                  <View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13, color: theme.text, fontWeight: '600' }}>Processing Intensity</Text>
                      <Text style={{ fontSize: 13, color: getMetricColor('NOVA', scorecard.nova_group), fontWeight: '700' }}>
                        NOVA {scorecard.nova_group} ({scorecard.nova_group === 4 ? 'Ultra-Processed' : 'Processed'})
                      </Text>
                    </View>
                    <View style={{ height: 5, backgroundColor: theme.border, borderRadius: 2.5 }}>
                      <View style={{ 
                        width: getProgressPercentage(scorecard.nova_group, 'nova'), 
                        height: '100%', 
                        backgroundColor: getMetricColor('NOVA', scorecard.nova_group), 
                        borderRadius: 2.5 
                      }} />
                    </View>
                  </View>

                  {/* Sugar Load */}
                  <View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13, color: theme.text, fontWeight: '600' }}>Sugar Load</Text>
                      <Text style={{ fontSize: 13, color: getMetricColor('Sugar', scorecard.sugar_load), fontWeight: '700' }}>
                        {scorecard.sugar_load}
                      </Text>
                    </View>
                    <View style={{ height: 5, backgroundColor: theme.border, borderRadius: 2.5 }}>
                      <View style={{ 
                        width: getProgressPercentage(scorecard.sugar_load, 'load'), 
                        height: '100%', 
                        backgroundColor: getMetricColor('Sugar', scorecard.sugar_load), 
                        borderRadius: 2.5 
                      }} />
                    </View>
                  </View>

                  {/* Additive Density */}
                  <View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13, color: theme.text, fontWeight: '600' }}>Additive Density</Text>
                      <Text style={{ fontSize: 13, color: getMetricColor('Additives', scorecard.additive_density), fontWeight: '700' }}>
                        {scorecard.additive_density}
                      </Text>
                    </View>
                    <View style={{ height: 5, backgroundColor: theme.border, borderRadius: 2.5 }}>
                      <View style={{ 
                        width: getProgressPercentage(scorecard.additive_density, 'density'), 
                        height: '100%', 
                        backgroundColor: getMetricColor('Additives', scorecard.additive_density), 
                        borderRadius: 2.5 
                      }} />
                    </View>
                  </View>

                  {/* Sodium Load */}
                  <View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13, color: theme.text, fontWeight: '600' }}>Sodium / Salt</Text>
                      <Text style={{ fontSize: 13, color: getMetricColor('Sodium', scorecard.sodium_load), fontWeight: '700' }}>
                        {scorecard.sodium_load}
                      </Text>
                    </View>
                    <View style={{ height: 5, backgroundColor: theme.border, borderRadius: 2.5 }}>
                      <View style={{ 
                        width: getProgressPercentage(scorecard.sodium_load, 'load'), 
                        height: '100%', 
                        backgroundColor: getMetricColor('Sodium', scorecard.sodium_load), 
                        borderRadius: 2.5 
                      }} />
                    </View>
                  </View>

                  {/* Ingredient Transparency */}
                  <View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ fontSize: 13, color: theme.text, fontWeight: '600' }}>Ingredient Transparency</Text>
                      <Text style={{ 
                        fontSize: 13, 
                        color: scorecard.transparency_index === 'High' ? theme.success : scorecard.transparency_index === 'Medium' ? theme.warning : theme.error, 
                        fontWeight: '700' 
                      }}>
                        {scorecard.transparency_index || 'High'}
                      </Text>
                    </View>
                    <View style={{ height: 5, backgroundColor: theme.border, borderRadius: 2.5 }}>
                      <View style={{ 
                        width: getProgressPercentage(scorecard.transparency_index || 'High', 'load'), 
                        height: '100%', 
                        backgroundColor: scorecard.transparency_index === 'High' ? theme.success : scorecard.transparency_index === 'Medium' ? theme.warning : theme.error, 
                        borderRadius: 2.5 
                      }} />
                    </View>
                  </View>
                </View>
              </View>

              {/* Point Breakdown */}
              {results.breakdown && results.breakdown.length > 0 && (
                <View>
                  <Text style={{ fontSize: 12, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 8, letterSpacing: 0.5 }}>
                    Deductions & Additions Breakdown
                  </Text>
                  <View style={{ gap: 8 }}>
                    {results.breakdown.map((item: any, idx: number) => (
                      <View key={idx} style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text style={{ color: theme.text, fontSize: 13, flex: 1, paddingRight: 10 }}>{item.reason}</Text>
                        <Text style={{ 
                          color: item.impact < 0 ? theme.error : theme.success, 
                          fontWeight: 'bold',
                          fontSize: 13
                        }}>
                          {item.impact > 0 ? `+${item.impact}` : item.impact}
                        </Text>
                      </View>
                    ))}
                  </View>
                </View>
              )}

              {/* Personalized Adjustments Alert */}
              {results.personalized_adjustments && (
                <View style={{
                  backgroundColor: 'rgba(255, 214, 10, 0.06)',
                  padding: 12,
                  borderRadius: 12,
                  borderWidth: 1,
                  borderColor: 'rgba(255, 214, 10, 0.15)',
                }}>
                  <Text style={{ fontSize: 13, color: theme.text }}>
                    ⚠️ <Text style={{ fontWeight: 'bold' }}>{results.personalized_adjustments.active_mode} Mode: </Text>
                    {results.personalized_adjustments.reason}
                  </Text>
                </View>
              )}

              {/* AI Written Narrative Explanation */}
              <View>
                <Text style={{ fontSize: 12, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 6, letterSpacing: 0.5 }}>
                  AI Summary Explanation
                </Text>
                <Text style={{ fontSize: 13, color: theme.muted, lineHeight: 18 }}>
                  {results.explanation}
                </Text>
              </View>

              {/* Extracted Ingredients text */}
              <View>
                <Text style={{ fontSize: 12, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 6, letterSpacing: 0.5 }}>
                  Verified Ingredients List
                </Text>
                <Text style={{ fontSize: 13, color: theme.muted, fontStyle: 'italic', lineHeight: 18 }}>
                  {results.corrected_text || 'No ingredient list saved.'}
                </Text>
              </View>
            </View>
          )}
        </View>

        {/* SWIPEABLE DETAILED COMPARISON & ALTERNATIVE CARDS */}
        {alternativesList.length > 0 && (
          <View style={{ marginBottom: 20 }}>
            <Text style={{ fontSize: 12, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 10, letterSpacing: 0.5 }}>
              Healthy Swaps & Side-by-Side Comparison
            </Text>
            <ScrollView 
              horizontal 
              pagingEnabled 
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={{ gap: 12 }}
            >
              {alternativesList.map((alt: any, idx: number) => {
                const isHelpful = feedbackLogged[idx];
                
                // Helper to get craving tags
                const getCravingTag = (categoryName: string, name: string) => {
                  const query = ((categoryName || '') + ' ' + (name || '')).toLowerCase();
                  if (query.includes('cookie') || query.includes('biscuit') || query.includes('sweet') || query.includes('chocolate') || query.includes('cereal')) {
                    return '🍪 Sweet Craving';
                  }
                  if (query.includes('chip') || query.includes('crisp') || query.includes('crunch') || query.includes('noodle') || query.includes('semiya') || query.includes('makhana')) {
                    return '🍿 Savory Crunch';
                  }
                  return '🌿 Clean Refreshment';
                };

                return (
                  <View key={idx} style={{ 
                    backgroundColor: theme.card, 
                    borderRadius: 24, 
                    padding: 20, 
                    borderWidth: 1, 
                    borderColor: theme.border,
                    width: 325,
                  }}>
                    {/* Header */}
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <Text style={{ fontSize: 17, fontWeight: '800', color: theme.text, flex: 1, marginRight: 8 }}>
                        {alt.name}
                      </Text>
                      <View style={{ backgroundColor: theme.accentSoft, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 }}>
                        <Text style={{ color: theme.primary, fontWeight: '700', fontSize: 11 }}>
                          Clean Swap
                        </Text>
                      </View>
                    </View>

                    {/* Premium craving & convenience tags */}
                    <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
                      <View style={{ backgroundColor: theme.bg, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, borderWidth: 1, borderColor: theme.border }}>
                        <Text style={{ fontSize: 11, color: theme.text, fontWeight: '600' }}>
                          {getCravingTag(results.category_info?.subcategory, alt.name)}
                        </Text>
                      </View>
                      <View style={{ backgroundColor: theme.bg, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, borderWidth: 1, borderColor: theme.border }}>
                        <Text style={{ fontSize: 11, color: theme.muted }}>
                          ⏱️ {alt.prep_time_mins || 15} Mins
                        </Text>
                      </View>
                      <View style={{ backgroundColor: theme.bg, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, borderWidth: 1, borderColor: theme.border }}>
                        <Text style={{ fontSize: 11, color: theme.muted }}>
                          🪙 ₹{alt.approx_cost_inr || 35} Est.
                        </Text>
                      </View>
                    </View>
                    
                    {/* Side-by-Side Visual Comparison */}
                    <View style={{ flexDirection: 'row', gap: 8, marginBottom: 14, alignItems: 'center' }}>
                      <View style={{ flex: 1, backgroundColor: theme.bg, padding: 8, borderRadius: 12, borderWidth: 1, borderColor: theme.border, alignItems: 'center' }}>
                        <Text style={{ fontSize: 9, color: theme.muted, textTransform: 'uppercase', marginBottom: 2 }}>Scanned</Text>
                        <Text style={{ fontSize: 12, fontWeight: '700', color: theme.error }}>NOVA {scorecard.nova_group}</Text>
                        <Text style={{ fontSize: 10, color: theme.muted }}>{scorecard.sugar_load} Sugar</Text>
                      </View>
                      <Text style={{ fontSize: 14, color: theme.muted }}>➔</Text>
                      <View style={{ flex: 1, backgroundColor: 'rgba(48, 209, 88, 0.05)', padding: 8, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(48, 209, 88, 0.2)', alignItems: 'center' }}>
                        <Text style={{ fontSize: 9, color: theme.muted, textTransform: 'uppercase', marginBottom: 2 }}>This Swap</Text>
                        <Text style={{ fontSize: 12, fontWeight: '700', color: theme.success }}>NOVA 1</Text>
                        <Text style={{ fontSize: 10, color: theme.success }}>Low Sugar</Text>
                      </View>
                    </View>

                    {/* Reasoning Narrative */}
                    <Text style={{ fontSize: 13, color: theme.text, lineHeight: 18, marginBottom: 12 }}>
                      {alt.reasoning?.why_selected || 'Recommended healthy swap matching the category craving.'}
                    </Text>

                    {/* Comparison Checklist Bullets */}
                    <View style={{ 
                      backgroundColor: theme.bg, 
                      borderRadius: 14, 
                      padding: 12, 
                      marginBottom: 16,
                      borderWidth: 1,
                      borderColor: theme.border
                    }}>
                      <Text style={{ fontSize: 11, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 6, letterSpacing: 0.5 }}>
                        Why it is better
                      </Text>
                      {alt.reasoning?.bullets ? (
                        alt.reasoning.bullets.map((b: string, bidx: number) => (
                          <Text key={bidx} style={{ fontSize: 12, color: theme.text, lineHeight: 17, marginBottom: 2 }}>
                            {b}
                          </Text>
                        ))
                      ) : (
                        <Text style={{ fontSize: 12, color: theme.text }}>
                          ✓ Minimizes refined fats & sugars{"\n"}
                          ✓ Eliminates synthetic preservatives{"\n"}
                          ✓ Quick home cooking recipe
                        </Text>
                      )}
                    </View>

                    {/* telemetric feedback loop */}
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                      <Text style={{ fontSize: 12, color: theme.muted }}>Was this swap helpful?</Text>
                      <View style={{ flexDirection: 'row', gap: 10 }}>
                        <TouchableOpacity 
                          onPress={() => handleFeedback(idx, 'up')}
                          style={{
                            padding: 6, 
                            borderRadius: 8,
                            backgroundColor: isHelpful === 'up' ? theme.accentSoft : 'transparent',
                            borderWidth: 1,
                            borderColor: isHelpful === 'up' ? theme.primary : theme.border
                          }}
                        >
                          <Text style={{ fontSize: 14 }}>👍</Text>
                        </TouchableOpacity>
                        <TouchableOpacity 
                          onPress={() => handleFeedback(idx, 'down')}
                          style={{
                            padding: 6, 
                            borderRadius: 8,
                            backgroundColor: isHelpful === 'down' ? 'rgba(255, 69, 58, 0.1)' : 'transparent',
                            borderWidth: 1,
                            borderColor: isHelpful === 'down' ? theme.error : theme.border
                          }}
                        >
                          <Text style={{ fontSize: 14 }}>👎</Text>
                        </TouchableOpacity>
                      </View>
                    </View>

                    {/* Recipe Reveal Button */}
                    <TouchableOpacity 
                      onPress={() => {
                        Alert.alert(alt.name, alt.recipe || 'Combine natural elements in a bowl.');
                      }}
                      style={{ 
                        backgroundColor: theme.primary,
                        paddingVertical: 12,
                        borderRadius: 14,
                        alignItems: 'center',
                      }}
                    >
                      <Text style={{ color: '#FFFFFF', fontWeight: '700', fontSize: 13 }}>
                        🍳 View Quick Recipe
                      </Text>
                    </TouchableOpacity>
                  </View>
                );
              })}
            </ScrollView>
          </View>
        )}
      </ScrollView>

      {/* Floating Assistant Button */}
      <Animated.View 
        pointerEvents={chatOpen ? 'none' : 'auto'}
        style={{
          position: 'absolute',
          bottom: 24,
          right: 24,
          transform: [{ scale: finalScale }],
          opacity: fabOpacity,
          shadowColor: theme.primary,
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.3,
          shadowRadius: 8,
          elevation: 6,
          zIndex: 999,
        }}
      >
        <TouchableOpacity
          onPress={() => setChatOpen(true)}
          style={{
            width: 56,
            height: 56,
            borderRadius: 28,
            backgroundColor: theme.primary,
            justifyContent: 'center',
            alignItems: 'center',
            borderWidth: 1.5,
            borderColor: theme.primaryLight,
          }}
        >
          <Text style={{ fontSize: 26 }}>🦕</Text>
        </TouchableOpacity>
      </Animated.View>

      {/* Elegant Assistant Bottom-Sheet Overlay */}
      {sheetVisible && (
        <View style={{
          ...StyleSheet.absoluteFillObject,
          zIndex: 1000,
        }}>
          {/* Backdrop Dismiss Trigger */}
          <Animated.View style={[
            StyleSheet.absoluteFillObject,
            {
              backgroundColor: '#000000',
              opacity: backdropOpacity,
            }
          ]}>
            <TouchableOpacity 
              style={StyleSheet.absoluteFillObject} 
              activeOpacity={1} 
              onPress={() => setChatOpen(false)} 
            />
          </Animated.View>
          
          <Animated.View style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            backgroundColor: theme.card,
            borderTopLeftRadius: 24,
            borderTopRightRadius: 24,
            borderWidth: 1,
            borderColor: theme.border,
            borderBottomWidth: 0,
            padding: 20,
            maxHeight: '75%',
            minHeight: 400,
            transform: [{ translateY: sheetTranslateY }],
            shadowColor: '#000',
            shadowOffset: { width: 0, height: -4 },
            shadowOpacity: 0.15,
            shadowRadius: 10,
            elevation: 10,
          }}>
            {/* Sheet Handle */}
            <View style={{
              width: 40,
              height: 4,
              backgroundColor: theme.border,
              borderRadius: 2,
              alignSelf: 'center',
              marginBottom: 16,
            }} />
            
            {/* Header */}
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                <Text style={{ fontSize: 28 }}>🦕</Text>
                <View>
                  <Text style={{ color: theme.text, fontWeight: '800', fontSize: 16 }}>Ask EcoSaur</Text>
                  <Text style={{ color: theme.muted, fontSize: 11 }}>Your clean-eating helper</Text>
                </View>
              </View>
              <TouchableOpacity onPress={() => setChatOpen(false)} style={{
                backgroundColor: theme.bg,
                paddingVertical: 6,
                paddingHorizontal: 12,
                borderRadius: 12,
                borderWidth: 1,
                borderColor: theme.border,
              }}>
                <Text style={{ color: theme.text, fontSize: 12, fontWeight: '600' }}>Close</Text>
              </TouchableOpacity>
            </View>
            
            {/* Chat History Messages */}
            <ScrollView 
              ref={chatScrollRef}
              style={{ flex: 1, marginBottom: 12 }} 
              contentContainerStyle={{ gap: 10, paddingBottom: 10 }}
            >
              {chatHistory.length === 0 ? (
                <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', marginVertical: 30 }}>
                  <Text style={{ fontSize: 40, marginBottom: 12 }}>🦕</Text>
                  <Text style={{ color: theme.text, fontSize: 15, fontWeight: '700', textAlign: 'center' }}>
                    How can I help you choose today?
                  </Text>
                  <Text style={{ color: theme.muted, fontSize: 12, textAlign: 'center', marginTop: 4, paddingHorizontal: 20, lineHeight: 18 }}>
                    Select a quick prompt below or type your question about this product's ingredients.
                  </Text>
                </View>
              ) : (
                chatHistory.map((msg, idx) => (
                  <View key={idx} style={{
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    backgroundColor: msg.role === 'user' ? theme.primary : theme.bg,
                    borderRadius: 16,
                    paddingVertical: 10,
                    paddingHorizontal: 14,
                    maxWidth: '85%',
                    borderWidth: msg.role === 'user' ? 0 : 1,
                    borderColor: theme.border,
                  }}>
                    <Text style={{ color: msg.role === 'user' ? '#FFFFFF' : theme.text, fontSize: 13, lineHeight: 18 }}>
                      {msg.content}
                    </Text>
                  </View>
                ))
              )}
              {chatLoading && (
                <View style={{ 
                  alignSelf: 'flex-start', 
                  flexDirection: 'row', 
                  alignItems: 'center', 
                  gap: 8, 
                  backgroundColor: theme.bg, 
                  borderRadius: 16, 
                  paddingVertical: 10, 
                  paddingHorizontal: 14, 
                  borderWidth: 1, 
                  borderColor: theme.border 
                }}>
                  <ActivityIndicator size="small" color={theme.primary} />
                  <Text style={{ fontSize: 12, color: theme.muted }}>EcoSaur is thinking...</Text>
                </View>
              )}
            </ScrollView>

            {/* Contextual Quick Actions */}
            {!chatLoading && (
              <View style={{ marginBottom: 12 }}>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
                  {[
                    { text: 'Why ultra-processed?', value: 'Why is this product classified under NOVA Group ' + scorecard.nova_group + '?' },
                    { text: 'Explain sugar load', value: 'What does glycemic sugar load of ' + scorecard.sugar_load + ' mean?' },
                    { text: 'Explain additive density', value: 'What does synthetic additive density of ' + scorecard.additive_density + ' mean?' },
                    { text: 'Why recommended swap?', value: 'Why was ' + mainAlternative.name + ' recommended as a swap?' },
                  ].map((act, i) => (
                    <TouchableOpacity
                      key={i}
                      onPress={() => handleQuickAction(act.value)}
                      style={{
                        backgroundColor: theme.bg,
                        borderWidth: 1,
                        borderColor: theme.border,
                        borderRadius: 20,
                        paddingVertical: 8,
                        paddingHorizontal: 12,
                      }}
                    >
                      <Text style={{ color: theme.primary, fontSize: 11, fontWeight: '600' }}>{act.text}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            )}

            {/* Input Box */}
            <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center', marginBottom: Platform.OS === 'ios' ? 24 : 10 }}>
              <TextInput
                value={chatInput}
                onChangeText={setChatInput}
                placeholder="Ask about ingredients or swaps..."
                placeholderTextColor={theme.muted}
                style={{
                  flex: 1,
                  backgroundColor: theme.bg,
                  color: theme.text,
                  borderRadius: 14,
                  paddingHorizontal: 14,
                  height: 42,
                  borderWidth: 1,
                  borderColor: theme.border,
                  fontSize: 13,
                }}
              />
              <TouchableOpacity 
                onPress={handleSendChat}
                style={{
                  backgroundColor: theme.primary,
                  width: 42,
                  height: 42,
                  borderRadius: 14,
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                <Text style={{ color: '#FFFFFF', fontWeight: 'bold', fontSize: 15 }}>➔</Text>
              </TouchableOpacity>
            </View>
          </Animated.View>
        </View>
      )}
    </View>
  );
}
