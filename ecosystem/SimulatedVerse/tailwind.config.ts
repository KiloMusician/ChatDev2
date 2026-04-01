import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./client/index.html", "./client/src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      colors: {
        // Culture-ship inspired palette
        quantum: {
          50: 'hsl(var(--quantum-50))',
          100: 'hsl(var(--quantum-100))',
          200: 'hsl(var(--quantum-200))',
          300: 'hsl(var(--quantum-300))',
          400: 'hsl(var(--quantum-400))',
          500: 'hsl(var(--quantum-500))',
          600: 'hsl(var(--quantum-600))',
          700: 'hsl(var(--quantum-700))',
          800: 'hsl(var(--quantum-800))',
          900: 'hsl(var(--quantum-900))',
        },
        neural: {
          50: 'hsl(var(--neural-50))',
          100: 'hsl(var(--neural-100))',
          200: 'hsl(var(--neural-200))',
          300: 'hsl(var(--neural-300))',
          400: 'hsl(var(--neural-400))',
          500: 'hsl(var(--neural-500))',
          600: 'hsl(var(--neural-600))',
          700: 'hsl(var(--neural-700))',
          800: 'hsl(var(--neural-800))',
          900: 'hsl(var(--neural-900))',
        },
        energy: {
          50: 'hsl(var(--energy-50))',
          400: 'hsl(var(--energy-400))',
          500: 'hsl(var(--energy-500))',
          600: 'hsl(var(--energy-600))',
        },
        void: {
          DEFAULT: 'hsl(var(--void))',
          foreground: 'hsl(var(--void-foreground))',
        },
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        chart: {
          "1": "var(--chart-1)",
          "2": "var(--chart-2)",
          "3": "var(--chart-3)",
          "4": "var(--chart-4)",
          "5": "var(--chart-5)",
        },
        sidebar: {
          DEFAULT: "var(--sidebar-background)",
          foreground: "var(--sidebar-foreground)",
          primary: "var(--sidebar-primary)",
          "primary-foreground": "var(--sidebar-primary-foreground)",
          accent: "var(--sidebar-accent)",
          "accent-foreground": "var(--sidebar-accent-foreground)",
          border: "var(--sidebar-border)",
          ring: "var(--sidebar-ring)",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        serif: ["var(--font-serif)"],
        mono: ["var(--font-mono)"],
        display: ["var(--font-display)", "system-ui"],
        body: ["var(--font-body)", "system-ui"],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
        '144': '36rem',
      },
      animation: {
        'pulse-quantum': 'pulse-quantum 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'slide-in': 'slide-in 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
        'scale-in': 'scale-in 0.2s ease-out',
        'neural-pulse': 'neural-pulse 3s ease-in-out infinite',
        'data-flow': 'data-flow 4s linear infinite',
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        'pulse-quantum': {
          '0%, 100%': {
            opacity: '1',
            transform: 'scale(1)',
            filter: 'brightness(1)',
          },
          '50%': {
            opacity: '0.8',
            transform: 'scale(1.05)',
            filter: 'brightness(1.2)',
          },
        },
        'glow': {
          from: { 'text-shadow': '0 0 20px currentColor', filter: 'brightness(1)' },
          to: { 'text-shadow': '0 0 30px currentColor, 0 0 40px currentColor', filter: 'brightness(1.3)' },
        },
        'slide-in': {
          from: { opacity: '0', transform: 'translateY(-10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.9)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'neural-pulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
        'data-flow': {
          from: { transform: 'translateX(-100%)', opacity: '0' },
          '10%, 90%': { opacity: '1' },
          to: { transform: 'translateX(100%)', opacity: '0' },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/typography")],
} satisfies Config;
