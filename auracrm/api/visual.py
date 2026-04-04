# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Visual Graph API
============================
Endpoints that return nodes/edges data for frappe_visual GraphEngine.
Each endpoint produces the { nodes: [...], edges: [...] } format
consumed directly by `new GraphEngine({ nodes, edges })`.

All data is shaped for Cytoscape.js via frappe_visual conventions:
  node: { id, label, type, parent?, doctype?, docname?, status?, meta?, summary?, icon?, badge? }
  edge: { source, target, label?, type?, animated?, color? }
"""
import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate, cint, flt, fmt_money
from auracrm.cache import cached
from caps.utils.resolver import require_capability


# ═══════════════════════════════════════════════════════════════════
# 1. COMMAND CENTER — CRM module map + live KPIs as graph nodes
# ═══════════════════════════════════════════════════════════════════
@frappe.whitelist()
@cached(ttl=60, key_prefix="visual:command_center")
def get_command_center_graph():
    """
    Returns a radial graph with AuraCRM as the central node.
    Each major module is a child node with live counts.
    Edges connect central → module nodes.
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("analytics:dashboard:view")
    start = add_days(getdate(now_datetime()), -30)

    # ── Batch-query all module counts in one go ───────────────────
    stats = frappe.db.sql("""
        SELECT
            (SELECT COUNT(*) FROM `tabLead` WHERE creation >= %(start)s) AS new_leads,
            (SELECT COUNT(*) FROM `tabLead` WHERE status = 'Converted' AND modified >= %(start)s) AS converted_leads,
            (SELECT COUNT(*) FROM `tabLead` WHERE status NOT IN ('Converted','Do Not Contact')) AS active_leads,
            (SELECT COUNT(*) FROM `tabOpportunity` WHERE status = 'Open') AS open_opps,
            (SELECT COALESCE(SUM(opportunity_amount),0) FROM `tabOpportunity` WHERE status = 'Open') AS pipeline_value,
            (SELECT COUNT(*) FROM `tabOpportunity` WHERE status = 'Converted' AND modified >= %(start)s) AS won_opps,
            (SELECT COUNT(*) FROM `tabSLA Breach Log` WHERE resolved = 0) AS sla_breaches,
            (SELECT COUNT(*) FROM `tabSLA Policy` WHERE enabled = 1) AS sla_policies,
            (SELECT COUNT(*) FROM `tabCRM Automation Rule` WHERE enabled = 1) AS automations,
            (SELECT COUNT(*) FROM `tabCampaign Sequence`) AS sequences,
            (SELECT COUNT(*) FROM `tabAuto Dialer Campaign`) AS dialer_campaigns,
            (SELECT COUNT(*) FROM `tabLead Scoring Rule` WHERE enabled = 1) AS scoring_rules,
            (SELECT COUNT(*) FROM `tabLead Distribution Rule` WHERE enabled = 1) AS dist_rules,
            (SELECT COUNT(*) FROM `tabMarketing List`) AS marketing_lists,
            (SELECT COUNT(*) FROM `tabAgent Scorecard` WHERE period_date >= %(start)s) AS scorecards
    """, {"start": start}, as_dict=True)[0]

    # Active users count
    agent_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT u.name) AS cnt
        FROM `tabUser` u
        JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE u.enabled = 1 AND hr.role IN ('Sales User','Sales Agent','Sales Manager')
    """, as_dict=True)[0].cnt or 0

    nodes = []
    edges = []

    # ── Central Hub Node ──────────────────────────────────────────
    nodes.append({
        "id": "hub",
        "label": "AuraCRM",
        "type": "crm-hub",
        "icon": "✦",
        "status": "active",
        "summary": {
            "Active Leads": cint(stats.active_leads),
            "Open Deals": cint(stats.open_opps),
            "Agents": cint(agent_count),
        },
    })

    # ── Module Definitions ────────────────────────────────────────
    modules = [
        {
            "id": "leads",
            "label": _("Leads"),
            "type": "crm-leads",
            "icon": "👤",
            "route": "List/Lead",
            "value": cint(stats.active_leads),
            "badge": f"+{cint(stats.new_leads)}",
            "summary": {
                "Active": cint(stats.active_leads),
                "New (30d)": cint(stats.new_leads),
                "Converted": cint(stats.converted_leads),
            },
        },
        {
            "id": "pipeline",
            "label": _("Pipeline"),
            "type": "crm-pipeline",
            "icon": "🔄",
            "route": "auracrm-pipeline",
            "value": cint(stats.open_opps),
            "badge": fmt_money(flt(stats.pipeline_value), currency=frappe.defaults.get_global_default("currency") or "USD"),
            "summary": {
                "Open Deals": cint(stats.open_opps),
                "Won (30d)": cint(stats.won_opps),
                "Value": fmt_money(flt(stats.pipeline_value), currency=frappe.defaults.get_global_default("currency") or "USD"),
            },
        },
        {
            "id": "team",
            "label": _("Team"),
            "type": "crm-team",
            "icon": "👥",
            "route": "auracrm-team",
            "value": cint(agent_count),
            "badge": f"{cint(stats.scorecards)} scorecards",
            "summary": {
                "Agents": cint(agent_count),
                "Scorecards": cint(stats.scorecards),
            },
        },
        {
            "id": "automation",
            "label": _("Automation"),
            "type": "crm-automation",
            "icon": "🤖",
            "route": "List/CRM Automation Rule",
            "value": cint(stats.automations),
            "badge": f"{cint(stats.sequences)} sequences",
            "summary": {
                "Active Rules": cint(stats.automations),
                "Sequences": cint(stats.sequences),
            },
        },
        {
            "id": "sla",
            "label": _("SLA"),
            "type": "crm-sla",
            "icon": "⏱️",
            "route": "List/SLA Breach Log",
            "value": cint(stats.sla_policies),
            "badge": f"{cint(stats.sla_breaches)} breaches" if stats.sla_breaches else "✓ OK",
            "status": "warning" if cint(stats.sla_breaches) > 0 else "active",
            "summary": {
                "Policies": cint(stats.sla_policies),
                "Open Breaches": cint(stats.sla_breaches),
            },
        },
        {
            "id": "scoring",
            "label": _("Scoring"),
            "type": "crm-scoring",
            "icon": "📊",
            "route": "List/Lead Scoring Rule",
            "value": cint(stats.scoring_rules),
            "summary": {
                "Active Rules": cint(stats.scoring_rules),
            },
        },
        {
            "id": "distribution",
            "label": _("Distribution"),
            "type": "crm-distribution",
            "icon": "📤",
            "route": "List/Lead Distribution Rule",
            "value": cint(stats.dist_rules),
            "summary": {
                "Active Rules": cint(stats.dist_rules),
            },
        },
        {
            "id": "dialer",
            "label": _("Dialer"),
            "type": "crm-dialer",
            "icon": "📞",
            "route": "List/Auto Dialer Campaign",
            "value": cint(stats.dialer_campaigns),
            "summary": {
                "Campaigns": cint(stats.dialer_campaigns),
            },
        },
        {
            "id": "marketing",
            "label": _("Marketing"),
            "type": "crm-marketing",
            "icon": "📢",
            "route": "List/Marketing List",
            "value": cint(stats.marketing_lists),
            "summary": {
                "Lists": cint(stats.marketing_lists),
            },
        },
    ]

    for mod in modules:
        nodes.append({
            "id": mod["id"],
            "label": mod["label"],
            "type": mod["type"],
            "icon": mod.get("icon"),
            "badge": mod.get("badge"),
            "status": mod.get("status", "active"),
            "meta": {"route": mod.get("route"), "value": mod.get("value", 0)},
            "summary": mod.get("summary", {}),
        })
        edges.append({
            "source": "hub",
            "target": mod["id"],
            "type": "flow",
            "animated": True,
        })

    # ── Inter-module flow edges (data relationships) ──────────────
    flow_edges = [
        ("leads", "scoring", _("scored by"), "reference"),
        ("leads", "distribution", _("assigned by"), "reference"),
        ("leads", "pipeline", _("→ opportunity"), "flow"),
        ("pipeline", "team", _("owned by"), "reference"),
        ("automation", "leads", _("triggers"), "flow"),
        ("automation", "pipeline", _("triggers"), "flow"),
        ("sla", "leads", _("monitors"), "reference"),
        ("sla", "pipeline", _("monitors"), "reference"),
        ("dialer", "leads", _("calls"), "flow"),
        ("marketing", "leads", _("generates"), "flow"),
    ]
    for src, tgt, label, etype in flow_edges:
        edges.append({
            "source": src,
            "target": tgt,
            "label": label,
            "type": etype,
        })

    return {"nodes": nodes, "edges": edges}


# ═══════════════════════════════════════════════════════════════════
# 2. PIPELINE FLOW — Stages as layered graph + live opportunity data
# ═══════════════════════════════════════════════════════════════════
@frappe.whitelist()
@cached(ttl=45, key_prefix="visual:pipeline_flow")
def get_pipeline_flow():
    """
    Returns a layered left-to-right graph:
    [Lead Source] → [Stage 1] → [Stage 2] → ... → [Won/Lost]
    Each stage node has live count + value as summary.
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("pipeline:stages:view")

    # Stages
    stages = frappe.get_all("Sales Stage",
        fields=["name", "stage_name"], order_by="idx asc")
    if not stages:
        return {"nodes": [], "edges": []}

    # Aggregated per-stage stats
    agg = {}
    for row in frappe.db.sql("""
        SELECT sales_stage, COUNT(*) AS cnt,
               COALESCE(SUM(opportunity_amount),0) AS total_value
        FROM `tabOpportunity` WHERE status = 'Open' AND sales_stage IS NOT NULL
        GROUP BY sales_stage
    """, as_dict=True):
        agg[row.sales_stage] = row

    # Source stats — where leads come from
    sources = frappe.db.sql("""
        SELECT COALESCE(source, 'Unknown') AS source, COUNT(*) AS cnt
        FROM `tabLead` WHERE creation >= %(start)s
        GROUP BY source ORDER BY cnt DESC LIMIT 5
    """, {"start": add_days(getdate(now_datetime()), -30)}, as_dict=True)

    # Outcome stats
    outcomes = frappe.db.sql("""
        SELECT
            SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS won,
            SUM(CASE WHEN status = 'Lost' THEN 1 ELSE 0 END) AS lost
        FROM `tabOpportunity` WHERE modified >= %(start)s
    """, {"start": add_days(getdate(now_datetime()), -30)}, as_dict=True)[0]

    nodes = []
    edges = []
    currency = frappe.defaults.get_global_default("currency") or "USD"

    # Source nodes
    for src in sources:
        nodes.append({
            "id": f"src-{src.source}",
            "label": src.source,
            "type": "crm-source",
            "icon": "🌐",
            "badge": str(cint(src.cnt)),
            "summary": {"Leads (30d)": cint(src.cnt)},
        })

    # Stage nodes
    prev_id = None
    for i, stage in enumerate(stages):
        data = agg.get(stage.name)
        sid = f"stage-{i}"
        count = cint(data.cnt) if data else 0
        value = flt(data.total_value) if data else 0
        nodes.append({
            "id": sid,
            "label": stage.stage_name or stage.name,
            "type": "crm-stage",
            "icon": "📋",
            "badge": str(count),
            "status": "active" if count > 0 else "disabled",
            "meta": {"stage": stage.name, "count": count, "value": value},
            "summary": {
                "Deals": count,
                "Value": fmt_money(value, currency=currency),
            },
        })
        # Source → first stage
        if i == 0:
            for src in sources:
                edges.append({
                    "source": f"src-{src.source}",
                    "target": sid,
                    "type": "flow",
                    "animated": True,
                })
        # Stage → next stage
        if prev_id:
            edges.append({
                "source": prev_id,
                "target": sid,
                "label": "→",
                "type": "flow",
                "animated": True,
            })
        prev_id = sid

    # Outcome nodes
    won_count = cint(outcomes.won) if outcomes else 0
    lost_count = cint(outcomes.lost) if outcomes else 0

    nodes.append({
        "id": "outcome-won",
        "label": _("Won"),
        "type": "crm-won",
        "icon": "🏆",
        "badge": str(won_count),
        "status": "active",
        "summary": {"Won (30d)": won_count},
    })
    nodes.append({
        "id": "outcome-lost",
        "label": _("Lost"),
        "type": "crm-lost",
        "icon": "❌",
        "badge": str(lost_count),
        "status": "error" if lost_count > 0 else "disabled",
        "summary": {"Lost (30d)": lost_count},
    })

    # Last stage → outcomes
    if prev_id:
        edges.append({"source": prev_id, "target": "outcome-won", "label": _("Won"), "type": "flow", "animated": True})
        edges.append({"source": prev_id, "target": "outcome-lost", "label": _("Lost"), "type": "flow"})

    return {"nodes": nodes, "edges": edges}


# ═══════════════════════════════════════════════════════════════════
# 3. LEAD EXPLORER — Single lead as radial relationship graph
# ═══════════════════════════════════════════════════════════════════
@frappe.whitelist()
def get_lead_explorer(lead_name):
    """
    Returns a radial graph centered on a single Lead.
    Branches out to: Opportunities, Communications, Tasks, SLA,
    Scoring history, Campaign enrollments, etc.
    """
    require_capability("workspace:360:view")

    lead = frappe.get_doc("Lead", lead_name)
    frappe.has_permission("Lead", "read", doc=lead, throw=True)

    nodes = []
    edges = []

    # ── Central Lead Node ─────────────────────────────────────────
    score = cint(lead.get("aura_score") or 0)
    score_type = "crm-lead-hot" if score >= 80 else "crm-lead-warm" if score >= 50 else "crm-lead-cold"

    nodes.append({
        "id": "lead-center",
        "label": lead.lead_name or lead.name,
        "type": score_type,
        "icon": "👤",
        "doctype": "Lead",
        "docname": lead.name,
        "status": "active",
        "badge": f"Score: {score}",
        "summary": {
            "Name": lead.lead_name or "",
            "Company": lead.company_name or "",
            "Source": lead.source or "",
            "Status": lead.status or "",
            "Score": score,
            "Owner": lead.lead_owner or "",
            "Phone": lead.mobile_no or lead.phone or "",
            "Email": lead.email_id or "",
        },
    })

    # ── Owner/Agent Node ──────────────────────────────────────────
    if lead.lead_owner:
        owner_name = frappe.db.get_value("User", lead.lead_owner, "full_name") or lead.lead_owner
        nodes.append({
            "id": "owner",
            "label": owner_name,
            "type": "crm-agent",
            "icon": "👔",
            "doctype": "User",
            "docname": lead.lead_owner,
            "summary": {"Email": lead.lead_owner},
        })
        edges.append({"source": "lead-center", "target": "owner", "label": _("owned by"), "type": "reference"})

    # ── Related Opportunities ─────────────────────────────────────
    opps = frappe.get_all("Opportunity",
        filters={"party_name": lead_name, "opportunity_from": "Lead"},
        fields=["name", "opportunity_amount", "sales_stage", "status", "expected_closing"],
        order_by="modified desc", limit=10)

    if opps:
        # Group node
        nodes.append({
            "id": "opps-group",
            "label": _("Opportunities"),
            "type": "group",
            "icon": "🎯",
            "summary": {"Count": len(opps)},
        })
        edges.append({"source": "lead-center", "target": "opps-group", "label": _("has"), "type": "flow", "animated": True})

        for opp in opps:
            oid = f"opp-{opp.name}"
            opp_status = "active" if opp.status == "Open" else "disabled"
            nodes.append({
                "id": oid,
                "label": opp.name,
                "type": "crm-opportunity",
                "parent": "opps-group",
                "doctype": "Opportunity",
                "docname": opp.name,
                "status": opp_status,
                "badge": opp.sales_stage or "",
                "summary": {
                    "Amount": fmt_money(flt(opp.opportunity_amount), currency=frappe.defaults.get_global_default("currency") or "USD"),
                    "Stage": opp.sales_stage or "",
                    "Status": opp.status or "",
                    "Closing": str(opp.expected_closing or ""),
                },
            })
            edges.append({"source": "opps-group", "target": oid, "type": "child"})

    # ── Communications ────────────────────────────────────────────
    comms = frappe.get_all("Communication",
        filters={"reference_doctype": "Lead", "reference_name": lead_name},
        fields=["name", "communication_type", "communication_medium", "subject", "sender", "creation"],
        order_by="creation desc", limit=10)

    if comms:
        nodes.append({
            "id": "comms-group",
            "label": _("Communications"),
            "type": "group",
            "icon": "💬",
            "summary": {"Count": len(comms)},
        })
        edges.append({"source": "lead-center", "target": "comms-group", "label": _("communicated"), "type": "reference"})

        for comm in comms:
            cid = f"comm-{comm.name}"
            nodes.append({
                "id": cid,
                "label": comm.subject or comm.communication_medium or comm.name,
                "type": "crm-communication",
                "parent": "comms-group",
                "doctype": "Communication",
                "docname": comm.name,
                "icon": "📧" if comm.communication_medium == "Email" else "📞" if comm.communication_medium == "Phone" else "💬",
                "summary": {
                    "Type": comm.communication_type or "",
                    "Medium": comm.communication_medium or "",
                    "Sender": comm.sender or "",
                    "Date": str(comm.creation or ""),
                },
            })
            edges.append({"source": "comms-group", "target": cid, "type": "child"})

    # ── Tasks / ToDos ─────────────────────────────────────────────
    tasks = frappe.get_all("ToDo",
        filters={"reference_type": "Lead", "reference_name": lead_name, "status": "Open"},
        fields=["name", "description", "allocated_to", "date", "priority"],
        order_by="date asc", limit=10)

    if tasks:
        nodes.append({
            "id": "tasks-group",
            "label": _("Tasks"),
            "type": "group",
            "icon": "📝",
            "summary": {"Open": len(tasks)},
        })
        edges.append({"source": "lead-center", "target": "tasks-group", "label": _("tasks"), "type": "reference"})

        for task in tasks:
            tid = f"task-{task.name}"
            nodes.append({
                "id": tid,
                "label": (task.description or task.name)[:40],
                "type": "crm-task",
                "parent": "tasks-group",
                "doctype": "ToDo",
                "docname": task.name,
                "status": "warning" if task.priority == "High" else "active",
                "summary": {
                    "Priority": task.priority or "",
                    "Due": str(task.date or ""),
                    "Assigned": task.allocated_to or "",
                },
            })
            edges.append({"source": "tasks-group", "target": tid, "type": "child"})

    # ── SLA Breaches ──────────────────────────────────────────────
    breaches = frappe.get_all("SLA Breach Log",
        filters={"reference_doctype": "Lead", "reference_name": lead_name},
        fields=["name", "sla_policy", "resolved", "creation"],
        order_by="creation desc", limit=5)

    if breaches:
        nodes.append({
            "id": "sla-group",
            "label": _("SLA"),
            "type": "crm-sla",
            "icon": "⏱️",
            "status": "warning" if any(not b.resolved for b in breaches) else "active",
            "summary": {
                "Total": len(breaches),
                "Open": len([b for b in breaches if not b.resolved]),
            },
        })
        edges.append({"source": "lead-center", "target": "sla-group", "label": _("SLA"), "type": "reference"})

    # ── Score History ─────────────────────────────────────────────
    score_logs = frappe.get_all("Lead Score Log",
        filters={"lead": lead_name},
        fields=["name", "rule_name", "points_change", "new_score", "creation"],
        order_by="creation desc", limit=5)

    if score_logs:
        nodes.append({
            "id": "scoring-group",
            "label": _("Score History"),
            "type": "crm-scoring",
            "icon": "📊",
            "summary": {
                "Current Score": score,
                "Changes": len(score_logs),
            },
        })
        edges.append({"source": "lead-center", "target": "scoring-group", "label": _("scored"), "type": "reference"})

    # ── Nurture Journey ───────────────────────────────────────────
    nurtures = frappe.get_all("Nurture Lead Instance",
        filters={"lead": lead_name},
        fields=["name", "journey", "status", "current_step"],
        limit=3)

    if nurtures:
        nodes.append({
            "id": "nurture-group",
            "label": _("Nurture"),
            "type": "crm-automation",
            "icon": "🌱",
            "summary": {"Journeys": len(nurtures)},
        })
        edges.append({"source": "lead-center", "target": "nurture-group", "label": _("enrolled in"), "type": "flow", "animated": True})

    return {"nodes": nodes, "edges": edges}


# ═══════════════════════════════════════════════════════════════════
# 4. TEAM GRAPH — Org-tree with agent nodes carrying live KPIs
# ═══════════════════════════════════════════════════════════════════
@frappe.whitelist()
@cached(ttl=120, key_prefix="visual:team_graph")
def get_team_graph():
    """
    Returns an org-tree graph:
    [CRM] → [Manager] → [Agent] with live metrics on each agent node.
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("team:overview:view")
    start = add_days(getdate(now_datetime()), -30)

    # Sales users
    users = frappe.db.sql("""
        SELECT DISTINCT u.name, u.full_name, u.user_image
        FROM `tabUser` u
        JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE u.enabled = 1 AND u.user_type = 'System User'
          AND hr.role IN ('Sales User','Sales Agent','Sales Manager')
    """, as_dict=True)

    if not users:
        return {"nodes": [], "edges": []}

    user_emails = [u.name for u in users]

    # Roles
    roles_map = {}
    for row in frappe.db.sql("""
        SELECT parent, role FROM `tabHas Role`
        WHERE parent IN %(users)s
          AND role IN ('Sales User','Sales Agent','Sales Manager','Quality Analyst')
    """, {"users": user_emails}, as_dict=True):
        roles_map.setdefault(row.parent, []).append(row.role)

    # Lead counts per owner
    lead_counts = {}
    for row in frappe.db.sql("""
        SELECT lead_owner, COUNT(*) AS cnt,
               SUM(CASE WHEN status = 'Converted' AND modified >= %(start)s THEN 1 ELSE 0 END) AS converted
        FROM `tabLead`
        WHERE lead_owner IN %(users)s AND creation >= %(start)s
        GROUP BY lead_owner
    """, {"users": user_emails, "start": start}, as_dict=True):
        lead_counts[row.lead_owner] = row

    # Scorecard data (latest per agent)
    scorecard_map = {}
    for row in frappe.db.sql("""
        SELECT agent, total_score, leads_handled, conversions
        FROM `tabAgent Scorecard`
        WHERE agent IN %(users)s
        ORDER BY period_date DESC
    """, {"users": user_emails}, as_dict=True):
        if row.agent not in scorecard_map:
            scorecard_map[row.agent] = row

    nodes = []
    edges = []

    # Root node
    nodes.append({
        "id": "crm-root",
        "label": _("AuraCRM Team"),
        "type": "crm-hub",
        "icon": "✦",
        "status": "active",
        "summary": {"Agents": len(users)},
    })

    managers = []
    agents = []

    for u in users:
        user_roles = roles_map.get(u.name, [])
        is_manager = "Sales Manager" in user_roles
        if is_manager:
            managers.append(u)
        else:
            agents.append(u)

    # Manager nodes
    for mgr in managers:
        lc = lead_counts.get(mgr.name, {})
        sc = scorecard_map.get(mgr.name, {})
        assigned = cint(getattr(lc, "cnt", 0)) if hasattr(lc, "cnt") else cint(lc.get("cnt", 0))
        converted = cint(getattr(lc, "converted", 0)) if hasattr(lc, "converted") else cint(lc.get("converted", 0))
        score = cint(getattr(sc, "total_score", 0)) if hasattr(sc, "total_score") else cint(sc.get("total_score", 0))

        mid = f"mgr-{mgr.name}"
        nodes.append({
            "id": mid,
            "label": mgr.full_name or mgr.name,
            "type": "crm-manager",
            "icon": "👔",
            "doctype": "User",
            "docname": mgr.name,
            "status": "active",
            "badge": f"Score: {score}" if score else "",
            "meta": {"avatar": mgr.user_image},
            "summary": {
                "Role": _("Sales Manager"),
                "Leads (30d)": assigned,
                "Converted": converted,
                "Score": score,
            },
        })
        edges.append({"source": "crm-root", "target": mid, "type": "child"})

    # Agent nodes — connect to managers if only 1 manager, else to root
    parent_target = managers[0].name if len(managers) == 1 else "crm-root"
    parent_id = f"mgr-{parent_target}" if len(managers) == 1 else "crm-root"

    for agent in agents:
        lc = lead_counts.get(agent.name, {})
        sc = scorecard_map.get(agent.name, {})
        assigned = cint(lc.get("cnt", 0)) if isinstance(lc, dict) else cint(getattr(lc, "cnt", 0))
        converted = cint(lc.get("converted", 0)) if isinstance(lc, dict) else cint(getattr(lc, "converted", 0))
        score = cint(sc.get("total_score", 0)) if isinstance(sc, dict) else cint(getattr(sc, "total_score", 0))
        conv_rate = round((converted / max(assigned, 1)) * 100, 1)

        # Determine status by performance
        if conv_rate >= 30:
            agent_status = "active"
        elif conv_rate >= 15:
            agent_status = "warning"
        elif assigned > 0:
            agent_status = "error"
        else:
            agent_status = "disabled"

        aid = f"agent-{agent.name}"
        nodes.append({
            "id": aid,
            "label": agent.full_name or agent.name,
            "type": "crm-agent",
            "icon": "💼",
            "doctype": "User",
            "docname": agent.name,
            "status": agent_status,
            "badge": f"{conv_rate}%" if assigned > 0 else "",
            "meta": {"avatar": agent.user_image},
            "summary": {
                "Leads (30d)": assigned,
                "Converted": converted,
                "Conv. Rate": f"{conv_rate}%",
                "Score": score,
            },
        })
        edges.append({"source": parent_id, "target": aid, "type": "child"})

    return {"nodes": nodes, "edges": edges}


# ═══════════════════════════════════════════════════════════════════
# 5. ANALYTICS GRAPH — Conversion funnel as layered flow
# ═══════════════════════════════════════════════════════════════════
@frappe.whitelist()
@cached(ttl=90, key_prefix="visual:analytics_funnel")
def get_analytics_funnel():
    """
    Returns a layered graph for the conversion funnel.
    Visitors → Leads → Qualified → Opportunities → Won
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("analytics:dashboard:view")
    start = add_days(getdate(now_datetime()), -30)

    funnel = frappe.db.sql("""
        SELECT
            (SELECT COUNT(*) FROM `tabLead` WHERE creation >= %(start)s) AS total_leads,
            (SELECT COUNT(*) FROM `tabLead` WHERE creation >= %(start)s AND status != 'Do Not Contact') AS qualified,
            (SELECT COUNT(*) FROM `tabOpportunity` WHERE creation >= %(start)s) AS opportunities,
            (SELECT COUNT(*) FROM `tabOpportunity` WHERE status = 'Converted' AND modified >= %(start)s) AS won,
            (SELECT COUNT(*) FROM `tabOpportunity` WHERE status = 'Lost' AND modified >= %(start)s) AS lost
    """, {"start": start}, as_dict=True)[0]

    total = cint(funnel.total_leads)
    qualified = cint(funnel.qualified)
    opps = cint(funnel.opportunities)
    won = cint(funnel.won)
    lost = cint(funnel.lost)

    steps = [
        ("funnel-leads", _("New Leads"), total, "crm-leads", "👤"),
        ("funnel-qualified", _("Qualified"), qualified, "crm-leads", "✅"),
        ("funnel-opps", _("Opportunities"), opps, "crm-pipeline", "🎯"),
        ("funnel-won", _("Won"), won, "crm-won", "🏆"),
    ]

    nodes = []
    edges = []

    for i, (sid, label, count, ntype, icon) in enumerate(steps):
        prev_count = steps[i - 1][2] if i > 0 else count
        conv = round((count / max(prev_count, 1)) * 100, 1) if i > 0 else 100
        nodes.append({
            "id": sid,
            "label": label,
            "type": ntype,
            "icon": icon,
            "badge": str(count),
            "status": "active" if count > 0 else "disabled",
            "summary": {
                "Count": count,
                "Conversion": f"{conv}%",
            },
        })
        if i > 0:
            edges.append({
                "source": steps[i - 1][0],
                "target": sid,
                "label": f"{conv}%",
                "type": "flow",
                "animated": True,
            })

    # Lost branch from opps
    if lost > 0:
        nodes.append({
            "id": "funnel-lost",
            "label": _("Lost"),
            "type": "crm-lost",
            "icon": "❌",
            "badge": str(lost),
            "status": "error",
            "summary": {"Count": lost},
        })
        edges.append({
            "source": "funnel-opps",
            "target": "funnel-lost",
            "label": f"{round((lost / max(opps, 1)) * 100, 1)}%",
            "type": "flow",
        })

    return {"nodes": nodes, "edges": edges}


# ═══════════════════════════════════════════════════════════════════
# 6. SCORE DISTRIBUTION — Heatmap-style graph of lead temperatures
# ═══════════════════════════════════════════════════════════════════
@frappe.whitelist()
@cached(ttl=120, key_prefix="visual:score_heatmap")
def get_score_heatmap():
    """
    Returns nodes grouped by score temperature band (Hot/Warm/Cool/Cold)
    with top leads in each band as child nodes.
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("scoring:scores:view")

    bands = frappe.db.sql("""
        SELECT
            CASE
                WHEN aura_score >= 80 THEN 'hot'
                WHEN aura_score >= 50 THEN 'warm'
                WHEN aura_score >= 30 THEN 'cool'
                ELSE 'cold'
            END AS band,
            COUNT(*) AS cnt
        FROM `tabLead`
        WHERE status NOT IN ('Converted','Do Not Contact')
        GROUP BY band
    """, as_dict=True)

    band_map = {b.band: cint(b.cnt) for b in bands}

    nodes = []
    edges = []

    # Central scoring node
    total = sum(band_map.values())
    nodes.append({
        "id": "score-center",
        "label": _("Lead Scoring"),
        "type": "crm-scoring",
        "icon": "📊",
        "status": "active",
        "summary": {"Total Active": total},
    })

    band_defs = [
        ("hot", _("Hot (80-100)"), "crm-lead-hot", "🔥"),
        ("warm", _("Warm (50-79)"), "crm-lead-warm", "☀️"),
        ("cool", _("Cool (30-49)"), "crm-leads", "💧"),
        ("cold", _("Cold (0-29)"), "crm-lead-cold", "❄️"),
    ]

    for band_key, label, ntype, icon in band_defs:
        count = band_map.get(band_key, 0)
        bid = f"band-{band_key}"
        nodes.append({
            "id": bid,
            "label": label,
            "type": ntype,
            "icon": icon,
            "badge": str(count),
            "status": "active" if count > 0 else "disabled",
            "summary": {"Leads": count, "Share": f"{round((count / max(total, 1)) * 100, 1)}%"},
        })
        edges.append({
            "source": "score-center",
            "target": bid,
            "label": str(count),
            "type": "reference",
            "animated": count > 0,
        })

    return {"nodes": nodes, "edges": edges}


# ═══════════════════════════════════════════════════════════════════
# 7. CRM NODE TYPE DEFINITIONS — For ColorSystem.registerNodeType
# ═══════════════════════════════════════════════════════════════════
@frappe.whitelist(allow_guest=False)
def get_crm_node_types():
    """
    Returns CRM-specific node type definitions for
    ColorSystem.registerNodeType() on the client side.
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    return {
        "crm-hub":           {"palette": "indigo",  "icon": "✦", "shape": "ellipse",         "width": 180, "height": 70},
        "crm-leads":         {"palette": "blue",    "icon": "👤", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-lead-hot":      {"palette": "red",     "icon": "🔥", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-lead-warm":     {"palette": "amber",   "icon": "☀️", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-lead-cold":     {"palette": "slate",   "icon": "❄️", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-pipeline":      {"palette": "emerald", "icon": "🔄", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-stage":         {"palette": "teal",    "icon": "📋", "shape": "roundrectangle", "width": 160, "height": 60},
        "crm-opportunity":   {"palette": "emerald", "icon": "🎯", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-won":           {"palette": "emerald", "icon": "🏆", "shape": "diamond",        "width": 120, "height": 60},
        "crm-lost":          {"palette": "red",     "icon": "❌", "shape": "diamond",        "width": 120, "height": 60},
        "crm-source":        {"palette": "violet",  "icon": "🌐", "shape": "roundrectangle", "width": 140, "height": 50},
        "crm-team":          {"palette": "purple",  "icon": "👥", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-manager":       {"palette": "purple",  "icon": "👔", "shape": "roundrectangle", "width": 160, "height": 60},
        "crm-agent":         {"palette": "cyan",    "icon": "💼", "shape": "roundrectangle", "width": 160, "height": 60},
        "crm-automation":    {"palette": "violet",  "icon": "🤖", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-sla":           {"palette": "amber",   "icon": "⏱️", "shape": "roundrectangle", "width": 140, "height": 50},
        "crm-scoring":       {"palette": "orange",  "icon": "📊", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-distribution":  {"palette": "sky",     "icon": "📤", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-dialer":        {"palette": "sky",     "icon": "📞", "shape": "roundrectangle", "width": 140, "height": 50},
        "crm-marketing":     {"palette": "pink",    "icon": "📢", "shape": "roundrectangle", "width": 150, "height": 55},
        "crm-communication": {"palette": "slate",   "icon": "💬", "shape": "roundrectangle", "width": 140, "height": 50},
        "crm-task":          {"palette": "amber",   "icon": "📝", "shape": "roundrectangle", "width": 140, "height": 50},
    }
