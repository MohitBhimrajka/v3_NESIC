import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#000000',
        white: '#ffffff',
        navy: '#000b37',
        lime: '#85c20b',
        'gray-dk': '#474747',
        'gray-lt': '#c7c7c7',
        blue: '#8289ec',
        'lime-lt': '#c3fb54',
        orange: '#ff9a5a',
        purple: '#b181ff',
        cyan: '#31b8e1',
        pink: '#ff94a8',
      },
      keyframes: {
        'gradient-x': {
          '0%, 100%': { 'background-position': '0% 50%' },
          '50%': { 'background-position': '100% 50%' },
        },
        'indeterminate-progress': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'gradient-x': 'gradient-x 15s ease infinite',
        'indeterminate-progress': 'indeterminate-progress 1.5s ease-in-out infinite',
      },
      backgroundSize: {
        'auto': 'auto',
        'cover': 'cover',
        'contain': 'contain',
        '200%': '200%',
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
}

export default config 