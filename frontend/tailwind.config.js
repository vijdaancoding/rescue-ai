/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1a1a1a',
        secondary: '#f5f5f5',
        accent: '#007bff',
        danger: '#dc3545',
        success: '#28a745',
        warning: '#ffc107',
      }
    },
  },
  plugins: [],
}
