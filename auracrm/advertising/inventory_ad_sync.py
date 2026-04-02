# Copyright (c) 2025, Arkan Labs and contributors
# For license information, please see license.txt

"""
P19 — Advertising Command Center: Inventory-Ad Sync + ROI Budget Engine
Pauses ads when inventory is sold, adjusts budgets based on campaign ROI.
"""

import frappe
import requests
from frappe.utils import now_datetime, nowdate


def on_unit_status_change(doc, method=None):
    """Triggered on Property Unit on_update. Pauses ads when unit is sold."""
    if not hasattr(doc, "status") or doc.status not in ("Sold", "Reserved"):
        return
    if not doc.has_value_changed("status"):
        return

    frappe.enqueue(
        "auracrm.advertising.inventory_ad_sync.pause_ads_for_unit",
        property_type=getattr(doc, "property_type", ""),
        unit_type=getattr(doc, "unit_type", ""),
        unit_name=doc.name,
        queue="high",
        is_async=True,
    )


def pause_ads_for_unit(property_type: str, unit_type: str, unit_name: str):
    """Pause all ad sets linked to a sold-out unit type."""
    settings = frappe.get_single("AuraCRM Settings")
    token = settings.get_password("meta_access_token") if hasattr(settings, "meta_access_token") else None

    # Check remaining inventory (if Property Unit doctype exists)
    try:
        available = frappe.db.count("Property Unit", {
            "property_type": property_type,
            "unit_type": unit_type,
            "status": "Available",
        })
        if available > 0:
            return  # Still have units — keep ads running
    except Exception:
        return  # Property Unit doctype may not exist

    # No units left — pause all linked ad sets
    links = frappe.get_all(
        "Ad Inventory Link",
        filters={
            "property_type": property_type,
            "unit_type": unit_type,
            "is_active": 1,
        },
        fields=["name", "platform_adset_id", "platform", "campaign_name"],
    )

    for link in links:
        if link.platform == "Meta" and token:
            _pause_meta_adset(link.platform_adset_id, token)

        frappe.db.set_value("Ad Inventory Link", link.name, {
            "is_active": 0,
            "current_status": "Paused",
            "paused_reason": f"No inventory: {unit_type} (unit {unit_name})",
            "paused_at": now_datetime(),
        })

    frappe.db.commit()

    # Queue social proof post about sold unit
    try:
        frappe.enqueue(
            "auracrm.social_publishing.sold_proof_generator.generate_sold_post",
            unit_name=unit_name,
            queue="default",
            is_async=True,
        )
    except Exception:
        pass


def adjust_budgets_by_roi():
    """Scheduled every 6 hours. Moves budget from losing to winning campaigns."""
    settings = frappe.get_single("AuraCRM Settings")
    token = settings.get_password("meta_access_token") if hasattr(settings, "meta_access_token") else None

    campaigns = frappe.db.sql("""
        SELECT r.name, r.platform_campaign_id, r.campaign_name,
               r.current_daily_budget, r.platform,
               COALESCE(r.total_revenue_7d, 0) as revenue_7d,
               COALESCE(r.total_deals_7d, 0) as deal_count
        FROM `tabCRM Campaign ROI Link` r
        WHERE r.is_active = 1
        ORDER BY revenue_7d DESC
    """, as_dict=True)

    if not campaigns:
        return

    top = campaigns[0]
    for c in campaigns:
        if not c.current_daily_budget:
            continue

        new_budget = c.current_daily_budget
        if c.revenue_7d == 0 and c.deal_count == 0:
            new_budget = c.current_daily_budget * 0.80  # Shrink losers by 20%
        elif c.name == top.name and c.revenue_7d > 0:
            new_budget = c.current_daily_budget * 1.20  # Scale winner by 20%

        if abs(new_budget - c.current_daily_budget) < 1:
            continue

        # Apply budget change on platform
        if c.platform == "Meta" and token:
            _update_meta_campaign_budget(c.platform_campaign_id, new_budget, token)

        # Log the adjustment
        history = frappe.parse_json(
            frappe.db.get_value("CRM Campaign ROI Link", c.name, "budget_adjustment_history") or "[]"
        )
        history.append({
            "date": nowdate(),
            "old_budget": float(c.current_daily_budget),
            "new_budget": float(new_budget),
            "reason": "ROI-based auto-adjustment",
        })
        frappe.db.set_value("CRM Campaign ROI Link", c.name, {
            "current_daily_budget": new_budget,
            "last_roi_check": now_datetime(),
            "budget_adjustment_history": frappe.as_json(history),
        })

    frappe.db.commit()


def _pause_meta_adset(adset_id: str, token: str):
    """Pause a Meta (Facebook) ad set."""
    if not adset_id or not token:
        return
    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{adset_id}",
            data={"status": "PAUSED", "access_token": token},
            timeout=30,
        )
        if r.status_code != 200:
            frappe.log_error(
                title=f"[AdSync] Meta pause failed: {adset_id}",
                message=r.text[:500],
            )
    except Exception as e:
        frappe.log_error(title="[AdSync] Meta API Error", message=str(e))


def _update_meta_campaign_budget(campaign_id: str, new_budget: float, token: str):
    """Update daily budget for a Meta campaign."""
    if not campaign_id or not token:
        return
    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{campaign_id}",
            data={
                "daily_budget": int(new_budget * 100),  # Meta uses cents
                "access_token": token,
            },
            timeout=30,
        )
        if r.status_code != 200:
            frappe.log_error(
                title=f"[AdSync] Meta budget update failed: {campaign_id}",
                message=r.text[:500],
            )
    except Exception as e:
        frappe.log_error(title="[AdSync] Meta Budget API Error", message=str(e))
