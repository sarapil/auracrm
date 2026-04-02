# AuraCRM — Copilot Instructions

## Application Overview

AuraCRM is a **Visual CRM Platform** built on Frappe v16 / ERPNext with 65 DocTypes, 9 engines, 20+ intelligence modules, full gamification, CAPS integration, and bilingual (AR/EN) support.

**Module**: AuraCRM | **Version**: 1.0.0 | **License**: MIT (Open Core)

## Architecture

```
auracrm/
├── api/              # 12 REST API modules (121 @frappe.whitelist endpoints)
├── engines/          # 9 core engines (scoring, distribution, SLA, automation,
│                     #   dedup, gamification, dialer, campaign, marketing)
├── intelligence/     # AI Profiler, OSINT, Enrichment, Holiday Guard,
│                     #   Lead Tagging, Resale Engine
├── interaction/      # Interaction Automation (P23)
├── nurture/          # Nurture Journey Engine (P25)
├── social_publishing/ # Multi-platform social + sold-proof (P21)
├── attribution/      # Multi-touch attribution (P30)
├── competitive/      # Competitive intelligence monitor (P26)
├── reputation/       # Review management + NPS (P28)
├── deal_rooms/       # Collaborative deal rooms (P27)
├── content_engine/   # AI content writer (P22)
├── advertising/      # Ad inventory sync (P19)
├── whatsapp/         # WhatsApp chatbot (P24)
├── performance/      # Cache warmer + DB indexes
├── caps_integration/ # CAPS naming convention enforcement
├── industry/         # Industry preset system
├── dashboard/        # Unified dashboard API
├── utils/            # License validation + Feature gating
├── reports/          # 3 script reports
├── auracrm/doctype/  # 65 DocTypes (JSON + Python controllers)
├── public/
│   ├── js/           # 25 JS files (bootstrap, sidebar, components, workspaces)
│   └── scss/         # 6 SCSS files
└── translations/
    └── ar.csv        # 1,539 Arabic translations
```

## Key Coding Patterns

### Python APIs
```python
@frappe.whitelist()
def my_api(param1, param2=None):
    frappe.has_permission("Lead", "write", throw=True)
    # Use parameterized SQL or QueryBuilder
    Lead = frappe.qb.DocType("Lead")
    result = frappe.qb.from_(Lead).select(Lead.name).where(Lead.status == "Open").run()
    return result
```

### Feature Gating
```python
from auracrm.utils.feature_flags import require_premium, is_feature_enabled

@frappe.whitelist()
@require_premium("ai_lead_scoring")
def ai_score_lead(lead_name):
    ...

# Runtime check
if is_feature_enabled("advanced_analytics"):
    ...
```

### Client-Side Feature Check
```javascript
// Check feature
if (frappe.auracrm.isEnabled("ai_lead_scoring")) {
    frm.add_custom_button(__("AI Score"), callback);
}

// Or with auto-upgrade prompt
frappe.auracrm.requirePremium("automation_builder", __("Automation Builder"), () => {
    // premium code
});
```

### Real-time Events
```python
frappe.publish_realtime("auracrm_lead_scored", {"lead": lead_name, "score": score})
```

### Translation
```python
frappe.throw(_("Score Decay After Days must be at least 1."))
```
```javascript
frappe.msgprint(__("Lead assigned successfully"));
```

## Required Apps
`frappe`, `erpnext`, `frappe_visual`, `arrowz`, `caps`

## Roles
`Sales Agent`, `Sales Manager`, `Quality Analyst`, `Marketing Manager`, `CRM Admin`

## Important Rules
1. All user-facing strings must use `_()` / `__()` for translation
2. No hardcoded Arabic in Python/JS source — use translations/ar.csv
3. Use parameterized `frappe.db.sql()` or QueryBuilder — never string formatting
4. All API endpoints need `@frappe.whitelist()` and permission checks
5. Premium features must be gated with `@require_premium()` decorator
6. Follow CAPS naming conventions where applicable
7. New DocTypes go under the `AuraCRM` module
8. CSS must include RTL overrides for Arabic support
