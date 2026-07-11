import { Platform } from 'react-native';
import { supabase } from './supabase';

const BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8000/api/v1';

export interface ApiResponseError {
  detail: string;
}

// In-memory caches for instant duplicate scan handling
export const barcodeAnalysisCache: Record<string, any> = {};
export const analysisCache: Record<string, any> = {};

// Helper to get headers dynamically with Bearer Token
async function getHeaders(contentType: string = 'application/json') {
  const { data: { session } } = await supabase.auth.getSession();
  const headers: Record<string, string> = {
    'Accept': 'application/json',
  };
  if (contentType !== 'multipart/form-data') {
    headers['Content-Type'] = contentType;
  }
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`;
  }
  return headers;
}

export const api = {
  barcodeAnalysisCache,
  analysisCache,
  /**
   * Uploads raw captured image and performs OCR text extraction.
   */
  async extractText(imageUri: string): Promise<{ raw_text: string; low_confidence_words: string[] }> {
    const formData = new FormData();
    const filename = imageUri.split('/').pop() || 'label.jpg';

    formData.append('file', {
      uri: imageUri,
      name: filename,
      type: 'image/jpeg',
    } as any);

    const headers = await getHeaders('multipart/form-data');
    const res = await fetch(`${BASE_URL}/scan/extract`, {
      method: 'POST',
      body: formData,
      headers: headers,
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'OCR extraction failed');
    }
    return data;
  },

  async analyzeFood(correctedText: string, productName?: string, userId: string = 'default'): Promise<any> {
    const cacheKey = correctedText.trim();
    if (analysisCache[cacheKey]) {
      return analysisCache[cacheKey];
    }
    
    const headers = await getHeaders();
    const res = await fetch(`${BASE_URL}/scan/analyze`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        corrected_text: correctedText,
        product_name: productName || undefined,
        user_id: userId,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Analysis failed');
    }
    analysisCache[cacheKey] = data;
    return data;
  },

  /**
   * Queries local custom database / OpenFoodFacts for registered barcodes.
   */
  async lookupBarcode(barcode: string): Promise<any> {
    const headers = await getHeaders();
    const res = await fetch(`${BASE_URL}/barcode/lookup/${barcode}`, {
      headers: headers,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Barcode lookup failed');
    }
    return data;
  },

  /**
   * permanent crowdsourcing ingestion for new barcodes.
   */
  async uploadBarcode(barcode: string, productName: string, ingredientsText: string): Promise<any> {
    const headers = await getHeaders();
    const res = await fetch(`${BASE_URL}/barcode/upload`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        barcode,
        product_name: productName,
        ingredients_text: ingredientsText,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Product contribution failed');
    }
    return data;
  },

  /**
   * Logs manual OCR corrections to improve synonym spellchecking maps.
   */
  async logOCRCorrection(originalText: string, correctedText: string, productName: string = 'Mobile Scans'): Promise<any> {
    const headers = await getHeaders();
    const res = await fetch(`${BASE_URL}/ocr/correct`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        original_text: originalText,
        corrected_text: correctedText,
        product_name: productName,
        user_id: 'default',
      }),
    });
    return res.json();
  },

  /**
   * Fetches user health/dietary preference mode.
   */
  async getUserPreferences(): Promise<{ id: string; health_mode: string }> {
    const headers = await getHeaders();
    const res = await fetch(`${BASE_URL}/user/preferences`, {
      headers: headers,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to fetch user preferences');
    }
    return data;
  },

  /**
   * Updates user health/dietary preference mode.
   */
  async updateUserPreferences(healthMode: string): Promise<{ id: string; health_mode: string }> {
    const headers = await getHeaders();
    const res = await fetch(`${BASE_URL}/user/preferences`, {
      method: 'PUT',
      headers: headers,
      body: JSON.stringify({
        health_mode: healthMode,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to update user preferences');
    }
    return data;
  },

  /**
   * Side-by-side comparison of 2 or more products.
   */
  async compareProducts(productNames: string[], correctedTexts: string[]): Promise<any> {
    const headers = await getHeaders();
    const res = await fetch(`${BASE_URL}/product/compare`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        product_names: productNames,
        corrected_texts: correctedTexts,
        user_id: 'default',
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Comparison request failed');
    }
    return data;
  },

  /**
   * Fetches scan history.
   */
  async getScanHistory(limit: number = 50): Promise<any[]> {
    const headers = await getHeaders();
    const res = await fetch(`${BASE_URL}/scan/history?limit=${limit}`, {
      headers: headers,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'History lookup failed');
    }
    return data;
  },

  /**
   * Requests conversational AI responses on specific ingredients.
   */
  async chatWithAI(ingredients: string[], history: { role: string; content: string }[], message: string): Promise<any> {
    const headers = await getHeaders();
    const res = await fetch(`${BASE_URL}/scan/chat`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        ingredients,
        history,
        message,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Chat query failed');
    }
    return data;
  },
};
