"""
AuraCRM - Lead Scoring Engine (Phase 2 - Full Implementation)
===============================================================
Multi-dimensional scoring:
- Demographic (field-based rules from Lead Scoring Rule DocType)
- Behavioral (communication activity, response patterns)
- Engagement (channel diversity, recency)
- Score decay for stale leads
- Score logging for audit trail
"""
import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate, cint, flt, time_diff_in_seconds


# ---- Hook Entry Points ----

def calculate_lead_score(doc, method=None):
    """Hook: validate on Lead - recalculate score."""
    if getattr(doc.flags, "skip_scoring", False):
        return
    try:
        settings = frappe.get_cached_doc("AuraCRM Settings")
        if not cint(settings.get("scoring_enabled")):
            return
    except Exception:
        return

    old_score = cint(doc.get("aura_score") or 0)

    # 1. Demographic score from rules
    demo_score = _evaluate_demographic_rules(doc)

    # 2. Behavioral score from communication activity
    behav_score = _evaluate_behavioral_score(doc.doctype, doc.name)

    # 3. Engagement score
    engage_score = _evaluate_engagement_score(doc.doctype, doc.name)

    # Combine: demographic 50%, behavioral 30%, engagement 20%
    max_score = cint(settings.get("max_lead_score") or 100)
    total = demo_score * 0.5 + behav_score * 0.3 + engage_score * 0.2
    new_score = max(0, min(int(round(total)), max_score))

    doc.aura_score = new_score

    # Log if changed significantly
    if abs(new_score - old_score) >= 5:
        _log_score_change(doc.name, old_score, new_score,
                          "Demographic: %d, Behavioral: %d, Engagement: %d" % (demo_score, behav_score, engage_score))


def calculate_opportunity_score(doc, method=None):
    """Hook: validate on Opportunity - score based on deal attributes."""
    if getattr(doc.flags, "skip_scoring", False):
        return

    score = 0

    # Amount-based scoring
    amount = flt(doc.get("opportunity_amount"))
    if amount > 1000000:
        score += 30
    elif amount > 500000:
        score += 25
    elif amount > 100000:
        score += 20
    elif amount > 50000:
        score += 15
    elif amount > 10000:
        score += 10

    # Stage progression scoring
    stage = (doc.get("sales_stage") or "").lower()
    stage_scores = {
        "prospecting": 5, "qualification": 15, "needs analysis": 25,
        "value proposition": 35, "identifying decision makers": 40,
        "perception analysis": 50, "proposal/price quote": 65,
        "negotiation/review": 80, "closed won": 100,
    }
    for key, val in stage_scores.items():
        if key in stage:
            score += val
            break

    # Has expected closing date
    if doc.get("expected_closing"):
        score += 10

    # Has contact person
    if doc.get("contact_person"):
        score += 5

    doc.opportunity_score = max(0, min(score, 100))


def on_communication(doc, method=None):
    """Hook: after_insert on Communication - update related lead/opp score."""
    if not doc.reference_doctype or not doc.reference_name:
        return

    if doc.reference_doctype == "Lead":
        try:
            lead = frappe.get_doc("Lead", doc.reference_name)
            lead.flags.skip_scoring = False
            lead.save(ignore_permissions=True)
        except Exception:
            pass
    elif doc.reference_doctype == "Opportunity":
        try:
            opp = frappe.get_doc("Opportunity", doc.reference_name)
            opp.flags.skip_scoring = False
            opp.save(ignore_permissions=True)
        except Exception:
            pass


def apply_score_decay():
    """Scheduled: daily at 2 AM - reduce scores for stale leads."""
    try:
        settings = frappe.get_cached_doc("AuraCRM Settings")
        decay_rate = cint(settings.get("score_decay_points_per_day")) or 2
        decay_after_days = cint(settings.get("score_decay_after_days")) or 7
    except Exception:
        return

    if not decay_rate:
        return

    cutoff = add_days(now_datetime(), -decay_after_days)

    leads = frappe.get_all(
        "Lead",
        filters={
            "aura_score": [">", 0],
            "modified": ["<", cutoff],
            "status": ["not in", ["Converted", "Do Not Contact"]],
        },
        fields=["name", "aura_score"],
        limit=500,
    )

    count = 0
    for lead in leads:
        new_score = max(0, lead.aura_score - decay_rate)
        if new_score != lead.aura_score:
            frappe.db.set_value("Lead", lead.name, "aura_score", new_score, update_modified=False)
            count += 1

    if count:
        frappe.db.commit()
        frappe.logger("auracrm").info("Score decay applied to %d leads" % count)


# ---- Demographic Scoring (Rule-Based) ----

def _evaluate_demographic_rules(doc):
    """Evaluate all enabled Lead Scoring Rules — batch criteria fetch."""
    rules = frappe.get_all(
        "Lead Scoring Rule",
        filters={"enabled": 1},
        fields=["name"],
        order_by="priority asc",
    )

    if not rules:
        return 0

    rule_names = [r.name for r in rules]

    # Single query: all criteria across all rules
    all_criteria = frappe.get_all(
        "Scoring Criterion",
        filters={"parent": ["in", rule_names], "parenttype": "Lead Scoring Rule"},
        fields=["field_name", "operator", "field_value", "points"],
        order_by="parent, idx asc",
    )

    total_score = 0
    for c in all_criteria:
        total_score += _evaluate_criterion(doc, c)

    return max(0, min(total_score, 100))


def _evaluate_criterion(doc, criterion):
    """Evaluate a single scoring criterion against a document."""
    field = criterion.get("field_name", "")
    operator = criterion.get("operator", "equals")
    value = criterion.get("field_value", "")
    points = cint(criterion.get("points", 0))

    doc_value = doc.get(field)
    if doc_value is None:
        doc_value = ""
    doc_value = str(doc_value)

    match = False
    if operator == "equals":
        match = doc_value.lower() == str(value).lower()
    elif operator == "contains":
        match = str(value).lower() in doc_value.lower()
    elif operator == "greater_than":
        try:
            match = flt(doc_value) > flt(value)
        except (ValueError, TypeError):
            pass
    elif operator == "less_than":
        try:
            match = flt(doc_value) < flt(value)
        except (ValueError, TypeError):
            pass
    elif operator == "in_list":
        vals = [v.strip().lower() for v in str(value).split(",")]
        match = doc_value.lower() in vals
    elif operator == "is_set":
        match = bool(doc_value and doc_value.strip())
    elif operator == "is_not_set":
        match = not bool(doc_value and doc_value.strip())

    return points if match else 0


# ---- Behavioral Scoring ----

def _evaluate_behavioral_score(doctype, name):
    """Score based on communication activity (last 30 days)."""
    cutoff = add_days(now_datetime(), -30)

    comms = frappe.get_all(
        "Communication",
        filters={
            "reference_doctype": doctype,
            "reference_name": name,
            "creation": [">=", cutoff],
        },
        fields=["communication_type", "sent_or_received", "communication_medium", "creation"],
    )

    if not comms:
        return 0

    score = 0

    # Points per communication type
    for comm in comms:
        medium = (comm.get("communication_medium") or "").lower()
        direction = (comm.get("sent_or_received") or "").lower()

        if direction == "received":
            score += 8  # Incoming = lead is engaged
        else:
            score += 3  # Outgoing = agent contacted

        if "phone" in medium or "call" in medium:
            score += 5  # Calls are high-value
        elif "whatsapp" in medium or "chat" in medium:
            score += 3
        elif "email" in medium:
            score += 2

    # Recency bonus: most recent comm
    if comms:
        most_recent = max(comms, key=lambda c: c.creation)
        days_ago = (getdate(now_datetime()) - getdate(most_recent.creation)).days
        if days_ago <= 1:
            score += 15
        elif days_ago <= 3:
            score += 10
        elif days_ago <= 7:
            score += 5

    return min(score, 100)


# ---- Engagement Scoring ----

def _evaluate_engagement_score(doctype, name):
    """Score based on channel diversity and interaction depth."""
    comms = frappe.get_all(
        "Communication",
        filters={
            "reference_doctype": doctype,
            "reference_name": name,
        },
        fields=["communication_medium"],
    )

    if not comms:
        return 0

    channels = set()
    for c in comms:
        medium = (c.get("communication_medium") or "").lower()
        if medium:
            channels.add(medium)

    score = 0

    # Channel diversity (max 40 points)
    score += min(len(channels) * 15, 40)

    # Volume bonus (max 30 points)
    score += min(len(comms) * 3, 30)

    # Has phone interaction (high-engagement signal)
    if any("phone" in ch or "call" in ch for ch in channels):
        score += 15

    # Has meeting
    if any("meeting" in ch or "video" in ch for ch in channels):
        score += 15

    return min(score, 100)


# ---- Score Logging ----

def _log_score_change(lead_name, old_score, new_score, reason=""):
    """Create a Lead Score Log entry for audit trail."""
    try:
        frappe.get_doc({
            "doctype": "Lead Score Log",
            "lead": lead_name,
            "old_score": old_score,
            "new_score": new_score,
            "reason": reason,
            "triggered_by": frappe.session.user,
        }).insert(ignore_permissions=True)
    except Exception:
        pass
