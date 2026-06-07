import { Platform } from 'react-native';

// Standard Android emulator loopback IP is 10.0.2.2, iOS is localhost
const BASE_URL = Platform.select({
  android: 'http://192.168.31.126:8000/api/v1',
  ios: 'http://localhost:8000/api/v1',
  default: 'http://localhost:8000/api/v1',
});

export interface ApiResponseError {
  detail: string;
}

export const api = {
  /**
   * Uploads raw captured image and performs OCR text extraction.
   */
  async extractText(imageUri: string): Promise<{ raw_text: string; low_confidence_words: string[] }> {
    const formData = new FormData();
    // Format image uri for file upload
    const filename = imageUri.split('/').pop() || 'label.jpg';

    formData.append('file', {
      uri: imageUri,
      name: filename,
      type: 'image/jpeg',
    } as any);

    const res = await fetch(`${BASE_URL}/scan/extract`, {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'multipart/form-data',
      },
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'OCR extraction failed');
    }
    return data;
  },

  /**
   * Performs rule-based analysis on verified/corrected ingredients text.
   */
  async analyzeFood(correctedText: string, productName?: string, userId: string = 'default'): Promise<any> {
    const res = await fetch(`${BASE_URL}/scan/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
    return data;
  },

  /**
   * Queries local custom moat DB / OpenFoodFacts for registered barcodes.
   */
  async lookupBarcode(barcode: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/barcode/lookup/${barcode}`);
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
    const res = await fetch(`${BASE_URL}/barcode/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
    const res = await fetch(`${BASE_URL}/ocr/correct`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
   * Side-by-side comparison of 2 or more products.
   */
  async compareProducts(productNames: string[], correctedTexts: string[]): Promise<any> {
    const res = await fetch(`${BASE_URL}/product/compare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
    const res = await fetch(`${BASE_URL}/scan/history?limit=${limit}`);
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
    const res = await fetch(`${BASE_URL}/scan/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
