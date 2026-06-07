/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./App.{js,jsx,ts,tsx}",
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
    "./screens/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Obsidian Dark Theme
        obsidian: {
          bg: '#09090A',
          card: '#161618',
          border: '#28282B',
          text: '#F2F2F7',
          muted: '#8A8A93',
        },
        // Cream Light Theme
        cream: {
          bg: '#FDFBF7',
          card: '#F6F3EC',
          border: '#EBE6DA',
          text: '#1C1C1E',
          muted: '#636366',
        },
        // Premium Emerald Accent
        emerald: {
          DEFAULT: '#10B981',
          dark: '#059669',
          light: '#34D399',
          soft: '#E6F4EA',
        }
      },
      fontFamily: {
        // Fallbacks (standard in mobile styling)
        sans: ["System", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      }
    },
  },
  plugins: [],
}
