"""AuraCRM — Scoring API (Phase 5: Performance Optimized)"""
import json
import frappe
from frappe import _
from auracrm.cache import cached
from caps.utils.resolver import require_capability


@frappe.whitelist()
def get_lead_scores(filters=None, limit=50):
    """Get leads with their scores for the scoring dashboard."""
    require_capability("scoring:scores:view")
    if isinstance(filters, str):
        filters = json.loads(filters)

    base_filters = {"status": ["not in", ["Converted", "Do Not Contact"]]}
    if filters:
        base_filters.update(filters)

    return frappe.get_all(
        "Lead",
        filters=base_filters,
        fields=["name", "lead_name", "company_name", "source", "lead_owner",
                "status", "aura_score", "modified", "creation"],
        order_by="aura_score desc",
        limit_page_length=limit,
    )


@frappe.whitelist()
@cached(ttl=120, key_prefix="scoring:dist")
def get_score_distribution():
    """Get distribution of lead scores — single query with CASE WHEN."""
    require_capability("scoring:distribution:view")
    row = frappe.db.sql("""
        SELECT
            SUM(CASE WHEN aura_score BETWEEN 80 AND 100 THEN 1 ELSE 0 END) AS hot,
            SUM(CASE WHEN aura_score BETWEEN 60 AND 79  THEN 1 ELSE 0 END) AS warm,
            SUM(CASE WHEN aura_score BETWEEN 30 AND 59  THEN 1 ELSE 0 END) AS cool,
            SUM(CASE WHEN aura_score BETWEEN 0  AND 29  THEN 1 ELSE 0 END) AS cold
        FROM `tabLead`
        WHERE status NOT IN ('Converted', 'Do Not Contact')
    """, as_dict=True)[0]

    return [
        {"label": _("Hot (80-100)"), "min": 80, "max": 100, "color": "#ef4444", "count": int(row.hot or 0)},
        {"label": _("Warm (60-79)"), "min": 60, "max": 79, "color": "#f59e0b", "count": int(row.warm or 0)},
        {"label": _("Cool (30-59)"), "min": 30, "max": 59, "color": "#3b82f6", "count": int(row.cool or 0)},
        {"label": _("Cold (0-29)"),  "min": 0,  "max": 29, "color": "#94a3b8", "count": int(row.cold or 0)},
    ]


@frappe.whitelist()
@cached(ttl=300, key_prefix="scoring:rules")
def get_scoring_rules():
    """Get all scoring rules with criteria — batch fetch."""
    require_capability("scoring:rules:view")
    rules = frappe.get_all(
        "Lead Scoring Rule",
        filters={"enabled": 1},
        fields=["name", "rule_name", "priority", "enabled"],
        order_by="priority asc",
    )
    if not rules:
        return []

    rule_names = [r.name for r in rules]

    # Batch: all criteria for all rules in one query
    all_criteria = frappe.get_all(
        "Scoring Criterion",
        filters={"parent": ["in", rule_names], "parenttype": "Lead Scoring Rule"},
        fields=["parent", "field_name", "operator", "field_value", "points"],
        order_by="parent, idx asc",
    )

    criteria_map = {}
    for c in all_criteria:
        criteria_map.setdefault(c.parent, []).append(c)

    for rule in rules:
        rule["criteria"] = criteria_map.get(rule.name, [])

    return rules


@frappe.whitelist()
def recalculate_all_scores():
    """Admin: Recalculate scores for all open leads. Returns count."""
    require_capability("scoring:recalculate")
    frappe.only_for(["System Manager", "Sales Manager"])

    leads = frappe.get_all(
        "Lead",
        filters={"status": ["not in", ["Converted", "Do Not Contact"]]},
        fields=["name"],
        limit=1000,
    )

    count = 0
    for lead in leads:
        try:
            doc = frappe.get_doc("Lead", lead.name)
            doc.flags.skip_scoring = False
            doc.save(ignore_permissions=True)
            count += 1
        except Exception:
            pass

    frappe.db.commit()
    return {"recalculated": count}


@frappe.whitelist()
def get_score_history(lead_name, limit=20):
    """Get score change history for a specific lead."""
    require_capability("scoring:history:view")
    logs = frappe.get_all(
        "Lead Score Log",
        filters={"lead": lead_name},
        fields=["name", "old_score", "new_score", "reason", "triggered_by", "creation"],
        order_by="creation desc",
        limit_page_length=limit,
    )
    return logs
