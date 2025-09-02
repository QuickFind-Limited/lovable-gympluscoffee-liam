# Design System Documentation

## Overview

The Source application implements a comprehensive design system built on **shadcn/ui** component library with **Tailwind CSS**, featuring a modern, accessible, and highly customizable interface. The design system emphasizes Apple-inspired aesthetics with smooth animations, consistent spacing, and semantic color usage.

## Core Technologies

- **shadcn/ui**: 50+ pre-built components
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Class Variance Authority (CVA)**: Component variant management
- **next-themes**: Dark/light mode theming
- **DM Sans**: Primary typography
- **Lucide React**: Icon system

## Design Tokens

### Color System

The design system uses CSS custom properties for dynamic theming with HSL color values:

#### Brand Colors
```css
brand: {
  50: '#fff0e5',   /* Lightest orange tint */
  100: '#ffe0cc',  /* Light warmth */
  200: '#ffc199',  /* Soft orange */
  300: '#ffa366',  /* Medium orange */
  400: '#ff8433',  /* Vibrant orange */
  500: '#ff6600',  /* Primary brand (Source orange) */
  600: '#cc5200',  /* Darker orange */
  700: '#993d00',  /* Deep orange */
  800: '#662900',  /* Very dark orange */
  900: '#331400',  /* Darkest orange */
}
```

#### Semantic Colors
```css
/* Light Theme */
--primary: 24 100% 50%;        /* Brand orange (#ff6600) */
--secondary: 210 40% 96.1%;    /* Light gray */
--background: 0 0% 100%;       /* Pure white */
--foreground: 222.2 84% 4.9%;  /* Near black */
--muted: 210 40% 96.1%;        /* Muted backgrounds */
--border: 214.3 31.8% 91.4%;   /* Light borders */
--input: 214.3 31.8% 91.4%;    /* Input backgrounds */
--destructive: 0 84.2% 60.2%;  /* Error red */

/* Dark Theme */
--background: 0 0% 13%;        /* Dark gray (#212121) */
--foreground: 0 0% 95%;        /* Light text */
--card: 0 0% 13%;              /* Card backgrounds */
--popover: 0 0% 19%;           /* Popover backgrounds (#303030) */
--input: 0 0% 19%;             /* Input backgrounds */
--border: 0 0% 15%;            /* Dark borders */
--muted: 0 0% 15%;             /* Muted dark */
```

#### Sidebar Colors
```css
/* Light Sidebar */
--sidebar-background: 0 0% 98%;    /* Light sidebar */
--sidebar-primary: 240 5.9% 10%;   /* Dark text */
--sidebar-accent: 240 4.8% 95.9%;  /* Hover states */

/* Dark Sidebar */
--sidebar-background: 0 0% 9%;     /* Very dark (#171717) */
--sidebar-primary: 224.3 76.3% 48%; /* Blue accent */
--sidebar-accent: 0 0% 15%;        /* Dark hover */
```

### Typography

#### Font Family
```css
font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
```

DM Sans provides excellent readability and modern appearance with proper font feature settings:
```css
font-feature-settings: "rlig" 1, "calt" 1;
```

#### Typography Scale
- **Headings**: Range from `text-xs` to `text-6xl`
- **Body**: `text-sm` (14px) and `text-base` (16px)
- **Weight**: `font-medium` (500), `font-semibold` (600), `font-bold` (700)
- **Tracking**: `tracking-tight` for headings, normal for body text

### Spacing & Layout

#### Border Radius
```css
--radius: 0.75rem;              /* Base radius (12px) */
rounded-md: calc(var(--radius) - 2px);  /* 10px */
rounded-sm: calc(var(--radius) - 4px);  /* 8px */
rounded-lg: var(--radius);              /* 12px */
rounded-2xl: 1rem;                      /* 16px */
rounded-3xl: 1.5rem;                    /* 24px */
```

#### Container
```css
container: {
  center: true,
  padding: '2rem',
  screens: {
    '2xl': '1400px'
  }
}
```

## Component Architecture

### UI Components (50+ Available)

#### Core Components
- **Button**: 6 variants, 4 sizes with CVA
- **Card**: Flexible container with header, content, footer
- **Input**: Consistent form inputs with focus states
- **Badge**: Status indicators with semantic colors
- **Alert**: Success/error messaging with icons
- **Dialog**: Modal overlays and confirmations
- **Tabs**: Navigation and content switching
- **Select**: Dropdown selections with scrolling
- **Table**: Data display with sorting/filtering
- **Toast**: Notification system

#### Navigation Components
- **Sidebar**: Collapsible navigation with themes
- **Breadcrumb**: Path navigation
- **Navigation Menu**: Top-level navigation
- **Pagination**: Content pagination

#### Form Components
- **Form**: Form validation and structure
- **Label**: Accessible form labels
- **Checkbox**: Selection inputs
- **Radio Group**: Single-select options
- **Switch**: Toggle controls
- **Slider**: Range inputs
- **Textarea**: Multi-line text inputs

#### Feedback Components
- **Progress**: Loading indicators
- **Skeleton**: Loading placeholders
- **Sonner**: Advanced toast notifications
- **Tooltip**: Contextual help
- **Hover Card**: Rich hover content

#### Layout Components
- **Accordion**: Collapsible content sections
- **Collapsible**: Show/hide content
- **Resizable**: Adjustable panels
- **Scroll Area**: Custom scrollbars
- **Separator**: Visual content dividers
- **Sheet**: Slide-out panels

### Component Variants with CVA

#### Button Variants
```typescript
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
  }
)
```

#### Badge Variants
```typescript
const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
      },
    },
  }
)
```

## Animation System

### Custom Keyframes
```css
@keyframes fade-in {
  0% { opacity: 0; transform: translateY(10px); }
  100% { opacity: 1; transform: translateY(0); }
}

@keyframes fade-out {
  0% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(10px); }
}

@keyframes scale-in {
  0% { transform: scale(0.95); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes slide-in-left {
  0% { transform: translateX(-100%); opacity: 0; }
  50% { opacity: 0.6; }
  100% { transform: translateX(0); opacity: 1; }
}

@keyframes slide-to-right {
  0% { transform: translateX(0) scale(1); opacity: 1; }
  100% { transform: translateX(0) scale(0.98); opacity: 0.95; }
}
```

### Animation Classes
```css
.animate-fade-in: fade-in 0.4s ease-out
.animate-fade-out: fade-out 0.4s ease-out
.animate-scale-in: scale-in 0.3s ease-out
.animate-float: float 6s ease-in-out infinite
.animate-slide-in-left: slide-in-left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)
.animate-slide-to-right: slide-to-right 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)
```

### Transition Components

#### LoginTransition
- **Purpose**: Smooth authentication flow transition
- **Features**: Progress bar animation, brand reveal
- **Duration**: 2-3 seconds with multiple phases
- **Implementation**: React component with useEffect timing

#### EmailSendingTransition
- **Purpose**: Purchase order email flow
- **Features**: Step-by-step progress with icons
- **Phases**: Generate → Attach → Send → Complete
- **Duration**: Staggered timing (1.5s, 2s, 2.5s intervals)

#### OrderPlacedTransition
- **Purpose**: Order processing workflow
- **Features**: Multi-phase progression
- **Phases**: Placing → Sending → Syncing → Complete
- **Animation**: Fade-in with slide-up effects

## Apple-Inspired Patterns

### Custom CSS Classes
```css
.apple-input {
  @apply rounded-2xl border-0 focus:ring-2 transition-all duration-200;
}

.apple-button {
  @apply rounded-2xl font-semibold transition-all duration-200 shadow-lg;
}

.apple-card {
  @apply rounded-3xl shadow-lg border-0 backdrop-blur-sm;
}
```

### Authentication Styles
```css
.auth-card {
  @apply bg-white dark:bg-gray-900 rounded-3xl shadow-xl overflow-hidden 
         backdrop-blur-lg border border-gray-100 dark:border-gray-800 relative z-10;
}

.auth-tab {
  @apply text-gray-600 dark:text-gray-400 py-3 px-5 text-center font-medium 
         relative transition-all duration-300 cursor-pointer;
}

.auth-tab.active::after {
  content: "";
  @apply absolute bottom-0 left-0 w-full h-0.5 bg-brand-500 dark:bg-brand-400 
         transition-all duration-300;
}

.auth-button {
  @apply w-full py-3.5 px-4 flex items-center justify-center rounded-2xl 
         font-medium transition-all duration-300 bg-brand-500 text-white 
         hover:bg-brand-600 focus:ring-4 focus:ring-brand-500/30 
         transform hover:-translate-y-0.5 shadow-lg;
}
```

### Form Input Patterns
```css
.form-input {
  @apply w-full h-12 px-4 border rounded-2xl bg-white/70 backdrop-blur-sm 
         transition-all duration-300 outline-none border-gray-200 
         focus:border-brand-400 focus:ring-2 focus:ring-brand-400/30 text-left;
}
```

## Theme System

### Theme Toggle Implementation
```typescript
export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  
  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  return (
    <Button variant="outline" size="icon" onClick={toggleTheme}>
      <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
```

### Dark Mode Support
- **Strategy**: CSS custom properties with class-based toggling
- **Scope**: All components support both light and dark themes
- **Transitions**: Smooth theme switching with CSS transitions
- **Icons**: Animated theme toggle with sun/moon icons

## Responsive Design

### Breakpoint Strategy
```css
screens: {
  'sm': '640px',
  'md': '768px', 
  'lg': '1024px',
  'xl': '1280px',
  '2xl': '1400px'
}
```

### Mobile-First Approach
- Base styles target mobile devices
- Progressive enhancement for larger screens
- Touch-friendly interactive elements (minimum 44px)
- Optimized typography scales for readability

### Responsive Patterns
```css
/* Mobile-first input styling */
.form-input {
  @apply h-12 text-base md:text-sm; /* Larger text on mobile */
}

/* Container responsiveness */
.container {
  @apply px-4 sm:px-6 lg:px-8;
}
```

## Accessibility Implementation

### ARIA Standards
- **Semantic HTML**: Proper heading hierarchy, landmarks
- **Screen Reader Support**: `sr-only` utility classes for hidden labels
- **Focus Management**: Clear focus indicators with ring utilities
- **Keyboard Navigation**: Tab order and keyboard shortcuts

### Accessibility Features
```css
/* Focus indicators */
focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2

/* Screen reader content */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

### Color Contrast
- **WCAG AA Compliance**: All text meets minimum contrast ratios
- **High Contrast Support**: System respect user preferences
- **Color Blindness**: No information conveyed through color alone

## Component Standards

### Naming Conventions
- **Components**: PascalCase (e.g., `ButtonVariants`, `AlertDialog`)
- **Props**: camelCase (e.g., `variant`, `size`, `className`)
- **CSS Classes**: kebab-case with BEM-like structure
- **File Names**: PascalCase for components, kebab-case for utilities

### Component Structure
```typescript
// Standard component pattern
const Component = React.forwardRef<HTMLElement, ComponentProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <Element
        ref={ref}
        className={cn(componentVariants({ variant, size }), className)}
        {...props}
      />
    )
  }
)
Component.displayName = "Component"
```

### Props Pattern
```typescript
interface ComponentProps
  extends React.HTMLAttributes<HTMLElement>,
    VariantProps<typeof componentVariants> {
  asChild?: boolean
}
```

## Utility Functions

### Class Name Utility
```typescript
// cn function combines clsx and tailwind-merge
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Benefits:**
- Handles conditional classes
- Merges Tailwind conflicts intelligently
- Optimizes final CSS output

## Performance Considerations

### Bundle Optimization
- Tree-shaking friendly component exports
- Lazy loading for large components
- CSS-in-JS avoided for better caching
- Minimal JavaScript footprint

### Animation Performance
- Hardware acceleration with `transform` and `opacity`
- Reduced motion support via `prefers-reduced-motion`
- Optimized keyframes for 60fps performance

### Loading States
- Skeleton components for content loading
- Progressive image loading
- Optimistic UI updates

## Development Guidelines

### Component Development
1. **Start with shadcn/ui**: Use existing components when possible
2. **Extend, Don't Replace**: Customize through className props
3. **Maintain Consistency**: Follow established patterns
4. **Test Accessibility**: Verify keyboard navigation and screen readers
5. **Document Variants**: Use CVA for component variations

### Styling Best Practices
1. **Utility-First**: Prefer Tailwind classes over custom CSS
2. **Semantic Classes**: Use design tokens over hardcoded values
3. **Responsive Design**: Mobile-first with progressive enhancement
4. **Animation Sparingly**: Enhance UX without overwhelming users
5. **Performance**: Consider bundle size and runtime performance

### Design Token Usage
```css
/* Preferred: Using design tokens */
.component {
  @apply bg-background text-foreground border-border;
}

/* Avoid: Hardcoded values */
.component {
  @apply bg-white text-black border-gray-200;
}
```

## Future Enhancements

### Planned Improvements
- **Component Storybook**: Visual component documentation
- **Design System Package**: Standalone npm package
- **Advanced Animations**: Framer Motion integration
- **Micro-interactions**: Enhanced user feedback
- **A11y Testing**: Automated accessibility testing

### Scalability Considerations
- **CSS Custom Properties**: Expandable theme system
- **Component Composition**: Flexible component architecture
- **Performance Monitoring**: Animation and bundle size tracking
- **Cross-browser Testing**: Comprehensive browser support

---

## Quick Reference

### Essential Classes
```css
/* Layout */
.container, .flex, .grid, .space-y-4

/* Typography */
.text-sm, .font-medium, .tracking-tight

/* Colors */
.bg-background, .text-foreground, .border-border

/* Interactive */
.hover:bg-accent, .focus-visible:ring-2, .transition-colors

/* Spacing */
.p-4, .m-4, .gap-2, .space-x-2

/* Borders */
.rounded-md, .border, .shadow-sm
```

### Component Imports
```typescript
// UI Components
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

// Utilities
import { cn } from "@/lib/utils"
import { cva, type VariantProps } from "class-variance-authority"
```

This design system provides a solid foundation for building consistent, accessible, and performant user interfaces across the Source application.