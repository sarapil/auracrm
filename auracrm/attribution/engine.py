"""
P30 — Revenue Attribution Engine
Tracks customer journeys across touchpoints and attributes revenue
to marketing channels using configurable attribution models.
Supports: First Touch, Last Touch, Linear, Time Decay, U-Shaped, W-Shaped.
"""
import frappe
from frappe.utils import now_datetime, add_to_date, getdate, flt, time_diff_in_hours
import json
from datetime import datetime


# ---------------------------------------------------------------------------
# Attribution Models
# ---------------------------------------------------------------------------
ATTRIBUTION_MODELS = {
    "First Touch": "_model_first_touch",
    "Last Touch": "_model_last_touch",
    "Linear": "_model_linear",
    "Time Decay": "_model_time_decay",
    "U-Shaped": "_model_u_shaped",
    "W-Shaped": "_model_w_shaped",
}


# ---------------------------------------------------------------------------
# Touchpoint Recording
# ---------------------------------------------------------------------------
def record_touchpoint(doc, method):
    """doc_event hook — record touchpoints from Communication, Lead, Opportunity events.
    Called on Communication after_insert and Lead/Opportunity on_update."""
    touchpoint_data = _extract_touchpoint_data(doc)
    if not touchpoint_data:
        return

    # Find or create Customer Journey
    journey = _get_or_create_journey(touchpoint_data)

    # Add touchpoint
    tp = frappe.new_doc("Journey Touchpoint")
    tp.parent = journey
    tp.parenttype = "Customer Journey"
    tp.parentfield = "touchpoints"

    existing_count = frappe.db.count(
        "Journey Touchpoint",
        {"parent": journey, "parenttype": "Customer Journey"},
    )
    tp.idx = existing_count + 1

    tp.channel = touchpoint_data.get("channel", "Direct")
    tp.source = touchpoint_data.get("source", "")
    tp.campaign = touchpoint_data.get("campaign", "")
    tp.interaction_type = touchpoint_data.get("interaction_type", "")
    tp.touchpoint_time = now_datetime()
    tp.reference_doctype = doc.doctype
    tp.reference_name = doc.name
    tp.insert(ignore_permissions=True)

    # Update journey's last touch
    frappe.db.set_value(
        "Customer Journey", journey, "last_touchpoint_at", now_datetime()
    )
    frappe.db.commit()


def _extract_touchpoint_data(doc):
    """Extract touchpoint information from various document types."""
    data = {}

    if doc.doctype == "Communication":
        data["lead"] = doc.get("reference_name") if doc.get("reference_doctype") == "Lead" else ""
        data["channel"] = _comm_to_channel(doc.get("communication_medium"))
        data["interaction_type"] = doc.get("communication_type") or "Communication"
        data["source"] = doc.get("sender") or ""
    elif doc.doctype == "Lead":
        data["lead"] = doc.name
        data["channel"] = doc.get("source") or "Direct"
        data["interaction_type"] = "Status Change"
        data["source"] = doc.get("campaign_name") or ""
        data["campaign"] = doc.get("campaign_name") or ""
    elif doc.doctype == "Opportunity":
        data["lead"] = doc.get("party_name") if doc.get("opportunity_from") == "Lead" else ""
        data["customer"] = doc.get("party_name") if doc.get("opportunity_from") == "Customer" else ""
        data["channel"] = doc.get("source") or "Direct"
        data["interaction_type"] = "Opportunity Update"
        data["campaign"] = doc.get("campaign") or ""

    return data if (data.get("lead") or data.get("customer")) else None


def _comm_to_channel(medium):
    """Map communication medium to marketing channel."""
    mapping = {
        "Email": "Email",
        "Phone": "Phone",
        "Chat": "Chat",
        "SMS": "SMS",
        "WhatsApp": "WhatsApp",
        "Other": "Direct",
    }
    return mapping.get(medium, "Direct")


def _get_or_create_journey(data):
    """Get or create a Customer Journey for the lead/customer."""
    lead = data.get("lead")
    customer = data.get("customer")

    filters = {}
    if lead:
        filters["lead"] = lead
    elif customer:
        filters["customer"] = customer
    else:
        return None

    existing = frappe.db.get_value("Customer Journey", filters, "name")
    if existing:
        return existing

    journey = frappe.new_doc("Customer Journey")
    journey.lead = lead or ""
    journey.customer = customer or ""
    journey.status = "Active"
    journey.first_touchpoint_at = now_datetime()
    journey.last_touchpoint_at = now_datetime()
    journey.insert(ignore_permissions=True)
    frappe.db.commit()
    return journey.name


# ---------------------------------------------------------------------------
# Attribution Calculation
# ---------------------------------------------------------------------------
@frappe.whitelist()
def calculate_attribution(journey_name, model_name=None):
    """Calculate and return attributed revenue for a customer journey.

    Args:
        journey_name: Customer Journey document name.
        model_name: Attribution Model name. If None, uses default.

    Returns:
        dict with channel_attribution breakdown.
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    journey = frappe.get_doc("Customer Journey", journey_name)

    # Get the model
    if not model_name:
        model_name = frappe.db.get_value(
            "Attribution Model",
            {"is_default": 1},
            "name",
        )
    if not model_name:
        # Fallback to first available
        model_name = frappe.db.get_value("Attribution Model", {}, "name")

    if not model_name:
        return {"error": "No attribution model configured"}

    model = frappe.get_doc("Attribution Model", model_name)
    model_type = model.get("model_type") or "Linear"

    # Get touchpoints
    touchpoints = frappe.get_all(
        "Journey Touchpoint",
        filters={"parent": journey_name, "parenttype": "Customer Journey"},
        fields=["channel", "source", "campaign", "touchpoint_time", "interaction_type"],
        order_by="touchpoint_time asc",
    )

    if not touchpoints:
        return {"touchpoints": 0, "attribution": {}}

    # Get total revenue
    total_revenue = _get_journey_revenue(journey)

    # Calculate attribution weights
    model_fn = getattr(
        __import__(__name__, fromlist=[ATTRIBUTION_MODELS[model_type]]),
        ATTRIBUTION_MODELS[model_type],
        _model_linear,
    )
    weights = model_fn(touchpoints)

    # Build attribution breakdown
    attribution = {}
    for i, tp in enumerate(touchpoints):
        channel = tp.channel
        weight = weights[i] if i < len(weights) else 0
        attributed_revenue = flt(total_revenue * weight, 2)

        if channel not in attribution:
            attribution[channel] = {
                "weight": 0,
                "revenue": 0,
                "touchpoints": 0,
            }
        attribution[channel]["weight"] = flt(attribution[channel]["weight"] + weight, 4)
        attribution[channel]["revenue"] = flt(attribution[channel]["revenue"] + attributed_revenue, 2)
        attribution[channel]["touchpoints"] += 1

    # Save to journey
    frappe.db.set_value(
        "Customer Journey",
        journey_name,
        {
            "attribution_model": model_name,
            "attributed_revenue": total_revenue,
            "attribution_json": json.dumps(attribution),
            "last_calculated_at": now_datetime(),
        },
    )
    frappe.db.commit()

    return {
        "total_revenue": total_revenue,
        "model": model_type,
        "touchpoints": len(touchpoints),
        "attribution": attribution,
    }


def recalculate_all_journeys():
    """Scheduled weekly — recalculate attribution for all active journeys."""
    journeys = frappe.get_all(
        "Customer Journey",
        filters={"status": "Active"},
        pluck="name",
        limit_page_length=500,
    )
    for j_name in journeys:
        try:
            calculate_attribution(j_name)
        except Exception as e:
            frappe.log_error(title=f"Attribution recalc failed: {j_name}", message=str(e))


# ---------------------------------------------------------------------------
# Attribution Model Functions
# All return a list of weights (same length as touchpoints), summing to 1.0.
# ---------------------------------------------------------------------------
def _model_first_touch(touchpoints):
    """100% credit to the first touchpoint."""
    n = len(touchpoints)
    if n == 0:
        return []
    weights = [0.0] * n
    weights[0] = 1.0
    return weights


def _model_last_touch(touchpoints):
    """100% credit to the last touchpoint."""
    n = len(touchpoints)
    if n == 0:
        return []
    weights = [0.0] * n
    weights[-1] = 1.0
    return weights


def _model_linear(touchpoints):
    """Equal credit to all touchpoints."""
    n = len(touchpoints)
    if n == 0:
        return []
    return [1.0 / n] * n


def _model_time_decay(touchpoints, half_life_days=7):
    """More credit to recent touchpoints, decaying over time."""
    n = len(touchpoints)
    if n == 0:
        return []
    if n == 1:
        return [1.0]

    import math

    last_time = touchpoints[-1].touchpoint_time
    raw_weights = []

    for tp in touchpoints:
        hours_ago = time_diff_in_hours(last_time, tp.touchpoint_time)
        days_ago = max(hours_ago / 24.0, 0)
        weight = math.pow(0.5, days_ago / half_life_days)
        raw_weights.append(weight)

    total = sum(raw_weights)
    return [w / total for w in raw_weights] if total > 0 else [1.0 / n] * n


def _model_u_shaped(touchpoints):
    """40% first, 40% last, 20% distributed among middle."""
    n = len(touchpoints)
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    if n == 2:
        return [0.5, 0.5]

    weights = [0.0] * n
    weights[0] = 0.4
    weights[-1] = 0.4
    middle_share = 0.2 / (n - 2)
    for i in range(1, n - 1):
        weights[i] = middle_share
    return weights


def _model_w_shaped(touchpoints):
    """30% first, 30% middle, 30% last, 10% distributed among others."""
    n = len(touchpoints)
    if n == 0:
        return []
    if n <= 2:
        return _model_u_shaped(touchpoints)
    if n == 3:
        return [1.0 / 3] * 3

    weights = [0.0] * n
    mid = n // 2
    weights[0] = 0.3
    weights[mid] = 0.3
    weights[-1] = 0.3

    remaining = 0.1
    others = n - 3
    if others > 0:
        share = remaining / others
        for i in range(n):
            if i not in (0, mid, n - 1):
                weights[i] = share
    else:
        weights[0] += remaining / 3
        weights[mid] += remaining / 3
        weights[-1] += remaining / 3

    return weights


# ---------------------------------------------------------------------------
# Revenue Lookup
# ---------------------------------------------------------------------------
def _get_journey_revenue(journey):
    """Get total attributed revenue from opportunities linked to the journey."""
    lead = journey.get("lead")
    customer = journey.get("customer")
    total = 0

    if lead:
        opps = frappe.get_all(
            "Opportunity",
            filters={"party_name": lead, "opportunity_from": "Lead", "status": "Won"},
            fields=["opportunity_amount"],
        )
        total += sum(flt(o.opportunity_amount) for o in opps)

    if customer:
        opps = frappe.get_all(
            "Opportunity",
            filters={"party_name": customer, "opportunity_from": "Customer", "status": "Won"},
            fields=["opportunity_amount"],
        )
        total += sum(flt(o.opportunity_amount) for o in opps)

    return total


# ---------------------------------------------------------------------------
# Reporting API
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_channel_performance(period_days=30):
    """Return aggregated channel performance across all journeys."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    cutoff = add_to_date(now_datetime(), days=-period_days)

    journeys = frappe.get_all(
        "Customer Journey",
        filters={"last_calculated_at": (">=", cutoff)},
        fields=["name", "attribution_json", "attributed_revenue"],
    )

    channel_totals = {}
    for j in journeys:
        try:
            attribution = json.loads(j.attribution_json or "{}")
        except (json.JSONDecodeError, TypeError):
            continue

        for channel, data in attribution.items():
            if channel not in channel_totals:
                channel_totals[channel] = {"revenue": 0, "touchpoints": 0, "journeys": 0}
            channel_totals[channel]["revenue"] += flt(data.get("revenue", 0))
            channel_totals[channel]["touchpoints"] += data.get("touchpoints", 0)
            channel_totals[channel]["journeys"] += 1

    return {
        "period_days": period_days,
        "channels": channel_totals,
        "total_journeys": len(journeys),
        "total_revenue": sum(flt(j.attributed_revenue) for j in journeys),
    }
