import React, { useState, useRef, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Button, ActivityIndicator, useColorScheme, Animated, Alert, Vibration } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { api } from '../services/api';
import { THEME } from '../theme';

export default function ScanScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  
  // Cache for duplicate barcode scans to avoid API delays
  const scanCache = useRef<Record<string, any>>({});
  
  const cameraRef = useRef<any>(null);
  const router = useRouter();
  const colorScheme = useColorScheme() ?? 'dark';
  const theme = THEME[colorScheme as 'light' | 'dark'];

  // Animation for the scan laser beam
  const beamAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Loop scan beam animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(beamAnim, {
          toValue: 1,
          duration: 2500,
          useNativeDriver: true,
        }),
        Animated.timing(beamAnim, {
          toValue: 0,
          duration: 2500,
          useNativeDriver: true,
        })
      ])
    ).start();
  }, []);

  if (!permission) {
    // Camera permissions are still loading
    return (
      <View style={[styles.center, { backgroundColor: theme.bg }]}>
        <ActivityIndicator size="large" color={theme.primary} />
      </View>
    );
  }

  if (!permission.granted) {
    // Camera permissions are not granted yet
    return (
      <View style={[styles.container, styles.center, { backgroundColor: theme.bg, padding: 24 }]}>
        <Text style={{ fontSize: 18, color: theme.text, textAlign: 'center', marginBottom: 20 }}>
          We need your permission to show the camera viewfinder
        </Text>
        <TouchableOpacity 
          onPress={requestPermission}
          style={{ backgroundColor: theme.primary, paddingVertical: 14, paddingHorizontal: 28, borderRadius: 12 }}
        >
          <Text style={{ color: '#fff', fontSize: 16, fontWeight: 'bold' }}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Handle capture button press
  const handleCapture = async () => {
    if (cameraRef.current && !loading) {
      Vibration.vibrate(15);
      setLoading(true);
      setLoadingStatus('📷 Capturing clear label...');
      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.85,
          skipProcessing: false,
        });

        setLoadingStatus('⚙️ OCR extraction running...');
        // Call OCR extract endpoint
        const ocrResult = await api.extractText(photo.uri);

        setLoadingStatus('🧪 Running safety analysis...');
        // Navigate to correction screen
        router.push({
          pathname: '/correction',
          params: {
            rawText: ocrResult.raw_text,
            lowConfidenceWords: JSON.stringify(ocrResult.low_confidence_words || []),
            productName: '',
          }
        });
      } catch (err: any) {
        Alert.alert('OCR Extraction Failed', err.message || 'Unable to scan ingredients list.');
      } finally {
        setLoading(false);
        setLoadingStatus('');
      }
    }
  };

  // Handle barcode scanned callback
  const handleBarcodeScanned = async ({ data }: { data: string }) => {
    if (scanned || loading) return;
    
    // Check local analysis cache first for instant results
    if (api.barcodeAnalysisCache[data]) {
      Vibration.vibrate([0, 15, 10, 15]);
      setScanned(true);
      const cachedResult = api.barcodeAnalysisCache[data];
      router.push({
        pathname: '/results',
        params: {
          resultsPayload: JSON.stringify(cachedResult),
          productName: cachedResult.product_name || 'Scanned Product',
        }
      });
      return;
    }

    // Check local duplicate cache
    if (scanCache.current[data]) {
      Vibration.vibrate(25);
      setScanned(true);
      const cachedResult = scanCache.current[data];
      router.push({
        pathname: '/correction',
        params: {
          rawText: cachedResult.raw_text,
          lowConfidenceWords: '[]',
          productName: cachedResult.product_name || 'Scanned Product',
          barcode: data,
        }
      });
      return;
    }

    Vibration.vibrate(25);
    setScanned(true);
    setLoading(true);
    setLoadingStatus('🏷️ Reading barcode...');
    try {
      const barcodeResult = await api.lookupBarcode(data);
      
      // Store in session cache
      scanCache.current[data] = barcodeResult;

      if (barcodeResult.barcode_not_found) {
        Alert.alert(
          'Product Not Registered',
          `Barcode ${data} is missing. Please type ingredients list manually to crowdsource!`,
          [
            {
              text: 'Write Manually',
              onPress: () => {
                router.push({
                  pathname: '/correction',
                  params: {
                    rawText: '',
                    lowConfidenceWords: '[]',
                    productName: '',
                    barcode: data,
                  }
                });
              }
            },
            {
              text: 'Cancel',
              onPress: () => setScanned(false)
            }
          ]
        );
      } else {
        // Barcode successfully retrieved ingredients. Go straight to correction / verification screen
        router.push({
          pathname: '/correction',
          params: {
            rawText: barcodeResult.raw_text,
            lowConfidenceWords: '[]',
            productName: barcodeResult.product_name || 'Scanned Product',
            barcode: data,
          }
        });
      }
    } catch (err: any) {
      Alert.alert('Barcode Lookup Error', 'Could not query barcode database.');
      setScanned(false);
    } finally {
      setLoading(false);
      setLoadingStatus('');
    }
  };

  // Translate vertical position for scanning beam
  const translateBeam = beamAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 240] // limits beam translation inside viewport box
  });

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <CameraRefWrapper 
        cameraRef={cameraRef}
        onBarcodeScanned={scanned ? undefined : handleBarcodeScanned}
      >
        <View style={styles.overlay}>
          {/* Top instructional guide */}
          <View style={styles.topContainer}>
            <Text style={styles.instructionText}>
              Scan Barcode OR Center Ingredients List inside Box
            </Text>
          </View>

          {/* Central scanner box */}
          <View style={styles.viewfinderContainer}>
            <View style={[styles.viewfinderBox, { borderColor: theme.primary }]}>
              {/* Scan Beam */}
              <Animated.View style={[
                styles.scanBeam, 
                { backgroundColor: theme.primary, transform: [{ translateY: translateBeam }] }
              ]} />
              <View style={[styles.corner, styles.topLeft, { borderColor: theme.primary }]} />
              <View style={[styles.corner, styles.topRight, { borderColor: theme.primary }]} />
              <View style={[styles.corner, styles.bottomLeft, { borderColor: theme.primary }]} />
              <View style={[styles.corner, styles.bottomRight, { borderColor: theme.primary }]} />
            </View>
          </View>

          {/* Bottom capturing action buttons */}
          <View style={styles.bottomContainer}>
            {loading ? (
              <View style={{ 
                alignItems: 'center', 
                gap: 12,
                backgroundColor: 'rgba(22, 22, 24, 0.85)',
                paddingVertical: 18,
                paddingHorizontal: 28,
                borderRadius: 24,
                borderWidth: 1,
                borderColor: theme.border,
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 4 },
                shadowOpacity: 0.2,
                shadowRadius: 8,
                elevation: 4
              }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                  <ActivityIndicator size="small" color={theme.primary} />
                  <Text style={{ fontSize: 24 }}>🦕</Text>
                </View>
                <Text style={{
                  color: theme.text,
                  fontSize: 14,
                  fontWeight: '600',
                  textAlign: 'center',
                }}>
                  {loadingStatus}
                </Text>
              </View>
            ) : (
              <TouchableOpacity 
                onPress={handleCapture}
                style={[styles.captureButton, { backgroundColor: theme.primary }]}
              >
                <Text style={styles.captureText}>📷 CAPTURE INGREDIENTS</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </CameraRefWrapper>
    </View>
  );
}

// Support newer CameraView standard cleanly
function CameraRefWrapper({ cameraRef, onBarcodeScanned, children }: any) {
  return (
    <CameraView
      style={StyleSheet.absoluteFill}
      facing="back"
      barcodeScannerSettings={{
        barcodeTypes: ["qr", "ean13", "ean8", "upc_a", "upc_e"],
      }}
      onBarcodeScanned={onBarcodeScanned}
      ref={cameraRef}
    >
      {children}
    </CameraView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  center: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'space-between',
  },
  topContainer: {
    paddingTop: 30,
    alignItems: 'center',
  },
  instructionText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    textAlign: 'center',
  },
  viewfinderContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  viewfinderBox: {
    width: 280,
    height: 250,
    borderWidth: 1,
    position: 'relative',
    backgroundColor: 'rgba(255,255,255,0.03)',
  },
  scanBeam: {
    height: 3,
    width: '100%',
    shadowColor: '#10B981',
    shadowOpacity: 0.8,
    shadowRadius: 5,
    elevation: 4,
  },
  corner: {
    position: 'absolute',
    width: 20,
    height: 20,
    borderWidth: 3,
  },
  topLeft: {
    top: -3,
    left: -3,
    borderBottomWidth: 0,
    borderRightWidth: 0,
  },
  topRight: {
    top: -3,
    right: -3,
    borderBottomWidth: 0,
    borderLeftWidth: 0,
  },
  bottomLeft: {
    bottom: -3,
    left: -3,
    borderTopWidth: 0,
    borderRightWidth: 0,
  },
  bottomRight: {
    bottom: -3,
    right: -3,
    borderTopWidth: 0,
    borderLeftWidth: 0,
  },
  bottomContainer: {
    paddingBottom: 40,
    alignItems: 'center',
  },
  captureButton: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 5,
  },
  captureText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  }
});
