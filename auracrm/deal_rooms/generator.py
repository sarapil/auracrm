"""
P27 — Deal Room Generator
Creates shareable, branded web pages (deal rooms) for clients to review
property details, documents, and interactive content.
Served via Frappe's website_route_rules as /deal-room/<key>.
"""
import frappe
from frappe.utils import now_datetime, random_string, get_url
import json


# ---------------------------------------------------------------------------
# Deal Room CRUD
# ---------------------------------------------------------------------------
@frappe.whitelist()
def create_deal_room(opportunity=None, lead=None, title=None, assets=None):
    """Create a new Deal Room and return its URL.

    Args:
        opportunity: Link to Opportunity doc.
        lead: Link to Lead doc.
        title: Display title for the deal room.
        assets: JSON array of asset dicts [{type, label, url, description}].

    Returns:
        dict with room name, url_key, and full_url.
    """
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    url_key = _generate_url_key()

    room = frappe.new_doc("Deal Room")
    room.title = title or f"Deal Room — {opportunity or lead or 'New'}"
    room.room_url_key = url_key
    room.opportunity = opportunity or ""
    room.lead = lead or ""
    room.status = "Active"
    room.created_by = frappe.session.user
    room.expires_at = None  # No expiry by default
    room.insert(ignore_permissions=True)

    # Add assets
    if assets:
        asset_list = assets if isinstance(assets, list) else json.loads(assets)
        for idx, a in enumerate(asset_list, 1):
            asset = frappe.new_doc("Deal Room Asset")
            asset.parent = room.name
            asset.parenttype = "Deal Room"
            asset.parentfield = "assets"
            asset.idx = idx
            asset.asset_type = a.get("type", "Document")
            asset.label = a.get("label", "")
            asset.url = a.get("url", "")
            asset.description = a.get("description", "")
            asset.insert(ignore_permissions=True)

    frappe.db.commit()

    full_url = f"{get_url()}/deal-room/{url_key}"
    return {"name": room.name, "url_key": url_key, "full_url": full_url}


@frappe.whitelist()
def add_asset_to_room(room_name, asset_type, label, url, description=""):
    """Add a single asset to an existing deal room."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    room = frappe.get_doc("Deal Room", room_name)

    count = frappe.db.count("Deal Room Asset", {"parent": room_name})
    asset = frappe.new_doc("Deal Room Asset")
    asset.parent = room_name
    asset.parenttype = "Deal Room"
    asset.parentfield = "assets"
    asset.idx = count + 1
    asset.asset_type = asset_type
    asset.label = label
    asset.url = url
    asset.description = description
    asset.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "success", "asset_name": asset.name}


@frappe.whitelist()
def deactivate_room(room_name):
    """Mark a deal room as inactive."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    frappe.db.set_value("Deal Room", room_name, "status", "Inactive")
    frappe.db.commit()
    return {"status": "success"}


# ---------------------------------------------------------------------------
# Public Page Controller (for website_route_rules)
# ---------------------------------------------------------------------------
def get_deal_room_context(context):
    """Called by Frappe website routing to render the deal room page.
    URL pattern: /deal-room/<room_url_key>
    """
    url_key = frappe.form_dict.get("room_url_key") or ""

    room = frappe.db.get_value(
        "Deal Room",
        {"room_url_key": url_key, "status": "Active"},
        ["name", "title", "opportunity", "lead", "created_by", "expires_at"],
        as_dict=True,
    )

    if not room:
        frappe.throw("Deal Room not found or inactive", frappe.DoesNotExistError)

    # Check expiry
    if room.expires_at and room.expires_at < now_datetime():
        frappe.throw("This Deal Room has expired", frappe.PermissionError)

    # Get assets
    assets = frappe.get_all(
        "Deal Room Asset",
        filters={"parent": room.name, "parenttype": "Deal Room"},
        fields=["asset_type", "label", "url", "description"],
        order_by="idx asc",
    )

    # Track view
    _log_room_view(room.name, url_key)

    context.room = room
    context.assets = assets
    context.no_cache = 1
    context.show_sidebar = False
    context.title = room.title


def _log_room_view(room_name, url_key):
    """Log a view event for analytics."""
    try:
        frappe.db.sql(
            """UPDATE `tabDeal Room`
            SET view_count = IFNULL(view_count, 0) + 1,
                last_viewed_at = %s
            WHERE name = %s""",
            (now_datetime(), room_name),
        )
    except Exception:
        pass  # Non-critical


# ---------------------------------------------------------------------------
# Auto-Generate from Opportunity
# ---------------------------------------------------------------------------
def auto_generate_on_opportunity(doc, method):
    """doc_event: Opportunity → on_update.
    Auto-generate deal room when opportunity reaches a certain stage."""
    settings = frappe.get_cached_doc("AuraCRM Settings")
    if not settings.get("auto_deal_rooms"):
        return

    trigger_status = settings.get("deal_room_trigger_status") or "Quotation"
    if doc.status != trigger_status:
        return

    # Check if room already exists
    existing = frappe.db.exists("Deal Room", {"opportunity": doc.name, "status": "Active"})
    if existing:
        return

    # Build assets from opportunity
    assets = []
    if doc.get("items"):
        for item in doc.items:
            assets.append({
                "type": "Property",
                "label": item.item_name or item.item_code,
                "url": "",
                "description": f"Qty: {item.qty}, Rate: {item.rate}",
            })

    result = create_deal_room(
        opportunity=doc.name,
        lead=doc.get("party_name") if doc.opportunity_from == "Lead" else None,
        title=f"Property Showcase — {doc.party_name or doc.name}",
        assets=assets,
    )

    # Notify the sales agent
    if doc.get("_assign"):
        assigned = json.loads(doc._assign) if isinstance(doc._assign, str) else doc._assign
        for user in assigned:
            frappe.publish_realtime(
                event="auracrm_deal_room_created",
                message={
                    "room_name": result["name"],
                    "full_url": result["full_url"],
                    "opportunity": doc.name,
                },
                user=user,
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _generate_url_key():
    """Generate a unique URL-safe key for the deal room."""
    while True:
        key = random_string(12).lower()
        if not frappe.db.exists("Deal Room", {"room_url_key": key}):
            return key
