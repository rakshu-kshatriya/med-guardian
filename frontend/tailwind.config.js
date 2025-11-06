/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,html}",
    "../backend/templates/**/*.html",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Roboto', 'system-ui', 'sans-serif'],
      },
      colors: {
        white: {
          10: 'rgba(255,255,255,0.10)',
          20: 'rgba(255,255,255,0.20)'
        }
      },
    },
  },
  safelist: [
    'text-white',
    'bg-white',
    'border-white',
    'text-black',
    'bg-black',
  ],
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

