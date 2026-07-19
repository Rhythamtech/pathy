import type { Config } from 'tailwindcss'
import tailwindcssAnimate from 'tailwindcss-animate'

export default {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        accent: 'hsl(var(--accent) / <alpha-value>)',
        primary: 'hsl(var(--primary) / <alpha-value>)',
        'on-primary': 'hsl(var(--on-primary) / <alpha-value>)',
        ink: 'hsl(var(--ink) / <alpha-value>)',
        'ink-deep': 'hsl(var(--ink-deep) / <alpha-value>)',
        charcoal: 'hsl(var(--charcoal) / <alpha-value>)',
        body: 'hsl(var(--body) / <alpha-value>)',
        mute: 'hsl(var(--mute) / <alpha-value>)',
        stone: 'hsl(var(--stone) / <alpha-value>)',
        ash: 'hsl(var(--ash) / <alpha-value>)',
        canvas: 'hsl(var(--canvas) / <alpha-value>)',
        'surface-soft': 'hsl(var(--surface-soft) / <alpha-value>)',
        'surface-card': 'hsl(var(--surface-card) / <alpha-value>)',
        'surface-dark': 'hsl(var(--surface-dark) / <alpha-value>)',
        'surface-dark-elevated': 'hsl(var(--surface-dark-elevated) / <alpha-value>)',
        hairline: 'hsl(var(--hairline) / <alpha-value>)',
        'hairline-strong': 'hsl(var(--hairline-strong) / <alpha-value>)',
        'on-dark': 'hsl(var(--on-dark) / <alpha-value>)',
        'on-dark-mute': 'hsl(var(--on-dark-mute) / <alpha-value>)',
        warning: 'hsl(34 100% 50%)',
        danger: 'hsl(4 100% 60%)',
        success: 'hsl(143 70% 50%)'
      },
      fontFamily: {
        sans: 'var(--font-jetbrains-mono)',
        serif: 'var(--font-newsreader)',
        mono: 'var(--font-jetbrains-mono)'
      },
      borderRadius: {
        none: '0px',
        sm: '4px',
        md: '8px',
        lg: '16px',
        full: '9999px'
      }
    }
  },
  plugins: [tailwindcssAnimate]
} satisfies Config
