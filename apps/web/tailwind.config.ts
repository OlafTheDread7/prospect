import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f4f8",
          100: "#d9e4ef",
          500: "#2e5a88",
          700: "#1f3a5f",
          900: "#142845",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
