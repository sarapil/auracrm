# AuraCRM — Extension Guide

> How to build extensions and customizations for AuraCRM

## Overview

AuraCRM is designed for extensibility. You can:
1. **Add custom engines** — New business logic modules
2. **Add DocTypes** — Extend the data model
3. **Override existing engines** — Modify scoring, distribution, etc.
4. **Add API endpoints** — New REST endpoints
5. **Create custom workspaces** — New UI views
6. **Add intelligence modules** — New AI/data integrations

## Creating an AuraCRM Extension App

```bash
bench new-app my_auracrm_extension
```

In your extension's `hooks.py`:
```python
required_apps = ["auracrm"]

doc_events = {
    "Lead": {
        "on_update": ["my_extension.hooks.on_lead_update"],
    },
}
```

## Adding a Custom Scoring Dimension

```python
# my_extension/scoring/custom_scorer.py

import frappe

def calculate_custom_score(lead_doc):
    """Custom scoring dimension — called from hooks."""
    score = 0

    # Your custom logic
    if lead_doc.get("custom_field"):
        score += 20

    # Update the lead's score
    current = lead_doc.get("lead_score") or 0
    lead_doc.lead_score = min(current + score, 100)
```

Register in hooks:
```python
doc_events = {
    "Lead": {
        "validate": ["my_extension.scoring.custom_scorer.calculate_custom_score"],
    },
}
```

## Adding a Custom Distribution Method

```python
# my_extension/distribution/geo_distributor.py

import frappe

def distribute_by_geography(lead_doc):
    """Assign leads based on geographic region."""
    region = lead_doc.get("territory") or "Default"

    agent = frappe.db.get_value(
        "Distribution Agent",
        {"region": region, "is_active": 1},
        "agent",
        order_by="current_load asc",
    )

    if agent:
        lead_doc.lead_owner = agent
```

## Custom Workspace Module

```javascript
// my_extension/public/js/workspaces/custom_dashboard.js

frappe.provide("frappe.auracrm.workspaces");

frappe.auracrm.workspaces.CustomDashboard = class {
    constructor(container) {
        this.container = container;
        this.render();
    }

    async render() {
        const data = await frappe.call({
            method: "my_extension.api.get_custom_data",
        });
        // Render your custom UI
    }
};
```

## Best Practices

1. **Never modify AuraCRM source** — Use hooks and overrides
2. **Respect feature gating** — Check `frappe.auracrm.isEnabled()` before using premium APIs
3. **Follow CAPS conventions** — If CAPS is installed, use proper naming
4. **Add translations** — Include ar.csv in your extension
5. **Write tests** — Follow AuraCRM's test patterns
6. **Document your extension** — Include README with setup instructions
