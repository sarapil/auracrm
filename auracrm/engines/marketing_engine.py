# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Marketing Engine (Phase 3)
======================================
Powers the Marketing Manager experience and Agent Context Panel:

1. **Call Context Resolution** — Finds the best-matching Call Context Rule for
   a contact based on campaign, segment, and classification. Rules have priority;
   highest matching rule wins.
2. **Agent Call Panel** — Assembles the full context panel data an agent sees
   during a call: rendered script, contact history, last call summary, campaign
   info, lead score, SLA status, visible/highlight fields.
3. **Auto-Classification** — Applies Contact Classification rules to contacts.
4. **Marketing List Sync** — Syncs list members from Audience Segments or
   Contact Classifications.
5. **Analytics** — Campaign performance, list health, classification stats.
"""
import frappe
from frappe import _
from frappe.utils import (
    now_datetime, today, cint, flt, getdate, add_days,
    get_first_day, get_last_day, get_datetime,
)
import json


# ---------------------------------------------------------------------------
# 1. Call Context Resolution
# ---------------------------------------------------------------------------
@frappe.whitelist()
def resolve_call_context(contact_doctype, contact_name, campaign_name=None):
    """
    Find the best-matching Call Context Rule for a contact.

    Priority resolution order:
      1. Campaign-specific rule (if campaign_name provided)
      2. Classification-specific rule (from contact's _user_tags)
      3. Segment-specific rule (contact matches audience segment)
      4. Default fallback rule (no campaign/segment/classification)

    Within each level, higher `priority` value wins.

    Returns:
        Call Context Rule name or None
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    rules = frappe.get_all(
        "Call Context Rule",
        filters={"enabled": 1},
        fields=[
            "name", "priority", "applies_to_campaign",
            "applies_to_segment", "applies_to_classification",
        ],
        order_by="priority desc",
    )

    if not rules:
        return None

    # Gather contact attributes
    contact_tags = _get_contact_tags(contact_doctype, contact_name)
    contact_segments = _get_contact_segments(contact_doctype, contact_name)

    best_rule = None
    best_score = -1

    for rule in rules:
        score = _score_rule(rule, campaign_name, contact_tags, contact_segments)
        if score > best_score:
            best_score = score
            best_rule = rule.name

    return best_rule


def _score_rule(rule, campaign_name, contact_tags, contact_segments):
    """Score how well a rule matches the current context. Higher = better."""
    score = 0
    matches = 0
    requirements = 0

    # Campaign match (strongest signal)
    if rule.applies_to_campaign:
        requirements += 1
        if campaign_name and rule.applies_to_campaign == campaign_name:
            score += 100
            matches += 1
        else:
            return -1  # Hard fail: rule requires specific campaign but doesn't match

    # Classification match
    if rule.applies_to_classification:
        requirements += 1
        if rule.applies_to_classification in contact_tags:
            score += 50
            matches += 1
        else:
            return -1  # Hard fail

    # Segment match
    if rule.applies_to_segment:
        requirements += 1
        if rule.applies_to_segment in contact_segments:
            score += 25
            matches += 1
        else:
            return -1  # Hard fail

    # Fallback rule (no criteria) — lowest priority
    if requirements == 0:
        score = 1

    # Add rule priority as tiebreaker
    score += cint(rule.priority) * 0.1

    return score


def _get_contact_tags(doctype, name):
    """Get contact classification tags."""
    try:
        tags = frappe.db.get_value(doctype, name, "_user_tags") or ""
        return set(t.strip() for t in tags.split(",") if t.strip())
    except Exception:
        return set()


def _get_contact_segments(doctype, name):
    """Determine which Audience Segments a contact belongs to."""
    segments = set()
    try:
        all_segments = frappe.get_all(
            "Audience Segment",
            filters={"enabled": 1},
            fields=["name", "target_doctype", "filter_json"],
        )
        for seg in all_segments:
            if seg.target_doctype != doctype:
                continue
            if _contact_matches_segment(doctype, name, seg.filter_json):
                segments.add(seg.name)
    except Exception:
        pass
    return segments


def _contact_matches_segment(doctype, name, filter_json):
    """Check if a contact matches an audience segment's filter criteria."""
    if not filter_json:
        return False
    try:
        filters = json.loads(filter_json)
        if isinstance(filters, list):
            filter_dict = {}
            for f in filters:
                if len(f) >= 3:
                    field, op, val = f[0], f[1], f[2]
                    filter_dict[field] = (op, val)
            filters = filter_dict

        filters["name"] = name
        exists = frappe.db.count(doctype, filters)
        return exists > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 2. Agent Call Panel — Full context data
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_agent_call_panel(contact_doctype, contact_name, campaign_name=None):
    """
    Assemble the full Agent Context Panel data for a call.

    Returns a dict with:
      - contact: Basic contact info
      - script: Rendered call script (Jinja template with contact data)
      - script_notes: Additional guidance notes
      - history: Recent communication history
      - last_call: Summary of the last call
      - campaign_info: Campaign details if applicable
      - score: Lead/Opportunity score
      - sla_status: Current SLA status
      - visible_fields: Fields to show on the panel
      - highlight_fields: Fields to highlight/emphasize
      - pre_call_briefing: Pre-call prep notes
      - post_call_checklist: Post-call action items
      - classification: Contact's classification(s)
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    # Get the matching context rule
    rule_name = resolve_call_context(contact_doctype, contact_name, campaign_name)
    rule = None
    if rule_name:
        rule = frappe.get_doc("Call Context Rule", rule_name)

    # Build the panel data
    panel = {
        "contact": _get_contact_info(contact_doctype, contact_name),
        "script": None,
        "script_notes": None,
        "history": [],
        "last_call": None,
        "campaign_info": None,
        "score": _get_contact_score(contact_doctype, contact_name),
        "sla_status": _get_sla_status(contact_doctype, contact_name),
        "visible_fields": [],
        "highlight_fields": [],
        "pre_call_briefing": None,
        "post_call_checklist": [],
        "classification": list(_get_contact_tags(contact_doctype, contact_name)),
        "rule_applied": rule_name,
    }

    if rule:
        # Render call script
        if rule.call_script:
            panel["script"] = _render_call_script(
                rule.call_script, contact_doctype, contact_name
            )
        panel["script_notes"] = rule.script_notes

        # Contact history
        if rule.show_contact_history:
            max_items = cint(rule.max_history_items) or 10
            panel["history"] = _get_contact_history(
                contact_doctype, contact_name, max_items
            )

        # Last call summary
        if rule.show_last_call_summary:
            panel["last_call"] = _get_last_call_summary(contact_doctype, contact_name)

        # Campaign info
        if rule.show_campaign_info and campaign_name:
            panel["campaign_info"] = _get_campaign_info(campaign_name)

        # Fields
        if rule.visible_fields_json:
            try:
                panel["visible_fields"] = json.loads(rule.visible_fields_json)
            except Exception:
                pass
        if rule.highlight_fields_json:
            try:
                panel["highlight_fields"] = json.loads(rule.highlight_fields_json)
            except Exception:
                pass

        # Briefing & checklist
        panel["pre_call_briefing"] = rule.pre_call_briefing
        if rule.post_call_checklist:
            try:
                panel["post_call_checklist"] = json.loads(rule.post_call_checklist)
            except Exception:
                pass
    else:
        # No specific rule — show defaults
        panel["history"] = _get_contact_history(contact_doctype, contact_name, 5)
        panel["last_call"] = _get_last_call_summary(contact_doctype, contact_name)

    return panel


# ---------------------------------------------------------------------------
# Panel data assemblers
# ---------------------------------------------------------------------------
def _get_contact_info(doctype, name):
    """Get basic contact information."""
    try:
        doc = frappe.get_doc(doctype, name)
        info = {
            "doctype": doctype,
            "name": name,
            "full_name": "",
            "email": "",
            "phone": "",
            "company": "",
            "source": "",
            "status": "",
        }
        # Map common fields
        if doctype == "Lead":
            info.update({
                "full_name": doc.lead_name or "",
                "email": doc.email_id or "",
                "phone": doc.mobile_no or doc.phone or "",
                "company": doc.company_name or "",
                "source": doc.source or "",
                "status": doc.status or "",
            })
        elif doctype == "Contact":
            info.update({
                "full_name": f"{doc.first_name or ''} {doc.last_name or ''}".strip(),
                "email": doc.email_id or "",
                "phone": doc.mobile_no or doc.phone or "",
                "company": doc.company_name or "",
            })
        elif doctype == "Customer":
            info.update({
                "full_name": doc.customer_name or "",
                "email": doc.email_id or "",
                "phone": doc.mobile_no or "",
                "company": doc.customer_name or "",
            })
        elif doctype == "Opportunity":
            info.update({
                "full_name": doc.party_name or doc.customer_name or "",
                "email": doc.contact_email or "",
                "phone": doc.contact_mobile or "",
                "status": doc.status or "",
            })
        return info
    except Exception:
        return {"doctype": doctype, "name": name}


def _get_contact_score(doctype, name):
    """Get the AuraCRM score for a contact."""
    try:
        score = frappe.db.get_value(doctype, name, "aura_score")
        return cint(score)
    except Exception:
        return 0


def _get_sla_status(doctype, name):
    """Get current SLA status for a contact's open items."""
    try:
        breaches = frappe.get_all(
            "SLA Breach Log",
            filters={
                "reference_doctype": doctype,
                "reference_name": name,
                "status": ("!=", "Resolved"),
            },
            fields=["name", "severity", "breached_at", "response_deadline"],
            order_by="creation desc",
            limit=3,
        )
        if breaches:
            return {"status": "At Risk", "breaches": breaches}
        return {"status": "On Track", "breaches": []}
    except Exception:
        return {"status": "Unknown", "breaches": []}


def _render_call_script(template_name, contact_doctype, contact_name):
    """Render a Communication Template with contact data using Jinja."""
    try:
        template = frappe.get_doc("Communication Template", template_name)
        content = template.get("content") or template.get("subject") or ""

        # Build context for Jinja rendering
        doc = frappe.get_doc(contact_doctype, contact_name)
        context = {
            "doc": doc,
            "contact_name": doc.get("lead_name") or doc.get("customer_name") or doc.get("name"),
            "company": doc.get("company_name") or doc.get("customer_name") or "",
            "phone": doc.get("mobile_no") or doc.get("phone") or "",
            "email": doc.get("email_id") or "",
            "status": doc.get("status") or "",
            "owner": doc.get("owner") or "",
            "score": doc.get("aura_score") or 0,
            "source": doc.get("source") or "",
        }

        rendered = frappe.render_template(content, context)
        return {
            "template_name": template_name,
            "rendered_html": rendered,
            "subject": template.get("subject") or "",
        }
    except Exception as e:
        return {
            "template_name": template_name,
            "rendered_html": f"<p>Error rendering script: {str(e)}</p>",
            "subject": "",
        }


def _get_contact_history(contact_doctype, contact_name, max_items=10):
    """Get recent communications for a contact."""
    history = []

    # Frappe Communications
    comms = frappe.get_all(
        "Communication",
        filters={
            "reference_doctype": contact_doctype,
            "reference_name": contact_name,
        },
        fields=[
            "name", "communication_type", "communication_medium",
            "subject", "content", "sent_or_received",
            "sender", "creation", "communication_date",
        ],
        order_by="communication_date desc",
        limit=max_items,
    )
    for c in comms:
        history.append({
            "type": "communication",
            "medium": c.communication_medium or c.communication_type,
            "direction": c.sent_or_received,
            "subject": c.subject,
            "snippet": (c.content or "")[:200],
            "date": c.communication_date or c.creation,
            "sender": c.sender,
            "doctype": "Communication",
            "name": c.name,
        })

    # Arrowz Call Logs (if available)
    try:
        phone = frappe.db.get_value(
            contact_doctype, contact_name,
            "mobile_no", as_dict=False,
        ) or frappe.db.get_value(contact_doctype, contact_name, "phone")

        if phone:
            calls = frappe.get_all(
                "AZ Call Log",
                filters={
                    "phone_number": ("like", f"%{phone[-8:]}%"),
                },
                fields=[
                    "name", "status", "duration", "direction",
                    "call_datetime", "caller_id", "notes",
                ],
                order_by="call_datetime desc",
                limit=max_items,
            )
            for cl in calls:
                history.append({
                    "type": "call",
                    "medium": "Phone",
                    "direction": cl.direction or "Unknown",
                    "subject": f"Call ({cl.status}) — {cl.duration or 0}s",
                    "snippet": cl.notes or "",
                    "date": cl.call_datetime,
                    "sender": cl.caller_id,
                    "doctype": "AZ Call Log",
                    "name": cl.name,
                })
    except Exception:
        pass  # AZ Call Log may not exist

    # Sort by date and limit
    history.sort(key=lambda x: x.get("date") or "", reverse=True)
    return history[:max_items]


def _get_last_call_summary(contact_doctype, contact_name):
    """Get the most recent call with full details."""
    try:
        phone = frappe.db.get_value(
            contact_doctype, contact_name, "mobile_no",
        ) or frappe.db.get_value(contact_doctype, contact_name, "phone")

        if not phone:
            return None

        calls = frappe.get_all(
            "AZ Call Log",
            filters={"phone_number": ("like", f"%{phone[-8:]}%")},
            fields=["*"],
            order_by="call_datetime desc",
            limit=1,
        )
        if calls:
            call = calls[0]
            return {
                "call_name": call.name,
                "datetime": call.get("call_datetime"),
                "duration": call.get("duration"),
                "status": call.get("status"),
                "direction": call.get("direction"),
                "notes": call.get("notes"),
                "recording": call.get("recording"),
                "caller": call.get("caller_id"),
            }
    except Exception:
        pass
    return None


def _get_campaign_info(campaign_name):
    """Get campaign details for the agent panel."""
    try:
        campaign = frappe.get_doc("Auto Dialer Campaign", campaign_name)
        return {
            "name": campaign.name,
            "campaign_name": campaign.campaign_name,
            "status": campaign.status,
            "priority": campaign.get("priority"),
            "total_entries": campaign.get("total_entries"),
            "completed_entries": campaign.get("completed_entries"),
            "start_date": campaign.get("start_date"),
            "end_date": campaign.get("end_date"),
            "notes": campaign.get("description") or campaign.get("notes") or "",
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 3. Auto-Classification
# ---------------------------------------------------------------------------
@frappe.whitelist()
def auto_classify_contact(doctype, name):
    """
    Apply Contact Classification rules to a contact.
    Scans all classifications with auto_classify=1 and evaluates their filter rules.

    Returns:
        list of classification names applied
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    classifications = frappe.get_all(
        "Contact Classification",
        filters={"auto_classify": 1},
        fields=[
            "name", "classification_name", "target_doctype",
            "filter_field", "filter_operator", "filter_value",
            "secondary_field", "secondary_operator", "secondary_value",
        ],
    )

    applied = []
    existing_tags = _get_contact_tags(doctype, name)

    for cls in classifications:
        if cls.target_doctype and cls.target_doctype != doctype:
            continue
        if cls.classification_name in existing_tags:
            continue

        if _matches_classification_rules(doctype, name, cls):
            # Apply tag
            try:
                frappe.db.sql("""
                    UPDATE `tab{doctype}`
                    SET _user_tags = CONCAT(IFNULL(_user_tags, ''), %s)
                    WHERE name = %s
                """.format(doctype=doctype),
                    (f",{cls.classification_name}", name),
                )
                applied.append(cls.classification_name)
            except Exception:
                pass

    if applied:
        frappe.db.commit()

    return applied


def _matches_classification_rules(doctype, name, cls):
    """Check if a contact matches a classification's filter rules."""
    try:
        # Primary filter
        if cls.filter_field and cls.filter_operator and cls.filter_value:
            val = frappe.db.get_value(doctype, name, cls.filter_field)
            if not _evaluate_filter(val, cls.filter_operator, cls.filter_value):
                return False
        elif not cls.filter_field:
            return False  # No filter means no auto-classify

        # Secondary filter (AND condition)
        if cls.secondary_field and cls.secondary_operator and cls.secondary_value:
            val = frappe.db.get_value(doctype, name, cls.secondary_field)
            if not _evaluate_filter(val, cls.secondary_operator, cls.secondary_value):
                return False

        return True
    except Exception:
        return False


def _evaluate_filter(actual_value, operator, expected_value):
    """Evaluate a single filter condition."""
    if actual_value is None:
        return operator == "is_not_set"

    op = operator.lower().replace(" ", "_")
    if op in ("=", "equals", "is"):
        return str(actual_value) == str(expected_value)
    elif op in ("!=", "not_equals", "is_not"):
        return str(actual_value) != str(expected_value)
    elif op in (">", "greater_than"):
        return flt(actual_value) > flt(expected_value)
    elif op in ("<", "less_than"):
        return flt(actual_value) < flt(expected_value)
    elif op in (">=", "greater_or_equal"):
        return flt(actual_value) >= flt(expected_value)
    elif op in ("<=", "less_or_equal"):
        return flt(actual_value) <= flt(expected_value)
    elif op in ("like", "contains"):
        return str(expected_value).lower() in str(actual_value).lower()
    elif op in ("not_like", "not_contains"):
        return str(expected_value).lower() not in str(actual_value).lower()
    elif op == "in":
        return str(actual_value) in [v.strip() for v in str(expected_value).split(",")]
    elif op == "not_in":
        return str(actual_value) not in [v.strip() for v in str(expected_value).split(",")]
    elif op == "is_set":
        return bool(actual_value)
    elif op == "is_not_set":
        return not bool(actual_value)
    return False


# ---------------------------------------------------------------------------
# 4. Marketing List Sync
# ---------------------------------------------------------------------------
@frappe.whitelist()
def sync_marketing_list(list_name):
    """Manually sync a marketing list from its source."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    doc = frappe.get_doc("Marketing List", list_name)
    if doc.source == "Segment" and doc.audience_segment:
        doc.sync_from_segment()
    elif doc.source == "Classification" and doc.classification:
        doc.sync_from_classification()
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "synced", "member_count": len(doc.members)}


def sync_all_marketing_lists():
    """Scheduler: sync all active lists with automatic sources."""
    lists = frappe.get_all(
        "Marketing List",
        filters={
            "status": "Active",
            "source": ("in", ["Segment", "Classification"]),
        },
        fields=["name"],
    )
    for ml in lists:
        try:
            sync_marketing_list(ml.name)
        except Exception as e:
            frappe.log_error(
                f"Marketing List Sync Error: {ml.name}\n{str(e)}",
                "AuraCRM Marketing List Sync",
            )


# ---------------------------------------------------------------------------
# 5. Analytics & Stats
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_marketing_dashboard():
    """Get marketing manager dashboard data."""
    frappe.has_permission("Auto Dialer Campaign", "read", throw=True)

    # Active campaigns
    campaigns = frappe.get_all(
        "Auto Dialer Campaign",
        filters={"status": "Active"},
        fields=["name", "campaign_name", "status", "total_entries",
                "completed_entries", "start_date", "end_date"],
        order_by="creation desc",
        limit=10,
    )

    # Marketing lists summary
    lists = frappe.get_all(
        "Marketing List",
        filters={"status": "Active"},
        fields=["name", "list_name", "source", "total_members",
                "active_members", "target_doctype"],
        order_by="creation desc",
        limit=10,
    )

    # Classifications
    classifications = frappe.get_all(
        "Contact Classification",
        fields=["name", "classification_name", "color", "priority",
                "icon", "auto_classify"],
        order_by="priority desc",
    )

    # Context rules
    context_rules = frappe.get_all(
        "Call Context Rule",
        filters={"enabled": 1},
        fields=["name", "rule_name", "priority", "applies_to_campaign",
                "applies_to_classification", "applies_to_segment"],
        order_by="priority desc",
    )

    # Segments
    segments = frappe.get_all(
        "Audience Segment",
        filters={"enabled": 1},
        fields=["name", "segment_name", "target_doctype", "member_count"],
        order_by="creation desc",
        limit=10,
    )

    # Stats
    total_leads = frappe.db.count("Lead")
    total_opps = frappe.db.count("Opportunity")
    active_campaigns = len(campaigns)

    return {
        "campaigns": campaigns,
        "lists": lists,
        "classifications": classifications,
        "context_rules": context_rules,
        "segments": segments,
        "stats": {
            "total_leads": total_leads,
            "total_opportunities": total_opps,
            "active_campaigns": active_campaigns,
            "active_lists": len(lists),
            "classifications_count": len(classifications),
            "context_rules_count": len(context_rules),
        },
    }


@frappe.whitelist()
def get_classification_stats():
    """Get per-classification contact counts."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    classifications = frappe.get_all(
        "Contact Classification",
        fields=["name", "classification_name", "color", "icon", "target_doctype"],
    )

    for cls in classifications:
        dt = cls.target_doctype or "Lead"
        # Security: validate doctype exists before using in SQL (prevents table injection)
        if not frappe.db.exists("DocType", dt):
            cls["contact_count"] = 0
            continue
        try:
            cls["contact_count"] = frappe.db.sql(
                "SELECT COUNT(*) FROM `tab{dt}` WHERE _user_tags LIKE %s".format(dt=dt),
                (f"%{cls.classification_name}%",),
            )[0][0]
        except Exception:
            cls["contact_count"] = 0

    return classifications


@frappe.whitelist()
def get_call_context_preview(contact_doctype, contact_name, campaign_name=None):
    """Preview what an agent would see for a given contact — for marketing managers."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    return get_agent_call_panel(contact_doctype, contact_name, campaign_name)
