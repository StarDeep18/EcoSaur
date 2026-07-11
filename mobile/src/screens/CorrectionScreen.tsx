import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, Alert, useColorScheme, Vibration } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { api } from '../services/api';
import { THEME } from '../theme';

export default function CorrectionScreen() {
  const params = useLocalSearchParams();
  const router = useRouter();
  const colorScheme = useColorScheme() ?? 'dark';
  const theme = THEME[colorScheme as 'light' | 'dark'];

  // Input states
  const [productName, setProductName] = useState((params.productName as string) || '');
  const [rawText, setRawText] = useState((params.rawText as string) || '');
  const [lowConfidenceWords, setLowConfidenceWords] = useState<string[]>(() => {
    try {
      return JSON.parse((params.lowConfidenceWords as string) || '[]');
    } catch {
      return [];
    }
  });

  const [activeWordToCorrect, setActiveWordToCorrect] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Simple dictionary helper for suggestions
  const getSuggestions = (word: string) => {
    const clean = word.toLowerCase().replace(/[^a-z]/g, "");
    if (clean.includes("plam") || clean.includes("oil")) return ["palm oil", "palmolein", "vegetable oil"];
    if (clean.includes("sug") || clean.includes("sger") || clean.includes("swet")) return ["sugar", "corn syrup", "jaggery"];
    if (clean.includes("wha") || clean.includes("floo") || clean.includes("maida")) return ["wheat flour", "maida", "oats flour"];
    if (clean.includes("salt") || clean.includes("sod")) return ["salt", "sodium benzoate", "potassium sorbate"];
    if (clean.includes("benzo") || clean.includes("pres")) return ["sodium benzoate", "potassium sorbate", "preservative"];
    return ["sugar", "salt", "palm oil"];
  };

  // Replace a word inside the raw text and log the correction loop
  const handleWordCorrection = (original: string, replacement: string) => {
    // Basic word replacement logic
    const regex = new RegExp(`\\b${original}\\b`, 'gi');
    const updated = rawText.replace(regex, replacement);
    setRawText(updated);
    
    // Filter out from highlighted list
    setLowConfidenceWords(prev => prev.filter(w => w.toLowerCase() !== original.toLowerCase()));
    setActiveWordToCorrect(null);

    // Call logging correction endpoint in background
    api.logOCRCorrection(original, replacement, productName || 'Mobile Scans').catch(err => {
      console.warn('Failed to log spellcheck correction mapping:', err);
    });
  };

  // Run scoring calculations and trigger dataset loop contribution
  const handleAnalyze = async () => {
    if (!rawText.trim() || rawText.trim().length < 5) {
      Alert.alert('Invalid Ingredients', 'Please provide a valid ingredients list (minimum 5 characters).');
      return;
    }

    setAnalyzing(true);
    try {
      // If barcode was scanned but not registered, upload it permanently to crowdsourced database moat
      if (params.barcode) {
        try {
          await api.uploadBarcode(params.barcode as string, productName || 'New Product', rawText);
          Vibration.vibrate(40);
          Alert.alert('Moat Database Contributed!', '🎉 +5 Contributor Points! Thank you for adding this product to EcoSaur.');
        } catch (dbErr) {
          console.warn('Failed to crowdsource new barcode scan:', dbErr);
        }
      }

      const result = await api.analyzeFood(
        rawText, 
        productName, 
        'default', 
        (params.imageUrl as string) || undefined
      );
      
      // Store in global in-memory session cache for instant repeat barcode scanning
      if (params.barcode) {
        api.barcodeAnalysisCache[params.barcode as string] = result;
      }
      
      // Navigate to results screen, passing data
      router.push({
        pathname: '/results',
        params: {
          resultsPayload: JSON.stringify(result),
          productName: productName || result.category_info?.subcategory || 'Scanned Product',
        }
      });
    } catch (err: any) {
      Alert.alert('Analysis Failed', err.message || 'Unable to analyze ingredients.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.bg }} contentContainerStyle={{ padding: 20 }}>
      {params.barcode && (
        <View style={{
          backgroundColor: 'rgba(255, 214, 10, 0.06)',
          borderRadius: 16,
          padding: 16,
          marginBottom: 18,
          borderWidth: 1,
          borderColor: 'rgba(255, 214, 10, 0.2)',
          flexDirection: 'row',
          gap: 12,
          alignItems: 'center'
        }}>
          <Text style={{ fontSize: 28 }}>🦕</Text>
          <View style={{ flex: 1 }}>
            <Text style={{ color: theme.text, fontSize: 13, fontWeight: '700', marginBottom: 2 }}>
              New Barcode: {params.barcode}
            </Text>
            <Text style={{ color: theme.muted, fontSize: 12, lineHeight: 16 }}>
              🦖 <Text style={{ fontWeight: 'bold' }}>EcoSaur:</Text> "Mapping this snack grows our database! Add the ingredients to crowdsource it and earn +5 contributor points."
            </Text>
          </View>
        </View>
      )}
      <Text style={{ fontSize: 14, color: theme.muted, marginBottom: 20, lineHeight: 20 }}>
        We've extracted the ingredients. Tap any highlighted words in amber to select spelling suggestions, or double-check and edit the text manually.
      </Text>

      {/* Product Name Input */}
      <View style={{ marginBottom: 20 }}>
        <Text style={{ fontSize: 13, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 8, letterSpacing: 0.5 }}>
          Product Brand / Name
        </Text>
        <TextInput
          value={productName}
          onChangeText={setProductName}
          placeholder="e.g. Oreo Cookies, Pepsi"
          placeholderTextColor={theme.muted}
          style={{
            backgroundColor: theme.card,
            color: theme.text,
            borderRadius: 14,
            paddingVertical: 14,
            paddingHorizontal: 16,
            borderWidth: 1,
            borderColor: theme.border,
            fontSize: 16,
          }}
        />
      </View>

      {/* Tap to Correct highlights box */}
      <View style={{ marginBottom: 20 }}>
        <Text style={{ fontSize: 13, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 8, letterSpacing: 0.5 }}>
          Interactive Spellcheck Highlights
        </Text>
        <View style={{
          backgroundColor: theme.card,
          borderRadius: 16,
          padding: 16,
          borderWidth: 1,
          borderColor: theme.border,
          minHeight: 100,
        }}>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 4 }}>
            {rawText.split(/\s+/).map((word, idx) => {
              const clean = word.replace(/[^a-zA-Z]/g, "").toLowerCase();
              const isLowConfidence = lowConfidenceWords.some(w => w.toLowerCase() === clean);

              if (isLowConfidence) {
                return (
                  <TouchableOpacity 
                    key={idx} 
                    onPress={() => {
                      Vibration.vibrate(10);
                      setActiveWordToCorrect(clean === activeWordToCorrect ? null : clean);
                    }}
                    style={{
                      backgroundColor: 'rgba(250, 204, 21, 0.08)',
                      borderBottomWidth: 1.5,
                      borderBottomColor: '#facc15',
                      paddingHorizontal: 2,
                      borderRadius: 2,
                    }}
                  >
                    <Text style={{ color: theme.text, fontSize: 15, fontWeight: '500' }}>{word}</Text>
                  </TouchableOpacity>
                );
              }
              return (
                <Text key={idx} style={{ color: theme.text, fontSize: 15 }}>
                  {word}{' '}
                </Text>
              );
            })}
          </View>
        </View>
      </View>

      {/* Suggestions Modal / Overlay */}
      {activeWordToCorrect && (
        <View style={{
          backgroundColor: theme.card,
          borderRadius: 18,
          padding: 18,
          borderWidth: 1,
          borderColor: 'rgba(250, 204, 21, 0.3)',
          marginBottom: 20,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.1,
          shadowRadius: 6,
          elevation: 2
        }}>
          <Text style={{ color: theme.text, fontWeight: '700', fontSize: 14, marginBottom: 12 }}>
            💡 Correction suggestion for <Text style={{ color: '#facc15' }}>"{activeWordToCorrect}"</Text>
          </Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
            {getSuggestions(activeWordToCorrect).map((suggestion, idx) => (
              <TouchableOpacity
                key={idx}
                onPress={() => {
                  Vibration.vibrate(15);
                  handleWordCorrection(activeWordToCorrect, suggestion);
                }}
                style={{
                  backgroundColor: 'rgba(250, 204, 21, 0.08)',
                  paddingVertical: 10,
                  paddingHorizontal: 16,
                  borderRadius: 12,
                  borderWidth: 1,
                  borderColor: '#facc15',
                }}
              >
                <Text style={{ color: theme.text, fontWeight: '600', fontSize: 13 }}>
                  {suggestion}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}

      {/* Edit Area Text Box */}
      <View style={{ marginBottom: 30 }}>
        <Text style={{ fontSize: 13, fontWeight: '700', color: theme.primary, textTransform: 'uppercase', marginBottom: 8, letterSpacing: 0.5 }}>
          Raw Ingredient Text
        </Text>
        <TextInput
          value={rawText}
          onChangeText={setRawText}
          multiline
          numberOfLines={6}
          placeholder="Paste or correct ingredients list..."
          placeholderTextColor={theme.muted}
          textAlignVertical="top"
          style={{
            backgroundColor: theme.card,
            color: theme.text,
            borderRadius: 16,
            padding: 16,
            borderWidth: 1,
            borderColor: theme.border,
            fontSize: 15,
            minHeight: 120,
            lineHeight: 22,
          }}
        />
      </View>

      {/* Analyze button */}
      {analyzing ? (
        <ActivityIndicator size="large" color={theme.primary} />
      ) : (
        <TouchableOpacity
          onPress={handleAnalyze}
          style={{
            backgroundColor: theme.primary,
            paddingVertical: 18,
            borderRadius: 18,
            alignItems: 'center',
            marginBottom: 40,
          }}
        >
          <Text style={{ color: '#FFFFFF', fontSize: 16, fontWeight: '700' }}>
            ✨ Review Ingredients
          </Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
}
