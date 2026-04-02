"""
AuraCRM - SLA Engine (Phase 2 - Full Implementation)
=====================================================
Tracks response/resolution SLA for leads and opportunities.
- Monitors SLA breaches on a 5-minute cron
- Records breaches in SLA Breach Log
- Escalates via email/assignment
- Resolves SLA timers when agent responds (on_update hook)
"""
import frappe
from frappe import _
from frappe.utils import (
    now_datetime, time_diff_in_seconds, time_diff_in_hours,
    add_to_date, cint, flt, get_datetime, getdate
)


# ---- Scheduled: every 5 minutes ----

def check_sla_breaches():
    """Cron job: check all active SLA policies for breaches."""
    policies = frappe.get_all(
        "SLA Policy",
        filters={"enabled": 1},
        fields=["name", "applies_to", "response_time_minutes",
                "escalate_to", "status_filter"],
    )

    now = now_datetime()
    total_breaches = 0

    for policy in policies:
        total_breaches += _check_policy_breaches(policy, now)

    if total_breaches:
        frappe.db.commit()


def _check_policy_breaches(policy, now):
    """Check a single SLA policy for breaches, return count of new breaches."""
    dt = policy.get("applies_to")
    if not dt or not frappe.db.exists("DocType", dt):
        return 0

    response_minutes = flt(policy.get("response_time_minutes"))
    response_hours = response_minutes / 60.0 if response_minutes else 0

    if not response_hours:
        return 0

    # Build filters for open documents
    filters = _build_sla_filters(dt, policy)
    if filters is None:
        return 0

    docs = frappe.get_all(
        dt,
        filters=filters,
        fields=["name", "creation", "modified", "owner", "_assign"],
        limit=200,
    )

    breach_count = 0

    for doc in docs:
        creation = get_datetime(doc.creation)

        # Check response time SLA
        if response_hours:
            response_deadline = add_to_date(creation, hours=response_hours)
            if now > response_deadline:
                if not _breach_already_logged(policy.name, doc.name, "Response Time"):
                    _create_breach_log(policy, doc, "Response Time", response_deadline, now)
                    breach_count += 1

    return breach_count


def _build_sla_filters(dt, policy):
    """Build query filters for documents that might breach SLA."""
    filters = {}

    # DocType-specific open status
    if dt == "Lead":
        filters["status"] = ["not in", ["Converted", "Do Not Contact"]]
    elif dt == "Opportunity":
        filters["status"] = ["not in", ["Closed", "Lost", "Converted"]]
    else:
        # Generic: try 'status' field
        meta = frappe.get_meta(dt)
        if meta.has_field("status"):
            filters["status"] = ["not in", ["Closed", "Completed", "Cancelled", "Resolved"]]

    # Priority filter (if set on policy)
    priority_filter = policy.get("priority_filter")
    if priority_filter:
        meta = frappe.get_meta(dt)
        if meta.has_field("priority"):
            filters["priority"] = priority_filter

    return filters


def _breach_already_logged(policy_name, doc_name, breach_type):
    """Check if this breach was already recorded."""
    return frappe.db.exists("SLA Breach Log", {
        "sla_policy": policy_name,
        "reference_name": doc_name,
    })


def _create_breach_log(policy, doc, breach_type, deadline, now):
    """Create SLA Breach Log entry and trigger escalation."""
    exceeded_by = time_diff_in_hours(now, deadline)

    assigned_to = ""
    if doc.get("_assign"):
        try:
            import json
            assigns = json.loads(doc._assign)
            if assigns:
                assigned_to = assigns[0]
        except (ValueError, TypeError):
            pass

    breach = frappe.get_doc({
        "doctype": "SLA Breach Log",
        "sla_policy": policy.name,
        "reference_doctype": policy.get("applies_to"),
        "reference_name": doc.name,
        "breach_time": now,
        "assigned_to": assigned_to or doc.get("owner", ""),
    })

    try:
        breach.insert(ignore_permissions=True)
    except Exception:
        frappe.log_error("AuraCRM SLA: Failed to create breach log")
        return

    # Escalate
    _escalate_breach(policy, doc, breach_type, exceeded_by)


def _escalate_breach(policy, doc, breach_type, exceeded_by_hours):
    """Send escalation notification for SLA breach."""
    dt = policy.get("applies_to")
    doc_name = doc.name

    # Email escalation
    esc_email = policy.get("escalate_to")
    if esc_email:
        try:
            subject = "[AuraCRM SLA] %s Breach - %s %s" % (breach_type, dt, doc_name)
            message = (
                "<p><strong>SLA Breach Alert</strong></p>"
                "<p>Document: <a href='/desk/{dt_lower}/{name}'>{dt} {name}</a></p>"
                "<p>Breach Type: {breach_type}</p>"
                "<p>Exceeded By: {hours:.1f} hours</p>"
                "<p>Policy: {policy}</p>"
            ).format(
                dt_lower=dt.lower().replace(" ", "-"),
                dt=dt, name=doc_name,
                breach_type=breach_type,
                hours=exceeded_by_hours,
                policy=policy.name,
            )

            frappe.sendmail(
                recipients=[esc_email],
                subject=subject,
                message=message,
                now=True,
            )
        except Exception:
            frappe.log_error("AuraCRM SLA: Failed to send escalation email")

    # Real-time notification to escalation user
    if esc_email:
        try:
            frappe.publish_realtime(
                "sla_breach",
                {
                    "doctype": dt,
                    "name": doc_name,
                    "breach_type": breach_type,
                    "exceeded_by": round(exceeded_by_hours, 1),
                },
                user=esc_email,
            )
        except Exception:
            pass


# ---- Doc Event: on_update ----

def check_sla_on_update(doc, method=None):
    """Hook: on_update for Lead/Opportunity - resolve SLA timers when status changes."""
    if not doc.get("name"):
        return

    dt = doc.doctype
    doc_name = doc.name

    # Check if document moved to a "responded" or "closed" status
    old_status = doc.get_db_value("status") if doc.get("name") else None
    new_status = doc.get("status")

    if not old_status or old_status == new_status:
        return

    # Determine if this is a response (first status change from initial)
    resolved_statuses = _get_resolved_statuses(dt)
    responded_statuses = _get_responded_statuses(dt)

    if new_status in responded_statuses and old_status not in responded_statuses:
        # Mark response SLA as met - update open breach logs
        _resolve_breach(doc_name, "Response Time")

    if new_status in resolved_statuses:
        # Mark resolution SLA as met
        _resolve_breach(doc_name, "Resolution Time")
        _resolve_breach(doc_name, "Response Time")


def _get_responded_statuses(dt):
    """Return statuses that indicate first response."""
    if dt == "Lead":
        return ["Replied", "Interested", "Converted", "Quotation",
                "Opportunity", "Do Not Contact"]
    elif dt == "Opportunity":
        return ["Reply", "Interested", "Quotation", "Converted",
                "Negotiation", "Closed"]
    return ["Replied", "In Progress", "Closed"]


def _get_resolved_statuses(dt):
    """Return statuses that indicate resolution."""
    if dt == "Lead":
        return ["Converted", "Do Not Contact"]
    elif dt == "Opportunity":
        return ["Closed", "Lost", "Converted"]
    return ["Closed", "Resolved", "Completed", "Cancelled"]


def _resolve_breach(doc_name, breach_type):
    """Mark breach log as resolved if it exists."""
    breaches = frappe.get_all(
        "SLA Breach Log",
        filters={
            "reference_name": doc_name,
            "resolved": 0,
        },
        fields=["name"],
    )

    for b in breaches:
        frappe.db.set_value(
            "SLA Breach Log", b.name,
            {
                "resolved": 1,
                "resolved_at": now_datetime(),
                "resolved_by": frappe.session.user,
            },
            update_modified=False,
        )
