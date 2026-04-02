# AuraCRM — Developer Cookbook

> Code recipes for common development tasks

## Adding a New API Endpoint

```python
# auracrm/api/my_module.py

import frappe
from auracrm.utils.feature_flags import require_premium


@frappe.whitelist()
def get_my_data(filters=None, limit=20):
    """Public API — available in free tier.

    Args:
        filters (dict): Optional filters
        limit (int): Max results (default 20)

    Returns:
        list[dict]: Results
    """
    frappe.has_permission("Lead", "read", throw=True)

    Lead = frappe.qb.DocType("Lead")
    query = (
        frappe.qb.from_(Lead)
        .select(Lead.name, Lead.lead_name, Lead.status)
        .limit(limit)
    )

    if filters and filters.get("status"):
        query = query.where(Lead.status == filters["status"])

    return query.run(as_dict=True)


@frappe.whitelist()
@require_premium("advanced_analytics")
def get_premium_analytics(period="month"):
    """Premium API — requires license.

    Automatically throws PermissionError if no premium license.
    """
    ...
```

## Adding a New Engine

```python
# auracrm/engines/my_engine.py

import frappe
from frappe.utils import now_datetime


class MyEngine:
    """Engine for [purpose].

    Hooks: Called from doc_events in hooks.py
    Scheduler: Called from scheduler_events in hooks.py
    """

    @staticmethod
    def on_lead_event(doc, method=None):
        """Hook: Called on Lead insert/update."""
        if not frappe.get_single("AuraCRM Settings").my_feature_enabled:
            return
        # Engine logic here

    @staticmethod
    def scheduled_task():
        """Scheduler: Called every N minutes."""
        # Batch processing logic


# Module-level functions for hooks.py
def on_lead_event(doc, method=None):
    MyEngine.on_lead_event(doc, method)

def scheduled_task():
    MyEngine.scheduled_task()
```

Then register in hooks.py:
```python
doc_events = {
    "Lead": {
        "on_update": [
            "auracrm.engines.my_engine.on_lead_event",
        ],
    },
}

scheduler_events = {
    "cron": {
        "*/10 * * * *": ["auracrm.engines.my_engine.scheduled_task"],
    },
}
```

## Adding a New DocType

1. Create via bench:
```bash
bench --site dev.localhost new-doctype "My DocType" --module AuraCRM
```

2. Edit the JSON and controller in `auracrm/auracrm/doctype/my_doctype/`

3. Add permissions in the JSON:
```json
{
    "permissions": [
        {"role": "Sales Agent", "read": 1, "write": 1, "create": 1},
        {"role": "Sales Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": "CRM Admin", "read": 1, "write": 1, "create": 1, "delete": 1}
    ]
}
```

4. Add translations for the DocType name and all field labels

## Adding Translations

```csv
# auracrm/translations/ar.csv
"My Feature","ميزتي",""
"Enable My Feature","تفعيل ميزتي",""
"My Feature is now active","ميزتي مفعلة الآن",""
```

Always use `_()` in Python and `__()` in JavaScript.

## Writing Tests

```python
# auracrm/engines/test_my_engine.py

import frappe
from frappe.tests import IntegrationTestCase


class TestMyEngine(IntegrationTestCase):
    def setUp(self):
        self.settings = frappe.get_single("AuraCRM Settings")

    def test_basic_functionality(self):
        """Test that the engine processes correctly."""
        lead = frappe.get_doc({
            "doctype": "Lead",
            "lead_name": "Test Lead",
            "email_id": "test@example.com",
        }).insert(ignore_permissions=True)

        # Assert engine behavior
        self.assertEqual(lead.status, "Lead")

    def tearDown(self):
        frappe.db.rollback()
```

Run tests:
```bash
bench --site dev.localhost run-tests --app auracrm --module auracrm.engines.test_my_engine
```

## Working with the Cache System

```python
from auracrm.cache import cached, invalidate_cache

# Decorate functions for auto-caching
@cached(key="my_data:{period}", ttl=300)
def get_expensive_data(period):
    # This result is cached for 5 minutes
    return heavy_computation(period)

# Invalidate when data changes
def on_data_change(doc, method):
    invalidate_cache("my_data:*")
```

## Real-time Events

```python
# Server-side
frappe.publish_realtime(
    "auracrm_custom_event",
    {"type": "update", "data": result},
    user=frappe.session.user,
)
```

```javascript
// Client-side
frappe.realtime.on("auracrm_custom_event", function(data) {
    console.log("Event received:", data);
    frappe.show_alert({message: __("Update received"), indicator: "green"});
});
```

## Feature Gating in Client JS

```javascript
// Check before showing UI
if (frappe.auracrm.isEnabled("my_premium_feature")) {
    frm.add_custom_button(__("Premium Action"), callback);
}

// Or with automatic upgrade prompt
frm.add_custom_button(__("AI Analysis"), () => {
    frappe.auracrm.requirePremium(
        "ai_lead_scoring",
        __("AI Lead Scoring"),
        () => {
            // Premium code executes only if licensed
            frappe.call({
                method: "auracrm.api.scoring.ai_score_lead",
                args: { lead: frm.doc.name },
            });
        }
    );
});
```
