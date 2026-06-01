'use client';

import { useState, useRef, useEffect } from 'react';

type Step = 'UPLOAD' | 'EXTRACTING' | 'CORRECTION' | 'ANALYZING' | 'RESULTS';

interface ChatMessage {
  role: 'user' | 'model';
  content: string;
}

export default function ScanFlow() {
  const [step, setStep] = useState<Step>('UPLOAD');
  const [file, setFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState('');
  const [productName, setProductName] = useState('');
  const [results, setResults] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // OCR Highlights & Inline correction popover states
  const [lowConfidenceWords, setLowConfidenceWords] = useState<string[]>([]);
  const [activePopover, setActivePopover] = useState<{ word: string; index: number; x: number; y: number } | null>(null);
  
  // Barcode crowdsourcing modal states
  const [showBarcodeModal, setShowBarcodeModal] = useState(false);
  const [missingBarcode, setMissingBarcode] = useState('');
  const [crowdProductName, setCrowdProductName] = useState('');
  const [crowdIngredients, setCrowdIngredients] = useState('');
  const [isSubmittingCrowd, setIsSubmittingCrowd] = useState(false);

  // Chat state
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Close active popovers on scroll or outer click
  useEffect(() => {
    const handleOuterClick = () => setActivePopover(null);
    window.addEventListener('click', handleOuterClick);
    return () => window.removeEventListener('click', handleOuterClick);
  }, []);

  // CLIENT-SIDE IMAGE PREPROCESSING UTILITY
  const preprocessImage = (fileToProcess: File): Promise<Blob> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d')!;
          
          // Resizing Dim (max 1200px)
          let width = img.width;
          let height = img.height;
          const maxDim = 1200;
          if (width > maxDim || height > maxDim) {
            if (width > height) {
              height = Math.round((height * maxDim) / width);
              width = maxDim;
            } else {
              width = Math.round((width * maxDim) / height);
              height = maxDim;
            }
          }
          
          canvas.width = width;
          canvas.height = height;
          ctx.drawImage(img, 0, 0, width, height);
          
          // Image enhancement pixel loops: Grayscale & High Contrast boost
          const imgData = ctx.getImageData(0, 0, width, height);
          const pixels = imgData.data;
          
          for (let i = 0; i < pixels.length; i += 4) {
            const r = pixels[i];
            const g = pixels[i+1];
            const b = pixels[i+2];
            
            // 1. Luma formula Grayscale
            let gray = 0.299 * r + 0.587 * g + 0.114 * b;
            
            // 2. High-Contrast thresholding (stretches dark and light borders)
            if (gray < 95) {
              gray = Math.max(0, gray - 30);
            } else if (gray > 160) {
              gray = Math.min(255, gray + 45);
            } else {
              gray = ((gray - 95) / 65) * 255;
            }
            
            pixels[i] = gray;
            pixels[i+1] = gray;
            pixels[i+2] = gray;
          }
          ctx.putImageData(imgData, 0, 0);
          
          // Export as compressed JPEG blob
          canvas.toBlob((blob) => {
            resolve(blob || fileToProcess);
          }, 'image/jpeg', 0.85);
        };
        img.src = event.target?.result as string;
      };
      reader.readAsDataURL(fileToProcess);
    });
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      
      if (!selectedFile.type.startsWith('image/')) {
        alert('Please upload a valid image file.');
        return;
      }

      setFile(selectedFile);
      setStep('EXTRACTING');
      
      const fileHash = `ecosaur_ocr_${selectedFile.name}_${selectedFile.size}`;
      try {
        const cached = localStorage.getItem(fileHash);
        if (cached) {
          const cachedData = JSON.parse(cached);
          setRawText(cachedData.raw_text);
          setLowConfidenceWords(cachedData.low_confidence_words || []);
          setStep('CORRECTION');
          return;
        }
      } catch (err) {
        console.warn("Failed to retrieve OCR cache:", err);
      }
      
      try {
        // Preprocess image on canvas (downscale, grayscale, increase contrast)
        const processedBlob = await preprocessImage(selectedFile);
        const processedFile = new File([processedBlob], selectedFile.name, { type: 'image/jpeg' });
        
        const formData = new FormData();
        formData.append('file', processedFile);
        
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
        const res = await fetch(`${API_URL}/scan/extract`, {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        
        if (!res.ok) throw new Error(data.detail || 'Failed to extract text');
        
        // Cache parsed results permanently in local storage moat
        try {
          localStorage.setItem(fileHash, JSON.stringify({
            raw_text: data.raw_text,
            low_confidence_words: data.low_confidence_words || []
          }));
        } catch (err) {
          console.warn("Failed to write to OCR cache:", err);
        }
        
        setRawText(data.raw_text);
        setLowConfidenceWords(data.low_confidence_words || []);
        setStep('CORRECTION');
      } catch (err: any) {
        console.error(err);
        alert(`OCR text extraction failed: ${err.message}. Transitioning to manual entry.`);
        setRawText("");
        setLowConfidenceWords([]);
        setStep('CORRECTION');
      }
    }
  };

  const handleAnalyze = async () => {
    if (!rawText || rawText.trim().length < 5) {
      alert("Please provide valid ingredient text to analyze.");
      return;
    }

    setStep('ANALYZING');
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
      const res = await fetch(`${API_URL}/scan/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          corrected_text: rawText,
          product_name: productName.trim() || undefined
        }),
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.detail || 'Analysis failed');
      
      setResults(data);
      setStep('RESULTS');

      // Save to local scan history (localstorage fallback)
      try {
        const history = JSON.parse(localStorage.getItem('ecosaur_history') || '[]');
        const computedScore = intScore(data.scorecard);
        const computedGrade = `NOVA ${data.scorecard.nova_group}`;
        history.unshift({
          date: new Date().toISOString(),
          score: computedScore,
          grade: computedGrade,
          name: data.alternative.name
        });
        localStorage.setItem('ecosaur_history', JSON.stringify(history.slice(0, 50)));
      } catch (e) { console.error("Could not save history", e); }

    } catch (err: any) {
      console.error(err);
      alert(`Error analyzing food: ${err.message}`);
      setStep('CORRECTION');
    }
  };

  const handleBarcodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const barcode = prompt("Enter product barcode (e.g., 5449000000996 for Coca Cola):");
    if (!barcode) return;

    setStep('EXTRACTING');
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
      const res = await fetch(`${API_URL}/scan/barcode/${barcode}`);
      const data = await res.json();
      
      if (data.barcode_not_found) {
        // Barcode missing - trigger packaging crowdsource modal
        setMissingBarcode(data.barcode);
        setCrowdProductName('');
        setCrowdIngredients('');
        setShowBarcodeModal(true);
        setStep('UPLOAD');
        return;
      }
      
      setRawText(data.raw_text);
      setProductName(data.product_name || "Scanned Product");
      setLowConfidenceWords([]);
      setStep('CORRECTION');
    } catch (err) {
      alert("Barcode lookup failed.");
      setStep('UPLOAD');
    }
  };

  // Submit crowdsourced product information to local database moat
  const handleCrowdsourceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!crowdProductName.trim() || !crowdIngredients.trim()) {
      alert("Please provide the product name and ingredient list.");
      return;
    }
    
    setIsSubmittingCrowd(true);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
      const res = await fetch(`${API_URL}/barcode/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          barcode: missingBarcode,
          product_name: crowdProductName.trim(),
          ingredients_text: crowdIngredients.trim()
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Submission failed");
      
      alert("Product saved permanently to database moat! Loaded into scanner correction.");
      setShowBarcodeModal(false);
      setRawText(crowdIngredients.trim());
      setProductName(crowdProductName.trim());
      setLowConfidenceWords([]);
      setStep('CORRECTION');
    } catch (err: any) {
      alert(`Failed to save product details: ${err.message}`);
    } finally {
      setIsSubmittingCrowd(false);
    }
  };

  const handleChatSubmit = async (e?: React.FormEvent, customMsg?: string) => {
    if (e) e.preventDefault();
    const msgText = customMsg || chatInput;
    if (!msgText.trim()) return;

    const userMessage: ChatMessage = { role: 'user', content: msgText };
    setChatHistory((prev) => [...prev, userMessage]);
    if (!customMsg) setChatInput('');
    setIsChatLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
      const res = await fetch(`${API_URL}/scan/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ingredients: [rawText],
          history: chatHistory,
          message: userMessage.content
        }),
      });
      const data = await res.json();
      const modelMessage: ChatMessage = { role: 'model', content: data.reply };
      setChatHistory((prev) => [...prev, modelMessage]);
    } catch (err) {
      console.error(err);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Helper dictionary suggestions for low confidence overlays
  const getSuggestionsForWord = (word: string) => {
    const clean = word.toLowerCase().replace(/[^a-z]/g, "");
    if (clean.includes("plam") || clean.includes("oil")) return ["palm oil", "palmolein", "vegetable oil"];
    if (clean.includes("sug") || clean.includes("sger") || clean.includes("swet")) return ["sugar", "corn syrup", "jaggery"];
    if (clean.includes("wha") || clean.includes("floo") || clean.includes("maida")) return ["wheat flour", "maida", "oats flour"];
    if (clean.includes("salt") || clean.includes("sod")) return ["salt", "sodium benzoate", "potassium sorbate"];
    if (clean.includes("benzo") || clean.includes("pres")) return ["sodium benzoate", "potassium sorbate", "preservative"];
    return ["sugar", "salt", "palm oil"];
  };

  // Handles inline click correction replacements and automatically logs correction loops
  const replaceWordInText = (wordToReplace: string, index: number, replacement: string) => {
    const tokens = rawText.split(/\s+/);
    let currentMatchCount = 0;
    
    const updatedTokens = tokens.map((token) => {
      const cleanToken = token.replace(/[^a-zA-Z]/g, "");
      if (cleanToken.toLowerCase() === wordToReplace.toLowerCase()) {
        if (currentMatchCount === index) {
          currentMatchCount++;
          const suffix = token.slice(cleanToken.length);
          return replacement + suffix;
        }
        currentMatchCount++;
      }
      return token;
    });

    setRawText(updatedTokens.join(" "));
    setActivePopover(null);
    setLowConfidenceWords((prev) => prev.filter((w) => w.toLowerCase() !== wordToReplace.toLowerCase()));

    // Background log OCR correction loops
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
      fetch(`${API_URL}/ocr/correct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_text: wordToReplace,
          corrected_text: replacement,
          product_name: productName || "Unknown Product",
          user_id: "default"
        })
      });
    } catch (e) {
      console.warn("Failed to log OCR correction mapping", e);
    }
  };

  // Score metrics index calculator
  const intScore = (sc: any) => {
    return Math.max(20, Math.min(100, intScoreRaw(sc)));
  };

  const intScoreRaw = (sc: any) => {
    let s = 100;
    s -= (sc.nova_group * 12);
    if (sc.sugar_load === "High") s -= 15;
    if (sc.sugar_load === "Moderate") s -= 5;
    if (sc.sodium_load === "High") s -= 10;
    if (sc.additive_density === "High") s -= 10;
    if (sc.additive_density === "Medium") s -= 5;
    if (sc.protein_quality === "High Source") s += 8;
    if (sc.fiber_quality === "High Source") s += 8;
    return s;
  };

  const scoreToGradeLetter = (score: number) => {
    if (score >= 90) return 'S';
    if (score >= 80) return 'A';
    if (score >= 70) return 'B';
    if (score >= 60) return 'C';
    if (score >= 40) return 'D';
    return 'F';
  };

  // Maps values to relative progress percentages
  const getRelativeBarPercentage = (metricName: string, value: string | number) => {
    if (metricName === "NOVA") {
      const val = Number(value);
      if (val === 1) return 25;
      if (val === 2) return 50;
      if (val === 3) return 75;
      return 100;
    }
    if (value === "High") return 90;
    if (value === "Medium" || value === "Moderate" || value === "Standard") return 55;
    if (value === "High Source") return 85;
    return 20; // Low
  };

  const getMetricColor = (metricName: string, value: string | number, isHealthyMetric = false) => {
    if (metricName === "NOVA") {
      const val = Number(value);
      if (val === 1) return "#10b981"; // green
      if (val === 2) return "#a3e635"; // light green
      if (val === 3) return "#fb923c"; // orange
      return "#ef4444"; // red
    }
    
    if (isHealthyMetric) {
      return value === "High Source" ? "#10b981" : "#64748b";
    }
    
    if (value === "High") return "#ef4444";
    if (value === "Medium" || value === "Moderate") return "#facc15";
    return "#10b981"; // Low
  };

  const radius = 60;
  const circumference = 2 * Math.PI * radius; // ~377

  return (
    <div className="container animate-fade-in">
      {/* CROWDSOURCING MISSING PRODUCT PACKAGING MODAL */}
      {showBarcodeModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h2 className="title" style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: 'var(--text-main)' }}>
               contribute Package Details
            </h2>
            <p className="subtitle" style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>
              Barcode <strong style={{ color: 'var(--primary)' }}>{missingBarcode}</strong> is missing from databases. Help crowdsource this product permanently to our database moat.
            </p>
            
            <form onSubmit={handleCrowdsourceSubmit}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
                  Product Name / Brand
                </label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g. Lay's Magic Masala, Pepsi 500ml"
                  value={crowdProductName}
                  onChange={(e) => setCrowdProductName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.8rem',
                    borderRadius: '12px',
                    border: '1px solid var(--input-border)',
                    backgroundColor: 'var(--input-bg)',
                    color: 'var(--text-main)',
                    fontSize: '0.9rem'
                  }}
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
                  Ingredient Label List
                </label>
                <textarea 
                  required
                  rows={4}
                  placeholder="Paste or type ingredients list from the package..."
                  value={crowdIngredients}
                  onChange={(e) => setCrowdIngredients(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.8rem',
                    borderRadius: '12px',
                    border: '1px solid var(--input-border)',
                    backgroundColor: 'var(--input-bg)',
                    color: 'var(--text-main)',
                    fontSize: '0.9rem',
                    resize: 'vertical',
                    fontFamily: 'inherit'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowBarcodeModal(false)} style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isSubmittingCrowd} style={{ flex: 1 }}>
                  {isSubmittingCrowd ? "Ingesting..." : "Save Product Moat"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {step === 'UPLOAD' && (
        <>
          <h1 className="title">Scan Ingredients</h1>
          <p className="subtitle">Capture package labels. Canvas filters dynamically boost contrast on your device for absolute reliability.</p>
          
          <div className="card card-glow-primary">
            <div className="scan-viewport">
              <div className="scan-pulse-ring">
                <span className="scan-icon">🦕</span>
              </div>
              <div className="scan-laser-beam"></div>
              <div className="scan-overlay-corners"></div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '1.25rem', letterSpacing: '0.05em' }}>PREPROCESSING CANVASES ACTIVE</span>
            </div>

            <input 
              type="file" 
              accept="image/*" 
              capture="environment" 
              className="hidden-input" 
              ref={fileInputRef}
              onChange={handleFileChange}
            />
            
            <button className="btn-primary" onClick={() => fileInputRef.current?.click()} style={{ marginBottom: '0.75rem' }}>
              📷 Squeeze Camera or Upload Label
            </button>
            <button className="btn-secondary" onClick={handleBarcodeSubmit}>
              🏷️ Enter Barcode (Moat & OFF Lookup)
            </button>
          </div>
        </>
      )}

      {step === 'EXTRACTING' && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
          <div className="scan-pulse-ring" style={{ margin: '0 auto 1.5rem auto' }}>
            <span className="scan-icon">⚡</span>
          </div>
          <h2 className="title" style={{ fontSize: '1.75rem' }}>Extracting Ingredients</h2>
          <p className="subtitle" style={{ marginBottom: 0 }}>Gemini OCR is processing the Canvas-boosted package details...</p>
          
          <div style={{ marginTop: '2rem' }}>
            <div className="skeleton-line" style={{ width: '90%' }}></div>
            <div className="skeleton-line" style={{ width: '75%' }}></div>
            <div className="skeleton-line" style={{ width: '85%' }}></div>
          </div>
        </div>
      )}

      {step === 'CORRECTION' && (
        <>
          <h1 className="title">Verify Extracted Text</h1>
          <p className="subtitle">Refine terms manually. Typo-tolerant matching resolves misspells programmatically.</p>
          
          <div className="card" style={{ position: 'relative' }}>
            {/* POPUP suggestion correct overlay */}
            {activePopover && (
              <div 
                className="correction-popover"
                style={{ 
                  left: `${Math.min(300, activePopover.x - 20)}px`, 
                  top: `${activePopover.y - 120}px` 
                }}
                onClick={(ev) => ev.stopPropagation()}
              >
                <div className="popover-title">OCR Spelling Suggestions</div>
                {getSuggestionsForWord(activePopover.word).map((suggestion, sIdx) => (
                  <div 
                    key={sIdx} 
                    className="popover-chip"
                    onClick={() => replaceWordInText(activePopover.word, activePopover.index, suggestion)}
                  >
                    ✔ {suggestion}
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginBottom: '1.25rem', width: '100%', textAlign: 'left' }}>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', color: 'var(--primary)' }}>
                Product Name / Brand
              </label>
              <input 
                type="text" 
                placeholder="e.g. Coca-Cola, Lay's, Oreo, Maggi..."
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.9rem 1.1rem',
                  borderRadius: '14px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  fontSize: '0.95rem',
                  backgroundColor: 'rgba(0, 0, 0, 0.3)',
                  color: 'var(--text-main)',
                }}
              />
            </div>

            {/* Smart Inline Highlights correction */}
            <div style={{ width: '100%', textAlign: 'left', marginBottom: '0.75rem' }}>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--primary)' }}>
                Tap-to-Correct Highlights (Click words in amber)
              </label>
              
              <div style={{ 
                background: 'rgba(0, 0, 0, 0.2)', 
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '14px', 
                padding: '0.85rem',
                minHeight: '80px',
                marginTop: '0.5rem',
                fontSize: '0.9rem',
                lineHeight: 1.6
              }}>
                {rawText ? (() => {
                  let matchMap: Record<string, number> = {};
                  return rawText.split(/\s+/).map((token, tIdx) => {
                    const cleanToken = token.replace(/[^a-zA-Z]/g, "");
                    const lowerToken = cleanToken.toLowerCase();
                    const isFlagged = lowConfidenceWords.some(w => w.toLowerCase() === lowerToken);
                    
                    if (isFlagged) {
                      if (!(lowerToken in matchMap)) matchMap[lowerToken] = 0;
                      const currentIdx = matchMap[lowerToken];
                      matchMap[lowerToken]++;
                      
                      return (
                        <span 
                          key={tIdx} 
                          className="ocr-highlight-token"
                          onClick={(ev) => {
                            ev.stopPropagation();
                            // Capture coordinates for popover relative positioning
                            const rect = ev.currentTarget.getBoundingClientRect();
                            const cardRect = ev.currentTarget.parentElement?.parentElement?.getBoundingClientRect();
                            const x = rect.left - (cardRect?.left || 0);
                            const y = rect.top - (cardRect?.top || 0) + ev.currentTarget.parentElement!.scrollTop;
                            
                            setActivePopover({
                              word: cleanToken,
                              index: currentIdx,
                              x: x,
                              y: y
                            });
                          }}
                        >
                          {token}
                        </span>
                      );
                    }
                    return <span key={tIdx}> {token} </span>;
                  });
                })() : (
                  <span style={{ color: 'var(--text-muted)' }}>No text loaded. Type below to correct.</span>
                )}
              </div>
            </div>

            <div style={{ width: '100%', textAlign: 'left', marginBottom: '0.5rem' }}>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                Full Raw Extracted List
              </label>
            </div>
            
            <textarea 
              className="textarea" 
              value={rawText} 
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste or type ingredients list..."
            />
            
            <button className="btn-primary" onClick={handleAnalyze}>
              🔍 Analyze Scanned Product
            </button>
          </div>
        </>
      )}

      {step === 'ANALYZING' && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
          <div className="scan-pulse-ring" style={{ margin: '0 auto 1.5rem auto' }}>
            <span className="scan-icon">🧬</span>
          </div>
          <h2 className="title" style={{ fontSize: '1.75rem' }}>Scoring Engine Running</h2>
          <p className="subtitle" style={{ marginBottom: 0 }}>Executing E-number maps and multi-stage token matching...</p>
          
          <div style={{ marginTop: '2rem' }}>
            <div className="skeleton-circle"></div>
            <div className="skeleton-line" style={{ width: '80%', margin: '0 auto 0.75rem auto' }}></div>
            <div className="skeleton-line" style={{ width: '60%', margin: '0 auto 0.75rem auto' }}></div>
          </div>
        </div>
      )}

      {step === 'RESULTS' && results && (() => {
        const scoreVal = intScore(results.scorecard);
        const gradeLetter = scoreToGradeLetter(scoreVal);
        const strokeDashoffset = circumference - (circumference * scoreVal) / 100;
        const colorClass = `color-grade-${gradeLetter}`;

        return (
          <>
            {/* 1. PRODUCT HEADER */}
            <div className="card animate-fade-in" style={{ paddingBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="carousel-badge" style={{ background: 'rgba(6, 182, 212, 0.12)', color: '#06b6d4', borderColor: 'rgba(6, 182, 212, 0.25)' }}>
                  {results.category_info?.subcategory || "Processed Snack"}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                  Deterministic Score Moat
                </span>
              </div>
              <h2 className="title" style={{ fontSize: '2rem', marginBottom: '0.25rem', color: 'var(--text-main)', WebkitTextFillColor: 'initial', background: 'none' }}>
                {productName || results.category_info?.subcategory || "Scanned Item"}
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Top-Level Category: <strong style={{ color: 'var(--text-main)' }}>{results.category_info?.category || "Snacks"}</strong>
              </p>
            </div>

            {results.confidence && (
              <div className="card animate-fade-in" style={{ 
                padding: '0.85rem 1.25rem', 
                background: 'var(--input-bg)', 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                fontSize: '0.8rem',
                border: '1px solid var(--card-border)',
                borderRadius: '16px',
                marginBottom: '1.25rem'
              }}>
                <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  🛡️ Trust Indicators:
                </div>
                <div style={{ display: 'flex', gap: '1.2rem', fontWeight: 600 }}>
                  <span style={{ color: results.confidence.ocr_level === 'High' ? '#10b981' : '#facc15' }}>
                    OCR Quality: {results.confidence.ocr_score}% ({results.confidence.ocr_level})
                  </span>
                  <span style={{ color: results.confidence.match_level === 'High' ? '#10b981' : '#facc15' }}>
                    Ingredients Recognized: {results.confidence.match_score}%
                  </span>
                </div>
              </div>
            )}

            {/* 2. CIRCULAR SVG GRADE DIAL & EXPLANATION */}
            <div className="card" style={{ textAlign: 'center' }}>
              <div className="grade-dial-wrapper">
                <svg className="grade-dial-svg">
                  <circle className="grade-dial-bg" cx="70" cy="70" r={radius} />
                  <circle 
                    className={`grade-dial-fill ${colorClass}`} 
                    cx="70" 
                    cy="70" 
                    r={radius} 
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                  />
                </svg>
                <div className="grade-text-center">
                  <span className={`grade-letter ${colorClass}`}>{gradeLetter}</span>
                  <span className="grade-score-label">{scoreVal}/100</span>
                </div>
              </div>
              
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.75rem' }}>Health Quality Index</h3>
              <p style={{ fontSize: '0.95rem', color: 'var(--text-main)', lineHeight: '1.6', padding: '0 0.5rem' }}>
                {results.explanation}
              </p>
              
              {results.personalized_adjustments && (
                <div style={{ 
                  marginTop: '1.25rem', 
                  padding: '0.85rem 1rem', 
                  borderRadius: '14px', 
                  background: 'rgba(239, 68, 68, 0.08)', 
                  border: '1px solid rgba(239, 68, 68, 0.2)', 
                  color: '#fca5a5', 
                  textAlign: 'left',
                  fontSize: '0.85rem',
                  lineHeight: 1.5
                }}>
                  ⚠️ <strong>{results.personalized_adjustments.active_mode} Mode Adjustment:</strong> {results.personalized_adjustments.reason}
                </div>
              )}
            </div>

            {/* 3. NUTRITIONAL PROFILE SCORECARD GRID */}
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '1.5rem 0 0.75rem 0', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Nutritional Profile Metrics
            </h3>
            
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-label">NOVA Processing</span>
                <div className={`metric-value nova-${results.scorecard.nova_group}`}>
                  NOVA {results.scorecard.nova_group}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>
                  {results.scorecard.nova_group === 4 ? "Ultra-Processed" : results.scorecard.nova_group === 3 ? "Processed" : "Minimally Processed"}
                </span>
              </div>
              
              <div className="metric-card">
                <span className="metric-label">Additive Load</span>
                <div className={`metric-value load-${results.scorecard.additive_density}`}>
                  {results.scorecard.additive_density}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>
                  Chemical stabilizers/dyes
                </span>
              </div>
              
              <div className="metric-card">
                <span className="metric-label">Sugar Load</span>
                <div className={`metric-value load-${results.scorecard.sugar_load}`}>
                  {results.scorecard.sugar_load}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>
                  Glycemic surge potential
                </span>
              </div>
              
              <div className="metric-card">
                <span className="metric-label">Sodium Load</span>
                <div className={`metric-value load-${results.scorecard.sodium_load}`}>
                  {results.scorecard.sodium_load}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>
                  Salt content levels
                </span>
              </div>
            </div>

            {/* 4. MAIN CONCERNS & STRENGTHS */}
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '1.5rem 0 0.75rem 0', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Ingredient Breakdown Analysis
            </h3>
            
            <div className="card" style={{ padding: '0.75rem 1.25rem' }}>
              {results.breakdown && results.breakdown.map((item: any, idx: number) => (
                <div key={idx} className="breakdown-item">
                  <span style={{ color: 'var(--text-main)', flex: 1, paddingRight: '0.5rem', lineHeight: '1.4' }}>
                    {item.impact < 0 ? '🔴' : '💚'} {item.reason}
                  </span>
                  <span className={item.impact < 0 ? 'impact-negative' : 'impact-positive'}>
                    {item.impact > 0 ? '+' : ''}{item.impact}
                  </span>
                </div>
              ))}
            </div>

            {/* 5. SWIPABLE BETTER ALTERNATIVES */}
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '1.5rem 0 0.75rem 0', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Indian Homemade Alternatives (Swipe Left)
            </h3>
            
            <div className="carousel-container" style={{ paddingLeft: '0.5rem', paddingRight: '0.5rem', marginBottom: '1.25rem' }}>
              {(results.alternatives || [results.alternative]).map((alt: any, idx: number) => (
                <div key={idx} className="carousel-card">
                  <div className="carousel-title-bar">
                    <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', flex: 1, paddingRight: '0.5rem' }}>{alt.name}</h4>
                    <span className="carousel-badge">NOVA 1 staple</span>
                  </div>
                  <div className="carousel-meta">
                    <span>⏱️ Prep: {alt.prep_time_mins || 10} mins</span>
                    <span>💰 Cost: ~₹{alt.approx_cost_inr || 20}</span>
                  </div>
                  <div className="carousel-recipe-steps">
                    <strong>Healthy Preparation Recipe:</strong>
                    <div style={{ marginTop: '0.4rem', color: 'var(--text-main)' }}>{alt.recipe}</div>
                  </div>
                  {alt.reasoning && (
                    <div style={{
                      marginTop: '0.75rem',
                      padding: '0.75rem',
                      borderRadius: '12px',
                      background: 'var(--primary-glow)',
                      border: '1px solid var(--primary)',
                      fontSize: '0.8rem',
                      lineHeight: '1.4'
                    }}>
                      <div style={{ fontWeight: 700, color: 'var(--primary)', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        🛡️ Why this alternative?
                      </div>
                      <p style={{ color: 'var(--text-muted)', marginBottom: '0.5rem', textAlign: 'left' }}>{alt.reasoning.why_selected}</p>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(1, 1fr)', gap: '0.25rem', textAlign: 'left' }}>
                        {alt.reasoning.bullets && alt.reasoning.bullets.map((b: string, bIdx: number) => (
                          <span key={bIdx} style={{ color: 'var(--text-main)', display: 'flex', alignItems: 'flex-start', gap: '0.3rem' }}>
                            {b}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* 6. SIDE-BY-SIDE SAME-CATEGORY PRODUCT COMPARISON WITH NUTRITION PROGRESS BARS */}
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '1.5rem 0 0.75rem 0', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Commercial Product Comparison in Same Category
            </h3>
            
            <div className="comparison-scroll" style={{ paddingLeft: '0.25rem', paddingRight: '0.25rem', marginBottom: '1.25rem' }}>
              {/* CURRENT SCAN PRODUCT */}
              <div className="comparison-card-v" style={{ border: '1px solid rgba(239, 68, 68, 0.2)', background: 'rgba(239, 68, 68, 0.02)' }}>
                <div className="comparison-header">
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fca5a5' }}>Scanned Item</h4>
                  <span className="comparison-grade c-grade-F">{gradeLetter}</span>
                </div>
                <div style={{ marginBottom: '1.25rem' }}>
                  <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{productName || "This Scanned Product"}</strong>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Top level category: {results.category_info?.subcategory}</div>
                </div>
                
                {/* Visual side by side comparison bar values */}
                <div className="comp-bar-row">
                  <div className="comp-bar-label-group">
                    <span className="comp-bar-label">Processing Index</span>
                    <span className="comp-bar-value" style={{ color: getMetricColor("NOVA", results.scorecard.nova_group) }}>
                      NOVA {results.scorecard.nova_group}
                    </span>
                  </div>
                  <div className="progress-bar-container">
                    <div 
                      className="progress-bar-fill" 
                      style={{ 
                        width: `${getRelativeBarPercentage("NOVA", results.scorecard.nova_group)}%`,
                        background: getMetricColor("NOVA", results.scorecard.nova_group)
                      }}
                    />
                  </div>
                </div>

                <div className="comp-bar-row">
                  <div className="comp-bar-label-group">
                    <span className="comp-bar-label">Sugar Load</span>
                    <span className="comp-bar-value" style={{ color: getMetricColor("Sugar", results.scorecard.sugar_load) }}>
                      {results.scorecard.sugar_load}
                    </span>
                  </div>
                  <div className="progress-bar-container">
                    <div 
                      className="progress-bar-fill" 
                      style={{ 
                        width: `${getRelativeBarPercentage("Sugar", results.scorecard.sugar_load)}%`,
                        background: getMetricColor("Sugar", results.scorecard.sugar_load)
                      }}
                    />
                  </div>
                </div>

                <div className="comp-bar-row">
                  <div className="comp-bar-label-group">
                    <span className="comp-bar-label">Sodium Load</span>
                    <span className="comp-bar-value" style={{ color: getMetricColor("Sodium", results.scorecard.sodium_load) }}>
                      {results.scorecard.sodium_load}
                    </span>
                  </div>
                  <div className="progress-bar-container">
                    <div 
                      className="progress-bar-fill" 
                      style={{ 
                        width: `${getRelativeBarPercentage("Sodium", results.scorecard.sodium_load)}%`,
                        background: getMetricColor("Sodium", results.scorecard.sodium_load)
                      }}
                    />
                  </div>
                </div>

                <div className="comp-bar-row">
                  <div className="comp-bar-label-group">
                    <span className="comp-bar-label">Additive Density</span>
                    <span className="comp-bar-value" style={{ color: getMetricColor("Additive", results.scorecard.additive_density) }}>
                      {results.scorecard.additive_density}
                    </span>
                  </div>
                  <div className="progress-bar-container">
                    <div 
                      className="progress-bar-fill" 
                      style={{ 
                        width: `${getRelativeBarPercentage("Additive", results.scorecard.additive_density)}%`,
                        background: getMetricColor("Additive", results.scorecard.additive_density)
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* COMMERCIAL SWAPPING OPTIONS */}
              {results.comparisons && results.comparisons.map((cCard: any, cIdx: number) => (
                <div key={cIdx} className="comparison-card-v" style={{ border: '1px solid rgba(16, 185, 129, 0.2)', background: 'rgba(16, 185, 129, 0.02)' }}>
                  <div className="comparison-header">
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#6ee7b7' }}>Swapping Option</h4>
                    <span className={`comparison-grade c-grade-${cCard.grade}`}>{cCard.grade}</span>
                  </div>
                  <div style={{ marginBottom: '1.25rem' }}>
                    <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{cCard.product_name}</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Index score: {cCard.score}/100</div>
                  </div>

                  {/* Dynamic side by side bar meters */}
                  <div className="comp-bar-row">
                    <div className="comp-bar-label-group">
                      <span className="comp-bar-label">Processing Index</span>
                      <span className="comp-bar-value" style={{ color: getMetricColor("NOVA", cCard.nova_group) }}>
                        NOVA {cCard.nova_group}
                      </span>
                    </div>
                    <div className="progress-bar-container">
                      <div 
                        className="progress-bar-fill" 
                        style={{ 
                          width: `${getRelativeBarPercentage("NOVA", cCard.nova_group)}%`,
                          background: getMetricColor("NOVA", cCard.nova_group)
                        }}
                      />
                    </div>
                  </div>

                  <div className="comp-bar-row">
                    <div className="comp-bar-label-group">
                      <span className="comp-bar-label">Sugar Load</span>
                      <span className="comp-bar-value" style={{ color: getMetricColor("Sugar", cCard.sugar_load) }}>
                        {cCard.sugar_load}
                      </span>
                    </div>
                    <div className="progress-bar-container">
                      <div 
                        className="progress-bar-fill" 
                        style={{ 
                          width: `${getRelativeBarPercentage("Sugar", cCard.sugar_load)}%`,
                          background: getMetricColor("Sugar", cCard.sugar_load)
                        }}
                      />
                    </div>
                  </div>

                  <div className="comp-bar-row">
                    <div className="comp-bar-label-group">
                      <span className="comp-bar-label">Sodium Load</span>
                      <span className="comp-bar-value" style={{ color: getMetricColor("Sodium", cCard.sodium_load) }}>
                        {cCard.sodium_load}
                      </span>
                    </div>
                    <div className="progress-bar-container">
                      <div 
                        className="progress-bar-fill" 
                        style={{ 
                          width: `${getRelativeBarPercentage("Sodium", cCard.sodium_load)}%`,
                          background: getMetricColor("Sodium", cCard.sodium_load)
                        }}
                      />
                    </div>
                  </div>

                  <p style={{ fontSize: '0.75rem', color: '#94a3b8', borderTop: '1px solid rgba(255,255,255,0.05)', marginTop: '0.85rem', paddingTop: '0.65rem', lineHeight: '1.4' }}>
                    💡 <strong>Why this recommendation?</strong> {cCard.description}
                  </p>
                </div>
              ))}
            </div>

            {/* 7. INTERACTIVE AI ASSISTANT CHAT */}
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '1.5rem 0 0.75rem 0', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Chat with EcoSaur Assistant
            </h3>
            
            <div className="card" style={{ padding: '1rem' }}>
              <div className="chat-window">
                <div className="chat-history">
                  {chatHistory.length === 0 && (
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', margin: 'auto' }}>
                      👋 Ask me any questions about these ingredients or food additives!
                    </p>
                  )}
                  {chatHistory.map((msg, idx) => (
                    <div 
                      key={idx} 
                      className={`chat-bubble chat-bubble-${msg.role === 'user' ? 'user' : 'model'}`}
                    >
                      {msg.content}
                    </div>
                  ))}
                  {isChatLoading && (
                    <div className="chat-bubble chat-bubble-model" style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
                      Analyzing query details...
                    </div>
                  )}
                </div>

                {/* Quick Chips Recommendations */}
                <div className="chat-chips-container">
                  <div className="chat-chip" onClick={() => handleChatSubmit(undefined, "Why is my product ultra-processed?")}>
                    ❓ Why ultra-processed?
                  </div>
                  <div className="chat-chip" onClick={() => handleChatSubmit(undefined, "Is this product child friendly?")}>
                    👶 Child suitability?
                  </div>
                  <div className="chat-chip" onClick={() => handleChatSubmit(undefined, "Are there diabetic alerts?")}>
                    🩸 Diabetic alerts?
                  </div>
                </div>

                <form onSubmit={handleChatSubmit} className="chat-form">
                  <input 
                    type="text" 
                    value={chatInput} 
                    onChange={(e) => setChatInput(e.target.value)} 
                    placeholder="E.g., What are the main preservatives here?" 
                    className="chat-input"
                  />
                  <button type="submit" className="chat-send-btn">Send</button>
                </form>
              </div>
            </div>

            <button className="btn-secondary animate-fade-in" onClick={() => {
              setStep('UPLOAD');
              setChatHistory([]);
              setResults(null);
              setProductName('');
              setLowConfidenceWords([]);
            }} style={{ marginBottom: '2rem', display: 'flex' }}>
              🔄 Scan Another Packaged Product
            </button>
          </>
        );
      })()}
    </div>
  );
}
