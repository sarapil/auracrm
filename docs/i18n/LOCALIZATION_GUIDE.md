# AuraCRM — Localization Guide

## Overview

AuraCRM ships with full Arabic (ar) translation and is designed for RTL-first, bilingual (Arabic + English) usage. This guide covers adding new translations and supporting additional languages.

## Translation Architecture

```
auracrm/
├── translations/
│   ├── ar.csv        # 1,539 entries — Arabic (complete)
│   └── en.csv        # English base (auto-generated)
```

### CSV Format

```csv
source,translated,context
"Lead Score","نقاط العميل المحتمل",""
"Pipeline Stage","مرحلة خط الأنابيب",""
"Convert to Opportunity","تحويل إلى فرصة",""
```

- **source**: The original English string as it appears in code
- **translated**: The target language translation
- **context**: Optional context hint for disambiguation

## Adding a New Language

### Step 1: Create Translation File

```bash
cd /path/to/frappe-bench
bench --site dev.localhost get-untranslated auracrm fr translations/fr.csv
```

### Step 2: Translate Strings

Edit the CSV file, filling in the `translated` column for each row.

### Step 3: Import Translations

```bash
bench --site dev.localhost import-translations auracrm/translations/fr.csv
```

### Step 4: Verify

```bash
bench --site dev.localhost clear-cache
# Switch language in user settings, verify UI strings
```

## Translation Sources

### Python Code

```python
# Simple string
frappe._(\"Lead Score\")

# With context
frappe._(\"Draft\", context=\"Pipeline Stage\")

# F-string pattern (extract the template)
frappe._(\"Assigned {count} leads\").format(count=5)
```

### JavaScript Code

```javascript
// Simple
__(\"Lead Score\")

// With formatting
__(\"{0} leads assigned\", [count])
```

### DocType JSON

Field labels, descriptions, and options in DocType JSON files are automatically picked up for translation.

### Jinja Templates

```html
{{ _(\"Welcome to AuraCRM\") }}
```

## Extracting New Strings

After adding new features:

```bash
# Extract all translatable strings
bench --site dev.localhost get-untranslated auracrm ar untranslated_ar.csv

# Review and translate the new strings
# Then import back
bench --site dev.localhost import-translations auracrm/translations/ar.csv
```

## Translation Best Practices

1. **Use `_()` everywhere** — Never hardcode user-facing strings
2. **Keep strings simple** — Avoid complex HTML in translatable strings
3. **Use placeholders** — `_("{0} leads").format(count)` not `_(f"{count} leads")`
4. **Context for ambiguity** — `_("Draft", context="Document Status")` vs `_("Draft", context="Email Draft")`
5. **Test RTL** — Always verify Arabic layout in browser
6. **Avoid concatenation** — `_("Hello {name}").format(name=n)` not `_("Hello ") + name`

## Current Translation Coverage

| Category | Strings | Status |
|----------|---------|--------|
| DocType Labels | ~800 | ✅ Complete |
| Button/Action Text | ~200 | ✅ Complete |
| Notification Messages | ~150 | ✅ Complete |
| Report Headers | ~100 | ✅ Complete |
| Validation Errors | ~150 | ✅ Complete |
| Settings Labels | ~100 | ✅ Complete |
| License/Feature Strings | ~39 | ✅ Complete |
| **Total** | **~1,539** | **✅ ar.csv** |

## Frappe Translation System

Frappe loads translations in this priority:
1. App-level `translations/<lang>.csv`
2. Site-level custom translations (via UI)
3. Frappe core translations

AuraCRM translations override Frappe defaults for CRM-specific terms.
