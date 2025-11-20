# mk-monitor Frontend UI Documentation

## Overview

The mk-monitor frontend is built with React 18, React Router v6, and Vite. It follows a modern design system with a unified theme system supporting both dark and light modes.

## Architecture

### Project Structure

```
frontend/src/
├── api/              # API client and endpoint wrappers
├── components/       # Reusable UI components
│   ├── Layout/      # Header, Sidebar, ThemeToggle
│   └── ui/          # Form components (Button, Input, TextField, etc.)
├── context/         # React contexts (AuthContext)
├── hooks/           # Custom React hooks
├── pages/           # Route page components
├── providers/       # Theme and other providers
└── styles/          # Global styles and design tokens
    ├── tokens.css   # Design tokens (colors, spacing, etc.)
    └── theme.css    # Theme utilities and components
```

### Theme System

The application uses a unified theme system powered by CSS custom properties (CSS variables).

#### ThemeProvider

**Location:** `src/providers/ThemeProvider.jsx`

The ThemeProvider is the single source of truth for theme management:

- Sets `data-theme="dark"` or `data-theme="light"` attribute on `document.documentElement`
- Persists theme choice in `localStorage` with key `'theme'`
- Supports system preference detection via `prefers-color-scheme` media query
- Provides context values: `{ theme, isDark, toggleTheme }`

**Usage:**

```jsx
import { useContext } from 'react'
import { ThemeContext } from '../providers/ThemeProvider.jsx'

function MyComponent() {
  const { theme, isDark, toggleTheme } = useContext(ThemeContext)
  // ...
}
```

#### Design Tokens

**Location:** `src/styles/tokens.css`

All design tokens follow a consistent naming convention:

**Color Tokens:**
- `--color-bg` - Primary background color
- `--color-bg-alt` - Alternative background (slightly different shade)
- `--color-surface` - Card/panel surface color
- `--color-surface-alt` - Alternative surface color
- `--color-border` - Default border color
- `--color-border-light` - Lighter border color
- `--color-text-primary` - Primary text color
- `--color-text-secondary` - Secondary text color
- `--color-text-muted` - Muted/subtle text color
- `--color-primary` - Brand primary color (interactive elements)
- `--color-primary-hover` - Primary hover state
- `--color-primary-contrast` - Text color on primary background
- `--color-success` - Success/healthy status
- `--color-critical` - Critical alerts
- `--color-severe` - Severe alerts
- `--color-minor` - Minor issues
- `--color-info` - Informational
- `--color-warning` - Warning state
- `--color-danger` - Danger/error state
- `--color-focus-ring` - Focus outline color
- `--color-chip` - Chip/badge background

**Spacing Tokens:**
- `--space-1` through `--space-8` (4px, 8px, 12px, 16px, 24px, 32px, 40px, 48px)

**Radius Tokens:**
- `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`, `--radius-full`

**Shadow Tokens:**
- `--shadow-sm`, `--shadow-1`, `--shadow-2`, `--shadow-lg`

**Font Tokens:**
- `--font-sans`, `--font-mono`
- `--font-size-xs` through `--font-size-3xl`

**Transition Tokens:**
- `--transition-fast`, `--transition-base`, `--transition-slow`

#### Dark vs Light Theme Values

```css
/* Dark Theme */
[data-theme="dark"] {
  --color-bg: #0E1115;
  --color-text-primary: #E6EBF1;
  --shadow-1: 0 2px 6px rgba(0,0,0,0.35);
  /* ... */
}

/* Light Theme */
[data-theme="light"] {
  --color-bg: #F5F7FA;
  --color-text-primary: #1A2128;
  --shadow-1: 0 2px 6px rgba(0,0,0,0.08);
  /* ... */
}
```

### Layout System

The application uses a consistent layout structure:

1. **ProtectedLayout** (`App.jsx`) - Wraps all authenticated routes
2. **Header** - Top navigation bar with tenant info, theme toggle, and logout
3. **Sidebar** - Left navigation menu (responsive drawer on mobile)
4. **Content** - Main content area for page components

Pages should NOT import layout components directly. The layout is applied automatically to all protected routes.

### Component Guidelines

#### Using CSS Variables in Components

✅ **DO:**
```jsx
<div style={{ 
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
  border: '1px solid var(--color-border)'
}}>
```

❌ **DON'T:**
```jsx
<div style={{ 
  background: '#1B2129',
  color: '#E6EBF1',
  border: '1px solid #27313D'
}}>
```

#### Utility Classes

Common utility classes are available in `theme.css`:

- `.card` - Standard card/panel
- `.row` - Flexbox row with gap
- `.col` - Flexbox column with gap
- `.muted` - Muted text color
- `.small` - Small text size
- `.glass` - Glassmorphism effect
- `.badge`, `.badge-critical`, `.badge-info`, etc. - Status badges
- `.btn`, `.btn-primary`, `.btn-secondary` - Button styles

### Accessibility

The application implements basic accessibility features:

- `role="navigation"` on sidebar navigation
- `role="alert"` on suspension banner
- `aria-label` on interactive elements (buttons, links)
- `aria-pressed` on toggle buttons (theme toggle)
- `aria-labelledby` and `aria-describedby` on modals
- Focus visible outlines using `--color-focus-ring`
- Keyboard navigation support

### Data Fetching

All data fetching hooks implement AbortController to prevent memory leaks and duplicate requests in React.StrictMode:

```jsx
useEffect(() => {
  const abortController = new AbortController()
  
  async function fetchData() {
    try {
      const response = await fetch(url, { 
        signal: abortController.signal 
      })
      if (!abortController.signal.aborted) {
        // Process data
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        // Handle error
      }
    }
  }
  
  fetchData()
  return () => abortController.abort()
}, [dependencies])
```

### Link Styling

All links are styled consistently without purple visited colors:

- Default: Primary color without underline
- Hover/Focus: Primary hover color with underline
- Visited: Same as default (no purple)
- Focus-visible: Focus ring outline

## Corrección rápida v1

### Summary of Changes

This section documents the unified theme system migration completed to fix inconsistent theming and improve maintainability.

#### Files Deleted

The following legacy files were removed as part of the consolidation:

1. **`src/context/ThemeContext.jsx`** - Deprecated theme context using body classes (`theme-dark`, `theme-light`)
2. **`src/styles/layout.css`** - Redundant minimal layout styles (merged into theme.css)

#### Files Created

1. **`src/styles/tokens.css`** - Unified design tokens with consistent `--color-*` naming convention
2. **`docs/ui.md`** - This comprehensive UI documentation

#### Files Modified

1. **`src/styles/theme.css`** - Refactored to import tokens.css and provide utility classes
2. **`src/providers/ThemeProvider.jsx`** - Already modern, no changes needed (uses data-theme)
3. **`src/main.jsx`** - Removed duplicate layout.css import
4. **`src/components/Layout/Header.jsx`** - Replaced hardcoded hex colors with CSS variables
5. **`src/components/Layout/Sidebar.jsx`** - Added `role="navigation"` for accessibility
6. **`src/components/Layout/ThemeToggle.jsx`** - Already implements proper aria-* attributes
7. **`src/pages/LoginPage.jsx`** - Replaced hardcoded colors with CSS variables
8. **`src/App.jsx`** - Added aria-labelledby/aria-describedby to session expired modal
9. **`src/hooks/useFetchAlerts.js`** - Added AbortController for idempotent effects
10. **`src/hooks/useDeviceHealth.js`** - Added AbortController for idempotent effects
11. **`src/pages/DashboardPage.jsx`** - Added AbortController to SLA metrics fetch

#### New Token Naming Convention

All color tokens now follow the `--color-*` pattern:

- Old: `--bg`, `--text`, `--primary`, `--card`, `--border`
- New: `--color-bg`, `--color-text-primary`, `--color-primary`, `--color-surface`, `--color-border`

Legacy aliases are maintained for backward compatibility during migration.

#### Theme Toggle Behavior

The theme toggle:
- Applies `data-theme="dark"` or `data-theme="light"` to `<html>` element
- Persists choice in localStorage (key: `'theme'`)
- Supports system preference detection on first load
- Manual toggle overrides system preference
- All components automatically adapt via CSS custom properties

#### Layout Strategy

- **Single Layout Wrapper:** `ProtectedLayout` in `App.jsx` wraps all authenticated routes
- **No Direct Imports:** Page components do not import `Header` or `Sidebar` directly
- **Responsive:** Sidebar becomes a drawer on mobile (<900px) with backdrop
- **Accessibility:** Navigation elements have proper ARIA roles and labels

#### Status Color Mapping

Status badges and indicators now use semantic color tokens:

- Critical alerts: `--color-critical` (#FF4D4F)
- Severe alerts: `--color-severe` (#FF914D)
- Minor issues: `--color-minor` (#FFD447)
- Success/Healthy: `--color-success` (#2ECC71)
- Informational: `--color-info` (#3DA8FF)

#### Contrast Compliance

Color combinations have been tested for WCAG AA contrast in both themes:

- **Dark theme:** Light text on dark backgrounds (4.5:1+)
- **Light theme:** Dark text on light backgrounds (4.5:1+)
- **Interactive elements:** Primary blue has sufficient contrast in both themes

#### API Integration Notes

- **No endpoint changes:** All API calls remain unchanged
- **No payload changes:** Request/response shapes are preserved
- **Auth flow:** Authentication and session management unchanged
- **AbortController:** Added to prevent duplicate network requests, but does not alter API behavior

### Migration Guide for Future Changes

When adding new components or modifying existing ones:

1. **Use CSS variables** - Never hardcode colors, spacing, or shadows
2. **Reference tokens.css** - Check available tokens before creating new ones
3. **Test both themes** - Toggle theme to verify visual consistency
4. **Add accessibility** - Include appropriate ARIA attributes
5. **Implement AbortController** - For any data fetching in useEffect

### Extending the Design System

To add new tokens:

1. Edit `src/styles/tokens.css`
2. Add token to both `[data-theme="dark"]` and `[data-theme="light"]`
3. Follow naming convention: `--color-*`, `--space-*`, `--radius-*`, etc.
4. Add legacy alias in `:root` if needed for backward compatibility
5. Document the new token in this file

### Known Limitations

- ESLint configuration is missing (linter not currently functional)
- Some components may still use legacy token names (backward compatible via aliases)
- Mobile responsiveness tested at 900px breakpoint only
- No automated visual regression tests

### Future Improvements

Potential enhancements for consideration:

1. Add ESLint configuration for consistent code style
2. Migrate remaining legacy token usages to new naming convention
3. Add automated theme contrast testing
4. Implement theme transition animations
5. Add more granular spacing tokens if needed
6. Consider adding `--color-overlay` token for consistent modal/backdrop styling
