/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // GitLab brand palette
        gitlab: {
          orange: "#FC6D26",
          red:    "#E24329",
          purple: "#6B4FBB",
          dark:   "#1F1E24",
        },
        // Surface scale — used throughout
        surface: {
          50:  "#FAFAF9",
          100: "#F4F3F0",
          200: "#E8E6E1",
          700: "#3D3B45",
          800: "#2D2B35",
          900: "#1F1E24",
          950: "#141319",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "fade-in":    "fadeIn 0.2s ease-out",
        "slide-up":   "slideUp 0.25s ease-out",
        "pulse-dot":  "pulseDot 1.4s ease-in-out infinite",
        "typing":     "typing 1s ease-in-out infinite",
      },
      keyframes: {
        fadeIn:   { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp:  { from: { opacity: 0, transform: "translateY(8px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        pulseDot: { "0%,100%": { opacity: 0.3, transform: "scale(0.8)" }, "50%": { opacity: 1, transform: "scale(1.1)" } },
      },
    },
  },
  plugins: [],
};