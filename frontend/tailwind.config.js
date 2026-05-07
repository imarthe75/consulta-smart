/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#002A4C',
                primaryLight: '#003a66',
                secondary: '#BDC3C7',
                accent: '#C0C0C0',
                textmain: '#002A4C',
                success: '#10B981',
                danger: '#EF4444',
                warning: '#F59E0B',
                info: '#3B82F6',
            },
            fontFamily: {
                sans: ['Open Sans', 'Inter', 'sans-serif'],
                heading: ['Montserrat', 'Roboto', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
