import Link from 'next/link';

export default function Home() {
  return (
    <div className="container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
      <h1 className="title">Eat Smarter, <br />Not Harder.</h1>
      <p className="subtitle" style={{ fontSize: '1.2rem', maxWidth: '400px', margin: '0 auto 2rem auto' }}>
        Snap a picture of any ingredient label. We'll translate the chemicals into plain English and suggest healthy homemade alternatives.
      </p>
      
      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>Ready to check your food?</h2>
        <Link href="/scan" className="btn-primary" style={{ marginBottom: '1rem' }}>
          Scan an Ingredient Label
        </Link>
        <Link href="/history" className="btn-secondary">
          View Past Scans
        </Link>
      </div>

      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '2rem' }}>
        EcoSaur does not provide medical advice. We just help you make informed choices.
      </p>
    </div>
  );
}
