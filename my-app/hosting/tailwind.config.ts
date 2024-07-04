import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: '#000080',
        dark_navy: "#00003b",
        grey_navy: "#141441",
        white: "#ffffff",
        light_blue: "#5E6E9E",
        main_white: "#E5E9EF",
        sub_grey: "#C2CAD8", 
        sub_sub_grey: "#909CB2",
        midjourney_navy: "#0A092A",
        briefly_box: "#0D1D3A"
      },
    },
  },
  plugins: [],
};
export default config;
