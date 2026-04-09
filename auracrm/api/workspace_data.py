# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""AuraCRM — Workspace Data Provider API"""
import frappe
from frappe import _
from frappe.utils import cint
from caps.utils.resolver import require_capability


@frappe.whitelist()
def get_sales_agent_workspace():
    """Get all data needed for the Sales Agent workspace."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("workspace:agent:view")
    user = frappe.session.user

    # My leads
    my_leads = frappe.get_all(
        "Lead",
        filters={"lead_owner": user, "status": ["in", ["Open", "Replied"]]},
        fields=["name", "lead_name", "company_name", "phone", "mobile_no",
                "email_id", "utm_source", "status", "aura_score", "creation", "modified"],
        order_by="aura_score desc, modified desc",
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

    # Today's tasks
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
            "hot_leads": len([l for l in my_leads if (l.get("aura_score") or 0) >= 80]),
        },
    }


@frappe.whitelist()
def get_contact_360(doctype, name):
    """Get 360° view of a contact — all related data across systems.

    Supports Lead, Opportunity, Customer, and Contact doctypes.
    Returns enriched data including score, SLA, related opps/tasks, assignments,
    and full communication timeline.
    """
    require_capability("workspace:360:view")
    if doctype not in ("Lead", "Opportunity", "Customer", "Contact"):
        frappe.throw(_("360° view is not available for {0}").format(doctype))

    doc = frappe.get_doc(doctype, name)
    frappe.has_permission(doctype, "read", doc=doc, throw=True)

    info = doc.as_dict()

    # ── Resolve a display-friendly title ──────────────────────────
    display_name = (
        info.get("lead_name")
        or info.get("customer_name")
        or info.get("party_name")
        or info.get("contact_display")
        or info.get("first_name", "")
        or name
    )

    # ── Lead-specific enrichments ─────────────────────────────────
    score = 0
    score_label = "Cold"
    sla_status = None
    if doctype == "Lead":
        score = info.get("aura_score") or 0
        score_label = "Hot" if score >= 80 else "Warm" if score >= 50 else "Cold"
        # SLA breach check
        breach = frappe.get_all(
            "SLA Breach Log",
            filters={"reference_doctype": "Lead", "reference_name": name, "resolved": 0},
            fields=["name", "sla_policy", "breach_time", "creation"],
            limit=1,
        )
        if breach:
            sla_status = {"breached": True, "breach": breach[0]}
        else:
            sla_status = {"breached": False}

    # ── Opportunity-specific enrichments ──────────────────────────
    if doctype == "Opportunity":
        score = cint(info.get("probability")) or 0
        score_label = info.get("sales_stage") or ""
        breach = frappe.get_all(
            "SLA Breach Log",
            filters={"reference_doctype": "Opportunity", "reference_name": name, "resolved": 0},
            fields=["name", "sla_policy", "breach_time", "creation"],
            limit=1,
        )
        sla_status = {"breached": bool(breach), "breach": breach[0] if breach else None}

    # ── Related Opportunities (for Lead / Customer) ───────────────
    related_opps = []
    if doctype == "Lead":
        related_opps = frappe.get_all(
            "Opportunity",
            filters={"party_name": name, "opportunity_from": "Lead"},
            fields=["name", "opportunity_amount", "sales_stage", "status",
                     "expected_closing", "modified"],
            order_by="modified desc",
            limit=10,
        )
    elif doctype == "Customer":
        related_opps = frappe.get_all(
            "Opportunity",
            filters={"party_name": name, "opportunity_from": "Customer"},
            fields=["name", "opportunity_amount", "sales_stage", "status",
                     "expected_closing", "modified"],
            order_by="modified desc",
            limit=10,
        )

    # ── Related Leads (for Customer) ──────────────────────────────
    related_leads = []
    if doctype == "Customer":
        related_leads = frappe.get_all(
            "Lead",
            filters={"company_name": info.get("customer_name")},
            fields=["name", "lead_name", "status", "aura_score", "utm_source", "modified"],
            order_by="modified desc",
            limit=10,
        )

    # ── Open Tasks / ToDos ────────────────────────────────────────
    tasks = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": doctype,
            "reference_name": name,
            "status": "Open",
        },
        fields=["name", "description", "allocated_to", "date", "priority"],
        order_by="date asc",
        limit=10,
    )

    # ── Assignments ───────────────────────────────────────────────
    assignments = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": doctype,
            "reference_name": name,
            "status": "Open",
            "assigned_by": ["is", "set"],
        },
        fields=["allocated_to", "assigned_by", "date"],
        limit=5,
    )

    # ── Communication Timeline ────────────────────────────────────
    communications = []
    try:
        from arrowz.api.communications import get_communication_history
        communications = get_communication_history(doctype, name)
    except (ImportError, Exception):
        communications = frappe.get_all(
            "Communication",
            filters={"reference_doctype": doctype, "reference_name": name},
            fields=["name", "communication_type", "communication_medium",
                     "subject", "content", "sender", "recipients",
                     "sent_or_received", "creation"],
            order_by="creation desc",
            limit=50,
        )

    # ── Activity Log ──────────────────────────────────────────────
    activities = frappe.get_all(
        "Activity Log",
        filters={"reference_doctype": doctype, "reference_name": name},
        fields=["subject", "content", "creation", "owner"],
        order_by="creation desc",
        limit=20,
    )

    return {
        "doctype": doctype,
        "name": name,
        "display_name": display_name,
        "doc": info,
        "score": score,
        "score_label": score_label,
        "sla_status": sla_status,
        "status": info.get("status") or "",
        "source": info.get("utm_source") or "",
        "company_name": info.get("company_name") or info.get("customer_name") or "",
        "phone": info.get("mobile_no") or info.get("phone") or info.get("contact_mobile") or "",
        "email": info.get("email_id") or info.get("contact_email") or "",
        "owner": info.get("lead_owner") or info.get("_assign") or "",
        "creation": str(info.get("creation") or ""),
        "modified": str(info.get("modified") or ""),
        "opportunities": related_opps,
        "leads": related_leads,
        "tasks": tasks,
        "assignments": assignments,
        "communications": communications,
        "activities": activities,
    }
