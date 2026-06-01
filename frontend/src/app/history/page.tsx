'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function HistoryPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [insights, setInsights] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
        
        // Fetch insights
        try {
          const insightsRes = await fetch(`${API_URL}/scan/history/insights`);
          if (insightsRes.ok) {
            const insightsData = await insightsRes.json();
            setInsights(insightsData);
          }
        } catch (e) {
          console.warn("Failed to load backend insights", e);
        }

        const res = await fetch(`${API_URL}/scan/history`);
        if (res.ok) {
          const data = await res.json();
          if (data && Array.isArray(data) && data.length > 0) {
            const formatted = data.map((item: any) => ({
              date: item.date,
              score: item.score,
              grade: item.grade.startsWith("NOVA") ? item.grade : `NOVA ${item.grade}`,
              name: item.alternative?.name || 'Scanned Food'
            }));
            setHistory(formatted);
            setIsLoading(false);
            return;
          }
        }
      } catch (err) {
        console.warn("Failed to load backend scan history, falling back to local storage.", err);
      }

      // Local storage fallback
      try {
        const savedHistory = localStorage.getItem('ecosaur_history');
        if (savedHistory) {
          setHistory(JSON.parse(savedHistory));
        }
      } catch (e) {
        console.error("Failed to read local storage", e);
      }
      setIsLoading(false);
    }

    fetchHistory();
  }, []);

  const getGradeLetter = (gradeStr: string, score: number) => {
    if (score >= 90) return 'S';
    if (score >= 80) return 'A';
    if (score >= 70) return 'B';
    if (score >= 60) return 'C';
    if (score >= 40) return 'D';
    return 'F';
  };

  return (
    <div className="container animate-fade-in">
      <h1 className="title">Analysis History</h1>
      <p className="subtitle">Track your past scans and review healthier choices side-by-side.</p>

      {insights && insights.has_scans && (
        <div className="card animate-fade-in" style={{ 
          background: 'var(--primary-glow)',
          border: '1px solid var(--primary)',
          padding: '1.5rem',
          borderRadius: '24px',
          marginBottom: '1.5rem',
          textAlign: 'left'
        }}>
          <h2 className="title" style={{ fontSize: '1.4rem', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.4rem', WebkitTextFillColor: 'initial', background: 'none', marginBottom: '0.5rem' }}>
            🦕 EcoSaur Diagnostic Insights
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', marginTop: '1rem', marginBottom: '1rem' }}>
            <div style={{ background: 'var(--input-bg)', padding: '0.85rem', borderRadius: '14px', border: '1px solid var(--input-border)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', fontWeight: 600 }}>Frequent Craving</span>
              <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '0.15rem', display: 'block' }}>{insights.common_category}</span>
            </div>
            <div style={{ background: 'var(--input-bg)', padding: '0.85rem', borderRadius: '14px', border: '1px solid var(--input-border)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', fontWeight: 600 }}>Ultra-Processed Ratio</span>
              <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ef4444', marginTop: '0.15rem', display: 'block' }}>{insights.ultra_processed_ratio}% NOVA 4</span>
            </div>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {insights.additive_trends && insights.additive_trends.map((t: string, idx: number) => (
              <p key={idx} style={{ fontSize: '0.85rem', color: 'var(--text-main)', lineHeight: '1.4' }}>
                💡 <strong>Weekly Trend:</strong> {t}
              </p>
            ))}
          </div>

          {insights.swap_suggestions && insights.swap_suggestions.length > 0 && (
            <div style={{ 
              marginTop: '1.25rem', 
              paddingTop: '1rem', 
              borderTop: '1px solid var(--primary-glow)', 
              textAlign: 'left'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--primary)', fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: '0.5rem' }}>
                ⭐ Personalized Healthier Swap
              </span>
              {insights.swap_suggestions.map((suggestion: any, idx: number) => (
                <div key={idx} style={{ background: 'var(--input-bg)', border: '1px solid var(--input-border)', padding: '0.75rem', borderRadius: '12px', fontSize: '0.85rem', lineHeight: '1.4' }}>
                  Replace <strong style={{ color: '#fb923c' }}>{suggestion.original}</strong> with <strong style={{ color: 'var(--primary)' }}>{suggestion.swap}</strong>.
                  <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.2rem' }}>
                    Reason: {suggestion.reason}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {isLoading ? (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
          <p style={{ color: 'var(--text-muted)' }}>Reading secure history records...</p>
          <div style={{ marginTop: '1.5rem' }}>
            <div className="skeleton-line" style={{ width: '90%' }}></div>
            <div className="skeleton-line" style={{ width: '75%' }}></div>
          </div>
        </div>
      ) : history.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
          <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>📂</span>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: 'var(--text-main)' }}>No past scans found</h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>Your analyzed packaged snacks will be listed here.</p>
          <Link href="/scan" className="btn-primary" style={{ maxWidth: '250px', margin: '0 auto' }}>
            Scan Your First Item
          </Link>
        </div>
      ) : (
        history.map((item, idx) => {
          const letter = getGradeLetter(item.grade, item.score);
          const colorClass = `c-grade-${letter}`;
          
          return (
            <div key={idx} className="card" style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '1.25rem', 
              padding: '1.25rem 1.5rem'
            }}>
              <div 
                className={`comparison-grade ${colorClass}`} 
                style={{ width: '54px', height: '54px', fontSize: '1.4rem', flexShrink: 0, fontWeight: 800 }}
              >
                {letter}
              </div>
              
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-main)' }}>Score: {item.score}/100</h3>
                {item.name && (
                  <p style={{ margin: '0.2rem 0', fontWeight: 600, color: 'var(--primary)', fontSize: '0.9rem' }}>
                    🥗 Alternative: {item.name}
                  </p>
                )}
                <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  🕒 {new Date(item.date).toLocaleString()}
                </p>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
