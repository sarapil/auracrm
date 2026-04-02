"""
P25 — Nurture Journey Engine
Multi-step drip campaigns that move leads through personalised sequences
of emails, WhatsApp messages, tasks, and wait periods.
"""
import frappe
from frappe.utils import now_datetime, add_to_date, getdate, cint, time_diff_in_hours
import json


# ---------------------------------------------------------------------------
# Scheduler — runs every 10 minutes
# ---------------------------------------------------------------------------
def process_nurture_queue():
    """Main scheduler entry: advance active nurture instances to the next step."""
    active = frappe.get_all(
        "Nurture Lead Instance",
        filters={"status": "Active", "next_action_at": ("<=", now_datetime())},
        fields=["name", "lead", "nurture_journey", "current_step_index"],
        order_by="next_action_at asc",
        limit_page_length=100,
    )

    for instance in active:
        try:
            _advance_instance(instance)
        except Exception as e:
            frappe.log_error(
                title=f"Nurture engine error: {instance.name}",
                message=str(e),
            )
            frappe.db.set_value(
                "Nurture Lead Instance", instance.name, "status", "Error"
            )
            frappe.db.commit()


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------
def enroll_lead(lead_name, journey_name, source="manual"):
    """Enroll a lead into a nurture journey.

    Args:
        lead_name: Name of the Lead document.
        journey_name: Name of the Nurture Journey.
        source: How enrollment happened (manual, automation, api).

    Returns:
        Name of the created Nurture Lead Instance.
    """
    # Check for existing active enrollment
    existing = frappe.db.exists(
        "Nurture Lead Instance",
        {"lead": lead_name, "nurture_journey": journey_name, "status": "Active"},
    )
    if existing:
        frappe.msgprint(f"Lead {lead_name} is already enrolled in {journey_name}")
        return existing

    journey = frappe.get_doc("Nurture Journey", journey_name)
    if not journey.enabled:
        frappe.throw(f"Journey {journey_name} is not enabled")

    steps = _get_journey_steps(journey_name)
    if not steps:
        frappe.throw(f"Journey {journey_name} has no steps")

    first_step = steps[0]
    delay_minutes = cint(first_step.get("delay_minutes"))

    instance = frappe.new_doc("Nurture Lead Instance")
    instance.lead = lead_name
    instance.nurture_journey = journey_name
    instance.enrollment_source = source
    instance.current_step_index = 0
    instance.status = "Active"
    instance.next_action_at = add_to_date(now_datetime(), minutes=delay_minutes)
    instance.enrolled_at = now_datetime()
    instance.insert(ignore_permissions=True)
    frappe.db.commit()

    return instance.name


@frappe.whitelist()
def enroll_lead_api(lead_name, journey_name):
    """Whitelisted API to enroll a lead."""
    return enroll_lead(lead_name, journey_name, source="api")


def auto_enroll_on_lead_insert(doc, method):
    """doc_event: Lead → after_insert.
    Auto-enroll in journeys that match the lead's criteria."""
    journeys = frappe.get_all(
        "Nurture Journey",
        filters={"enabled": 1, "auto_enroll": 1},
        fields=["name", "auto_enroll_conditions"],
    )

    for journey in journeys:
        if _matches_auto_enroll(doc, journey):
            try:
                enroll_lead(doc.name, journey.name, source="auto")
            except Exception as e:
                frappe.log_error(
                    title=f"Auto-enroll failed: {doc.name} → {journey.name}",
                    message=str(e),
                )


def pause_on_conversion(doc, method):
    """doc_event: Lead → on_update.
    Pause/complete nurture if lead status changes to converted/won."""
    terminal_statuses = ["Converted", "Do Not Contact", "Lost"]
    if doc.get("status") not in terminal_statuses:
        return

    active_instances = frappe.get_all(
        "Nurture Lead Instance",
        filters={"lead": doc.name, "status": "Active"},
        pluck="name",
    )
    for inst_name in active_instances:
        frappe.db.set_value(
            "Nurture Lead Instance",
            inst_name,
            {"status": "Completed", "completed_reason": f"Lead status: {doc.status}"},
        )
    if active_instances:
        frappe.db.commit()


# ---------------------------------------------------------------------------
# Step Advancement
# ---------------------------------------------------------------------------
def _advance_instance(instance):
    """Execute the current step and schedule the next one."""
    journey_name = instance.nurture_journey
    steps = _get_journey_steps(journey_name)
    current_idx = cint(instance.current_step_index)

    if current_idx >= len(steps):
        # Journey complete
        frappe.db.set_value(
            "Nurture Lead Instance",
            instance.name,
            {"status": "Completed", "completed_reason": "All steps completed"},
        )
        frappe.db.commit()
        return

    step = steps[current_idx]
    lead = frappe.get_doc("Lead", instance.lead)

    # Execute the step action
    _execute_step(step, lead, instance)

    # Move to next step
    next_idx = current_idx + 1
    if next_idx >= len(steps):
        frappe.db.set_value(
            "Nurture Lead Instance",
            instance.name,
            {
                "status": "Completed",
                "current_step_index": next_idx,
                "completed_reason": "All steps completed",
            },
        )
    else:
        next_step = steps[next_idx]
        delay = cint(next_step.get("delay_minutes"))
        frappe.db.set_value(
            "Nurture Lead Instance",
            instance.name,
            {
                "current_step_index": next_idx,
                "next_action_at": add_to_date(now_datetime(), minutes=delay),
                "last_action_at": now_datetime(),
            },
        )

    frappe.db.commit()


def _execute_step(step, lead, instance):
    """Execute a single nurture step action."""
    action = step.get("action_type")

    if action == "Send Email":
        _step_send_email(step, lead)
    elif action == "Send WhatsApp":
        _step_send_whatsapp(step, lead)
    elif action == "Create Task":
        _step_create_task(step, lead)
    elif action == "Update Field":
        _step_update_field(step, lead)
    elif action == "Wait":
        pass  # Just a delay, nothing to execute
    elif action == "Condition Check":
        _step_condition_check(step, lead, instance)
    else:
        frappe.log_error(
            title=f"Unknown nurture step action: {action}",
            message=f"Instance: {instance.name}, Step: {step.get('step_name')}",
        )


def _step_send_email(step, lead):
    """Send nurture email to lead."""
    email = lead.get("email_id") or lead.get("email")
    if not email:
        return

    template = step.get("email_template")
    subject = step.get("subject") or "Update from AuraCRM"
    message = step.get("message_body") or ""

    # Simple variable replacement
    message = message.replace("{{lead_name}}", lead.lead_name or "")
    message = message.replace("{{first_name}}", (lead.first_name or lead.lead_name or "").split()[0])
    message = message.replace("{{company}}", lead.company_name or "")

    frappe.sendmail(
        recipients=[email],
        subject=subject,
        message=message,
        template=template,
        reference_doctype="Lead",
        reference_name=lead.name,
    )


def _step_send_whatsapp(step, lead):
    """Send WhatsApp message to lead."""
    phone = lead.get("mobile_no") or lead.get("phone")
    if not phone:
        return

    try:
        from frappe_whatsapp.utils import send_whatsapp_message

        message = step.get("message_body") or ""
        message = message.replace("{{lead_name}}", lead.lead_name or "")
        message = message.replace("{{first_name}}", (lead.first_name or lead.lead_name or "").split()[0])

        send_whatsapp_message(to=phone, message=message)
    except ImportError:
        frappe.log_error(title="WhatsApp not available for nurture step")


def _step_create_task(step, lead):
    """Create a follow-up task for the assigned agent."""
    task = frappe.new_doc("ToDo")
    task.description = (step.get("task_description") or f"Nurture follow-up: {lead.lead_name}").replace(
        "{{lead_name}}", lead.lead_name or ""
    )
    task.allocated_to = lead.get("lead_owner") or lead.owner
    task.reference_type = "Lead"
    task.reference_name = lead.name
    task.date = add_to_date(now_datetime(), days=1).date()
    task.priority = step.get("task_priority") or "Medium"
    task.insert(ignore_permissions=True)


def _step_update_field(step, lead):
    """Update a field on the lead."""
    field = step.get("target_field")
    value = step.get("target_value")
    if field:
        frappe.db.set_value("Lead", lead.name, field, value)


def _step_condition_check(step, lead, instance):
    """Check a condition and optionally skip to a different step."""
    conditions_json = step.get("conditions_json")
    if not conditions_json:
        return

    try:
        conditions = json.loads(conditions_json)
    except (json.JSONDecodeError, TypeError):
        return

    for cond in conditions:
        field = cond.get("field")
        expected = cond.get("value")
        doc_value = lead.get(field)
        if str(doc_value) != str(expected):
            # Condition not met — optionally jump to step
            jump_to = cond.get("jump_to_step")
            if jump_to is not None:
                frappe.db.set_value(
                    "Nurture Lead Instance",
                    instance.name,
                    "current_step_index",
                    cint(jump_to),
                )
            break


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_journey_steps(journey_name):
    """Return ordered list of steps for a journey."""
    return frappe.get_all(
        "Nurture Step",
        filters={"parent": journey_name, "parenttype": "Nurture Journey"},
        fields=["*"],
        order_by="idx asc",
    )


def _matches_auto_enroll(doc, journey):
    """Check if a lead matches the auto-enroll conditions of a journey."""
    conditions_str = journey.get("auto_enroll_conditions")
    if not conditions_str:
        return True  # No conditions = all leads

    try:
        conditions = json.loads(conditions_str)
    except (json.JSONDecodeError, TypeError):
        return True

    for cond in conditions:
        field = cond.get("field")
        value = cond.get("value")
        if field and str(doc.get(field)) != str(value):
            return False

    return True
