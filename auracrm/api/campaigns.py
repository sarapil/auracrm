"""
AuraCRM - Campaign Sequence API
=================================
REST API endpoints for the Campaign Sequence system.
"""
import frappe
from frappe import _
from frappe.utils import cint
from caps.utils.resolver import require_capability


@frappe.whitelist()
def activate_sequence(sequence_name):
    """Activate a campaign sequence."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("campaigns:activate")
    from auracrm.engines.campaign_engine import activate_sequence as _activate
    return _activate(sequence_name)


@frappe.whitelist()
def pause_sequence(sequence_name):
    """Pause an active sequence."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("campaigns:pause")
    from auracrm.engines.campaign_engine import pause_sequence as _pause
    return _pause(sequence_name)


@frappe.whitelist()
def get_sequence_progress(sequence_name):
    """Get sequence progress with step-level breakdown."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("campaigns:progress:view")
    from auracrm.engines.campaign_engine import get_sequence_progress as _progress
    return _progress(sequence_name)


@frappe.whitelist()
def enroll_contact(sequence_name, contact_doctype, contact_name,
                   email=None, phone=None):
    """Manually enroll a contact in a sequence."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("campaigns:enroll")
    from auracrm.engines.campaign_engine import enroll_contact as _enroll
    return _enroll(sequence_name, contact_doctype, contact_name, email, phone)


@frappe.whitelist()
def opt_out(sequence_name, contact_doctype, contact_name, reason=None):
    """Opt-out a contact from a sequence."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    require_capability("campaigns:opt_out")
    from auracrm.engines.campaign_engine import opt_out_contact as _opt_out
    return _opt_out(sequence_name, contact_doctype, contact_name, reason)


@frappe.whitelist()
def get_active_sequences():
    """Get all active campaign sequences with stats."""
    require_capability("campaigns:sequences:view")
    frappe.has_permission("Campaign Sequence", "read", throw=True)

    sequences = frappe.get_all(
        "Campaign Sequence",
        filters={"status": ["in", ["Active", "Paused"]]},
        fields=[
            "name", "sequence_name", "status", "target_doctype",
            "audience_segment", "total_contacts", "completed_contacts",
            "response_count", "opt_out_count",
        ],
        order_by="modified desc",
    )
    return sequences


@frappe.whitelist()
def get_enrollment_detail(enrollment_name):
    """Get detailed enrollment info with execution log."""
    require_capability("campaigns:enrollments:view")
    frappe.has_permission("Sequence Enrollment", "read", throw=True)

    enrollment = frappe.get_doc("Sequence Enrollment", enrollment_name)
    sequence = frappe.get_doc("Campaign Sequence", enrollment.sequence)

    import json
    return {
        "enrollment": enrollment.name,
        "sequence": enrollment.sequence,
        "sequence_name": sequence.sequence_name,
        "contact_doctype": enrollment.contact_doctype,
        "contact_name": enrollment.contact_name,
        "contact_email": enrollment.contact_email,
        "contact_phone": enrollment.contact_phone,
        "status": enrollment.status,
        "current_step": cint(enrollment.current_step_idx),
        "total_steps": cint(enrollment.total_steps),
        "enrolled_at": str(enrollment.enrolled_at or ""),
        "next_step_due": str(enrollment.next_step_due or ""),
        "completed_at": str(enrollment.completed_at or ""),
        "execution_log": json.loads(enrollment.execution_log or "[]"),
        "steps": [
            {
                "idx": i + 1,
                "name": s.step_name,
                "channel": s.channel,
                "template": s.template,
                "delay_days": s.delay_days,
                "delay_hours": s.delay_hours,
            }
            for i, s in enumerate(sequence.steps)
        ],
    }


@frappe.whitelist()
def get_sequence_enrollments(sequence_name, status=None, limit=50, start=0):
    """Get paginated enrollment list for a sequence."""
    require_capability("campaigns:enrollments:view")
    frappe.has_permission("Sequence Enrollment", "read", throw=True)

    filters = {"sequence": sequence_name}
    if status:
        filters["status"] = status

    enrollments = frappe.get_all(
        "Sequence Enrollment",
        filters=filters,
        fields=[
            "name", "contact_doctype", "contact_name",
            "contact_email", "status", "current_step_idx",
            "total_steps", "last_step_executed", "next_step_due",
        ],
        order_by="modified desc",
        limit_page_length=cint(limit),
        limit_start=cint(start),
    )

    total = frappe.db.count("Sequence Enrollment", filters=filters)

    return {
        "enrollments": enrollments,
        "total": total,
        "has_more": (cint(start) + cint(limit)) < total,
    }
