# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""AuraCRM — Pipeline API (Phase 5: Performance Optimized)"""
import json
import frappe
from frappe import _
from frappe.utils import cint, flt
from auracrm.cache import cached
from caps.utils.resolver import require_capability


@frappe.whitelist()
@cached(ttl=60, key_prefix="pipeline:stages")
def get_pipeline_stages():
    """Get pipeline stages with counts — single aggregated query."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("pipeline:stages:view")
    stages = frappe.get_all("Sales Stage", fields=["name", "stage_name"], order_by="idx asc")
    if not stages:
        return []

    # Batch counts + totals in one query
    agg = {}
    for row in frappe.db.sql("""
        SELECT sales_stage,
               COUNT(*) AS cnt,
               COALESCE(SUM(opportunity_amount), 0) AS total_value
        FROM `tabOpportunity`
        WHERE status = 'Open' AND sales_stage IS NOT NULL
        GROUP BY sales_stage
    """, as_dict=True):
        agg[row.sales_stage] = row

    result = []
    for stage in stages:
        data = agg.get(stage.name)
        result.append({
            "stage": stage.name,
            "label": stage.stage_name or stage.name,
            "count": cint(data.cnt) if data else 0,
            "value": flt(data.total_value) if data else 0,
        })
    return result


@frappe.whitelist()
# Allowed filter columns for pipeline board — prevents SQL injection via column names
_PIPELINE_FILTER_COLUMNS = {
    "sales_stage", "opportunity_from", "party_name", "contact_person",
    "territory", "source", "campaign", "opportunity_type",
    "expected_closing", "company", "_assign",
}


def get_pipeline_board(filters=None):
    """Get Kanban board data — single query for all stage opportunities."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("pipeline:board:view")
    if isinstance(filters, str):
        filters = json.loads(filters)

    stages = get_pipeline_stages()
    if not stages:
        return {}

    # Build single query for all stages
    conditions = ["status = 'Open'"]
    params = {}
    if filters:
        for key, val in filters.items():
            # Security: only allow whitelisted column names (prevents SQL injection)
            if key not in _PIPELINE_FILTER_COLUMNS:
                frappe.throw(
                    _("Filter column '{0}' is not allowed").format(key),
                    title=_("Invalid Filter"),
                )
            safe_key = key.replace(" ", "_")
            conditions.append("`{col}` = %({param})s".format(col=key, param=safe_key))
            params[safe_key] = val

    opps = frappe.db.sql("""
        SELECT name, sales_stage, opportunity_from, party_name, opportunity_amount,
               expected_closing, contact_person, _assign, modified
        FROM `tabOpportunity`
        WHERE {conds}
        ORDER BY modified DESC
    """.format(conds=" AND ".join(conditions)), params, as_dict=True)

    # Group by stage (limit 50 per stage)
    stage_opps = {}
    for opp in opps:
        bucket = stage_opps.setdefault(opp.sales_stage, [])
        if len(bucket) < 50:
            bucket.append(opp)

    board = {}
    for stage in stages:
        board[stage["stage"]] = {
            "stage": stage,
            "opportunities": stage_opps.get(stage["stage"], []),
        }
    return board


@frappe.whitelist()
def move_opportunity(opportunity, new_stage):
    """Move an opportunity to a new pipeline stage."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    require_capability("pipeline:move")
    frappe.db.set_value("Opportunity", opportunity, "sales_stage", new_stage)
    from auracrm.cache import invalidate_prefix
    invalidate_prefix("pipeline:")
    frappe.publish_realtime("auracrm_pipeline_update", {
        "opportunity": opportunity, "new_stage": new_stage,
    })
    return {"status": "ok"}
