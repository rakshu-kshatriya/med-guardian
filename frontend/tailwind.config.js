/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Roboto', 'system-ui', 'sans-serif'],
      },
      colors: {
        /* Provide a couple of convenient opacity shades for white so classes like
           border-white/10 map consistently in environments where the JIT
           parser may be strict. These are optional and won't override 'white'. */
        white: {
          10: 'rgba(255,255,255,0.10)',
          20: 'rgba(255,255,255,0.20)'
        }
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

