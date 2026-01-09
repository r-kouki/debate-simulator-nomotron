/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        xp: {
          blue: '#0054E3',
          'blue-light': '#4285F4',
          'blue-gradient-start': '#0054E3',
          'blue-gradient-end': '#3F8CF3',
          gray: '#ECE9D8',
          'gray-dark': '#D4D0C8',
          'gray-light': '#F1EFE2',
          'taskbar-green': '#1F9F3A',
          'taskbar-blue': '#245EDC',
          'text-disabled': '#808080',
        },
      },
      fontFamily: {
        tahoma: ['Tahoma', 'Segoe UI', 'sans-serif'],
      },
      fontSize: {
        xp: {
          xs: '11px',
          sm: '12px',
          md: '13px',
          lg: '16px',
          xl: '20px',
        },
      },
      boxShadow: {
        xp: '0 0 0 1px rgba(0, 0, 0, 0.2), 0 4px 8px rgba(0, 0, 0, 0.3)',
        'xp-button': 'inset -1px -1px 0 #808080, inset 1px 1px 0 #fff',
        'xp-button-active': 'inset 1px 1px 0 #808080, inset -1px -1px 0 #fff',
        'xp-inset': 'inset 1px 1px 0 #808080, inset -1px -1px 0 #fff',
      },
    },
  },
  plugins: [],
};
