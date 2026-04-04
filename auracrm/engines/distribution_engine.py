# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM - Lead Distribution Engine (Phase 2 - Full Implementation)
===================================================================
Seven distribution methods:
  1. round_robin          - simple cyclic rotation
  2. weighted_round_robin - agents with higher weight receive more
  3. skill_based          - match lead attributes to agent skills
  4. geographic           - match lead territory/city to agent territory
  5. load_based           - least-current-workload wins
  6. performance_based    - higher conversion-rate agents get more
  7. manual_pool          - no auto-assign, goes to shared pool
"""
import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate, cint, flt
import json, re


# ---- Hook Entry Points ----

def auto_assign_lead(doc, method=None):
    """Hook: after_insert on Lead — auto-assign via active distribution rules."""
    if getattr(doc.flags, "skip_auto_assign", False):
        return
    if doc.lead_owner:
        return
    try:
        settings = frappe.get_cached_doc("AuraCRM Settings")
        if not cint(settings.get("auto_assign_on_create")):
            return
    except Exception:
        return

    rules = _get_active_rules("Lead")
    if not rules:
        return
    agent = _find_best_agent(doc, rules)
    if agent:
        doc.db_set("lead_owner", agent, update_modified=False)
        _publish_assignment(doc.doctype, doc.name, agent)
        _log_assignment(doc.doctype, doc.name, agent, rules[0].name)


def auto_assign_opportunity(doc, method=None):
    """Hook: after_insert on Opportunity — auto-assign via active distribution rules."""
    if getattr(doc.flags, "skip_auto_assign", False):
        return
    if doc.get("_assign"):
        return
    try:
        settings = frappe.get_cached_doc("AuraCRM Settings")
        if not cint(settings.get("auto_assign_on_create")):
            return
    except Exception:
        return

    rules = _get_active_rules("Opportunity")
    if not rules:
        return
    agent = _find_best_agent(doc, rules)
    if agent:
        doc.db_set("_assign", json.dumps([agent]), update_modified=False)
        _publish_assignment(doc.doctype, doc.name, agent)


def rebalance_workload():
    """Daily scheduler - redistribute leads from overloaded agents."""
    try:
        settings = frappe.get_cached_doc("AuraCRM Settings")
        if not cint(settings.get("rebalance_enabled")):
            return
    except Exception:
        return

    rules = _get_active_rules("Lead")
    for rule in rules:
        agents_data = _get_rule_agents_with_meta(rule.name)
        if len(agents_data) < 2:
            continue

        # Batch load counts
        load_map = _batch_agent_open_counts([a["email"] for a in agents_data])
        for ad in agents_data:
            ad["load"] = load_map.get(ad["email"], 0)

        avg_load = sum(a["load"] for a in agents_data) / len(agents_data)
        overloaded = [a for a in agents_data if a["load"] > avg_load * 1.5 and a["load"] > a["max_load"]]
        underloaded = sorted(
            [a for a in agents_data if a["load"] < avg_load * 0.75],
            key=lambda x: x["load"],
        )
        if not overloaded or not underloaded:
            continue

        for over_agent in overloaded:
            excess = int(over_agent["load"] - avg_load)
            if excess <= 0:
                continue
            leads_to_move = frappe.get_all(
                "Lead",
                filters={"lead_owner": over_agent["email"], "status": ["in", ["Open", "Replied"]]},
                fields=["name"],
                order_by="aura_score asc",
                limit=excess,
            )
            for lead in leads_to_move:
                if not underloaded:
                    break
                target = underloaded[0]
                frappe.db.set_value("Lead", lead.name, "lead_owner", target["email"], update_modified=False)
                target["load"] += 1
                if target["load"] >= avg_load:
                    underloaded.pop(0)

    frappe.db.commit()


# ---- Rule & Agent Fetching ----

def _get_active_rules(doctype):
    """Fetch enabled distribution rules for the given DocType, ordered by priority."""
    return frappe.get_all(
        "Lead Distribution Rule",
        filters={"enabled": 1, "applies_to": doctype},
        fields=["*"],
        order_by="priority asc",
    )


def _get_rule_agents(rule_name):
    """Return list of available agent emails for a rule (batch workload check)."""
    rows = frappe.get_all(
        "Distribution Agent",
        filters={"parent": rule_name, "parenttype": "Lead Distribution Rule"},
        fields=["agent_email", "weight", "max_load", "skills"],
        order_by="idx asc",
    )
    emails = [r.agent_email for r in rows if r.agent_email]
    if not emails:
        return []
    # Batch availability + workload
    enabled_map = {r[0]: cint(r[1]) for r in frappe.db.sql(
        "SELECT name, enabled FROM `tabUser` WHERE name IN %(e)s", {"e": emails}
    )}
    load_map = _batch_agent_open_counts(emails)
    available = []
    for r in rows:
        if not r.agent_email:
            continue
        if enabled_map.get(r.agent_email) and load_map.get(r.agent_email, 0) < cint(r.max_load or 999):
            available.append(r.agent_email)
    return available


def _get_rule_agents_with_meta(rule_name):
    """Return agent dicts with email, weight, max_load, and skills."""
    rows = frappe.get_all(
        "Distribution Agent",
        filters={"parent": rule_name, "parenttype": "Lead Distribution Rule"},
        fields=["agent_email", "weight", "max_load", "skills"],
        order_by="idx asc",
    )
    result = []
    for r in rows:
        if not r.agent_email:
            continue
        result.append({
            "email": r.agent_email,
            "weight": cint(r.weight) or 1,
            "max_load": cint(r.max_load) or 50,
            "skills": [s.strip().lower() for s in (r.skills or "").split(",") if s.strip()],
        })
    return result


def _is_agent_available(agent_email):
    """Check if a User is enabled (returns 0 or 1)."""
    return cint(frappe.db.get_value("User", agent_email, "enabled"))


def _agent_open_count(agent_email):
    """Count open leads + opportunities for a single agent (2 queries)."""
    leads = frappe.db.count("Lead", {"lead_owner": agent_email, "status": ["in", ["Open", "Replied"]]})
    opps = frappe.db.count("Opportunity", {"_assign": ["like", "%%%s%%" % agent_email], "status": "Open"})
    return leads + opps


def _batch_agent_open_counts(emails):
    """Batch: open workload for multiple agents in 2 queries instead of 2*N."""
    if not emails:
        return {}

    lead_map = {}
    for row in frappe.db.sql("""
        SELECT lead_owner, COUNT(*) AS cnt
        FROM `tabLead`
        WHERE lead_owner IN %(users)s AND status IN ('Open', 'Replied')
        GROUP BY lead_owner
    """, {"users": emails}, as_dict=True):
        lead_map[row.lead_owner] = cint(row.cnt)

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

    return {e: lead_map.get(e, 0) + opp_map.get(e, 0) for e in emails}


# ---- Dispatcher ----

def _find_best_agent(doc, rules):
    """Iterate rules in priority order and return the first matching agent."""
    for rule in rules:
        method = rule.get("distribution_method", "round_robin")
        agent = None
        if method == "round_robin":
            agent = _round_robin(rule)
        elif method == "weighted_round_robin":
            agent = _weighted_round_robin(rule)
        elif method == "skill_based":
            agent = _skill_based(doc, rule)
        elif method == "geographic":
            agent = _geographic(doc, rule)
        elif method == "load_based":
            agent = _load_based(rule)
        elif method == "performance_based":
            agent = _performance_based(rule)
        elif method == "manual_pool":
            return None
        if agent:
            return agent
    return None


# ---- Distribution Methods ----

def _round_robin(rule):
    """Simple cyclic rotation — pick the next available agent."""
    agents = _get_rule_agents(rule.name)
    if not agents:
        return None
    cache_key = "auracrm_rr_%s" % rule.name
    last_idx = cint(frappe.cache.get_value(cache_key))
    next_idx = (last_idx + 1) % len(agents)
    frappe.cache.set_value(cache_key, next_idx)
    return agents[next_idx]


def _weighted_round_robin(rule):
    """Weighted rotation — agents with higher weight appear more in expanded list."""
    agents_meta = _get_rule_agents_with_meta(rule.name)
    if not agents_meta:
        return None
    emails = [a["email"] for a in agents_meta]
    enabled_map = {r[0]: cint(r[1]) for r in frappe.db.sql(
        "SELECT name, enabled FROM `tabUser` WHERE name IN %(e)s", {"e": emails}
    )}
    load_map = _batch_agent_open_counts(emails)
    agents_meta = [a for a in agents_meta if enabled_map.get(a["email"]) and load_map.get(a["email"], 0) < a["max_load"]]
    if not agents_meta:
        return None
    expanded = []
    for a in agents_meta:
        expanded.extend([a["email"]] * max(1, a["weight"]))
    cache_key = "auracrm_wrr_%s" % rule.name
    last_idx = cint(frappe.cache.get_value(cache_key))
    next_idx = (last_idx + 1) % len(expanded)
    frappe.cache.set_value(cache_key, next_idx)
    return expanded[next_idx]


def _skill_based(doc, rule):
    """Match lead attributes (source, industry, city, etc.) to agent skills."""
    agents_meta = _get_rule_agents_with_meta(rule.name)
    if not agents_meta:
        return None
    emails = [a["email"] for a in agents_meta]
    enabled_map = {r[0]: cint(r[1]) for r in frappe.db.sql(
        "SELECT name, enabled FROM `tabUser` WHERE name IN %(e)s", {"e": emails}
    )}
    load_map = _batch_agent_open_counts(emails)
    agents_meta = [a for a in agents_meta if enabled_map.get(a["email"]) and load_map.get(a["email"], 0) < a["max_load"]]
    if not agents_meta:
        return None

    lead_tags = set()
    for field in ["source", "industry", "language", "company_name", "territory", "city"]:
        val = (doc.get(field) or "").lower()
        for token in re.split(r"[\s,/\-]+", val):
            if token and len(token) > 2:
                lead_tags.add(token)
        if val:
            lead_tags.add(val)

    scored = []
    for a in agents_meta:
        overlap = len(lead_tags & set(a["skills"]))
        scored.append((a["email"], overlap, load_map.get(a["email"], 0)))

    scored.sort(key=lambda x: (-x[1], x[2]))
    return scored[0][0] if scored else None


def _geographic(doc, rule):
    """Match lead city/territory/country to agent geographic skills."""
    agents_meta = _get_rule_agents_with_meta(rule.name)
    if not agents_meta:
        return None
    emails = [a["email"] for a in agents_meta]
    enabled_map = {r[0]: cint(r[1]) for r in frappe.db.sql(
        "SELECT name, enabled FROM `tabUser` WHERE name IN %(e)s", {"e": emails}
    )}
    load_map = _batch_agent_open_counts(emails)
    agents_meta = [a for a in agents_meta if enabled_map.get(a["email"]) and load_map.get(a["email"], 0) < a["max_load"]]
    if not agents_meta:
        return None

    lead_city = (doc.get("city") or doc.get("territory") or "").lower().strip()
    lead_country = (doc.get("country") or "").lower().strip()

    if not lead_city and not lead_country:
        return _load_based(rule)

    scored = []
    for a in agents_meta:
        geo_score = 0
        for skill in a["skills"]:
            if lead_city and skill == lead_city:
                geo_score += 10
            elif lead_country and skill == lead_country:
                geo_score += 5
            elif lead_city and skill in lead_city:
                geo_score += 3
        scored.append((a["email"], geo_score, load_map.get(a["email"], 0)))

    scored.sort(key=lambda x: (-x[1], x[2]))
    return scored[0][0] if scored else None


def _load_based(rule):
    """Least-workload-first — assign to the agent with fewest open items."""
    agents = _get_rule_agents(rule.name)
    if not agents:
        return None
    load_map = _batch_agent_open_counts(agents)
    loads = [(agent, load_map.get(agent, 0)) for agent in agents]
    loads.sort(key=lambda x: x[1])
    return loads[0][0] if loads else None


def _performance_based(rule):
    """Score agents by 30-day conversion rate (70%) + remaining capacity (30%)."""
    agents_meta = _get_rule_agents_with_meta(rule.name)
    if not agents_meta:
        return None
    emails = [a["email"] for a in agents_meta]
    enabled_map = {r[0]: cint(r[1]) for r in frappe.db.sql(
        "SELECT name, enabled FROM `tabUser` WHERE name IN %(e)s", {"e": emails}
    )}
    load_map = _batch_agent_open_counts(emails)
    agents_meta = [a for a in agents_meta if enabled_map.get(a["email"]) and load_map.get(a["email"], 0) < a["max_load"]]
    if not agents_meta:
        return None

    start = add_days(getdate(now_datetime()), -30)
    agent_emails = [a["email"] for a in agents_meta]

    # Batch: assigned + converted counts
    assigned_map = {}
    for row in frappe.db.sql("""
        SELECT lead_owner, COUNT(*) AS cnt FROM `tabLead`
        WHERE lead_owner IN %(agents)s AND creation >= %(start)s
        GROUP BY lead_owner
    """, {"agents": agent_emails, "start": start}, as_dict=True):
        assigned_map[row.lead_owner] = cint(row.cnt)

    converted_map = {}
    for row in frappe.db.sql("""
        SELECT lead_owner, COUNT(*) AS cnt FROM `tabLead`
        WHERE lead_owner IN %(agents)s AND status = 'Converted' AND modified >= %(start)s
        GROUP BY lead_owner
    """, {"agents": agent_emails, "start": start}, as_dict=True):
        converted_map[row.lead_owner] = cint(row.cnt)

    scored = []
    for a in agents_meta:
        assigned = assigned_map.get(a["email"], 0) or 1
        converted = converted_map.get(a["email"], 0)
        rate = converted / max(assigned, 1)
        capacity = 1 - (load_map.get(a["email"], 0) / max(a["max_load"], 1))
        performance = rate * 0.7 + capacity * 0.3
        scored.append((a["email"], performance))

    scored.sort(key=lambda x: -x[1])
    return scored[0][0] if scored else None


# ---- Helpers ----

def _publish_assignment(doctype, name, agent):
    """Emit real-time event so the agent's UI shows a new assignment."""
    frappe.publish_realtime(
        "auracrm_lead_assigned",
        {"doctype": doctype, "name": name, "agent": agent},
        user=agent,
    )


def _log_assignment(doctype, name, agent, rule_name):
    """Create a Comment on the document recording the auto-assignment."""
    try:
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": doctype,
            "reference_name": name,
            "content": "Auto-assigned to <b>%s</b> via rule <b>%s</b>" % (agent, rule_name),
        }).insert(ignore_permissions=True)
    except Exception:
        pass
