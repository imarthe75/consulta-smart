/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#1E40AF',
                secondary: '#7C3AED',
                accent: '#F59E0B',
                success: '#10B981',
                danger: '#EF4444',
                warning: '#F59E0B',
                info: '#3B82F6',
            },
            fontFamily: {
                sans: ['system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
