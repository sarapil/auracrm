# AuraCRM — Audit Log Specification

## Overview

AuraCRM leverages Frappe's built-in Version tracking plus custom audit DocTypes to provide comprehensive activity logging.

## Audit Sources

### 1. Frappe Version System (Built-in)

Every document change is automatically recorded:

```python
# Reading audit trail
versions = frappe.get_all("Version",
    filters={"ref_doctype": "Aura Lead", "ref_docname": lead_name},
    fields=["owner", "creation", "data"],
    order_by="creation desc"
)
for v in versions:
    changes = frappe.parse_json(v.data)
    # changes.changed = [[fieldname, old_value, new_value], ...]
```

### 2. CRM-Specific Audit DocTypes

| DocType | What it Tracks |
|---------|---------------|
| **Interaction Log** | All customer interactions (call, email, meeting, note, WhatsApp, social) |
| **Agent Points Log** | Gamification events — point awards and deductions |
| **SLA Breach Log** | SLA violations with breach time and assigned agent |
| **OSINT Hunt Log** | External intelligence gathering operations |
| **Enrichment Job** | Data enrichment requests and results |
| **Distribution Log** | Lead assignment decisions and routing |
| **Campaign Log** | Campaign execution events |

### 3. License Events

| Event | Logged Where |
|-------|-------------|
| License key validated | `frappe.logger("auracrm.license")` |
| License expired | `frappe.logger("auracrm.license")` |
| Premium feature blocked | `frappe.logger("auracrm.feature_flags")` |
| Feature flag checked | In-memory only (no log by default) |

## Log Format

### Interaction Log Schema

```json
{
  "interaction_type": "Call|Email|Meeting|Note|WhatsApp|Social",
  "reference_doctype": "Aura Lead",
  "reference_name": "LEAD-00001",
  "communication_date": "2025-01-15 10:30:00",
  "agent": "agent@company.com",
  "summary": "Discussed pricing for Enterprise plan",
  "duration": 15,
  "direction": "Outbound",
  "sentiment": "Positive"
}
```

### Agent Points Log Schema

```json
{
  "agent": "agent@company.com",
  "points": 10,
  "action": "lead_converted",
  "reference_doctype": "Aura Opportunity",
  "reference_name": "OPP-00001",
  "period": "2025-W03"
}
```

## Retention & Archival

### Recommended Retention Periods

| Log Type | Active | Archive | Delete |
|----------|--------|---------|--------|
| Document Versions | 1 year | 3 years | 7 years |
| Interaction Logs | 2 years | 5 years | 7 years |
| Agent Points | 1 year | 2 years | 3 years |
| SLA Breaches | 1 year | 3 years | 5 years |
| OSINT Hunts | 6 months | 1 year | 2 years |

### Archival Script

```python
# Archive old interaction logs
import frappe
from frappe.utils import add_months, nowdate

cutoff = add_months(nowdate(), -24)
old_logs = frappe.get_all("Interaction Log",
    filters={"communication_date": ["<", cutoff]},
    pluck="name"
)
for log in old_logs:
    frappe.get_doc("Interaction Log", log).archive()
    frappe.db.commit()
```

## Querying Audit Data

### Recent Activity for a Lead

```python
frappe.call({
    method: "frappe.client.get_list",
    args: {
        doctype: "Interaction Log",
        filters: {reference_doctype: "Aura Lead", reference_name: lead_name},
        fields: ["interaction_type", "summary", "communication_date", "agent"],
        order_by: "communication_date desc",
        limit_page_length: 20
    }
})
```

### Agent Activity Report

```python
# All actions by a specific agent in the last 30 days
from frappe.utils import add_days, nowdate

logs = frappe.get_all("Interaction Log",
    filters={
        "agent": agent_email,
        "communication_date": [">=", add_days(nowdate(), -30)]
    },
    fields=["interaction_type", "count(name) as count"],
    group_by="interaction_type"
)
```
