# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Analytics API (Phase 5: Performance Optimized)
==========================================================
All N+1 query loops replaced with aggregated SQL.
TTL-based Redis caching on dashboard endpoints.
"""
import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate, cint
from auracrm.cache import cached
from caps.utils.resolver import require_capability


def _period_start(period):
    """Convert period name ('week', 'quarter', 'month') to a start date."""
    today = getdate(now_datetime())
    if period == "week":
        return add_days(today, -7)
    if period == "quarter":
        return add_days(today, -90)
    return add_days(today, -30)


@frappe.whitelist()
@cached(ttl=90, key_prefix="analytics:kpis")
def get_dashboard_kpis(period="month"):
    """Get KPI data — single aggregated query per DocType."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("analytics:dashboard:view")
    start = _period_start(period)

    # One query for all Lead KPIs
    lead_stats = frappe.db.sql("""
        SELECT
            COUNT(*) AS new_leads,
            SUM(CASE WHEN status = 'Converted' AND modified >= %(start)s THEN 1 ELSE 0 END) AS converted_leads
        FROM `tabLead`
        WHERE creation >= %(start)s
    """, {"start": start}, as_dict=True)[0]

    # One query for all Opportunity KPIs
    opp_stats = frappe.db.sql("""
        SELECT
            COUNT(CASE WHEN creation >= %(start)s THEN 1 END) AS new_opportunities,
            COUNT(CASE WHEN status = 'Converted' AND modified >= %(start)s THEN 1 END) AS won_opportunities,
            COUNT(CASE WHEN status = 'Lost' AND modified >= %(start)s THEN 1 END) AS lost_opportunities,
            COALESCE(SUM(CASE WHEN status = 'Open' THEN opportunity_amount ELSE 0 END), 0) AS pipeline_value
        FROM `tabOpportunity`
        WHERE creation >= %(start)s OR status = 'Open'
    """, {"start": start}, as_dict=True)[0]

    new_leads = cint(lead_stats.new_leads)
    converted = cint(lead_stats.converted_leads)

    return {
        "new_leads": new_leads,
        "converted_leads": converted,
        "new_opportunities": cint(opp_stats.new_opportunities),
        "won_opportunities": cint(opp_stats.won_opportunities),
        "lost_opportunities": cint(opp_stats.lost_opportunities),
        "pipeline_value": float(opp_stats.pipeline_value or 0),
        "conversion_rate": round((converted / max(new_leads, 1)) * 100, 1),
    }


@frappe.whitelist()
@cached(ttl=120, key_prefix="analytics:agent_perf")
def get_agent_performance(period="month"):
    """Per-agent metrics — single aggregated SQL instead of N+1 loops."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("analytics:agent_performance:view")
    start = _period_start(period)

    # One query: group by lead_owner, get assigned + converted counts
    rows = frappe.db.sql("""
        SELECT
            l.lead_owner AS agent,
            u.full_name,
            u.user_image AS avatar,
            COUNT(*) AS leads_assigned,
            SUM(CASE WHEN l.status = 'Converted' AND l.modified >= %(start)s THEN 1 ELSE 0 END) AS leads_converted
        FROM `tabLead` l
        JOIN `tabUser` u ON u.name = l.lead_owner AND u.enabled = 1
        WHERE l.creation >= %(start)s
          AND l.lead_owner IS NOT NULL AND l.lead_owner != ''
        GROUP BY l.lead_owner, u.full_name, u.user_image
        ORDER BY leads_converted DESC
    """, {"start": start}, as_dict=True)

    for r in rows:
        r["leads_assigned"] = cint(r.leads_assigned)
        r["leads_converted"] = cint(r.leads_converted)
        r["conversion_rate"] = round(
            (r["leads_converted"] / max(r["leads_assigned"], 1)) * 100, 1
        )

    return sorted(rows, key=lambda x: x["conversion_rate"], reverse=True)


@frappe.whitelist()
@cached(ttl=180, key_prefix="analytics:overview")
def get_overview():
    """System-wide AuraCRM stats — single compound query."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("analytics:overview:view")
    stats = frappe.db.sql("""
        SELECT
            (SELECT COUNT(*) FROM `tabLead`) AS total_leads,
            (SELECT COUNT(*) FROM `tabOpportunity`) AS total_opportunities,
            (SELECT COUNT(*) FROM `tabSLA Breach Log` WHERE resolved = 0) AS active_breaches,
            (SELECT COUNT(*) FROM `tabCRM Automation Rule` WHERE enabled = 1) AS active_automation_rules,
            (SELECT COUNT(*) FROM `tabLead Scoring Rule` WHERE enabled = 1) AS scoring_rules,
            (SELECT COUNT(*) FROM `tabLead Distribution Rule` WHERE enabled = 1) AS distribution_rules,
            (SELECT COUNT(*) FROM `tabSLA Policy` WHERE enabled = 1) AS sla_policies,
            (SELECT COUNT(*) FROM `tabLead` WHERE creation >= %(month_start)s) AS leads_this_month,
            (SELECT COUNT(*) FROM `tabLead` WHERE status = 'Converted' AND modified >= %(month_start)s) AS conversions_this_month
    """, {"month_start": add_days(getdate(now_datetime()), -30)}, as_dict=True)[0]

    return {k: cint(v) for k, v in stats.items()}
