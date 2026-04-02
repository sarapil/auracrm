"""
AuraCRM - Auto Dialer API
===========================
REST API endpoints for the Auto Dialer system.
All functions are @frappe.whitelist() for frontend access.
"""
import frappe
from frappe import _
from frappe.utils import cint
from caps.utils.resolver import require_capability


@frappe.whitelist()
def start_campaign(campaign_name):
    """Start/activate a dialer campaign."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("dialer:campaign:start")
    from auracrm.engines.dialer_engine import start_campaign as _start
    return _start(campaign_name)


@frappe.whitelist()
def pause_campaign(campaign_name):
    """Pause an active campaign."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("dialer:campaign:pause")
    from auracrm.engines.dialer_engine import pause_campaign as _pause
    return _pause(campaign_name)


@frappe.whitelist()
def cancel_campaign(campaign_name):
    """Cancel a campaign."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("dialer:campaign:cancel")
    from auracrm.engines.dialer_engine import cancel_campaign as _cancel
    return _cancel(campaign_name)


@frappe.whitelist()
def get_campaign_progress(campaign_name):
    """Get campaign progress and stats."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("dialer:progress:view")
    from auracrm.engines.dialer_engine import get_campaign_progress as _progress
    return _progress(campaign_name)


@frappe.whitelist()
def get_agent_stats(campaign_name, agent=None):
    """Get per-agent dialing statistics."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("dialer:agent_stats:view")
    from auracrm.engines.dialer_engine import get_agent_dialer_stats as _stats
    return _stats(campaign_name, agent)


@frappe.whitelist()
def handle_call_result(entry_name, disposition, duration=0, notes=None, call_log=None):
    """Process a call result from the softphone."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("dialer:handle_result")
    from auracrm.engines.dialer_engine import handle_call_result as _result
    return _result(entry_name, disposition, cint(duration), notes, call_log)


@frappe.whitelist()
def skip_entry(entry_name, reason=None):
    """Skip a dialer entry."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("dialer:skip_entry")
    from auracrm.engines.dialer_engine import skip_entry as _skip
    return _skip(entry_name, reason)


@frappe.whitelist()
def add_entry(campaign_name, phone_number, contact_name=None,
              reference_doctype=None, reference_name=None, priority=0):
    """Add a new entry to a campaign."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("dialer:add_entry")
    from auracrm.engines.dialer_engine import add_entry_to_campaign as _add
    return _add(campaign_name, phone_number, contact_name,
                reference_doctype, reference_name, cint(priority))


@frappe.whitelist()
def get_active_campaigns():
    """Get all active dialer campaigns with stats summary."""
    require_capability("dialer:campaigns:view")
    frappe.has_permission("Auto Dialer Campaign", "read", throw=True)

    campaigns = frappe.get_all(
        "Auto Dialer Campaign",
        filters={"status": ["in", ["Active", "Paused"]]},
        fields=[
            "name", "campaign_name", "status", "call_type",
            "total_entries", "completed_entries", "success_count",
            "failed_count", "in_progress_count", "pending_count",
        ],
        order_by="modified desc",
    )
    return campaigns


@frappe.whitelist()
def get_next_entry_for_agent(campaign_name=None):
    """Get the next dialer entry assigned to the current user.

    Used by the softphone UI to fetch the next call in queue.
    """
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("dialer:next_entry")
    user = frappe.session.user
    filters = {
        "assigned_agent": user,
        "status": ["in", ["Dialing", "Ringing"]],
    }
    if campaign_name:
        filters["campaign"] = campaign_name

    entry = frappe.get_all(
        "Auto Dialer Entry",
        filters=filters,
        fields=[
            "name", "phone_number", "contact_name", "campaign",
            "reference_doctype", "reference_name", "attempts",
            "call_log",
        ],
        order_by="last_attempt desc",
        limit=1,
    )
    if entry:
        # Include call script if available
        campaign_doc = frappe.get_doc("Auto Dialer Campaign", entry[0].campaign)
        entry[0]["call_script"] = campaign_doc.call_script
        return entry[0]

    return None
