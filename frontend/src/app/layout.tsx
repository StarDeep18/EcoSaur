import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'EcoSaur - Food Ingredient Analyzer',
  description: 'Understand what you eat. Friendly, clear food analysis.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="header">
          <Link href="/" className="logo">
            🦕 EcoSaur
          </Link>
          <nav style={{ display: 'flex', gap: '1rem', fontWeight: 500 }}>
            <Link href="/scan">Scan</Link>
            <Link href="/history">History</Link>
          </nav>
        </header>
        <main>
          {children}
        </main>
      </body>
    </html>
  );
}
