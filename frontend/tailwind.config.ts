import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#F7F9FC",
        surface: "#FFFFFF",
        subtle: "#F1F5F9",
        video: "#0E1117",
        primary: { DEFAULT: "#2563EB", hover: "#1D4ED8", soft: "#DBEAFE" },
        success: { DEFAULT: "#16866F", soft: "#DDF7EF" },
        warning: { DEFAULT: "#D97706", soft: "#FFF2D8" },
        danger: { DEFAULT: "#DC3944", soft: "#FEE2E2" },
        ink: { DEFAULT: "#172033", muted: "#667085", faint: "#98A2B3" },
        border: "#DDE3EC",
        focus: "#60A5FA",
      },
      fontFamily: { sans: ["Segoe UI", "Inter", "Arial", "sans-serif"] },
      boxShadow: { card: "0 8px 28px rgba(23, 32, 51, 0.06)" },
      borderRadius: { xl: "14px" },
    },
  },
  plugins: [],
} satisfies Config;
