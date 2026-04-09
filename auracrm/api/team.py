# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Team Management API (Phase 5: Performance Optimized)
================================================================
N+1 query loops replaced with aggregated SQL.
"""
import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate, cint, flt
from auracrm.cache import cached
from caps.utils.resolver import require_capability


@frappe.whitelist()
@cached(ttl=120, key_prefix="team:overview")
def get_team_overview():
    """Team overview — batch queries instead of per-agent loops."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("team:overview:view")
    # Step 1: Get sales users via Has Role (single query)
    sales_users = frappe.db.sql("""
        SELECT DISTINCT u.name, u.full_name, u.user_image
        FROM `tabUser` u
        JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE u.enabled = 1
          AND u.user_type = 'System User'
          AND hr.role IN ('Sales User', 'Sales Agent', 'Sales Manager')
    """, as_dict=True)

    if not sales_users:
        return []

    user_emails = [u.name for u in sales_users]

    # Step 2: Batch query — open leads per owner
    lead_counts = {}
    for row in frappe.db.sql("""
        SELECT lead_owner, COUNT(*) AS cnt
        FROM `tabLead`
        WHERE lead_owner IN %(users)s
          AND status NOT IN ('Converted', 'Do Not Contact')
        GROUP BY lead_owner
    """, {"users": user_emails}, as_dict=True):
        lead_counts[row.lead_owner] = cint(row.cnt)

    # Step 3: Batch query — open opps per assignee
    opp_counts = {}
    for row in frappe.db.sql("""
        SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(_assign, '"', 2), '"', -1) AS agent,
               COUNT(*) AS cnt
        FROM `tabOpportunity`
        WHERE status NOT IN ('Closed', 'Lost', 'Converted')
          AND _assign IS NOT NULL AND _assign != '[]'
        GROUP BY agent
    """, as_dict=True):
        if row.agent in user_emails:
            opp_counts[row.agent] = cint(row.cnt)

    # Step 4: Batch roles lookup
    user_roles_map = {}
    for row in frappe.db.sql("""
        SELECT parent, role FROM `tabHas Role`
        WHERE parent IN %(users)s
          AND role IN ('Sales User', 'Sales Agent', 'Sales Manager', 'Quality Analyst')
    """, {"users": user_emails}, as_dict=True):
        user_roles_map.setdefault(row.parent, []).append(row.role)

    result = []
    for u in sales_users:
        roles = user_roles_map.get(u.name, [])
        open_leads = lead_counts.get(u.name, 0)
        open_opps = opp_counts.get(u.name, 0)
        result.append({
            "agent": u.name,
            "full_name": u.full_name,
            "avatar": u.user_image,
            "roles": roles,
            "is_manager": "Sales Manager" in roles,
            "open_leads": open_leads,
            "open_opportunities": open_opps,
            "workload": open_leads + open_opps,
        })

    result.sort(key=lambda x: x["workload"], reverse=True)
    return result


@frappe.whitelist()
def get_agent_detail(agent):
    """Get detailed stats for a single agent — batch query."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("team:agent_detail:view")
    today = getdate(now_datetime())
    month_start = today.replace(day=1)

    stats = frappe.db.sql("""
        SELECT
            (SELECT COUNT(*) FROM `tabLead`
             WHERE _assign LIKE %(like_agent)s AND creation >= %(month)s) AS leads_this_month,
            (SELECT COUNT(*) FROM `tabLead`
             WHERE lead_owner = %(agent)s AND status = 'Converted' AND modified >= %(month)s) AS conversions,
            (SELECT COUNT(*) FROM `tabCommunication`
             WHERE sender = %(agent)s AND creation >= %(month)s) AS communications,
            (SELECT COUNT(*) FROM `tabSLA Breach Log`
             WHERE assigned_to = %(agent)s AND resolved = 0) AS open_breaches
    """, {"agent": agent, "like_agent": f"%%{agent}%%", "month": month_start}, as_dict=True)[0]

    # Latest scorecard
    scorecard = frappe.get_all(
        "Agent Scorecard",
        filters={"agent_email": agent},
        fields=["name", "date", "overall_score", "leads_assigned",
                "leads_converted", "avg_response_time_minutes"],
        order_by="date desc",
        limit=1,
    )

    leads = cint(stats.leads_this_month)
    convs = cint(stats.conversions)

    return {
        "agent": agent,
        "leads_this_month": leads,
        "conversions": convs,
        "communications": cint(stats.communications),
        "open_breaches": cint(stats.open_breaches),
        "conversion_rate": round((convs / leads * 100) if leads else 0, 1),
        "latest_scorecard": scorecard[0] if scorecard else None,
    }


def calculate_daily_scorecards():
    """Scheduled: calculate daily agent scorecards at midnight."""
    today = getdate(now_datetime())
    yesterday = add_days(today, -1)

    agents = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name"],
    )

    for agent in agents:
        roles = frappe.get_roles(agent.name)
        if not any(r in roles for r in ["Sales User", "Sales Agent"]):
            continue

        # Skip if already calculated for today
        if frappe.db.exists("Agent Scorecard", {"agent_email": agent.name, "date": today}):
            continue

        _create_scorecard(agent.name, today, yesterday)

    frappe.db.commit()


def _create_scorecard(agent, today, yesterday):
    """Create a single agent scorecard for the period."""
    month_start = today.replace(day=1)

    # Leads handled (assigned)
    leads_handled = frappe.db.count("Lead", {
        "_assign": ["like", "%%%s%%" % agent],
        "creation": [">=", month_start],
    })

    # Conversions
    conversions = frappe.db.count("Lead", {
        "lead_owner": agent,
        "status": "Converted",
        "modified": [">=", month_start],
    })

    # Communications sent
    comms_sent = frappe.db.count("Communication", {
        "sender": agent,
        "creation": [">=", month_start],
    })

    # SLA breaches (unresolved)
    breaches = frappe.db.count("SLA Breach Log", {
        "assigned_to": agent,
        "creation": [">=", month_start],
    })

    # Calculate composite score (0-100)
    score = 0
    # Conversion rate component (max 40 points)
    if leads_handled:
        conv_rate = conversions / leads_handled
        score += min(conv_rate * 100 * 0.4, 40)

    # Activity component (max 30 points) - based on communications
    score += min(comms_sent * 2, 30)

    # SLA compliance (max 30 points) - deduct for breaches
    sla_score = max(30 - breaches * 5, 0)
    score += sla_score

    score = max(0, min(round(score), 100))

    try:
        frappe.get_doc({
            "doctype": "Agent Scorecard",
            "agent_email": agent,
            "date": today,
            "overall_score": score,
            "leads_assigned": leads_handled,
            "leads_converted": conversions,
            "messages_sent": comms_sent,
            "conversion_rate": round((conversions / leads_handled * 100) if leads_handled else 0, 1),
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error("AuraCRM: Failed to create scorecard for %s" % agent)


@frappe.whitelist()
def recalculate_agent_scores(agent=None):
    """Manually recalculate agent scorecards — callable from Team Dashboard.

    If agent is specified, recalculate for that agent only.
    Otherwise, recalculate for all sales agents.
    """
    require_capability("team:recalculate_scores")
    frappe.has_permission("Agent Scorecard", "create", throw=True)

    today = getdate(now_datetime())
    yesterday = add_days(today, -1)

    if agent:
        # Single agent
        _create_scorecard(agent, today, yesterday)
        frappe.db.commit()
        return {"status": "ok", "message": _("Scorecard recalculated for {0}").format(agent)}

    # All agents
    agents = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name"],
    )

    count = 0
    for a in agents:
        roles = frappe.get_roles(a.name)
        if not any(r in roles for r in ["Sales User", "Sales Agent"]):
            continue
        # Delete existing scorecard for today to allow recalculation
        existing = frappe.db.exists("Agent Scorecard", {"agent_email": a.name, "date": today})
        if existing:
            frappe.delete_doc("Agent Scorecard", existing, ignore_permissions=True)
        _create_scorecard(a.name, today, yesterday)
        count += 1

    frappe.db.commit()
    return {"status": "ok", "message": _("Scorecards recalculated for {0} agents").format(count)}
