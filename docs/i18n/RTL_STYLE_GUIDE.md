# AuraCRM — RTL Style Guide

## Overview

AuraCRM is designed RTL-first for Arabic users while maintaining full LTR English support. This guide covers CSS/SCSS patterns for bidirectional layout.

## SCSS Architecture

```
auracrm/public/scss/
├── auracrm.scss              # Main entry — imports all partials
├── _variables.scss           # Colors, spacing, breakpoints
├── _crm_base.scss            # Base CRM component styles
├── _pipeline.scss            # Pipeline board (Kanban)
├── _gamification.scss        # Leaderboards, badges
├── _softphone.scss           # Dialer/softphone widget
└── _dashboard.scss           # Dashboard cards and charts
```

## RTL Principles

### 1. Use Logical Properties

```scss
// ✅ Correct — works in both RTL and LTR
.crm-card {
  margin-inline-start: 1rem;
  padding-inline-end: 0.5rem;
  border-inline-start: 3px solid var(--primary);
}

// ❌ Avoid — breaks in RTL
.crm-card {
  margin-left: 1rem;
  padding-right: 0.5rem;
  border-left: 3px solid var(--primary);
}
```

### 2. Logical Property Reference

| Physical (avoid) | Logical (use) |
|-------------------|---------------|
| `margin-left` | `margin-inline-start` |
| `margin-right` | `margin-inline-end` |
| `padding-left` | `padding-inline-start` |
| `padding-right` | `padding-inline-end` |
| `border-left` | `border-inline-start` |
| `border-right` | `border-inline-end` |
| `text-align: left` | `text-align: start` |
| `text-align: right` | `text-align: end` |
| `float: left` | `float: inline-start` |
| `left: 0` | `inset-inline-start: 0` |
| `right: 0` | `inset-inline-end: 0` |

### 3. Flexbox Direction

```scss
// ✅ Flexbox auto-reverses in RTL
.pipeline-board {
  display: flex;
  flex-direction: row;  // Auto-reverses in RTL via dir="rtl"
  gap: 1rem;
}
```

### 4. When Physical Properties Are Needed

```scss
// Icons that should NOT flip
.icon-arrow-forward {
  // Use [dir] selector for explicit control
  [dir="rtl"] & {
    transform: scaleX(-1);
  }
}

// Specific RTL overrides
[dir="rtl"] .phone-input {
  direction: ltr;  // Phone numbers always LTR
  text-align: right;
}
```

## Component Patterns

### Pipeline Board (Kanban)

```scss
.pipeline-board {
  display: flex;
  overflow-x: auto;
  gap: var(--spacing-md);
  
  .pipeline-column {
    min-width: 280px;
    flex-shrink: 0;
    
    .column-header {
      text-align: start;
      font-weight: 600;
    }
  }
}
```

### Dashboard Cards

```scss
.dashboard-card {
  .card-metric {
    text-align: start;
    font-size: var(--text-3xl);
  }
  
  .card-label {
    text-align: start;
    color: var(--text-muted);
  }
  
  .card-trend {
    margin-inline-start: auto;
  }
}
```

### Form Layouts

```scss
// Frappe forms are RTL-aware by default
// Custom form sections:
.aura-form-section {
  .section-label {
    text-align: start;
    margin-block-end: var(--spacing-sm);
  }
  
  .field-group {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-md);
  }
}
```

## Arabic Typography

### Font Stack

```scss
:root {
  --font-stack-ar: "Cairo", "Noto Sans Arabic", "Segoe UI", sans-serif;
  --font-stack-en: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
}

[lang="ar"] body {
  font-family: var(--font-stack-ar);
  line-height: 1.8;  // Arabic needs more line height
}
```

### Number Display

```scss
// Numbers in Arabic UI should be Western (0-9) not Eastern (٠-٩)
.metric-value {
  font-variant-numeric: tabular-nums;
  direction: ltr;
  unicode-bidi: isolate;
}
```

## Testing Checklist

- [ ] Pipeline board scrolls correctly in RTL
- [ ] Dashboard cards align properly
- [ ] Form fields read right-to-left
- [ ] Phone number inputs remain LTR
- [ ] Icons that indicate direction are flipped
- [ ] Charts render correctly (labels, legends)
- [ ] Modal dialogs center properly
- [ ] Dropdown menus open on correct side
- [ ] Notification badges position correctly
- [ ] Print layouts are RTL-aware

## Browser Testing

```javascript
// Quick RTL toggle for testing
document.documentElement.setAttribute('dir', 'rtl');
document.documentElement.setAttribute('lang', 'ar');
```

## Frappe RTL Integration

Frappe automatically adds `dir="rtl"` to `<html>` when the user's language is Arabic. AuraCRM styles should:

1. Never fight Frappe's RTL mechanism
2. Use logical properties that auto-flip
3. Only use `[dir="rtl"]` selectors for exceptions (phone inputs, code blocks)
4. Test with both Frappe's Arabic and English language settings
