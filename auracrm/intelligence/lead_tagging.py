# Copyright (c) 2025, Arkan Labs and contributors
# For license information, please see license.txt

"""
P18 extension — Lead Tagging & Auto-Grouping
Automatically tags leads based on segment, score, and enrichment data.
"""

import frappe


def auto_tag_and_group(doc, method=None):
    """Triggered on Lead on_update. Auto-tags based on AI profile and enrichment data."""
    # Check if AI profile exists
    profile = frappe.db.get_value(
        "AI Lead Profile",
        {"lead": doc.name},
        ["disc_profile", "lead_segment", "priority_score"],
        as_dict=True,
    )
    if not profile:
        return

    # Auto-tag based on segment
    if profile.lead_segment and profile.lead_segment != "Unknown":
        _ensure_tag(doc.name, "Lead", f"Segment: {profile.lead_segment}")

    # Auto-tag based on DISC profile
    if profile.disc_profile:
        _ensure_tag(doc.name, "Lead", f"DISC: {profile.disc_profile}")

    # Priority tier
    score = profile.priority_score or 0
    if score >= 80:
        _ensure_tag(doc.name, "Lead", "Priority: Hot")
    elif score >= 60:
        _ensure_tag(doc.name, "Lead", "Priority: Warm")
    elif score >= 40:
        _ensure_tag(doc.name, "Lead", "Priority: Cold")


def _ensure_tag(docname: str, doctype: str, tag: str):
    """Add a tag if it doesn't already exist."""
    try:
        existing = frappe.db.exists("Tag Link", {
            "document_type": doctype,
            "document_name": docname,
            "tag": tag,
        })
        if not existing:
            frappe.get_doc({
                "doctype": "Tag Link",
                "document_type": doctype,
                "document_name": docname,
                "tag": tag,
            }).insert(ignore_permissions=True)
    except Exception:
        pass
