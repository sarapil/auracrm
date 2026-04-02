"""
P23 — Interaction Automation Engine
Rule-based engine that triggers automated actions (emails, WhatsApp, SMS,
task creation, field updates) based on CRM events and conditions.
"""
import frappe
from frappe.utils import now_datetime, add_to_date, cint, time_diff_in_seconds
import json


# ---------------------------------------------------------------------------
# Scheduler Entry Points
# ---------------------------------------------------------------------------
def process_interaction_queue():
    """Scheduled every 10 minutes — process pending interaction queue items."""
    pending = frappe.get_all(
        "Interaction Queue",
        filters={"status": "Pending", "scheduled_time": ("<=", now_datetime())},
        fields=["name", "rule", "reference_doctype", "reference_name", "action_type", "action_data"],
        order_by="scheduled_time asc",
        limit_page_length=50,
    )

    for item in pending:
        try:
            frappe.db.set_value("Interaction Queue", item.name, "status", "Processing")
            frappe.db.commit()

            _execute_action(item)

            frappe.db.set_value(
                "Interaction Queue",
                item.name,
                {"status": "Completed", "executed_at": now_datetime()},
            )
            frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(title=f"Interaction Queue failed: {item.name}", message=str(e))
            frappe.db.set_value(
                "Interaction Queue",
                item.name,
                {"status": "Failed", "error_message": str(e)[:500]},
            )
            frappe.db.commit()


def evaluate_interaction_rules(doc, method):
    """doc_event hook — evaluate all active Interaction Automation Rules
    against the triggering document event."""
    doctype = doc.doctype
    event_type = _method_to_event(method)

    rules = frappe.get_all(
        "Interaction Automation Rule",
        filters={
            "enabled": 1,
            "trigger_doctype": doctype,
            "trigger_event": event_type,
        },
        fields=["name", "rule_name", "conditions_json", "action_type",
                "action_data", "delay_minutes", "max_executions_per_lead",
                "cooldown_hours"],
        order_by="priority desc",
    )

    for rule in rules:
        try:
            if _check_conditions(doc, rule):
                if _check_execution_limits(doc, rule):
                    _enqueue_action(doc, rule)
        except Exception as e:
            frappe.log_error(
                title=f"Interaction rule evaluation failed: {rule.rule_name}",
                message=f"Doc: {doc.name}\nError: {str(e)}",
            )


# ---------------------------------------------------------------------------
# Condition Evaluation
# ---------------------------------------------------------------------------
def _check_conditions(doc, rule):
    """Evaluate JSON conditions against the document."""
    conditions_json = rule.get("conditions_json")
    if not conditions_json:
        return True  # No conditions = always match

    try:
        conditions = json.loads(conditions_json)
    except (json.JSONDecodeError, TypeError):
        return True

    for condition in conditions:
        field = condition.get("field")
        operator = condition.get("operator", "=")
        value = condition.get("value")

        if not field:
            continue

        doc_value = doc.get(field)

        if not _eval_condition(doc_value, operator, value):
            return False

    return True


def _eval_condition(doc_value, operator, expected):
    """Evaluate a single condition."""
    if operator == "=":
        return str(doc_value) == str(expected)
    elif operator == "!=":
        return str(doc_value) != str(expected)
    elif operator == ">":
        return float(doc_value or 0) > float(expected or 0)
    elif operator == "<":
        return float(doc_value or 0) < float(expected or 0)
    elif operator == ">=":
        return float(doc_value or 0) >= float(expected or 0)
    elif operator == "<=":
        return float(doc_value or 0) <= float(expected or 0)
    elif operator == "in":
        return str(doc_value) in (expected if isinstance(expected, list) else str(expected).split(","))
    elif operator == "not in":
        return str(doc_value) not in (expected if isinstance(expected, list) else str(expected).split(","))
    elif operator == "like":
        return str(expected).lower() in str(doc_value or "").lower()
    elif operator == "is_set":
        return bool(doc_value)
    elif operator == "is_not_set":
        return not bool(doc_value)
    return True


def _check_execution_limits(doc, rule):
    """Check max executions per lead and cooldown period."""
    max_exec = cint(rule.get("max_executions_per_lead"))
    cooldown_hours = cint(rule.get("cooldown_hours"))

    if not max_exec and not cooldown_hours:
        return True

    filters = {
        "rule": rule.name,
        "reference_doctype": doc.doctype,
        "reference_name": doc.name,
        "status": ("in", ["Completed", "Pending", "Processing"]),
    }

    if max_exec:
        count = frappe.db.count("Interaction Queue", filters=filters)
        if count >= max_exec:
            return False

    if cooldown_hours:
        cutoff = add_to_date(now_datetime(), hours=-cooldown_hours)
        recent = frappe.db.count(
            "Interaction Queue",
            filters={**filters, "creation": (">=", cutoff)},
        )
        if recent > 0:
            return False

    return True


# ---------------------------------------------------------------------------
# Action Enqueueing & Execution
# ---------------------------------------------------------------------------
def _enqueue_action(doc, rule):
    """Create an Interaction Queue entry for delayed or immediate execution."""
    delay = cint(rule.get("delay_minutes"))
    scheduled = add_to_date(now_datetime(), minutes=delay) if delay else now_datetime()

    q = frappe.new_doc("Interaction Queue")
    q.rule = rule.name
    q.reference_doctype = doc.doctype
    q.reference_name = doc.name
    q.action_type = rule.get("action_type")
    q.action_data = rule.get("action_data")
    q.scheduled_time = scheduled
    q.status = "Pending"
    q.insert(ignore_permissions=True)


def _execute_action(item):
    """Execute the action based on action_type."""
    action_type = item.action_type
    action_data = _parse_action_data(item.action_data)

    executors = {
        "Send Email": _action_send_email,
        "Send WhatsApp": _action_send_whatsapp,
        "Send SMS": _action_send_sms,
        "Create Task": _action_create_task,
        "Update Field": _action_update_field,
        "Add Tag": _action_add_tag,
        "Notify User": _action_notify_user,
        "Create Note": _action_create_note,
    }

    executor = executors.get(action_type)
    if not executor:
        raise ValueError(f"Unknown action type: {action_type}")

    executor(item, action_data)


def _parse_action_data(data_str):
    """Parse action_data JSON string."""
    if not data_str:
        return {}
    try:
        return json.loads(data_str)
    except (json.JSONDecodeError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# Action Executors
# ---------------------------------------------------------------------------
def _action_send_email(item, data):
    """Send email using Frappe's email system."""
    recipients = data.get("recipients") or _get_contact_email(item)
    if not recipients:
        raise ValueError("No recipients found")

    frappe.sendmail(
        recipients=recipients if isinstance(recipients, list) else [recipients],
        subject=data.get("subject", "Notification from AuraCRM"),
        message=data.get("message", ""),
        template=data.get("template"),
        args=data.get("template_args", {}),
        reference_doctype=item.reference_doctype,
        reference_name=item.reference_name,
    )


def _action_send_whatsapp(item, data):
    """Send WhatsApp message via frappe_whatsapp integration."""
    phone = data.get("phone") or _get_contact_phone(item)
    if not phone:
        raise ValueError("No phone number found")

    try:
        from frappe_whatsapp.utils import send_whatsapp_message
        send_whatsapp_message(
            to=phone,
            message=data.get("message", ""),
            template=data.get("template"),
        )
    except ImportError:
        frappe.log_error(
            title="WhatsApp not available",
            message="frappe_whatsapp module not installed",
        )


def _action_send_sms(item, data):
    """Send SMS via Frappe's SMS manager."""
    phone = data.get("phone") or _get_contact_phone(item)
    if not phone:
        raise ValueError("No phone number found")

    from frappe.core.doctype.sms_settings.sms_settings import send_sms
    send_sms([phone], data.get("message", ""))


def _action_create_task(item, data):
    """Create a ToDo task."""
    task = frappe.new_doc("ToDo")
    task.description = data.get("description", f"Follow up on {item.reference_name}")
    task.allocated_to = data.get("assigned_to") or _get_owner(item)
    task.reference_type = item.reference_doctype
    task.reference_name = item.reference_name
    task.date = data.get("due_date") or add_to_date(now_datetime(), days=1).date()
    task.priority = data.get("priority", "Medium")
    task.insert(ignore_permissions=True)


def _action_update_field(item, data):
    """Update a field on the reference document."""
    field = data.get("field")
    value = data.get("value")
    if field and item.reference_doctype and item.reference_name:
        frappe.db.set_value(item.reference_doctype, item.reference_name, field, value)


def _action_add_tag(item, data):
    """Add a tag to the reference document."""
    tag = data.get("tag")
    if tag and item.reference_doctype and item.reference_name:
        frappe.db.sql(
            """INSERT IGNORE INTO `tabTag Link`
            (name, tag, document_type, document_name)
            VALUES (%s, %s, %s, %s)""",
            (frappe.generate_hash(length=10), tag, item.reference_doctype, item.reference_name),
        )


def _action_notify_user(item, data):
    """Send a Frappe notification to a user."""
    user = data.get("user") or _get_owner(item)
    if user:
        frappe.publish_realtime(
            event="auracrm_interaction_notification",
            message={
                "title": data.get("title", "AuraCRM Notification"),
                "message": data.get("message", f"Action required for {item.reference_name}"),
                "reference_doctype": item.reference_doctype,
                "reference_name": item.reference_name,
            },
            user=user,
        )


def _action_create_note(item, data):
    """Add a Comment/Note to the reference document."""
    if item.reference_doctype and item.reference_name:
        frappe.get_doc(
            {
                "doctype": "Comment",
                "comment_type": "Info",
                "reference_doctype": item.reference_doctype,
                "reference_name": item.reference_name,
                "content": data.get("note", "Automated interaction note"),
            }
        ).insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _method_to_event(method):
    """Convert Frappe hook method name to human-readable event."""
    mapping = {
        "after_insert": "After Insert",
        "on_update": "On Update",
        "validate": "Validate",
        "on_submit": "On Submit",
        "on_cancel": "On Cancel",
        "on_trash": "On Trash",
    }
    if callable(method):
        method = method.__name__
    return mapping.get(method, method)


def _get_contact_email(item):
    """Get email from the reference document."""
    if item.reference_doctype and item.reference_name:
        doc = frappe.get_doc(item.reference_doctype, item.reference_name)
        return doc.get("email_id") or doc.get("email") or ""
    return ""


def _get_contact_phone(item):
    """Get phone from the reference document."""
    if item.reference_doctype and item.reference_name:
        doc = frappe.get_doc(item.reference_doctype, item.reference_name)
        return doc.get("mobile_no") or doc.get("phone") or ""
    return ""


def _get_owner(item):
    """Get the owner/assigned user of the reference doc."""
    if item.reference_doctype and item.reference_name:
        return frappe.db.get_value(
            item.reference_doctype, item.reference_name, "owner"
        )
    return ""
