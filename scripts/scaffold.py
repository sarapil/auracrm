"""
AuraCRM — Scaffold Builder
===========================
Creates the complete directory structure and all foundation files.
Run: python apps/auracrm/scripts/scaffold.py
"""
import os
import json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(BASE, "auracrm")


def mkdir(path):
    os.makedirs(os.path.join(APP, path), exist_ok=True)


def write(path, content):
    full = os.path.join(APP, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  ✓ {path}")


def main():
    print("🏗️  AuraCRM Scaffold Builder")
    print("=" * 50)

    # ─── Directory structure ──────────────────────────────────────
    dirs = [
        "api", "engines", "overrides",
        "public/js/workspaces", "public/js/components", "public/js/utils", "public/js/overrides",
        "public/scss", "public/images",
        "auracrm/doctype/auracrm_settings",
        "auracrm/doctype/lead_distribution_rule",
        "auracrm/doctype/lead_scoring_rule",
        "auracrm/doctype/lead_score_log",
        "auracrm/doctype/sla_policy",
        "auracrm/doctype/sla_breach_log",
        "auracrm/doctype/auto_dialer_campaign",
        "auracrm/doctype/auto_dialer_entry",
        "auracrm/doctype/agent_scorecard",
        "auracrm/doctype/agent_shift",
        "auracrm/doctype/crm_automation_rule",
        "auracrm/doctype/communication_template",
        "auracrm/doctype/campaign_sequence",
        "auracrm/doctype/campaign_sequence_step",
        "auracrm/doctype/audience_segment",
        "auracrm/doctype/duplicate_rule",
        "auracrm/doctype/distribution_agent",
        "auracrm/doctype/scoring_criterion",
    ]
    print("\n📁 Creating directories...")
    for d in dirs:
        mkdir(d)
        print(f"  📂 {d}")

    # ─── __init__.py files ────────────────────────────────────────
    print("\n📝 Creating __init__.py files...")
    for d in ["api", "engines", "overrides"]:
        write(f"{d}/__init__.py", "")

    # ─── Engine stubs ─────────────────────────────────────────────
    print("\n⚙️  Creating engine stubs...")

    write("engines/distribution_engine.py", '''\
"""
AuraCRM — Lead Distribution Engine
====================================
Handles automatic assignment of Leads and Opportunities to agents
based on configurable rules: Round Robin, Weighted, Skill-Based,
Geographic, Load-Based, Performance-Based, Manual Pool.
"""

import frappe
from frappe import _


def auto_assign_lead(doc, method=None):
    """Hook: after_insert on Lead — auto-assign based on active rules."""
    if doc.flags.skip_auto_assign:
        return
    if doc.lead_owner:
        return  # Already assigned

    rules = get_active_rules("Lead")
    if not rules:
        return

    agent = find_best_agent(doc, rules)
    if agent:
        doc.db_set("lead_owner", agent, update_modified=False)
        frappe.publish_realtime(
            "auracrm_lead_assigned",
            {"lead": doc.name, "agent": agent},
            user=agent,
        )


def auto_assign_opportunity(doc, method=None):
    """Hook: after_insert on Opportunity — auto-assign."""
    if doc.flags.skip_auto_assign:
        return

    rules = get_active_rules("Opportunity")
    if not rules:
        return

    agent = find_best_agent(doc, rules)
    if agent:
        doc.db_set("_assign", frappe.as_json([agent]), update_modified=False)


def get_active_rules(doctype):
    """Get enabled distribution rules for a DocType, ordered by priority."""
    return frappe.get_all(
        "Lead Distribution Rule",
        filters={"enabled": 1, "applies_to": doctype},
        fields=["*"],
        order_by="priority asc",
    )


def find_best_agent(doc, rules):
    """Evaluate rules and return the best agent email."""
    for rule in rules:
        method = rule.get("distribution_method", "round_robin")

        if method == "round_robin":
            return _round_robin(rule)
        elif method == "weighted_round_robin":
            return _weighted_round_robin(rule)
        elif method == "skill_based":
            return _skill_based(doc, rule)
        elif method == "geographic":
            return _geographic(doc, rule)
        elif method == "load_based":
            return _load_based(rule)
        elif method == "performance_based":
            return _performance_based(rule)
        elif method == "manual_pool":
            return None  # Goes to pool, first-come-first-served

    return None


def _round_robin(rule):
    """Simple round-robin across agents in the rule."""
    agents = get_rule_agents(rule.name)
    if not agents:
        return None

    # Get last assigned index from cache
    cache_key = f"auracrm_rr_{rule.name}"
    last_idx = frappe.cache.get_value(cache_key) or 0
    next_idx = (last_idx + 1) % len(agents)
    frappe.cache.set_value(cache_key, next_idx)

    return agents[next_idx]


def _weighted_round_robin(rule):
    """Weighted round-robin — agents with higher weight get more leads."""
    # TODO: implement weighted distribution
    return _round_robin(rule)


def _skill_based(doc, rule):
    """Match lead attributes to agent skills (language, product, region)."""
    # TODO: implement skill matching
    return _round_robin(rule)


def _geographic(doc, rule):
    """Assign based on lead location → nearest agent territory."""
    # TODO: implement geographic matching
    return _round_robin(rule)


def _load_based(rule):
    """Assign to agent with least current workload."""
    agents = get_rule_agents(rule.name)
    if not agents:
        return None

    loads = []
    for agent in agents:
        count = frappe.db.count("Lead", {"lead_owner": agent, "status": ["in", ["Open", "Replied"]]})
        count += frappe.db.count("Opportunity", {"_assign": ["like", f"%{agent}%"], "status": "Open"})
        loads.append((agent, count))

    loads.sort(key=lambda x: x[1])
    return loads[0][0] if loads else None


def _performance_based(rule):
    """Assign more leads to higher-performing agents."""
    # TODO: implement performance-based distribution
    return _round_robin(rule)


def get_rule_agents(rule_name):
    """Get list of agent emails for a distribution rule."""
    agents = frappe.get_all(
        "Distribution Agent",
        filters={"parent": rule_name},
        fields=["agent_email"],
        order_by="idx asc",
    )
    return [a.agent_email for a in agents if a.agent_email]


def rebalance_workload():
    """Daily scheduler: check for overloaded agents and redistribute."""
    pass  # TODO: implement workload rebalancing
''')

    write("engines/scoring_engine.py", '''\
"""
AuraCRM — Lead Scoring Engine
===============================
Calculates and maintains lead scores based on:
- Demographic criteria (job title, company size, industry, location)
- Behavioral signals (email opens, clicks, replies, calls answered)
- Communication activity (response time, channel diversity)
- Score decay over time without interaction
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, date_diff, getdate


def calculate_lead_score(doc, method=None):
    """Hook: validate on Lead — recalculate score."""
    if doc.flags.skip_scoring:
        return

    try:
        settings = frappe.get_cached_doc("AuraCRM Settings")
        if not settings.get("scoring_enabled"):
            return
    except Exception:
        return

    rules = frappe.get_all(
        "Lead Scoring Rule",
        filters={"enabled": 1},
        fields=["*"],
        order_by="priority asc",
    )

    total_score = 0
    for rule in rules:
        score = evaluate_scoring_rule(doc, rule)
        total_score += score

    doc.lead_score = max(0, min(total_score, 100))  # Clamp 0-100


def calculate_opportunity_score(doc, method=None):
    """Hook: validate on Opportunity — score based on deal attributes."""
    if doc.flags.skip_scoring:
        return
    # Opportunity scoring uses different criteria
    pass


def on_communication(doc, method=None):
    """Hook: after_insert on Communication — update related lead/opp score."""
    if doc.reference_doctype == "Lead" and doc.reference_name:
        try:
            lead = frappe.get_doc("Lead", doc.reference_name)
            lead.flags.skip_scoring = False
            lead.save(ignore_permissions=True)
        except Exception:
            pass


def evaluate_scoring_rule(doc, rule):
    """Evaluate a single scoring rule against a document."""
    field = rule.get("field_name", "")
    operator = rule.get("operator", "equals")
    value = rule.get("field_value", "")
    points = rule.get("points", 0)

    doc_value = doc.get(field, "")
    if doc_value is None:
        doc_value = ""

    match = False
    if operator == "equals":
        match = str(doc_value).lower() == str(value).lower()
    elif operator == "contains":
        match = str(value).lower() in str(doc_value).lower()
    elif operator == "greater_than":
        try:
            match = float(doc_value) > float(value)
        except (ValueError, TypeError):
            pass
    elif operator == "less_than":
        try:
            match = float(doc_value) < float(value)
        except (ValueError, TypeError):
            pass
    elif operator == "in_list":
        match = str(doc_value) in [v.strip() for v in str(value).split(",")]
    elif operator == "is_set":
        match = bool(doc_value)
    elif operator == "is_not_set":
        match = not bool(doc_value)

    return points if match else 0


def apply_score_decay():
    """Scheduled: reduce scores for leads with no recent interaction."""
    try:
        settings = frappe.get_cached_doc("AuraCRM Settings")
        decay_rate = settings.get("score_decay_points_per_day", 2)
        decay_after_days = settings.get("score_decay_after_days", 7)
    except Exception:
        return

    if not decay_rate:
        return

    cutoff = frappe.utils.add_days(now_datetime(), -decay_after_days)

    leads = frappe.get_all(
        "Lead",
        filters={
            "lead_score": [">", 0],
            "modified": ["<", cutoff],
            "status": ["not in", ["Converted", "Do Not Contact"]],
        },
        fields=["name", "lead_score"],
    )

    for lead in leads:
        new_score = max(0, lead.lead_score - decay_rate)
        if new_score != lead.lead_score:
            frappe.db.set_value("Lead", lead.name, "lead_score", new_score, update_modified=False)

    if leads:
        frappe.db.commit()
''')

    write("engines/sla_engine.py", '''\
"""
AuraCRM — SLA Engine
======================
Tracks response time SLAs for Leads and Opportunities.
Escalates when SLA is about to breach or has breached.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, time_diff_in_seconds


def check_sla_on_update(doc, method=None):
    """Hook: on_update — check if this update resolves an SLA timer."""
    pass  # TODO: implement SLA resolution tracking


def check_sla_breaches():
    """Scheduled: every 5 min — find leads/opps approaching or past SLA."""
    policies = frappe.get_all(
        "SLA Policy",
        filters={"enabled": 1},
        fields=["*"],
    )

    for policy in policies:
        _check_policy_breaches(policy)


def _check_policy_breaches(policy):
    """Check a single SLA policy for breaches."""
    doctype = policy.get("applies_to", "Lead")
    response_time_mins = policy.get("response_time_minutes", 60)

    # Find unresponded items older than SLA
    cutoff = frappe.utils.add_to_date(now_datetime(), minutes=-response_time_mins)

    items = frappe.get_all(
        doctype,
        filters={
            "creation": ["<", cutoff],
            "status": "Open",
        },
        fields=["name", "creation", "lead_owner" if doctype == "Lead" else "owner"],
        limit=50,
    )

    for item in items:
        # Check if already breached
        existing = frappe.db.exists("SLA Breach Log", {
            "reference_doctype": doctype,
            "reference_name": item.name,
            "sla_policy": policy.name,
        })
        if existing:
            continue

        # Create breach log
        breach = frappe.new_doc("SLA Breach Log")
        breach.reference_doctype = doctype
        breach.reference_name = item.name
        breach.sla_policy = policy.name
        breach.breach_time = now_datetime()
        breach.assigned_to = item.get("lead_owner") or item.get("owner")
        breach.insert(ignore_permissions=True)

        # Notify
        _escalate_breach(breach, policy)

    if items:
        frappe.db.commit()


def _escalate_breach(breach, policy):
    """Send notification for SLA breach."""
    escalate_to = policy.get("escalate_to")
    if not escalate_to:
        return

    frappe.publish_realtime(
        "auracrm_sla_breach",
        {
            "doctype": breach.reference_doctype,
            "name": breach.reference_name,
            "policy": policy.name,
            "assigned_to": breach.assigned_to,
        },
        user=escalate_to,
    )
''')

    # ─── API stubs ────────────────────────────────────────────────
    print("\n🔌 Creating API stubs...")

    write("api/__init__.py", "")

    write("api/pipeline.py", '''\
"""AuraCRM — Pipeline API"""
import frappe
from frappe import _


@frappe.whitelist()
def get_pipeline_stages():
    """Get pipeline stages with counts."""
    stages = frappe.get_all("Sales Stage", fields=["name", "stage_name"], order_by="idx asc")
    result = []
    for stage in stages:
        count = frappe.db.count("Opportunity", {"sales_stage": stage.name, "status": "Open"})
        total_value = frappe.db.sql(
            "SELECT COALESCE(SUM(opportunity_amount), 0) FROM `tabOpportunity` WHERE sales_stage=%s AND status='Open'",
            stage.name,
        )[0][0]
        result.append({
            "stage": stage.name,
            "label": stage.stage_name or stage.name,
            "count": count,
            "value": float(total_value),
        })
    return result


@frappe.whitelist()
def get_pipeline_board(filters=None):
    """Get Kanban board data for pipeline."""
    import json
    if isinstance(filters, str):
        filters = json.loads(filters)

    stages = get_pipeline_stages()
    board = {}
    for stage in stages:
        opps = frappe.get_all(
            "Opportunity",
            filters={"sales_stage": stage["stage"], "status": "Open", **(filters or {})},
            fields=["name", "opportunity_from", "party_name", "opportunity_amount",
                     "expected_closing", "contact_person", "_assign", "modified"],
            order_by="modified desc",
            limit=50,
        )
        board[stage["stage"]] = {
            "stage": stage,
            "opportunities": opps,
        }
    return board


@frappe.whitelist()
def move_opportunity(opportunity, new_stage):
    """Move an opportunity to a new pipeline stage."""
    frappe.db.set_value("Opportunity", opportunity, "sales_stage", new_stage)
    frappe.publish_realtime("auracrm_pipeline_update", {
        "opportunity": opportunity, "new_stage": new_stage,
    })
    return {"status": "ok"}
''')

    write("api/distribution.py", '''\
"""AuraCRM — Distribution API"""
import frappe
from frappe import _


@frappe.whitelist()
def get_distribution_stats():
    """Get lead distribution statistics per agent."""
    agents = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name", "user_image"],
    )
    result = []
    for agent in agents:
        leads = frappe.db.count("Lead", {"lead_owner": agent.name, "status": ["in", ["Open", "Replied"]]})
        opps = frappe.db.count("Opportunity", {"_assign": ["like", f"%{agent.name}%"], "status": "Open"})
        result.append({
            "agent": agent.name,
            "full_name": agent.full_name,
            "avatar": agent.user_image,
            "open_leads": leads,
            "open_opportunities": opps,
            "total_workload": leads + opps,
        })
    return sorted(result, key=lambda x: x["total_workload"], reverse=True)


@frappe.whitelist()
def manually_assign(doctype, name, agent):
    """Manually assign a lead or opportunity to an agent."""
    frappe.has_permission(doctype, "write", throw=True)
    if doctype == "Lead":
        frappe.db.set_value("Lead", name, "lead_owner", agent)
    elif doctype == "Opportunity":
        frappe.db.set_value("Opportunity", name, "_assign", frappe.as_json([agent]))

    frappe.publish_realtime("auracrm_manual_assign", {
        "doctype": doctype, "name": name, "agent": agent,
    }, user=agent)
    return {"status": "ok"}
''')

    write("api/scoring.py", '''\
"""AuraCRM — Scoring API"""
import frappe
from frappe import _


@frappe.whitelist()
def get_lead_scores(filters=None, limit=50):
    """Get leads with their scores for the scoring dashboard."""
    import json
    if isinstance(filters, str):
        filters = json.loads(filters)

    base_filters = {"status": ["not in", ["Converted", "Do Not Contact"]]}
    if filters:
        base_filters.update(filters)

    leads = frappe.get_all(
        "Lead",
        filters=base_filters,
        fields=["name", "lead_name", "company_name", "source", "lead_owner",
                "status", "lead_score", "modified", "creation"],
        order_by="lead_score desc",
        limit_page_length=limit,
    )
    return leads


@frappe.whitelist()
def get_score_distribution():
    """Get distribution of lead scores in buckets."""
    buckets = [
        {"label": "Hot (80-100)", "min": 80, "max": 100, "color": "#ef4444"},
        {"label": "Warm (60-79)", "min": 60, "max": 79, "color": "#f59e0b"},
        {"label": "Cool (30-59)", "min": 30, "max": 59, "color": "#3b82f6"},
        {"label": "Cold (0-29)", "min": 0, "max": 29, "color": "#94a3b8"},
    ]
    for bucket in buckets:
        bucket["count"] = frappe.db.count("Lead", {
            "lead_score": [">=", bucket["min"]],
            "lead_score": ["<=", bucket["max"]],
            "status": ["not in", ["Converted", "Do Not Contact"]],
        })
    return buckets
''')

    write("api/analytics.py", '''\
"""AuraCRM — Analytics API"""
import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate


@frappe.whitelist()
def get_dashboard_kpis(period="month"):
    """Get KPI data for the command center dashboard."""
    today = getdate(now_datetime())

    if period == "week":
        start = add_days(today, -7)
    elif period == "month":
        start = add_days(today, -30)
    elif period == "quarter":
        start = add_days(today, -90)
    else:
        start = add_days(today, -30)

    kpis = {
        "new_leads": frappe.db.count("Lead", {"creation": [">=", start]}),
        "converted_leads": frappe.db.count("Lead", {"status": "Converted", "modified": [">=", start]}),
        "new_opportunities": frappe.db.count("Opportunity", {"creation": [">=", start]}),
        "won_opportunities": frappe.db.count("Opportunity", {"status": "Converted", "modified": [">=", start]}),
        "lost_opportunities": frappe.db.count("Opportunity", {"status": "Lost", "modified": [">=", start]}),
        "pipeline_value": frappe.db.sql(
            "SELECT COALESCE(SUM(opportunity_amount), 0) FROM `tabOpportunity` WHERE status='Open'"
        )[0][0],
    }

    # Conversion rate
    total_leads = kpis["new_leads"] or 1
    kpis["conversion_rate"] = round((kpis["converted_leads"] / total_leads) * 100, 1)

    return kpis


@frappe.whitelist()
def get_agent_performance(period="month"):
    """Get per-agent performance metrics."""
    today = getdate(now_datetime())
    start = add_days(today, -30) if period == "month" else add_days(today, -7)

    agents = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name", "user_image"],
    )

    result = []
    for agent in agents:
        leads_assigned = frappe.db.count("Lead", {"lead_owner": agent.name, "creation": [">=", start]})
        leads_converted = frappe.db.count("Lead", {
            "lead_owner": agent.name, "status": "Converted", "modified": [">=", start],
        })
        result.append({
            "agent": agent.name,
            "full_name": agent.full_name,
            "avatar": agent.user_image,
            "leads_assigned": leads_assigned,
            "leads_converted": leads_converted,
            "conversion_rate": round((leads_converted / max(leads_assigned, 1)) * 100, 1),
        })

    return sorted(result, key=lambda x: x["conversion_rate"], reverse=True)
''')

    write("api/team.py", '''\
"""AuraCRM — Team Management API"""
import frappe
from frappe import _


@frappe.whitelist()
def get_team_overview():
    """Get full team overview for the management workspace."""
    agents = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name", "user_image"],
    )

    result = []
    for agent in agents:
        roles = frappe.get_roles(agent.name)
        if not any(r in roles for r in ["Sales User", "Sales Agent", "Sales Manager"]):
            continue

        result.append({
            "agent": agent.name,
            "full_name": agent.full_name,
            "avatar": agent.user_image,
            "roles": [r for r in roles if r in ["Sales User", "Sales Agent", "Sales Manager", "Quality Analyst"]],
            "is_manager": "Sales Manager" in roles,
        })

    return result


def calculate_daily_scorecards():
    """Scheduled: calculate daily agent scorecards."""
    pass  # TODO: implement daily scorecard calculation
''')

    write("api/workspace_data.py", '''\
"""AuraCRM — Workspace Data Provider API"""
import frappe
from frappe import _


@frappe.whitelist()
def get_sales_agent_workspace():
    """Get all data needed for the Sales Agent workspace."""
    user = frappe.session.user

    # My leads
    my_leads = frappe.get_all(
        "Lead",
        filters={"lead_owner": user, "status": ["in", ["Open", "Replied"]]},
        fields=["name", "lead_name", "company_name", "phone", "mobile_no",
                "email_id", "source", "status", "lead_score", "creation", "modified"],
        order_by="lead_score desc, modified desc",
        limit=50,
    )

    # My opportunities
    my_opps = frappe.get_all(
        "Opportunity",
        filters={"_assign": ["like", f"%{user}%"], "status": "Open"},
        fields=["name", "party_name", "opportunity_amount", "sales_stage",
                "expected_closing", "contact_person", "modified"],
        order_by="modified desc",
        limit=50,
    )

    # Today\'s tasks
    my_tasks = frappe.get_all(
        "ToDo",
        filters={
            "allocated_to": user,
            "status": "Open",
            "reference_type": ["in", ["Lead", "Opportunity", "Customer"]],
        },
        fields=["name", "description", "reference_type", "reference_name", "date", "priority"],
        order_by="date asc",
        limit=20,
    )

    return {
        "leads": my_leads,
        "opportunities": my_opps,
        "tasks": my_tasks,
        "stats": {
            "total_leads": len(my_leads),
            "total_opps": len(my_opps),
            "total_tasks": len(my_tasks),
            "hot_leads": len([l for l in my_leads if (l.get("lead_score") or 0) >= 80]),
        },
    }


@frappe.whitelist()
def get_contact_360(doctype, name):
    """Get 360° view of a contact — all related data across systems."""
    doc = frappe.get_doc(doctype, name)
    frappe.has_permission(doctype, "read", doc=doc, throw=True)

    result = {
        "doc": doc.as_dict(),
        "communications": [],
        "activities": [],
    }

    # Get communication history from Arrowz if available
    try:
        from arrowz.api.communications import get_communication_history
        result["communications"] = get_communication_history(doctype, name)
    except (ImportError, Exception):
        # Fallback to Frappe Communications
        result["communications"] = frappe.get_all(
            "Communication",
            filters={"reference_doctype": doctype, "reference_name": name},
            fields=["*"],
            order_by="creation desc",
            limit=50,
        )

    return result
''')

    # ─── JS Bootstrap ────────────────────────────────────────────
    print("\n🌐 Creating JavaScript files...")

    write("public/js/aura_bootstrap.js", '''\
/**
 * AuraCRM — Bootstrap Loader
 * ===========================
 * Lightweight global loader (included on every page via hooks.py).
 * Provides the `frappe.auracrm` namespace and lazy-load helpers.
 * The heavy bundles are loaded on-demand only when a workspace opens.
 */

(function () {
\t"use strict";

\tfrappe.provide("frappe.auracrm");
\tfrappe.provide("frappe.auracrm._cache");

\tconst BUNDLE = "auracrm.bundle.js";

\tfrappe.auracrm._loaded = false;
\tfrappe.auracrm.version = "0.1.0";

\t/**
\t * Load the full AuraCRM bundle on demand.
\t */
\tfrappe.auracrm.load = async function () {
\t\tif (!frappe.auracrm._loaded) {
\t\t\t// Ensure frappe_visual is loaded first
\t\t\tif (frappe.visual && frappe.visual.engine) {
\t\t\t\tawait frappe.visual.engine();
\t\t\t}
\t\t\tawait frappe.require(BUNDLE);
\t\t\tfrappe.auracrm._loaded = true;
\t\t}
\t\treturn frappe.auracrm;
\t};

\t/**
\t * Open a workspace by role.
\t * @param {string} workspace - e.g. "sales-agent", "sales-manager", "quality", "marketing", "command-center", "settings"
\t */
\tfrappe.auracrm.openWorkspace = async function (workspace) {
\t\tawait frappe.auracrm.load();
\t\tif (frappe.auracrm.WorkspaceRouter) {
\t\t\tfrappe.auracrm.WorkspaceRouter.open(workspace);
\t\t}
\t};

\t/**
\t * Get user CRM role from boot session.
\t */
\tfrappe.auracrm.getUserRole = function () {
\t\tconst boot = (frappe.boot && frappe.boot.auracrm) || {};
\t\tconst roles = boot.user_roles || {};
\t\tif (roles.is_crm_admin) return "admin";
\t\tif (roles.is_sales_manager) return "manager";
\t\tif (roles.is_quality_analyst) return "quality";
\t\tif (roles.is_marketing_manager) return "marketing";
\t\tif (roles.is_sales_agent) return "agent";
\t\treturn "viewer";
\t};

\tconsole.log(
\t\t"%c✦ AuraCRM%c v0.1.0 ready",
\t\t"color:#6366f1;font-weight:bold;font-size:12px",
\t\t"color:#94a3b8"
\t);
})();
''')

    write("public/js/auracrm.bundle.js", '''\
/**
 * AuraCRM — Main Bundle Entry
 * =============================
 * Loaded on-demand via frappe.require("auracrm.bundle.js").
 * Imports all workspace modules and registers them.
 */

// ── Workspace Modules ────────────────────────────────────────────
import { SalesAgentWorkspace } from "./workspaces/sales_agent";
import { SalesManagerWorkspace } from "./workspaces/sales_manager";
import { CommandCenterWorkspace } from "./workspaces/command_center";
// import { QualityWorkspace } from "./workspaces/quality";
// import { MarketingWorkspace } from "./workspaces/marketing";
// import { SettingsWorkspace } from "./workspaces/settings_hub";

// ── Components ───────────────────────────────────────────────────
import { PipelineBoard } from "./components/pipeline_board";
import { CommunicationTimeline } from "./components/communication_timeline";
import { LeadCard } from "./components/lead_card";
import { AgentCard } from "./components/agent_card";
import { ScoringGauge } from "./components/scoring_gauge";
import { SLATimer } from "./components/sla_timer";

// ── Utils ────────────────────────────────────────────────────────
import { CRMDataAdapter } from "./utils/crm_data_adapter";
import { ArrowzBridge } from "./utils/arrowz_bridge";

// ── Register ─────────────────────────────────────────────────────
frappe.provide("frappe.auracrm");

// Workspaces
frappe.auracrm.SalesAgentWorkspace = SalesAgentWorkspace;
frappe.auracrm.SalesManagerWorkspace = SalesManagerWorkspace;
frappe.auracrm.CommandCenterWorkspace = CommandCenterWorkspace;

// Components
frappe.auracrm.PipelineBoard = PipelineBoard;
frappe.auracrm.CommunicationTimeline = CommunicationTimeline;
frappe.auracrm.LeadCard = LeadCard;
frappe.auracrm.AgentCard = AgentCard;
frappe.auracrm.ScoringGauge = ScoringGauge;
frappe.auracrm.SLATimer = SLATimer;

// Utils
frappe.auracrm.CRMDataAdapter = CRMDataAdapter;
frappe.auracrm.ArrowzBridge = ArrowzBridge;

// ── Workspace Router ─────────────────────────────────────────────
frappe.auracrm.WorkspaceRouter = {
\tworkspaces: {
\t\t"sales-agent": SalesAgentWorkspace,
\t\t"sales-manager": SalesManagerWorkspace,
\t\t"command-center": CommandCenterWorkspace,
\t},
\topen(name) {
\t\tconst Cls = this.workspaces[name];
\t\tif (Cls) {
\t\t\tCls.open();
\t\t} else {
\t\t\tfrappe.show_alert({ message: __("Workspace not found: " + name), indicator: "orange" });
\t\t}
\t},
};

console.log(
\t"%c✦ AuraCRM Engine%c loaded — workspaces ready",
\t"color:#6366f1;font-weight:bold",
\t"color:#94a3b8"
);
''')

    # ─── Workspace stubs ──────────────────────────────────────────
    write("public/js/workspaces/sales_agent.js", '''\
/**
 * Sales Agent Workspace
 * ======================
 * The primary workspace for sales agents — everything they need on one page:
 * - My Leads (scored, sorted)
 * - My Opportunities (pipeline position)
 * - Contact 360° view (all channels: call, WhatsApp, email, SMS)
 * - Quick actions: Call, WhatsApp, Email, Schedule Meeting
 * - SLA timers on each lead
 * - Softphone integration (via Arrowz)
 */

export class SalesAgentWorkspace {
\tstatic async open() {
\t\t// TODO: implement full workspace
\t\tfrappe.show_alert({ message: __("Sales Agent Workspace — coming soon"), indicator: "blue" });
\t}

\tconstructor(container) {
\t\tthis.container = typeof container === "string" ? document.querySelector(container) : container;
\t}

\tasync init() {
\t\t// Fetch workspace data
\t\tconst data = await frappe.xcall("auracrm.api.workspace_data.get_sales_agent_workspace");
\t\tthis.data = data;
\t\tthis.render();
\t}

\trender() {
\t\t// TODO: implement visual layout using Frappe Visual components
\t}

\tdestroy() {
\t\tif (this.container) this.container.innerHTML = "";
\t}
}
''')

    write("public/js/workspaces/sales_manager.js", '''\
/**
 * Sales Manager Workspace
 * ========================
 * Management dashboard for sales managers:
 * - Team performance overview (graph)
 * - Pipeline health (Kanban + funnel)
 * - Agent workload distribution
 * - SLA breach alerts
 * - Conversion analytics
 * - Lead distribution controls
 */

export class SalesManagerWorkspace {
\tstatic async open() {
\t\tfrappe.show_alert({ message: __("Sales Manager Workspace — coming soon"), indicator: "blue" });
\t}

\tdestroy() {}
}
''')

    write("public/js/workspaces/command_center.js", '''\
/**
 * Command Center Workspace
 * =========================
 * The executive dashboard — bird\'s eye view of the entire CRM:
 * - KPI cards (leads, conversions, revenue, SLA health)
 * - Pipeline graph (stages as nodes, flow as edges)
 * - Live activity feed (real-time via Socket.IO)
 * - Campaign health
 * - Agent performance grid
 */

export class CommandCenterWorkspace {
\tstatic async open() {
\t\tfrappe.show_alert({ message: __("Command Center — coming soon"), indicator: "blue" });
\t}

\tdestroy() {}
}
''')

    # ─── Component stubs ──────────────────────────────────────────
    write("public/js/components/pipeline_board.js", '''\
/**
 * PipelineBoard — Visual Kanban Pipeline
 * ========================================
 * Kanban-style pipeline using Frappe Visual GraphEngine.
 * Stages as columns (compound nodes), opportunities as cards.
 * Drag-and-drop between stages triggers API update.
 */
export class PipelineBoard {
\tconstructor(container, opts = {}) {
\t\tthis.container = typeof container === "string" ? document.querySelector(container) : container;
\t\tthis.opts = opts;
\t}
\tasync init() { /* TODO */ }
\tdestroy() { if (this.container) this.container.innerHTML = ""; }
}
''')

    write("public/js/components/communication_timeline.js", '''\
/**
 * CommunicationTimeline — Unified Interaction Timeline
 * =====================================================
 * Visualizes all interactions with a contact across all channels
 * (call, WhatsApp, Telegram, email, SMS, meeting) using Frappe Visual.
 * Uses GraphEngine with elk-layered layout for chronological display.
 */
export class CommunicationTimeline {
\tconstructor(container, opts = {}) {
\t\tthis.container = typeof container === "string" ? document.querySelector(container) : container;
\t\tthis.opts = opts;
\t}
\tasync init() { /* TODO */ }
\tdestroy() { if (this.container) this.container.innerHTML = ""; }
}
''')

    write("public/js/components/lead_card.js", '''\
/**
 * LeadCard — Rich Lead Information Card
 * =======================================
 * Displays lead details with scoring gauge, SLA timer,
 * communication channels, and quick action buttons.
 */
export class LeadCard {
\tconstructor(container, leadData) {
\t\tthis.container = typeof container === "string" ? document.querySelector(container) : container;
\t\tthis.data = leadData;
\t}
\trender() { /* TODO */ }
\tdestroy() { if (this.container) this.container.innerHTML = ""; }
}
''')

    write("public/js/components/agent_card.js", '''\
/**
 * AgentCard — Agent Status & Performance Card
 */
export class AgentCard {
\tconstructor(container, agentData) {
\t\tthis.container = typeof container === "string" ? document.querySelector(container) : container;
\t\tthis.data = agentData;
\t}
\trender() { /* TODO */ }
\tdestroy() { if (this.container) this.container.innerHTML = ""; }
}
''')

    write("public/js/components/scoring_gauge.js", '''\
/**
 * ScoringGauge — Visual Lead Score Indicator
 * ============================================
 * Circular gauge showing lead score (0-100) with color coding:
 * Hot (80-100) red, Warm (60-79) amber, Cool (30-59) blue, Cold (0-29) gray
 */
export class ScoringGauge {
\tconstructor(container, score = 0) {
\t\tthis.container = typeof container === "string" ? document.querySelector(container) : container;
\t\tthis.score = score;
\t}
\trender() { /* TODO */ }
\tdestroy() { if (this.container) this.container.innerHTML = ""; }
}
''')

    write("public/js/components/sla_timer.js", '''\
/**
 * SLATimer — Visual SLA Countdown
 * =================================
 * Shows time remaining before SLA breach with color transitions.
 * Green → Yellow → Red as deadline approaches.
 */
export class SLATimer {
\tconstructor(container, deadline) {
\t\tthis.container = typeof container === "string" ? document.querySelector(container) : container;
\t\tthis.deadline = deadline;
\t}
\trender() { /* TODO */ }
\tdestroy() {
\t\tif (this._interval) clearInterval(this._interval);
\t\tif (this.container) this.container.innerHTML = "";
\t}
}
''')

    # ─── Utils ────────────────────────────────────────────────────
    write("public/js/utils/crm_data_adapter.js", '''\
/**
 * CRMDataAdapter — AuraCRM Data Bridge
 * =======================================
 * Fetches CRM data and transforms it for Frappe Visual components.
 */
export class CRMDataAdapter {
\tstatic async fetchDashboardKPIs(period = "month") {
\t\treturn frappe.xcall("auracrm.api.analytics.get_dashboard_kpis", { period });
\t}

\tstatic async fetchPipelineBoard(filters) {
\t\treturn frappe.xcall("auracrm.api.pipeline.get_pipeline_board", { filters });
\t}

\tstatic async fetchAgentWorkspace() {
\t\treturn frappe.xcall("auracrm.api.workspace_data.get_sales_agent_workspace");
\t}

\tstatic async fetchContact360(doctype, name) {
\t\treturn frappe.xcall("auracrm.api.workspace_data.get_contact_360", { doctype, name });
\t}

\tstatic async fetchTeamOverview() {
\t\treturn frappe.xcall("auracrm.api.team.get_team_overview");
\t}
}
''')

    write("public/js/utils/arrowz_bridge.js", '''\
/**
 * ArrowzBridge — Integration with Arrowz Communications
 * =======================================================
 * Bridges AuraCRM with Arrowz\'s communication capabilities:
 * - Softphone (click-to-call, screen pop)
 * - Omni-channel messaging (WhatsApp, Telegram, SMS)
 * - Call recording & monitoring
 * - Meeting scheduling
 * - Unified communication history
 */
export class ArrowzBridge {
\t/**
\t * Check if Arrowz is available and user has extension.
\t */
\tstatic isAvailable() {
\t\treturn !!(frappe.boot?.arrowz?.enabled);
\t}

\t/**
\t * Make a call via Arrowz softphone.
\t */
\tstatic async makeCall(phoneNumber) {
\t\tif (!ArrowzBridge.isAvailable()) {
\t\t\tfrappe.show_alert({ message: __("Softphone not available"), indicator: "orange" });
\t\t\treturn;
\t\t}
\t\tif (typeof arrowz !== "undefined" && arrowz.softphone) {
\t\t\tarrowz.softphone.makeCall(phoneNumber);
\t\t} else {
\t\t\treturn frappe.xcall("arrowz.api.calls.make_call", { phone_number: phoneNumber });
\t\t}
\t}

\t/**
\t * Open WhatsApp conversation for a contact.
\t */
\tstatic async openWhatsApp(phoneNumber, doctype, docname) {
\t\tif (!ArrowzBridge.isAvailable()) return;
\t\treturn frappe.xcall("arrowz.api.omni.start_whatsapp_session", {
\t\t\tphone_number: phoneNumber,
\t\t\treference_doctype: doctype,
\t\t\treference_name: docname,
\t\t});
\t}

\t/**
\t * Get unified communication history for a CRM record.
\t */
\tstatic async getCommunicationHistory(doctype, docname) {
\t\ttry {
\t\t\treturn await frappe.xcall("arrowz.api.communications.get_communication_history", {
\t\t\t\tdoctype, docname,
\t\t\t});
\t\t} catch (e) {
\t\t\tconsole.warn("[AuraCRM] Arrowz communication history unavailable:", e);
\t\t\treturn [];
\t\t}
\t}

\t/**
\t * Get communication stats per channel.
\t */
\tstatic async getChannelStats(doctype, docname) {
\t\ttry {
\t\t\treturn await frappe.xcall("arrowz.api.communications.get_channel_stats", {
\t\t\t\tdoctype, docname,
\t\t\t});
\t\t} catch (e) {
\t\t\treturn {};
\t\t}
\t}

\t/**
\t * Schedule a meeting via Arrowz OpenMeetings.
\t */
\tstatic async scheduleMeeting(doctype, docname) {
\t\ttry {
\t\t\treturn await frappe.xcall("arrowz.api.omni.quick_schedule_meeting", {
\t\t\t\treference_doctype: doctype,
\t\t\t\treference_name: docname,
\t\t\t});
\t\t} catch (e) {
\t\t\tconsole.warn("[AuraCRM] Meeting scheduling unavailable:", e);
\t\t}
\t}
}
''')

    # ─── DocType JS Overrides ─────────────────────────────────────
    write("public/js/overrides/lead_override.js", '''\
/**
 * AuraCRM — Lead Form Override
 * ==============================
 * Extends the Lead form with AuraCRM features:
 * - Visual scoring gauge
 * - Quick communication actions (call, WhatsApp, email)
 * - SLA timer
 * - 360° contact view button
 */
frappe.ui.form.on("Lead", {
\trefresh(frm) {
\t\tif (!frm.is_new()) {
\t\t\t// Add AuraCRM buttons
\t\t\tfrm.add_custom_button(__("360° View"), async () => {
\t\t\t\tconst aura = await frappe.auracrm.load();
\t\t\t\t// TODO: open Contact 360 floating window
\t\t\t}, __("AuraCRM"));

\t\t\tfrm.add_custom_button(__("Communication Timeline"), async () => {
\t\t\t\tconst aura = await frappe.auracrm.load();
\t\t\t\t// TODO: open communication timeline
\t\t\t}, __("AuraCRM"));
\t\t}
\t},
});
''')

    write("public/js/overrides/opportunity_override.js", '''\
/**
 * AuraCRM — Opportunity Form Override
 */
frappe.ui.form.on("Opportunity", {
\trefresh(frm) {
\t\tif (!frm.is_new()) {
\t\t\tfrm.add_custom_button(__("Pipeline View"), async () => {
\t\t\t\tconst aura = await frappe.auracrm.load();
\t\t\t\t// TODO: open pipeline board focused on this opportunity
\t\t\t}, __("AuraCRM"));
\t\t}
\t},
});
''')

    write("public/js/overrides/customer_override.js", '''\
/**
 * AuraCRM — Customer Form Override
 */
frappe.ui.form.on("Customer", {
\trefresh(frm) {
\t\tif (!frm.is_new()) {
\t\t\tfrm.add_custom_button(__("360° View"), async () => {
\t\t\t\tconst aura = await frappe.auracrm.load();
\t\t\t\t// TODO: open Contact 360 floating window
\t\t\t}, __("AuraCRM"));
\t\t}
\t},
});
''')

    # ─── SCSS ─────────────────────────────────────────────────────
    print("\n🎨 Creating SCSS files...")

    write("public/scss/auracrm.bundle.scss", '''\
/**
 * AuraCRM — Main SCSS Bundle
 * ============================
 */
@import "./_variables";
@import "./_workspaces";
@import "./_pipeline";
@import "./_scorecards";
@import "./_dialer";
''')

    write("public/scss/_variables.scss", '''\
/* AuraCRM Design Tokens — extends Frappe Visual --fv-* vars */
$aura-primary: #6366f1;
$aura-primary-light: #818cf8;
$aura-success: #10b981;
$aura-warning: #f59e0b;
$aura-danger: #ef4444;
$aura-info: #3b82f6;

/* Score colors */
$score-hot: #ef4444;
$score-warm: #f59e0b;
$score-cool: #3b82f6;
$score-cold: #94a3b8;

/* SLA colors */
$sla-safe: #10b981;
$sla-warning: #f59e0b;
$sla-breach: #ef4444;
''')

    write("public/scss/_workspaces.scss", '''\
/* AuraCRM Workspace Layouts */
.aura-workspace {
\tdisplay: flex;
\tflex-direction: column;
\theight: 100vh;
\tbackground: var(--fv-bg-primary, #ffffff);
}

.aura-workspace-header {
\tdisplay: flex;
\talign-items: center;
\tjustify-content: space-between;
\tpadding: 16px 24px;
\tbackground: var(--fv-bg-surface, #ffffff);
\tborder-bottom: 1px solid var(--fv-border-primary, #e2e8f0);
}

.aura-workspace-body {
\tflex: 1;
\toverflow: auto;
\tpadding: 24px;
}

.aura-grid {
\tdisplay: grid;
\tgrid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
\tgap: 16px;
}
''')

    write("public/scss/_pipeline.scss", '''\
/* Pipeline Board Styles */
.aura-pipeline { display: flex; gap: 16px; overflow-x: auto; padding: 16px 0; }
.aura-pipeline-column {
\tmin-width: 280px;
\tmax-width: 320px;
\tbackground: var(--fv-bg-secondary, #f8fafc);
\tborder-radius: var(--fv-radius-lg, 16px);
\tpadding: 12px;
}
''')

    write("public/scss/_scorecards.scss", '''\
/* Agent Scorecards & Scoring */
.aura-score-gauge {
\twidth: 60px;
\theight: 60px;
\tborder-radius: 50%;
\tdisplay: flex;
\talign-items: center;
\tjustify-content: center;
\tfont-weight: 800;
\tfont-size: 18px;
}
''')

    write("public/scss/_dialer.scss", '''\
/* Auto-Dialer Panel */
.aura-dialer-panel {
\tposition: fixed;
\tbottom: 24px;
\tright: 24px;
\twidth: 360px;
\tbackground: var(--fv-bg-surface, white);
\tborder: 1px solid var(--fv-border-primary, #e2e8f0);
\tborder-radius: var(--fv-radius-lg, 16px);
\tbox-shadow: var(--fv-shadow-lg);
\tz-index: 10000;
}
''')

    print("\n✅ Scaffold complete!")
    print(f"\nTotal files created in {APP}")


if __name__ == "__main__":
    main()
