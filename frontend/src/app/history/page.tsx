'use client';
import { useEffect, useState } from 'react';

export default function HistoryPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        const res = await fetch(`${API_URL}/scan/history`);
        if (res.ok) {
          const data = await res.json();
          if (data && Array.isArray(data) && data.length > 0) {
            const formatted = data.map((item: any) => ({
              date: item.date,
              score: item.score,
              grade: item.grade,
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

  return (
    <div className="container">
      <h1 className="title">Scan History</h1>
      <p className="subtitle">Your recent food analyses will appear here.</p>
      
      {isLoading ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <p style={{ color: 'var(--text-muted)' }}>Loading scan history...</p>
        </div>
      ) : history.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <p style={{ color: 'var(--text-muted)' }}>You haven't scanned anything yet.</p>
        </div>
      ) : (
        history.map((item, idx) => (
          <div key={idx} className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem' }}>
            <div className={`grade-dial grade-${item.grade}`} style={{ width: '60px', height: '60px', fontSize: '1.5rem', margin: 0 }}>
              {item.grade}
            </div>
            <div>
              <h3 style={{ margin: 0 }}>Score: {item.score}/100</h3>
              {item.name && <p style={{ margin: '0.2rem 0', fontWeight: 500, color: 'var(--primary-dark)' }}>{item.name}</p>}
              <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                {new Date(item.date).toLocaleString()}
              </p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

