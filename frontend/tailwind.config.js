/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', "monospace"],
      },
      colors: {
        falcon: {
          bg: "#0a0e17",
          surface: "#111827",
          border: "#1f2937",
          accent: "#22d3ee",
          green: "#10b981",
          red: "#ef4444",
          muted: "#6b7280",
        },
      },
    },
  },
  plugins: [],
};
