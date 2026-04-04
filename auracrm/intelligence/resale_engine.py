# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
P20 — Smart Resale Engine
Monitors property portfolios for price appreciation and triggers AI-powered resale alerts.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, nowdate


def register_property_for_tracking(doc, method=None):
    """Triggered on Opportunity on_submit. Registers property for price monitoring."""
    property_unit = getattr(doc, "custom_property_unit", None)
    if not property_unit:
        return
    if frappe.db.exists("Property Portfolio Item", {"deal": doc.name}):
        return
    frappe.get_doc({
        "doctype": "Property Portfolio Item",
        "lead": getattr(doc, "lead", None) or getattr(doc, "party_name", None),
        "deal": doc.name,
        "property_unit": property_unit,
        "purchase_price": getattr(doc, "custom_deal_value", 0) or getattr(doc, "opportunity_amount", 0),
        "purchase_date": nowdate(),
        "alert_threshold_percent": 20.0,
    }).insert(ignore_permissions=True)
    frappe.db.commit()


def check_price_appreciation():
    """Scheduled weekly. Checks if any property has appreciated past threshold."""
    items = frappe.get_all(
        "Property Portfolio Item",
        filters={
            "resale_interest": ["!=", "Sold via Us"],
            "alert_sent": 0,
        },
        fields=[
            "name", "lead", "purchase_price", "property_unit",
            "alert_threshold_percent",
        ],
    )

    for item in items:
        if not item.purchase_price:
            continue

        # Try to get current market price (if Property Unit doctype exists)
        current_price = None
        try:
            current_price = frappe.db.get_value(
                "Property Unit", item.property_unit, "current_market_price",
            )
        except Exception:
            pass

        if not current_price:
            continue

        appreciation = ((current_price - item.purchase_price) / item.purchase_price) * 100

        frappe.db.set_value("Property Portfolio Item", item.name, {
            "current_market_price": current_price,
            "last_price_check": now_datetime(),
            "appreciation_percent": appreciation,
        })

        if appreciation >= (item.alert_threshold_percent or 20.0):
            _send_resale_alert(item, appreciation, current_price)

    frappe.db.commit()


def _send_resale_alert(item: dict, appreciation: float, current_price: float):
    """Send AI-generated resale offer to the client."""
    if not item.lead:
        return

    try:
        lead = frappe.get_doc("Lead", item.lead)
    except Exception:
        return

    # Generate AI resale message
    try:
        from auracrm.intelligence.ai_profiler import generate_resale_message
        message = generate_resale_message(lead, appreciation, current_price)
    except Exception:
        message = _("Your property has appreciated by {0}%! Contact us.").format(f"{appreciation:.1f}")

    # Log the alert
    frappe.log_error(
        title=f"[Resale Alert] {lead.lead_name} — {appreciation:.1f}%",
        message=message,
    )

    frappe.db.set_value("Property Portfolio Item", item.name, {
        "alert_sent": 1,
        "alert_sent_at": now_datetime(),
    })
