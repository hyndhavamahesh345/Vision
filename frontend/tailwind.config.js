/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'pulse-slow': 'pulse-slow 8s ease-in-out infinite',
        'sweep': 'sweep 3s infinite',
      },
    },
  },
  plugins: [],
}
