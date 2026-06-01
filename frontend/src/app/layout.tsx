import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import ThemeToggle from './ThemeToggle';

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
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var saved = localStorage.getItem('theme');
                  if (saved) {
                    document.documentElement.setAttribute('data-theme', saved);
                  } else {
                    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body suppressHydrationWarning>
        <header className="header">
          <Link href="/" className="logo">
            🦕 EcoSaur
          </Link>
          <nav style={{ display: 'flex', gap: '1.25rem', alignItems: 'center', fontWeight: 600 }}>
            <Link href="/scan" className="nav-link">Scan</Link>
            <Link href="/history" className="nav-link">History</Link>
            <ThemeToggle />
          </nav>
        </header>
        <main>
          {children}
        </main>
      </body>
    </html>
  );
}
