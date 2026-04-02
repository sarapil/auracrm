"""
AuraCRM - Campaign Sequence Engine (Phase 2)
=============================================
Manages multi-step automated campaign sequences with:
  - Enrollment management: populate contacts from Audience Segment
  - Step scheduler: process due steps every 5 minutes (delay_days/delay_hours)
  - Multi-channel dispatch: Email, WhatsApp, SMS, Call
  - Jinja condition evaluation per step (skip if condition not met)
  - Opt-out handling and tracking
  - Real-time progress stats on Campaign Sequence

Dispatch Channels:
  - Email: frappe.sendmail with Jinja template rendering
  - WhatsApp: arrowz.api.communications.send_message
  - SMS: arrowz.api.sms.send_sms
  - Call: Creates Auto Dialer Entry for the dialer engine

Integration Points:
  - AuraCRM: Audience Segment (member query), Communication Template (Jinja)
  - AuraCRM: Auto Dialer Engine (for Call channel)
  - Arrowz: send_message (WhatsApp/Telegram), send_sms
  - Frappe: sendmail for Email channel
"""
import frappe
from frappe import _
from frappe.utils import (
    now_datetime, add_to_date, get_datetime, getdate,
    cint, nowdate, time_diff_in_hours,
)
import json


# ---------------------------------------------------------------------------
# Scheduler Entry Point — runs every 5 minutes
# ---------------------------------------------------------------------------

def process_sequence_queue():
    """Cron job (every 5 minutes): process active campaign sequences.

    For each active sequence:
      1. Check for enrollments whose next step is due
      2. Evaluate step condition (Jinja)
      3. Dispatch via the step's channel
      4. Advance enrollment to next step or mark complete
    """
    active_sequences = frappe.get_all(
        "Campaign Sequence",
        filters={"status": "Active"},
        fields=["name"],
    )

    for seq in active_sequences:
        try:
            _process_single_sequence(seq.name)
        except Exception as e:
            frappe.log_error(
                title=f"Campaign Engine: Sequence {seq.name} error",
                message=str(e),
            )

    frappe.db.commit()


def _process_single_sequence(sequence_name):
    """Process all due enrollments for a single sequence."""
    now = now_datetime()

    # Get enrollments where next step is due
    due_enrollments = frappe.get_all(
        "Sequence Enrollment",
        filters={
            "sequence": sequence_name,
            "status": "Active",
            "next_step_due": ["<=", now],
        },
        fields=["name"],
        limit=200,  # Process in batches
    )

    if not due_enrollments:
        return

    sequence = frappe.get_doc("Campaign Sequence", sequence_name)
    steps = sequence.steps  # ordered child table rows

    for enrollment_data in due_enrollments:
        try:
            enrollment = frappe.get_doc("Sequence Enrollment", enrollment_data.name)
            _execute_next_step(enrollment, steps, sequence)
        except Exception as e:
            frappe.log_error(
                title=f"Campaign Engine: Enrollment {enrollment_data.name} error",
                message=str(e),
            )

    # Update sequence stats
    _update_sequence_stats(sequence_name)


def _execute_next_step(enrollment, steps, sequence):
    """Execute the next step for an enrollment."""
    step_idx = cint(enrollment.current_step_idx)

    if step_idx >= len(steps):
        # All steps completed
        enrollment.status = "Completed"
        enrollment.completed_at = now_datetime()
        enrollment.save(ignore_permissions=True)
        return

    step = steps[step_idx]

    # ---- Evaluate condition (Jinja) ----
    if step.condition and step.condition.strip():
        if not _evaluate_step_condition(step.condition, enrollment):
            # Condition not met — skip this step, schedule next
            enrollment.advance_step(
                step_name=step.step_name,
                channel=step.channel,
                success=True,
                error="Condition not met — skipped",
            )
            _schedule_next_step(enrollment, steps)
            return

    # ---- Dispatch via channel ----
    success, error = _dispatch_step(step, enrollment, sequence)

    # ---- Record & advance ----
    enrollment.advance_step(
        step_name=step.step_name,
        channel=step.channel,
        success=success,
        error=error,
    )

    # ---- Schedule next step if not yet completed ----
    if enrollment.status == "Active":
        _schedule_next_step(enrollment, steps)


# ---------------------------------------------------------------------------
# Step Condition Evaluation
# ---------------------------------------------------------------------------

def _evaluate_step_condition(condition_template, enrollment):
    """Evaluate a Jinja condition against the contact's current state.

    The condition is rendered as Jinja and should evaluate to truthy/falsy.
    Available variables: all fields of the contact document + enrollment meta.
    """
    context = _build_contact_context(enrollment)

    try:
        rendered = frappe.render_template(condition_template, context)
        # Strip and evaluate as boolean
        result = rendered.strip().lower()
        return result not in ("", "0", "false", "none", "no")
    except Exception as e:
        frappe.log_error(
            title=f"Campaign Engine: Condition error for {enrollment.name}",
            message=f"Condition: {condition_template}\nError: {str(e)}",
        )
        # On error, proceed (don't block the sequence)
        return True


def _build_contact_context(enrollment):
    """Build Jinja template context from the contact document."""
    context = {
        "enrollment": enrollment.name,
        "sequence": enrollment.sequence,
        "current_step": cint(enrollment.current_step_idx) + 1,
        "enrolled_at": str(enrollment.enrolled_at or ""),
        "contact_email": enrollment.contact_email or "",
        "contact_phone": enrollment.contact_phone or "",
    }

    # Load the actual contact document
    if enrollment.contact_doctype and enrollment.contact_name:
        try:
            doc = frappe.get_doc(enrollment.contact_doctype, enrollment.contact_name)
            for field in doc.meta.fields:
                if field.fieldtype not in ("Table", "Table MultiSelect", "Attach", "Attach Image"):
                    context[field.fieldname] = doc.get(field.fieldname)

            # Standard context aliases
            context.update({
                "lead_name": doc.get("lead_name") or doc.get("customer_name") or doc.get("title") or doc.name,
                "company": doc.get("company_name") or doc.get("company") or "",
                "status": doc.get("status") or "",
                "phone": doc.get("mobile_no") or doc.get("phone") or enrollment.contact_phone or "",
                "email": doc.get("email_id") or doc.get("email") or enrollment.contact_email or "",
                "responded": _has_responded(enrollment),
                "doc_name": doc.name,
                "doc_doctype": enrollment.contact_doctype,
            })
        except Exception:
            pass

    return context


def _has_responded(enrollment):
    """Check if the contact has responded (replied email, answered call, etc.)."""
    if not enrollment.contact_doctype or not enrollment.contact_name:
        return False

    # Check for communications
    replies = frappe.db.count(
        "Communication",
        filters={
            "reference_doctype": enrollment.contact_doctype,
            "reference_name": enrollment.contact_name,
            "sent_or_received": "Received",
            "creation": [">=", enrollment.enrolled_at or "2000-01-01"],
        },
    )
    return replies > 0


# ---------------------------------------------------------------------------
# Multi-Channel Dispatch
# ---------------------------------------------------------------------------

def _dispatch_step(step, enrollment, sequence):
    """Dispatch a step via the configured channel.

    Returns:
        tuple: (success: bool, error: str|None)
    """
    channel = step.channel

    if channel == "Email":
        return _dispatch_email(step, enrollment, sequence)
    elif channel == "WhatsApp":
        return _dispatch_whatsapp(step, enrollment)
    elif channel == "SMS":
        return _dispatch_sms(step, enrollment)
    elif channel == "Call":
        return _dispatch_call(step, enrollment, sequence)
    else:
        return False, f"Unknown channel: {channel}"


def _dispatch_email(step, enrollment, sequence):
    """Send an email using the Communication Template."""
    recipient = enrollment.contact_email
    if not recipient:
        return False, "No email address for contact"

    # Render template
    subject, message = _render_template(step.template, enrollment)
    if not message:
        return False, "Empty message after template rendering"

    try:
        frappe.sendmail(
            recipients=[recipient],
            subject=subject or f"[{sequence.sequence_name}] {step.step_name}",
            message=message,
            reference_doctype=enrollment.contact_doctype,
            reference_name=enrollment.contact_name,
            now=True,
        )
        return True, None
    except Exception as e:
        return False, str(e)


def _dispatch_whatsapp(step, enrollment):
    """Send a WhatsApp message via Arrowz."""
    phone = enrollment.contact_phone
    if not phone:
        return False, "No phone number for contact"

    _, message = _render_template(step.template, enrollment)
    if not message:
        return False, "Empty message after template rendering"

    try:
        from arrowz.api.communications import send_message
        result = send_message(
            channel="WhatsApp",
            recipient=phone,
            message=message,
            reference_doctype=enrollment.contact_doctype,
            reference_name=enrollment.contact_name,
        )
        if result and result.get("success") is False:
            return False, result.get("error", "WhatsApp send failed")
        return True, None
    except ImportError:
        return False, "Arrowz WhatsApp integration not available"
    except Exception as e:
        return False, str(e)


def _dispatch_sms(step, enrollment):
    """Send an SMS via Arrowz."""
    phone = enrollment.contact_phone
    if not phone:
        return False, "No phone number for contact"

    _, message = _render_template(step.template, enrollment)
    if not message:
        return False, "Empty message after template rendering"

    try:
        from arrowz.api.sms import send_sms
        result = send_sms(
            to_number=phone,
            message=message,
            party_type=enrollment.contact_doctype,
            party=enrollment.contact_name,
        )
        return True, None
    except ImportError:
        return False, "Arrowz SMS integration not available"
    except Exception as e:
        return False, str(e)


def _dispatch_call(step, enrollment, sequence):
    """Schedule a call via the Auto Dialer Engine.

    Creates an Auto Dialer Entry linked to an active campaign,
    or creates a one-off campaign for this sequence step.
    """
    phone = enrollment.contact_phone
    if not phone:
        return False, "No phone number for contact"

    try:
        # Find or create a dialer campaign for this sequence
        campaign_name = _get_or_create_sequence_campaign(sequence)

        entry = frappe.new_doc("Auto Dialer Entry")
        entry.campaign = campaign_name
        entry.phone_number = phone
        entry.contact_name = enrollment.get("contact_name") or ""
        entry.reference_doctype = enrollment.contact_doctype
        entry.reference_name = enrollment.contact_name
        entry.status = "Pending"
        entry.priority = 5  # Higher priority for sequence-triggered calls
        entry.insert(ignore_permissions=True)

        return True, None
    except Exception as e:
        return False, str(e)


def _get_or_create_sequence_campaign(sequence):
    """Get or create an Auto Dialer Campaign for sequence call steps."""
    campaign_name = f"SEQ-CALLS-{sequence.name}"

    if frappe.db.exists("Auto Dialer Campaign", {"campaign_name": campaign_name}):
        return frappe.db.get_value(
            "Auto Dialer Campaign",
            {"campaign_name": campaign_name},
            "name",
        )

    campaign = frappe.new_doc("Auto Dialer Campaign")
    campaign.campaign_name = campaign_name
    campaign.status = "Active"
    campaign.call_type = "Outbound"
    campaign.max_concurrent_calls = 1
    campaign.retry_attempts = 2
    campaign.retry_interval_minutes = 30
    campaign.insert(ignore_permissions=True)

    return campaign.name


# ---------------------------------------------------------------------------
# Template Rendering
# ---------------------------------------------------------------------------

def _render_template(template_name, enrollment):
    """Render a Communication Template with contact context.

    Returns:
        tuple: (subject, message)
    """
    if not template_name:
        return "", ""

    try:
        tmpl = frappe.get_doc("Communication Template", template_name)
    except frappe.DoesNotExistError:
        return "", ""

    if not tmpl.enabled:
        return "", f"Template {template_name} is disabled"

    context = _build_contact_context(enrollment)

    subject = ""
    message = ""

    try:
        if tmpl.subject:
            subject = frappe.render_template(tmpl.subject, context)
        if tmpl.message:
            message = frappe.render_template(tmpl.message, context)
    except Exception as e:
        frappe.log_error(
            title=f"Campaign Engine: Template render error",
            message=f"Template: {template_name}\nError: {str(e)}",
        )
        return "", ""

    return subject, message


# ---------------------------------------------------------------------------
# Step Scheduling
# ---------------------------------------------------------------------------

def _schedule_next_step(enrollment, steps):
    """Calculate and set the next_step_due datetime for an enrollment."""
    next_idx = cint(enrollment.current_step_idx)

    if next_idx >= len(steps):
        # No more steps
        return

    step = steps[next_idx]
    delay_hours = cint(step.delay_days) * 24 + cint(step.delay_hours)

    if delay_hours <= 0:
        # Execute immediately (next scheduler run)
        enrollment.next_step_due = now_datetime()
    else:
        enrollment.next_step_due = add_to_date(
            now_datetime(),
            hours=delay_hours,
        )

    enrollment.save(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Sequence Lifecycle
# ---------------------------------------------------------------------------

@frappe.whitelist()
def activate_sequence(sequence_name):
    """Activate a campaign sequence: create enrollments from audience segment."""
    frappe.has_permission("Campaign Sequence", "write", throw=True)
    sequence = frappe.get_doc("Campaign Sequence", sequence_name)

    if sequence.status not in ("Draft", "Paused"):
        frappe.throw(_("Sequence can only be activated from Draft or Paused status"))

    if not sequence.steps:
        frappe.throw(_("Add at least one step before activating"))

    # Create enrollments from audience segment
    if sequence.audience_segment and sequence.status == "Draft":
        count = _create_enrollments(sequence)
        if count == 0:
            frappe.throw(_("No contacts found in the audience segment"))
    elif not sequence.audience_segment:
        # Check if manual enrollments exist
        existing = frappe.db.count(
            "Sequence Enrollment",
            {"sequence": sequence_name, "status": "Active"},
        )
        if existing == 0:
            frappe.throw(_("No enrollments found. Link an Audience Segment or create enrollments manually."))

    sequence.status = "Active"
    sequence.save(ignore_permissions=True)

    _update_sequence_stats(sequence_name)

    frappe.publish_realtime(
        "sequence_activated",
        {"sequence": sequence_name, "name": sequence.sequence_name},
        after_commit=True,
    )
    return {"status": "Active", "message": _("Sequence activated")}


@frappe.whitelist()
def pause_sequence(sequence_name):
    """Pause an active sequence."""
    frappe.has_permission("Campaign Sequence", "write", throw=True)
    sequence = frappe.get_doc("Campaign Sequence", sequence_name)

    if sequence.status != "Active":
        frappe.throw(_("Only active sequences can be paused"))

    sequence.status = "Paused"
    sequence.save(ignore_permissions=True)
    return {"status": "Paused"}


@frappe.whitelist()
def opt_out_contact(sequence_name, contact_doctype, contact_name, reason=None):
    """Opt-out a contact from a sequence."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    enrollment = frappe.db.get_value(
        "Sequence Enrollment",
        {
            "sequence": sequence_name,
            "contact_doctype": contact_doctype,
            "contact_name": contact_name,
            "status": "Active",
        },
        "name",
    )

    if not enrollment:
        frappe.throw(_("No active enrollment found for this contact"))

    doc = frappe.get_doc("Sequence Enrollment", enrollment)
    doc.opt_out(reason)

    _update_sequence_stats(sequence_name)
    return {"status": "Opted Out"}


@frappe.whitelist()
def enroll_contact(sequence_name, contact_doctype, contact_name, email=None, phone=None):
    """Manually enroll a single contact in a sequence."""
    frappe.has_permission("Sequence Enrollment", "create", throw=True)

    # Check if already enrolled
    existing = frappe.db.exists(
        "Sequence Enrollment",
        {
            "sequence": sequence_name,
            "contact_doctype": contact_doctype,
            "contact_name": contact_name,
            "status": ["in", ["Active", "Paused"]],
        },
    )
    if existing:
        frappe.throw(_("Contact is already enrolled in this sequence"))

    sequence = frappe.get_doc("Campaign Sequence", sequence_name)

    enrollment = frappe.new_doc("Sequence Enrollment")
    enrollment.sequence = sequence_name
    enrollment.contact_doctype = contact_doctype
    enrollment.contact_name = contact_name
    enrollment.contact_email = email
    enrollment.contact_phone = phone
    enrollment.status = "Active"
    enrollment.current_step_idx = 0
    enrollment.enrolled_at = now_datetime()
    enrollment.total_steps = len(sequence.steps)
    enrollment.execution_log = "[]"
    enrollment.insert(ignore_permissions=True)

    # Schedule first step
    _schedule_next_step(enrollment, sequence.steps)

    _update_sequence_stats(sequence_name)
    return {"enrollment": enrollment.name}


# ---------------------------------------------------------------------------
# Enrollment Creation from Audience Segment
# ---------------------------------------------------------------------------

def _create_enrollments(sequence):
    """Create Sequence Enrollment records from Audience Segment."""
    seg = frappe.get_doc("Audience Segment", sequence.audience_segment)
    if not seg.filter_json or not seg.target_doctype:
        return 0

    filters = json.loads(seg.filter_json)
    frappe_filters = {}
    for f in filters:
        if len(f) >= 4:
            field, operator, value = f[1], f[2], f[3]
            if operator == "=":
                frappe_filters[field] = value
            else:
                frappe_filters[field] = [operator, value]

    # Determine email/phone fields
    field_map = {
        "Lead": {"email": "email_id", "phone": "mobile_no", "name_field": "lead_name"},
        "Opportunity": {"email": "contact_email", "phone": "contact_mobile", "name_field": "title"},
        "Customer": {"email": "email_id", "phone": "mobile_no", "name_field": "customer_name"},
    }
    fm = field_map.get(seg.target_doctype, {"email": "email", "phone": "phone", "name_field": "name"})

    records = frappe.get_all(
        seg.target_doctype,
        filters=frappe_filters,
        fields=["name", fm.get("email", "email"), fm.get("phone", "phone")],
        limit=5000,
    )

    count = 0
    for rec in records:
        # Skip already enrolled
        if frappe.db.exists("Sequence Enrollment", {
            "sequence": sequence.name,
            "contact_doctype": seg.target_doctype,
            "contact_name": rec.name,
            "status": ["in", ["Active", "Paused"]],
        }):
            continue

        enrollment = frappe.new_doc("Sequence Enrollment")
        enrollment.sequence = sequence.name
        enrollment.contact_doctype = seg.target_doctype
        enrollment.contact_name = rec.name
        enrollment.contact_email = rec.get(fm.get("email", "")) or ""
        enrollment.contact_phone = rec.get(fm.get("phone", "")) or ""
        enrollment.status = "Active"
        enrollment.current_step_idx = 0
        enrollment.enrolled_at = now_datetime()
        enrollment.total_steps = len(sequence.steps)
        enrollment.execution_log = "[]"
        enrollment.insert(ignore_permissions=True)

        # Schedule first step
        _schedule_next_step(enrollment, sequence.steps)
        count += 1

    return count


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def _update_sequence_stats(sequence_name):
    """Refresh Campaign Sequence statistics from enrollments."""
    stats = frappe.db.sql("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'Opted Out' THEN 1 ELSE 0 END) as opted_out
        FROM `tabSequence Enrollment`
        WHERE sequence = %s
    """, sequence_name, as_dict=True)[0]

    # Count responses (contacts that replied after enrollment)
    responses = 0
    enrollments = frappe.get_all(
        "Sequence Enrollment",
        filters={"sequence": sequence_name},
        fields=["contact_doctype", "contact_name", "enrolled_at"],
        limit=5000,
    )
    for e in enrollments:
        if _has_responded_simple(e.contact_doctype, e.contact_name, e.enrolled_at):
            responses += 1

    frappe.db.set_value("Campaign Sequence", sequence_name, {
        "total_contacts": cint(stats.total),
        "completed_contacts": cint(stats.completed),
        "opt_out_count": cint(stats.opted_out),
        "response_count": responses,
    }, update_modified=False)


def _has_responded_simple(doctype, docname, since):
    """Quick check for contact response."""
    if not doctype or not docname:
        return False
    return frappe.db.exists(
        "Communication",
        {
            "reference_doctype": doctype,
            "reference_name": docname,
            "sent_or_received": "Received",
            "creation": [">=", since or "2000-01-01"],
        },
    )


# ---------------------------------------------------------------------------
# Utility APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_sequence_progress(sequence_name):
    """Get detailed progress for a sequence."""
    frappe.has_permission("Campaign Sequence", "read", throw=True)

    _update_sequence_stats(sequence_name)
    seq = frappe.get_doc("Campaign Sequence", sequence_name)

    enrollments_by_step = frappe.db.sql("""
        SELECT
            current_step_idx,
            COUNT(*) as count
        FROM `tabSequence Enrollment`
        WHERE sequence = %s AND status = 'Active'
        GROUP BY current_step_idx
    """, sequence_name, as_dict=True)

    return {
        "sequence_name": seq.sequence_name,
        "status": seq.status,
        "total": cint(seq.total_contacts),
        "completed": cint(seq.completed_contacts),
        "responses": cint(seq.response_count),
        "opt_outs": cint(seq.opt_out_count),
        "completion_rate": round(
            cint(seq.completed_contacts) / max(cint(seq.total_contacts), 1) * 100, 1
        ),
        "enrollments_by_step": enrollments_by_step,
        "steps": [
            {"idx": i + 1, "name": s.step_name, "channel": s.channel}
            for i, s in enumerate(seq.steps)
        ],
    }
