'use client';
import { useEffect, useState } from 'react';

export default function HistoryPage() {
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    const savedHistory = localStorage.getItem('ecosaur_history');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  return (
    <div className="container">
      <h1 className="title">Scan History</h1>
      <p className="subtitle">Your recent food analyses will appear here.</p>
      
      {history.length === 0 ? (
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
              <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                {new Date(item.date).toLocaleDateString()}
              </p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
