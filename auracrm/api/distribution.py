# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""AuraCRM — Distribution API (Phase 5: Performance Optimized)"""
import frappe
from frappe import _
from frappe.utils import cint
from auracrm.cache import cached
from caps.utils.resolver import require_capability


@frappe.whitelist()
@cached(ttl=60, key_prefix="dist:stats")
def get_distribution_stats():
    """Get lead distribution statistics — batch queries instead of per-agent loop."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("distribution:stats:view")
    agents = frappe.db.sql("""
        SELECT DISTINCT u.name, u.full_name, u.user_image
        FROM `tabUser` u
        JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE u.enabled = 1 AND u.user_type = 'System User'
          AND hr.role IN ('Sales User', 'Sales Agent', 'Sales Manager')
    """, as_dict=True)

    if not agents:
        return []

    emails = [a.name for a in agents]

    # Batch: open leads per owner
    lead_map = {}
    for row in frappe.db.sql("""
        SELECT lead_owner, COUNT(*) AS cnt
        FROM `tabLead`
        WHERE lead_owner IN %(users)s AND status IN ('Open', 'Replied')
        GROUP BY lead_owner
    """, {"users": emails}, as_dict=True):
        lead_map[row.lead_owner] = cint(row.cnt)

    # Batch: open opps per assignee
    opp_map = {}
    for row in frappe.db.sql("""
        SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(_assign, '"', 2), '"', -1) AS agent,
               COUNT(*) AS cnt
        FROM `tabOpportunity`
        WHERE status = 'Open' AND _assign IS NOT NULL AND _assign != '[]'
        GROUP BY agent
    """, as_dict=True):
        if row.agent in emails:
            opp_map[row.agent] = cint(row.cnt)

    result = []
    for a in agents:
        leads = lead_map.get(a.name, 0)
        opps = opp_map.get(a.name, 0)
        result.append({
            "agent": a.name,
            "full_name": a.full_name,
            "avatar": a.user_image,
            "open_leads": leads,
            "open_opportunities": opps,
            "total_workload": leads + opps,
        })
    return sorted(result, key=lambda x: x["total_workload"], reverse=True)


@frappe.whitelist()
def manually_assign(doctype, name, agent):
    """Manually assign a lead or opportunity to an agent."""
    require_capability("distribution:manual_assign")
    frappe.has_permission(doctype, "write", throw=True)
    if doctype == "Lead":
        frappe.db.set_value("Lead", name, "lead_owner", agent)
    elif doctype == "Opportunity":
        frappe.db.set_value("Opportunity", name, "_assign", frappe.as_json([agent]))

    frappe.publish_realtime("auracrm_manual_assign", {
        "doctype": doctype, "name": name, "agent": agent,
    }, user=agent)
    return {"status": "ok"}


@frappe.whitelist()
def get_next_agent(rule_name):
    """Preview which agent would be assigned next by a distribution rule.

    Called from Lead Distribution Rule 'Test Distribution' button.
    """
    require_capability("distribution:preview_next")
    frappe.has_permission("Lead Distribution Rule", "read", throw=True)

    if not frappe.db.exists("Lead Distribution Rule", rule_name):
        frappe.throw(_("Rule {0} not found").format(rule_name))

    rule = frappe.get_doc("Lead Distribution Rule", rule_name)

    if not rule.enabled:
        return {"agent": None, "message": _("Rule is disabled")}

    agents = []
    for agent_row in rule.agents:
        if not agent_row.get("enabled", 1):
            continue
        user = agent_row.agent
        if not frappe.db.get_value("User", user, "enabled"):
            continue
        open_leads = frappe.db.count("Lead", {"lead_owner": user, "status": ["in", ["Open", "Replied"]]})
        agents.append({
            "agent": user,
            "full_name": frappe.db.get_value("User", user, "full_name") or user,
            "open_leads": open_leads,
            "weight": agent_row.get("weight", 1),
        })

    if not agents:
        return {"agent": None, "message": _("No available agents in this rule")}

    method = rule.distribution_method or "round_robin"

    if method == "round_robin":
        # Pick the agent with fewest open leads
        agents.sort(key=lambda a: a["open_leads"])
        selected = agents[0]
    elif method == "weighted_round_robin":
        # Weight-adjusted load: open_leads / weight → pick lowest
        for a in agents:
            a["adjusted_load"] = a["open_leads"] / max(a["weight"], 1)
        agents.sort(key=lambda a: a["adjusted_load"])
        selected = agents[0]
    elif method == "load_based":
        agents.sort(key=lambda a: a["open_leads"])
        selected = agents[0]
    else:
        selected = agents[0]

    return {
        "agent": selected["agent"],
        "full_name": selected["full_name"],
        "open_leads": selected["open_leads"],
        "method": method,
        "available_agents": len(agents),
    }
