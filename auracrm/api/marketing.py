"""
AuraCRM — Marketing API
=========================
REST API endpoints for the Marketing Manager experience
and Agent Context Panel.
"""
import frappe
from frappe import _
from frappe.utils import cint
from caps.utils.resolver import require_capability


# ---------------------------------------------------------------------------
# Agent Context Panel
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_call_panel(contact_doctype, contact_name, campaign_name=None):
    """Get the full agent context panel data for a call."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("marketing:call_panel:view")
    from auracrm.engines.marketing_engine import get_agent_call_panel
    return get_agent_call_panel(contact_doctype, contact_name, campaign_name)


@frappe.whitelist()
def preview_call_context(contact_doctype, contact_name, campaign_name=None):
    """Preview what an agent sees — for marketing managers to test rules."""
    require_capability("marketing:context:preview")
    frappe.has_permission("Call Context Rule", "read", throw=True)
    from auracrm.engines.marketing_engine import get_call_context_preview
    return get_call_context_preview(contact_doctype, contact_name, campaign_name)


@frappe.whitelist()
def resolve_context_rule(contact_doctype, contact_name, campaign_name=None):
    """Find which Call Context Rule would apply for a contact."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("marketing:context:resolve")
    from auracrm.engines.marketing_engine import resolve_call_context
    rule_name = resolve_call_context(contact_doctype, contact_name, campaign_name)
    if rule_name:
        return frappe.get_doc("Call Context Rule", rule_name).as_dict()
    return None


# ---------------------------------------------------------------------------
# Auto-Classification
# ---------------------------------------------------------------------------
@frappe.whitelist()
def classify_contact(doctype, name):
    """Auto-classify a contact based on classification rules."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("marketing:classify_contact")
    from auracrm.engines.marketing_engine import auto_classify_contact
    return auto_classify_contact(doctype, name)


# Allowed doctypes for bulk classification — prevents SQL injection
_CLASSIFIABLE_DOCTYPES = {"Lead", "Contact", "Customer", "Prospect", "Opportunity"}


@frappe.whitelist()
def bulk_classify(doctype, names=None):
    """Bulk auto-classify contacts. names = JSON array or None for all."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    require_capability("marketing:bulk_classify")
    from auracrm.engines.marketing_engine import auto_classify_contact
    import json as _json

    # Security: validate doctype against allowlist (prevents SQL injection)
    if doctype not in _CLASSIFIABLE_DOCTYPES:
        frappe.throw(
            _("DocType {0} is not allowed for bulk classification. Allowed: {1}").format(
                doctype, ", ".join(sorted(_CLASSIFIABLE_DOCTYPES))
            ),
            title=_("Invalid DocType"),
        )

    if names:
        if isinstance(names, str):
            names = _json.loads(names)
    else:
        # Safe: doctype validated above against strict allowlist
        names = frappe.db.sql_list(
            "SELECT name FROM `tab{dt}` LIMIT 1000".format(dt=doctype)
        )

    results = {"classified": 0, "total": len(names), "details": []}
    for name in names:
        applied = auto_classify_contact(doctype, name)
        if applied:
            results["classified"] += 1
            results["details"].append({"name": name, "classifications": applied})

    return results


# ---------------------------------------------------------------------------
# Marketing Lists
# ---------------------------------------------------------------------------
@frappe.whitelist()
def sync_list(list_name):
    """Sync a marketing list from its source."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    require_capability("marketing:list:sync")
    from auracrm.engines.marketing_engine import sync_marketing_list
    return sync_marketing_list(list_name)


@frappe.whitelist()
def get_list_members(list_name, status=None, limit=50, offset=0):
    """Get members of a marketing list with optional status filter."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("marketing:list_members:view")
    filters = {"parent": list_name, "parenttype": "Marketing List"}
    if status:
        filters["status"] = status

    members = frappe.get_all(
        "Marketing List Member",
        filters=filters,
        fields=["member_doctype", "member_name", "full_name",
                "email", "phone", "status", "added_on"],
        order_by="added_on desc",
        limit_start=cint(offset),
        limit_page_length=cint(limit) or 50,
    )
    total = frappe.db.count("Marketing List Member", filters)
    return {"members": members, "total": total}


@frappe.whitelist()
def add_list_member(list_name, member_doctype, member_name, email=None, phone=None):
    """Manually add a member to a marketing list."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    require_capability("marketing:list_members:manage")
    doc = frappe.get_doc("Marketing List", list_name)
    # Check for duplicates
    for m in doc.members:
        if m.member_doctype == member_doctype and m.member_name == member_name:
            frappe.throw(_("This contact is already in the list"))

    full_name = frappe.db.get_value(
        member_doctype, member_name,
        "lead_name" if member_doctype == "Lead"
        else "customer_name" if member_doctype == "Customer"
        else "full_name",
    ) or member_name

    doc.append("members", {
        "member_doctype": member_doctype,
        "member_name": member_name,
        "full_name": full_name,
        "email": email or frappe.db.get_value(member_doctype, member_name, "email_id"),
        "phone": phone or frappe.db.get_value(member_doctype, member_name, "mobile_no"),
        "status": "Active",
        "added_on": frappe.utils.now_datetime(),
    })
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "added", "member_count": len(doc.members)}


@frappe.whitelist()
def remove_list_member(list_name, member_doctype, member_name):
    """Remove a member from a marketing list."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    require_capability("marketing:list_members:manage")
    doc = frappe.get_doc("Marketing List", list_name)
    to_remove = None
    for m in doc.members:
        if m.member_doctype == member_doctype and m.member_name == member_name:
            to_remove = m
            break
    if to_remove:
        doc.remove(to_remove)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "removed"}
    frappe.throw(_("Member not found in list"))


# ---------------------------------------------------------------------------
# Classification Management
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_classifications():
    """Get all contact classifications with stats."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("marketing:classifications:view")
    from auracrm.engines.marketing_engine import get_classification_stats
    return get_classification_stats()


@frappe.whitelist()
def get_classification_context(classification_name):
    """Get the agent context settings for a classification."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("marketing:classifications:view")
    cls = frappe.get_doc("Contact Classification", classification_name)
    return {
        "name": cls.name,
        "classification_name": cls.classification_name,
        "description": cls.description,
        "color": cls.color,
        "icon": cls.icon,
        "default_script": cls.default_script,
        "agent_notes": cls.agent_notes,
        "visible_fields": cls.visible_fields_json,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_dashboard():
    """Get the full marketing manager dashboard."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("marketing:dashboard:view")
    from auracrm.engines.marketing_engine import get_marketing_dashboard
    return get_marketing_dashboard()


# ---------------------------------------------------------------------------
# Context Rule Management
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_context_rules():
    """Get all call context rules with details."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("marketing:context_rules:manage")
    return frappe.get_all(
        "Call Context Rule",
        fields=["name", "rule_name", "enabled", "priority",
                "applies_to_campaign", "applies_to_segment",
                "applies_to_classification", "call_script",
                "show_contact_history", "show_last_call_summary",
                "show_campaign_info", "show_score", "show_sla_status"],
        order_by="priority desc",
    )


@frappe.whitelist()
def test_context_rule(rule_name, contact_doctype, contact_name):
    """Test a specific context rule against a contact — see what would show."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    require_capability("marketing:context_rules:manage")
    rule = frappe.get_doc("Call Context Rule", rule_name)
    from auracrm.engines.marketing_engine import get_agent_call_panel
    # Temporarily force this rule by passing its campaign
    campaign = rule.applies_to_campaign
    panel = get_agent_call_panel(contact_doctype, contact_name, campaign)
    panel["tested_rule"] = rule_name
    return panel
