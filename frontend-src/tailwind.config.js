/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontSize: {
        base: "13px",
      },
      spacing: {
        1: "4px",
        2: "8px",
        3: "12px",
        4: "16px",
        5: "20px",
        6: "24px",
        8: "32px",
        10: "40px",
        12: "48px",
      },
      colors: {
        ew: {
          blue: "#1a73e8",
          "blue-light": "#e8f0fe",
          "blue-dark": "#1557b0",
          gray: "#f8f9fa",
          "gray-border": "#dadce0",
          "gray-text": "#5f6368",
        },
      },
    },
  },
  plugins: [],
};
