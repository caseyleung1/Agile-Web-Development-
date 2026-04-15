/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html", "./static/**/*.js"],
  theme: {
    extend: {
      colors: {
        brand: {
          purple: "#8A3FFC",
          purpledeep: "#5B21B6",
          orange: "#FF7648",
          sky: "#45B5F5",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
