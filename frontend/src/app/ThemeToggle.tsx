'use client';

import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  // Sync state on component mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'dark' | 'light' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const initialTheme = prefersDark ? 'dark' : 'light';
      setTheme(initialTheme);
      document.documentElement.setAttribute('data-theme', initialTheme);
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
    localStorage.setItem('theme', nextTheme);
  };

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle Theme Mode"
      style={{
        background: 'var(--input-bg)',
        border: '1px solid var(--input-border)',
        color: 'var(--text-main)',
        borderRadius: '12px',
        padding: '0.45rem 0.85rem',
        fontSize: '0.85rem',
        fontWeight: 600,
        cursor: 'pointer',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        outline: 'none',
      }}
      onMouseOver={(e) => {
        e.currentTarget.style.borderColor = 'var(--primary)';
        e.currentTarget.style.transform = 'scale(1.03)';
      }}
      onMouseOut={(e) => {
        e.currentTarget.style.borderColor = 'var(--input-border)';
        e.currentTarget.style.transform = 'scale(1)';
      }}
    >
      {theme === 'dark' ? '☀️ Light' : '🌙 Obsidian'}
    </button>
  );
}
