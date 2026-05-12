'use client';

import { useState, useRef } from 'react';

type Step = 'UPLOAD' | 'EXTRACTING' | 'CORRECTION' | 'ANALYZING' | 'RESULTS';

interface ChatMessage {
  role: 'user' | 'model';
  content: string;
}

export default function ScanFlow() {
  const [step, setStep] = useState<Step>('UPLOAD');
  const [file, setFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState('');
  const [results, setResults] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Chat state
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      
      if (!selectedFile.type.startsWith('image/')) {
        alert('Please upload a valid image file.');
        return;
      }
      if (selectedFile.size > 10 * 1024 * 1024) {
        alert('File size exceeds 10MB limit.');
        return;
      }

      setFile(selectedFile);
      setStep('EXTRACTING');
      
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      let retryCount = 0;
      const maxRetries = 2;
      
      while (retryCount <= maxRetries) {
        try {
          const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
          const res = await fetch(`${API_URL}/scan/extract`, {
            method: 'POST',
            body: formData,
          });
          const data = await res.json();
          
          if (!res.ok) throw new Error(data.detail || 'Failed to extract text');
          
          setRawText(data.raw_text);
          setStep('CORRECTION');
          return;
        } catch (err: any) {
          retryCount++;
          if (retryCount > maxRetries) {
            console.error(err);
            setRawText(`Error: ${err.message}. Please type manually.`);
            setStep('CORRECTION');
          }
        }
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
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${API_URL}/scan/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ corrected_text: rawText }),
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.detail || 'Analysis failed');
      
      setResults(data);
      setStep('RESULTS');

      // Advanced Feature: Save to History (localStorage for MVP without Auth)
      try {
        const history = JSON.parse(localStorage.getItem('ecosaur_history') || '[]');
        history.unshift({
          date: new Date().toISOString(),
          score: data.score,
          grade: data.grade,
          name: data.alternative.name // proxy for food name
        });
        localStorage.setItem('ecosaur_history', JSON.stringify(history.slice(0, 50)));
      } catch (e) { console.error("Could not save history"); }

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
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${API_URL}/scan/barcode/${barcode}`);
      const data = await res.json();
      setRawText(data.raw_text);
      setStep('CORRECTION');
    } catch (err) {
      alert("Barcode lookup failed.");
      setStep('UPLOAD');
    }
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage: ChatMessage = { role: 'user', content: chatInput };
    setChatHistory((prev) => [...prev, userMessage]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      // In a real app we'd need to extract the raw ingredients list from the results object or have the backend send it down.
      // For this MVP we will just send the whole raw text as context to the chat API.
      // Or we can extract it from results.breakdown if we modify the backend, but backend doesn't send ingredients yet.
      // Let's pass rawText as a proxy for ingredients for the conversational UX context.
      const res = await fetch(`${API_URL}/scan/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ingredients: [rawText], // passing raw string as context
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

  return (
    <div className="container">
      {step === 'UPLOAD' && (
        <>
          <h1 className="title">Scan Ingredients</h1>
          <p className="subtitle">Upload or take a photo of the ingredient label and nutrition facts.</p>
          <div className="card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <input 
              type="file" 
              accept="image/*" 
              capture="environment" 
              className="hidden-input" 
              ref={fileInputRef}
              onChange={handleFileChange}
            />
            <button className="btn-primary" onClick={() => fileInputRef.current?.click()} style={{ marginBottom: '1rem' }}>
              📷 Take Photo or Upload
            </button>
            <button className="btn-secondary" onClick={handleBarcodeSubmit}>
              🏷️ Enter Barcode
            </button>
          </div>
        </>
      )}

      {step === 'EXTRACTING' && (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <h2>Extracting text...</h2>
          <p className="subtitle" style={{ marginTop: '1rem' }}>Reading the label with AI Vision.</p>
        </div>
      )}

      {step === 'CORRECTION' && (
        <>
          <h1 className="title">Review OCR</h1>
          <p className="subtitle">Sometimes labels are blurry. Please correct any misspelled ingredients below before we analyze.</p>
          <div className="card">
            <textarea 
              className="textarea" 
              value={rawText} 
              onChange={(e) => setRawText(e.target.value)}
            />
            <button className="btn-primary" onClick={handleAnalyze}>
              Analyze Food
            </button>
          </div>
        </>
      )}

      {step === 'ANALYZING' && (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <h2>Analyzing...</h2>
          <p className="subtitle" style={{ marginTop: '1rem' }}>Running deterministic scoring engine.</p>
        </div>
      )}

      {step === 'RESULTS' && results && (
        <>
          <h1 className="title" style={{ textAlign: 'center' }}>Results</h1>
          <p className="subtitle" style={{ textAlign: 'center' }}>Here is your transparent food analysis.</p>

          <div className="card" style={{ textAlign: 'center' }}>
            <div className={`grade-dial grade-${results.grade}`}>
              {results.grade}
            </div>
            <h2>Score: {results.score}/100</h2>
            <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>{results.explanation}</p>
          </div>

          <h2 style={{ marginBottom: '1rem' }}>Score Breakdown</h2>
          <div className="card" style={{ padding: '1rem' }}>
            {results.breakdown.map((item: any, idx: number) => (
              <div key={idx} className="breakdown-item">
                <span>{item.reason}</span>
                <span className={item.impact < 0 ? 'impact-negative' : 'impact-positive'}>
                  {item.impact > 0 ? '+' : ''}{item.impact}
                </span>
              </div>
            ))}
          </div>

          <h2 style={{ marginBottom: '1rem' }}>Homemade Alternative</h2>
          <div className="card">
            <h3 style={{ color: 'var(--primary-dark)', marginBottom: '1rem' }}>{results.alternative.name}</h3>
            <p style={{ whiteSpace: 'pre-line' }}>{results.alternative.recipe}</p>
          </div>

          {/* Conversational UX Section */}
          <h2 style={{ marginBottom: '1rem' }}>Ask EcoSaur</h2>
          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '1rem' }}>
              {chatHistory.length === 0 && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center' }}>
                  Have questions about these ingredients? Ask me!
                </p>
              )}
              {chatHistory.map((msg, idx) => (
                <div key={idx} style={{ 
                  margin: '0.5rem 0', 
                  textAlign: msg.role === 'user' ? 'right' : 'left',
                }}>
                  <span style={{
                    display: 'inline-block',
                    padding: '0.5rem 1rem',
                    borderRadius: '12px',
                    backgroundColor: msg.role === 'user' ? 'var(--primary)' : '#e2e8f0',
                    color: msg.role === 'user' ? 'white' : 'black',
                  }}>
                    {msg.content}
                  </span>
                </div>
              ))}
              {isChatLoading && <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Typing...</p>}
            </div>
            <form onSubmit={handleChatSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
              <input 
                type="text" 
                value={chatInput} 
                onChange={(e) => setChatInput(e.target.value)} 
                placeholder="E.g., Why is maltodextrin bad?" 
                style={{ flex: 1, padding: '0.8rem', borderRadius: '8px', border: '1px solid #ccc' }}
              />
              <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0 1.5rem' }}>Send</button>
            </form>
          </div>

          <button className="btn-secondary" onClick={() => {
            setStep('UPLOAD');
            setChatHistory([]);
            setResults(null);
          }} style={{ marginBottom: '2rem' }}>
            Scan Another Product
          </button>
        </>
      )}
    </div>
  );
}
