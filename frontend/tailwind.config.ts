import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        surface: '#111111',
        border: '#222222',
        accent: '#f59e0b',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}

export default config
