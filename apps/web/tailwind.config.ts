import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        motec: {
          bg: "#070A12",
          panel: "#0F1626",
          border: "#1E293B",
          accent: "#38BDF8",
          emerald: "#10B981",
          amber: "#F59E0B",
          danger: "#EF4444",
        },
      },
    },
  },
  plugins: [],
};

export default config;
