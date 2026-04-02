# AuraCRM — Analytics Integration Guide

## Built-in Analytics

### Script Reports

AuraCRM ships with 3 built-in script reports:

| Report | Path | Description |
|--------|------|-------------|
| **Conversion Funnel** | `auracrm/report/conversion_funnel_report/` | Stage-by-stage conversion analysis |
| **Pipeline Velocity** | `auracrm/report/pipeline_velocity_report/` | Pipeline speed and bottleneck detection |
| **Agent Performance** | `auracrm/report/agent_performance_report/` | Agent KPIs and ranking |

### Dashboard Charts

AuraCRM pages include embedded charts:
- Pipeline Board — stage distribution bar chart
- Team Dashboard — leaderboard, activity timeline
- Aura Lead list — scoring distribution

## External Analytics Integration

### Google Analytics 4

Track CRM portal usage:

```javascript
// In hooks.py, add to website context
website_context = {
    "head_template": "templates/includes/analytics_head.html"
}
```

```html
<!-- templates/includes/analytics_head.html -->
{% if not frappe.session.user == "Guest" %}
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
{% endif %}
```

### Mixpanel / PostHog

Track CRM events:

```javascript
// In aura_bootstrap.js, add event tracking
frappe.auracrm.trackEvent = function(event_name, properties) {
    if (window.posthog) {
        posthog.capture(event_name, properties);
    }
    if (window.mixpanel) {
        mixpanel.track(event_name, properties);
    }
};

// Usage in other scripts
frappe.auracrm.trackEvent('lead_created', {source: 'web_form'});
frappe.auracrm.trackEvent('lead_converted', {score: 85, days_to_convert: 12});
```

### Metabase / Superset (Direct DB)

For advanced BI, connect directly to MariaDB:

```
Host: your-db-host
Port: 3306
Database: _<site_name> (e.g., _dev_localhost)
User: read-only user recommended

Key tables:
- tabAura Lead
- tabAura Opportunity
- tabAura Deal
- tabInteraction Log
- tabAgent Points Log
- tabSLA Breach Log
- tabCampaign Log
```

### Sample Metabase Queries

```sql
-- Lead conversion funnel
SELECT 
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM `tabAura Lead`
WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY status
ORDER BY FIELD(status, 'New', 'Contacted', 'Qualified', 'Proposal', 'Negotiation', 'Converted', 'Lost');

-- Agent performance this month
SELECT 
    lead_owner as agent,
    COUNT(*) as total_leads,
    SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) as converted,
    ROUND(SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as conversion_rate
FROM `tabAura Lead`
WHERE creation >= DATE_FORMAT(NOW(), '%Y-%m-01')
GROUP BY lead_owner
ORDER BY conversion_rate DESC;

-- Pipeline velocity
SELECT 
    DATE_FORMAT(creation, '%Y-%m') as month,
    AVG(DATEDIFF(modified, creation)) as avg_days_in_pipeline,
    COUNT(*) as deals
FROM `tabAura Opportunity`
WHERE status IN ('Won', 'Lost')
GROUP BY DATE_FORMAT(creation, '%Y-%m')
ORDER BY month DESC
LIMIT 12;
```

## Webhook Integration

Push CRM events to external systems:

```python
# In hooks.py
doc_events = {
    "Aura Lead": {
        "on_update": "auracrm.integrations.webhooks.on_lead_update",
        "after_insert": "auracrm.integrations.webhooks.on_lead_created"
    }
}
```

```python
# auracrm/integrations/webhooks.py
import frappe
import requests

def on_lead_created(doc, method):
    webhooks = frappe.get_all("AuraCRM Webhook",
        filters={"event": "lead_created", "enabled": 1},
        fields=["url", "secret"]
    )
    for wh in webhooks:
        requests.post(wh.url, json={
            "event": "lead_created",
            "data": doc.as_dict()
        }, headers={"X-Webhook-Secret": wh.secret}, timeout=5)
```

## Data Export for ML/BI

```python
# Export leads to CSV for external analysis
import frappe
import csv

leads = frappe.get_all("Aura Lead",
    fields=["name", "lead_name", "source", "status", "lead_score",
            "lead_owner", "creation", "modified", "industry", "territory"],
    limit_page_length=0
)

with open("/tmp/auracrm_leads_export.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=leads[0].keys())
    writer.writeheader()
    writer.writerows(leads)
```
