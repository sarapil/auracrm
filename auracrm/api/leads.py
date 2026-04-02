# Copyright (c) 2026, Arkan Labs and contributors
# auracrm/api/leads.py
# CAPS-gated Lead API endpoints

import frappe
from frappe import _
from auracrm.caps_integration.gate import require_capability, get_leads_query_filter, check_capability


@frappe.whitelist()
@require_capability("crm_lead_create")
def get_lead_list(
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    search: str = None,
    sort_by: str = "modified",
    sort_order: str = "desc",
):
    """
    Get paginated, filtered Lead list. Respects CAPS visibility rules.

    API: /api/method/auracrm.api.leads.get_lead_list
    """
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    filters = get_leads_query_filter()

    if status:
        filters["status"] = status

    or_filters = {}
    if search:
        or_filters = {
            "lead_name": ["like", f"%{search}%"],
            "email_id": ["like", f"%{search}%"],
            "mobile_no": ["like", f"%{search}%"],
            "company_name": ["like", f"%{search}%"],
        }

    start = (int(page) - 1) * int(page_size)

    leads = frappe.get_all(
        "Lead",
        filters=filters,
        or_filters=or_filters if or_filters else None,
        fields=[
            "name", "lead_name", "email_id", "mobile_no",
            "company_name", "status", "source", "lead_owner",
            "creation", "modified",
        ],
        order_by=f"{sort_by} {sort_order}",
        start=start,
        page_length=int(page_size),
    )

    total = frappe.db.count("Lead", filters=filters)

    return {
        "data": leads,
        "page": int(page),
        "page_size": int(page_size),
        "total": total,
        "total_pages": (total + int(page_size) - 1) // int(page_size),
    }


@frappe.whitelist()
@require_capability("osint_enrich")
def get_ai_profile(lead_name: str):
    """
    Get AI-enriched profile for a Lead.
    Requires osint_enrich capability.

    API: /api/method/auracrm.api.leads.get_ai_profile
    """
    if not lead_name:
        frappe.throw(_("Lead name is required"))

    lead = frappe.get_doc("Lead", lead_name)

    # Build profile from available OSINT data
    profile = {
        "lead_name": lead.lead_name,
        "email": lead.email_id,
        "phone": lead.mobile_no,
        "company": lead.company_name,
        "source": lead.source,
        "score": getattr(lead, "lead_score", 0),
    }

    # Enrich with OSINT data if available
    if frappe.db.exists("DocType", "OSINT Profile"):
        osint_profiles = frappe.get_all(
            "OSINT Profile",
            filters={"lead": lead_name},
            fields=["*"],
            limit=1,
        )
        if osint_profiles:
            profile["osint"] = osint_profiles[0]

    # Enrich with social profiles
    if frappe.db.exists("DocType", "Social Profile"):
        social_profiles = frappe.get_all(
            "Social Profile",
            filters={"lead": lead_name},
            fields=["platform", "profile_url", "followers", "engagement_rate"],
        )
        profile["social_profiles"] = social_profiles

    # Activity timeline
    activities = frappe.get_all(
        "Activity Log",
        filters={
            "reference_doctype": "Lead",
            "reference_name": lead_name,
        },
        fields=["subject", "creation", "owner"],
        order_by="creation desc",
        limit=10,
    )
    profile["recent_activities"] = activities

    return profile


@frappe.whitelist()
@require_capability("osint_hunt_run")
def trigger_osint_hunt(lead_name: str, hunt_type: str = "basic"):
    """
    Trigger an OSINT intelligence hunt for a Lead.
    Requires osint_hunt_run capability.

    API: /api/method/auracrm.api.leads.trigger_osint_hunt
    """
    if not lead_name:
        frappe.throw(_("Lead name is required"))

    if not frappe.db.exists("Lead", lead_name):
        frappe.throw(_("Lead {0} not found").format(lead_name))

    # Enqueue the hunt as background job
    frappe.enqueue(
        "auracrm.osint_engine.hunter.run_hunt",
        queue="long",
        timeout=600,
        lead_name=lead_name,
        hunt_type=hunt_type,
        user=frappe.session.user,
    )

    return {
        "status": "queued",
        "message": _("OSINT hunt '{0}' queued for lead {1}").format(hunt_type, lead_name),
        "lead": lead_name,
        "hunt_type": hunt_type,
    }


@frappe.whitelist()
@require_capability("social_publish")
def generate_content(lead_name: str = None, topic: str = None, platform: str = "general"):
    """
    Generate AI content suggestions related to a lead or topic.
    Requires social_publish capability.

    API: /api/method/auracrm.api.leads.generate_content
    """
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    context = {}

    if lead_name and frappe.db.exists("Lead", lead_name):
        lead = frappe.get_doc("Lead", lead_name)
        context["lead"] = {
            "name": lead.lead_name,
            "company": lead.company_name,
            "industry": getattr(lead, "industry", ""),
            "source": lead.source,
        }

    if topic:
        context["topic"] = topic

    context["platform"] = platform

    # Get content suggestions from AI engine if available
    suggestions = []
    try:
        from auracrm.content_engine.generator import generate_suggestions
        suggestions = generate_suggestions(context)
    except (ImportError, Exception):
        # Fallback: return template suggestions
        settings = frappe.get_single("AuraCRM Settings")
        preset_code = getattr(settings, "active_industry_preset", "")

        topic_suggestions = []
        if preset_code:
            preset = frappe.db.get_value(
                "AuraCRM Industry Preset",
                {"preset_code": preset_code},
                "content_topic_suggestions",
            )
            if preset:
                topic_suggestions = frappe.parse_json(preset) or []

        suggestions = [
            {"type": "topic", "content": t, "platform": platform}
            for t in (topic_suggestions or ["Industry News", "Tips & Tricks", "Case Study", "Product Update"])
        ]

    return {
        "suggestions": suggestions,
        "context": context,
    }


@frappe.whitelist()
def get_lead_capabilities():
    """
    Returns which lead-related actions the current user can perform.
    Useful for frontend UI rendering.

    API: /api/method/auracrm.api.leads.get_lead_capabilities
    """
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    return {
        "can_create": check_capability("crm_lead_create"),
        "can_edit": check_capability("crm_lead_edit"),
        "can_delete": check_capability("crm_lead_delete"),
        "can_assign": check_capability("crm_lead_assign"),
        "can_view_all": check_capability("crm_lead_view_all"),
        "can_enrich": check_capability("osint_enrich"),
        "can_hunt": check_capability("osint_hunt_run"),
        "can_publish": check_capability("social_publish"),
        "can_manage_pipeline": check_capability("crm_pipeline_manage"),
    }
