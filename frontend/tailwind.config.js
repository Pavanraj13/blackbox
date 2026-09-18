/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#070a13',
          800: '#0f172a',
          700: '#1e293b',
          600: '#334155'
        },
        cyan: {
          400: '#38bdf8',
          500: '#06b6d4',
        }
      }
    },
  },
  plugins: [],
}
