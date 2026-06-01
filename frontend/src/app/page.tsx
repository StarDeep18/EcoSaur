import Link from 'next/link';

export default function Home() {
  return (
    <div className="container animate-fade-in" style={{ textAlign: 'center', paddingTop: '3.5rem' }}>
      <span className="carousel-badge" style={{ marginBottom: '1rem', background: 'rgba(16, 185, 129, 0.12)', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.25)', fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
        🦕 INTELLIGENT FOOD WELLNESS
      </span>
      
      <h1 className="title" style={{ fontSize: '3.25rem', marginBottom: '1rem' }}>
        Eat Smarter. <br />Not Harder.
      </h1>
      
      <p className="subtitle" style={{ fontSize: '1.1rem', maxWidth: '480px', margin: '0 auto 2.5rem auto', color: 'var(--text-muted)', lineHeight: '1.7' }}>
        Scan any packaged food label. We deterministically evaluate the nutritional quality, demystify complex chemical additives, and rank authentic homemade alternatives.
      </p>
      
      <div className="card card-glow-primary" style={{ padding: '2.5rem 1.75rem' }}>
        <h2 style={{ marginBottom: '1.25rem', fontSize: '1.35rem', fontWeight: 700, color: 'var(--text-main)' }}>
          Evaluate Your Packaged Food
        </h2>
        
        <Link href="/scan" className="btn-primary" style={{ marginBottom: '0.85rem' }}>
          📷 Launch Ingredient Label Scanner
        </Link>
        <Link href="/history" className="btn-secondary">
          📂 View Analysis History
        </Link>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginTop: '1.5rem', textAlign: 'left' }}>
        <div className="card" style={{ padding: '1rem', marginBottom: 0 }}>
          <span style={{ fontSize: '1.5rem', display: 'block', marginBottom: '0.5rem' }}>🛡️</span>
          <strong style={{ fontSize: '0.85rem', color: 'var(--text-main)', display: 'block' }}>Zero Brand Shaming</strong>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>Purely objective, evidence-based details.</span>
        </div>
        
        <div className="card" style={{ padding: '1rem', marginBottom: 0 }}>
          <span style={{ fontSize: '1.5rem', display: 'block', marginBottom: '0.5rem' }}>⚖️</span>
          <strong style={{ fontSize: '0.85rem', color: 'var(--text-main)', display: 'block' }}>Rule-Based Scoring</strong>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>No randomly made-up AI health grades.</span>
        </div>
        
        <div className="card" style={{ padding: '1rem', marginBottom: 0 }}>
          <span style={{ fontSize: '1.5rem', display: 'block', marginBottom: '0.5rem' }}>🍳</span>
          <strong style={{ fontSize: '0.85rem', color: 'var(--text-main)', display: 'block' }}>Indian Alternatives</strong>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>Curated home staples matching cravings.</span>
        </div>
      </div>

      <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '3.5rem', lineHeight: '1.5' }}>
        EcoSaur respects your health profile goals. We do not provide clinical diagnostics or medical advice.
      </p>
    </div>
  );
}
